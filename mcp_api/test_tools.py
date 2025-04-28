"""
Test script for the Zenodo MCP tools.
"""

import asyncio
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.server.tools.data_type_tool import detect_data_type
from server.server.tools.citation_tool import get_citation
from server.server.tools.files_tool import list_files
from server.server.tools.related_tool import get_related_records

async def main():
    """Run tests for the Zenodo MCP tools."""
    # Test record ID (replace with an actual Zenodo record ID)
    record_id = "1234567"
    
    print("Testing Zenodo MCP tools...")
    
    try:
        # Test data type detection
        print("\n1. Testing data type detection...")
        result = await detect_data_type(record_id)
        print(f"Detected type: {result['data_type']}")
        print(f"Confidence: {result['confidence']}")
        
        # Test citation retrieval
        print("\n2. Testing citation retrieval...")
        result = await get_citation(record_id, format="bibtex")
        print(f"Citation format: {result['format']}")
        print(f"Citation: {result['citation'][:100]}...")  # Print first 100 chars
        
        # Test file listing
        print("\n3. Testing file listing...")
        result = await list_files(record_id)
        print(f"Total files: {result['total_count']}")
        for i, file_info in enumerate(result['files'][:3]):  # Show first 3 files
            print(f"  {i+1}. {file_info['filename']} ({file_info['size']} bytes)")
        
        # Test related records
        print("\n4. Testing related records...")
        result = await get_related_records(record_id, max_results=3)
        print(f"Total related records: {result['total_count']}")
        for i, related in enumerate(result['related_records']):
            print(f"  {i+1}. {related['title']} (similarity: {related['similarity']:.2f})")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 