"""
Target Website Ownership Verification Service.
Executes non-invasive verification checks (HTTP file token, HTML meta-tag, DNS challenge).
All verification attempts are recorded with timestamp and detailed diagnostic feedback.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Tuple
import httpx
import structlog

from app.models.website import VerificationMethod, VerificationStatus, Website
from app.security.safe_http import create_safe_async_client

logger = structlog.get_logger(__name__)


class VerificationService:
    @staticmethod
    async def verify_website_ownership(website: Website) -> Tuple[bool, str]:
        """
        Executes the designated ownership verification check against the target.
        Returns:
            tuple[is_verified: bool, message: str]
        """
        method = website.verification_method
        target_url = website.target_url.rstrip("/")
        token = website.verification_token

        logger.info(
            "Initiating website ownership verification",
            website_id=website.id,
            target_url=target_url,
            method=method,
        )

        try:
            if method == VerificationMethod.FILE.value:
                return await VerificationService._verify_file_token(target_url, token)
            elif method == VerificationMethod.META_TAG.value:
                return await VerificationService._verify_meta_tag(target_url, token)
            elif method == VerificationMethod.DNS_TXT.value:
                return await VerificationService._verify_dns_txt(website.domain, token)
            else:
                return False, f"Unsupported verification method: {method}"
        except httpx.ConnectTimeout:
            return False, "Connection timed out while attempting to reach target server."
        except httpx.ConnectError:
            return False, "Could not establish connection to target server. Ensure domain resolves and server is online."
        except Exception as exc:
            logger.warning("Verification error", error=str(exc))
            return False, f"Verification failed: {str(exc)}"

    @staticmethod
    async def _verify_file_token(target_url: str, token: str) -> Tuple[bool, str]:
        # Support dual verification paths: prefer PATCHORA, fallback to legacy BugHunter
        paths_to_check = [
            f"{target_url}/.well-known/patchora-verification.txt",
            f"{target_url}/.well-known/bughunter-verification.txt",
        ]

        async with create_safe_async_client(
            timeout=httpx.Timeout(8.0, connect=4.0),
            headers={"User-Agent": "PATCHORA-Ownership-Verifier/1.0 (+https://patchora.io/verification-bot)"},
        ) as client:
            last_err = ""
            for verification_path in paths_to_check:
                try:
                    resp = await client.get(verification_path)
                    if resp.status_code == 200:
                        content = resp.text.strip()
                        if token in content:
                            return True, "Ownership verified successfully via HTTP file token."
                        else:
                            last_err = f"File found at {verification_path}, but did not contain the expected token '{token}'."
                    else:
                        last_err = f"Verification file returned HTTP {resp.status_code} at {verification_path}."
                except Exception as exc:
                    last_err = f"Could not reach {verification_path}: {exc}"

            return False, last_err or "Verification file not found at /.well-known/patchora-verification.txt (or legacy bughunter-verification.txt)."

    @staticmethod
    async def _verify_meta_tag(target_url: str, token: str) -> Tuple[bool, str]:
        async with create_safe_async_client(
            timeout=httpx.Timeout(8.0, connect=4.0),
            headers={"User-Agent": "PATCHORA-Ownership-Verifier/1.0 (+https://patchora.io/verification-bot)"},
        ) as client:
            resp = await client.get(target_url)

            if resp.status_code != 200:
                return False, f"Homepage returned HTTP {resp.status_code}. Expected HTTP 200."

            html = resp.text
            # Regex for <meta name="patchora-verification" content="token"> or legacy <meta name="bughunter-verification" content="token">
            names = ["patchora-verification", "bughunter-verification"]
            for name in names:
                pattern = rf'<meta\s+[^>]*name=["\']{re.escape(name)}["\'][^>]*content=["\']{re.escape(token)}["\']'
                alt_pattern = rf'<meta\s+[^>]*content=["\']{re.escape(token)}["\'][^>]*name=["\']{re.escape(name)}["\']'
                if re.search(pattern, html, re.IGNORECASE) or re.search(alt_pattern, html, re.IGNORECASE):
                    return True, "Ownership verified successfully via HTML meta tag."

            return False, "Homepage reached, but required <meta name='patchora-verification' content='...'> (or legacy bughunter-verification) tag was not found."

    @staticmethod
    async def _verify_dns_txt(domain: str, token: str) -> Tuple[bool, str]:
        """
        DNS TXT challenge verification for _patchora-challenge.<domain> (or legacy _bughunter-challenge.<domain>).
        Checks for token in DNS TXT record.
        """
        try:
            import dns.resolver
            record_names = [f"_patchora-challenge.{domain}", f"_bughunter-challenge.{domain}"]
            for record_name in record_names:
                try:
                    answers = dns.resolver.resolve(record_name, "TXT")
                    for rdata in answers:
                        txt_string = "".join([t.decode("utf-8") if isinstance(t, bytes) else str(t) for t in rdata.strings])
                        if token in txt_string:
                            return True, "Ownership verified successfully via DNS TXT record."
                except Exception:
                    continue
            return False, f"DNS TXT record found neither at '_patchora-challenge.{domain}' nor '_bughunter-challenge.{domain}' with expected token."
        except Exception:
            # Fallback message when dnspython resolver is unconfigured or record not found
            return False, f"DNS TXT challenge could not be resolved for '_patchora-challenge.{domain}' or '_bughunter-challenge.{domain}'. Ensure the TXT record has propagated."
