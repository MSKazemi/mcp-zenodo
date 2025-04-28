"""
Response models for MCP Zenodo integration.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

class ZenodoFile(BaseModel):
    """Model for Zenodo file metadata."""
    filename: str
    size: int
    checksum: str
    download_url: str
    file_type: Optional[str] = None

class CreatorInfo(BaseModel):
    """Model for creator information."""
    name: str
    affiliation: Optional[str] = None
    orcid: Optional[str] = None
    gnd: Optional[str] = None

class ZenodoRecord(BaseModel):
    """Model for Zenodo record metadata."""
    id: int
    title: str
    description: Optional[str]
    creators: List[CreatorInfo]
    publication_date: str
    files: List[ZenodoFile]
    metadata: Dict[str, Any]

class MCPResponse(BaseModel):
    """Base MCP response model."""
    records: List[ZenodoRecord]
    total_count: int
    query_time: float

class CitationResponse(BaseModel):
    """Response model for citations."""
    citation: Union[str, Dict[str, Any]]
    format: str
    record_id: str
    query_time: float

class MetadataResponse(BaseModel):
    """Response model for record metadata."""
    record: Dict[str, Any]
    record_id: str
    query_time: float
    error: Optional[str] = None

class DownloadResponse(BaseModel):
    """Response model for file downloads."""
    file_path: Optional[str] = None
    record_id: str
    file_name: str
    file_size: Optional[int] = None
    query_time: float
    error: Optional[str] = None

class SummarizeResponse(BaseModel):
    """Response model for record summaries."""
    summary: Optional[str] = None
    record_id: str
    query_time: float
    error: Optional[str] = None

class EmbedResponse(BaseModel):
    """Response model for embeddable links."""
    embed_url: str
    record_id: str
    record_type: str
    query_time: float
    error: Optional[str] = None

class DataTypeResponse(BaseModel):
    """Response containing the detected data type of a Zenodo record."""
    record_id: str
    data_type: str
    confidence: float
    metadata: Dict[str, Any]

class ListFilesResponse(BaseModel):
    """Response model for listing files in a record."""
    record_id: str
    files: List[Dict[str, Any]]
    total_count: int
    query_time: Optional[float] = None
    error: Optional[str] = None

class RelatedRecordsResponse(BaseModel):
    """Response model for related records."""
    record_id: str
    related_records: List[Dict[str, Any]]
    total_count: int
    query_time: Optional[float] = None
    error: Optional[str] = None

class CompareRecordsResponse(BaseModel):
    """Response model for record comparison results."""
    record_ids: List[str]
    field_comparisons: Dict[str, Dict[str, Union[str, float]]]
    overall_similarity: float
    differences: Dict[str, List[Dict[str, str]]]

__all__ = ["ZenodoFile", "ZenodoRecord", "MCPResponse", "CreatorInfo", "CitationResponse", "MetadataResponse", "DownloadResponse", "SummarizeResponse", "EmbedResponse", "DataTypeResponse", "ListFilesResponse", "RelatedRecordsResponse", "CompareRecordsResponse"] 