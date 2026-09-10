"""Prowlarr MCP server: search indexers and queue downloads."""

import os
from collections.abc import AsyncIterator, Iterable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import httpx
from mcp.server.fastmcp import Context, FastMCP

DEFAULT_URL = "http://prowlarr.home.gustafson.me:9696"


@dataclass(frozen=True, slots=True)
class ProwlarrClient:
    http: httpx.AsyncClient

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response = await self.http.request(method, path, **kwargs)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            body = exc.response.text.strip()
            raise RuntimeError(f"Prowlarr returned {exc.response.status_code} for {method} {path}: {body[:200]}") from exc
        except httpx.RequestError as exc:
            raise RuntimeError(f"Could not reach Prowlarr at {self.http.base_url}: {exc}") from exc
        return response.json()

    async def search(self, params: dict[str, Any]) -> list[dict[str, Any]]:
        return await self._request("GET", "/api/v1/search", params=params)

    async def grab(self, guid: str, indexer_id: int) -> dict[str, Any]:
        return await self._request("POST", "/api/v1/search", json={"guid": guid, "indexerId": indexer_id})

    async def indexers(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/api/v1/indexer")

    async def categories(self) -> list[dict[str, Any]]:
        return await self._request("GET", "/api/v1/indexer/categories")


@asynccontextmanager
async def _lifespan(_server: FastMCP) -> AsyncIterator[ProwlarrClient]:
    api_key = os.environ.get("PROWLARR_API_KEY")
    if not api_key:
        raise RuntimeError("PROWLARR_API_KEY is not set")
    base_url = os.environ.get("PROWLARR_URL", DEFAULT_URL).rstrip("/")
    async with httpx.AsyncClient(
        base_url=base_url,
        headers={"X-Api-Key": api_key},
        timeout=httpx.Timeout(60.0, connect=10.0),
    ) as http:
        yield ProwlarrClient(http=http)


mcp = FastMCP("prowlarr", lifespan=_lifespan)


def _client(ctx: Context) -> ProwlarrClient:
    return ctx.request_context.lifespan_context


def _humanize_size(num_bytes: int | None) -> str | None:
    if num_bytes is None:
        return None
    size = float(num_bytes)
    units = ("B", "KiB", "MiB", "GiB", "TiB", "PiB")
    for unit in units[:-1]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} {units[-1]}"


def _summarize_release(release: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": release.get("title"),
        "indexer": release.get("indexer"),
        "indexerId": release.get("indexerId"),
        "guid": release.get("guid"),
        "protocol": release.get("protocol"),
        "size": _humanize_size(release.get("size")),
        "sizeBytes": release.get("size"),
        "seeders": release.get("seeders"),
        "leechers": release.get("leechers"),
        "grabs": release.get("grabs"),
        "ageDays": release.get("age"),
        "publishDate": release.get("publishDate"),
        "categories": [c.get("name") for c in (release.get("categories") or []) if c.get("name")],
        "infoUrl": release.get("infoUrl"),
    }


def _flatten_categories(categories: Iterable[dict[str, Any]], parent: str | None = None) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    for category in categories:
        flat.append({"id": category.get("id"), "name": category.get("name"), "parent": parent})
        flat.extend(_flatten_categories(category.get("subCategories") or [], category.get("name")))
    return flat


@mcp.tool()
async def search(
    ctx: Context,
    query: str,
    search_type: str = "search",
    indexer_ids: list[int] | None = None,
    categories: list[int] | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """Search configured Prowlarr indexers for releases.

    search_type is the Newznab/Torznab search mode: "search" (generic, works on every indexer), "tvsearch", "moviesearch", "music", or "book". indexer_ids and categories restrict the search to those indexer/category ids (see list_indexers and list_categories). Each result carries guid and indexerId, which queue_download needs to grab it.
    """
    params: dict[str, Any] = {"query": query, "type": search_type, "limit": limit}
    if indexer_ids:
        params["indexerIds"] = indexer_ids
    if categories:
        params["categories"] = categories
    releases = await _client(ctx).search(params)
    return [_summarize_release(release) for release in releases]


@mcp.tool()
async def queue_download(ctx: Context, guid: str, indexer_id: int) -> dict[str, Any]:
    """Grab a release, sending it to the download client Prowlarr is configured to use.

    guid and indexer_id come from a search result. Prowlarr resolves the release from its cache of recent searches, so grab shortly after searching.
    """
    result = await _client(ctx).grab(guid, indexer_id)
    return {
        "status": "grabbed",
        "title": result.get("title"),
        "indexer": result.get("indexer"),
        "guid": guid,
        "indexerId": indexer_id,
    }


@mcp.tool()
async def list_indexers(ctx: Context) -> list[dict[str, Any]]:
    """List configured indexers and their ids, for scoping a search via indexer_ids."""
    return [
        {
            "id": indexer.get("id"),
            "name": indexer.get("name"),
            "protocol": indexer.get("protocol"),
            "enabled": indexer.get("enable"),
            "supportsSearch": indexer.get("supportsSearch"),
        }
        for indexer in await _client(ctx).indexers()
    ]


@mcp.tool()
async def list_categories(ctx: Context) -> list[dict[str, Any]]:
    """List indexer categories as flat id/name/parent entries, for scoping a search via categories."""
    return _flatten_categories(await _client(ctx).categories())


def main() -> None:
    mcp.run()
