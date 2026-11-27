"""A local stand-in for the parts of the Zenodo records API the tools use."""

import hashlib

from aiohttp import web

# Every tool both servers must offer; add new tools here
TOOL_NAMES = {
    "search_records", "get_metadata", "get_citation", "detect_data_type",
    "compare_records", "list_files", "download_file", "generate_embed_link",
    "extract_keywords", "get_related_records", "summarize_record",
}

BODY = b"a,b\n1,2\n"
CHECKSUM = "md5:" + hashlib.md5(BODY).hexdigest()


def record(record_id: int, origin: str = "https://zenodo.org") -> dict:
    return {
        "id": record_id,
        "metadata": {
            "title": "Ocean data: depth/salinity (v1.0)",
            "description": "<p>Ocean <a href='x'>salinity</a> data. Salinity data.</p>",
            "creators": [{"name": "Doe, Jane"}],
            "keywords": ["ocean", "salinity"],
            "publication_date": "2026-01-02",
            "doi": f"10.5281/zenodo.{record_id}",
            "resource_type": {"type": "dataset", "title": "Dataset"},
            "relations": {"version": [{"index": 0, "is_last": True}]},
        },
        "files": [{
            "key": "data.csv",
            "size": len(BODY),
            "checksum": CHECKSUM,
            "links": {"self": f"{origin}/content"},
        }],
    }


async def start_stub(add_cleanup, queries=None, rate_limited=None) -> str:
    """Serve the stand-in on a free local port and return its origin.

    While ``rate_limited`` is a non-empty list, every request is answered 429.
    """
    origin = ""

    async def handle(request):
        if rate_limited:
            return web.json_response(
                {"status": 429}, status=429, headers={"Retry-After": "7"}
            )
        if request.path == "/content":
            return web.Response(body=BODY)
        if request.path == "/api/records":
            if queries is not None:
                queries.append(dict(request.query))
            hits = [record(1, origin), record(2, origin)]
            return web.json_response({"hits": {"hits": hits, "total": 2}})
        record_id = request.path.rsplit("/", 1)[1]
        return web.json_response(record(int(record_id), origin))

    app = web.Application()
    app.router.add_get("/{path:.*}", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    add_cleanup(runner.cleanup)
    await web.TCPSite(runner, "127.0.0.1", 0).start()
    origin = f"http://127.0.0.1:{runner.addresses[0][1]}"
    return origin
