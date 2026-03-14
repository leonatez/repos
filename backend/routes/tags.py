from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from database import supabase_service as supabase
from auth import get_optional_user

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("")
async def list_tags():
    """List all tags."""
    try:
        result = supabase.table("tags").select("*").order("name").execute()
        return result.data
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
    user = await get_optional_user(authorization)
    user_id = user["id"] if user else None

    try:
        # Get tag ID
        tag_result = (
            supabase.table("tags").select("*").eq("slug", slug).single().execute()
        )
        if not tag_result.data:
            raise HTTPException(status_code=404, detail="Tag not found")

        tag = tag_result.data

        # Get post IDs for this tag
        pt_result = (
            supabase.table("post_tags")
            .select("post_id")
            .eq("tag_id", tag["id"])
            .execute()
        )
        post_ids = [pt["post_id"] for pt in pt_result.data]

        if not post_ids:
            return {
                "tag": tag,
                "items": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
            }

        # Fetch posts
        posts_result = (
            supabase.table("posts")
            .select(
                "*, github_repositories(id, repo_name, github_url), post_tags(tags(id, name, slug))"
            )
            .eq("status", "published")
            .in_("id", post_ids)
            .order("published_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        posts = []
        for p in posts_result.data:
            tags_list = [pt["tags"] for pt in p.get("post_tags", []) if pt.get("tags")]
            repo = p.get("github_repositories")
            posts.append({
                **{k: v for k, v in p.items() if k not in ("post_tags", "github_repositories")},
                "tags": tags_list,
                "repo": repo,
                "likes_count": 0,
                "is_liked": False,
                "is_saved": False,
            })

        return {
            "tag": tag,
            "items": posts,
            "total": len(post_ids),
            "limit": limit,
            "offset": offset,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
