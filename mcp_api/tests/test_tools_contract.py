"""Tool tests against record payloads shaped like the Zenodo records API."""

from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from server.tools import citation_tool, data_type_tool, files_tool, related_records_tool
from server.zenodo_client import MCPZenodoClient

CONTENT_URL = "https://zenodo.org/api/records/1/files/table.csv/content"


def _record(record_id, title="Ocean temperature data"):
    return {
        "id": record_id,
        "metadata": {"title": title, "creators": [{"name": "Doe, Jane"}]},
        "files": [{"key": "table.csv", "size": 3, "links": {"self": CONTENT_URL}}],
    }


class FakeClient(MCPZenodoClient):
    """Serve canned payloads instead of performing HTTP requests."""

    def __init__(self):
        super().__init__(api_token="token", base_url="https://example.org/api")
        self.requests = []

    async def _make_request(self, method, endpoint, **kwargs):
        self.requests.append(endpoint)
        if endpoint == "records":
            return {"hits": {"hits": [_record(1), _record(2)], "total": 2}}
        return _record(1)


class RecordIdTests(IsolatedAsyncioTestCase):
    async def test_non_numeric_record_id_never_reaches_the_api(self):
        client = FakeClient()
        for bad in ["../deposit/depositions", "1/../../me", "1?x=", "", "١"]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                await client.get_metadata(bad)
        self.assertEqual(client.requests, [])

    async def test_integer_record_id_is_accepted(self):
        client = FakeClient()
        await client.get_metadata(42)
        self.assertEqual(client.requests, ["records/42"])


class ToolPayloadTests(IsolatedAsyncioTestCase):
    async def test_bibtex_escapes_special_characters_in_title_and_authors(self):
        class CitationClient:
            async def get_metadata(self, record_id):
                return {
                    "metadata": {
                        "title": "Salt & water: 100% {raw}_data #1",
                        "creators": [{"name": "Doe, Jane & Roe"}],
                        "publication_date": "2025-01-02",
                        "doi": "10.5281/zenodo.1",
                    }
                }

        with patch.object(citation_tool, "_client", CitationClient()):
            result = await citation_tool.get_citation("1")

        self.assertIn(r"author = {Doe, Jane \& Roe}", result.citation)
        self.assertIn(r"title = {Salt \& water: 100\% \{raw\}\_data \#1}", result.citation)

    async def test_list_files_reports_name_and_url(self):
        with patch.object(files_tool, "_client", FakeClient()):
            result = await files_tool.list_files("1")
        self.assertEqual(result["files"][0]["filename"], "table.csv")
        self.assertEqual(result["files"][0]["download_url"], CONTENT_URL)

    async def test_data_type_falls_back_to_file_extensions(self):
        with patch.object(data_type_tool, "_client", FakeClient()):
            result = await data_type_tool.detect_data_type("1")
        self.assertEqual(result["data_type"], "dataset")
        self.assertEqual(result["metadata"]["file_types"], ["csv"])

    async def test_related_records_excludes_source_and_repeats(self):
        with patch.object(related_records_tool, "_client", FakeClient()):
            result = await related_records_tool.get_related_records("1")
        self.assertEqual([r["record_id"] for r in result["related_records"]], ["2"])
