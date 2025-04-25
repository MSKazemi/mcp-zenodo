"""
Download tool implementation for Zenodo API.
"""

import os
import time
from typing import Dict, Any, Optional
from pathlib import Path
from models.request import DownloadRequest
from models.response import DownloadResponse
from server.zenodo_client import MCPZenodoClient
from .registry import tool

# Initialize the client and cache directory
_client = None
_cache_dir = os.path.join(os.path.expanduser("~"), ".zenodo_cache")

# Create cache directory if it doesn't exist
os.makedirs(_cache_dir, exist_ok=True)

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
    start_time = time.time()
    
    # Create request object
    request = DownloadRequest(
        record_id=record_id,
        file_name=file_name,
        force_download=force_download
    )
    
    # Get client and download file
    client = _get_client()
    response = await client.download_file(request)
    
    # Add query time to response
    response.query_time = time.time() - start_time
    
    return response 