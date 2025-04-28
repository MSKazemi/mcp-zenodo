"""
Test script for the data type detection tool.
"""

import asyncio
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.server.tools.data_type_tool import detect_data_type

async def main():
    """Run a test of the data type detection tool."""
    # Test with a known software record
    software_record_id = "1234567"  # Replace with an actual Zenodo record ID for software
    
    # Test with a known dataset record
    dataset_record_id = "7654321"  # Replace with an actual Zenodo record ID for a dataset
    
    # Test with a known article record
    article_record_id = "9876543"  # Replace with an actual Zenodo record ID for an article
    
    # Run the tests
    print("Testing data type detection...")
    
    try:
        # Test software detection
        result = await detect_data_type(software_record_id)
        print(f"\nSoftware record ({software_record_id}):")
        print(f"Detected type: {result['data_type']}")
        print(f"Confidence: {result['confidence']}")
        
        # Test dataset detection
        result = await detect_data_type(dataset_record_id)
        print(f"\nDataset record ({dataset_record_id}):")
        print(f"Detected type: {result['data_type']}")
        print(f"Confidence: {result['confidence']}")
        
        # Test article detection
        result = await detect_data_type(article_record_id)
        print(f"\nArticle record ({article_record_id}):")
        print(f"Detected type: {result['data_type']}")
        print(f"Confidence: {result['confidence']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 