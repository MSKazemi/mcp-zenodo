"""
Summarize tool implementation for Zenodo API.
"""

import time
from typing import Dict, Any, Optional
from models.request import SummarizeRequest
from models.response import SummarizeResponse
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

def _format_summary(summary_dict: Dict[str, Any]) -> str:
    """Format the summary dictionary into a readable string.
    
    Args:
        summary_dict: Dictionary containing summary information
        
    Returns:
        Formatted summary string
    """
    lines = []
    
    # Add title
    lines.append(f"Title: {summary_dict['title']}")
    
    # Add description
    lines.append(f"\nDescription: {summary_dict['summary_text']}")
    
    # Add publication date
    lines.append(f"\nPublication Date: {summary_dict['publication_date']}")
    
    # Add resource type
    if isinstance(summary_dict['resource_type'], dict):
        resource_type = summary_dict['resource_type'].get('title', '')
    else:
        resource_type = str(summary_dict['resource_type'])
    lines.append(f"Resource Type: {resource_type}")
    
    # Add access right
    lines.append(f"Access Right: {summary_dict['access_right']}")
    
    # Add creators
    creators = [f"{c.get('name', '')}" for c in summary_dict['creators']]
    lines.append(f"Creators: {', '.join(creators)}")
    
    # Add file information if present
    if 'files' in summary_dict:
        files = summary_dict['files']
        lines.append(f"\nFiles:")
        lines.append(f"- Count: {files['count']}")
        lines.append(f"- Total Size: {files['total_size']} bytes")
        lines.append(f"- File Types: {', '.join(files['file_types'])}")
    
    # Add version information if present
    if 'versions' in summary_dict:
        versions = summary_dict['versions']
        lines.append(f"\nVersions:")
        lines.append(f"- Count: {versions['count']}")
        lines.append(f"- Latest Version: {'Yes' if versions['is_latest'] else 'No'}")
        if versions['parent_id']:
            lines.append(f"- Parent ID: {versions['parent_id']}")
    
    return "\n".join(lines)

@tool(
    name="summarize_record",
    description="Generates a summary from a Zenodo record's metadata",
    parameters={
        "type": "object",
        "properties": {
            "record_id": {
                "type": "string",
                "description": "The ID of the Zenodo record"
            },
            "include_files": {
                "type": "boolean",
                "description": "Whether to include file information in the summary",
                "default": False
            },
            "include_versions": {
                "type": "boolean",
                "description": "Whether to include version information in the summary",
                "default": False
            },
            "max_length": {
                "type": "integer",
                "description": "Maximum length of the summary in characters",
                "default": 500
            }
        },
        "required": ["record_id"]
    }
)
async def summarize_record(
    record_id: str,
    include_files: bool = False,
    include_versions: bool = False,
    max_length: int = 500
) -> SummarizeResponse:
    """Generate a summary from a Zenodo record's metadata.
    
    Args:
        record_id: The ID of the Zenodo record
        include_files: Whether to include file information in the summary
        include_versions: Whether to include version information in the summary
        max_length: Maximum length of the summary in characters
        
    Returns:
        SummarizeResponse containing the generated summary
    """
    start_time = time.time()
    
    # Get client
    client = _get_client()
    
    # Get the full metadata using the client
    metadata = await client.get_metadata(record_id)
    
    # Create base summary
    summary_dict = {
        "record_id": record_id,
        "title": metadata.get("metadata", {}).get("title", ""),
        "summary_text": metadata.get("metadata", {}).get("description", "")[:max_length],
        "publication_date": metadata.get("metadata", {}).get("publication_date", ""),
        "resource_type": metadata.get("metadata", {}).get("resource_type", {}),
        "access_right": metadata.get("metadata", {}).get("access_right", ""),
        "creators": metadata.get("metadata", {}).get("creators", [])
    }
    
    # Add file information if requested
    if include_files and "files" in metadata:
        summary_dict["files"] = {
            "count": len(metadata["files"]),
            "total_size": sum(f.get("size", 0) for f in metadata["files"]),
            "file_types": list(set(f.get("key", "").split(".")[-1] for f in metadata["files"] if "." in f.get("key", "")))
        }
    
    # Add version information if requested
    if include_versions and "relations" in metadata.get("metadata", {}):
        versions = metadata["metadata"]["relations"].get("version", [])
        summary_dict["versions"] = {
            "count": len(versions),
            "is_latest": any(v.get("is_last", False) for v in versions),
            "parent_id": versions[0].get("parent", {}).get("pid_value") if versions else None
        }
    
    # Format the summary dictionary into a string
    formatted_summary = _format_summary(summary_dict)
    
    # Create response
    response = SummarizeResponse(
        record_id=record_id,
        summary=formatted_summary,
        query_time=time.time() - start_time
    )
    
    return response 