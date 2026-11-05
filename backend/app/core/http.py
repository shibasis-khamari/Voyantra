"""HTTP helpers shared by routers."""
from fastapi import Request
from .config import settings


def get_client_ip(request: Request) -> str:
    """
    Best-effort client IP for rate limiting.

    Behind a reverse proxy / load balancer, request.client.host is the proxy's
    address, so every user would share one rate-limit bucket. When
    TRUST_PROXY_HEADERS=true we use the left-most X-Forwarded-For entry.

    Only enable that when the app is reachable *only* through your proxy;
    otherwise clients can spoof the header and dodge rate limits.
    """
    if settings.TRUST_PROXY_HEADERS:
        forwarded = request.headers.get("x-forwarded-for", "")
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    return request.client.host if request.client else "127.0.0.1"
