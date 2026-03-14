# AI GitHub Repo Digest — Project Documentation

## Table of Contents

1. [Product Overview](#product-overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Database Schema](#database-schema)
5. [API Endpoints](#api-endpoints)
6. [Frontend Pages & Components](#frontend-pages--components)
7. [Configuration & Environment](#configuration--environment)
8. [Key Data Flows](#key-data-flows)
9. [Running the Project](#running-the-project)

---

## Product Overview

**AI GitHub Repo Digest** is a bilingual (Vietnamese / English) tech blog platform that automatically converts GitHub repositories into curated articles using Google Gemini AI. Admins submit a GitHub URL (or social media text containing one), Gemini analyzes the repository and generates a full article in both Vietnamese and English, and the article is published for public readers.

---

## Features

### Reader Features
- Browse published articles in a responsive card grid with featured post
- Toggle between Vietnamese and English for every article
- Like articles (requires login)
- Save / bookmark articles for later (requires login)
- Comment on articles (requires login)
- Filter articles by tag
- Full-text search across titles, summaries, and tags
- View saved (bookmarked) articles in a personal Favorites page

### Authentication
- Sign up with email + password + username
- Sign in / Sign out
- Session persistence via Supabase JWT stored in localStorage
- Admin role gating (Settings icon and admin routes hidden for non-admins)

### Admin Features
- Submit text containing **one or more** GitHub URLs to generate articles in bulk
- All URLs extracted automatically (regex + Gemini fallback); each repo processed concurrently
- Review and edit generated draft articles (title, summary, content, tags)
- Publish drafts to make them publicly visible
- View all posts (draft + published) in a management dashboard with stats
- Delete comments (soft-delete)

### Article Generation Pipeline
1. Admin pastes text (tweet, HN post, HackerNews thread, etc.) containing **one or more** GitHub URLs
2. All GitHub URLs are extracted — supports both `github.com/owner/repo` and `github.com/owner/` formats; fbclid/tracking params stripped automatically
3. All URLs are processed **concurrently** — each repo is fetched and analyzed in parallel
4. GitHub API fetches repository metadata (name, description, language, stars, forks, topics, license, README) per repo
5. Gemini generates a bilingual article per repo: titles, summaries, full markdown content (800+ words each language), tags
6. Each article saved as a **draft** — admin reviews and publishes each one independently
7. Partial failures handled gracefully: if one URL fails, the others still complete

### Thumbnails
- GitHub OpenGraph images are generated dynamically: `https://opengraph.githubassets.com/{YYYYMMDD}/{owner}/{repo}`
- Date-based URL provides automatic cache-busting — no image storage needed

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                           Browser (React + Vite)                     │
│                                                                      │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────────────┐  │
│  │  Auth       │  │  Article Pages   │  │  Admin Pages          │  │
│  │  (Supabase  │  │  (Home, Article, │  │  (AdminPanel,         │  │
│  │   Auth JS)  │  │   Tag, Search,   │  │   NewPost, EditPost)  │  │
│  └──────┬──────┘  │   Favorites)     │  └──────────┬────────────┘  │
│         │         └────────┬─────────┘             │               │
│         │                  │  axios (+ JWT Bearer) │               │
└─────────┼──────────────────┼───────────────────────┼───────────────┘
          │                  │                       │
          │ Supabase Auth    │  REST /api/*          │
          ▼                  ▼                       │
┌──────────────────┐  ┌──────────────────────────────┼────────────┐
│  Supabase        │  │  FastAPI Backend (Python)     │            │
│  Auth Service    │  │                               │            │
│  (JWT issue &    │  │  routes/                      │            │
│   verification)  │  │  ├── posts.py                 │            │
└──────────────────┘  │  ├── tags.py                  │            │
          │           │  ├── comments.py              │            │
          │           │  ├── search.py                │            │
          │           │  ├── favorites.py             │            │
          │           │  └── admin.py ◄───────────────┘            │
          │           │                                             │
          │           │  services/                                  │
          │           │  ├── ai_pipeline.py ──────► Google Gemini  │
          │           │  ├── github_service.py ───► GitHub API     │
          │           │  └── thumbnail.py                          │
          │           │                                             │
          │           │  auth.py (JWT verify + admin check)        │
          │           └────────────────┬────────────────────────────┘
          │                            │
          │ SQL (service_role key)     │ SQL (service_role key)
          ▼                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    Supabase (PostgreSQL)                              │
│                                                                      │
│  users  │  posts  │  github_repositories  │  tags  │  post_tags    │
│  likes  │  saved_posts  │  comments                                 │
└──────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend framework | React 18 + TypeScript |
| Build tool | Vite 5 |
| Styling | Tailwind CSS 3 (custom design tokens) |
| Routing | React Router v6 |
| HTTP client | Axios (with JWT interceptor) |
| Auth | Supabase Auth (email/password) |
| Backend framework | FastAPI (Python 3.11+) |
| ASGI server | Uvicorn |
| AI | Google Gemini (`gemini-3.1-flash-lite-preview`) |
| GitHub data | PyGitHub (GitHub REST API v3) |
| Database | Supabase (PostgreSQL) |
| Database client | supabase-py (v2) |
| Validation | Pydantic v2 |

### Key Design Decisions

- **Two Supabase clients on the backend** — `supabase` (anon key) is used only to verify JWTs; `supabase_service` (service_role key) is used for all database reads/writes, bypassing Row Level Security.
- **Synchronous JWT cache** — `authToken.ts` stores the current JWT in a module-level variable. The Axios interceptor reads it synchronously to avoid async hangs when Supabase network is slow.
- **Bilingual content** — Every post stores separate Vietnamese and English fields for title, summary, and markdown content. Language selection is a frontend-only concern.
- **No image uploads** — Thumbnails are generated on-the-fly from GitHub's OpenGraph CDN; no storage bucket needed.
- **Draft → Publish workflow** — Articles are always created as `draft` first, allowing admin review before public visibility.

---

## Database Schema

### Tables

#### `users`
Mirrors `auth.users`; auto-populated by a trigger on signup.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | Same as `auth.users.id` |
| `email` | TEXT NOT NULL | |
| `username` | TEXT | |
| `avatar_url` | TEXT | |
| `created_at` | TIMESTAMPTZ | |
| `role` | TEXT | `'user'` (default) or `'admin'` |

#### `github_repositories`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `repo_name` | TEXT NOT NULL | |
| `github_url` | TEXT UNIQUE NOT NULL | Canonical repo URL |
| `created_at` | TIMESTAMPTZ | |

#### `posts`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `title_vi` | TEXT NOT NULL | Vietnamese title |
| `title_en` | TEXT NOT NULL | English title |
| `slug` | TEXT UNIQUE NOT NULL | URL-safe identifier |
| `summary_vi` | TEXT | 2–3 sentence summary (VI) |
| `summary_en` | TEXT | 2–3 sentence summary (EN) |
| `content_markdown_vi` | TEXT | Full article (VI, markdown) |
| `content_markdown_en` | TEXT | Full article (EN, markdown) |
| `cover_image` | TEXT | Fallback image URL |
| `repo_id` | UUID FK → `github_repositories` | |
| `status` | TEXT | `'draft'` or `'published'` |
| `created_at` | TIMESTAMPTZ | |
| `published_at` | TIMESTAMPTZ | Set when published |
| `views` | INTEGER | Incremented on article load |

#### `tags`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `name` | TEXT UNIQUE NOT NULL | Display name |
| `slug` | TEXT UNIQUE NOT NULL | URL-safe identifier |

#### `post_tags` (junction)

| Column | Type | Notes |
|--------|------|-------|
| `post_id` | UUID FK → `posts` CASCADE | |
| `tag_id` | UUID FK → `tags` CASCADE | |

#### `likes`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `user_id` | UUID FK → `users` CASCADE | |
| `post_id` | UUID FK → `posts` CASCADE | |
| `created_at` | TIMESTAMPTZ | |
| — | UNIQUE(user_id, post_id) | |

#### `saved_posts`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `user_id` | UUID FK → `users` CASCADE | |
| `post_id` | UUID FK → `posts` CASCADE | |
| `created_at` | TIMESTAMPTZ | |
| — | UNIQUE(user_id, post_id) | |

#### `comments`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `post_id` | UUID FK → `posts` CASCADE | |
| `user_id` | UUID FK → `users` CASCADE | |
| `content` | TEXT NOT NULL | |
| `created_at` | TIMESTAMPTZ | |
| `status` | TEXT | `'visible'` or `'deleted'` |

### Row Level Security (RLS) Summary

| Table | Anon SELECT | Auth SELECT | Auth INSERT/UPDATE | Admin / Service Role |
|-------|-------------|-------------|--------------------|-----------------------|
| `users` | ✅ all rows | ✅ all rows | own row only | full access |
| `posts` | published only | published only | — | full access |
| `tags` | ✅ | ✅ | — | full access |
| `post_tags` | ✅ | ✅ | — | full access |
| `likes` | — | own rows | own rows | full access |
| `saved_posts` | — | own rows | own rows | full access |
| `comments` | visible only | visible only | own rows | full access |

> The backend always uses `supabase_service` (service_role key) which bypasses RLS entirely.

---

## API Endpoints

**Base URL:** `http://localhost:8000`

All endpoints are prefixed with `/api`.

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/` | — | API info |
| GET | `/health` | — | Health check |

### Posts — `/api/posts`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/posts` | Optional | List published posts. Query: `limit` (default 12), `offset` (default 0) |
| GET | `/api/posts/{slug}` | Optional | Get a single published post by slug. Increments `views`. Returns post with tags, likes count, and (if authed) whether user liked/saved it |
| POST | `/api/posts/{id}/like` | Required | Toggle like on a post. Returns `{ liked: bool, likes_count: int }` |
| POST | `/api/posts/{id}/save` | Required | Toggle save (bookmark) on a post. Returns `{ saved: bool }` |

### Comments — `/api/posts/{postId}/comments`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/posts/{postId}/comments` | Optional | List all visible comments for a post |
| POST | `/api/posts/{postId}/comments` | Required | Create a comment. Body: `{ "content": "string" }`. Returns comment with username/avatar |

### Tags — `/api/tags`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/tags` | — | List all tags ordered by name |
| GET | `/api/tags/{slug}/posts` | Optional | Get published posts for a tag. Query: `limit`, `offset` |

### Search — `/api/search`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/search` | Optional | Search posts. Query: `q` (required), `limit` (default 12, max 50), `offset`. Searches titles, summaries, and tag names (case-insensitive) |

### Favorites — `/api/favorites`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/favorites` | Required | Get the authenticated user's saved posts. Query: `limit`, `offset` |

### Admin — `/api/admin` (Admin JWT required for all)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/admin/submit` | Admin | Submit text containing one or more GitHub URLs. All URLs processed concurrently. Body: `{ "text": "string" }`. Returns `{ posts: [...], total: N, errors: [{ url, detail }] }` |
| GET | `/api/admin/posts` | Admin | List all posts (draft + published). Query: `limit` (default 20), `offset` |
| PUT | `/api/admin/posts/{id}` | Admin | Update a post's fields (title, content, tags, status, etc.). Body: partial post object |
| POST | `/api/admin/posts/{id}/publish` | Admin | Publish a draft post. Sets `status='published'` and `published_at=now()` |
| DELETE | `/api/admin/comments/{id}` | Admin | Soft-delete a comment (sets `status='deleted'`) |

### Authentication (Supabase — not proxied through backend)

Auth is handled directly by the Supabase JS SDK on the frontend:

| Action | SDK call |
|--------|---------|
| Sign up | `supabase.auth.signUp({ email, password, options: { data: { username } } })` |
| Sign in | `supabase.auth.signInWithPassword({ email, password })` |
| Sign out | `supabase.auth.signOut()` |
| Get session | `supabase.auth.getSession()` |
| Listen for changes | `supabase.auth.onAuthStateChange(callback)` |

---

## Frontend Pages & Components

### Pages

| Route | Component | Auth Required | Description |
|-------|-----------|---------------|-------------|
| `/` | `Home.tsx` | No | Featured article at top, paginated article grid, tag sidebar, "Load More" |
| `/login` | `LoginPage.tsx` | No (redirects if authed) | Sign in / Sign up toggle form |
| `/articles/:slug` | `Article.tsx` | No (some actions need auth) | Full article view with markdown, language toggle, likes, save, comment section |
| `/tag/:slug` | `TagPage.tsx` | No | All published articles for a given tag |
| `/search?q=` | `SearchPage.tsx` | No | Search results with query display |
| `/favorites` | `FavoritesPage.tsx` | Yes | User's bookmarked articles |
| `/admin` | `AdminPanel.tsx` | Admin | Dashboard: post table with stats, publish/edit actions |
| `/admin/new` | `NewPost.tsx` | Admin | Multi-step article generation form |
| `/admin/posts/:id/edit` | `EditPost.tsx` | Admin | Edit draft or published post |

### Reusable Components

| Component | Description |
|-----------|-------------|
| `Navbar.tsx` | Sticky top nav — logo, search bar, language toggle, auth buttons, admin settings icon |
| `ArticleCard.tsx` | Article preview card (featured large card or grid card) with thumbnail, title, summary, tags, stats |
| `CommentSection.tsx` | Comments list + inline create form |
| `TagSidebar.tsx` | Trending tags list (linked to tag pages) |
| `LanguageToggle.tsx` | VI / EN language switcher button |
| `MarkdownRenderer.tsx` | Renders markdown content with `react-markdown` + `remark-gfm` (tables, code blocks, etc.) |

### Contexts

| Context | Purpose |
|---------|---------|
| `AuthContext.tsx` | Manages Supabase session, user profile (incl. role), `isAdmin` flag, login/signup/logout functions |
| `LanguageContext.tsx` | Stores current language preference (`'vi'` or `'en'`), persisted in localStorage |

### Auth Token Flow

```
Supabase Auth → onAuthStateChange → setAuthToken(session.access_token)
                                           │
                                           ▼
                                    authToken.ts (module cache)
                                           │
                                           ▼ (synchronous read)
                               axios interceptor → Authorization: Bearer <token>
                                           │
                                           ▼
                                   FastAPI backend
```

---

## Configuration & Environment

### Backend — `backend/.env`

```env
GEMINI_API_KEY=your_gemini_api_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
GITHUB_TOKEN=optional_github_personal_access_token
```

- `SUPABASE_KEY` — anon/public key; used **only** to verify user JWTs
- `SUPABASE_SERVICE_KEY` — service_role key (long JWT, starts with `eyJ`); used for all DB reads/writes
- `GITHUB_TOKEN` — optional; increases GitHub API rate limit from 60 to 5000 req/hr

### Frontend — `frontend/.env`

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### CORS Origins (backend)

The backend allows requests from:
- `http://localhost:5173`
- `http://localhost:3000`
- `http://127.0.0.1:5173`
- `http://127.0.0.1:3000`

---

## Key Data Flows

### 1. Article Generation (Admin Submit)

```
Admin UI (NewPost.tsx)
  │ POST /api/admin/submit { text: "..." }
  ▼
admin.py — extract_github_urls(text)
  │ Regex scans for all github.com/owner/repo and github.com/owner/ URLs
  │ Falls back to Gemini only if regex finds nothing (shortened links, etc.)
  │ returns ["https://github.com/owner/repo-1", "https://github.com/org/repo-2", ...]
  ▼
asyncio.gather — all URLs processed concurrently
  │
  ├─ _process_single_url("...repo-1")          ├─ _process_single_url("...repo-2")
  │    github_service: fetch metadata + README  │    github_service: fetch metadata + README
  │    ai_pipeline: Gemini generates article    │    ai_pipeline: Gemini generates article
  │    DB: UPSERT repo, INSERT post+tags        │    DB: UPSERT repo, INSERT post+tags
  │    → post dict                              │    → post dict (or error captured)
  ▼
Response: { posts: [...], total: N, errors: [{url, detail}] }
  └── Admin sees one card per generated draft, reviews and publishes each independently
```

### 2. Article Reading

```
Reader visits /articles/:slug
  │ GET /api/posts/{slug}
  ▼
posts.py
  ├── Fetch post from DB (published only)
  ├── Increment views counter
  ├── Fetch associated tags
  ├── Count likes
  └── If authenticated: check if user liked/saved
  │
  ▼
Article.tsx renders title/content in selected language (VI or EN)
```

### 3. Authentication & Admin Check

```
User logs in → Supabase issues JWT
  │
  ▼ AuthContext.tsx
  ├── setAuthToken(session.access_token)   ← module-level cache
  └── fetchUserProfile(user)
       │ SELECT * FROM users WHERE id = user.id
       ▼
       setUser({ ..., role: 'admin' | 'user' })

isAdmin = user?.role === 'admin'
  │
  ├── Navbar shows ⚙ Settings icon
  └── /admin routes become accessible

Admin API call
  │ axios attaches Bearer token (from authToken.ts cache)
  ▼
auth.py — get_admin_user()
  ├── Verify JWT with supabase.auth.get_user(token)
  └── Check role in users table via supabase_service
```

---

## Running the Project

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Supabase project with the schema from `database/schema.sql` applied
- Google Gemini API key

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env         # Fill in your keys
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
# Create frontend/.env with VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY
npm run dev
```

App runs at `http://localhost:5173`. API calls proxy to `http://localhost:8000`.

### Making Yourself Admin

After creating your account, run this SQL in Supabase Dashboard → SQL Editor:

```sql
UPDATE public.users SET role = 'admin' WHERE email = 'your@email.com';
```

Then refresh the page — the ⚙ Settings icon will appear in the navbar.

### Database Setup

Apply the schema to your Supabase project:

```bash
# In Supabase Dashboard → SQL Editor, paste the contents of:
database/schema.sql
```

Also ensure these GRANTs are in place (required for frontend auth queries):

```sql
GRANT SELECT ON TABLE public.users TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
```
