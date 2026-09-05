"""VCV Library catalog: scrape, cache, and query the official VCV Rack module
marketplace (library.vcvrack.com).

The public listing pages are fully server-rendered HTML with real query-string
filters (brand/tag/license/query/sort/page/limit) - no login or API token
needed to browse. Verified live: `fetch("https://library.vcvrack.com/?...")`
returns a complete card list per page, no client-side JS required. This module
regex-parses that fixed HTML template rather than adding a bs4/lxml
dependency - it will break if VCV changes the template, which is an accepted
tradeoff for a small, dependency-free scraper.

Per-module popularity and last-updated date are NOT available on listing
pages (verified) - only on each module's own detail page. Fetching all
~4,500 detail pages up front isn't done here; `fetch_module_detail()` fetches
one on demand, cached once retrieved.
"""

from __future__ import annotations

import html
import re
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import aiohttp

LIBRARY_BASE = "https://library.vcvrack.com"
DB_PATH = Path.home() / ".oscmcp" / "vcv_library.db"

_THUMBNAIL_SPLIT = '<div class="library-thumbnail">'
_BRAND_RE = re.compile(r'library-thumbnail-brand" href="/\?brand=[^"]*">([^<]*)</a>')
_MODULE_LINK_RE = re.compile(r'<a href="(/[^"?]+/[^"?]+)">([^<]*)</a>')
_SCREENSHOT_RE = re.compile(r'<img src="(/screenshots/[^"]+)"')
_PRICE_RE = re.compile(r'library-price">\s*\$?([\d,.]+)')
_PLUS_RE = re.compile(r"Available in VCV\+")
_TAG_RE = re.compile(r'library-tag" href="/\?tag=[^"]*">([^<\n]*)')
_TOTAL_RE = re.compile(r"<strong>([\d,]+)</strong><span> modules found")


@dataclass
class VcvModule:
    plugin_slug: str
    module_slug: str
    brand: str
    name: str
    description: str
    tags: list[str] = field(default_factory=list)
    price: str | None = None
    is_plus: bool = False
    screenshot_url: str | None = None
    module_url: str = ""


def _parse_listing_html(page_html: str) -> tuple[list[VcvModule], int]:
    total_match = _TOTAL_RE.search(page_html)
    total = int(total_match.group(1).replace(",", "")) if total_match else 0

    section_start = page_html.find("library-thumbnails")
    if section_start == -1:
        return [], total
    section = page_html[section_start:]

    modules: list[VcvModule] = []
    chunks = section.split(_THUMBNAIL_SPLIT)[1:]
    for chunk in chunks:
        brand_match = _BRAND_RE.search(chunk)
        module_match = _MODULE_LINK_RE.search(chunk)
        if not brand_match or not module_match:
            continue
        module_url, name = module_match.group(1), module_match.group(2).strip()
        parts = module_url.strip("/").split("/", 1)
        if len(parts) != 2:
            continue
        plugin_slug, module_slug = parts

        screenshot_match = _SCREENSHOT_RE.search(chunk)
        price_match = _PRICE_RE.search(chunk)
        is_plus = bool(_PLUS_RE.search(chunk))
        tags = [t.strip() for t in _TAG_RE.findall(chunk) if t.strip()]

        # Description is the first <p> after the tag/price line that isn't
        # itself a button or the tags paragraph - grab the plain-text <p>.
        desc_match = re.search(r"</p>\s*<p>\s*([^<]+?)\s*</p>", chunk)
        description = desc_match.group(1).strip() if desc_match else ""

        modules.append(
            VcvModule(
                plugin_slug=plugin_slug,
                module_slug=module_slug,
                brand=html.unescape(brand_match.group(1).strip()),
                name=html.unescape(name),
                description=html.unescape(description),
                tags=[html.unescape(t) for t in tags],
                price=price_match.group(1) if price_match else None,
                is_plus=is_plus,
                screenshot_url=(LIBRARY_BASE + screenshot_match.group(1)) if screenshot_match else None,
                module_url=module_url,
            )
        )
    return modules, total


async def fetch_listing_page(
    session: aiohttp.ClientSession, page: int, limit: int = 100
) -> tuple[list[VcvModule], int]:
    params = {
        "page": str(page),
        "limit": str(limit),
        "brand": "",
        "license": "",
        "query": "",
        "sort": "name",
        "tag": "",
    }
    async with session.get(LIBRARY_BASE + "/", params=params, timeout=aiohttp.ClientTimeout(total=20)) as resp:
        resp.raise_for_status()
        page_html = await resp.text()
    return _parse_listing_html(page_html)


async def fetch_all_modules() -> list[VcvModule]:
    """Page through the entire public catalog. ~45 requests at limit=100 for ~4,500 modules."""
    modules: list[VcvModule] = []
    async with aiohttp.ClientSession(headers={"User-Agent": "osc-mcp/vcv-library-catalog"}) as session:
        page = 1
        total = None
        while True:
            page_modules, total = await fetch_listing_page(session, page, limit=100)
            if not page_modules:
                break
            modules.extend(page_modules)
            if total and len(modules) >= total:
                break
            page += 1
    return modules


def _init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS modules (
            plugin_slug TEXT NOT NULL,
            module_slug TEXT NOT NULL,
            brand TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            tags TEXT,
            price TEXT,
            is_plus INTEGER,
            screenshot_url TEXT,
            module_url TEXT,
            PRIMARY KEY (plugin_slug, module_slug)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sync_meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_modules_brand ON modules(brand)")
    conn.commit()


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _init_db(conn)
    return conn


def save_modules(modules: list[VcvModule]) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM modules")
        conn.executemany(
            """
            INSERT INTO modules
                (plugin_slug, module_slug, brand, name, description, tags, price, is_plus, screenshot_url, module_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    m.plugin_slug,
                    m.module_slug,
                    m.brand,
                    m.name,
                    m.description,
                    "\t".join(m.tags),
                    m.price,
                    1 if m.is_plus else 0,
                    m.screenshot_url,
                    m.module_url,
                )
                for m in modules
            ],
        )
        conn.execute(
            "INSERT OR REPLACE INTO sync_meta (key, value) VALUES ('last_synced_at', ?)",
            (str(time.time()),),
        )
        conn.execute(
            "INSERT OR REPLACE INTO sync_meta (key, value) VALUES ('total_modules', ?)",
            (str(len(modules)),),
        )
        conn.commit()
    finally:
        conn.close()


def query_modules(
    q: str = "",
    brand: str = "",
    tag: str = "",
    license_filter: str = "",
    page: int = 1,
    limit: int = 50,
) -> tuple[list[dict], int]:
    conn = get_connection()
    try:
        clauses = []
        params: list[str] = []
        if q:
            clauses.append("(name LIKE ? OR description LIKE ? OR brand LIKE ?)")
            like = f"%{q}%"
            params.extend([like, like, like])
        if brand:
            clauses.append("brand = ?")
            params.append(brand)
        if tag:
            clauses.append("tags LIKE ?")
            params.append(f"%{tag}%")
        if license_filter == "free":
            clauses.append("price IS NULL")
        elif license_filter == "premium":
            clauses.append("price IS NOT NULL")

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        total = conn.execute(f"SELECT COUNT(*) FROM modules {where}", params).fetchone()[0]  # noqa: S608
        offset = (page - 1) * limit
        rows = conn.execute(
            f"SELECT * FROM modules {where} ORDER BY brand, name LIMIT ? OFFSET ?",  # noqa: S608
            [*params, limit, offset],
        ).fetchall()
        results = [
            {
                "plugin_slug": r["plugin_slug"],
                "module_slug": r["module_slug"],
                "brand": r["brand"],
                "name": r["name"],
                "description": r["description"],
                "tags": r["tags"].split("\t") if r["tags"] else [],
                "price": r["price"],
                "is_plus": bool(r["is_plus"]),
                "screenshot_url": r["screenshot_url"],
                "module_url": r["module_url"],
            }
            for r in rows
        ]
        return results, total
    finally:
        conn.close()


def get_sync_status() -> dict:
    conn = get_connection()
    try:
        rows = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM sync_meta")}
        return {
            "last_synced_at": float(rows["last_synced_at"]) if "last_synced_at" in rows else None,
            "total_modules": int(rows["total_modules"]) if "total_modules" in rows else 0,
        }
    finally:
        conn.close()


def list_brands() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT brand, COUNT(*) AS count FROM modules GROUP BY brand ORDER BY brand").fetchall()
        return [{"brand": r["brand"], "count": r["count"]} for r in rows]
    finally:
        conn.close()


def list_tags() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT tags FROM modules WHERE tags != ''").fetchall()
    finally:
        conn.close()
    counts: dict[str, int] = {}
    for r in rows:
        for t in r["tags"].split("\t"):
            if t:
                counts[t] = counts.get(t, 0) + 1
    return [{"tag": t, "count": c} for t, c in sorted(counts.items())]


_DETAIL_LICENSE_RE = re.compile(r"License:\s*(?:<a[^>]*>)?\s*([^\n<]+)")
_DETAIL_UPDATED_RE = re.compile(r'Last updated:\s*<span[^>]*data-timestamp="(\d+)"')
_DETAIL_CREATED_RE = re.compile(r'Created:\s*<span[^>]*data-timestamp="(\d+)"')
_DETAIL_POPULARITY_RE = re.compile(r"Popularity:\s*([\d,]+)")
_DETAIL_AUTHOR_RE = re.compile(r"Author:\s*(?:<a[^>]*>)?\s*([^\n<]+)")


async def fetch_module_detail(plugin_slug: str, module_slug: str) -> dict:
    """On-demand fetch of one module's detail page for license/dates/popularity.

    Not called in bulk (~4,500 modules is too many individual requests to do
    eagerly) - fetched per-module when a user actually opens it in the UI.
    """
    url = f"{LIBRARY_BASE}/{plugin_slug}/{module_slug}"
    async with aiohttp.ClientSession(headers={"User-Agent": "osc-mcp/vcv-library-catalog"}) as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            resp.raise_for_status()
            detail_html = await resp.text()

    unavailable = "Unavailable" in detail_html[: detail_html.find("Author:") if "Author:" in detail_html else 2000]
    license_match = _DETAIL_LICENSE_RE.search(detail_html)
    updated_match = _DETAIL_UPDATED_RE.search(detail_html)
    created_match = _DETAIL_CREATED_RE.search(detail_html)
    popularity_match = _DETAIL_POPULARITY_RE.search(detail_html)
    author_match = _DETAIL_AUTHOR_RE.search(detail_html)

    def _timestamp_to_iso(match: re.Match[str] | None) -> str | None:
        if not match:
            return None
        return datetime.fromtimestamp(int(match.group(1)), tz=UTC).date().isoformat()

    return {
        "plugin_slug": plugin_slug,
        "module_slug": module_slug,
        "unavailable": unavailable,
        "license": license_match.group(1).strip() if license_match else None,
        "last_updated": _timestamp_to_iso(updated_match),
        "created": _timestamp_to_iso(created_match),
        "popularity": int(popularity_match.group(1).replace(",", "")) if popularity_match else None,
        "author": author_match.group(1).strip() if author_match else None,
    }
