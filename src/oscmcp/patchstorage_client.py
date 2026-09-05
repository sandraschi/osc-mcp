"""Patchstorage community patch browser: search and fetch patches from the
public Patchstorage.com Beta REST API - all 92 platforms it hosts (VCV Rack,
SuperCollider, Max for Live, TouchOSC, and 88 others), no scraping needed.

Live-verified: `GET https://patchstorage.com/api/beta/patches` is a real,
self-describing WordPress REST API and needs no auth to read. VCV Rack's
platform taxonomy id is 745 (9,179+ patches at verification time). The
per-patch detail response includes real direct-download file URLs - this
module only proxies Patchstorage's own responses, it doesn't scrape or
guess anything.

The Alpha API (`patchstorage.com/api/alpha/`) is deprecated per Patchstorage's
own docs (shut down 2023Q1) - only Beta is used here.

No rate limits are documented (no `X-RateLimit-*` headers observed on a live
request), so responses are cached briefly rather than re-hit on every UI
re-render or pagination click.
"""

from __future__ import annotations

import time
from typing import Any

import aiohttp

BASE = "https://patchstorage.com/api/beta"
_HEADERS = {"User-Agent": "osc-mcp/patchstorage-browser"}


class _TTLCache:
    """Minimal TTL cache - not worth a dependency for this small a need."""

    def __init__(self, ttl_seconds: float, max_entries: int = 256) -> None:
        self._ttl = ttl_seconds
        self._max = max_entries
        self._store: dict[Any, tuple[float, Any]] = {}

    def get(self, key: Any) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if time.monotonic() >= expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: Any, value: Any) -> None:
        if len(self._store) >= self._max:
            self._store.pop(next(iter(self._store)))
        self._store[key] = (time.monotonic() + self._ttl, value)


_platforms_cache = _TTLCache(ttl_seconds=3600, max_entries=1)
_search_cache = _TTLCache(ttl_seconds=120, max_entries=200)
_detail_cache = _TTLCache(ttl_seconds=600, max_entries=500)


async def list_platforms() -> list[dict[str, Any]]:
    """All platforms Patchstorage hosts patches for (92 at verification time),
    sorted by name. Cached for an hour - this list changes rarely.
    """
    cached = _platforms_cache.get("all")
    if cached is not None:
        return cached
    async with aiohttp.ClientSession(headers=_HEADERS) as session:
        async with session.get(
            f"{BASE}/platforms", params={"per_page": "100"}, timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
    platforms = sorted(
        ({"id": p["id"], "name": p["name"], "slug": p["slug"]} for p in data),
        key=lambda p: p["name"].lower(),
    )
    _platforms_cache.set("all", platforms)
    return platforms


async def search_patches(
    platform_id: int | None,
    q: str = "",
    orderby: str = "date",
    order: str = "desc",
    page: int = 1,
    per_page: int = 24,
) -> dict[str, Any]:
    """Proxies `GET /beta/patches`. `platform_id=None` searches across all
    platforms; pass one of the ids from `list_platforms()` to filter to one.
    """
    cache_key = (platform_id, q, orderby, order, page, per_page)
    cached = _search_cache.get(cache_key)
    if cached is not None:
        return cached

    request_params: list[tuple[str, str]] = [
        ("page", str(page)),
        ("per_page", str(per_page)),
        ("orderby", orderby),
        ("order", order),
    ]
    if q:
        request_params.append(("search", q))
    if platform_id is not None:
        request_params.append(("platforms[]", str(platform_id)))

    async with aiohttp.ClientSession(headers=_HEADERS) as session:
        async with session.get(
            f"{BASE}/patches", params=request_params, timeout=aiohttp.ClientTimeout(total=15)
        ) as resp:
            resp.raise_for_status()
            patches = await resp.json()
            total = int(resp.headers.get("X-WP-Total", len(patches)))

    result = {"patches": patches, "total": total, "page": page, "per_page": per_page}
    _search_cache.set(cache_key, result)
    return result


async def get_patch(patch_id: int) -> dict[str, Any]:
    """Proxies `GET /beta/patches/{id}` - includes real direct-download file
    URLs (`files[].url`), unlike the list response.
    """
    cached = _detail_cache.get(patch_id)
    if cached is not None:
        return cached
    async with aiohttp.ClientSession(headers=_HEADERS) as session:
        async with session.get(f"{BASE}/patches/{patch_id}", timeout=aiohttp.ClientTimeout(total=15)) as resp:
            resp.raise_for_status()
            detail = await resp.json()
    _detail_cache.set(patch_id, detail)
    return detail
