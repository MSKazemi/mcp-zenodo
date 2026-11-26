"""Tools and endpoints that previously failed (issues #1 and #4)."""

import tempfile
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

import httpx

from server import main
from server.tools import (
    compare_tool, download_tool, embed_tool, keywords_tool, metadata_tool,
    related_records_tool, summarize_tool,
)
from server.tools.registry import dispatch_tool_call, get_tool_registry
from server.zenodo_client import MCPZenodoClient
from zenodo_stub import record, start_stub

TOOL_NAMES = {
    "search_records", "get_metadata", "get_citation", "detect_data_type",
    "compare_records", "list_files", "download_file", "generate_embed_link",
    "extract_keywords", "get_related_records", "summarize_record",
}


class ToolTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.queries = []
        origin = await start_stub(self.addAsyncCleanup, self.queries)
        cache = tempfile.TemporaryDirectory()
        self.addCleanup(cache.cleanup)
        self.client = MCPZenodoClient(base_url=f"{origin}/api", cache_dir=cache.name)
        self.client.api_token = None
        self.addAsyncCleanup(self.client._close_session)
        for module in (compare_tool, download_tool, embed_tool, keywords_tool,
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

    async def test_related_search_terms_carry_no_query_syntax(self):
        await dispatch_tool_call("get_related_records", {"record_id": "1", "max_results": 40})
        sent = [query["q"] for query in self.queries]
        self.assertIn("Ocean data depth salinity v1.0", sent)
        self.assertEqual({query["size"] for query in self.queries}, {"25"})
        self.assertFalse(
            [q for q in sent if set('()[]{}:/"') & set(q)], "query syntax was sent"
        )

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

    async def post_process(self, body):
        with patch.object(main.mcp_server.tool_invoker, "client", self.client):
            transport = httpx.ASGITransport(app=main.app, client=("127.0.0.1", 5000))
            async with httpx.AsyncClient(
                transport=transport, base_url="http://127.0.0.1:8000"
            ) as http:
                return await http.post("/mcp/process", json=body)

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
