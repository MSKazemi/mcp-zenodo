# Zenodo MCP - FastAPI

A FastAPI-based service that provides a set of tools for interacting with Zenodo records, specifically designed for integration with LLM projects using the Model Context Protocol (MCP). This API enables seamless interaction with Zenodo's repository for data retrieval, citation management, and metadata analysis in LangChain and LangGraph applications.

## Features

- **MCP-Compatible Tools**: Pre-configured tools that follow the Model Context Protocol for easy integration with LLM frameworks
- **Zenodo Integration**:
  - Search and retrieve records
  - Get citations in various formats
  - Detect data types of records
  - Access detailed metadata
  - List and analyze files
- **LLM Framework Support**:
  - LangChain integration
  - LangGraph compatibility
  - Custom tool creation support

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/MSKazemi/zenodo-mcp.git
   cd zenodo-mcp
   ```

2. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. Configure your environment:
   - Create a `.env` file with your Zenodo API token
   - Set up any additional configuration options

## Installation

```bash
pip install -r requirements.txt
```

## Usage with LLM Projects

### LangChain Integration

```python
from langchain.agents import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_openai import ChatOpenAI

# Import Zenodo MCP tools
from zenodo_mcp.tools import (
    search_records,
    get_citation,
    detect_data_type,
    get_metadata,
    list_files
)

# Create tools
tools = [
    Tool(
        name="search_zenodo",
        func=search_records,
        description="Search for records in Zenodo"
    ),
    Tool(
        name="get_citation",
        func=get_citation,
        description="Get citation for a Zenodo record"
    ),
    # Add other tools as needed
]

# Create agent
llm = ChatOpenAI(temperature=0)
agent = create_react_agent(llm, tools)
agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools)
```

### LangGraph Integration

```python
from langgraph.graph import Graph
from zenodo_mcp.tools import search_records, get_metadata

# Define nodes
def search_node(state):
    query = state["query"]
    results = search_records(query=query)
    return {"results": results}

def analyze_node(state):
    record_id = state["selected_record"]
    metadata = get_metadata(record_id=record_id)
    return {"analysis": metadata}

# Create graph
workflow = Graph()
workflow.add_node("search", search_node)
workflow.add_node("analyze", analyze_node)
workflow.add_edge("search", "analyze")
```

## Available MCP Tools

1. **Search Records**
   - Search Zenodo repository
   - Filter by various criteria
   - Sort results by relevance or date

2. **Get Citation**
   - Retrieve citations in multiple formats (BibTeX, APA, etc.)
   - Customize citation style
   - Export citations for academic use

3. **Detect Data Type**
   - Automatically classify Zenodo records
   - Identify datasets, software, or articles
   - Provide confidence scores

4. **Get Metadata**
   - Access detailed record metadata
   - Include file information
   - Track version history

5. **List Files**
   - Browse record contents
   - Access file metadata
   - Download file information

## API Documentation

The API documentation is available at `http://localhost:8000/docs` when running the server.

## Environment Variables

Create a `.env` file with the following variables:
```
ZENODO_API_TOKEN=your_token_here
API_HOST=0.0.0.0
API_PORT=8000
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Zenodo API for data access
- FastAPI for the web framework
- LangChain and LangGraph communities 