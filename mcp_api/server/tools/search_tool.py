"""
Tool for searching Zenodo records.
"""

from typing import Any, Dict
from server.text import strip_html
from server.zenodo_client import MCPZenodoClient, RateLimitError
from .registry import tool

# Enough to judge relevance without filling a model's context
MAX_DESCRIPTION = 300
MAX_CREATORS = 10

# Create a single client instance for the tool
client = MCPZenodoClient()

def _summarise(record: Dict[str, Any], web_url: str) -> Dict[str, Any]:
    """Reduce a search hit to what is needed to choose a record."""
    metadata = record.get("metadata", {})
    description = strip_html(metadata.get("description", ""))
    if len(description) > MAX_DESCRIPTION:
        description = description[:MAX_DESCRIPTION].rstrip() + "..."
    return {
        "id": record.get("id"),
        "title": metadata.get("title", ""),
        "doi": record.get("doi") or metadata.get("doi", ""),
        "publication_date": metadata.get("publication_date", ""),
        "resource_type": metadata.get("resource_type", {}).get("type", ""),
        "creators": [c.get("name", "") for c in metadata.get("creators", [])[:MAX_CREATORS]],
        "keywords": metadata.get("keywords", []),
        "description": description,
        "file_count": len(record.get("files", [])),
        "url": f"{web_url}/records/{record.get('id')}",
    }

@tool(
    name="search_records",
    description="Search for records in Zenodo",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (at most 25 without a Zenodo token)",
                "default": 10
            },
            "sort": {
                "type": "string",
                "description": "Sort order (bestmatch, mostrecent)",
                "default": "mostrecent"
            },
            "full": {
                "type": "boolean",
                "description": "Return Zenodo's complete records instead of short summaries (very large)",
                "default": False
            }
        },
        "required": ["query"]
    }
)
async def search_records(
    query: str, max_results: int = 10, sort: str = "mostrecent", full: bool = False
) -> Dict[str, Any]:
    """
    Search for records in Zenodo.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        sort: Sort order (bestmatch, mostrecent)
        full: Return complete records instead of summaries
        
    Returns:
        Dictionary containing search results
    """
    try:
        # Search through the canonical client
        response = await client.search_records(query, max_results, sort)
        
        # Extract and format the results
        hits = response.get('hits', {})
        results = hits.get('hits', [])
        if not full:
            web_url = client.base_url.rstrip("/").removesuffix("/api")
            results = [_summarise(record, web_url) for record in results]
        total = hits.get('total', 0)
        
        return {
            "query": query,
            "total_results": total,
            "returned_results": len(results),
            "records": results
        }
    except RateLimitError:
        raise  # Callers must be able to tell that waiting will help
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "total_results": 0,
            "records": []
        } 