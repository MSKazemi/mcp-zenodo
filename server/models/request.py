"""
Request models for MCP Zenodo integration.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class MCPRequest(BaseModel):
    """Base MCP request model."""
    query: str = Field(..., description="The search query for Zenodo")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters for the search")
    max_results: Optional[int] = Field(default=10, description="Maximum number of results to return")

class ZenodoSearchRequest(MCPRequest):
    """Specific request model for Zenodo searches."""
    access_token: Optional[str] = Field(None, description="Zenodo API access token")
    sort_by: Optional[str] = Field("most_recent", description="Sort criteria for results")
    file_types: Optional[List[str]] = Field(None, description="Filter by file types")

class CitationRequest(BaseModel):
    """Request model for getting citations."""
    record_id: str = Field(..., description="The ID of the Zenodo record")
    format: Optional[str] = Field(default="bibtex", description="The citation format (bibtex, cff, datacite, dc, dublincore, json, jsonld, schema.org)")

class MetadataRequest(BaseModel):
    """Request model for getting record metadata."""
    record_id: str = Field(..., description="The ID of the Zenodo record")
    include_files: Optional[bool] = Field(default=True, description="Whether to include file information")
    include_versions: Optional[bool] = Field(default=True, description="Whether to include version information")

class DownloadRequest(BaseModel):
    """Request model for downloading files."""
    record_id: str = Field(..., description="The ID of the Zenodo record")
    file_name: str = Field(..., description="The name of the file to download")
    force_download: Optional[bool] = Field(default=False, description="Whether to force download even if cached")

class SummarizeRequest(BaseModel):
    """Request model for summarizing records."""
    record_id: str = Field(..., description="The ID of the Zenodo record")
    include_files: Optional[bool] = Field(default=False, description="Whether to include file information in the summary")
    include_versions: Optional[bool] = Field(default=False, description="Whether to include version information in the summary")
    max_length: Optional[int] = Field(default=500, description="Maximum length of the summary in characters")

class EmbedRequest(BaseModel):
    """Request model for generating embeddable links."""
    record_id: str = Field(..., description="The ID of the Zenodo record")

class DataTypeRequest(BaseModel):
    """Request for detecting the data type of a Zenodo record."""
    record_id: str = Field(..., description="The ID of the Zenodo record to analyze")

class ListFilesRequest(BaseModel):
    """Request model for listing files in a record."""
    record_id: str = Field(..., description="The ID of the Zenodo record")
    include_metadata: Optional[bool] = Field(default=True, description="Whether to include file metadata")

class RelatedRecordsRequest(BaseModel):
    """Request model for finding related records."""
    record_id: str = Field(..., description="The ID of the Zenodo record")
    max_results: Optional[int] = Field(default=5, description="Maximum number of related records to return")
    similarity_threshold: Optional[float] = Field(default=0.3, description="Minimum similarity score (0.0 to 1.0)")

class CompareRecordsRequest(BaseModel):
    """Request model for comparing multiple Zenodo records."""
    record_ids: List[str]
    compare_fields: Optional[List[str]] = ["title", "authors", "topics", "publication_date"]

__all__ = ["MCPRequest", "ZenodoSearchRequest", "CitationRequest", "MetadataRequest", "DownloadRequest", "SummarizeRequest", "EmbedRequest", "DataTypeRequest", "ListFilesRequest", "RelatedRecordsRequest", "CompareRecordsRequest"] 