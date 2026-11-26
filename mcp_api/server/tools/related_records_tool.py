"""
Tool for finding related Zenodo records.
"""

import re
from typing import Dict, Any, List
from server.zenodo_client import MCPZenodoClient
from .registry import tool

# Upper bound on searches issued for a single lookup
MAX_SEARCH_TERMS = 10
# Largest page Zenodo serves to requests without a token
MAX_PAGE_SIZE = 25
# Characters and words that Zenodo's search reads as query syntax
QUERY_SYNTAX = re.compile(r'[-+=&|><!(){}\[\]^"~*?:\\/]|\b(?:AND|OR|NOT)\b')

# Initialize the client
_client = None

def _get_client() -> MCPZenodoClient:
    """Get or create the MCPZenodoClient instance.
    
    Returns:
        MCPZenodoClient instance
    """
    global _client
    if _client is None:
        _client = MCPZenodoClient()
    return _client

@tool(
    name="get_related_records",
    description="Find records related to a given Zenodo record",
    parameters={
        "type": "object",
        "properties": {
            "record_id": {
                "type": "string",
                "description": "The ID of the Zenodo record"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of related records to return",
                "default": 5
            },
            "similarity_threshold": {
                "type": "number",
                "description": "Minimum similarity score (0.0 to 1.0)",
                "default": 0.3
            }
        },
        "required": ["record_id"]
    }
)
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
    record = await client.get_metadata(record_id)
    
    # Extract search terms from the record
    search_terms = _extract_search_terms(record)
    
    # Search for related records, keyed by ID so each appears once
    matches: Dict[str, Dict[str, Any]] = {}
    for term in search_terms:
        # One extra, because the source record usually matches itself
        response = await client.search_records(
            term, max_results=min(max_results + 1, MAX_PAGE_SIZE)
        )
        for result in response.get("hits", {}).get("hits", []):
            result_id = str(result["id"])
            if result_id == str(record_id) or result_id in matches:
                continue  # Skip the original record and repeats
            similarity = _calculate_similarity(record, result)
            if similarity >= similarity_threshold:
                matches[result_id] = {
                    "record_id": result_id,
                    "title": result.get("metadata", {}).get("title", ""),
                    "similarity": similarity
                }
    related_records = list(matches.values())

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
    
    # Titles and names are plain text; raw punctuation can make Zenodo answer 500
    cleaned = [" ".join(QUERY_SYNTAX.sub(" ", term).split()) for term in terms]
    # One request per term: cap them so a record with many authors stays usable
    return list(dict.fromkeys(term for term in cleaned if term))[:MAX_SEARCH_TERMS]

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