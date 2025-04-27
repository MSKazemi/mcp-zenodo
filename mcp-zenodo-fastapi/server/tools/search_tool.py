"""
Tool for searching Zenodo records.
"""

from typing import Dict, Any, List, Optional
from server.zenodo_client import MCPZenodoClient
from .registry import tool

# Create a single client instance for the tool
client = MCPZenodoClient()

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
                "description": "Maximum number of results to return",
                "default": 10
            },
            "sort": {
                "type": "string",
                "description": "Sort order (bestmatch, mostrecent)",
                "default": "mostrecent"
            }
        },
        "required": ["query"]
    }
)
async def search_records(query: str, max_results: int = 10, sort: str = "mostrecent") -> Dict[str, Any]:
    """
    Search for records in Zenodo.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        sort: Sort order (bestmatch, mostrecent)
        
    Returns:
        Dictionary containing search results
    """
    try:
        # Prepare search parameters
        params = {
            "q": query,
            "size": max_results,
            "sort": sort
        }
        
        # Make the search request
        response = await client._make_request('GET', 'records', params=params)
        
        # Extract and format the results
        hits = response.get('hits', {})
        results = hits.get('hits', [])
        total = hits.get('total', 0)
        
        return {
            "query": query,
            "total_results": total,
            "records": results
        }
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "total_results": 0,
            "records": []
        } 