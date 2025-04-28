import asyncio
from client.client import MCPZenodoClient
from dotenv import load_dotenv
import os

load_dotenv()


async def main():
    # Initialize the client
    async with MCPZenodoClient(
        base_url="http://localhost:8000",  # Optional: defaults to localhost:8000
        access_token= os.getenv("ZENODO_API_TOKEN")   # Optional: your Zenodo API token
    ) as client:
        try:
            # Example 1: Search for records
            print("Searching for records...")
            search_results = await client.search_records("machine learning")
            print(f"Found {len(search_results.get('hits', {}).get('hits', []))} records")

            # Example 2: Get metadata for a specific record
            record_id = "1234567"  # Replace with an actual record ID
            print(f"\nGetting metadata for record {record_id}...")
            metadata = await client.get_metadata(record_id)
            print(f"Record title: {metadata.get('metadata', {}).get('title')}")

            # Example 3: List available tools
            print("\nDiscovering available tools...")
            tools = await client.discover_tools()
            print("Available tools:")
            for tool in tools:
                print(f"- {tool.get('name')}: {tool.get('description')}")
                print(tool)

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())