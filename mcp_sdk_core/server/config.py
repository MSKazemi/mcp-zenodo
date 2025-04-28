"""
Configuration module for MCP Zenodo server.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field

class ZenodoConfig(BaseModel):
    """Configuration for Zenodo API."""
    api_token: Optional[str] = Field(None, description="Zenodo API access token")
    api_url: str = Field("https://zenodo.org/api", description="Zenodo API base URL")
    sandbox_mode: bool = Field(False, description="Whether to use Zenodo sandbox instead of production")
    
    @property
    def base_url(self) -> str:
        """Get the base URL for the Zenodo API."""
        if self.sandbox_mode:
            return "https://sandbox.zenodo.org/api"
        return self.api_url

def load_config() -> ZenodoConfig:
    """Load configuration from environment variables.
    
    Returns:
        ZenodoConfig object with settings from environment
    """
    return ZenodoConfig(
        api_token=os.environ.get("ZENODO_API_TOKEN"),
        api_url=os.environ.get("ZENODO_API_URL", "https://zenodo.org/api"),
        sandbox_mode=os.environ.get("ZENODO_SANDBOX", "false").lower() == "true"
    )

# Global configuration instance
config = load_config() 