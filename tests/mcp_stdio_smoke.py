"""Verify Humanity Score MCP over stdio."""

from __future__ import annotations

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

EXPECTED_TOOLS = {
    "audit_product",
    "score_product",
    "generate_badge",
    "generate_viral_teardown",
}


async def main() -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["server.py", "--transport", "stdio"],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            names = {tool.name for tool in result.tools}
            missing = EXPECTED_TOOLS - names
            if missing:
                raise SystemExit(f"Missing stdio tools: {sorted(missing)}")
            print("Detected stdio tools:", sorted(names))


if __name__ == "__main__":
    asyncio.run(main())
