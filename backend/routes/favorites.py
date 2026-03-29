from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from db import get_db
from auth import get_current_user

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("")
async def get_saved_posts(
    limit: int = 12,
    offset: int = 0,
    authorization: Optional[str] = Header(None),
):
    """Get the authenticated user's saved/bookmarked posts."""
    user = await get_current_user(authorization)
    user_id = user["id"]
    db = get_db()

    try:
        posts, total = await db.get_saved_posts(user_id, limit=limit, offset=offset)
        return {"items": posts, "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
