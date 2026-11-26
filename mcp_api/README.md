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

Requires Python 3.12 or newer.

```bash
git clone https://github.com/MSKazemi/mcp-zenodo.git
cd mcp-zenodo/mcp_api
pip install -r requirements.txt
cp .env.example .env   # then add your Zenodo API token, if you have one
python -m server.main
```

`./setup.sh` does the first three steps in a virtual environment. The server listens on
`HOST` and `PORT` (default `127.0.0.1:8000`).

## Access control

The service acts with your Zenodo token and saves downloads to disk, so it is closed to
other machines unless you give it a key:

- **No `MCP_API_KEY`** (default): only requests from the same machine, addressed to
  `localhost`, `127.0.0.1` or `[::1]`, are accepted.
- **With `MCP_API_KEY`**: every request must send `Authorization: Bearer <key>`. This is
  required for access from another machine, a container's published port or a reverse proxy.
  The service speaks plain HTTP, so put TLS in front of it on any untrusted network.

Web pages on other origins are refused unless the origin is listed in `CORS_ORIGINS`.
Do not run a keyless server behind a proxy that rewrites the `Host` header to `localhost`:
its requests would look local.

## Calling the API

```python
import requests

BASE = "http://127.0.0.1:8000"
HEADERS = {}  # {"Authorization": "Bearer <MCP_API_KEY>"} when a key is set

# Tool names, descriptions and JSON Schemas, for your LLM framework
tools = requests.get(f"{BASE}/mcp/tools/openai-schema", headers=HEADERS).json()["tools"]

# Run one tool
response = requests.post(
    f"{BASE}/mcp/tools/call",
    headers=HEADERS,
    json={"name": "search_records", "arguments": {"query": "climate", "max_results": 3}},
)
response.raise_for_status()
print(response.json()["result"])
```

`POST /mcp/process` runs a search and returns typed records. It takes `query`, `max_results`
and optional `filters` (`all_versions`, `bounds`, `communities`, `page`, `status`,
`subtype`, `type`). Without a token, Zenodo serves at most 25 results per page.

## Available MCP Tools

| Tool | What it returns |
|------|-----------------|
| `search_records` | Records matching a query |
| `get_metadata` | A record's metadata |
| `get_citation` | A BibTeX or APA citation |
| `detect_data_type` | A best-effort guess: dataset, software or article |
| `summarize_record` | A plain-text summary built from the metadata |
| `extract_keywords` | Frequent terms from the title, description and keywords |
| `list_files` | A record's files with sizes, checksums and links |
| `download_file` | A file saved on the server |
| `compare_records` | Field-by-field similarity of two to ten records |
| `get_related_records` | Similar records found by searching |
| `generate_embed_link` | A file preview link, or the record page (Zenodo blocks framing from other sites) |

## Downloading Files

`download_file` takes a numeric `record_id` and a `file_name` exactly as `list_files` reports it.
Files are saved on the machine running the server, under `~/.zenodo_cache/<record_id>/`
(a `/` in a file name is stored as `%2F`). A cached file is returned without a new download
unless `force_download` is true. Size and MD5 checksum are verified before a file is kept.
Failures are reported in the response's `error` field.
The cache is not pruned automatically.

## API Documentation

The API documentation is available at `http://localhost:8000/docs` when running the server.

## Environment Variables

Set these in the environment, in `mcp_api/.env` or in a `.env` at the repository root
(see `.env.example`). The environment wins, then `mcp_api/.env`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `ZENODO_API_TOKEN` | none | Zenodo access token |
| `ZENODO_API_URL` | `https://zenodo.org/api` | API base URL |
| `ZENODO_SANDBOX` | `false` | Use sandbox.zenodo.org |
| `HOST` | `127.0.0.1` | Listen address for `python -m server.main` |
| `PORT` | `8000` | Listen port for `python -m server.main` |
| `MCP_API_KEY` | none | Key required from callers (see Access control) |
| `CORS_ORIGINS` | none | Browser origins allowed to call the service |

## Tests

```bash
python -m unittest discover -s tests   # from mcp_api/, with the project dependencies and `mcp<2`
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