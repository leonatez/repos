from fastapi import APIRouter, HTTPException, Query, Header
from typing import Optional

from db import get_db
from auth import get_optional_user

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def search_posts(
    q: str = Query(..., min_length=1, max_length=200, description="Search keyword"),
    limit: int = Query(12, ge=1, le=50),
    offset: int = Query(0, ge=0),
    authorization: Optional[str] = Header(None),
):
    """
    Search published posts by title (VI/EN), summary (VI/EN), or tags.
    Uses ILIKE for case-insensitive partial matching.
    """
    await get_optional_user(authorization)
    db = get_db()

    try:
        posts, total = await db.search_posts(q, limit=limit, offset=offset)
        return {
            "query": q,
            "items": posts,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
