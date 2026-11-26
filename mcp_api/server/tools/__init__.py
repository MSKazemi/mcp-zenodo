"""
Tool implementations for MCP Zenodo server.
"""

from .registry import tool, get_tool_registry
from .search_tool import search_records
from .metadata_tool import get_metadata
from .download_tool import download_file
from .summarize_tool import summarize_record
from .data_type_tool import detect_data_type
from .citation_tool import get_citation
from .files_tool import list_files
from .related_records_tool import get_related_records
from .compare_tool import compare_records
from .keywords_tool import extract_keywords
from .embed_tool import generate_embed_link

__all__ = [
    "tool",
    "get_tool_registry",
    "search_records",
    "get_metadata",
    "download_file",
    "summarize_record",
    "detect_data_type",
    "get_citation",
    "list_files",
    "get_related_records",
    "compare_records",
    "extract_keywords",
    "generate_embed_link"
]
