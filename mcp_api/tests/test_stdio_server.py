"""The stdio MCP server, driven by a real MCP client (issue #5)."""

import sys
import tempfile
from pathlib import Path
from unittest import IsolatedAsyncioTestCase

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from zenodo_stub import TOOL_NAMES, start_stub

SERVER = Path(__file__).resolve().parents[2] / "mcp_sdk_core" / "server" / "server.py"
ARGUMENTS = {
    "search_records": {"query": "ocean"},
    "compare_records": {"record_ids": ["1", "2"]},
    "download_file": {"record_id": "1", "file_name": "data.csv"},
}


class StdioServerTests(IsolatedAsyncioTestCase):
    async def test_every_tool_works_over_stdio(self):
        origin = await start_stub(self.addAsyncCleanup)
        home = tempfile.TemporaryDirectory()
        self.addCleanup(home.cleanup)
        parameters = StdioServerParameters(
            command=sys.executable,
            args=[str(SERVER)],
            env={
                "HOME": home.name,
                "ZENODO_API_URL": f"{origin}/api",
                "ZENODO_API_TOKEN": "test-token",
                "ZENODO_SANDBOX": "false",
            },
            cwd=home.name,
        )
        async with stdio_client(parameters) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = (await session.list_tools()).tools
                self.assertEqual({tool.name for tool in tools}, TOOL_NAMES)
                undescribed = [
                    f"{tool.name}.{name}"
                    for tool in tools
                    for name, schema in tool.inputSchema["properties"].items()
                    if not schema.get("description")
                ]
                self.assertEqual(undescribed, [])
                for tool in tools:
                    arguments = ARGUMENTS.get(tool.name, {"record_id": "1"})
                    with self.subTest(tool=tool.name):
                        result = await session.call_tool(tool.name, arguments)
                        text = result.content[0].text
                        self.assertFalse(result.isError, text)
                        self.assertNotIn('"error": "', text)
                refused = await session.call_tool(
                    "get_metadata", {"record_id": "../deposit/depositions"}
                )
                self.assertTrue(refused.isError)
