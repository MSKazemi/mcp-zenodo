"""
Access control for the HTTP service.

The service acts with the operator's Zenodo token and writes downloads to disk,
so it must not be open to whoever can reach the port:

* with ``MCP_API_KEY`` set, every request needs ``Authorization: Bearer <key>``;
* without it, only requests made from this machine to a local host name pass.

Both checks apply per request, so they hold however the ASGI server was bound.
"""

import ipaddress
import secrets
from typing import Optional
from urllib.parse import urlsplit

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import config

LOCAL_HOST_NAMES = {"localhost", "127.0.0.1", "::1"}
bearer_security = HTTPBearer(auto_error=False)


def _is_loopback(address: Optional[str]) -> bool:
    try:
        parsed = ipaddress.ip_address(address or "")
    except ValueError:
        return False
    mapped = getattr(parsed, "ipv4_mapped", None)
    return (mapped or parsed).is_loopback


def _origin_allowed(origin: str, host_header: str) -> bool:
    if urlsplit(origin).netloc == host_header:
        return True  # Same origin, such as the bundled /docs page
    if origin in config.cors_origins:
        return True
    # A wildcard would let any web page use a keyless local server
    return "*" in config.cors_origins and bool(config.api_key)


async def require_access(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_security),
) -> None:
    """Reject requests that are not entitled to use this server."""
    host_header = request.headers.get("host", "")

    # Browsers can send some cross-site requests without asking first
    origin = request.headers.get("origin")
    if origin and not _origin_allowed(origin, host_header):
        raise HTTPException(status_code=403, detail="Origin not allowed")

    if config.api_key:
        if credentials is None or not secrets.compare_digest(
            credentials.credentials.encode(), config.api_key.encode()
        ):
            raise HTTPException(
                status_code=401,
                detail="Missing or invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return

    client = request.client.host if request.client else None
    # The host name check stops DNS rebinding and local reverse proxies
    if not _is_loopback(client) or urlsplit(f"//{host_header}").hostname not in LOCAL_HOST_NAMES:
        raise HTTPException(
            status_code=403,
            detail="Set MCP_API_KEY to use this server from anywhere but this machine",
        )
