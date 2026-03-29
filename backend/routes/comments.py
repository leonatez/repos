from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from db import get_db
from auth import get_current_user
from models.schemas import CommentCreate

router = APIRouter(prefix="/api/posts", tags=["comments"])


@router.get("/{post_id}/comments")
async def list_comments(post_id: str):
    """List visible comments for a post."""
    try:
        db = get_db()
        return await db.get_comments(post_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{post_id}/comments")
async def create_comment(
    post_id: str,
    comment: CommentCreate,
    authorization: Optional[str] = Header(None),
):
    """Create a new comment. Requires authentication."""
    user = await get_current_user(authorization)
    user_id = user["id"]
    db = get_db()

    # Verify post exists and is published
    try:
        post = await db.get_post_by_id(post_id)
        if not post or post.get("status") != "published":
            raise HTTPException(status_code=404, detail="Post not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        return await db.create_comment(post_id, user_id, comment.content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
