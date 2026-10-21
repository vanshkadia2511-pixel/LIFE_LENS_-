"""
LifeLens Ω — SSRF & Network Security Shield
Implementation Plan §36, §38

Protects against Server-Side Request Forgery (SSRF) when fetching external company URLs:
- Private IP address blocking (RFC 1918, Link-local, Cloud metadata)
- Protocol restrictions (HTTPS/HTTP only)
- DNS resolution validation
- Timeouts & response size limits
"""
from __future__ import annotations
import ipaddress
import socket
import urllib.parse
from dataclasses import dataclass
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Cloud metadata service IPs & reserved ranges (§38)
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("10.0.0.0/8"),        # Private RFC 1918
    ipaddress.ip_network("172.16.0.0/12"),     # Private RFC 1918
    ipaddress.ip_network("192.168.0.0/16"),    # Private RFC 1918
    ipaddress.ip_network("169.254.0.0/16"),    # Link-local / Cloud Metadata (169.254.169.254)
    ipaddress.ip_network("0.0.0.0/8"),         # Current network
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),          # IPv6 Unique local
    ipaddress.ip_network("fe80::/10"),         # IPv6 Link-local
]

_ALLOWED_SCHEMES = {"http", "https"}
_DEFAULT_TIMEOUT_SECONDS = 5.0
_MAX_RESPONSE_BYTES = 5 * 1024 * 1024  # 5 MB limit


@dataclass
class SSRFValidationResult:
    is_safe: bool
    url: str
    ip_address: Optional[str] = None
    reason: Optional[str] = None


class SSRFShield:
    """
    Validates external URLs to prevent SSRF vulnerabilities (§38).
    """

    @staticmethod
    def is_ip_blocked(ip_str: str) -> bool:
        """Check if an IP address belongs to a private, loopback, or cloud metadata network."""
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            for net in _BLOCKED_NETWORKS:
                if ip_obj in net:
                    return True
            return False
        except ValueError:
            return True  # Block unparseable IP addresses by default

    @classmethod
    def validate_url(cls, url: str) -> SSRFValidationResult:
        """
        Validate URL scheme, domain, and resolved IP against SSRF blocklists.
        """
        if not url or not url.strip():
            return SSRFValidationResult(is_safe=False, url=url, reason="URL is empty")

        parsed = urllib.parse.urlparse(url.strip())
        if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
            return SSRFValidationResult(
                is_safe=False, url=url, reason=f"Unsupported scheme '{parsed.scheme}'. Only HTTP/HTTPS allowed."
            )

        hostname = parsed.hostname
        if not hostname:
            return SSRFValidationResult(is_safe=False, url=url, reason="Missing hostname in URL")

        # Check raw IP literals
        try:
            ip_obj = ipaddress.ip_address(hostname)
            if cls.is_ip_blocked(str(ip_obj)):
                return SSRFValidationResult(
                    is_safe=False, url=url, ip_address=str(ip_obj), reason=f"IP '{ip_obj}' is in a restricted private/metadata range."
                )
            return SSRFValidationResult(is_safe=True, url=url, ip_address=str(ip_obj))
        except ValueError:
            # Hostname is a domain name — resolve DNS
            pass

        # Resolve DNS to verify all returned IP addresses
        try:
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            resolved_ips = list(set([info[4][0] for info in addr_info]))

            for ip_str in resolved_ips:
                if cls.is_ip_blocked(ip_str):
                    logger.warning("SSRF blocked URL '%s': Hostname '%s' resolved to private/metadata IP '%s'", url, hostname, ip_str)
                    return SSRFValidationResult(
                        is_safe=False, url=url, ip_address=ip_str, reason=f"Hostname '{hostname}' resolved to private IP '{ip_str}'."
                    )

            first_ip = resolved_ips[0] if resolved_ips else None
            return SSRFValidationResult(is_safe=True, url=url, ip_address=first_ip)

        except socket.gaierror as e:
            return SSRFValidationResult(is_safe=False, url=url, reason=f"DNS resolution failed for hostname '{hostname}': {str(e)}")
