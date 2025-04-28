# Zenodo MCP

A comprehensive toolkit for interacting with Zenodo records through the Model Context Protocol (MCP), providing two distinct implementations for different use cases.

## Repository Structure

This repository contains two main implementations:

1. **MCP SDK Core** (`/mcp_sdk_core`): A Python-based MCP server implementation designed for integration with Cursor IDE and other MCP-enabled environments.
2. **MCP API** (`/mcp_api`): A FastAPI-based service that provides MCP-compatible tools for integration with LLM frameworks like LangChain and LangGraph.

## Implementation Differences

### MCP SDK Core

The MCP SDK Core implementation is designed for direct integration with MCP-enabled environments like Cursor IDE. It provides:

- **Direct MCP Integration**: Follows the Model Context Protocol standard developed by Anthropic
- **Cursor IDE Compatibility**: Seamlessly integrates with Cursor's MCP extension
- **Simple Configuration**: Managed through a JSON config file
- **Unified API**: Standardized access to Zenodo resources

This implementation is ideal for developers who want to access Zenodo directly from their development environment without additional middleware.

[Learn more about the MCP SDK Core implementation →](mcp_sdk_core/README.md)

### MCP API

The MCP API implementation is a FastAPI-based service that provides MCP-compatible tools for integration with LLM frameworks. It offers:

- **LangChain Integration**: Seamless integration with LangChain agents and tools
- **LangGraph Compatibility**: Support for LangGraph workflows and graphs
- **OpenAI-Compatible API**: Can be used with OpenAI-compatible clients
- **LibreChat Support**: Compatible with LibreChat and similar platforms
- **Custom Tool Creation**: Extensible architecture for creating custom tools

This implementation is ideal for developers building LLM applications that need to interact with Zenodo as part of a larger workflow.

[Learn more about the MCP API implementation →](mcp_api/README.md)

## Features

Both implementations provide access to Zenodo's rich repository of research outputs:

- **Search and Retrieve Records**: Find and access Zenodo records
- **Get Citations**: Retrieve citations in various formats (BibTeX, APA, etc.)
- **Detect Data Types**: Automatically classify Zenodo records
- **Access Metadata**: Get detailed information about records
- **List and Download Files**: Browse and download files from records

## Getting Started

Choose the implementation that best fits your needs:

### For Cursor IDE Integration

```bash
# Clone the repository
git clone https://github.com/yourusername/zenodo-mcp.git
cd zenodo-mcp/mcp_sdk_core

# Install dependencies
pip install -r requirements.txt

# Configure Cursor IDE (create mcp.json)
# See mcp_sdk_core/README.md for details
```

### For LLM Framework Integration

```bash
# Clone the repository
git clone https://github.com/yourusername/zenodo-mcp.git
cd zenodo-mcp/mcp_api

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Zenodo API token

# Run the API server
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

## Contributing

We welcome contributions to both implementations! Please see the respective README files for contribution guidelines.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
