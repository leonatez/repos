from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from database import supabase_service as supabase
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

    try:
        saved_result = (
            supabase.table("saved_posts")
            .select("post_id, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        post_ids = [s["post_id"] for s in saved_result.data]
        if not post_ids:
            return {"items": [], "total": 0, "limit": limit, "offset": offset}

        posts_result = (
            supabase.table("posts")
            .select(
                "*, github_repositories(id, repo_name, github_url), post_tags(tags(id, name, slug))"
            )
            .eq("status", "published")
            .in_("id", post_ids)
            .execute()
        )

        posts = []
        for p in posts_result.data:
            tags_list = [pt["tags"] for pt in p.get("post_tags", []) if pt.get("tags")]
            repo = p.get("github_repositories")

            # Get likes count
            likes_count = 0
            try:
                lc = (
                    supabase.table("likes")
                    .select("id", count="exact")
                    .eq("post_id", p["id"])
                    .execute()
                )
                likes_count = lc.count or 0
            except Exception:
                pass

            posts.append({
                **{k: v for k, v in p.items() if k not in ("post_tags", "github_repositories")},
                "tags": tags_list,
                "repo": repo,
                "likes_count": likes_count,
                "is_liked": False,
                "is_saved": True,
            })

        # Count total
        total_result = (
            supabase.table("saved_posts")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .execute()
        )
        total = total_result.count or len(posts)

        return {"items": posts, "total": total, "limit": limit, "offset": offset}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
