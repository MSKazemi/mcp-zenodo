"""
Sampling functionality for the MCP Zenodo client.
"""

from typing import Optional, Dict, Any
import aiohttp

class SamplingRoot:
    """Handles basic API communication with Zenodo."""
    
    ZENODO_API_BASE = "https://zenodo.org/api"
    
    def __init__(self):
        """Initialize the sampling root."""
        self._session = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def _close_session(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        auth_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a request to the Zenodo API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            params: Optional query parameters
            auth_context: Authentication context containing headers
            **kwargs: Additional arguments for the request
            
        Returns:
            Response data as a dictionary
        """
        session = await self._get_session()
        url = f"{self.ZENODO_API_BASE}/{endpoint.lstrip('/')}"
        
        # Add authentication headers if provided
        if auth_context and "headers" in auth_context:
            kwargs["headers"] = {**(kwargs.get("headers", {})), **auth_context["headers"]}
        
        async with session.request(method, url, params=params, **kwargs) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Zenodo API error: {response.status} - {error_text}")
            
            if response.content_type == "application/json":
                return await response.json()
            else:
                return {"text": await response.text()}
  