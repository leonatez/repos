"""Local PostgreSQL implementation of AbstractRepository using asyncpg."""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

import asyncpg

from db.base import AbstractRepository


def _row_to_dict(record) -> dict:
    """Convert an asyncpg Record to a plain dict, serializing JSONB arrays."""
    if record is None:
        return None
    d = dict(record)
    # asyncpg returns JSONB as Python objects already; convert datetimes to ISO strings
    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


def _enrich(p: dict, tags: list, repo: Optional[dict] = None,
            likes_count: int = 0, is_liked: bool = False, is_saved: bool = False) -> dict:
    return {
        **p,
        "tags": tags,
        "repo": repo,
        "likes_count": likes_count,
        "is_liked": is_liked,
        "is_saved": is_saved,
    }


class PostgresRepository(AbstractRepository):
    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    # ─── Internal helpers ─────────────────────────────────────────────────────

    async def _get_tags_for_post(self, conn, post_id: str) -> list:
        rows = await conn.fetch(
            "SELECT t.id, t.name, t.slug FROM tags t "
            "JOIN post_tags pt ON pt.tag_id = t.id WHERE pt.post_id = $1",
            post_id,
        )
        return [{"id": str(r["id"]), "name": r["name"], "slug": r["slug"]} for r in rows]

    async def _get_repo_for_post(self, conn, repo_id) -> Optional[dict]:
        if not repo_id:
            return None
        row = await conn.fetchrow(
            "SELECT id, repo_name, github_url FROM github_repositories WHERE id = $1", repo_id
        )
        return {"id": str(row["id"]), "repo_name": row["repo_name"], "github_url": row["github_url"]} if row else None

    async def _enrich_post(self, conn, row: dict, likes_count: int = 0, is_liked: bool = False, is_saved: bool = False) -> dict:
        tags = await self._get_tags_for_post(conn, row["id"])
        repo = await self._get_repo_for_post(conn, row.get("repo_id"))
        post = {k: v for k, v in row.items() if k not in ("repo_id",)}
        # Ensure gallery_images is a list
        gi = post.get("gallery_images")
        if isinstance(gi, str):
            try:
                post["gallery_images"] = json.loads(gi)
            except Exception:
                post["gallery_images"] = []
        elif gi is None:
            post["gallery_images"] = []
        return _enrich(post, tags, repo, likes_count, is_liked, is_saved)

    # ─── Posts ────────────────────────────────────────────────────────────────

    async def get_posts(self, limit: int, offset: int, status: Optional[str] = None) -> tuple[list, int]:
        async with self._pool.acquire() as conn:
            if status:
                rows = await conn.fetch(
                    "SELECT * FROM posts WHERE status = $1 ORDER BY published_at DESC NULLS LAST LIMIT $2 OFFSET $3",
                    status, limit, offset,
                )
                total = await conn.fetchval("SELECT COUNT(*) FROM posts WHERE status = $1", status)
            else:
                rows = await conn.fetch(
                    "SELECT * FROM posts ORDER BY published_at DESC NULLS LAST LIMIT $1 OFFSET $2",
                    limit, offset,
                )
                total = await conn.fetchval("SELECT COUNT(*) FROM posts")
            posts = []
            for row in rows:
                p = _row_to_dict(row)
                posts.append(await self._enrich_post(conn, p))
            return posts, total or 0

    async def get_post_by_slug(self, slug: str, status: Optional[str] = None) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            if status:
                row = await conn.fetchrow(
                    "SELECT * FROM posts WHERE slug = $1 AND status = $2", slug, status
                )
            else:
                row = await conn.fetchrow("SELECT * FROM posts WHERE slug = $1", slug)
            if not row:
                return None
            return await self._enrich_post(conn, _row_to_dict(row))

    async def get_post_by_id(self, post_id: str) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM posts WHERE id = $1", uuid.UUID(post_id))
            if not row:
                return None
            return await self._enrich_post(conn, _row_to_dict(row))

    async def create_post(self, data: dict) -> dict:
        async with self._pool.acquire() as conn:
            gallery = data.get("gallery_images", [])
            row = await conn.fetchrow(
                """INSERT INTO posts (id, title_vi, title_en, slug, summary_vi, summary_en,
                   content_markdown_vi, content_markdown_en, cover_image, gallery_images, repo_id, status)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) RETURNING *""",
                uuid.uuid4(),
                data["title_vi"], data["title_en"], data["slug"],
                data.get("summary_vi"), data.get("summary_en"),
                data.get("content_markdown_vi"), data.get("content_markdown_en"),
                data.get("cover_image"),
                json.dumps(gallery),
                uuid.UUID(data["repo_id"]) if data.get("repo_id") else None,
                data.get("status", "draft"),
            )
            return _row_to_dict(row)

    async def update_post(self, post_id: str, data: dict) -> Optional[dict]:
        if not data:
            return await self.get_post_by_id(post_id)
        set_clauses = []
        values = []
        i = 1
        for k, v in data.items():
            if k == "gallery_images":
                v = json.dumps(v)
            set_clauses.append(f"{k} = ${i}")
            values.append(v)
            i += 1
        values.append(uuid.UUID(post_id))
        sql = f"UPDATE posts SET {', '.join(set_clauses)} WHERE id = ${i} RETURNING *"
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(sql, *values)
            return _row_to_dict(row) if row else None

    async def increment_views(self, post_id: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                "UPDATE posts SET views = views + 1 WHERE id = $1",
                uuid.UUID(post_id),
            )

    async def publish_post(self, post_id: str) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "UPDATE posts SET status = 'published', published_at = $1 WHERE id = $2 RETURNING *",
                datetime.now(timezone.utc), uuid.UUID(post_id),
            )
            return _row_to_dict(row) if row else None

    # ─── Repositories ─────────────────────────────────────────────────────────

    async def get_or_create_repo(self, repo_name: str, github_url: str) -> str:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM github_repositories WHERE github_url = $1", github_url
            )
            if row:
                return str(row["id"])
            new_id = uuid.uuid4()
            await conn.execute(
                "INSERT INTO github_repositories (id, repo_name, github_url) VALUES ($1,$2,$3)",
                new_id, repo_name, github_url,
            )
            return str(new_id)

    # ─── Tags ─────────────────────────────────────────────────────────────────

    async def get_all_tags(self) -> list:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM tags ORDER BY name")
            return [{"id": str(r["id"]), "name": r["name"], "slug": r["slug"]} for r in rows]

    async def get_tag_by_slug(self, slug: str) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM tags WHERE slug = $1", slug)
            return {"id": str(row["id"]), "name": row["name"], "slug": row["slug"]} if row else None

    async def upsert_tag(self, name: str, slug: str) -> str:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO tags (id, name, slug) VALUES ($1,$2,$3) ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name RETURNING id",
                uuid.uuid4(), name, slug,
            )
            return str(row["id"])

    async def get_posts_by_tag(self, tag_slug: str, limit: int, offset: int) -> tuple[list, int]:
        tag = await self.get_tag_by_slug(tag_slug)
        if not tag:
            return [], 0
        async with self._pool.acquire() as conn:
            post_ids = await conn.fetch(
                "SELECT post_id FROM post_tags WHERE tag_id = $1", uuid.UUID(tag["id"])
            )
            ids = [r["post_id"] for r in post_ids]
            if not ids:
                return [], 0
            rows = await conn.fetch(
                "SELECT * FROM posts WHERE status = 'published' AND id = ANY($1) "
                "ORDER BY published_at DESC NULLS LAST LIMIT $2 OFFSET $3",
                ids, limit, offset,
            )
            posts = [await self._enrich_post(conn, _row_to_dict(r)) for r in rows]
            return posts, len(ids)

    async def add_post_tags(self, post_id: str, tag_ids: list) -> None:
        if not tag_ids:
            return
        async with self._pool.acquire() as conn:
            await conn.executemany(
                "INSERT INTO post_tags (post_id, tag_id) VALUES ($1,$2) ON CONFLICT DO NOTHING",
                [(uuid.UUID(post_id), uuid.UUID(tid)) for tid in tag_ids],
            )

    async def remove_post_tags(self, post_id: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM post_tags WHERE post_id = $1", uuid.UUID(post_id))

    async def get_tags_for_post(self, post_id: str) -> list:
        async with self._pool.acquire() as conn:
            return await self._get_tags_for_post(conn, post_id)

    # ─── Likes ────────────────────────────────────────────────────────────────

    async def toggle_like(self, user_id: str, post_id: str) -> bool:
        async with self._pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT id FROM likes WHERE post_id = $1 AND user_id = $2",
                uuid.UUID(post_id), uuid.UUID(user_id),
            )
            if existing:
                await conn.execute(
                    "DELETE FROM likes WHERE post_id = $1 AND user_id = $2",
                    uuid.UUID(post_id), uuid.UUID(user_id),
                )
                return False
            await conn.execute(
                "INSERT INTO likes (id, post_id, user_id) VALUES ($1,$2,$3)",
                uuid.uuid4(), uuid.UUID(post_id), uuid.UUID(user_id),
            )
            return True

    async def get_likes_count(self, post_id: str) -> int:
        async with self._pool.acquire() as conn:
            return await conn.fetchval("SELECT COUNT(*) FROM likes WHERE post_id = $1", uuid.UUID(post_id)) or 0

    async def is_liked_by_user(self, post_id: str, user_id: str) -> bool:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM likes WHERE post_id = $1 AND user_id = $2",
                uuid.UUID(post_id), uuid.UUID(user_id),
            )
            return row is not None

    # ─── Saved posts ──────────────────────────────────────────────────────────

    async def toggle_save(self, user_id: str, post_id: str) -> bool:
        async with self._pool.acquire() as conn:
            existing = await conn.fetchrow(
                "SELECT id FROM saved_posts WHERE post_id = $1 AND user_id = $2",
                uuid.UUID(post_id), uuid.UUID(user_id),
            )
            if existing:
                await conn.execute(
                    "DELETE FROM saved_posts WHERE post_id = $1 AND user_id = $2",
                    uuid.UUID(post_id), uuid.UUID(user_id),
                )
                return False
            await conn.execute(
                "INSERT INTO saved_posts (id, post_id, user_id) VALUES ($1,$2,$3)",
                uuid.uuid4(), uuid.UUID(post_id), uuid.UUID(user_id),
            )
            return True

    async def is_saved_by_user(self, post_id: str, user_id: str) -> bool:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id FROM saved_posts WHERE post_id = $1 AND user_id = $2",
                uuid.UUID(post_id), uuid.UUID(user_id),
            )
            return row is not None

    async def get_saved_posts(self, user_id: str, limit: int, offset: int) -> tuple[list, int]:
        async with self._pool.acquire() as conn:
            saved = await conn.fetch(
                "SELECT post_id FROM saved_posts WHERE user_id = $1 ORDER BY created_at DESC LIMIT $2 OFFSET $3",
                uuid.UUID(user_id), limit, offset,
            )
            ids = [r["post_id"] for r in saved]
            if not ids:
                total = await conn.fetchval("SELECT COUNT(*) FROM saved_posts WHERE user_id = $1", uuid.UUID(user_id))
                return [], total or 0
            rows = await conn.fetch(
                "SELECT * FROM posts WHERE status = 'published' AND id = ANY($1)", ids
            )
            total = await conn.fetchval("SELECT COUNT(*) FROM saved_posts WHERE user_id = $1", uuid.UUID(user_id))
            posts = []
            for row in rows:
                p = _row_to_dict(row)
                lc = await conn.fetchval("SELECT COUNT(*) FROM likes WHERE post_id = $1", row["id"]) or 0
                posts.append(await self._enrich_post(conn, p, likes_count=lc, is_saved=True))
            return posts, total or 0

    # ─── Comments ─────────────────────────────────────────────────────────────

    async def get_comments(self, post_id: str) -> list:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT c.*, u.username, u.avatar_url FROM comments c "
                "LEFT JOIN users u ON u.id = c.user_id "
                "WHERE c.post_id = $1 AND c.status = 'visible' ORDER BY c.created_at ASC",
                uuid.UUID(post_id),
            )
            return [_row_to_dict(r) for r in rows]

    async def create_comment(self, post_id: str, user_id: str, content: str) -> dict:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "INSERT INTO comments (id, post_id, user_id, content, status) VALUES ($1,$2,$3,$4,'visible') RETURNING *",
                uuid.uuid4(), uuid.UUID(post_id), uuid.UUID(user_id), content,
            )
            c = _row_to_dict(row)
            user_row = await conn.fetchrow("SELECT username, avatar_url FROM users WHERE id = $1", uuid.UUID(user_id))
            if user_row:
                c["username"] = user_row["username"]
                c["avatar_url"] = user_row["avatar_url"]
            return c

    async def soft_delete_comment(self, comment_id: str) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE comments SET status = 'deleted' WHERE id = $1", uuid.UUID(comment_id)
            )
            return result != "UPDATE 0"

    # ─── Users ────────────────────────────────────────────────────────────────

    async def upsert_user(self, user_id: str, email: str, username: Optional[str], avatar_url: Optional[str], role: str = "user") -> dict:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """INSERT INTO users (id, email, username, avatar_url, role)
                   VALUES ($1,$2,$3,$4,$5)
                   ON CONFLICT (id) DO UPDATE SET email = EXCLUDED.email,
                       username = COALESCE(EXCLUDED.username, users.username),
                       avatar_url = COALESCE(EXCLUDED.avatar_url, users.avatar_url)
                   RETURNING *""",
                uuid.UUID(user_id), email, username or email.split("@")[0], avatar_url, role,
            )
            return _row_to_dict(row)

    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", uuid.UUID(user_id))
            return _row_to_dict(row) if row else None

    # ─── Search ───────────────────────────────────────────────────────────────

    async def search_posts(self, keyword: str, limit: int, offset: int) -> tuple[list, int]:
        kw = f"%{keyword}%"
        async with self._pool.acquire() as conn:
            post_map: dict = {}
            for field in ["title_en", "title_vi", "summary_en", "summary_vi"]:
                rows = await conn.fetch(
                    f"SELECT * FROM posts WHERE status = 'published' AND {field} ILIKE $1 ORDER BY published_at DESC NULLS LAST",
                    kw,
                )
                for row in rows:
                    p = _row_to_dict(row)
                    if p["id"] not in post_map:
                        post_map[p["id"]] = p

            tag_rows = await conn.fetch("SELECT id FROM tags WHERE name ILIKE $1", kw)
            tag_ids = [r["id"] for r in tag_rows]
            if tag_ids:
                pt_rows = await conn.fetch(
                    "SELECT post_id FROM post_tags WHERE tag_id = ANY($1)", tag_ids
                )
                extra_ids = [r["post_id"] for r in pt_rows if str(r["post_id"]) not in {str(k) for k in post_map}]
                if extra_ids:
                    extra_rows = await conn.fetch(
                        "SELECT * FROM posts WHERE status = 'published' AND id = ANY($1) ORDER BY published_at DESC NULLS LAST",
                        extra_ids,
                    )
                    for row in extra_rows:
                        p = _row_to_dict(row)
                        if p["id"] not in post_map:
                            post_map[p["id"]] = p

            all_posts = []
            for p in post_map.values():
                all_posts.append(await self._enrich_post(conn, p))
            total = len(all_posts)
            return all_posts[offset:offset + limit], total
