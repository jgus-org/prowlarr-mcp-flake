# prowlarr-mcp

Nix flake providing **prowlarr-mcp**, a stdio MCP server that searches a Prowlarr server's configured indexers and grabs releases through the [Prowlarr v1 API](https://prowlarr.com/docs/api/). The server is first-party Python source carried in this flake; there is no upstream project.

## Outputs

- `packages.<system>.prowlarr-mcp` — the package, installing the `prowlarr-mcp` console script at `bin/prowlarr-mcp`.
- `packages.<system>.default` — the same package.

Packages are the flake's only outputs, defined for `x86_64-linux`, `aarch64-linux`, and `aarch64-darwin`. The package builds entirely from nixpkgs (`python3`, its `mcp` and `httpx` bindings, and `hatchling`) and vendors no distribution of its own; the flake declares it MIT-licensed.

Consume the package from a flake input:

```nix
prowlarr-mcp.packages.${system}.prowlarr-mcp
```

Or build it directly:

```bash
nix build "github:jgus-org/prowlarr-mcp-flake#default"
```

## Running it

Register `prowlarr-mcp` as an MCP server command in the client that will use it. It speaks MCP over stdio for the life of the process; it is not a daemon and listens on no port.

Environment it reads:

- `PROWLARR_API_KEY` (required) — the Prowlarr API key, sent as `X-Api-Key`. Startup fails with `PROWLARR_API_KEY is not set` when it is absent.
- `PROWLARR_URL` — base URL of the Prowlarr server, e.g. `http://prowlarr.example.net:9696`. The module carries a hard-coded default pointing at the author's own home-lab host, which resolves for no other deployment: set this variable explicitly.

Requests are given 60 s, with a 10 s connect limit. A non-2xx response raises `Prowlarr returned <status> for <method> <path>: <body>` with the body cut to its first 200 characters; an unreachable server raises `Could not reach Prowlarr at <base_url>`.

## Tools

- `search(query, search_type="search", indexer_ids=None, categories=None, limit=50)` — search indexers for releases. `search_type` is the Newznab/Torznab search mode: `"search"` (generic, works on every indexer), `"tvsearch"`, `"moviesearch"`, `"music"`, or `"book"`. `indexer_ids` and `categories` restrict the search to those ids. Each result carries `guid` and `indexerId`, which `queue_download` needs, plus `title`, `indexer`, `protocol`, `seeders`, `leechers`, `grabs`, `ageDays`, `publishDate`, `infoUrl`, `categories` (names only), and the release size twice — `sizeBytes` raw and `size` humanized.
- `queue_download(guid, indexer_id)` — grab a release to the download client Prowlarr is configured to use. Takes `guid` and `indexerId` from a search result and reports the grabbed title.
- `list_indexers()` — configured indexers with `id`, `name`, `protocol`, `enabled`, `supportsSearch`, for scoping a search with `indexer_ids`.
- `list_categories()` — category ids as flat `id`/`name`/`parent` entries, subcategories included, for scoping a search with `categories`.

## Sharp edges

`queue_download` resolves the `guid` from Prowlarr's cache of recent searches, so it succeeds only shortly after the `search` call that returned that release. A grab of an older `guid` fails with whatever error Prowlarr returns.
