"""
Tool for finding related Zenodo records.
"""

import re
from typing import Any, Dict, List, Set

from server.zenodo_client import ANONYMOUS_PAGE_SIZE, MCPZenodoClient
from .registry import tool

# Scores are word and name overlap, so even close relatives score well below 1
DEFAULT_THRESHOLD = 0.05
# Candidates fetched per requested result, to leave room for filtering
CANDIDATES_PER_RESULT = 3
MIN_CANDIDATES = 15
STOP_WORDS = {
    "and", "are", "data", "dataset", "for", "from", "not", "the", "using", "with",
}

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
                "description": (
                    "Minimum similarity score from 0.0 to 1.0, based on shared title words, "
                    "keywords and authors; close relatives often score 0.1 to 0.4"
                ),
                "default": DEFAULT_THRESHOLD
            }
        },
        "required": ["record_id"]
    }
)
async def get_related_records(
    record_id: str,
    max_results: int = 5,
    similarity_threshold: float = DEFAULT_THRESHOLD
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
    max_results = max(max_results, 1)

    # Get the record metadata
    record = await client.get_metadata(record_id)

    # One combined search, because Zenodo limits how often it may be asked
    matches: Dict[str, Dict[str, Any]] = {}
    query = _build_query(record)
    if query:
        size = min(
            max(max_results * CANDIDATES_PER_RESULT, MIN_CANDIDATES), ANONYMOUS_PAGE_SIZE
        )
        response = await client.search_records(query, max_results=size, sort="bestmatch")
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

    # Sort by similarity (ties keep Zenodo's best-match order) and limit results
    related_records = sorted(
        matches.values(), key=lambda x: x["similarity"], reverse=True
    )[:max_results]

    return {
        "record_id": record_id,
        "related_records": related_records,
        "total_count": len(related_records)
    }

def _words(text: str) -> List[str]:
    """Return the distinct meaningful words of ``text``, in order.

    Only letters, digits, "_" and inner dots survive, so none of Zenodo's query
    syntax can reach a search.
    """
    found = re.findall(r"\w+(?:\.\w+)*", (text or "").lower())
    return list(dict.fromkeys(
        word for word in found
        if word not in STOP_WORDS and (len(word) > 2 or not word.isascii())
    ))

def _build_query(record: Dict[str, Any]) -> str:
    """Build one search matching the record's keywords, title words or authors.
    
    Args:
        record: Record payload from the records API
        
    Returns:
        Search query, empty when the record offers nothing to search for
    """
    metadata = record.get("metadata", {})
    phrases = [
        *metadata.get("keywords", [])[:6],
        *(creator.get("name", "") for creator in metadata.get("creators", [])[:3]),
    ]
    terms = [f'"{" ".join(_words(phrase))}"' for phrase in phrases if _words(phrase)]
    terms.extend(_words(metadata.get("title", ""))[:8])
    return " OR ".join(dict.fromkeys(terms))

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

    def keywords(metadata: Dict[str, Any]) -> Set[str]:
        return {k.lower() for k in metadata.get("keywords", [])}

    def creators(metadata: Dict[str, Any]) -> Set[str]:
        return {c.get("name", "").lower() for c in metadata.get("creators", [])}

    title_similarity = _calculate_set_similarity(
        set(_words(metadata1.get("title", ""))), set(_words(metadata2.get("title", "")))
    )
    keyword_similarity = _calculate_set_similarity(keywords(metadata1), keywords(metadata2))
    creator_similarity = _calculate_set_similarity(creators(metadata1), creators(metadata2))

    # Weighted average of similarities
    return (0.4 * title_similarity + 0.3 * keyword_similarity + 0.3 * creator_similarity)

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

    return len(set1 & set2) / len(set1 | set2)
