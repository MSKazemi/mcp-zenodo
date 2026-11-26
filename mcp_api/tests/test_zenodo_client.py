"""Contract tests for the server-side Zenodo API client."""

from unittest import IsolatedAsyncioTestCase

from server.zenodo_client import MCPZenodoClient


class RecordingClient(MCPZenodoClient):
    """Capture calls instead of performing HTTP requests."""

    def __init__(self):
        super().__init__(api_token="token", base_url="https://example.org/api")
        self.calls = []

    async def _make_request(self, method, endpoint, **kwargs):
        self.calls.append((method, endpoint, kwargs))
        return {"ok": True}


class ClientContractTests(IsolatedAsyncioTestCase):
    async def test_get_metadata_delegates_to_records_endpoint(self):
        client = RecordingClient()

        await client.get_metadata("42")

        self.assertEqual(client.calls, [("GET", "records/42", {})])

    async def test_search_records_builds_zenodo_params(self):
        client = RecordingClient()

        await client.search_records("climate", max_results=7, sort="bestmatch")

        self.assertEqual(
            client.calls,
            [
                (
                    "GET",
                    "records",
                    {"params": {"q": "climate", "size": 7, "sort": "bestmatch"}},
                )
            ],
        )
