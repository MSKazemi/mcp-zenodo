"""Stdio MCP server for Zenodo (Cursor IDE, Claude Desktop).

The tools are implemented once, in ``mcp_api``; this module exposes them over
stdio, so both entry points offer the same tools and behave the same way.
Keep the whole repository checked out: this server imports from ``mcp_api``.
"""

import inspect
import logging
import sys
from pathlib import Path
from typing import Annotated, Any, Callable, Dict

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "mcp_api"))

from mcp.server.fastmcp import FastMCP  # noqa: E402
from pydantic import Field  # noqa: E402

import server.tools  # noqa: E402,F401  (importing registers the tools)
from server.tools.registry import get_tool_registry  # noqa: E402

# Logs go to stderr; stdout carries the MCP protocol
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("zenodo_mcp")

mcp = FastMCP("Zenodo")


def _with_descriptions(entry: Dict[str, Any]) -> Callable:
    """Wrap a registered tool so FastMCP sees its parameter descriptions.

    FastMCP builds each input schema from the function signature alone.
    """
    function = entry["function"]
    properties = entry["parameters"]["properties"]
    signature = inspect.signature(function)

    async def call(**arguments):
        return await function(**arguments)

    call.__name__ = entry["name"]
    call.__signature__ = signature.replace(parameters=[
        parameter.replace(annotation=Annotated[
            parameter.annotation,
            Field(description=properties[name]["description"]),
        ])
        for name, parameter in signature.parameters.items()
    ])
    return call


for entry in get_tool_registry().values():
    mcp.add_tool(
        _with_descriptions(entry), name=entry["name"], description=entry["description"]
    )


if __name__ == "__main__":
    logger.info("Starting Zenodo MCP server")
    mcp.run(transport="stdio")
