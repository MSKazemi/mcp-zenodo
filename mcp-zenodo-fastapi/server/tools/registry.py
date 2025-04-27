"""
Tool registry and decorator for MCP Zenodo server.
"""

from typing import Dict, Any, Callable, Optional, List
from functools import wraps

# Global registry of tools
_TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}

def tool(name: str, description: str, parameters: Dict[str, Any]):
    """Decorator to register a tool function.
    
    Args:
        name: Name of the tool
        description: Description of what the tool does
        parameters: JSON Schema of tool parameters
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
            
        # Register the tool
        _TOOL_REGISTRY[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "function": wrapper
        }
        return wrapper
    return decorator

def get_tool_registry() -> Dict[str, Dict[str, Any]]:
    """Get the complete tool registry.
    
    Returns:
        Dictionary mapping tool names to their metadata
    """
    return _TOOL_REGISTRY

def get_tool(name: str) -> Optional[Dict[str, Any]]:
    """Get a specific tool by name.
    
    Args:
        name: Name of the tool to get
        
    Returns:
        Tool metadata dictionary if found, None otherwise
    """
    return _TOOL_REGISTRY.get(name)

def get_openai_tool_specs() -> List[Dict[str, Any]]:
    """Get tool specifications for OpenAI function-calling.
    
    Returns:
        List of tool specifications in OpenAI-compatible format
    """
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"]
        }
        for tool in get_tool_registry().values()
    ]

async def dispatch_tool_call(name: str, arguments: Dict[str, Any]) -> Any:
    """Execute a registered tool by name with given arguments.
    
    Args:
        name: Name of the tool to execute
        arguments: Arguments to pass to the tool
        
    Returns:
        Result of the tool execution
    """
    tool = get_tool(name)
    if tool:
        return await tool["function"](**arguments)
    raise ValueError(f"Tool {name} not found")