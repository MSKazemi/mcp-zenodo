# MCP Zenodo Server

## Overview

**Model Context Protocol (MCP)** is an open standard developed by Anthropic to enable seamless integration between large language models (LLMs) and external tools, systems, and data sources. MCP standardizes how context is exchanged, allowing AI assistants and applications like [Cursor IDE](https://cursor.sh/) to interact efficiently with files, APIs, databases, and other resources.

This repository provides an **MCP server implementation for [Zenodo](https://zenodo.org/)**, a trusted open-access repository developed by CERN for sharing research outputs.

With this Zenodo MCP server, you can search, retrieve metadata, and download datasets from Zenodo, directly inside MCP-enabled environments such as Cursor IDE.

> **Important:** This project implements an MCP **server** for Zenodo. It does not implement or modify the MCP standard itself.

## Features

- ✨ **Unified API**: Access Zenodo through a standardized API.
- 🔧 **Extensible Architecture**: Add support for more services by creating additional MCP servers.
- 🔒 **Simple Configuration**: Manage services easily with a JSON config file.
- 📖 **Zenodo Data Access**: Search, browse, and download research artifacts.
- 🌈 **Cursor IDE Integration**: Connect seamlessly to Cursor's MCP extension.

## What is Zenodo?

[Zenodo](https://zenodo.org/) is a free, open-access research data repository developed by CERN under the European OpenAIRE program. Researchers use Zenodo to share datasets, publications, software, and other research outputs, complete with Digital Object Identifiers (DOIs) for citation and long-term preservation.

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/mcp-zenodo.git
cd mcp-zenodo/mcp_sdk_core
```

### 2. Install Dependencies

Ensure you have **Python 3.8+** installed. Then install the required packages:

```bash
pip install -r requirements.txt
```

Alternatively, if you use `uvicorn` manually:

```bash
pip install uvicorn
```

### 3. Add MCP Server Configuration to Cursor IDE (`mcp.json`)

To connect the Zenodo MCP server to Cursor IDE, create a `mcp.json` file that specifies how to start the server:

```json
{
  "mcpServers": {
    "Zenodo": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-zenodo/mcp_sdk_core/server",
        "run",
        "server.py"
      ]
    }
  }
}
```

- **command**: The executable to run (e.g., `uv` or `python`).
- **args**: Arguments for launching the MCP server.

**Note:** Adjust the `--directory` and script paths based on your local setup.

### 4. Run with Cursor MCP

1. Open Cursor IDE.
2. Make sure the MCP extension is installed and enabled.
3. Place the `mcp.json` file in your project root or in `~/.cursor/`.
4. Cursor will automatically detect and start the Zenodo MCP server.

### 5. Using the Zenodo MCP Server

- Open the MCP sidebar or command palette in Cursor.
- Search for Zenodo records.
- Retrieve metadata and download files directly.
- Use Zenodo as a contextual resource within your development environment.

## Directory Structure

```
mcp_sdk_core/
├── client/           # Core client utilities
│   ├── client.py
│   └── ...
├── server/           # MCP server implementation
│   ├── server.py
│   ├── zenodo_client.py
│   └── models/       # Request/response models
├── README.md
└── requirements.txt  # Project dependencies
```

## Extending MCP

To add more services beyond Zenodo:

1. Create a new MCP server under the `server/` directory.
2. Define necessary request/response models.
3. Update the `mcp.json` configuration with the new server details.

Example: Adding an "Arxiv" MCP server or a "Kaggle" MCP server.

## Troubleshooting

- 🔗 **Incorrect Paths**: Verify paths in `mcp.json`.
- ⚡ **Missing Packages**: Install dependencies listed in `requirements.txt`.
- 📊 **Debugging**: Run the server manually using `uv run server.py` to inspect issues.

## License

This project is licensed under the [MIT License](LICENSE).

---

> Developed to extend MCP functionality by connecting Zenodo as a powerful open research data source inside development environments like Cursor.

---

## References

- [Zenodo Official Website](https://zenodo.org/)
- [Model Context Protocol Overview](https://www.anthropic.com/)
- [Cursor IDE](https://cursor.sh/)
- [Uvicorn Documentation](https://www.uvicorn.org/)

