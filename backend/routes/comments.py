from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from database import supabase_service as supabase
from auth import get_current_user
from models.schemas import CommentCreate

router = APIRouter(prefix="/api/posts", tags=["comments"])


@router.get("/{post_id}/comments")
async def list_comments(post_id: str):
    """List visible comments for a post."""
    try:
        result = (
            supabase.table("comments")
            .select("*, users(username, avatar_url)")
            .eq("post_id", post_id)
            .eq("status", "visible")
            .order("created_at", desc=False)
            .execute()
        )

        comments = []
        for c in result.data:
            user_data = c.get("users") or {}
            comments.append({
                **{k: v for k, v in c.items() if k != "users"},
                "username": user_data.get("username"),
                "avatar_url": user_data.get("avatar_url"),
            })

        return comments
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

    # Verify post exists and is published
    try:
        post_check = (
            supabase.table("posts")
            .select("id")
            .eq("id", post_id)
            .eq("status", "published")
            .execute()
        )
        if not post_check.data:
            raise HTTPException(status_code=404, detail="Post not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        result = (
            supabase.table("comments")
            .insert(
                {
                    "post_id": post_id,
                    "user_id": user_id,
                    "content": comment.content,
                    "status": "visible",
                }
            )
            .execute()
        )
        c = result.data[0]

        # Fetch user info
        try:
            user_result = (
                supabase.table("users")
                .select("username, avatar_url")
                .eq("id", user_id)
                .single()
                .execute()
            )
            user_data = user_result.data or {}
        except Exception:
            user_data = {}

        return {
            **c,
            "username": user_data.get("username"),
            "avatar_url": user_data.get("avatar_url"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
