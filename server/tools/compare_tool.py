"""
Tool for comparing multiple Zenodo records.
"""

from typing import Dict, Any, List, Optional, Union
from server.zenodo_client import MCPZenodoClient
from models.request import CompareRecordsRequest
from models.response import CompareRecordsResponse
from .registry import tool
from difflib import SequenceMatcher
import numpy as np

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
    name="compare_records",
    description="Compares metadata of multiple Zenodo records",
    parameters={
        "type": "object",
        "properties": {
            "record_ids": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "List of Zenodo record IDs to compare"
            },
            "compare_fields": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "Fields to compare (title, authors, topics, etc.)",
                "default": ["title", "authors", "topics", "publication_date"]
            }
        },
        "required": ["record_ids"]
    }
)
async def compare_records(request: CompareRecordsRequest) -> CompareRecordsResponse:
    """
    Compare multiple Zenodo records based on specified fields.
    
    Args:
        request: CompareRecordsRequest containing record IDs and fields to compare
        
    Returns:
        CompareRecordsResponse with comparison results
    """
    record_ids = request.record_ids
    compare_fields = request.compare_fields or ['title', 'creators', 'description', 'keywords']
    
    # Fetch metadata for all records
    records_metadata = {}
    client = _get_client()
    
    for record_id in record_ids:
        try:
            metadata = await client.get_metadata(record_id)
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