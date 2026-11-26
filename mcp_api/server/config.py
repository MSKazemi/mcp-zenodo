"""
Configuration module for MCP Zenodo server.
"""

import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class ZenodoConfig(BaseModel):
    """Configuration for the Zenodo API and the HTTP service."""
    api_token: Optional[str] = Field(None, description="Zenodo API access token")
    api_url: str = Field("https://zenodo.org/api", description="Zenodo API base URL")
    sandbox_mode: bool = Field(False, description="Whether to use Zenodo sandbox instead of production")
    host: str = Field("127.0.0.1", description="Address the HTTP service listens on")
    port: int = Field(8000, description="Port the HTTP service listens on")
    api_key: Optional[str] = Field(None, description="Key HTTP callers must send as a bearer token")
    cors_origins: List[str] = Field(default_factory=list, description="Browser origins allowed to call the service")

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
    origins = os.environ.get("CORS_ORIGINS", "")
    return ZenodoConfig(
        api_token=os.environ.get("ZENODO_API_TOKEN") or None,
        api_url=os.environ.get("ZENODO_API_URL", "https://zenodo.org/api"),
        sandbox_mode=os.environ.get("ZENODO_SANDBOX", "false").lower() == "true",
        host=os.environ.get("HOST") or "127.0.0.1",
        port=int(os.environ.get("PORT") or 8000),
        api_key=os.environ.get("MCP_API_KEY") or None,
        cors_origins=[o.strip().rstrip("/") for o in origins.split(",") if o.strip()],
    )


# mcp_api/.env, then the repository's .env; variables already set always win
_API_DIR = Path(__file__).resolve().parents[1]
for _directory in (_API_DIR, _API_DIR.parent):
    load_dotenv(_directory / ".env")

# Global configuration instance
config = load_config()
