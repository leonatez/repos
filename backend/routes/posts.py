from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from db import get_db
from auth import get_current_user, get_optional_user

router = APIRouter(prefix="/api/posts", tags=["posts"])


@router.get("")
async def list_posts(
    limit: int = 12,
    offset: int = 0,
    authorization: Optional[str] = Header(None),
):
    """List published posts with pagination."""
    user = await get_optional_user(authorization)
    user_id = user["id"] if user else None
    db = get_db()

    try:
        posts, total = await db.get_posts(limit=limit, offset=offset, status="published")
        if user_id:
            for p in posts:
                p["is_liked"] = await db.is_liked_by_user(str(p["id"]), user_id)
                p["is_saved"] = await db.is_saved_by_user(str(p["id"]), user_id)
                p["likes_count"] = await db.get_likes_count(str(p["id"]))
        else:
            for p in posts:
                p["likes_count"] = await db.get_likes_count(str(p["id"]))
        return {"items": posts, "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{slug}")
async def get_post_by_slug(
    slug: str,
    authorization: Optional[str] = Header(None),
):
    """Get a single published post by slug. Increments view count."""
    user = await get_optional_user(authorization)
    user_id = user["id"] if user else None
    db = get_db()

    try:
        post = await db.get_post_by_slug(slug, status="published")
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        await db.increment_views(str(post["id"]))
        post["views"] = (post.get("views") or 0) + 1

        post["likes_count"] = await db.get_likes_count(str(post["id"]))
        if user_id:
            post["is_liked"] = await db.is_liked_by_user(str(post["id"]), user_id)
            post["is_saved"] = await db.is_saved_by_user(str(post["id"]), user_id)

        return post
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{post_id}/like")
async def toggle_like(
    post_id: str,
    authorization: Optional[str] = Header(None),
):
    """Toggle like on a post. Requires authentication."""
    user = await get_current_user(authorization)
    user_id = user["id"]
    db = get_db()

    try:
        liked = await db.toggle_like(user_id, post_id)
        likes_count = await db.get_likes_count(post_id)
        return {"liked": liked, "likes_count": likes_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{post_id}/save")
async def toggle_save(
    post_id: str,
    authorization: Optional[str] = Header(None),
):
    """Toggle save/bookmark on a post. Requires authentication."""
    user = await get_current_user(authorization)
    user_id = user["id"]
    db = get_db()

    try:
        saved = await db.toggle_save(user_id, post_id)
        return {"saved": saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
