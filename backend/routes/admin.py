import asyncio
import logging
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from datetime import datetime, timezone

from db import get_db
from auth import get_admin_user
from models.schemas import (
    AdminSubmitRequest,
    PostUpdate,
)
from services.ai_pipeline import extract_github_urls, analyze_and_generate_article, generate_article_from_content, extract_candidate_tags
from services.github_service import fetch_repo_info
from utils import generate_unique_slug, slugify_tag

logger = logging.getLogger("admin")

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def _process_single_url(github_url: str) -> dict:
    """
    Full pipeline for one GitHub URL:
      1. Fetch repo info (including gallery_images)
      2. Generate bilingual article via Gemini
      3. Save repo, post, tags to DB
    Returns the created post dict, or raises on failure.
    """
    db = get_db()

    # Fetch repo info
    repo_info = await fetch_repo_info(github_url)

    # Find related published posts by repo topics + language before generating
    related_posts = []
    try:
        candidate_slugs = [t.lower().replace(" ", "-") for t in repo_info.get("topics", [])]
        if repo_info.get("language"):
            candidate_slugs.append(repo_info["language"].lower())
        if candidate_slugs:
            related_posts = await db.get_related_posts_by_tags(candidate_slugs, limit=5)
    except Exception as e:
        logger.warning(f"Related posts lookup failed (continuing without): {e}")

    # Generate article via AI
    article = await analyze_and_generate_article(repo_info, related_posts=related_posts)

    # Save or reuse github_repositories row
    repo_id = await db.get_or_create_repo(repo_info["repo_name"], repo_info["url"])

    # Create draft post
    slug = generate_unique_slug(article["title_en"])
    post = await db.create_post({
        "title_vi": article["title_vi"],
        "title_en": article["title_en"],
        "slug": slug,
        "summary_vi": article.get("summary_vi"),
        "summary_en": article.get("summary_en"),
        "content_markdown_vi": article.get("content_markdown_vi"),
        "content_markdown_en": article.get("content_markdown_en"),
        "gallery_images": repo_info.get("gallery_images", []),
        "repo_id": repo_id,
        "status": "draft",
    })
    post_id = str(post["id"])

    # Save tags
    tag_ids = []
    for tag_name in article.get("tags", []):
        tag_slug = slugify_tag(tag_name)
        if not tag_slug:
            continue
        try:
            tag_id = await db.upsert_tag(tag_name.lower(), tag_slug)
            tag_ids.append(tag_id)
        except Exception:
            try:
                tag = await db.get_tag_by_slug(tag_slug)
                if tag:
                    tag_ids.append(str(tag["id"]))
            except Exception:
                pass

    if tag_ids:
        try:
            await db.add_post_tags(post_id, tag_ids)
        except Exception:
            pass

    tags = await db.get_tags_for_post(post_id)

    return {
        **post,
        "repo": {"id": repo_id, "repo_name": repo_info["repo_name"], "github_url": repo_info["url"]},
        "tags": tags,
        "likes_count": 0,
        "is_liked": False,
        "is_saved": False,
    }


async def _process_free_content(text: str) -> dict:
    """
    Pipeline for text that contains no GitHub URL:
      1. AI researches the topic on the internet
      2. Generates a bilingual article combining the research with the original content
      3. Save post and tags to DB (no repo link)
    Returns the created post dict.
    """
    db = get_db()

    # Extract candidate tags from text, then find related posts before generating
    related_posts = []
    try:
        candidate_slugs = await extract_candidate_tags(text)
        if candidate_slugs:
            related_posts = await db.get_related_posts_by_tags(candidate_slugs, limit=5)
    except Exception as e:
        logger.warning(f"Related posts lookup failed (continuing without): {e}")

    article = await generate_article_from_content(text, related_posts=related_posts)

    slug = generate_unique_slug(article["title_en"])
    post = await db.create_post({
        "title_vi": article["title_vi"],
        "title_en": article["title_en"],
        "slug": slug,
        "summary_vi": article.get("summary_vi"),
        "summary_en": article.get("summary_en"),
        "content_markdown_vi": article.get("content_markdown_vi"),
        "content_markdown_en": article.get("content_markdown_en"),
        "gallery_images": [],
        "repo_id": None,
        "status": "draft",
    })
    post_id = str(post["id"])

    tag_ids = []
    for tag_name in article.get("tags", []):
        tag_slug = slugify_tag(tag_name)
        if not tag_slug:
            continue
        try:
            tag_id = await db.upsert_tag(tag_name.lower(), tag_slug)
            tag_ids.append(tag_id)
        except Exception:
            try:
                tag = await db.get_tag_by_slug(tag_slug)
                if tag:
                    tag_ids.append(str(tag["id"]))
            except Exception:
                pass

    if tag_ids:
        try:
            await db.add_post_tags(post_id, tag_ids)
        except Exception:
            pass

    tags = await db.get_tags_for_post(post_id)

    return {
        **post,
        "repo": None,
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

    github_urls = extract_github_urls(request.text)

    if github_urls:
        # ── GitHub pipeline: one article per repo ──────────────────────────────
        logger.info(f"Processing {len(github_urls)} GitHub URL(s): {github_urls}")

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
            raise HTTPException(
                status_code=500,
                detail=f"All {len(errors)} URL(s) failed. First error: {errors[0]['detail']}",
            )
    else:
        # ── Free-content pipeline: AI researches topic and composes article ─────
        logger.info("No GitHub URLs found — composing article from content via AI research")
        try:
            post = await _process_free_content(request.text)
            posts = [post]
            errors = []
        except Exception as e:
            logger.error(f"Failed to generate article from content: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

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
    db = get_db()

    try:
        posts, total = await db.get_posts(limit=limit, offset=offset)
        return {"items": posts, "total": total, "limit": limit, "offset": offset}
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
    db = get_db()

    update_data = update.model_dump(exclude_none=True)
    tags = update_data.pop("tags", None)

    if not update_data and tags is None:
        raise HTTPException(status_code=422, detail="No update data provided")

    try:
        if update_data:
            updated = await db.update_post(post_id, update_data)
            if updated is None:
                raise HTTPException(status_code=404, detail="Post not found")

        if tags is not None:
            await db.remove_post_tags(post_id)
            tag_ids = []
            for tag_name in tags:
                tag_slug = slugify_tag(tag_name)
                if not tag_slug:
                    continue
                try:
                    tag_id = await db.upsert_tag(tag_name.lower(), tag_slug)
                    tag_ids.append(tag_id)
                except Exception:
                    pass
            if tag_ids:
                await db.add_post_tags(post_id, tag_ids)

        post = await db.get_post_by_id(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        post["tags"] = await db.get_tags_for_post(post_id)
        return post
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
    db = get_db()

    try:
        post = await db.publish_post(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        post["tags"] = []
        post["repo"] = None
        post["likes_count"] = 0
        post["is_liked"] = False
        post["is_saved"] = False
        return post
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
    db = get_db()

    try:
        found = await db.soft_delete_comment(comment_id)
        if not found:
            raise HTTPException(status_code=404, detail="Comment not found")
        return {"message": "Comment deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
