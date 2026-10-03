"""Vercel ASGI entrypoint for the Humanity Score MCP server.

Vercel imports the module-level app object defined here. The MCP endpoint
remains available at /mcp; lightweight health routes make deployment checks
and browser verification straightforward.
"""

from __future__ import annotations

import os

from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

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

    # Vercel is the TLS-terminating reverse proxy and controls the public Host
    # header. If its system hostname variables are unavailable, disabling the
    # SDK's localhost-oriented rebinding check is the correct proxy setup.
    return TransportSecuritySettings(enable_dns_rebinding_protection=False)


async def health(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "ok": True,
            "service": "humanity-score-checker",
            "product_version": "3.1.0",
            "mcp_endpoint": "/mcp",
        }
    )


mcp.settings.transport_security = _transport_security()
app = mcp.streamable_http_app()
app.router.routes.append(Route("/", endpoint=health, methods=["GET"]))
app.router.routes.append(Route("/healthz", endpoint=health, methods=["GET"]))
