"""
FastAPI application entry point for MCP Zenodo integration.
"""

from fastapi import FastAPI, HTTPException
from server.tools.registry import get_openai_tool_specs, dispatch_tool_call
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from .server import MCPServer
from models.request import MCPRequest
from models.response import MCPResponse

class ToolCallRequest(BaseModel):
    """Request model for tool calls."""
    name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(..., description="Arguments to pass to the tool")

class ToolCallResponse(BaseModel):
    """Response model for tool calls."""
    result: Any = Field(..., description="Result returned by the tool")
    execution_time: float = Field(..., description="Time taken to execute the tool in seconds")

# Initialize the MCP server
mcp_server = MCPServer()

app = FastAPI(
    title="MCP Zenodo Integration",
    description="Model Context Protocol integration with Zenodo research data repository",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "message": "MCP Zenodo Integration API",
        "version": "0.1.0",
        "documentation": "/docs"
    }

@app.get("/mcp/tools/openai-schema")
async def list_openai_compatible_tools():
    """List OpenAI-compatible tool specifications."""
    try:
        tools = get_openai_tool_specs()
        return {"tools": tools}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    """Call a specific individual tool directly with arguments.
    
    This endpoint allows calling a single tool by name with specific arguments.
    It provides direct, low-level access to individual tools.
    """
    try:
        import time
        start_time = time.time()
        
        result = await dispatch_tool_call(request.name, request.arguments)
        
        execution_time = time.time() - start_time
        return ToolCallResponse(result=result, execution_time=execution_time)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/process", response_model=MCPResponse)
async def process_mcp_request(request: MCPRequest):
    """Process a complete MCP request through the full server pipeline.
    
    This endpoint handles full MCP requests by:
    1. Assembling prompts via PromptAssembler
    2. Preparing resources via ResourceHandler 
    3. Invoking necessary tools via ToolInvoker
    
    It provides higher-level orchestration compared to direct tool calls.
    """
    try:
        return await mcp_server.handle_request(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    # For production
    # uvicorn server.main:app --reload  

if __name__ == "__main__":
    start()
