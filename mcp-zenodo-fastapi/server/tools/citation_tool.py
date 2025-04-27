"""
Tool for retrieving citations for Zenodo records.
"""

from typing import Dict, Any, Optional
import time
from server.zenodo_client import MCPZenodoClient
from models.request import CitationRequest
from models.response import CitationResponse
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
    name="get_citation",
    description="Returns BibTeX or APA citation of a Zenodo record",
    parameters={
        "type": "object",
        "properties": {
            "record_id": {
                "type": "string",
                "description": "The ID of the Zenodo record"
            },
            "format": {
                "type": "string",
                "description": "The citation format (bibtex, apa, etc.)",
                "default": "bibtex"
            }
        },
        "required": ["record_id"]
    }
)
async def get_citation(record_id: str, format: str = "bibtex") -> CitationResponse:
    """Get a citation for a Zenodo record in the specified format.
    
    Args:
        record_id: The ID of the Zenodo record
        format: The citation format (bibtex, apa, etc.)
        
    Returns:
        CitationResponse containing the citation
    """
    start_time = time.time()
    client = _get_client()
    
    # Get metadata for the record
    metadata = await client.get_metadata(record_id)
    
    # Extract necessary fields
    title = metadata.get("metadata", {}).get("title", "")
    creators = metadata.get("metadata", {}).get("creators", [])
    pub_date = metadata.get("metadata", {}).get("publication_date", "")
    doi = metadata.get("metadata", {}).get("doi", "")
    
    if format.lower() == "bibtex":
        # Generate BibTeX citation
        authors = " and ".join(c.get("name", "") for c in creators)
        year = pub_date.split("-")[0] if pub_date else ""
        
        citation = f"""@misc{{{record_id},
  author = {{{authors}}},
  title = {{{title}}},
  year = {{{year}}},
  publisher = {{Zenodo}},
  doi = {{{doi}}}
}}"""
    
    elif format.lower() == "apa":
        # Generate APA citation
        authors = ", ".join(c.get("name", "") for c in creators)
        year = pub_date.split("-")[0] if pub_date else ""
        
        citation = f"{authors} ({year}). {title}. Zenodo. https://doi.org/{doi}"
    
    else:
        raise ValueError(f"Unsupported citation format: {format}")
    
    # Create and return response
    return CitationResponse(
        record_id=record_id,
        citation=citation,
        format=format,
        query_time=time.time() - start_time
    ) 