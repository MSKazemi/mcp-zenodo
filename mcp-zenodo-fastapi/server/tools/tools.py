"""
Tool invocation functionality for the MCP Zenodo server.
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
import time
from models.request import MCPRequest, MetadataRequest, DownloadRequest, SummarizeRequest, DataTypeRequest, CitationRequest, ListFilesRequest, RelatedRecordsRequest, CompareRecordsRequest
from models.response import MCPResponse, MetadataResponse, DownloadResponse, SummarizeResponse, DataTypeResponse, CitationResponse, ListFilesResponse, RelatedRecordsResponse, CompareRecordsResponse
from server.zenodo_client import MCPZenodoClient

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from .search_tool import search_records
    from .metadata_tool import get_metadata
    from .download_tool import download_file
    from .summarize_tool import summarize_record
    from .data_type_tool import detect_data_type
    from .citation_tool import get_citation
    from .files_tool import list_files
    from .related_records_tool import get_related_records
    from .compare_tool import compare_records

class ToolInvoker:
    """Invokes necessary tools to process requests."""
    
    def __init__(self, client: Optional[MCPZenodoClient] = None, cache_dir: Optional[str] = None):
        """Initialize the tool invoker.
        
        Args:
            client: Optional MCPZenodoClient instance (defaults to creating a new one)
            cache_dir: Optional directory to cache downloaded files
        """
        self.client = client or MCPZenodoClient()
        self.cache_dir = cache_dir
        self.search_tool = None
        self.metadata_tool = None
        self.download_tool = None
        self.summarize_tool = None
        self.data_type_tool = None
        self.citation_tool = None
        self.files_tool = None
        self.related_tool = None
        self.compare_tool = None
    
    def _get_search_tool(self):
        """Lazy initialization of search tool."""
        if self.search_tool is None:
            from .search_tool import search_records
            self.search_tool = search_records
        return self.search_tool
    
    def _get_metadata_tool(self):
        """Lazy initialization of metadata tool."""
        if self.metadata_tool is None:
            from .metadata_tool import get_metadata
            self.metadata_tool = get_metadata
        return self.metadata_tool
    
    def _get_download_tool(self):
        """Lazy initialization of download tool."""
        if self.download_tool is None:
            from .download_tool import download_file
            self.download_tool = download_file
        return self.download_tool
    
    def _get_summarize_tool(self):
        """Lazy initialization of summarize tool."""
        if self.summarize_tool is None:
            from .summarize_tool import summarize_record
            self.summarize_tool = summarize_record
        return self.summarize_tool
    
    def _get_data_type_tool(self):
        """Lazy initialization of data type detection tool."""
        if self.data_type_tool is None:
            from .data_type_tool import detect_data_type
            self.data_type_tool = detect_data_type
        return self.data_type_tool
    
    def _get_citation_tool(self):
        """Lazy initialization of citation tool."""
        if self.citation_tool is None:
            from .citation_tool import get_citation
            self.citation_tool = get_citation
        return self.citation_tool
    
    def _get_files_tool(self):
        """Lazy initialization of files tool."""
        if self.files_tool is None:
            from .files_tool import list_files
            self.files_tool = list_files
        return self.files_tool
    
    def _get_related_tool(self):
        """Lazy initialization of related records tool."""
        if self.related_tool is None:
            from .related_records_tool import get_related_records
            self.related_tool = get_related_records
        return self.related_tool
    
    def _get_compare_tool(self):
        """Lazy initialization of compare records tool."""
        if self.compare_tool is None:
            from .compare_tool import compare_records
            self.compare_tool = compare_records
        return self.compare_tool
    

    


    async def get_metadata(self, request: MetadataRequest) -> MetadataResponse:
        """Get detailed metadata for a Zenodo record.
        
        Args:
            request: The metadata request containing the record ID
            
        Returns:
            MetadataResponse containing the record metadata
        """
        # Use the metadata tool for metadata requests
        metadata_tool = self._get_metadata_tool()
        return await metadata_tool(
            record_id=request.record_id,
            include_files=request.include_files,
            include_versions=request.include_versions
        )
    
    async def download_file(self, request: DownloadRequest) -> DownloadResponse:
        """Download a specific file from a Zenodo record.
        
        Args:
            request: The download request containing the record ID and file name
            
        Returns:
            DownloadResponse containing the file path and metadata
        """
        # Use the download tool for file downloads
        download_tool = self._get_download_tool()
        return await download_tool(
            record_id=request.record_id,
            file_name=request.file_name,
            force_download=request.force_download
        )
    
    async def summarize_record(self, request: SummarizeRequest) -> SummarizeResponse:
        """Build a summary from a Zenodo record's metadata.
        
        Args:
            request: The summarize request containing the record ID and options
            
        Returns:
            SummarizeResponse containing the record summary
        """
        # Use the summarize tool for record summarization
        summarize_tool = self._get_summarize_tool()
        return await summarize_tool(
            record_id=request.record_id,
            include_files=request.include_files,
            include_versions=request.include_versions,
            max_length=request.max_length
        )
    
    async def detect_data_type(self, request: DataTypeRequest) -> DataTypeResponse:
        """Determine if a Zenodo record is a dataset, software, or article.
        
        Args:
            request: The data type request containing the record ID
            
        Returns:
            DataTypeResponse containing the detected data type and confidence
        """
        # Use the data type detection tool
        data_type_tool = self._get_data_type_tool()
        result = await data_type_tool(record_id=request.record_id)
        
        # Convert to response model
        return DataTypeResponse(
            record_id=result["record_id"],
            data_type=result["data_type"],
            confidence=result["confidence"],
            metadata=result["metadata"]
        )
    
    async def get_citation(self, request: CitationRequest) -> CitationResponse:
        """Get a citation for a Zenodo record.
        
        Args:
            request: The citation request containing the record ID and format
            
        Returns:
            CitationResponse containing the citation
        """
        # Use the citation tool
        citation_tool = self._get_citation_tool()
        result = await citation_tool(
            record_id=request.record_id,
            format=request.format
        )
        
        # Convert to response model
        return CitationResponse(
            citation=result["citation"],
            format=result["format"],
            record_id=result["record_id"],
            query_time=0.0  # We don't track query time in the tool
        )
    
    async def list_files(self, request: ListFilesRequest) -> ListFilesResponse:
        """List files available in a Zenodo record.
        
        Args:
            request: The list files request containing the record ID
            
        Returns:
            ListFilesResponse containing the list of files
        """
        # Use the files tool
        files_tool = self._get_files_tool()
        result = await files_tool(
            record_id=request.record_id,
            include_metadata=request.include_metadata
        )
        
        # Convert to response model
        return ListFilesResponse(
            record_id=result["record_id"],
            files=result["files"],
            total_count=result["total_count"],
            query_time=0.0  # We don't track query time in the tool
        )
    
    async def get_related_records(self, request: RelatedRecordsRequest) -> RelatedRecordsResponse:
        """Find records related to a given Zenodo record.
        
        Args:
            request: The related records request containing the record ID and options
            
        Returns:
            RelatedRecordsResponse containing the related records
        """
        # Use the related records tool
        related_tool = self._get_related_tool()
        result = await related_tool(
            record_id=request.record_id,
            max_results=request.max_results,
            similarity_threshold=request.similarity_threshold
        )
        
        # Convert to response model
        return RelatedRecordsResponse(
            record_id=result["record_id"],
            related_records=result["related_records"],
            total_count=result["total_count"],
            query_time=0.0  # We don't track query time in the tool
        )
    
    async def compare_records(self, request: CompareRecordsRequest) -> CompareRecordsResponse:
        """Compare multiple Zenodo records.
        
        Args:
            request: The compare records request containing the record IDs and fields to compare
            
        Returns:
            CompareRecordsResponse containing the comparison results
        """
        # Use the compare records tool
        compare_tool = self._get_compare_tool()
        result = await compare_tool(
            record_ids=request.record_ids,
            compare_fields=request.compare_fields
        )
        
        # Convert to response model
        return CompareRecordsResponse(
            record_ids=result["record_ids"],
            comparison=result["comparison"],
            total_records=result["total_records"]
        ) 
    
    async def invoke(
        self,
        prompt: Dict[str, Any],
        resources: Dict[str, Any],
        request: MCPRequest
    ) -> MCPResponse:
        """Invoke necessary tools to process the request.
        
        This function acts as a dispatcher that takes an MCP request and routes it to the appropriate tool.
        Currently, it only handles search requests by delegating to the search_tool to perform Zenodo searches.
        
        The function takes a prompt dictionary and resources dictionary which appear to be unused currently,
        suggesting this may be extended in the future to handle other types of requests or processing.
        
        Args:
            prompt: The assembled prompt dictionary (currently unused)
            resources: The prepared resources dictionary (currently unused) 
            request: The original MCP request containing search parameters like query, filters, pagination etc.
            
        Returns:
            MCPResponse containing the search results from Zenodo
        """
        # Use the search tool for search requests
        search_tool = self._get_search_tool()
        return await search_tool(
            query=request.query,
            filters=request.filters,
            page=request.page,
            size=request.size,
            sort_by=request.sort_by
        )
