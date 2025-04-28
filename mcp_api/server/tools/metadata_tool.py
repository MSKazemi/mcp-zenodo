"""
Metadata tool implementation for Zenodo API.
"""

from typing import Dict, Any, Optional
import time
from models.request import MetadataRequest
from models.response import MetadataResponse
from server.zenodo_client import MCPZenodoClient
from .registry import tool

# Initialize the client
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
    name="get_metadata",
    description="Retrieves detailed metadata of a Zenodo record",
    parameters={
        "type": "object",
        "properties": {
            "record_id": {
                "type": "string",
                "description": "The ID of the Zenodo record"
            },
            "include_files": {
                "type": "boolean",
                "description": "Whether to include file information",
                "default": True
            },
            "include_versions": {
                "type": "boolean",
                "description": "Whether to include version information",
                "default": True
            }
        },
        "required": ["record_id"]
    }
)
async def get_metadata(
    record_id: str,
    include_files: bool = True,
    include_versions: bool = True
) -> MetadataResponse:
    """Retrieve detailed metadata for a Zenodo record.
    
    Args:
        record_id: The ID of the Zenodo record
        include_files: Whether to include file information
        include_versions: Whether to include version information
        
    Returns:
        MetadataResponse containing the record metadata
    """
    start_time = time.time()
    
    # Create request object
    request = MetadataRequest(
        record_id=record_id,
        include_files=include_files,
        include_versions=include_versions
    )
    
    # Get client and retrieve metadata
    client = _get_client()
    response = await client.get_metadata(request)
    
    # Add query time to response
    response.query_time = time.time() - start_time
    
    return response 