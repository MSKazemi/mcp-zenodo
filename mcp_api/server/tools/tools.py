"""
Tool invocation functionality for the MCP Zenodo server.
"""

import time
from typing import Any, Dict, Optional

from models.request import MCPRequest
from models.response import CreatorInfo, MCPResponse, ZenodoFile, ZenodoRecord
from server.zenodo_client import MCPZenodoClient

# Search parameters of the records API that callers may pass as filters
ALLOWED_FILTERS = {"all_versions", "bounds", "communities", "page", "status", "subtype", "type"}


def _to_record(hit: Dict[str, Any]) -> ZenodoRecord:
    """Convert one search hit into the response model."""
    metadata = hit.get("metadata", {})
    return ZenodoRecord(
        id=hit["id"],
        title=metadata.get("title") or hit.get("title", ""),
        description=metadata.get("description"),
        creators=[
            CreatorInfo(
                name=creator.get("name", ""),
                affiliation=creator.get("affiliation"),
                orcid=creator.get("orcid"),
                gnd=creator.get("gnd"),
            )
            for creator in metadata.get("creators", [])
        ],
        publication_date=metadata.get("publication_date", ""),
        files=[
            ZenodoFile(
                filename=entry.get("key", ""),
                size=entry.get("size", 0),
                checksum=entry.get("checksum", ""),
                download_url=entry.get("links", {}).get("self", ""),
            )
            for entry in hit.get("files", [])
        ],
        metadata=metadata,
    )


class ToolInvoker:
    """Invokes necessary tools to process requests."""

    def __init__(self, client: Optional[MCPZenodoClient] = None):
        """Initialize the tool invoker.

        Args:
            client: Optional MCPZenodoClient instance (defaults to creating a new one)
        """
        self.client = client or MCPZenodoClient()

    async def invoke(
        self,
        prompt: Dict[str, Any],
        resources: Dict[str, Any],
        request: MCPRequest
    ) -> MCPResponse:
        """Run the search described by an MCP request.

        Args:
            prompt: The assembled prompt dictionary (currently unused)
            resources: The prepared resources dictionary (currently unused)
            request: The search request: query, filters and result count

        Returns:
            MCPResponse containing the search results from Zenodo
        """
        filters = request.filters or {}
        unknown = sorted(set(filters) - ALLOWED_FILTERS)
        if unknown:
            raise ValueError(
                f"Unsupported filters: {', '.join(unknown)}. "
                f"Supported: {', '.join(sorted(ALLOWED_FILTERS))}"
            )

        invalid = sorted(
            key for key, value in filters.items() if not isinstance(value, (str, int))
        )
        if invalid:
            raise ValueError(
                f"Filter values must be text, numbers or booleans: {', '.join(invalid)}"
            )

        start = time.monotonic()
        response = await self.client.search_records(
            request.query,
            max_results=request.max_results or 10,
            filters=filters,
        )
        hits = response.get("hits", {})
        return MCPResponse(
            records=[_to_record(hit) for hit in hits.get("hits", [])],
            total_count=hits.get("total", 0),
            query_time=time.monotonic() - start,
        )
