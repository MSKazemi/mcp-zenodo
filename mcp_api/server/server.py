"""
Main MCP Server implementation for Zenodo.
"""

import time
from typing import Dict, Any, Optional
from .prompt import PromptAssembler
from .resources import ResourceHandler
from .tools.tools import ToolInvoker
from models.request import MCPRequest
from models.response import MCPResponse

class MCPServer:
    """Main server class for MCP Zenodo integration."""
    
    def __init__(self):
        """Initialize the MCP Server components."""
        self.prompt_assembler = PromptAssembler()
        self.resource_handler = ResourceHandler()
        self.tool_invoker = ToolInvoker()
    
    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle an incoming MCP request.
        
        Args:
            request: The incoming MCP request
            
        Returns:
            MCPResponse containing the processed results
        """
        # Assemble the prompt based on the request
        prompt = await self.prompt_assembler.assemble(request)
        
        # Handle any resource requirements
        resources = await self.resource_handler.prepare(request)
        
        # Invoke necessary tools
        results = await self.tool_invoker.invoke(
            prompt,
            resources,
            request
        )
        
        return results