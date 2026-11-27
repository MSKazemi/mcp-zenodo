"""Tools and endpoints that previously failed (issues #1 and #4)."""

import tempfile
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

import httpx

from server import main
from server.tools import (
    compare_tool, data_type_tool, download_tool, embed_tool, keywords_tool, metadata_tool,
    related_records_tool, search_tool, summarize_tool,
)
from server.tools.registry import dispatch_tool_call, get_tool_registry
from server.zenodo_client import MCPZenodoClient
from zenodo_stub import TOOL_NAMES, record, start_stub


class ToolTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.queries = []
        self.rate_limited = []
        origin = await start_stub(
            self.addAsyncCleanup, self.queries, self.rate_limited
        )
        cache = tempfile.TemporaryDirectory()
        self.addCleanup(cache.cleanup)
        self.client = MCPZenodoClient(base_url=f"{origin}/api", cache_dir=cache.name)
        self.client.api_token = None
        self.addAsyncCleanup(self.client._close_session)
        for module in (compare_tool, data_type_tool, download_tool, embed_tool, keywords_tool,
                       metadata_tool, related_records_tool, summarize_tool):
            patcher = patch.object(module, "_client", self.client)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_every_documented_tool_is_registered(self):
        self.assertEqual(set(get_tool_registry()), TOOL_NAMES)

    async def test_compare_records_accepts_tool_arguments(self):
        result = await dispatch_tool_call(
            "compare_records",
            {"record_ids": ["1", "2"], "compare_fields": ["authors", "license"]},
        )
        self.assertEqual(
            result.field_comparisons["authors"]["similarity_scores"], {"1_2": 1.0}
        )
        # A field neither record has does not count towards the overall score
        self.assertIsNone(result.field_comparisons["license"]["average_similarity"])
        self.assertEqual(result.overall_similarity, 1.0)

    async def test_compare_records_needs_two_different_records(self):
        with self.assertRaises(ValueError):
            await dispatch_tool_call("compare_records", {"record_ids": ["1", "1"]})

    async def test_compare_records_rejects_a_string_of_ids(self):
        with self.assertRaises(ValueError):
            await dispatch_tool_call("compare_records", {"record_ids": "12"})
        self.assertEqual(self.queries, [])

    async def test_keywords_come_from_text_not_markup(self):
        result = await dispatch_tool_call("extract_keywords", {"record_id": "1"})
        words = [entry["keyword"] for entry in result["keywords"]]
        self.assertEqual(words[0], "salinity")
        self.assertNotIn("href", words)

    async def test_summary_has_no_markup(self):
        result = await dispatch_tool_call("summarize_record", {"record_id": "1"})
        self.assertIn("Ocean salinity data.", result.summary)
        self.assertNotIn("<p>", result.summary)

    async def test_embed_link_points_at_the_file_preview(self):
        result = await dispatch_tool_call("generate_embed_link", {"record_id": "1"})
        self.assertTrue(result.embed_url.endswith("/records/1/preview/data.csv"))
        self.assertEqual(result.record_type, "dataset")

    async def test_related_records_use_one_search_without_stray_syntax(self):
        await dispatch_tool_call("get_related_records", {"record_id": "1", "max_results": 40})
        self.assertEqual(len(self.queries), 1)
        sent = self.queries[0]
        self.assertEqual(
            sent["q"],
            '"ocean" OR "salinity" OR "doe jane" OR ocean OR depth OR salinity OR v1.0',
        )
        self.assertEqual((sent["size"], sent["sort"]), ("25", "bestmatch"))

    async def test_metadata_honours_include_flags(self):
        result = await dispatch_tool_call(
            "get_metadata",
            {"record_id": "1", "include_files": False, "include_versions": False},
        )
        self.assertNotIn("files", result.record)
        self.assertNotIn("relations", result.record["metadata"])

    async def test_download_with_wrong_checksum_is_discarded(self):
        bad = record(1)
        bad["files"][0]["checksum"] = "md5:" + "0" * 32
        bad["files"][0]["links"]["self"] = self.client.base_url.removesuffix("/api") + "/content"
        with patch.object(self.client, "get_metadata", return_value=bad):
            result = await dispatch_tool_call(
                "download_file", {"record_id": "1", "file_name": "data.csv"}
            )
        self.assertIn("Checksum mismatch", result.error)
        self.assertEqual(list(self.client.cache_dir.rglob("*.*")), [])

    async def test_search_returns_short_records_unless_asked_for_all(self):
        with patch.object(search_tool, "client", self.client):
            short = await dispatch_tool_call("search_records", {"query": "ocean"})
            full = await dispatch_tool_call(
                "search_records", {"query": "ocean", "full": True}
            )
        first = short["records"][0]
        self.assertEqual(short["returned_results"], 2)
        self.assertEqual(first["resource_type"], "dataset")
        self.assertEqual(first["file_count"], 1)
        self.assertEqual(first["description"], "Ocean salinity data. Salinity data.")
        self.assertNotIn("files", first)
        self.assertIn("files", full["records"][0])

    async def test_page_size_is_capped_only_without_a_token(self):
        await self.client.search_records("ocean", max_results=100)
        self.client.api_token = "token"
        await self.client.search_records("ocean", max_results=100)
        self.assertEqual([q["size"] for q in self.queries], ["25", "100"])

    async def test_data_type_is_the_stated_resource_type(self):
        for stated, expected in (("software", "software"), ("publication", "article"),
                                 ("poster", "poster")):
            payload = record(1)
            payload["metadata"]["resource_type"] = {"type": stated}
            with self.subTest(stated=stated), patch.object(
                self.client, "get_metadata", return_value=payload
            ):
                result = await dispatch_tool_call("detect_data_type", {"record_id": "1"})
            self.assertEqual((result["data_type"], result["confidence"]), (expected, 1.0))
            self.assertEqual(result["metadata"]["file_types"], ["csv"])

    async def test_bad_arguments_are_a_client_error(self):
        for arguments in ({}, {"record_id": "1", "bogus": 1}):
            with self.subTest(arguments=arguments):
                response = await self.post_call("get_metadata", arguments)
                self.assertEqual(response.status_code, 400, response.text)
        self.assertEqual(self.queries, [])

    async def test_rate_limit_is_passed_on(self):
        self.rate_limited.append(True)
        with patch.object(search_tool, "client", self.client):
            for response in (
                await self.post_call("search_records", {"query": "x"}),
                await self.post_call("get_metadata", {"record_id": "1"}),
                await self.post_process({"query": "x"}),
            ):
                self.assertEqual(response.status_code, 429, response.text)
                self.assertEqual(response.headers["Retry-After"], "7")

    async def post_call(self, name, arguments):
        return await self.post("/mcp/tools/call", {"name": name, "arguments": arguments})

    async def post(self, path, body):
        with patch.object(main.config, "api_key", None):
            transport = httpx.ASGITransport(app=main.app, client=("127.0.0.1", 5000))
            async with httpx.AsyncClient(
                transport=transport, base_url="http://127.0.0.1:8000"
            ) as http:
                return await http.post(path, json=body)

    async def post_process(self, body):
        with patch.object(main.mcp_server.tool_invoker, "client", self.client):
            return await self.post("/mcp/process", body)

    async def test_process_endpoint_returns_records(self):
        with patch.object(main.config, "api_key", None):
            response = await self.post_process(
                {"query": "ocean", "max_results": 2, "filters": {"type": "dataset"}}
            )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual([r["id"] for r in response.json()["records"]], [1, 2])
        self.assertEqual(response.json()["records"][0]["files"][0]["filename"], "data.csv")
        self.assertEqual(self.queries[0]["type"], "dataset")

    async def test_process_endpoint_rejects_bad_filters(self):
        for filters in ({"q": "y"}, {"type": ["dataset"]}):
            with self.subTest(filters=filters), patch.object(main.config, "api_key", None):
                response = await self.post_process({"query": "x", "filters": filters})
                self.assertEqual(response.status_code, 400)
        self.assertEqual(self.queries, [])
