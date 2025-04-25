"""
Tool for extracting keywords from Zenodo records.
"""

from typing import Dict, Any, List, Optional
from server.zenodo_client import MCPZenodoClient
from models.request import KeywordsRequest
from models.response import KeywordsResponse
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
    name="extract_keywords",
    description="Extracts top keywords from a Zenodo record's abstract or text",
    parameters={
        "type": "object",
        "properties": {
            "record_id": {
                "type": "string",
                "description": "The ID of the Zenodo record"
            },
            "max_keywords": {
                "type": "integer",
                "description": "Maximum number of keywords to extract",
                "default": 10
            },
            "min_frequency": {
                "type": "integer",
                "description": "Minimum frequency for a term to be considered a keyword",
                "default": 2
            }
        },
        "required": ["record_id"]
    }
)
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
    record = await client.get_metadata(record_id)
    
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