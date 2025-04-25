"""
Main MCP Client implementation for Zenodo.
"""

import os
from typing import Optional, Dict, Any, List
from .roots import AuthenticationRoot
from .sampling import SamplingRoot
from models.request import MCPRequest
from .discovery import DiscoveryClient
import aiohttp

class MCPZenodoClient:
    """Main client class for MCP Zenodo integration."""
    
    def __init__(self, base_url: str = "http://localhost:8000", access_token: Optional[str] = None):
        """Initialize the MCP Zenodo client.
        
        Args:
            base_url: Base URL of the MCP server
            access_token: Optional access token for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.access_token = access_token
        self._session: Optional[aiohttp.ClientSession] = None
        self.auth_root = AuthenticationRoot(self.access_token)
        self.sampling_root = SamplingRoot()
        self.discovery = DiscoveryClient(base_url)
    
    async def __aenter__(self):
        """Create aiohttp session when entering context."""
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session when exiting context."""
        if self._session:
            try:
                await self._session.close()
            except Exception as e:
                print(f"Error closing session: {e}")
            finally:
                self._session = None
    
    async def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover available tools from the MCP server.
        
        Returns:
            List of dictionaries containing tool information
            
        Raises:
            aiohttp.ClientError: If the request fails
        """
        return await self.discovery.get_available_tools()
    
    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool.
        
        Args:
            tool_name: Name of the tool to get information about
            
        Returns:
            Dictionary containing tool information if found, None otherwise
            
        Raises:
            aiohttp.ClientError: If the request fails
        """
        return await self.discovery.get_tool_info(tool_name)
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool by name with the given arguments.
        
        Args:
            name: Name of the tool to call
            arguments: Arguments to pass to the tool
            
        Returns:
            Result of the tool call
            
        Raises:
            aiohttp.ClientError: If the request fails
        """
        if not self._session:
            self._session = aiohttp.ClientSession()
        
        try:
            async with self._session.post(
                f"{self.base_url}/mcp/tools/call",
                json={"name": name, "arguments": arguments}
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("result")
        except aiohttp.ClientError as e:
            print(f"Error calling tool {name}: {e}")
            return None
    
    async def make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make an authenticated request to the Zenodo API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Optional query parameters
            **kwargs: Additional arguments for the request
            
        Returns:
            Response data as a dictionary
        """
        # Get authentication context
        auth_context = await self.auth_root.authenticate(MCPRequest(query=""))
        
        # Make the request through sampling root
        return await self.sampling_root.make_request(
            method=method,
            endpoint=endpoint,
            params=params,
            auth_context=auth_context,
            **kwargs
        )
    
    async def get_metadata(self, record_id: str) -> Dict[str, Any]:
        """Get detailed metadata for a Zenodo record.
        
        Args:
            record_id: The ID of the Zenodo record
            
        Returns:
            Dictionary containing the record metadata
        """
        return await self.make_request("GET", f"records/{record_id}")
    
    async def search_records(self, query: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Basic search operation for Zenodo records.
        
        Args:
            query: Search query string
            params: Optional additional parameters
            
        Returns:
            Raw search results from Zenodo API
        """
        search_params = {"q": query, **(params or {})}
        return await self.make_request("GET", "records", params=search_params)