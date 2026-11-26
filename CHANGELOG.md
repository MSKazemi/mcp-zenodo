# Changelog

## Unreleased

### Changed
- **Breaking:** the HTTP service accepts requests from other machines, containers or proxies
  only with `MCP_API_KEY`, and from other browser origins only if listed in `CORS_ORIGINS`.
- **Breaking:** `search_records` returns short record summaries; pass `full: true` for Zenodo's
  complete records.
- `detect_data_type` reports Zenodo's resource type, including types such as `poster`.
- `get_related_records` sends one search and its default threshold is 0.05 instead of 0.3.
- The stdio server (`mcp_sdk_core`) offers all eleven tools, using the `mcp_api` code.
- `/mcp/process` rejects unsupported filters.

### Added
- Real file downloads with size and checksum verification. Thanks @cheeseonamonkey (#7).
- The `/docs` page can send the API key. Thanks @harshacreate (#26).
- `extract_keywords` and `generate_embed_link`.
- A Dockerfile, a test suite and CI.
- A contributor guide, issue and pull request templates, a security policy and a Makefile.
- Parameter descriptions for the stdio tools.

### Fixed
- A single Zenodo client replaces the broken duplicate. Thanks @cheeseonamonkey (#6).
- BibTeX citations stay valid when titles or names contain special characters. Thanks
  @harshacreate (#25).
- `compare_records`, `/mcp/process`, `list_files` and related-record lookups.
- Record IDs are validated before they are used in a request.
- Clear errors for invalid tool arguments and Zenodo's rate limit; page size is capped
  without a token.

### Removed
- Unused dependencies, unused modules and test scripts that no longer ran.
