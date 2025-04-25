"""
FastAPI routes for MCP Zenodo integration.
"""

from fastapi import APIRouter, HTTPException
from models.request import MCPRequest, CitationRequest
from models.response import MCPResponse, CitationResponse
from server.server import MCPServer

router = APIRouter()
server = MCPServer()

@router.post("/search", response_model=MCPResponse)
async def search(request: MCPRequest) -> MCPResponse:
    """Handle MCP search requests.
    
    Args:
        request: The MCP search request
        
    Returns:
        MCPResponse containing the search results
        
    Raises:
        HTTPException: If the request cannot be processed
    """
    try:
        return await server.handle_request(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/citation", response_model=CitationResponse)
async def get_citation(request: CitationRequest) -> CitationResponse:
    """Handle citation requests.
    
    Args:
        request: The citation request
        
    Returns:
        CitationResponse containing the citation
        
    Raises:
        HTTPException: If the request cannot be processed
    """
    try:
        return await server.handle_citation_request(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 