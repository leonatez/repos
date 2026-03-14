// ─── Tag ──────────────────────────────────────────────────────────────────────
export interface Tag {
  id: string
  name: string
  slug: string
}

// ─── Repository ───────────────────────────────────────────────────────────────
export interface RepoInfo {
  id?: string
  repo_name: string
  github_url: string
}

// ─── Post ─────────────────────────────────────────────────────────────────────
export interface PostSummary {
  id: string
  title_vi: string
  title_en: string
  slug: string
  summary_vi?: string
  summary_en?: string
  cover_image?: string
  status: 'draft' | 'published'
  created_at: string
  published_at?: string
  views: number
  tags: Tag[]
  repo?: RepoInfo
  likes_count: number
  is_liked: boolean
  is_saved: boolean
}

export interface Post extends PostSummary {
  content_markdown_vi?: string
  content_markdown_en?: string
}

// ─── Comment ──────────────────────────────────────────────────────────────────
export interface Comment {
  id: string
  post_id: string
  user_id: string
  content: string
  created_at: string
  status: 'visible' | 'deleted'
  username?: string
  avatar_url?: string
}

// ─── Auth ─────────────────────────────────────────────────────────────────────
export interface User {
  id: string
  email: string
  username?: string
  avatar_url?: string
  role?: 'admin' | 'user'
}

// ─── API Response Types ───────────────────────────────────────────────────────
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  limit: number
  offset: number
}

export interface SearchResponse extends PaginatedResponse<PostSummary> {
  query: string
}

export interface TagPostsResponse extends PaginatedResponse<PostSummary> {
  tag: Tag
}

// ─── Language ─────────────────────────────────────────────────────────────────
export type Language = 'vi' | 'en'

// ─── Admin ────────────────────────────────────────────────────────────────────
export interface AdminSubmitRequest {
  text: string
}

export interface AdminSubmitResponse {
  posts: Post[]
  total: number
  errors: { url: string; detail: string }[]
}

export interface PostUpdate {
  title_vi?: string
  title_en?: string
  slug?: string
  summary_vi?: string
  summary_en?: string
  content_markdown_vi?: string
  content_markdown_en?: string
  cover_image?: string
  status?: 'draft' | 'published'
  tags?: string[]
}
