"""download_file tests against a local stand-in for the Zenodo API."""

import asyncio
import tempfile
from pathlib import Path
from unittest import IsolatedAsyncioTestCase

from aiohttp import web

from server.zenodo_client import MCPZenodoClient

BODY = b"a,b\n1,2\n"
SLASH_KEY = "owner/repo-v1.0.zip"


class DownloadTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.requests = []
        self.other_origin = await self._serve()
        self.origin = await self._serve()
        cache = tempfile.TemporaryDirectory()
        self.addCleanup(cache.cleanup)
        self.cache = Path(cache.name)
        self.client = MCPZenodoClient(
            api_token="secret", base_url=f"{self.origin}/api", cache_dir=cache.name
        )
        self.addAsyncCleanup(self.client._close_session)

    async def _serve(self) -> str:
        app = web.Application()
        app.router.add_get("/{path:.*}", self._handle)
        runner = web.AppRunner(app)
        await runner.setup()
        self.addAsyncCleanup(runner.cleanup)
        await web.TCPSite(runner, "127.0.0.1", 0).start()
        return f"http://127.0.0.1:{runner.addresses[0][1]}"

    async def _handle(self, request):
        self.requests.append((request.path, request.headers.get("Authorization")))
        if request.path != "/api/records/1":
            return web.Response(body=BODY)

        def entry(key, origin=self.origin, size=len(BODY)):
            return {"key": key, "size": size, "links": {"self": f"{origin}/content"}}

        return web.json_response({"files": [
            entry("data.csv"),
            entry(SLASH_KEY),
            entry("repo-v1.0.zip"),
            entry("elsewhere.csv", origin=self.other_origin),
            entry("short.csv", size=999),
        ]})

    async def test_download_then_cache_then_force(self):
        first = await self.client.download_file("1", "data.csv")
        self.assertIsNone(first.error)
        self.assertEqual(Path(first.file_path).read_bytes(), BODY)
        seen = len(self.requests)
        await self.client.download_file("1", "data.csv")
        self.assertEqual(len(self.requests), seen)
        await self.client.download_file("1", "data.csv", force_download=True)
        self.assertGreater(len(self.requests), seen)

    async def test_keys_with_slashes_get_their_own_cache_file(self):
        nested = await self.client.download_file("1", SLASH_KEY)
        flat = await self.client.download_file("1", "repo-v1.0.zip")
        self.assertIsNone(nested.error)
        self.assertNotEqual(nested.file_path, flat.file_path)
        self.assertEqual(Path(nested.file_path).parent, self.cache / "1")

    async def test_bad_input_reports_an_error_and_writes_nothing(self):
        for record_id, name in [("999/1", "data.csv"), ("..", "data.csv"),
                                ("1", ".."), ("1", "../../data.csv"), ("1", "missing")]:
            with self.subTest(record_id=record_id, name=name):
                result = await self.client.download_file(record_id, name)
                self.assertIsNotNone(result.error)
                self.assertIsNone(result.file_path)
        self.assertEqual([p for p in self.cache.rglob("*") if p.is_file()], [])

    async def test_size_mismatch_leaves_no_partial_file(self):
        result = await self.client.download_file("1", "short.csv")
        self.assertIn("expected 999", result.error)
        self.assertEqual(list((self.cache / "1").iterdir()), [])

    async def test_token_is_not_sent_to_another_origin(self):
        await self.client.download_file("1", "data.csv")
        self.assertEqual(self.requests[-1], ("/content", "Bearer secret"))
        await self.client.download_file("1", "elsewhere.csv")
        self.assertEqual(self.requests[-1], ("/content", None))

    async def test_concurrent_downloads_of_one_file(self):
        results = await asyncio.gather(
            *[self.client.download_file("1", "data.csv", True) for _ in range(10)]
        )
        self.assertEqual([r.error for r in results if r.error], [])
        self.assertEqual([p.name for p in (self.cache / "1").iterdir()], ["data.csv"])
