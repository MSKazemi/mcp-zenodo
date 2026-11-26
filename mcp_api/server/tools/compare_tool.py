"""
Tool for comparing multiple Zenodo records.
"""

from difflib import SequenceMatcher
from itertools import combinations
from typing import Any, Dict, List, Optional

from server.zenodo_client import MCPZenodoClient
from server.text import strip_html
from models.response import CompareRecordsResponse
from .registry import tool

DEFAULT_FIELDS = ["title", "authors", "topics", "publication_date"]
# Values less alike than this are listed under "differences"
DIFFERENCE_THRESHOLD = 0.8
# One request per record, so bound how many a single call may ask for
MAX_RECORDS = 10

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
                "description": "Two to ten Zenodo record IDs to compare"
            },
            "compare_fields": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "Fields to compare: title, authors, topics, publication_date, description, license or another metadata field",
                "default": DEFAULT_FIELDS
            }
        },
        "required": ["record_ids"]
    }
)
async def compare_records(
    record_ids: List[str],
    compare_fields: Optional[List[str]] = None
) -> CompareRecordsResponse:
    """Compare multiple Zenodo records based on specified fields.
    
    Args:
        record_ids: IDs of the records to compare
        compare_fields: Metadata fields to compare
        
    Returns:
        CompareRecordsResponse with comparison results
    """
    # A string would otherwise be read as a list of one-character IDs or fields
    if isinstance(record_ids, str) or isinstance(compare_fields, str):
        raise ValueError("record_ids and compare_fields must be lists")
    record_ids = list(dict.fromkeys(str(record_id) for record_id in record_ids))
    if not 2 <= len(record_ids) <= MAX_RECORDS:
        raise ValueError(f"Provide between 2 and {MAX_RECORDS} different record IDs")
    fields = compare_fields or DEFAULT_FIELDS

    client = _get_client()
    records = {record_id: await client.get_metadata(record_id) for record_id in record_ids}

    field_comparisons: Dict[str, Dict[str, Any]] = {}
    differences: Dict[str, List[Dict[str, str]]] = {}
    averages = []

    for field in fields:
        values = {rid: _extract_field_value(record, field) for rid, record in records.items()}
        scores = {}
        differences[field] = []
        for first, second in combinations(record_ids, 2):
            score = _calculate_similarity(values[first], values[second])
            scores[f"{first}_{second}"] = score
            if score is not None and score < DIFFERENCE_THRESHOLD:
                differences[field].append({
                    "record_id1": first,
                    "record_id2": second,
                    "value1": str(values[first]),
                    "value2": str(values[second])
                })
        known = [score for score in scores.values() if score is not None]
        average = sum(known) / len(known) if known else None
        if average is not None:
            averages.append(average)
        field_comparisons[field] = {
            "similarity_scores": scores,
            "average_similarity": average
        }

    return CompareRecordsResponse(
        record_ids=record_ids,
        field_comparisons=field_comparisons,
        overall_similarity=sum(averages) / len(averages) if averages else 0.0,
        differences=differences
    )

def _extract_field_value(record: Dict[str, Any], field: str) -> Any:
    """Extract a field value from a record.
    
    Args:
        record: Record payload from the records API
        field: Field name to extract
        
    Returns:
        Field value
    """
    metadata = record.get("metadata", {})

    if field in ("authors", "creators"):
        return [creator.get("name", "") for creator in metadata.get("creators", [])]
    if field in ("topics", "keywords"):
        return metadata.get("keywords", [])
    if field == "description":
        return strip_html(metadata.get("description", ""))
    if field == "license":
        return (metadata.get("license") or {}).get("id", "")
    return metadata.get(field, "")

def _calculate_similarity(value1: Any, value2: Any) -> Optional[float]:
    """Calculate similarity between two values.
    
    Args:
        value1: First value
        value2: Second value
        
    Returns:
        Score between 0.0 and 1.0, or None when neither record has the field
    """
    if not value1 and not value2:
        return None
    if not value1 or not value2:
        return 0.0
    if isinstance(value1, list) and isinstance(value2, list):
        # Jaccard similarity for lists such as authors and keywords
        set1 = {str(item).lower() for item in value1}
        set2 = {str(item).lower() for item in value2}
        return len(set1 & set2) / len(set1 | set2)
    return SequenceMatcher(
        None, str(value1).lower(), str(value2).lower(), autojunk=False
    ).ratio()
