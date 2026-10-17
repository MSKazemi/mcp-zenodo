# mcp-zenodo — Zenodo MCP Server

**mcp-zenodo is a Zenodo MCP server: it connects large language models to [Zenodo](https://zenodo.org/), the CERN-hosted open-access research repository, through the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/).** It lets an LLM search Zenodo records, read metadata, retrieve citations, and list or download files as callable tools. It is built for developers and researchers who want AI assistants to work with open research datasets, software, and publications. Use it when you want tools like Claude Desktop, Cursor IDE, or a LangChain/LangGraph agent to ground answers in real Zenodo records with DOIs. Do not use it if you need to *deposit* or *publish* to Zenodo, since this project is read/retrieval oriented and does not implement upload workflows. Compared with calling the Zenodo REST API directly, mcp-zenodo packages that access as MCP tools so any MCP-compatible client can use Zenodo without writing custom integration code.

> One-line value prop: **an MCP server for Zenodo that turns open-access research data into LLM-callable tools.**

Written in Python. Licensed under Apache-2.0.

---

## What it does

mcp-zenodo exposes Zenodo's repository of research outputs to LLMs through MCP tools:

- **Search and retrieve records** — find Zenodo records by query.
- **Get citations** — retrieve citations in formats such as BibTeX and APA.
- **Detect data types** — classify a record as dataset, software, or article.
- **Access metadata** — get detailed metadata for a record.
- **List and download files** — browse and download files attached to records.

### Available tools

| Tool | Description |
|------|-------------|
| `search_records` | Search for records in Zenodo |
| `get_metadata` | Retrieve detailed metadata of a Zenodo record |
| `get_citation` | Return a BibTeX or APA citation of a Zenodo record |
| `detect_data_type` | Determine if a record is a dataset, software, or article |
| `compare_records` | Compare metadata of multiple Zenodo records |
| `list_files` | List available files in a Zenodo record |
| `download_file` | Download a specific file from a record |
| `generate_embed_link` | Create a direct embeddable link for a record (PDF, dataset) |
| `extract_keywords` | Extract top keywords from a record's abstract or text |
| `get_related_records` | Find records related to a given Zenodo record |
| `summarize_record` | Generate a summary from a record's metadata |

---

## Repository structure

This repository contains two implementations for two different use cases:

1. **MCP SDK Core** (`/mcp_sdk_core`) — a Python MCP server for integration with MCP-enabled environments such as Cursor IDE and Claude Desktop.
2. **MCP API** (`/mcp_api`) — a FastAPI service that exposes MCP-compatible tools for LLM frameworks such as LangChain and LangGraph, and OpenAI-compatible clients.

### MCP SDK Core

The MCP SDK Core implementation is designed for direct integration with MCP-enabled environments. It provides:

- **Direct MCP integration** — follows the Model Context Protocol standard.
- **Cursor IDE / Claude Desktop compatibility** — connects through the standard MCP client config.
- **Simple configuration** — managed through a JSON config file.
- **Unified API** — standardized access to Zenodo resources.

This is ideal for developers who want to access Zenodo directly from their development environment without additional middleware.

[Learn more about the MCP SDK Core implementation →](mcp_sdk_core/README.md)

### MCP API

The MCP API implementation is a FastAPI service that provides MCP-compatible tools for LLM frameworks. It offers:

- **LangChain integration** — use the tools with LangChain agents.
- **LangGraph compatibility** — use the tools in LangGraph workflows.
- **OpenAI-compatible API** — usable with OpenAI-compatible clients.
- **LibreChat support** — compatible with LibreChat and similar platforms.
- **Custom tool creation** — extensible architecture for adding tools.

This is ideal for developers building LLM applications that interact with Zenodo as part of a larger workflow.

[Learn more about the MCP API implementation →](mcp_api/README.md)

---

## 30-second quickstart

### Option A — MCP server for Cursor IDE / Claude Desktop

```bash
# Clone the repository
git clone https://github.com/MSKazemi/mcp-zenodo.git
cd mcp-zenodo/mcp_sdk_core

# Install dependencies
pip install -r requirements.txt
```

Then register the server with your MCP client. For Cursor IDE, create an `mcp.json` (in your project root or `~/.cursor/`); for Claude Desktop, add the same block to `claude_desktop_config.json`:

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

Adjust the `--directory` path to your local checkout. Restart the client; it will detect and start the Zenodo MCP server. You can then ask the assistant to search Zenodo, fetch metadata, or retrieve a citation.

### Option B — FastAPI service for LangChain / LangGraph / OpenAI-compatible clients

```bash
# Clone the repository
git clone https://github.com/MSKazemi/mcp-zenodo.git
cd mcp-zenodo/mcp_api

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Zenodo API token

# Run the API server
uvicorn server.main:app --host 0.0.0.0 --port 8000
```

---

## Example

Ask an MCP-enabled assistant (Claude Desktop, Cursor) a question that triggers the `search_records` tool:

> "Search Zenodo for records about climate model output and show me the top result with its DOI."

The assistant calls the `search_records` tool, then `get_metadata`, and returns a record's title, authors, DOI, and description. A representative (abbreviated) tool result looks like:

```json
{
  "hits": [
    {
      "title": "Example Climate Model Output Dataset",
      "doi": "10.5281/zenodo.1234567",
      "type": "dataset",
      "url": "https://zenodo.org/record/1234567"
    }
  ]
}
```

You can then follow up with `get_citation` to obtain a BibTeX or APA citation, or `list_files` / `download_file` to access the record's files. (Exact fields and values depend on the live Zenodo record returned.)

---

## Use cases

- **Literature and dataset discovery** — let an AI assistant search Zenodo and surface relevant datasets, software, and papers with DOIs.
- **Citation retrieval** — pull BibTeX or APA citations for records directly into a manuscript or notebook.
- **Research agents** — give LangChain/LangGraph agents a Zenodo tool so they can ground answers in open research data.
- **In-editor research** — query Zenodo from Cursor IDE or Claude Desktop while writing code or documentation.
- **Reproducibility workflows** — locate, inspect metadata for, and download research artifacts programmatically.

---

## Comparison and alternatives

- **vs. calling the Zenodo REST API directly** — the [Zenodo REST API](https://developers.zenodo.org/) gives full control (including deposition/upload), but you must write and maintain the integration yourself. mcp-zenodo wraps common read/retrieval operations as MCP tools so any MCP client can use them with no custom code.
- **vs. general-purpose HTTP/fetch MCP servers** — a generic fetch tool can hit Zenodo URLs but has no knowledge of records, metadata, citations, or file listings. mcp-zenodo provides Zenodo-specific, typed tools.
- **vs. other research-repository MCP servers** — comparable MCP servers exist for sources such as arXiv and other data repositories; mcp-zenodo is focused specifically on Zenodo. It ships two integration paths (a stdio MCP server and a FastAPI service), which lets you choose between direct MCP clients and LLM-framework/OpenAI-compatible usage.

---

## Limitations / when NOT to use

- **Not for depositing or publishing** — this project focuses on searching and retrieving from Zenodo; it does not implement Zenodo deposition/upload workflows.
- **Depends on the Zenodo API** — availability, rate limits, and returned fields are governed by Zenodo; some operations may require a Zenodo API token.
- **Retrieval quality depends on Zenodo metadata** — data-type detection, keyword extraction, and summaries are derived from record metadata and are best-effort.
- **Two separate implementations** — the MCP SDK Core server and the FastAPI service are configured differently; pick the one matching your client rather than expecting a single unified deployment.

---

## FAQ

**What is mcp-zenodo?**
mcp-zenodo is a Zenodo MCP server — an implementation of the Model Context Protocol that exposes Zenodo (the CERN open-access research repository) to large language models as callable tools for searching records, reading metadata, retrieving citations, and listing or downloading files.

**How do I use Zenodo with Claude or ChatGPT via MCP?**
For Claude Desktop or Cursor IDE, install the `mcp_sdk_core` server and add it to your MCP client config (`claude_desktop_config.json` or `mcp.json`) as shown in the quickstart. For OpenAI-compatible / ChatGPT-style workflows, run the `mcp_api` FastAPI service and call its MCP-compatible tools from your framework (e.g., LangChain, LangGraph) or OpenAI-compatible client.

**Which MCP clients are supported?**
Any MCP-compatible client can use the `mcp_sdk_core` server over the standard MCP transport; it is tested with Cursor IDE and works with Claude Desktop. The `mcp_api` service targets LLM frameworks such as LangChain and LangGraph, OpenAI-compatible clients, and platforms such as LibreChat.

**Do I need a Zenodo API token?**
The FastAPI service reads a Zenodo API token from `.env` (see `.env.example`). Some Zenodo operations work without a token, but a token is recommended for reliable access.

**Is mcp-zenodo on PyPI?**
Not at this time — install it by cloning the repository as shown in the quickstart.

---

## Contributing

Contributions to both implementations are welcome. Please see the implementation READMEs ([mcp_sdk_core](mcp_sdk_core/README.md), [mcp_api](mcp_api/README.md)) for details.

---

## License

This project is licensed under the Apache License 2.0 — see the [LICENSE](LICENSE) file for details.

---

## Citation

If you use mcp-zenodo in your work, please cite it. Citation metadata is provided in [`CITATION.cff`](CITATION.cff). Example:

> Seyedkazemi Ardebili, M. *mcp-zenodo: A Zenodo MCP server.* https://github.com/MSKazemi/mcp-zenodo

<!-- legal-notice: start -->
### Legal notice and responsible use

The materials in this repository are made available without warranties to the extent permitted by applicable law. **Please read the [Disclaimer and Responsible-Use Notice](DISCLAIMER.md)** before relying on or deploying them. This notice does not change any existing software license or limit rights that cannot legally be waived.
<!-- legal-notice: end -->
