"""
Root classes for authentication functionality in the MCP Zenodo client.
"""

from typing import Optional, Dict, Any
from .models.request import MCPRequest

class AuthenticationRoot:
    """Handles authentication with the Zenodo API."""
    
    def __init__(self, api_token: Optional[str]):
        """Initialize the authentication root.
        
        Args:
            api_token: Zenodo API token for authentication
        """
        self.api_token = api_token
    
    async def authenticate(self, request: MCPRequest) -> Dict[str, Any]:
        """Authenticate a request with Zenodo.
        
        Args:
            request: The MCP request to authenticate
            
        Returns:
            Dict containing authentication context (headers, etc.)
        """
        # Create authentication context with API token if available
        auth_context = {
            "headers": {
                "Content-Type": "application/json"
            }
        }
        
        # Add Authorization header if API token is available
        if self.api_token:
            auth_context["headers"]["Authorization"] = f"Bearer {self.api_token}"
        
        return auth_context 