"""
URL Validation and Server-Side Request Forgery (SSRF) Prevention Utility.
Ensures registered target websites are valid external HTTP/HTTPS addresses and
prohibits local, loopback, private RFC-1918, link-local, carrier-grade NAT,
and cloud metadata targets across both IPv4 and IPv6.
"""
from __future__ import annotations

import ipaddress
import re
import socket
from typing import Tuple, Union
from urllib.parse import urlparse


# Prohibited hostnames and domain keywords
PROHIBITED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
    "[::1]",
    "metadata.google.internal",
    "metadata.internal",
    "instance-data",
    "169.254.169.254",
}

# Special reserved or cloud metadata networks
CUSTOM_PROHIBITED_NETWORKS = [
    ipaddress.ip_network("169.254.0.0/16"),       # IPv4 link-local & cloud metadata
    ipaddress.ip_network("100.64.0.0/10"),        # Carrier Grade NAT
    ipaddress.ip_network("198.18.0.0/15"),        # Benchmark testing
    ipaddress.ip_network("192.0.0.0/24"),         # IETF protocol assignments
    ipaddress.ip_network("192.0.2.0/24"),         # TEST-NET-1
    ipaddress.ip_network("198.51.100.0/24"),      # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),       # TEST-NET-3
    ipaddress.ip_network("240.0.0.0/4"),          # Reserved
    ipaddress.ip_network("0.0.0.0/8"),            # Current network
    ipaddress.ip_network("fe80::/10"),            # IPv6 link-local
    ipaddress.ip_network("fc00::/7"),             # IPv6 unique local
    ipaddress.ip_network("::1/128"),              # IPv6 loopback
    ipaddress.ip_network("::/128"),               # IPv6 unspecified
]

PROHIBITED_PORTS = {22, 25, 111, 2375, 2376, 5432, 6379, 8080, 27017, 3306, 9200}


def is_ip_prohibited(ip: Union[ipaddress.IPv4Address, ipaddress.IPv6Address]) -> bool:
    """
    Checks if an IP address is internal, private, loopback, link-local, multicast,
    reserved, or designated for cloud instance metadata.
    """
    if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        return True

    # Handle IPv4-mapped IPv6 addresses (e.g. ::ffff:127.0.0.1)
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        if is_ip_prohibited(ip.ipv4_mapped):
            return True

    # Check custom prohibited network ranges
    for net in CUSTOM_PROHIBITED_NETWORKS:
        if ip in net:
            return True

    # Check exact cloud metadata IPs
    if str(ip) in ("169.254.169.254", "169.254.170.2"):
        return True

    return False


def resolve_and_validate_hostname(hostname: str) -> None:
    """
    Performs DNS resolution on a hostname and asserts that none of the resolved
    IP addresses (IPv4 or IPv6) fall within prohibited private/internal ranges.
    """
    try:
        # Resolve all addresses (both AF_INET and AF_INET6)
        addr_info = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in addr_info:
            ip_str = sockaddr[0]
            try:
                ip = ipaddress.ip_address(ip_str)
                if is_ip_prohibited(ip):
                    raise ValueError(
                        f"SSRF violation: Hostname '{hostname}' resolves to restricted internal IP address '{ip_str}'."
                    )
            except ValueError as ve:
                if "SSRF violation" in str(ve):
                    raise
    except socket.gaierror:
        # Domain resolution failed or offline environment: allow regex-validated domain
        pass


def validate_and_normalize_target_url(raw_url: str, resolve_dns: bool = True) -> Tuple[str, str]:
    """
    Validates and normalizes a website target URL with comprehensive SSRF defenses.
    Returns:
        tuple[normalized_url, domain]
    Raises:
        ValueError if the URL is invalid, non-HTTP/HTTPS, or violates SSRF rules.
    """
    if not raw_url or not isinstance(raw_url, str):
        raise ValueError("Target URL cannot be empty.")

    trimmed = raw_url.strip()
    if not trimmed:
        raise ValueError("Target URL cannot be empty whitespace.")

    # Automatically prefix https:// if protocol is omitted
    if not trimmed.startswith(("http://", "https://")):
        trimmed = f"https://{trimmed}"

    parsed = urlparse(trimmed)

    # 1. Scheme check (strictly HTTP/HTTPS)
    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError("Target website protocol must be HTTP or HTTPS.")

    # 2. Hostname check
    hostname = parsed.hostname
    if not hostname:
        raise ValueError("Invalid target URL: missing domain or host.")

    hostname_lower = hostname.lower()

    if hostname_lower in PROHIBITED_HOSTNAMES:
        raise ValueError(f"Targeting '{hostname_lower}' or loopback/metadata addresses is strictly prohibited.")

    # 3. Disallow dangerous internal service ports
    if parsed.port and parsed.port in PROHIBITED_PORTS:
        raise ValueError(f"Port {parsed.port} is reserved for internal services and cannot be registered as a web target.")

    # 4. Check if hostname is an IP literal
    try:
        ip = ipaddress.ip_address(hostname_lower)
        if is_ip_prohibited(ip):
            raise ValueError(
                f"Targeting internal, private, loopback, or cloud metadata IP addresses ('{ip}') is strictly prohibited."
            )
    except ValueError as e:
        if "strictly prohibited" in str(e):
            raise
        # Not a raw IP literal; validate domain format
        if not re.match(r"^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$", hostname_lower):
            raise ValueError(f"'{hostname}' is not a valid fully-qualified domain name.")

        # Resolve DNS and verify resolved addresses if enabled
        if resolve_dns:
            resolve_and_validate_hostname(hostname_lower)

    # Construct normalized base URL (scheme + netloc)
    normalized_url = f"{parsed.scheme.lower()}://{parsed.netloc}"

    return normalized_url, hostname_lower


def validate_target_url(raw_url: str, resolve_dns: bool = True) -> Tuple[str, str]:
    """Compatibility alias for validate_and_normalize_target_url."""
    return validate_and_normalize_target_url(raw_url, resolve_dns=resolve_dns)
