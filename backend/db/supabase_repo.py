"""Supabase implementation of AbstractRepository. Uses supabase_service (service_role key) for all data ops."""
from datetime import datetime, timezone
from typing import Optional

from database import supabase_service as _sb
from db.base import AbstractRepository


def _enrich(p: dict, *, user_id: Optional[str] = None, likes_count: int = 0, is_liked: bool = False, is_saved: bool = False) -> dict:
    """Flatten post_tags / github_repositories joins and attach interaction fields."""
    tags = [pt["tags"] for pt in p.get("post_tags", []) if pt.get("tags")]
    repo = p.get("github_repositories")
    return {
        **{k: v for k, v in p.items() if k not in ("post_tags", "github_repositories")},
        "tags": tags,
        "repo": repo,
        "likes_count": likes_count,
        "is_liked": is_liked,
        "is_saved": is_saved,
    }


_POST_SELECT = "*, github_repositories(id, repo_name, github_url), post_tags(tags(id, name, slug))"


class SupabaseRepository(AbstractRepository):

    # ─── Posts ────────────────────────────────────────────────────────────────

    async def get_posts(self, limit: int, offset: int, status: Optional[str] = None) -> tuple[list, int]:
        q = _sb.table("posts").select(_POST_SELECT)
        if status:
            q = q.eq("status", status)
        result = q.order("published_at", desc=True).range(offset, offset + limit - 1).execute()
        count_q = _sb.table("posts").select("id", count="exact")
        if status:
            count_q = count_q.eq("status", status)
        total = (count_q.execute().count or 0)
        posts = [_enrich(p) for p in result.data]
        return posts, total

    async def get_post_by_slug(self, slug: str, status: Optional[str] = None) -> Optional[dict]:
        q = _sb.table("posts").select(_POST_SELECT).eq("slug", slug)
        if status:
            q = q.eq("status", status)
        result = q.single().execute()
        if not result.data:
            return None
        return _enrich(result.data)

    async def get_post_by_id(self, post_id: str) -> Optional[dict]:
        result = _sb.table("posts").select(_POST_SELECT).eq("id", post_id).single().execute()
        if not result.data:
            return None
        return _enrich(result.data)

    async def create_post(self, data: dict) -> dict:
        result = _sb.table("posts").insert(data).execute()
        return result.data[0]

    async def update_post(self, post_id: str, data: dict) -> Optional[dict]:
        result = _sb.table("posts").update(data).eq("id", post_id).execute()
        if not result.data:
            return None
        return result.data[0]

    async def increment_views(self, post_id: str) -> None:
        post = _sb.table("posts").select("views").eq("id", post_id).single().execute()
        if post.data:
            _sb.table("posts").update({"views": (post.data.get("views") or 0) + 1}).eq("id", post_id).execute()

    async def publish_post(self, post_id: str) -> Optional[dict]:
        result = _sb.table("posts").update({
            "status": "published",
            "published_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", post_id).execute()
        if not result.data:
            return None
        return result.data[0]

    # ─── Repositories ─────────────────────────────────────────────────────────

    async def get_or_create_repo(self, repo_name: str, github_url: str) -> str:
        existing = _sb.table("github_repositories").select("id").eq("github_url", github_url).execute()
        if existing.data:
            return existing.data[0]["id"]
        inserted = _sb.table("github_repositories").insert({"repo_name": repo_name, "github_url": github_url}).execute()
        return inserted.data[0]["id"]

    # ─── Tags ─────────────────────────────────────────────────────────────────

    async def get_all_tags(self) -> list:
        return _sb.table("tags").select("*").order("name").execute().data

    async def get_tag_by_slug(self, slug: str) -> Optional[dict]:
        result = _sb.table("tags").select("*").eq("slug", slug).single().execute()
        return result.data if result.data else None

    async def upsert_tag(self, name: str, slug: str) -> str:
        result = _sb.table("tags").upsert({"name": name, "slug": slug}, on_conflict="slug").execute()
        if result.data:
            return result.data[0]["id"]
        # Fallback: fetch existing
        existing = _sb.table("tags").select("id").eq("slug", slug).execute()
        return existing.data[0]["id"]

    async def get_posts_by_tag(self, tag_slug: str, limit: int, offset: int) -> tuple[list, int]:
        tag = await self.get_tag_by_slug(tag_slug)
        if not tag:
            return [], 0
        pt = _sb.table("post_tags").select("post_id").eq("tag_id", tag["id"]).execute()
        post_ids = [r["post_id"] for r in pt.data]
        if not post_ids:
            return [], 0
        result = (
            _sb.table("posts")
            .select(_POST_SELECT)
            .eq("status", "published")
            .in_("id", post_ids)
            .order("published_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        posts = [_enrich(p) for p in result.data]
        return posts, len(post_ids)

    async def get_related_posts_by_tags(self, tag_slugs: list, limit: int) -> list:
        if not tag_slugs:
            return []
        tag_rows = _sb.table("tags").select("id").in_("slug", tag_slugs).execute()
        tag_ids = [t["id"] for t in tag_rows.data]
        if not tag_ids:
            return []
        pt = _sb.table("post_tags").select("post_id").in_("tag_id", tag_ids).execute()
        post_ids = list({r["post_id"] for r in pt.data})
        if not post_ids:
            return []
        result = (
            _sb.table("posts")
            .select("id, title_en, slug, summary_en, post_tags(tags(name))")
            .eq("status", "published")
            .in_("id", post_ids)
            .order("published_at", desc=True)
            .limit(limit)
            .execute()
        )
        out = []
        for p in result.data:
            tags = [pt["tags"]["name"] for pt in p.get("post_tags", []) if pt.get("tags")]
            out.append({
                "title_en": p["title_en"],
                "slug": p["slug"],
                "summary_en": p.get("summary_en") or "",
                "tags": tags,
            })
        return out

    async def add_post_tags(self, post_id: str, tag_ids: list) -> None:
        if tag_ids:
            _sb.table("post_tags").insert([{"post_id": post_id, "tag_id": tid} for tid in tag_ids]).execute()

    async def remove_post_tags(self, post_id: str) -> None:
        _sb.table("post_tags").delete().eq("post_id", post_id).execute()

    async def get_tags_for_post(self, post_id: str) -> list:
        result = _sb.table("post_tags").select("tags(id, name, slug)").eq("post_id", post_id).execute()
        return [pt["tags"] for pt in result.data if pt.get("tags")]

    # ─── Likes ────────────────────────────────────────────────────────────────

    async def toggle_like(self, user_id: str, post_id: str) -> bool:
        existing = _sb.table("likes").select("id").eq("post_id", post_id).eq("user_id", user_id).execute()
        if existing.data:
            _sb.table("likes").delete().eq("post_id", post_id).eq("user_id", user_id).execute()
            return False
        _sb.table("likes").insert({"post_id": post_id, "user_id": user_id}).execute()
        return True

    async def get_likes_count(self, post_id: str) -> int:
        result = _sb.table("likes").select("id", count="exact").eq("post_id", post_id).execute()
        return result.count or 0

    async def is_liked_by_user(self, post_id: str, user_id: str) -> bool:
        result = _sb.table("likes").select("id").eq("post_id", post_id).eq("user_id", user_id).execute()
        return bool(result.data)

    # ─── Saved posts ──────────────────────────────────────────────────────────

    async def toggle_save(self, user_id: str, post_id: str) -> bool:
        existing = _sb.table("saved_posts").select("id").eq("post_id", post_id).eq("user_id", user_id).execute()
        if existing.data:
            _sb.table("saved_posts").delete().eq("post_id", post_id).eq("user_id", user_id).execute()
            return False
        _sb.table("saved_posts").insert({"post_id": post_id, "user_id": user_id}).execute()
        return True

    async def is_saved_by_user(self, post_id: str, user_id: str) -> bool:
        result = _sb.table("saved_posts").select("id").eq("post_id", post_id).eq("user_id", user_id).execute()
        return bool(result.data)

    async def get_saved_posts(self, user_id: str, limit: int, offset: int) -> tuple[list, int]:
        saved = (
            _sb.table("saved_posts")
            .select("post_id, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        post_ids = [s["post_id"] for s in saved.data]
        if not post_ids:
            return [], 0
        posts_result = (
            _sb.table("posts")
            .select(_POST_SELECT)
            .eq("status", "published")
            .in_("id", post_ids)
            .execute()
        )
        total = (_sb.table("saved_posts").select("id", count="exact").eq("user_id", user_id).execute().count or 0)
        posts = []
        for p in posts_result.data:
            likes_count = 0
            try:
                lc = _sb.table("likes").select("id", count="exact").eq("post_id", p["id"]).execute()
                likes_count = lc.count or 0
            except Exception:
                pass
            posts.append(_enrich(p, likes_count=likes_count, is_saved=True))
        return posts, total

    # ─── Comments ─────────────────────────────────────────────────────────────

    async def get_comments(self, post_id: str) -> list:
        result = (
            _sb.table("comments")
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

    async def create_comment(self, post_id: str, user_id: str, content: str) -> dict:
        result = _sb.table("comments").insert({
            "post_id": post_id,
            "user_id": user_id,
            "content": content,
            "status": "visible",
        }).execute()
        c = result.data[0]
        try:
            user_result = _sb.table("users").select("username, avatar_url").eq("id", user_id).single().execute()
            user_data = user_result.data or {}
        except Exception:
            user_data = {}
        return {**c, "username": user_data.get("username"), "avatar_url": user_data.get("avatar_url")}

    async def soft_delete_comment(self, comment_id: str) -> bool:
        result = _sb.table("comments").update({"status": "deleted"}).eq("id", comment_id).execute()
        return bool(result.data)

    # ─── Users ────────────────────────────────────────────────────────────────

    async def upsert_user(self, user_id: str, email: str, username: Optional[str], avatar_url: Optional[str], role: str = "user") -> dict:
        result = _sb.table("users").upsert({
            "id": user_id,
            "email": email,
            "username": username or email.split("@")[0],
            "avatar_url": avatar_url,
            "role": role,
        }, on_conflict="id").execute()
        return result.data[0]

    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        result = _sb.table("users").select("*").eq("id", user_id).single().execute()
        return result.data if result.data else None

    # ─── Search ───────────────────────────────────────────────────────────────

    async def search_posts(self, keyword: str, limit: int, offset: int) -> tuple[list, int]:
        kw = f"%{keyword}%"
        post_map: dict = {}
        for field in ["title_en", "title_vi", "summary_en", "summary_vi"]:
            r = (
                _sb.table("posts")
                .select(_POST_SELECT)
                .eq("status", "published")
                .ilike(field, kw)
                .order("published_at", desc=True)
                .execute()
            )
            for p in r.data:
                if p["id"] not in post_map:
                    post_map[p["id"]] = p

        tag_result = _sb.table("tags").select("id").ilike("name", kw).execute()
        matching_tag_ids = [t["id"] for t in tag_result.data]
        if matching_tag_ids:
            pt_result = _sb.table("post_tags").select("post_id").in_("tag_id", matching_tag_ids).execute()
            extra_post_ids = [pt["post_id"] for pt in pt_result.data if pt["post_id"] not in post_map]
            if extra_post_ids:
                extra = (
                    _sb.table("posts")
                    .select(_POST_SELECT)
                    .eq("status", "published")
                    .in_("id", extra_post_ids)
                    .order("published_at", desc=True)
                    .execute()
                )
                for p in extra.data:
                    post_map[p["id"]] = p

        all_posts = [_enrich(p) for p in post_map.values()]
        total = len(all_posts)
        return all_posts[offset:offset + limit], total
