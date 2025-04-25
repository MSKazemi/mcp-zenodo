from typing import Dict, Any, List, Optional
import aiohttp

class DiscoveryClient:
    """Client for discovering MCP tools."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the discovery client.
        
        Args:
            base_url: Base URL of the MCP server
        """
        self.base_url = base_url.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Create aiohttp session when entering context."""
        self._session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close aiohttp session when exiting context."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get information about all available tools.
        
        Returns:
            List of dictionaries containing tool information
            
        Raises:
            aiohttp.ClientError: If the request fails
        """
        if not self._session:
            self._session = aiohttp.ClientSession()
        
        try:
            async with self._session.get(f"{self.base_url}/mcp/tools/openai-schema") as response:
                response.raise_for_status()
                data = await response.json()
                
                # Check if the response has the expected structure
                if "tools" in data:
                    return data["tools"]
                elif isinstance(data, list):
                    # If the response is already a list, return it directly
                    return data
                else:
                    # If the structure is different, log it and return an empty list
                    print(f"Unexpected response format: {data}")
                    return []
        except aiohttp.ClientError as e:
            print(f"Error discovering tools: {e}")
            return []

    async def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool.
        
        Args:
            tool_name: Name of the tool to get information about
            
        Returns:
            Dictionary containing tool information if found, None otherwise
            
        Raises:
            aiohttp.ClientError: If the request fails
        """
        tools = await this.get_available_tools()
        # tools = await self.get_available_tools()
        for tool in tools:
            if tool["name"] == tool_name:
                return tool
        return None 
    








        


