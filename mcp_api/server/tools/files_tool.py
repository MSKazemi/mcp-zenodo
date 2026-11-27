"""
Tool for listing files in Zenodo records.
"""

from typing import Dict, Any
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
    name="list_files",
    description="Lists available files in a Zenodo record",
    parameters={
        "type": "object",
        "properties": {
            "record_id": {
                "type": "string",
                "description": "The ID of the Zenodo record"
            },
            "include_metadata": {
                "type": "boolean",
                "description": "Whether to include file metadata",
                "default": True
            }
        },
        "required": ["record_id"]
    }
)
async def list_files(record_id: str, include_metadata: bool = True) -> Dict[str, Any]:
    """List all files available in a Zenodo record.
    
    Args:
        record_id: The ID of the Zenodo record
        include_metadata: Whether to include file metadata
        
    Returns:
        Dictionary containing the list of files and their metadata
    """
    client = _get_client()
    
    # Get the record metadata which includes file information
    record = await client.get_metadata(record_id)
    
    # Extract file information
    files = []
    if "files" in record:
        for file_info in record["files"]:
            links = file_info.get("links", {})
            file_data = {
                # The records API names files "key"; "filename" is the deposit API.
                "filename": file_info.get("key") or file_info.get("filename", ""),
                "size": file_info.get("size", 0),
                "type": file_info.get("type", ""),
                "download_url": links.get("download") or links.get("self", "")
            }
            
            # Add additional metadata if requested
            if include_metadata:
                file_data["checksum"] = file_info.get("checksum", "")
                file_data["file_type"] = file_info.get("type", "")
                file_data["mime_type"] = file_info.get("mime_type", "")
            
            files.append(file_data)
    
    # Return the file list
    return {
        "record_id": record_id,
        "files": files,
        "total_count": len(files)
    } 