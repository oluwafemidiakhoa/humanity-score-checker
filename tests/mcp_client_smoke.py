"""End-to-end MCP Streamable HTTP discovery smoke test."""

from __future__ import annotations

import asyncio
import sys
import time

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

EXPECTED_TOOLS = {
    "audit_product",
    "score_product",
    "generate_badge",
    "generate_viral_teardown",
}


async def discover(url: str) -> set[str]:
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return {tool.name for tool in result.tools}


async def main() -> None:
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/mcp"
    last_error: Exception | None = None

    for _ in range(30):
        try:
            names = await discover(url)
            missing = EXPECTED_TOOLS - names
            if missing:
                raise RuntimeError(f"Missing tools: {sorted(missing)}")
            print("Detected tools:", sorted(names))
            return
        except Exception as exc:
            last_error = exc
            await asyncio.sleep(1)

    raise SystemExit(f"MCP discovery failed for {url}: {last_error}")


if __name__ == "__main__":
    asyncio.run(main())
