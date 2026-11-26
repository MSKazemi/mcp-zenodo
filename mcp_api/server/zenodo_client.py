"""Zenodo API client used by the MCP server tools."""

import time
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import quote

import aiohttp

from models.response import DownloadResponse

from .config import config

def _find_file(record: Dict[str, Any], file_name: str) -> Dict[str, Any]:
    """Return the file entry matching ``file_name`` in a Zenodo record."""
    for entry in record.get("files", []):
        if entry.get("key") == file_name or entry.get("filename") == file_name:
            return entry
    raise ValueError(f"File {file_name!r} not found in record")


class MCPZenodoClient:
    """Basic client for Zenodo API authentication and communication."""
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        base_url: Optional[str] = None,
        cache_dir: Optional[str] = None,
    ):
        """Initialize the Zenodo client.

        Args:
            api_token: Optional Zenodo API token (defaults to config)
            base_url: Optional base URL for the API (defaults to config)
            cache_dir: Directory for downloaded files (defaults to ~/.zenodo_cache)
        """
        self.api_token = api_token or config.api_token
        self.base_url = base_url or config.base_url
        self.cache_dir = Path(cache_dir or Path.home() / ".zenodo_cache").expanduser()
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

    async def get_metadata(self, record_id: str) -> Dict[str, Any]:
        """Return the raw record payload for ``record_id``."""
        return await self._make_request("GET", f"records/{record_id}")

    async def search_records(
        self,
        query: str,
        max_results: int = 10,
        sort: str = "mostrecent",
    ) -> Dict[str, Any]:
        """Return the raw search payload for ``query``."""
        return await self._make_request(
            "GET",
            "records",
            params={"q": query, "size": max_results, "sort": sort},
        )

    async def download_file(
        self,
        record_id: str,
        file_name: str,
        force_download: bool = False,
    ) -> DownloadResponse:
        """Stream a record file into the local cache and return its path."""
        start = time.monotonic()
        safe_record = Path(record_id).name
        safe_name = Path(file_name).name
        target = self.cache_dir / safe_record / safe_name

        try:
            if target.exists() and not force_download:
                return DownloadResponse(
                    record_id=record_id,
                    file_name=file_name,
                    file_path=str(target),
                    file_size=target.stat().st_size,
                    query_time=time.monotonic() - start,
                )

            record = await self.get_metadata(record_id)
            entry = _find_file(record, file_name)
            links = entry.get("links") or {}
            url = links.get("download") or links.get("self") or (
                f"{self.base_url}/records/{quote(record_id, safe='')}"
                f"/files/{quote(file_name, safe='')}/content"
            )
            expected_size = entry.get("size")

            target.parent.mkdir(parents=True, exist_ok=True)
            temp = target.with_name(target.name + ".part")
            size = 0
            try:
                headers = {}
                if self.api_token and url.startswith(self.base_url.rstrip("/")):
                    headers["Authorization"] = f"Bearer {self.api_token}"
                session = await self._get_session()
                async with session.get(url, headers=headers) as response:
                    if response.status >= 400:
                        raise ValueError(
                            f"Zenodo API error: {response.status} - {await response.text()}"
                        )
                    with temp.open("wb") as stream:
                        async for chunk in response.content.iter_chunked(64 * 1024):
                            stream.write(chunk)

                size = temp.stat().st_size
                if expected_size and size != expected_size:
                    raise ValueError(
                        f"Downloaded {size} bytes; expected {expected_size} for {file_name}"
                    )
                temp.replace(target)
            except BaseException:
                temp.unlink(missing_ok=True)
                raise
        except (ValueError, OSError, aiohttp.ClientError) as exc:
            return DownloadResponse(
                record_id=record_id,
                file_name=file_name,
                query_time=time.monotonic() - start,
                error=str(exc),
            )

        return DownloadResponse(
            record_id=record_id,
            file_name=file_name,
            file_path=str(target),
            file_size=size,
            query_time=time.monotonic() - start,
        )
