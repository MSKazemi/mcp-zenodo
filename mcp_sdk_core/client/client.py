import asyncio
import json
import os
from typing import Optional, Dict, Any
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from dotenv import load_dotenv
load_dotenv()  # load environment variables from .env


async def main():
    server_script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "server", "server.py")
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

            # Example record IDs for testing
            test_records = {
                "dataset": "10533504",  # Example dataset record
                "publication": "10050368"  # Example publication record
            }

            # Test each available tool with proper error handling
            async def test_tool(tool_name, params):
                try:
                    print(f"\nTesting {tool_name}...")
                    result = await session.call_tool(tool_name, params)
                    print(f"Success! Response:\n{result}\n")
                    return result
                except Exception as e:
                    print(f"Error testing {tool_name}: {str(e)}\n")
                    return None

            # Test metadata retrieval
            await test_tool("get_metadata", {"record_id": test_records["dataset"]})

            # Test citation generation
            await test_tool("get_citation", {
                "record_id": test_records["publication"],
                "format": "bibtex"
            })

            # Test file operations
            await test_tool("list_files", {"record_id": test_records["dataset"]})
            

            # Test search functionality
            await test_tool("search_records", {
                "query": "ExaData Marconi 100 Datacenter",
                "max_results": 5
            })

            # Test related records
            await test_tool("get_related_records", {"record_id": test_records["dataset"]})





if __name__ == "__main__":
    asyncio.run(main())

