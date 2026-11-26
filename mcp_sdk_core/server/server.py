"""Stdio MCP server for Zenodo (Cursor IDE, Claude Desktop).

The tools are implemented once, in ``mcp_api``; this module exposes them over
stdio, so both entry points offer the same tools and behave the same way.
Keep the whole repository checked out: this server imports from ``mcp_api``.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mcp_api"))

from mcp.server.fastmcp import FastMCP  # noqa: E402

import server.tools  # noqa: E402,F401  (importing registers the tools)
from server.tools.registry import get_tool_registry  # noqa: E402

# Logs go to stderr; stdout carries the MCP protocol
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("zenodo_mcp")

mcp = FastMCP("Zenodo")

for entry in get_tool_registry().values():
    mcp.add_tool(entry["function"], name=entry["name"], description=entry["description"])


if __name__ == "__main__":
    logger.info("Starting Zenodo MCP server")
    mcp.run(transport="stdio")
