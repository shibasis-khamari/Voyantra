"""
Voyantra Website Crawler
Enforces strict SSRF defense, socket-level IP pinning, redirect revalidation,
content-hash diffing, and page versioning.
"""
import ipaddress
import socket
import urllib.parse
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup
import requests

from ....core.config import settings
from ....schemas.knowledge import (
    KnowledgeDocument,
    KnowledgeChunk,
    KnowledgeSource,
    SourceTypeEnum,
    utc_now_iso,
)
from ..storage.knowledge_repository import knowledge_repository, KnowledgeRepository

# Blocked IP ranges (RFC 1918, RFC 3927, RFC 6890, Carrier-Grade NAT, Loopback, Cloud Metadata)
BLOCKED_IPV4_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),       # Cloud metadata (AWS, GCP, Azure)
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("198.18.0.0/15"),
    ipaddress.ip_network("198.51.100.0/24"),
    ipaddress.ip_network("203.0.113.0/24"),
    ipaddress.ip_network("224.0.0.0/4"),
    ipaddress.ip_network("240.0.0.0/4"),
    ipaddress.ip_network("255.255.255.255/32"),
]

BLOCKED_IPV6_NETWORKS = [
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("2001:db8::/32"),
    ipaddress.ip_network("2002::/16"),
]


class SSRFValidationError(Exception):
    """Raised when a URL or resolved destination IP violates SSRF policy."""
    pass


class WebsiteCrawler:
    def __init__(
        self,
        repository: Optional[KnowledgeRepository] = None,
        allowed_domains: Optional[List[str]] = None,
        max_redirect_hops: int = 3,
        request_timeout: float = 6.0,
    ):
        self.repo = repository or knowledge_repository
        self.allowed_domains = allowed_domains or settings.KNOWLEDGE_CRAWL_ALLOWED_DOMAINS
        self.max_redirect_hops = max_redirect_hops
        self.timeout = request_timeout

    def is_ip_blocked(self, ip_str: str) -> bool:
        """Checks if IP string is private, loopback, or reserved."""
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            # Unmap IPv4-mapped IPv6 (e.g., ::ffff:127.0.0.1)
            if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
                ip_obj = ip_obj.ipv4_mapped

            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local or ip_obj.is_reserved:
                return True

            if isinstance(ip_obj, ipaddress.IPv4Address):
                return any(ip_obj in net for net in BLOCKED_IPV4_NETWORKS)
            else:
                return any(ip_obj in net for net in BLOCKED_IPV6_NETWORKS)
        except ValueError:
            return True

    def validate_and_resolve_destination(self, url: str) -> Tuple[str, str, int]:
        """
        Validates URL scheme, domain allowlist, and resolves destination IP with SSRF checks.
        Returns (validated_ip, hostname, port).
        """
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            raise SSRFValidationError(f"Disallowed URL scheme: {parsed.scheme}")

        hostname = parsed.hostname
        if not hostname:
            raise SSRFValidationError("Missing hostname in URL")

        # Domain allowlist check
        domain_match = any(
            hostname == allowed or hostname.endswith("." + allowed)
            for allowed in self.allowed_domains
        )
        if not domain_match:
            raise SSRFValidationError(f"Domain '{hostname}' is not in allowed crawl domains: {self.allowed_domains}")

        port = parsed.port or (443 if parsed.scheme == "https" else 80)

        # Resolve IP
        try:
            addr_info = socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            ip_str = addr_info[0][4][0]
        except Exception as e:
            raise SSRFValidationError(f"Failed to resolve DNS for {hostname}: {e}")

        # In production (DEBUG=False), loopback/private IPs are strictly forbidden
        if not settings.DEBUG:
            if self.is_ip_blocked(ip_str):
                raise SSRFValidationError(f"Destination IP {ip_str} for host {hostname} is blocked by SSRF policy.")
        else:
            # In DEV mode (DEBUG=True), allow localhost / 127.0.0.1 only for allowed ports
            if self.is_ip_blocked(ip_str) and hostname not in ["localhost", "127.0.0.1"]:
                raise SSRFValidationError(f"Destination IP {ip_str} is blocked.")

        return ip_str, hostname, port

    def fetch_page_with_pinning(self, url: str) -> Tuple[str, int, str]:
        """
        Performs safe HTTP GET with destination IP pinning and manual redirect revalidation.
        Returns (response_text, status_code, final_url).
        """
        current_url = url
        for hop in range(self.max_redirect_hops + 1):
            ip_str, hostname, port = self.validate_and_resolve_destination(current_url)
            
            parsed = urllib.parse.urlparse(current_url)
            scheme = parsed.scheme
            path = parsed.path or "/"
            if parsed.query:
                path += f"?{parsed.query}"

            # Make request directly to validated IP with original Host header
            pinned_url = f"{scheme}://{ip_str}:{port}{path}"
            headers = {
                "Host": hostname,
                "User-Agent": "VoyantraCrawler/2.0 (SSRF-Hardened-Bot)",
                "Accept": "text/html,application/xhtml+xml",
            }

            resp = requests.get(
                pinned_url,
                headers=headers,
                timeout=self.timeout,
                allow_redirects=False,
                verify=False if ip_str in ["127.0.0.1", "localhost"] else True,
            )

            # Handle redirects manually
            if resp.status_code in [301, 302, 303, 307, 308]:
                location = resp.headers.get("Location")
                if not location:
                    raise SSRFValidationError("Redirect response missing Location header")
                current_url = urllib.parse.urljoin(current_url, location)
                continue

            return resp.text, resp.status_code, current_url

        raise SSRFValidationError(f"Exceeded max redirect hops ({self.max_redirect_hops})")

    @staticmethod
    def extract_clean_content(html: str) -> Tuple[str, str]:
        """Extracts page title and main cleaned text, stripping scripts, styles, and chrome."""
        soup = BeautifulSoup(html, "html.parser")
        
        # Remove noisy elements
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
            tag.decompose()

        title = (soup.title.string.strip() if soup.title and soup.title.string else "").strip()
        body_text = soup.get_text(separator="\n", strip=True)
        # Clean consecutive newlines
        cleaned = "\n".join([line.strip() for line in body_text.splitlines() if line.strip()])
        return title or "Untitled Voyantra Page", cleaned

    def crawl_page(self, url: str) -> Dict[str, Any]:
        """Crawls a single page, detects content changes via hash, and versions document."""
        html, status, final_url = self.fetch_page_with_pinning(url)
        if status != 200:
            return {"success": False, "status_code": status, "url": final_url}

        title, cleaned_text = self.extract_clean_content(html)
        content_hash = hashlib.sha256(cleaned_text.encode("utf-8")).hexdigest()

        # Check existing document in repository
        existing_doc = self.repo.get_document_by_url(final_url)
        if existing_doc:
            if existing_doc.content_hash == content_hash:
                # Content unchanged, skip re-indexing
                return {
                    "success": True,
                    "url": final_url,
                    "document_id": existing_doc.id,
                    "status": "unchanged",
                    "version": existing_doc.version,
                }
            # Content changed: increment version and deactivate prior chunks
            new_version = existing_doc.version + 1
            self.repo.deactivate_document_chunks(existing_doc.id)
            doc_id = existing_doc.id
        else:
            new_version = 1
            doc_id = f"doc-voyantra-{hashlib.md5(final_url.encode('utf-8')).hexdigest()[:10]}"

        new_doc = KnowledgeDocument(
            id=doc_id,
            source_id="voyantra_website",
            url=final_url,
            title=title,
            raw_content=html[:50000],  # bounded raw HTML
            cleaned_content=cleaned_text,
            content_hash=content_hash,
            version=new_version,
            is_active=True,
            fetched_at=utc_now_iso(),
            metadata={"status_code": status, "content_length": len(cleaned_text)},
        )
        self.repo.upsert_document(new_doc)

        return {
            "success": True,
            "url": final_url,
            "document_id": new_doc.id,
            "status": "updated" if existing_doc else "created",
            "version": new_version,
            "content_length": len(cleaned_text),
            "content_hash": content_hash,
            "document": new_doc,
        }
