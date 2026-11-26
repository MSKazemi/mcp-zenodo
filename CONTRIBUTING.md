# Contributing to mcp-zenodo

Thank you for being here. Bug reports, documentation fixes, tests and code are all welcome,
and small pull requests are as useful as large ones.

## Find something to work on

- [Good first issues](https://github.com/MSKazemi/mcp-zenodo/labels/good%20first%20issue):
  small, with pointers to the code.
- [Help wanted](https://github.com/MSKazemi/mcp-zenodo/labels/help%20wanted): larger
  improvements.

Comment on an issue before you start, so two people don't do the same work. An issue that has
an assignee or an open pull request is taken. For a new idea, open an issue first.

## Set up

You need Python 3.12 or newer and [uv](https://docs.astral.sh/uv/). Fork the repository, then:

```bash
git clone https://github.com/<your-username>/mcp-zenodo.git
cd mcp-zenodo
make setup
make test
```

The tests use a local stand-in for Zenodo, so they need no token and no network access.
Without `make`, run `uv sync`, then `uv run python -m unittest discover -s tests` from
`mcp_api/`.

## Try your change

```bash
make serve
```

In another terminal:

```bash
curl -H "Content-Type: application/json" \
  -d '{"name": "search_records", "arguments": {"query": "climate", "max_results": 2}}' \
  http://127.0.0.1:8000/mcp/tools/call
```

This calls the real Zenodo API, which allows 30 requests a minute without a token. Interactive
API documentation is at <http://127.0.0.1:8000/docs>. To use your checkout from an MCP client
such as Cursor, follow the [stdio server guide](mcp_sdk_core/README.md).

## Where things are

| Path | Contents |
|------|----------|
| `mcp_api/server/tools/` | One module per tool |
| `mcp_api/server/zenodo_client.py` | The only code that talks to Zenodo |
| `mcp_api/server/main.py`, `access.py` | HTTP endpoints and who may call them |
| `mcp_sdk_core/server/server.py` | Exposes the same tools over stdio |
| `mcp_api/tests/` | Tests and the Zenodo stand-in (`zenodo_stub.py`) |

## Add a tool

1. Create `mcp_api/server/tools/doi_tool.py`:

   ```python
   """Tool that returns a record's DOI."""

   from typing import Any, Dict

   from server.zenodo_client import MCPZenodoClient
   from .registry import tool

   _client = None


   def _get_client() -> MCPZenodoClient:
       global _client
       if _client is None:
           _client = MCPZenodoClient()
       return _client


   @tool(
       name="get_doi",
       description="Returns the DOI of a Zenodo record",
       parameters={
           "type": "object",
           "properties": {
               "record_id": {"type": "string", "description": "The ID of the Zenodo record"}
           },
           "required": ["record_id"],
       },
   )
   async def get_doi(record_id: str) -> Dict[str, Any]:
       record = await _get_client().get_metadata(record_id)
       return {"record_id": record_id, "doi": record.get("doi", "")}
   ```

2. Import it in `mcp_api/server/tools/__init__.py`: `from .doi_tool import get_doi`.
3. Add `"get_doi"` to `TOOL_NAMES` in `mcp_api/tests/zenodo_stub.py`. If it needs more than a
   `record_id`, add example arguments to `ARGUMENTS` in `test_stdio_server.py`.
4. Write a test for what it returns, and add it to the tool tables in `README.md` and
   `mcp_api/README.md`.

Both servers pick the tool up from the registry. Every parameter needs a description, and the
function's parameter names must match the schema.

## Open a pull request

- Work on a branch, and keep one topic per pull request.
- Add a test that fails without your change.
- Start the title with `feat:`, `fix:`, `docs:`, `test:`, `ci:` or `chore:`.
- Never commit tokens or `.env` files.
- GitHub may hold the checks on your first pull request until a maintainer approves the run.
- If you leave "Allow edits by maintainers" on, a maintainer can finish small fixes on your
  branch. You keep the credit.

A draft pull request is a good way to ask for help before the work is finished.

## Credit

Everyone whose code or reports are merged is listed in [CONTRIBUTORS.md](CONTRIBUTORS.md).

## Security problems

Please don't describe them in a public issue or pull request. See [SECURITY.md](SECURITY.md).
