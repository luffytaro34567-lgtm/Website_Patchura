"""
In-Memory Sliding-Window Rate Limiting Utility.
Protects sensitive authentication, recovery, scanning, and public opt-out endpoints
against automated brute-force attacks, credential stuffing, and resource exhaustion.
"""
import asyncio
from collections import defaultdict
import time
from typing import Dict, List
from fastapi import HTTPException, Request, status


class InMemoryRateLimiter:
    """Sliding-window rate limiter tracking request timestamps per client IP."""

    def __init__(self):
        # Maps key -> list of float timestamps
        self._history: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
    ) -> None:
        """
        Enforces that `key` does not exceed `max_requests` within `window_seconds`.
        Raises HTTP 429 Too Many Requests if the limit is exceeded.
        """
        now = time.time()
        cutoff = now - window_seconds

        async with self._lock:
            timestamps = self._history[key]
            # Prune timestamps older than window
            self._history[key] = [t for t in timestamps if t > cutoff]

            if len(self._history[key]) >= max_requests:
                oldest_in_window = self._history[key][0]
                retry_after = max(1, int(oldest_in_window + window_seconds - now))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Too many requests. Please retry in {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)},
                )

            # Record current request timestamp
            self._history[key].append(now)

    async def reset(self) -> None:
        """Clears all stored rate limit history (primarily for test isolation)."""
        async with self._lock:
            self._history.clear()


# Global singleton instance
limiter = InMemoryRateLimiter()


class RateLimit:
    """FastAPI route dependency enforcing sliding-window rate limits by client IP."""

    def __init__(self, max_requests: int, window_seconds: int = 60, scope: str = "default"):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.scope = scope

    async def __call__(self, request: Request) -> None:
        # Determine client identifier: X-Forwarded-For or direct client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown_client"

        key = f"{self.scope}:{client_ip}"
        await limiter.check_rate_limit(
            key=key,
            max_requests=self.max_requests,
            window_seconds=self.window_seconds,
        )
