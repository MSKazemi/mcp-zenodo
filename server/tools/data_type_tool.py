"""
Tool for detecting the data type of a Zenodo record.
"""

from typing import Dict, Any, Optional
from server.zenodo_client import MCPZenodoClient
from models.request import DataTypeRequest
from models.response import DataTypeResponse
from .registry import tool

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
    name="detect_data_type",
    description="Determines if a Zenodo record is a dataset, software, or article",
    parameters={
        "type": "object",
        "properties": {
            "record_id": {
                "type": "string",
                "description": "The ID of the Zenodo record to analyze"
            }
        },
        "required": ["record_id"]
    }
)
async def detect_data_type(record_id: str) -> Dict[str, Any]:
    """Determine if a Zenodo record is a dataset, software, or article.
    
    Args:
        record_id: The ID of the Zenodo record to analyze
        
    Returns:
        Dictionary containing the detected data type and confidence score
    """
    client = _get_client()
    
    # Fetch the record metadata
    record = await client.get_metadata(record_id)
    
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