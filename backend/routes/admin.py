import asyncio
import logging
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from datetime import datetime, timezone
import uuid

from database import supabase_service as supabase
from auth import get_admin_user
from models.schemas import (
    AdminSubmitRequest,
    PostUpdate,
    PipelineStatusResponse,
)
from services.ai_pipeline import extract_github_urls, analyze_and_generate_article
from services.github_service import fetch_repo_info
from utils import generate_unique_slug, slugify_tag

logger = logging.getLogger("admin")

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def _process_single_url(github_url: str) -> dict:
    """
    Full pipeline for one GitHub URL:
      1. Fetch repo info
      2. Generate bilingual article via Gemini
      3. Save repo, post, tags to DB
    Returns the created post dict, or raises on failure.
    """
    # Fetch repo info
    repo_info = await fetch_repo_info(github_url)

    # Generate article via AI
    article = await analyze_and_generate_article(repo_info)

    # Save or reuse github_repositories row
    existing_repo = (
        supabase.table("github_repositories")
        .select("id")
        .eq("github_url", repo_info["url"])
        .execute()
    )
    if existing_repo.data:
        repo_id = existing_repo.data[0]["id"]
    else:
        repo_insert = (
            supabase.table("github_repositories")
            .insert({"repo_name": repo_info["repo_name"], "github_url": repo_info["url"]})
            .execute()
        )
        repo_id = repo_insert.data[0]["id"]

    # Create draft post
    slug = generate_unique_slug(article["title_en"])
    post_result = supabase.table("posts").insert({
        "title_vi": article["title_vi"],
        "title_en": article["title_en"],
        "slug": slug,
        "summary_vi": article.get("summary_vi"),
        "summary_en": article.get("summary_en"),
        "content_markdown_vi": article.get("content_markdown_vi"),
        "content_markdown_en": article.get("content_markdown_en"),
        "repo_id": repo_id,
        "status": "draft",
    }).execute()
    post = post_result.data[0]
    post_id = post["id"]

    # Save tags
    tag_ids = []
    for tag_name in article.get("tags", []):
        tag_slug = slugify_tag(tag_name)
        if not tag_slug:
            continue
        try:
            tag_result = (
                supabase.table("tags")
                .upsert({"name": tag_name.lower(), "slug": tag_slug}, on_conflict="slug")
                .execute()
            )
            tag_ids.append(tag_result.data[0]["id"])
        except Exception:
            try:
                existing = supabase.table("tags").select("id").eq("slug", tag_slug).execute()
                if existing.data:
                    tag_ids.append(existing.data[0]["id"])
            except Exception:
                pass

    if tag_ids:
        try:
            supabase.table("post_tags").insert(
                [{"post_id": post_id, "tag_id": tid} for tid in tag_ids]
            ).execute()
        except Exception:
            pass

    # Fetch tags for response
    tags = []
    try:
        pt_result = (
            supabase.table("post_tags")
            .select("tags(id, name, slug)")
            .eq("post_id", post_id)
            .execute()
        )
        tags = [pt["tags"] for pt in pt_result.data if pt.get("tags")]
    except Exception:
        pass

    return {
        **post,
        "repo": {"id": repo_id, "repo_name": repo_info["repo_name"], "github_url": repo_info["url"]},
        "tags": tags,
        "likes_count": 0,
        "is_liked": False,
        "is_saved": False,
    }


@router.post("/submit")
async def submit_social_text(
    request: AdminSubmitRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Admin submits text containing one or more GitHub URLs.
    All URLs are processed concurrently — each gets a full AI-generated bilingual article saved as a draft.
    Returns { posts: [...], errors: [{ url, detail }] }.
    """
    await get_admin_user(authorization)

    # Extract all GitHub URLs from the submitted text
    github_urls = extract_github_urls(request.text)
    if not github_urls:
        raise HTTPException(
            status_code=422,
            detail="Could not find any GitHub repository URLs in the provided text.",
        )

    logger.info(f"Processing {len(github_urls)} URL(s): {github_urls}")

    # Process all URLs concurrently; capture per-URL errors without failing the whole batch
    async def safe_process(url: str):
        try:
            return {"url": url, "post": await _process_single_url(url), "error": None}
        except Exception as e:
            logger.error(f"Failed to process {url}: {e}", exc_info=True)
            return {"url": url, "post": None, "error": str(e)}

    results = await asyncio.gather(*[safe_process(url) for url in github_urls])

    posts = [r["post"] for r in results if r["post"] is not None]
    errors = [{"url": r["url"], "detail": r["error"]} for r in results if r["error"] is not None]

    if not posts and errors:
        # All failed — return 500 with details
        raise HTTPException(
            status_code=500,
            detail=f"All {len(errors)} URL(s) failed. First error: {errors[0]['detail']}",
        )

    return {
        "posts": posts,
        "total": len(posts),
        "errors": errors,
    }


@router.get("/posts")
async def list_all_posts(
    limit: int = 20,
    offset: int = 0,
    authorization: Optional[str] = Header(None),
):
    """List all posts (draft + published) for admin."""
    await get_admin_user(authorization)

    try:
        result = (
            supabase.table("posts")
            .select(
                "*, github_repositories(id, repo_name, github_url), post_tags(tags(id, name, slug))"
            )
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        posts = []
        for p in result.data:
            tags = [pt["tags"] for pt in p.get("post_tags", []) if pt.get("tags")]
            repo = p.get("github_repositories")
            posts.append({
                **{k: v for k, v in p.items() if k not in ("post_tags", "github_repositories")},
                "tags": tags,
                "repo": repo,
                "likes_count": 0,
                "is_liked": False,
                "is_saved": False,
            })

        return {"items": posts, "total": len(posts), "limit": limit, "offset": offset}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/posts/{post_id}")
async def update_post(
    post_id: str,
    update: PostUpdate,
    authorization: Optional[str] = Header(None),
):
    """Edit a post (any field)."""
    await get_admin_user(authorization)

    update_data = update.model_dump(exclude_none=True)
    tags = update_data.pop("tags", None)

    if not update_data and tags is None:
        raise HTTPException(status_code=422, detail="No update data provided")

    try:
        if update_data:
            result = (
                supabase.table("posts")
                .update(update_data)
                .eq("id", post_id)
                .execute()
            )
            if not result.data:
                raise HTTPException(status_code=404, detail="Post not found")

        # Update tags if provided
        if tags is not None:
            # Remove existing tags
            supabase.table("post_tags").delete().eq("post_id", post_id).execute()

            for tag_name in tags:
                tag_slug = slugify_tag(tag_name)
                if not tag_slug:
                    continue
                try:
                    tag_result = (
                        supabase.table("tags")
                        .upsert(
                            {"name": tag_name.lower(), "slug": tag_slug},
                            on_conflict="slug",
                        )
                        .execute()
                    )
                    tag_id = tag_result.data[0]["id"]
                    supabase.table("post_tags").insert(
                        {"post_id": post_id, "tag_id": tag_id}
                    ).execute()
                except Exception:
                    pass

        # Fetch updated post
        post_result = (
            supabase.table("posts")
            .select(
                "*, github_repositories(id, repo_name, github_url), post_tags(tags(id, name, slug))"
            )
            .eq("id", post_id)
            .single()
            .execute()
        )
        p = post_result.data
        tags_list = [pt["tags"] for pt in p.get("post_tags", []) if pt.get("tags")]
        return {
            **{k: v for k, v in p.items() if k not in ("post_tags", "github_repositories")},
            "tags": tags_list,
            "repo": p.get("github_repositories"),
            "likes_count": 0,
            "is_liked": False,
            "is_saved": False,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/posts/{post_id}/publish")
async def publish_post(
    post_id: str,
    authorization: Optional[str] = Header(None),
):
    """Publish a draft post."""
    await get_admin_user(authorization)

    try:
        result = (
            supabase.table("posts")
            .update(
                {
                    "status": "published",
                    "published_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            .eq("id", post_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Post not found")

        p = result.data[0]
        return {**p, "tags": [], "repo": None, "likes_count": 0, "is_liked": False, "is_saved": False}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    authorization: Optional[str] = Header(None),
):
    """Soft-delete a comment (set status to 'deleted')."""
    await get_admin_user(authorization)

    try:
        result = (
            supabase.table("comments")
            .update({"status": "deleted"})
            .eq("id", comment_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Comment not found")
        return {"message": "Comment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
