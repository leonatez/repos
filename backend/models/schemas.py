from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# ─── Tag Schemas ───────────────────────────────────────────────────────────────

class TagResponse(BaseModel):
    id: UUID
    name: str
    slug: str


# ─── Post Schemas ──────────────────────────────────────────────────────────────

class PostCreate(BaseModel):
    title_vi: str
    title_en: str
    summary_vi: Optional[str] = None
    summary_en: Optional[str] = None
    content_markdown_vi: Optional[str] = None
    content_markdown_en: Optional[str] = None
    cover_image: Optional[str] = None
    status: str = "draft"
    tags: Optional[List[str]] = []


class PostUpdate(BaseModel):
    title_vi: Optional[str] = None
    title_en: Optional[str] = None
    slug: Optional[str] = None
    summary_vi: Optional[str] = None
    summary_en: Optional[str] = None
    content_markdown_vi: Optional[str] = None
    content_markdown_en: Optional[str] = None
    cover_image: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None


class RepoInfo(BaseModel):
    id: Optional[UUID] = None
    repo_name: str
    github_url: str


class PostSummary(BaseModel):
    id: UUID
    title_vi: str
    title_en: str
    slug: str
    summary_vi: Optional[str] = None
    summary_en: Optional[str] = None
    cover_image: Optional[str] = None
    status: str
    created_at: datetime
    published_at: Optional[datetime] = None
    views: int = 0
    tags: List[TagResponse] = []
    repo: Optional[RepoInfo] = None
    likes_count: int = 0
    is_liked: bool = False
    is_saved: bool = False


class PostResponse(BaseModel):
    id: UUID
    title_vi: str
    title_en: str
    slug: str
    summary_vi: Optional[str] = None
    summary_en: Optional[str] = None
    content_markdown_vi: Optional[str] = None
    content_markdown_en: Optional[str] = None
    cover_image: Optional[str] = None
    status: str
    created_at: datetime
    published_at: Optional[datetime] = None
    views: int = 0
    tags: List[TagResponse] = []
    repo: Optional[RepoInfo] = None
    likes_count: int = 0
    is_liked: bool = False
    is_saved: bool = False


# ─── Comment Schemas ───────────────────────────────────────────────────────────

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class CommentResponse(BaseModel):
    id: UUID
    post_id: UUID
    user_id: UUID
    content: str
    created_at: datetime
    status: str
    username: Optional[str] = None
    avatar_url: Optional[str] = None


# ─── Search Schemas ────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    q: str = Field(..., min_length=1, max_length=200)


# ─── Admin Schemas ─────────────────────────────────────────────────────────────

class AdminSubmitRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Social media text containing a GitHub URL")


# ─── Like / Save Schemas ───────────────────────────────────────────────────────

class LikeRequest(BaseModel):
    post_id: UUID


class SaveRequest(BaseModel):
    post_id: UUID


# ─── Pipeline Status ───────────────────────────────────────────────────────────

class PipelineStatusResponse(BaseModel):
    status: str
    message: str
    post_id: Optional[UUID] = None
    slug: Optional[str] = None


# ─── Pagination ────────────────────────────────────────────────────────────────

class PaginatedPosts(BaseModel):
    items: List[PostSummary]
    total: int
    limit: int
    offset: int
