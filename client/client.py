import asyncio
import json
import os
from typing import Optional, Dict, Any
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
load_dotenv()  # load environment variables from .env

# class MCPClient:
#     def __init__(self):
#         # Initialize session and client objects
#         self.session: Optional[ClientSession] = None
#         self.exit_stack = AsyncExitStack()
#     # methods will go here
#     async def connect_to_server(self, server_script_path: str):
#         """Connect to an MCP server

#         Args:
#             server_script_path: Path to the server script (.py or .js)
#         """
#         is_python = server_script_path.endswith('.py')
#         is_js = server_script_path.endswith('.js')
#         if not (is_python or is_js):
#             raise ValueError("Server script must be a .py or .js file")

#         command = "python" if is_python else "node"
#         server_params = StdioServerParameters(
#             command=command,
#             args=[server_script_path],
#             env=None
#         )

#         stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
#         self.stdio, self.write = stdio_transport
#         self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

#         await self.session.initialize()

#         # List available tools
#         response = await self.session.list_tools()
#         tools = response.tools
#         print("\nConnected to server with tools:", [tool.name for tool in tools])

# async def main():
#     client = MCPClient()
#     await client.connect_to_server("/home/mohsen/scratch/ZenodoMCP/mcp-zenodo/server/server.py")
#     # You can add more client logic here if needed

# if __name__ == "__main__":
#     asyncio.run(main())

import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
load_dotenv()

async def main():
    server_script_path = "/home/mohsen/scratch/ZenodoMCP/mcp-zenodo/server/server.py"
    is_python = server_script_path.endswith('.py')
    is_js = server_script_path.endswith('.js')
    if not (is_python or is_js):
        raise ValueError("Server script must be a .py or .js file")

    command = "python" if is_python else "node"
    server_params = StdioServerParameters(
        command=command,
        args=[server_script_path],
        env=None
    )

    async with stdio_client(server_params) as (stdio, write):
        async with ClientSession(stdio, write) as session:
            await session.initialize()
            response = await session.list_tools()
            tools = response.tools
            print("\nConnected to server with tools:", [tool.name for tool in tools])
            # Add more client logic here if needed
            # Example:
            # result = await session.call_tool("search_records", {"query": "ExaData", "max_results": 1})
            # print(result)
            print("--------------------------------")
            result = await session.call_tool("get_citation", {"record_id": "10533504"})
            print(result)
            print("--------------------------------")
            result = await session.call_tool("get_record", {"record_id": "10533504"})
            print(result)
            print("--------------------------------")
            result = await session.call_tool("get_record_files", {"record_id": "10533504"})
            print(result)




if __name__ == "__main__":
    asyncio.run(main())

