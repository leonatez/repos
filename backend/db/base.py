from abc import ABC, abstractmethod
from typing import Optional


class AbstractRepository(ABC):
    """Abstract base class defining all data operations. Implementations: SupabaseRepository, PostgresRepository."""

    # ─── Posts ────────────────────────────────────────────────────────────────

    @abstractmethod
    async def get_posts(self, limit: int, offset: int, status: Optional[str] = None) -> tuple[list, int]:
        """Return (items, total) for posts, optionally filtered by status."""
        ...

    @abstractmethod
    async def get_post_by_slug(self, slug: str, status: Optional[str] = None) -> Optional[dict]:
        """Return a single post by slug. Returns None if not found."""
        ...

    @abstractmethod
    async def get_post_by_id(self, post_id: str) -> Optional[dict]:
        """Return a single post by id. Returns None if not found."""
        ...

    @abstractmethod
    async def create_post(self, data: dict) -> dict:
        """Insert a new post. Returns the created row."""
        ...

    @abstractmethod
    async def update_post(self, post_id: str, data: dict) -> Optional[dict]:
        """Update a post. Returns the updated row, or None if not found."""
        ...

    @abstractmethod
    async def delete_post(self, post_id: str) -> bool:
        """Permanently delete a post and its post_tags rows. Returns True if found and deleted."""
        ...

    @abstractmethod
    async def increment_views(self, post_id: str) -> None:
        """Atomically increment views counter on a post."""
        ...

    @abstractmethod
    async def publish_post(self, post_id: str) -> Optional[dict]:
        """Set status=published and published_at=now(). Returns updated row."""
        ...

    # ─── Repositories ─────────────────────────────────────────────────────────

    @abstractmethod
    async def get_or_create_repo(self, repo_name: str, github_url: str) -> str:
        """Return repo_id (UUID string), creating the row if it doesn't exist."""
        ...

    # ─── Tags ─────────────────────────────────────────────────────────────────

    @abstractmethod
    async def get_all_tags(self) -> list:
        """Return all tags ordered by name."""
        ...

    @abstractmethod
    async def get_tag_by_slug(self, slug: str) -> Optional[dict]:
        """Return a single tag by slug. Returns None if not found."""
        ...

    @abstractmethod
    async def upsert_tag(self, name: str, slug: str) -> str:
        """Insert or update a tag. Returns tag_id (UUID string)."""
        ...

    @abstractmethod
    async def get_posts_by_tag(self, tag_slug: str, limit: int, offset: int) -> tuple[list, int]:
        """Return (items, total) of published posts with the given tag slug."""
        ...

    @abstractmethod
    async def get_related_posts_by_tags(self, tag_slugs: list, limit: int) -> list:
        """Return up to `limit` published posts that share any of the given tag slugs.
        Each item contains only: title_en, slug, summary_en, tags (list of tag names).
        Used by the AI pipeline to inject related-article context before generation."""
        ...

    @abstractmethod
    async def add_post_tags(self, post_id: str, tag_ids: list) -> None:
        """Create post_tags rows linking post_id to each tag_id."""
        ...

    @abstractmethod
    async def remove_post_tags(self, post_id: str) -> None:
        """Delete all post_tags rows for a post."""
        ...

    @abstractmethod
    async def get_tags_for_post(self, post_id: str) -> list:
        """Return list of tag dicts for a post."""
        ...

    # ─── Likes ────────────────────────────────────────────────────────────────

    @abstractmethod
    async def toggle_like(self, user_id: str, post_id: str) -> bool:
        """Toggle like. Returns True if now liked, False if unliked."""
        ...

    @abstractmethod
    async def get_likes_count(self, post_id: str) -> int:
        """Return the number of likes for a post."""
        ...

    @abstractmethod
    async def is_liked_by_user(self, post_id: str, user_id: str) -> bool:
        """Return True if user has liked the post."""
        ...

    # ─── Saved posts ──────────────────────────────────────────────────────────

    @abstractmethod
    async def toggle_save(self, user_id: str, post_id: str) -> bool:
        """Toggle save. Returns True if now saved, False if unsaved."""
        ...

    @abstractmethod
    async def is_saved_by_user(self, post_id: str, user_id: str) -> bool:
        """Return True if user has saved the post."""
        ...

    @abstractmethod
    async def get_saved_posts(self, user_id: str, limit: int, offset: int) -> tuple[list, int]:
        """Return (items, total) of posts saved by user."""
        ...

    # ─── Comments ─────────────────────────────────────────────────────────────

    @abstractmethod
    async def get_comments(self, post_id: str) -> list:
        """Return visible comments for a post (oldest first), with username/avatar_url."""
        ...

    @abstractmethod
    async def create_comment(self, post_id: str, user_id: str, content: str) -> dict:
        """Insert a new comment. Returns the created row with username/avatar_url."""
        ...

    @abstractmethod
    async def soft_delete_comment(self, comment_id: str) -> bool:
        """Set comment status=deleted. Returns True if found and updated."""
        ...

    # ─── Users ────────────────────────────────────────────────────────────────

    @abstractmethod
    async def upsert_user(self, user_id: str, email: str, username: Optional[str], avatar_url: Optional[str], role: str = "user") -> dict:
        """Insert or update a user row. Returns the upserted row."""
        ...

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Return a user by id. Returns None if not found."""
        ...

    # ─── Search ───────────────────────────────────────────────────────────────

    @abstractmethod
    async def search_posts(self, keyword: str, limit: int, offset: int) -> tuple[list, int]:
        """Full-text ILIKE search across titles, summaries, and tags. Returns (items, total)."""
        ...
