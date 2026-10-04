"""Vercel ASGI entrypoint for the Humanity Score MCP server.

The direct HTTP MCP endpoint is fail-closed: set HUMANITY_SCORE_API_KEY in
Vercel before using /mcp. MCPMarket's managed stdio deployment is unaffected.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque

from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from core import PRODUCT_VERSION, RUBRIC_VERSION
from provenance import signing_metadata
from server import mcp


def _split_env_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _vercel_hosts() -> list[str]:
    hosts: list[str] = []
    for name in ("VERCEL_URL", "VERCEL_PROJECT_PRODUCTION_URL", "VERCEL_BRANCH_URL"):
        value = os.getenv(name, "").strip()
        if value:
            value = value.removeprefix("https://").removeprefix("http://").rstrip("/")
            if value and value not in hosts:
                hosts.append(value)
    return hosts


def _transport_security() -> TransportSecuritySettings:
    allowed_hosts = _split_env_list(os.getenv("MCP_ALLOWED_HOSTS"))
    allowed_origins = _split_env_list(os.getenv("MCP_ALLOWED_ORIGINS"))

    for host in _vercel_hosts():
        if host not in allowed_hosts:
            allowed_hosts.append(host)
        wildcard_port = f"{host}:*"
        if wildcard_port not in allowed_hosts:
            allowed_hosts.append(wildcard_port)
        origin = f"https://{host}"
        if origin not in allowed_origins:
            allowed_origins.append(origin)

    if allowed_hosts:
        return TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=allowed_hosts,
            allowed_origins=allowed_origins,
        )

    return TransportSecuritySettings(enable_dns_rebinding_protection=False)


async def health(_: Request) -> JSONResponse:
    signing = signing_metadata()
    api_key_configured = bool(os.getenv("HUMANITY_SCORE_API_KEY", "").strip())
    return JSONResponse(
        {
            "ok": True,
            "service": "humanity-score-checker",
            "product_version": PRODUCT_VERSION,
            "rubric_version": RUBRIC_VERSION,
            "mcp_endpoint": "/mcp",
            "http_auth_configured": api_key_configured,
            "provenance_signing_configured": bool(signing.get("configured")),
            "rate_limit_scope": "process_local_only",
            "production_ready_for_private_or_low_volume_http": (
                api_key_configured and bool(signing.get("configured"))
            ),
            "production_note": (
                "Use platform-level/global rate limiting before exposing this HTTP endpoint "
                "to high-volume public traffic."
            ),
        }
    )


mcp.settings.transport_security = _transport_security()
app = mcp.streamable_http_app()
app.router.routes.append(Route("/", endpoint=health, methods=["GET"]))
app.router.routes.append(Route("/healthz", endpoint=health, methods=["GET"]))

_REQUESTS: dict[str, deque[float]] = defaultdict(deque)


async def protect_mcp(request: Request, call_next):
    if not request.url.path.startswith("/mcp"):
        return await call_next(request)

    expected = os.getenv("HUMANITY_SCORE_API_KEY", "").strip()
    if not expected:
        return JSONResponse(
            {
                "error": "http_mcp_not_configured",
                "message": "Set HUMANITY_SCORE_API_KEY before exposing the direct HTTP MCP endpoint.",
            },
            status_code=503,
        )

    supplied = request.headers.get("authorization", "")
    if supplied.lower().startswith("bearer "):
        supplied = supplied[7:].strip()
    else:
        supplied = request.headers.get("x-api-key", "").strip()

    import hmac
    if not supplied or not hmac.compare_digest(supplied, expected):
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    try:
        limit = int(os.getenv("HUMANITY_SCORE_RATE_LIMIT_PER_MINUTE", "60"))
    except ValueError:
        limit = 60
    limit = max(1, min(limit, 600))

    now = time.monotonic()
    key = supplied
    bucket = _REQUESTS[key]
    while bucket and now - bucket[0] >= 60:
        bucket.popleft()
    if len(bucket) >= limit:
        return JSONResponse(
            {"error": "rate_limited", "retry_after_seconds": 60},
            status_code=429,
            headers={"Retry-After": "60"},
        )
    bucket.append(now)

    return await call_next(request)


app.add_middleware(BaseHTTPMiddleware, dispatch=protect_mcp)
