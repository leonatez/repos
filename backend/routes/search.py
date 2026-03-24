from fastapi import APIRouter, HTTPException, Query, Header
from typing import Optional

from database import supabase_service as supabase
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
    # Use % wildcard with direct .ilike() calls to avoid PostgREST or() encoding
    # issues with Cloudflare (both % and * fail in or() URL filters via Supabase hosted API)
    keyword = f"%{q}%"

    try:
        # Search by title_en, title_vi, summary_en, summary_vi using separate ilike queries
        post_map: dict = {}
        select_fields = "*, github_repositories(id, repo_name, github_url), post_tags(tags(id, name, slug))"
        for field in ["title_en", "title_vi", "summary_en", "summary_vi"]:
            r = (
                supabase.table("posts")
                .select(select_fields)
                .eq("status", "published")
                .ilike(field, keyword)
                .order("published_at", desc=True)
                .execute()
            )
            for p in r.data:
                if p["id"] not in post_map:
                    post_map[p["id"]] = p

        # Also search by tag name
        tag_result = (
            supabase.table("tags")
            .select("id")
            .ilike("name", keyword)
            .execute()
        )
        matching_tag_ids = [t["id"] for t in tag_result.data]

        extra_posts = []

        if matching_tag_ids:
            pt_result = (
                supabase.table("post_tags")
                .select("post_id")
                .in_("tag_id", matching_tag_ids)
                .execute()
            )
            extra_post_ids = [
                pt["post_id"]
                for pt in pt_result.data
                if pt["post_id"] not in post_map
            ]

            if extra_post_ids:
                extra_result = (
                    supabase.table("posts")
                    .select(select_fields)
                    .eq("status", "published")
                    .in_("id", extra_post_ids)
                    .order("published_at", desc=True)
                    .execute()
                )
                extra_posts = extra_result.data

        all_posts = list(post_map.values()) + extra_posts

        posts = []
        for p in all_posts:
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
            "query": q,
            "items": posts,
            "total": len(posts),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
