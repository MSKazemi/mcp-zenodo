"""
Basic Zenodo API client for authentication and communication.
"""

import aiohttp
from typing import Dict, Any, Optional, List
from config import config

class MCPZenodoClient:
    """Basic client for Zenodo API authentication and communication."""
    
    def __init__(self, api_token: Optional[str] = None, base_url: Optional[str] = None):
        """Initialize the Zenodo client.
        
        Args:
            api_token: Optional Zenodo API token (defaults to config)
            base_url: Optional base URL for the API (defaults to config)
        """
        self.api_token = api_token or config.api_token
        self.base_url = base_url or config.base_url
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
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an authenticated request to the Zenodo API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional arguments for the request
            
        Returns:
            Response data as a dictionary
        """
        session = await self._get_session()
        
        # Add authentication if token is available
        headers = kwargs.pop('headers', {})
        if self.api_token:
            headers['Authorization'] = f'Bearer {self.api_token}'
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        async with session.request(method, url, headers=headers, **kwargs) as response:
            if response.status == 401:
                raise ValueError("Authentication failed. Please check your Zenodo API token.")
            elif response.status == 403:
                raise ValueError("Permission denied. Your token may not have sufficient permissions.")
            elif response.status >= 400:
                error_text = await response.text()
                raise ValueError(f"Zenodo API error: {response.status} - {error_text}")
            
            return await response.json()
