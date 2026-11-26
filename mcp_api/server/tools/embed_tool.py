"""
Embed tool implementation for Zenodo API.
"""

import time
from urllib.parse import quote

from models.response import EmbedResponse
from server.zenodo_client import MCPZenodoClient
from .registry import tool

# File types Zenodo can render, best first
PREVIEWABLE = ("pdf", "png", "jpg", "jpeg", "gif", "md", "txt", "csv", "json", "zip")

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
    name="generate_embed_link",
    description=(
        "Returns a link that shows a Zenodo record's file preview, or its record page. "
        "Zenodo does not let other websites frame these pages"
    ),
    parameters={
        "type": "object",
        "properties": {
            "record_id": {
                "type": "string",
                "description": "The ID of the Zenodo record"
            }
        },
        "required": ["record_id"]
    }
)
async def generate_embed_link(
    record_id: str
) -> EmbedResponse:
    """Generate a preview link for a Zenodo record.
    
    Args:
        record_id: The ID of the Zenodo record
        
    Returns:
        EmbedResponse containing the link and the record's resource type
    """
    start_time = time.time()
    client = _get_client()
    record = await client.get_metadata(record_id)

    web_url = client.base_url.rstrip("/").removesuffix("/api")
    link = f"{web_url}/records/{record_id}"

    names = [entry.get("key", "") for entry in record.get("files", [])]
    candidates = [
        name for name in names
        if "." in name and name.rsplit(".", 1)[1].lower() in PREVIEWABLE
    ]
    if candidates:
        best = min(candidates, key=lambda n: PREVIEWABLE.index(n.rsplit(".", 1)[1].lower()))
        link = f"{link}/preview/{quote(best, safe='')}"

    resource_type = record.get("metadata", {}).get("resource_type", {})

    return EmbedResponse(
        embed_url=link,
        record_id=record_id,
        record_type=resource_type.get("type", "unknown"),
        query_time=time.time() - start_time
    )
