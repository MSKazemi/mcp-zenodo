from mcp.server.fastmcp import FastMCP
from typing import Dict, Any, Optional, List, Union
from zenodo_client import MCPZenodoClient
from models.request import DataTypeRequest, DownloadRequest, MetadataRequest, SummarizeRequest, CitationRequest, ListFilesRequest, RelatedRecordsRequest, CompareRecordsRequest
from models.response import DataTypeResponse, DownloadResponse, MetadataResponse, SummarizeResponse, CitationResponse, ListFilesResponse, RelatedRecordsResponse, CompareRecordsResponse, EmbedResponse
import os
import time
from pathlib import Path
import numpy as np
from difflib import SequenceMatcher





# Initialize FastMCP server
mcp = FastMCP("Zenodo")

# Initialize the client
_client = None
_cache_dir = os.path.join(os.path.expanduser("~"), ".zenodo_cache")

# Create cache directory if it doesn't exist
os.makedirs(_cache_dir, exist_ok=True)

def _get_client() -> MCPZenodoClient:
    """Get or create the MCPZenodoClient instance.
    
    Returns:
        MCPZenodoClient instance
    """
    global _client
    if _client is None:
        _client = MCPZenodoClient()
    return _client

"""
Tool for detecting the data type of a Zenodo record.
"""

@mcp.tool()
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
    
    # Check for software indicators
    if "keywords" in metadata and any(kw.lower() in ["software", "code", "program"] for kw in metadata["keywords"]):
        result["data_type"] = "software"
        result["confidence"] = 0.8
    # Check for dataset indicators
    elif "keywords" in metadata and any(kw.lower() in ["dataset", "data", "measurement"] for kw in metadata["keywords"]):
        result["data_type"] = "dataset"
        result["confidence"] = 0.8
    # Check for article indicators
    elif "keywords" in metadata and any(kw.lower() in ["article", "paper", "publication"] for kw in metadata["keywords"]):
        result["data_type"] = "article"
        result["confidence"] = 0.8
    
    # Check file extensions as a fallback
    if result["data_type"] == "unknown" and "files" in record:
        file_extensions = [f.get("filename", "").split(".")[-1].lower() for f in record["files"] if "." in f.get("filename", "")]
        
        # Software indicators
        if any(ext in ["py", "js", "java", "cpp", "c", "h", "r", "matlab"] for ext in file_extensions):
            result["data_type"] = "software"
            result["confidence"] = 0.6
        # Dataset indicators
        elif any(ext in ["csv", "tsv", "json", "xml", "hdf5", "nc", "npy", "npz"] for ext in file_extensions):
            result["data_type"] = "dataset"
            result["confidence"] = 0.6
        # Article indicators
        elif any(ext in ["pdf", "doc", "docx", "tex"] for ext in file_extensions):
            result["data_type"] = "article"
            result["confidence"] = 0.6
    
    # Store relevant metadata for reference
    result["metadata"] = {
        "title": metadata.get("title", ""),
        "description": metadata.get("description", ""),
        "keywords": metadata.get("keywords", []),
        "file_count": len(record.get("files", [])),
        "file_types": list(set(file_extensions)) if "files" in record else []
    }
    
    return result

"""
Download tool implementation for Zenodo API.
"""

@mcp.tool()
async def download_file(
    record_id: str,
    file_name: str,
    force_download: bool = False
) -> DownloadResponse:
    """Download a specific file from a Zenodo record.
    
    Args:
        record_id: The ID of the Zenodo record
        filename: The name of the file to download
        force_download: Whether to force download the file
        
    Returns:
        DownloadResponse containing the file path and metadata
    """
    start_time = time.time()
    
    # Create request object
    request = DownloadRequest(
        record_id=record_id,
        file_name=file_name,
        force_download=force_download
    )
    
    # Get client and download file
    client = _get_client()
    
    # Check if file is already cached
    cache_path = os.path.join(_cache_dir, f"{record_id}_{file_name}")
    if os.path.exists(cache_path):
        # Return cached file
        return DownloadResponse(
            file_path=cache_path,
            record_id=record_id,
            file_name=file_name,
            file_size=os.path.getsize(cache_path),
            query_time=time.time() - start_time
        )
    
    # Get file metadata to find download URL
    record = await client._make_request('GET', f'records/{record_id}')
    files = record.get('files', [])
    
    # Find the requested file
    file_info = None
    for f in files:
        if f.get('filename') == file_name:
            file_info = f
            break
    
    if not file_info:
        return DownloadResponse(
            record_id=record_id,
            file_name=file_name,
            query_time=time.time() - start_time,
            error=f"File '{file_name}' not found in record {record_id}"
        )
    
    # Download the file
    download_url = file_info.get('links', {}).get('download')
    if not download_url:
        return DownloadResponse(
            record_id=record_id,
            file_name=file_name,
            query_time=time.time() - start_time,
            error=f"Download URL not found for file '{file_name}'"
        )
    
    # Create cache directory if it doesn't exist
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    
    # Download the file
    session = await client._get_session()
    async with session.get(download_url) as response:
        if response.status != 200:
            return DownloadResponse(
                record_id=record_id,
                file_name=file_name,
                query_time=time.time() - start_time,
                error=f"Failed to download file: HTTP {response.status}"
            )
        
        # Save the file to cache
        with open(cache_path, 'wb') as f:
            f.write(await response.read())
    
    # Return response
    return DownloadResponse(
        file_path=cache_path,
        record_id=record_id,
        file_name=file_name,
        file_size=os.path.getsize(cache_path),
        query_time=time.time() - start_time
    )

"""
Tool for extracting keywords from Zenodo records.
"""

@mcp.tool()
async def extract_keywords(
    record_id: str,
    max_keywords: int = 10,
    min_frequency: int = 2
) -> Dict[str, Any]:
    """Extract top keywords from a Zenodo record's abstract or text.
    
    Args:
        record_id: The ID of the Zenodo record
        max_keywords: Maximum number of keywords to extract
        min_frequency: Minimum frequency for a term to be considered a keyword
        
    Returns:
        Dictionary containing the extracted keywords and their frequencies
    """
    client = _get_client()
    
    # Get the record metadata
    record = await client._make_request('GET', f'records/{record_id}')
    
    # Extract text from the record
    text = ""
    
    # Add title
    if "title" in record.get("metadata", {}):
        text += record["metadata"]["title"] + " "
    
    # Add description/abstract
    if "description" in record.get("metadata", {}):
        text += record["metadata"]["description"] + " "
    
    # Add keywords if available
    if "keywords" in record.get("metadata", {}):
        text += " ".join(record["metadata"]["keywords"]) + " "
    
    # Extract keywords using a simple frequency-based approach
    keywords = _extract_keywords_from_text(text, max_keywords, min_frequency)
    
    # Return the keywords
    return {
        "record_id": record_id,
        "keywords": keywords,
        "total_count": len(keywords)
    }

def _extract_keywords_from_text(text: str, max_keywords: int, min_frequency: int) -> List[Dict[str, Any]]:
    """Extract keywords from text using a simple frequency-based approach.
    
    Args:
        text: The text to extract keywords from
        max_keywords: Maximum number of keywords to extract
        min_frequency: Minimum frequency for a term to be considered a keyword
        
    Returns:
        List of dictionaries containing keywords and their frequencies
    """
    import re
    from collections import Counter
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters and digits
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', '', text)
    
    # Split into words
    words = text.split()
    
    # Remove common words (stop words)
    stop_words = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 'has', 'he',
        'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 'to', 'was', 'were',
        'will', 'with', 'the', 'this', 'but', 'they', 'have', 'had', 'what', 'when',
        'where', 'who', 'which', 'why', 'how', 'all', 'any', 'both', 'each', 'few',
        'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
        'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now'
    }
    
    # Filter out stop words and short words
    filtered_words = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Count word frequencies
    word_counts = Counter(filtered_words)
    
    # Get the most common words
    keywords = []
    for word, count in word_counts.most_common(max_keywords):
        if count >= min_frequency:
            keywords.append({
                "keyword": word,
                "frequency": count
            })
    
    return keywords

"""
Metadata tool implementation for Zenodo API.
"""

@mcp.tool()
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
    
    try:
        # Get the record metadata
        record = await client._make_request('GET', f'records/{record_id}')
        
        # Create response
        response = MetadataResponse(
            record=record,
            record_id=record_id,
            query_time=time.time() - start_time
        )
        
        return response
    except Exception as e:
        return MetadataResponse(
            record={},
            record_id=record_id,
            query_time=time.time() - start_time,
            error=str(e)
        )

"""
Embed tool implementation for Zenodo API.
"""

@mcp.tool()
async def generate_embed_link(
    record_id: str
) -> EmbedResponse:
    """Generate an embeddable link for a Zenodo record.
    
    Args:
        record_id: The ID of the Zenodo record
        
    Returns:
        EmbedResponse containing the embeddable link and metadata
    """
    start_time = time.time()
    
    # Generate embed URL directly
    embed_url = f"https://zenodo.org/record/{record_id}/embed"
    
    # For simplicity, we'll assume it's a dataset by default
    # In a real implementation, you might want to check the record type
    record_type = "dataset"
    
    # Create response
    response = EmbedResponse(
        embed_url=embed_url,
        record_id=record_id,
        record_type=record_type,
        query_time=time.time() - start_time
    )
    
    return response

"""
Tool for listing files in Zenodo records.
"""

@mcp.tool()
async def list_files(record_id: str, include_metadata: bool = True) -> Dict[str, Any]:
    """List all files available in a Zenodo record.
    
    Args:
        record_id: The ID of the Zenodo record
        include_metadata: Whether to include file metadata
        
    Returns:
        Dictionary containing the list of files and their metadata
    """
    client = _get_client()
    
    try:
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
        
        # Return the file list
        return {
            "record_id": record_id,
            "files": files,
            "total_count": len(files)
        }
    except Exception as e:
        return {
            "record_id": record_id,
            "files": [],
            "total_count": 0,
            "error": str(e)
        }

"""
Tool for comparing multiple Zenodo records.
"""

@mcp.tool()
async def compare_records(request: CompareRecordsRequest) -> CompareRecordsResponse:
    """
    Compare multiple Zenodo records based on specified fields.
    
    Args:
        request: CompareRecordsRequest containing record IDs and fields to compare
        
    Returns:
        CompareRecordsResponse with comparison results
    """
    record_ids = request.record_ids
    compare_fields = request.compare_fields or ['title', 'authors', 'topics', 'publication_date']
    
    # Fetch metadata for all records
    records_metadata = {}
    client = _get_client()
    
    for record_id in record_ids:
        try:
            metadata = await client._make_request('GET', f'records/{record_id}')
            records_metadata[record_id] = metadata
        except Exception as e:
            print(f"Error fetching metadata for record {record_id}: {str(e)}")
            continue
    
    if len(records_metadata) < 2:
        raise ValueError("At least two valid records are required for comparison")
    
    # Compare fields and calculate similarities
    field_comparisons = {}
    differences = {}
    
    for field in compare_fields:
        field_values = {}
        for record_id, metadata in records_metadata.items():
            field_values[record_id] = extract_field_value(metadata, field)
        
        # Calculate similarity scores
        similarity_scores = {}
        field_differences = []
        
        for i, (record_id1, value1) in enumerate(field_values.items()):
            for record_id2, value2 in list(field_values.items())[i+1:]:
                similarity = calculate_similarity(value1, value2)
                key = f"{record_id1}_{record_id2}"
                similarity_scores[key] = similarity
                
                if similarity < 0.8:  # Threshold for considering values different
                    field_differences.append({
                        "record_id1": record_id1,
                        "record_id2": record_id2,
                        "value1": str(value1),
                        "value2": str(value2)
                    })
        
        field_comparisons[field] = {
            "similarity_scores": similarity_scores,
            "average_similarity": np.mean(list(similarity_scores.values())) if similarity_scores else 0.0
        }
        differences[field] = field_differences
    
    # Calculate overall similarity
    overall_similarity = np.mean([
        field_data["average_similarity"] 
        for field_data in field_comparisons.values()
    ])
    
    return CompareRecordsResponse(
        record_ids=record_ids,
        field_comparisons=field_comparisons,
        overall_similarity=overall_similarity,
        differences=differences
    )

def extract_field_value(metadata: Dict, field: str) -> Union[str, List, Dict]:
    """Extract field value from metadata dictionary."""
    if field == 'creators':
        return [creator.get('name', '') for creator in metadata.get('creators', [])]
    elif field == 'keywords':
        return metadata.get('keywords', [])
    else:
        return metadata.get(field, '')

def calculate_similarity(value1: Union[str, List, Dict], value2: Union[str, List, Dict]) -> float:
    """Calculate similarity between two values."""
    if isinstance(value1, list) and isinstance(value2, list):
        # For lists (e.g., creators, keywords), use Jaccard similarity
        set1 = set(str(x).lower() for x in value1)
        set2 = set(str(x).lower() for x in value2)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0
    else:
        # For strings, use sequence matcher
        str1 = str(value1).lower()
        str2 = str(value2).lower()
        return SequenceMatcher(None, str1, str2).ratio()

def _compare_records_metadata(records: List[Dict[str, Any]], compare_fields: List[str]) -> Dict[str, Any]:
    """Compare metadata of multiple records.
    
    Args:
        records: List of record metadata dictionaries
        compare_fields: Fields to compare
        
    Returns:
        Dictionary containing comparison results
    """
    comparison = {}
    
    # Compare each field
    for field in compare_fields:
        field_comparison = {}
        
        # Extract field values from each record
        field_values = []
        for i, record in enumerate(records):
            value = _extract_field_value(record, field)
            field_values.append({
                "record_id": record.get("id", f"record_{i}"),
                "value": value
            })
        
        # Compare field values
        field_comparison["values"] = field_values
        
        # Calculate similarity scores
        similarity_scores = []
        for i in range(len(records)):
            for j in range(i + 1, len(records)):
                score = _calculate_similarity(field_values[i]["value"], field_values[j]["value"])
                similarity_scores.append({
                    "record_id_1": field_values[i]["record_id"],
                    "record_id_2": field_values[j]["record_id"],
                    "score": score
                })
        
        field_comparison["similarity_scores"] = similarity_scores
        comparison[field] = field_comparison
    
    return comparison

def _extract_field_value(record: Dict[str, Any], field: str) -> Any:
    """Extract a field value from a record.
    
    Args:
        record: Record metadata dictionary
        field: Field name to extract
        
    Returns:
        Field value
    """
    metadata = record.get("metadata", {})
    
    if field == "title":
        return metadata.get("title", "")
    elif field == "authors":
        return [creator.get("name", "") for creator in metadata.get("creators", [])]
    elif field == "topics":
        return metadata.get("keywords", [])
    elif field == "publication_date":
        return metadata.get("publication_date", "")
    elif field == "description":
        return metadata.get("description", "")
    elif field == "license":
        return metadata.get("license", {}).get("id", "")
    else:
        return metadata.get(field, "")

def _calculate_similarity(value1: Any, value2: Any) -> float:
    """Calculate similarity between two values.
    
    Args:
        value1: First value
        value2: Second value
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    # Handle different types of values
    if isinstance(value1, str) and isinstance(value2, str):
        return _calculate_string_similarity(value1, value2)
    elif isinstance(value1, list) and isinstance(value2, list):
        return _calculate_list_similarity(value1, value2)
    else:
        # For other types, convert to string and compare
        return _calculate_string_similarity(str(value1), str(value2))

def _calculate_string_similarity(str1: str, str2: str) -> float:
    """Calculate similarity between two strings.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    # Simple implementation using Levenshtein distance
    if not str1 or not str2:
        return 0.0
    
    # Convert to lowercase for case-insensitive comparison
    str1 = str1.lower()
    str2 = str2.lower()
    
    # Calculate Levenshtein distance
    distance = _levenshtein_distance(str1, str2)
    
    # Calculate similarity score
    max_length = max(len(str1), len(str2))
    if max_length == 0:
        return 1.0
    
    return 1.0 - (distance / max_length)

def _calculate_list_similarity(list1: List[Any], list2: List[Any]) -> float:
    """Calculate similarity between two lists.
    
    Args:
        list1: First list
        list2: Second list
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not list1 or not list2:
        return 0.0
    
    # Convert lists to sets for intersection calculation
    set1 = set(str(item).lower() for item in list1)
    set2 = set(str(item).lower() for item in list2)
    
    # Calculate Jaccard similarity
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    if union == 0:
        return 0.0
    
    return intersection / union

def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Levenshtein distance
    """
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1] 


"""
Tool for retrieving citations for Zenodo records.
"""

@mcp.tool()
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
    
    try:
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
        
        # Create and return response
        return CitationResponse(
            record_id=record_id,
            citation=citation,
            format=format,
            query_time=time.time() - start_time
        )
    except Exception as e:
        return CitationResponse(
            record_id=record_id,
            citation="",
            format=format,
            query_time=time.time() - start_time,
            error=str(e)
        )

"""
Tool for finding related Zenodo records.
"""

@mcp.tool()
async def get_related_records(
    record_id: str,
    max_results: int = 5,
    similarity_threshold: float = 0.3
) -> Dict[str, Any]:
    """Find records related to a given Zenodo record.
    
    Args:
        record_id: The ID of the Zenodo record
        max_results: Maximum number of related records to return
        similarity_threshold: Minimum similarity score (0.0 to 1.0)
        
    Returns:
        Dictionary containing related records
    """
    client = _get_client()
    
    # Get the record metadata
    record = await client._make_request('GET', f'records/{record_id}')
    
    # Extract search terms from the record
    search_terms = _extract_search_terms(record)
    
    # Search for related records
    related_records = []
    for term in search_terms:
        results = await client._make_request('GET', 'records', params={"q": term, "size": max_results})
        hits = results.get('hits', {}).get('hits', [])
        
        for result in hits:
            if result["id"] != record_id:  # Exclude the original record
                similarity = _calculate_similarity(record, result)
                if similarity >= similarity_threshold:
                    related_records.append({
                        "record_id": result["id"],
                        "title": result.get("metadata", {}).get("title", ""),
                        "similarity": similarity
                    })
    
    # Sort by similarity and limit results
    related_records.sort(key=lambda x: x["similarity"], reverse=True)
    related_records = related_records[:max_results]
    
    return {
        "record_id": record_id,
        "related_records": related_records,
        "total_count": len(related_records)
    }

def _extract_search_terms(record: Dict[str, Any]) -> List[str]:
    """Extract search terms from a record.
    
    Args:
        record: Record metadata dictionary
        
    Returns:
        List of search terms
    """
    terms = []
    metadata = record.get("metadata", {})
    
    # Add title
    if "title" in metadata:
        terms.append(metadata["title"])
    
    # Add keywords
    if "keywords" in metadata:
        terms.extend(metadata["keywords"])
    
    # Add creators
    if "creators" in metadata:
        for creator in metadata["creators"]:
            if "name" in creator:
                terms.append(creator["name"])
    
    return terms

def _calculate_similarity(record1: Dict[str, Any], record2: Dict[str, Any]) -> float:
    """Calculate similarity between two records.
    
    Args:
        record1: First record metadata dictionary
        record2: Second record metadata dictionary
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    metadata1 = record1.get("metadata", {})
    metadata2 = record2.get("metadata", {})
    
    # Compare titles
    title1 = metadata1.get("title", "").lower()
    title2 = metadata2.get("title", "").lower()
    title_similarity = _calculate_string_similarity(title1, title2)
    
    # Compare keywords
    keywords1 = set(k.lower() for k in metadata1.get("keywords", []))
    keywords2 = set(k.lower() for k in metadata2.get("keywords", []))
    keyword_similarity = _calculate_set_similarity(keywords1, keywords2)
    
    # Compare creators
    creators1 = set(c.get("name", "").lower() for c in metadata1.get("creators", []))
    creators2 = set(c.get("name", "").lower() for c in metadata2.get("creators", []))
    creator_similarity = _calculate_set_similarity(creators1, creators2)
    
    # Weighted average of similarities
    return (0.4 * title_similarity + 0.3 * keyword_similarity + 0.3 * creator_similarity)

def _calculate_string_similarity(str1: str, str2: str) -> float:
    """Calculate similarity between two strings.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not str1 or not str2:
        return 0.0
    
    # Simple word overlap similarity
    words1 = set(str1.split())
    words2 = set(str2.split())
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    if union == 0:
        return 0.0
    
    return intersection / union

def _calculate_set_similarity(set1: set, set2: set) -> float:
    """Calculate Jaccard similarity between two sets.
    
    Args:
        set1: First set
        set2: Second set
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not set1 or not set2:
        return 0.0
    
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    
    if union == 0:
        return 0.0
    
    return intersection / union

"""
Summarize tool implementation for Zenodo API.
"""

@mcp.tool()
async def summarize_record(
    record_id: str,
    include_files: bool = False,
    include_versions: bool = False,
    max_length: int = 500
) -> SummarizeResponse:
    """Generate a summary from a Zenodo record's metadata.
    
    Args:
        record_id: The ID of the Zenodo record
        include_files: Whether to include file information in the summary
        include_versions: Whether to include version information in the summary
        max_length: Maximum length of the summary in characters
        
    Returns:
        SummarizeResponse containing the generated summary
    """
    start_time = time.time()
    
    # Get client
    client = _get_client()
    
    try:
        # Get the full metadata using the client
        metadata = await client._make_request('GET', f'records/{record_id}')
        
        # Create base summary
        summary_dict = {
            "record_id": record_id,
            "title": metadata.get("metadata", {}).get("title", ""),
            "summary_text": metadata.get("metadata", {}).get("description", "")[:max_length],
            "publication_date": metadata.get("metadata", {}).get("publication_date", ""),
            "resource_type": metadata.get("metadata", {}).get("resource_type", {}),
            "access_right": metadata.get("metadata", {}).get("access_right", ""),
            "creators": metadata.get("metadata", {}).get("creators", [])
        }
        
        # Add file information if requested
        if include_files and "files" in metadata:
            summary_dict["files"] = {
                "count": len(metadata["files"]),
                "total_size": sum(f.get("size", 0) for f in metadata["files"]),
                "file_types": list(set(f.get("key", "").split(".")[-1] for f in metadata["files"] if "." in f.get("key", "")))
            }
        
        # Add version information if requested
        if include_versions and "relations" in metadata.get("metadata", {}):
            versions = metadata["metadata"]["relations"].get("version", [])
            summary_dict["versions"] = {
                "count": len(versions),
                "is_latest": any(v.get("is_last", False) for v in versions),
                "parent_id": versions[0].get("parent", {}).get("pid_value") if versions else None
            }
        
        # Format the summary dictionary into a string
        formatted_summary = _format_summary(summary_dict)
        
        # Create response
        response = SummarizeResponse(
            record_id=record_id,
            summary=formatted_summary,
            query_time=time.time() - start_time
        )
        
        return response
    except Exception as e:
        return SummarizeResponse(
            record_id=record_id,
            summary="",
            query_time=time.time() - start_time,
            error=str(e)
        )

def _format_summary(summary_dict: Dict[str, Any]) -> str:
    """Format the summary dictionary into a readable string.
    
    Args:
        summary_dict: Dictionary containing summary information
        
    Returns:
        Formatted summary string
    """
    lines = []
    
    # Add title
    lines.append(f"Title: {summary_dict['title']}")
    
    # Add description
    lines.append(f"\nDescription: {summary_dict['summary_text']}")
    
    # Add publication date
    lines.append(f"\nPublication Date: {summary_dict['publication_date']}")
    
    # Add resource type
    if isinstance(summary_dict['resource_type'], dict):
        resource_type = summary_dict['resource_type'].get('title', '')
    else:
        resource_type = str(summary_dict['resource_type'])
    lines.append(f"Resource Type: {resource_type}")
    
    # Add access right
    lines.append(f"Access Right: {summary_dict['access_right']}")
    
    # Add creators
    creators = [f"{c.get('name', '')}" for c in summary_dict['creators']]
    lines.append(f"Creators: {', '.join(creators)}")
    
    # Add file information if present
    if 'files' in summary_dict:
        files = summary_dict['files']
        lines.append(f"\nFiles:")
        lines.append(f"- Count: {files['count']}")
        lines.append(f"- Total Size: {files['total_size']} bytes")
        lines.append(f"- File Types: {', '.join(files['file_types'])}")
    
    # Add version information if present
    if 'versions' in summary_dict:
        versions = summary_dict['versions']
        lines.append(f"\nVersions:")
        lines.append(f"- Count: {versions['count']}")
        lines.append(f"- Latest Version: {'Yes' if versions['is_latest'] else 'No'}")
        if versions['parent_id']:
            lines.append(f"- Parent ID: {versions['parent_id']}")
    
    return "\n".join(lines)



"""
Tool for searching Zenodo records.
"""

# Create a single client instance for the tool
client = MCPZenodoClient()

@mcp.tool()
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
    try:
        # Prepare search parameters
        params = {
            "q": query,
            "size": max_results,
            "sort": sort
        }
        
        # Make the search request
        response = await client._make_request('GET', 'records', params=params)
        
        # Extract and format the results
        hits = response.get('hits', {})
        results = hits.get('hits', [])
        total = hits.get('total', 0)
        
        return {
            "query": query,
            "total_results": total,
            "records": results
        }
    except Exception as e:
        return {
            "query": query,
            "error": str(e),
            "total_results": 0,
            "records": []
        }


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')