"""
Embed tool implementation for Zenodo API.
"""

import time
from typing import Dict, Any, Optional
from models.request import EmbedRequest
from models.response import EmbedResponse
from .registry import tool

@tool(
    name="generate_embed_link",
    description="Creates a direct embeddable link for a Zenodo record (PDF, dataset)",
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
    """Generate an embeddable link for a Zenodo record.
    
    Args:
        record_id: The ID of the Zenodo record
        
    Returns:
        EmbedResponse containing the embeddable link and metadata
    """
    start_time = time.time()
    
    # Generate embed URL directly
    embed_url = f"https://zenodo.org/record/{record_id}/embed"
    
    # For simplicity, we'll assume it's a dataset by default
    # In a real implementation, you might want to check the record type
    record_type = "dataset"
    
    # Create response
    response = EmbedResponse(
        embed_url=embed_url,
        record_id=record_id,
        record_type=record_type,
        query_time=time.time() - start_time
    )
    
    return response 