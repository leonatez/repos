from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from database import supabase_service as supabase
from auth import get_current_user, get_optional_user

router = APIRouter(prefix="/api/posts", tags=["posts"])


def _enrich_post(p: dict, user_id: Optional[str] = None) -> dict:
    """Enrich a post dict with tags, repo, likes_count, is_liked, is_saved."""
    tags = [pt["tags"] for pt in p.get("post_tags", []) if pt.get("tags")]
    repo = p.get("github_repositories")

    # Count likes
    likes_count = 0
    is_liked = False
    is_saved = False
    try:
        likes_result = (
            supabase.table("likes")
            .select("id", count="exact")
            .eq("post_id", p["id"])
            .execute()
        )
        likes_count = likes_result.count or 0
    except Exception:
        pass

    if user_id:
        try:
            liked = (
                supabase.table("likes")
                .select("id")
                .eq("post_id", p["id"])
                .eq("user_id", user_id)
                .execute()
            )
            is_liked = bool(liked.data)
        except Exception:
            pass
        try:
            saved = (
                supabase.table("saved_posts")
                .select("id")
                .eq("post_id", p["id"])
                .eq("user_id", user_id)
                .execute()
            )
            is_saved = bool(saved.data)
        except Exception:
            pass

    return {
        **{k: v for k, v in p.items() if k not in ("post_tags", "github_repositories")},
        "tags": tags,
        "repo": repo,
        "likes_count": likes_count,
        "is_liked": is_liked,
        "is_saved": is_saved,
    }


@router.get("")
async def list_posts(
    limit: int = 12,
    offset: int = 0,
    authorization: Optional[str] = Header(None),
):
    """List published posts with pagination."""
    user = await get_optional_user(authorization)
    user_id = user["id"] if user else None

    try:
        result = (
            supabase.table("posts")
            .select(
                "*, github_repositories(id, repo_name, github_url), post_tags(tags(id, name, slug))"
            )
            .eq("status", "published")
            .order("published_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        posts = [_enrich_post(p, user_id) for p in result.data]

        # Get total count
        count_result = (
            supabase.table("posts")
            .select("id", count="exact")
            .eq("status", "published")
            .execute()
        )
        total = count_result.count or len(posts)

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

    try:
        result = (
            supabase.table("posts")
            .select(
                "*, github_repositories(id, repo_name, github_url), post_tags(tags(id, name, slug))"
            )
            .eq("slug", slug)
            .eq("status", "published")
            .single()
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Post not found")

        post = result.data

        # Increment views
        try:
            supabase.table("posts").update(
                {"views": (post.get("views") or 0) + 1}
            ).eq("id", post["id"]).execute()
            post["views"] = (post.get("views") or 0) + 1
        except Exception:
            pass

        return _enrich_post(post, user_id)
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

    try:
        # Check if already liked
        existing = (
            supabase.table("likes")
            .select("id")
            .eq("post_id", post_id)
            .eq("user_id", user_id)
            .execute()
        )

        if existing.data:
            # Unlike
            supabase.table("likes").delete().eq("post_id", post_id).eq("user_id", user_id).execute()
            liked = False
        else:
            # Like
            supabase.table("likes").insert(
                {"post_id": post_id, "user_id": user_id}
            ).execute()
            liked = True

        # Get updated count
        count_result = (
            supabase.table("likes")
            .select("id", count="exact")
            .eq("post_id", post_id)
            .execute()
        )
        likes_count = count_result.count or 0

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

    try:
        existing = (
            supabase.table("saved_posts")
            .select("id")
            .eq("post_id", post_id)
            .eq("user_id", user_id)
            .execute()
        )

        if existing.data:
            supabase.table("saved_posts").delete().eq("post_id", post_id).eq("user_id", user_id).execute()
            saved = False
        else:
            supabase.table("saved_posts").insert(
                {"post_id": post_id, "user_id": user_id}
            ).execute()
            saved = True

        return {"saved": saved}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
