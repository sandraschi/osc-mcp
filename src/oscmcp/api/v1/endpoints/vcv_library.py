"""VCV Library catalog API: browse, search, and sync the official VCV Rack
module marketplace (library.vcvrack.com).

Read-only against a local SQLite cache populated by `POST /sync`. Actually
installing a module still requires the user's own VCV account (the browser
"Add" flow + Rack's own "Update all") - this API surfaces the catalog and
links out to the real install flow, it doesn't automate an account-gated
action on the user's behalf.
"""

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Query

from oscmcp.vcv_library import (
    fetch_all_modules,
    fetch_module_detail,
    get_sync_status,
    list_brands,
    list_tags,
    query_modules,
    save_modules,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["vcv-library"], prefix="/vcv-library")

_sync_lock = asyncio.Lock()
_sync_in_progress = False


@router.get("/status")
async def vcv_library_status() -> dict:
    status = get_sync_status()
    return {**status, "syncing": _sync_in_progress}


@router.post("/sync")
async def vcv_library_sync() -> dict:
    global _sync_in_progress
    if _sync_lock.locked():
        return {"started": False, "reason": "sync already in progress"}

    async def _run_sync() -> None:
        global _sync_in_progress
        async with _sync_lock:
            _sync_in_progress = True
            try:
                modules = await fetch_all_modules()
                save_modules(modules)
                logger.info("VCV Library sync complete: %d modules", len(modules))
            except Exception:
                logger.exception("VCV Library sync failed")
            finally:
                _sync_in_progress = False

    _sync_in_progress = True
    asyncio.create_task(_run_sync())  # fire-and-forget: progress is polled via /status
    return {"started": True}


@router.get("/modules")
async def vcv_library_modules(
    q: str = Query("", description="Search name/description/brand"),
    brand: str = Query("", description="Exact brand filter"),
    tag: str = Query("", description="Tag filter"),
    license: str = Query("", description="'free' or 'premium'"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
) -> dict:
    results, total = query_modules(q=q, brand=brand, tag=tag, license_filter=license, page=page, limit=limit)
    return {"modules": results, "total": total, "page": page, "limit": limit}


@router.get("/brands")
async def vcv_library_brands() -> dict:
    return {"brands": list_brands()}


@router.get("/tags")
async def vcv_library_tags() -> dict:
    return {"tags": list_tags()}


@router.get("/modules/{plugin_slug}/{module_slug}/detail")
async def vcv_library_module_detail(plugin_slug: str, module_slug: str) -> dict:
    try:
        return await fetch_module_detail(plugin_slug, module_slug)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch module detail: {exc}") from exc
