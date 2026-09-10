# prowlarr-mcp

stdio MCP server exposing Prowlarr search and download-grab over the Prowlarr v1 API.

## Tools

- `search(query, search_type="search", indexer_ids=None, categories=None, limit=50)` — search indexers; returns releases with `guid`/`indexerId` for grabbing.
- `queue_download(guid, indexer_id)` — grab a release to Prowlarr's configured download client.
- `list_indexers()` — configured indexers and their ids.
- `list_categories()` — flattened category ids/names.

## Configuration

- `PROWLARR_API_KEY` (required) — Prowlarr API key (`X-Api-Key`).
- `PROWLARR_URL` — base URL; defaults to `http://prowlarr.home.gustafson.me:9696`.
