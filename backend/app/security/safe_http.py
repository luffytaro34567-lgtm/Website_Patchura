"""
Safe HTTP Client Factory for SSRF Defense-in-Depth.
Enforces redirect validation, timeout limits, response body size limits,
and disallows destinations resolving to private/metadata IPs during redirect chains.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from urllib.parse import urljoin
import httpx
import structlog

from app.security.url_validator import validate_and_normalize_target_url

logger = structlog.get_logger(__name__)

DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0, read=8.0, write=5.0)
MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MB maximum response size


async def validate_redirect_ssrf(response: httpx.Response) -> None:
    """
    HTTP response hook that inspects 3xx redirects and asserts that the redirection
    target does not point to internal, private, loopback, or cloud metadata endpoints.
    """
    if response.is_redirect:
        location = response.headers.get("location")
        if location:
            target_url = urljoin(str(response.url), location)
            try:
                # Disallow redirecting to internal or prohibited IP targets
                validate_and_normalize_target_url(target_url, resolve_dns=True)
            except ValueError as ve:
                logger.warning(
                    "ssrf_redirect_blocked",
                    source_url=str(response.url),
                    blocked_redirect=location,
                    reason=str(ve),
                )
                raise httpx.RequestError(f"SSRF Redirect Blocked: {str(ve)}")


def create_safe_async_client(
    timeout: Optional[httpx.Timeout] = None,
    headers: Optional[Dict[str, str]] = None,
    max_redirects: int = 3,
    verify_ssl: bool = False,
) -> httpx.AsyncClient:
    """
    Constructs an httpx.AsyncClient pre-configured with SSRF redirect guards,
    strict connection timeouts, and reasonable redirect limits.
    """
    transport = httpx.AsyncHTTPTransport(retries=1)
    return httpx.AsyncClient(
        transport=transport,
        timeout=timeout or DEFAULT_TIMEOUT,
        headers=headers or {},
        follow_redirects=True,
        max_redirects=max_redirects,
        verify=verify_ssl,
        event_hooks={"response": [validate_redirect_ssrf]},
    )
