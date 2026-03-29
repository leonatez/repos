"""
One-time migration script: sync all data from Supabase to local PostgreSQL.

Usage (run from backend/ directory):
    python -m scripts.sync_from_supabase

Requirements:
  - SUPABASE_URL, SUPABASE_SERVICE_KEY set in .env
  - INTERNAL_DB_URL set in .env (e.g. postgresql://repos_user:pass@localhost:5432/repos_db)
  - Local PostgreSQL running and schema applied:
      psql $INTERNAL_DB_URL -f ../database/local_schema.sql

Idempotent: uses INSERT ... ON CONFLICT DO NOTHING so it's safe to re-run.
"""
import asyncio
import json
import sys
import os

# Allow running from backend/ dir
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncpg
from supabase import create_client
from config import settings


def make_supabase():
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


async def migrate():
    if not settings.INTERNAL_DB_URL:
        print("ERROR: INTERNAL_DB_URL is not set in .env")
        sys.exit(1)

    sb = make_supabase()
    print(f"Connecting to local PostgreSQL: {settings.INTERNAL_DB_URL[:40]}...")
    pool = await asyncpg.create_pool(settings.INTERNAL_DB_URL)
    print("Connected.\n")

    # ── github_repositories ───────────────────────────────────────────────────
    print("Migrating github_repositories...")
    rows = sb.table("github_repositories").select("*").execute().data
    async with pool.acquire() as conn:
        for r in rows:
            await conn.execute(
                """INSERT INTO github_repositories (id, repo_name, github_url, created_at)
                   VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING""",
                _uuid(r["id"]), r["repo_name"], r["github_url"], _ts(r.get("created_at")),
            )
    print(f"  → {len(rows)} repos")

    # ── users ─────────────────────────────────────────────────────────────────
    print("Migrating users...")
    rows = sb.table("users").select("*").execute().data
    async with pool.acquire() as conn:
        for r in rows:
            await conn.execute(
                """INSERT INTO users (id, email, username, avatar_url, created_at, role)
                   VALUES ($1,$2,$3,$4,$5,$6) ON CONFLICT DO NOTHING""",
                _uuid(r["id"]), r["email"], r.get("username"), r.get("avatar_url"),
                _ts(r.get("created_at")), r.get("role", "user"),
            )
    print(f"  → {len(rows)} users")

    # ── posts ─────────────────────────────────────────────────────────────────
    print("Migrating posts...")
    rows = sb.table("posts").select("*").execute().data
    async with pool.acquire() as conn:
        for r in rows:
            gallery = r.get("gallery_images") or []
            if isinstance(gallery, str):
                try:
                    gallery = json.loads(gallery)
                except Exception:
                    gallery = []
            await conn.execute(
                """INSERT INTO posts
                   (id, title_vi, title_en, slug, summary_vi, summary_en,
                    content_markdown_vi, content_markdown_en, cover_image, gallery_images,
                    repo_id, status, created_at, published_at, views)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15)
                   ON CONFLICT DO NOTHING""",
                _uuid(r["id"]), r["title_vi"], r["title_en"], r["slug"],
                r.get("summary_vi"), r.get("summary_en"),
                r.get("content_markdown_vi"), r.get("content_markdown_en"),
                r.get("cover_image"), json.dumps(gallery),
                _uuid(r["repo_id"]) if r.get("repo_id") else None,
                r.get("status", "draft"),
                _ts(r.get("created_at")), _ts(r.get("published_at")),
                r.get("views", 0),
            )
    print(f"  → {len(rows)} posts")

    # ── tags ──────────────────────────────────────────────────────────────────
    print("Migrating tags...")
    rows = sb.table("tags").select("*").execute().data
    async with pool.acquire() as conn:
        for r in rows:
            await conn.execute(
                "INSERT INTO tags (id, name, slug) VALUES ($1,$2,$3) ON CONFLICT DO NOTHING",
                _uuid(r["id"]), r["name"], r["slug"],
            )
    print(f"  → {len(rows)} tags")

    # ── post_tags ─────────────────────────────────────────────────────────────
    print("Migrating post_tags...")
    rows = sb.table("post_tags").select("*").execute().data
    async with pool.acquire() as conn:
        for r in rows:
            await conn.execute(
                "INSERT INTO post_tags (post_id, tag_id) VALUES ($1,$2) ON CONFLICT DO NOTHING",
                _uuid(r["post_id"]), _uuid(r["tag_id"]),
            )
    print(f"  → {len(rows)} post_tags")

    # ── likes ─────────────────────────────────────────────────────────────────
    print("Migrating likes...")
    rows = sb.table("likes").select("*").execute().data
    async with pool.acquire() as conn:
        for r in rows:
            await conn.execute(
                "INSERT INTO likes (id, user_id, post_id, created_at) VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING",
                _uuid(r["id"]), _uuid(r["user_id"]), _uuid(r["post_id"]), _ts(r.get("created_at")),
            )
    print(f"  → {len(rows)} likes")

    # ── saved_posts ───────────────────────────────────────────────────────────
    print("Migrating saved_posts...")
    rows = sb.table("saved_posts").select("*").execute().data
    async with pool.acquire() as conn:
        for r in rows:
            await conn.execute(
                "INSERT INTO saved_posts (id, user_id, post_id, created_at) VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING",
                _uuid(r["id"]), _uuid(r["user_id"]), _uuid(r["post_id"]), _ts(r.get("created_at")),
            )
    print(f"  → {len(rows)} saved_posts")

    # ── comments ──────────────────────────────────────────────────────────────
    print("Migrating comments...")
    rows = sb.table("comments").select("*").execute().data
    async with pool.acquire() as conn:
        for r in rows:
            await conn.execute(
                """INSERT INTO comments (id, post_id, user_id, content, created_at, status)
                   VALUES ($1,$2,$3,$4,$5,$6) ON CONFLICT DO NOTHING""",
                _uuid(r["id"]), _uuid(r["post_id"]), _uuid(r["user_id"]),
                r["content"], _ts(r.get("created_at")), r.get("status", "visible"),
            )
    print(f"  → {len(rows)} comments")

    await pool.close()
    print("\nMigration complete.")


import uuid as _uuid_mod
from datetime import datetime


def _uuid(val):
    if val is None:
        return None
    return _uuid_mod.UUID(str(val))


def _ts(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except Exception:
        return None


if __name__ == "__main__":
    asyncio.run(migrate())
