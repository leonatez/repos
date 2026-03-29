from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from db import get_db
from auth import get_optional_user

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("")
async def list_tags():
    """List all tags."""
    try:
        db = get_db()
        return await db.get_all_tags()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{slug}/posts")
async def get_posts_by_tag(
    slug: str,
    limit: int = 12,
    offset: int = 0,
    authorization: Optional[str] = Header(None),
):
    """List published posts that have a specific tag."""
    await get_optional_user(authorization)
    db = get_db()

    try:
        tag = await db.get_tag_by_slug(slug)
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")

        posts, total = await db.get_posts_by_tag(slug, limit=limit, offset=offset)

        return {
            "tag": tag,
            "items": posts,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
