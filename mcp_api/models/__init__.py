"""
Pydantic models for MCP Zenodo integration.
"""

from .request import (
    MCPRequest,
    ZenodoSearchRequest,
    CitationRequest,
    MetadataRequest,
    DownloadRequest,
    SummarizeRequest,
    EmbedRequest,
    DataTypeRequest,
    ListFilesRequest,
    RelatedRecordsRequest,
    CompareRecordsRequest,
)
from .response import (
    ZenodoFile,
    ZenodoRecord,
    MCPResponse,
    CreatorInfo,
    CitationResponse,
    MetadataResponse,
    DownloadResponse,
    SummarizeResponse,
    EmbedResponse,
    DataTypeResponse,
    ListFilesResponse,
    RelatedRecordsResponse,
    CompareRecordsResponse,
)

__all__ = [
    "MCPRequest",
    "ZenodoSearchRequest",
    "CitationRequest",
    "MetadataRequest",
    "DownloadRequest",
    "SummarizeRequest",
    "EmbedRequest",
    "DataTypeRequest",
    "ListFilesRequest",
    "RelatedRecordsRequest",
    "CompareRecordsRequest",
    "ZenodoFile",
    "ZenodoRecord",
    "MCPResponse",
    "CreatorInfo",
    "CitationResponse",
    "MetadataResponse",
    "DownloadResponse",
    "SummarizeResponse",
    "EmbedResponse",
    "DataTypeResponse",
    "ListFilesResponse",
    "RelatedRecordsResponse",
    "CompareRecordsResponse",
]
