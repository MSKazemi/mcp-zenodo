from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, List, Union, Optional, Set, Tuple
from zenodo_client import MCPZenodoClient
from models.request import DownloadRequest, MetadataRequest, CompareRecordsRequest
from models.response import DownloadResponse, MetadataResponse, SummarizeResponse, CitationResponse, CompareRecordsResponse, EmbedResponse
import os
import time
import numpy as np
from difflib import SequenceMatcher
import logging
import functools
import asyncio
from collections import Counter
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("zenodo_mcp")

# Initialize FastMCP server
mcp = FastMCP("Zenodo")



########################################################
#             Initialize the Zenodo client             #
########################################################

_client = None
_cache_dir = os.path.join(os.path.expanduser("~"), ".zenodo_cache")
_api_cache = {}
_api_cache_ttl = 1  # 5 minutes cache TTL

# Create cache directory if it doesn't exist
os.makedirs(_cache_dir, exist_ok=True)

def _get_client() -> MCPZenodoClient:
    """Get or create the MCPZenodoClient instance using a singleton pattern.
    
    Returns:
        MCPZenodoClient instance
    """
    global _client
    if _client is None:
        _client = MCPZenodoClient()
        logger.info("Initialized new MCPZenodoClient instance")
    return _client

def _cache_api_response(func):
    """Decorator to cache API responses with TTL.
    
    Args:
        func: The async function to cache
        
    Returns:
        Wrapped function with caching
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Create a cache key from function name and arguments
        key_parts = [func.__name__]
        key_parts.extend([str(arg) for arg in args])
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        cache_key = "|".join(key_parts)
        
        # Check if we have a cached result that's still valid
        if cache_key in _api_cache:
            timestamp, result = _api_cache[cache_key]
            if time.time() - timestamp < _api_cache_ttl:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
        
        # Call the original function
        result = await func(*args, **kwargs)
        
        # Cache the result
        _api_cache[cache_key] = (time.time(), result)
        logger.debug(f"Cached result for {func.__name__}")
        
        return result
    
    return wrapper

def _handle_api_error(func):
    """Decorator to handle API errors consistently.
    
    Args:
        func: The async function to wrap
        
    Returns:
        Wrapped function with error handling
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            # Return appropriate error response based on function return type
            if func.__name__ == "download_file":
                return DownloadResponse(
                    record_id=kwargs.get("record_id", ""),
                    file_name=kwargs.get("file_name", ""),
                    query_time=time.time() - time.time(),
                    error=str(e)
                )
            elif func.__name__ == "get_metadata":
                return MetadataResponse(
                    record={},
                    record_id=kwargs.get("record_id", ""),
                    query_time=time.time() - time.time(),
                    error=str(e)
                )
            elif func.__name__ == "summarize_record":
                return SummarizeResponse(
                    record_id=kwargs.get("record_id", ""),
                    summary="",
                    query_time=time.time() - time.time(),
                    error=str(e)
                )
            elif func.__name__ == "get_citation":
                return CitationResponse(
                    record_id=kwargs.get("record_id", ""),
                    citation="",
                    format=kwargs.get("format", "bibtex"),
                    query_time=time.time() - time.time(),
                    error=str(e)
                )
            elif func.__name__ == "generate_embed_link":
                return EmbedResponse(
                    embed_url="",
                    record_id=kwargs.get("record_id", ""),
                    record_type="unknown",
                    query_time=time.time() - time.time(),
                    error=str(e)
                )
            elif func.__name__ == "compare_records":
                return CompareRecordsResponse(
                    record_ids=kwargs.get("request", CompareRecordsRequest()).record_ids,
                    field_comparisons={},
                    overall_similarity=0.0,
                    differences={},
                    error=str(e)
                )
            else:
                # Generic error response for other functions
                return {
                    "error": str(e),
                    "success": False
                }
    
    return wrapper


########################################################
#                  Tools for Zenodo API                #
########################################################


################################
#   Searching Zenodo Records   #
################################

@mcp.tool()
@_handle_api_error
@_cache_api_response
async def search_records(query: str, max_results: int = 10, sort: str = "mostrecent") -> Dict[str, Any]:
    """
    Search for records in Zenodo.
    
    Args:
        query: Search query
        max_results: Maximum number of results to return
        sort: Sort order (bestmatch, mostrecent)
        
    Returns:
        Dictionary containing search results
    """
    # Prepare search parameters
    params = {
        "q": query,
        "size": max_results,
        "sort": sort
    }
    
    client = _get_client()

    # Make the search request
    response = await client._make_request('GET', 'records', params=params)
    
    # Extract and format the results
    hits = response.get('hits', {})
    results = hits.get('hits', [])
    total = hits.get('total', 0)
    
    logger.info(f"Search for '{query}' returned {total} results")
    
    return {
        "query": query,
        "total_results": total,
        "records": results
    }

################################
#   Retrieving Citations      #
################################

@mcp.tool()
@_handle_api_error
@_cache_api_response
async def get_citation(record_id: str, format: str = "bibtex") -> CitationResponse:
    """Get a citation for a Zenodo record in the specified format.
    
    Args:
        record_id: The ID of the Zenodo record
        format: The citation format (bibtex, apa, etc.)
        
    Returns:
        CitationResponse containing the citation
    """
    start_time = time.time()
    client = _get_client()
    
    # Get metadata for the record
    metadata = await client._make_request('GET', f'records/{record_id}')
    
    # Extract necessary fields
    title = metadata.get("metadata", {}).get("title", "")
    creators = metadata.get("metadata", {}).get("creators", [])
    pub_date = metadata.get("metadata", {}).get("publication_date", "")
    doi = metadata.get("metadata", {}).get("doi", "")
    
    if format.lower() == "bibtex":
        # Generate BibTeX citation
        authors = " and ".join(c.get("name", "") for c in creators)
        year = pub_date.split("-")[0] if pub_date else ""
        
        citation = f"""@misc{{{record_id},
  author = {{{authors}}},
  title = {{{title}}},
  year = {{{year}}},
  publisher = {{Zenodo}},
  doi = {{{doi}}}
}}"""
    
    elif format.lower() == "apa":
        # Generate APA citation
        authors = ", ".join(c.get("name", "") for c in creators)
        year = pub_date.split("-")[0] if pub_date else ""
        
        citation = f"{authors} ({year}). {title}. Zenodo. https://doi.org/{doi}"
    
    else:
        raise ValueError(f"Unsupported citation format: {format}")
    
    logger.info(f"Generated {format} citation for record {record_id}")
    
    # Create and return response
    return CitationResponse(
        record_id=record_id,
        citation=citation,
        format=format,
        query_time=time.time() - start_time
    )





################################
#   Detecting Data Type       #
################################

@mcp.tool()
@_handle_api_error
@_cache_api_response
async def detect_data_type(record_id: str) -> Dict[str, Any]:
    """Determine if a Zenodo record is a dataset, software, or article.
    
    Args:
        record_id: The ID of the Zenodo record to analyze
        
    Returns:
        Dictionary containing the detected data type and confidence score
    """
    client = _get_client()
    
    # Fetch the record metadata
    record = await client._make_request('GET', f'records/{record_id}')
    
    # Initialize result
    result = {
        "record_id": record_id,
        "data_type": "unknown",
        "confidence": 0.0,
        "metadata": {}
    }
    
    # Check for type indicators in metadata
    metadata = record.get("metadata", {})
    
    # Define type indicators
    type_indicators = {
        "software": ["software", "code", "program", "library", "package", "tool"],
        "dataset": ["dataset", "data", "measurement", "survey", "collection"],
        "article": ["article", "paper", "publication", "journal", "conference"]
    }
    
    # Check for type indicators in keywords
    if "keywords" in metadata:
        keywords = [kw.lower() for kw in metadata["keywords"]]
        for data_type, indicators in type_indicators.items():
            if any(indicator in keywords for indicator in indicators):
                result["data_type"] = data_type
                result["confidence"] = 0.8
                break
    
    # Check file extensions as a fallback
    if result["data_type"] == "unknown" and "files" in record:
        file_extensions = [f.get("filename", "").split(".")[-1].lower() for f in record["files"] if "." in f.get("filename", "")]
        
        # Define file extension indicators
        extension_indicators = {
            "software": ["py", "js", "java", "cpp", "c", "h", "r", "matlab", "php", "rb", "go", "rs", "swift", "kt", "scala"],
            "dataset": ["csv", "tsv", "json", "xml", "hdf5", "nc", "npy", "npz", "db", "sql", "xlsx", "xls", "parquet", "avro"],
            "article": ["pdf", "doc", "docx", "tex", "md", "txt", "rtf", "odt"]
        }
        
        for data_type, extensions in extension_indicators.items():
            if any(ext in file_extensions for ext in extensions):
                result["data_type"] = data_type
                result["confidence"] = 0.6
                break
    
    # Store relevant metadata for reference
    result["metadata"] = {
        "title": metadata.get("title", ""),
        "description": metadata.get("description", ""),
        "keywords": metadata.get("keywords", []),
        "file_count": len(record.get("files", [])),
        "file_types": list(set(file_extensions)) if "files" in record else []
    }
    
    logger.info(f"Detected data type for record {record_id}: {result['data_type']} (confidence: {result['confidence']})")
    return result

################################
#   Downloading Files         #
################################

# TODO: Implement this tool

################################
#   Extracting Keywords       #
################################

# TODO: Implement this tool


################################
#             Metadata         #
################################

@mcp.tool()
@_handle_api_error
@_cache_api_response
async def get_metadata(
    record_id: str,
    include_files: bool = True,
    include_versions: bool = True
) -> MetadataResponse:
    """Retrieve detailed metadata for a Zenodo record.
    
    Args:
        record_id: The ID of the Zenodo record
        include_files: Whether to include file information
        include_versions: Whether to include version information
        
    Returns:
        MetadataResponse containing the record metadata
    """
    start_time = time.time()
    
    # Create request object
    request = MetadataRequest(
        record_id=record_id,
        include_files=include_files,
        include_versions=include_versions
    )
    
    # Get client and retrieve metadata
    client = _get_client()
    
    # Get the record metadata
    record = await client._make_request('GET', f'records/{record_id}')
    
    # Create response
    response = MetadataResponse(
        record=record,
        record_id=record_id,
        query_time=time.time() - start_time
    )
    
    logger.info(f"Retrieved metadata for record {record_id}")
    return response

################################
#             Embed             #
################################

# TODO: Implement this tool


################################
#   Listing Files             #
################################



@mcp.tool()
@_handle_api_error
@_cache_api_response
async def list_files(record_id: str, include_metadata: bool = True) -> Dict[str, Any]:
    """List all files available in a Zenodo record.
    
    Args:
        record_id: The ID of the Zenodo record
        include_metadata: Whether to include file metadata
        
    Returns:
        Dictionary containing the list of files and their metadata
    """
    client = _get_client()
    
    # Get the record metadata which includes file information
    record = await client._make_request('GET', f'records/{record_id}')
    
    # Extract file information
    files = []
    if "files" in record:
        for file_info in record["files"]:
            file_data = {
                "filename": file_info.get("filename", ""),
                "size": file_info.get("size", 0),
                "type": file_info.get("type", ""),
                "download_url": file_info.get("links", {}).get("download", "")
            }
            
            # Add additional metadata if requested
            if include_metadata:
                file_data["checksum"] = file_info.get("checksum", "")
                file_data["file_type"] = file_info.get("type", "")
                file_data["mime_type"] = file_info.get("mime_type", "")
            
            files.append(file_data)
    
    logger.info(f"Listed {len(files)} files for record {record_id}")
    
    # Return the file list
    return {
        "record_id": record_id,
        "files": files,
        "total_count": len(files)
    }

################################
#   Comparing Records        #
################################

# TODO: Implement this tool




################################
#   Finding Related Records   #
################################

# TODO: Implement this tool


################################
#   Summarizing Records      #
################################

# TODO: Implement this tool









if __name__ == "__main__":
    # Initialize and run the server
    logger.info("Starting Zenodo MCP server")
    mcp.run(transport='stdio')