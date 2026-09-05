"""Patchstorage community patch browser API: search and fetch patches across
all platforms Patchstorage.com hosts (VCV Rack, SuperCollider, Max for Live,
TouchOSC, and 88 others).

Thin proxy over the real Patchstorage Beta API - no local cache/sync step
like vcv_library.py, since Patchstorage already does server-side search,
filtering, and pagination. Downloading a patch still goes through
Patchstorage's own file URL (returned by `/patches/{id}`) - this API
surfaces the catalog, it doesn't fetch files on the user's behalf.
"""

from fastapi import APIRouter, HTTPException, Query

from oscmcp.patchstorage_client import get_patch, list_platforms, search_patches

router = APIRouter(tags=["patchstorage"], prefix="/patchstorage")


@router.get("/platforms")
async def patchstorage_platforms() -> dict:
    try:
        return {"platforms": await list_platforms()}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch Patchstorage platforms: {exc}") from exc


@router.get("/patches")
async def patchstorage_patches(
    platform_id: int | None = Query(None, description="Filter to one platform id from /platforms; omit for all"),
    q: str = Query("", description="Search title/content"),
    orderby: str = Query(
        "date",
        description="author, date, id, modified, relevance, slug, title, view_count, like_count, download_count",
    ),
    order: str = Query("desc", description="'asc' or 'desc'"),
    page: int = Query(1, ge=1),
    per_page: int = Query(24, ge=1, le=100),
) -> dict:
    try:
        return await search_patches(
            platform_id=platform_id, q=q, orderby=orderby, order=order, page=page, per_page=per_page
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to search Patchstorage: {exc}") from exc


@router.get("/patches/{patch_id}")
async def patchstorage_patch_detail(patch_id: int) -> dict:
    try:
        return await get_patch(patch_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to fetch Patchstorage patch {patch_id}: {exc}") from exc
