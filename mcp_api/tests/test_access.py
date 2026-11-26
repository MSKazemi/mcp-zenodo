"""Who may call the HTTP service."""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

import httpx

from server import main
from server.config import config

LOCAL = "http://127.0.0.1:8000"
CALL = {"name": "download_file", "arguments": {"record_id": "1", "file_name": "a"}}


class AccessTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.dispatch = AsyncMock(return_value={})
        for patcher in (
            patch.object(main, "dispatch_tool_call", self.dispatch),
            patch.object(config, "api_key", None),
            patch.object(config, "cors_origins", []),
        ):
            patcher.start()
            self.addCleanup(patcher.stop)

    async def call(self, client_ip="127.0.0.1", base_url=LOCAL, headers=None):
        transport = httpx.ASGITransport(app=main.app, client=(client_ip, 5000))
        async with httpx.AsyncClient(transport=transport, base_url=base_url) as http:
            response = await http.post("/mcp/tools/call", json=CALL, headers=headers)
        return response.status_code

    async def assert_refused(self, status, **kwargs):
        self.assertEqual(await self.call(**kwargs), status)
        self.dispatch.assert_not_awaited()

    async def test_local_calls_work_without_a_key(self):
        self.assertEqual(await self.call(), 200)
        self.assertEqual(await self.call("::1", "http://[::1]:8000"), 200)
        self.assertEqual(await self.call(base_url="http://localhost:8000"), 200)

    async def test_other_machines_are_refused_without_a_key(self):
        await self.assert_refused(403, client_ip="192.168.1.20")

    async def test_foreign_host_name_is_refused_without_a_key(self):
        await self.assert_refused(403, base_url="http://rebound.example:8000")

    async def test_cross_site_browser_requests_are_refused(self):
        await self.assert_refused(403, headers={"Origin": "https://evil.example"})

    async def test_same_origin_and_listed_origins_pass(self):
        self.assertEqual(await self.call(headers={"Origin": LOCAL}), 200)
        config.cors_origins.append("https://app.example")
        self.assertEqual(await self.call(headers={"Origin": "https://app.example"}), 200)

    async def test_wildcard_origin_needs_a_key(self):
        config.cors_origins.append("*")
        await self.assert_refused(403, headers={"Origin": "https://evil.example"})

    async def test_key_is_required_once_set(self):
        config.api_key = "s3cret"
        await self.assert_refused(401)
        await self.assert_refused(401, headers={"Authorization": "Bearer wrong"})
        await self.assert_refused(401, headers={"Authorization": "s3cret"})

    async def test_openapi_documents_optional_bearer_authentication(self):
        schema = main.app.openapi()
        self.assertIn("HTTPBearer", schema["components"]["securitySchemes"])
        self.assertIn(
            {"HTTPBearer": []},
            schema["paths"]["/mcp/tools/call"]["post"]["security"],
        )

    async def test_key_admits_other_machines(self):
        config.api_key = "s3cret"
        status = await self.call(
            "192.168.1.20",
            "http://zenodo.lan:8000",
            {"Authorization": "Bearer s3cret"},
        )
        self.assertEqual(status, 200)

    async def test_every_api_route_is_covered(self):
        transport = httpx.ASGITransport(app=main.app, client=("192.168.1.20", 5000))
        async with httpx.AsyncClient(transport=transport, base_url=LOCAL) as http:
            for path in ("/", "/mcp/tools/openai-schema"):
                self.assertEqual((await http.get(path)).status_code, 403, path)
            response = await http.post("/mcp/process", json={"query": "x"})
            self.assertEqual(response.status_code, 403)
