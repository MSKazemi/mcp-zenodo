"""
Download tool implementation for Zenodo API.
"""

from models.response import DownloadResponse
from server.zenodo_client import MCPZenodoClient
from .registry import tool

_client = None

def _get_client() -> MCPZenodoClient:
    """Get or create the MCPZenodoClient instance.
    
    Returns:
        MCPZenodoClient instance
    """
    global _client
    if _client is None:
        _client = MCPZenodoClient()
    return _client

@tool(
    name="download_file",
    description="Downloads a specific file from a record",
    parameters={
        "type": "object",
        "properties": {
            "record_id": {
                "type": "string",
                "description": "The ID of the Zenodo record"
            },
            "file_name": {
                "type": "string",
                "description": "The name of the file to download"
            },
            "force_download": {
                "type": "boolean",
                "description": "Whether to force download even if cached",
                "default": False
            }
        },
        "required": ["record_id", "file_name"]
    }
)
async def download_file(
    record_id: str,
    file_name: str,
    force_download: bool = False
) -> DownloadResponse:
    """Download a specific file from a Zenodo record.
    
    Args:
        record_id: The ID of the Zenodo record
        file_name: The name of the file to download
        force_download: Whether to force download even if cached
        
    Returns:
        DownloadResponse containing the file path and metadata
    """
    client = _get_client()
    return await client.download_file(record_id, file_name, force_download)