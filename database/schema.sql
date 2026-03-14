-- ============================================================
-- AI GitHub Repo Digest — Database Schema
-- Run this in your Supabase SQL editor
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── Users ────────────────────────────────────────────────────────────────────
-- Extends Supabase Auth users table with app-level profile data
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    username TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    role TEXT DEFAULT 'user' CHECK (role IN ('admin', 'user'))
);

-- Auto-create user profile when a new auth user is created
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, username, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1)),
        NEW.raw_user_meta_data->>'avatar_url'
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ─── GitHub Repositories ──────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS github_repositories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    repo_name TEXT NOT NULL,
    github_url TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─── Posts ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title_vi TEXT NOT NULL,
    title_en TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    summary_vi TEXT,
    summary_en TEXT,
    content_markdown_vi TEXT,
    content_markdown_en TEXT,
    cover_image TEXT,
    repo_id UUID REFERENCES github_repositories(id) ON DELETE SET NULL,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'published')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    published_at TIMESTAMPTZ,
    views INTEGER DEFAULT 0
);

-- Index for faster slug lookups
CREATE INDEX IF NOT EXISTS idx_posts_slug ON posts(slug);
CREATE INDEX IF NOT EXISTS idx_posts_status ON posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_published_at ON posts(published_at DESC);

-- ─── Tags ─────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE
);

CREATE INDEX IF NOT EXISTS idx_tags_slug ON tags(slug);

-- ─── Post Tags (junction) ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS post_tags (
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);

CREATE INDEX IF NOT EXISTS idx_post_tags_post_id ON post_tags(post_id);
CREATE INDEX IF NOT EXISTS idx_post_tags_tag_id ON post_tags(tag_id);

-- ─── Likes ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS likes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, post_id)
);

CREATE INDEX IF NOT EXISTS idx_likes_post_id ON likes(post_id);
CREATE INDEX IF NOT EXISTS idx_likes_user_id ON likes(user_id);

-- ─── Saved Posts ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS saved_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, post_id)
);

CREATE INDEX IF NOT EXISTS idx_saved_posts_user_id ON saved_posts(user_id);

-- ─── Comments ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id UUID REFERENCES posts(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'visible' CHECK (status IN ('visible', 'deleted'))
);

CREATE INDEX IF NOT EXISTS idx_comments_post_id ON comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_user_id ON comments(user_id);

-- ─── Row Level Security (RLS) ─────────────────────────────────────────────────

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE github_repositories ENABLE ROW LEVEL SECURITY;
ALTER TABLE posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE post_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE likes ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_posts ENABLE ROW LEVEL SECURITY;
ALTER TABLE comments ENABLE ROW LEVEL SECURITY;

-- Users: anyone can read, users can update their own profile
CREATE POLICY "Users are publicly readable" ON users FOR SELECT USING (true);
CREATE POLICY "Users can update own profile" ON users FOR UPDATE USING (auth.uid() = id);

-- GitHub repositories: publicly readable
CREATE POLICY "Repos are publicly readable" ON github_repositories FOR SELECT USING (true);
CREATE POLICY "Service role can manage repos" ON github_repositories FOR ALL USING (true);

-- Posts: published posts are publicly readable; all posts readable by service role
CREATE POLICY "Published posts are publicly readable" ON posts FOR SELECT USING (status = 'published');
CREATE POLICY "Service role can manage posts" ON posts FOR ALL USING (true);

-- Tags: publicly readable
CREATE POLICY "Tags are publicly readable" ON tags FOR SELECT USING (true);
CREATE POLICY "Service role can manage tags" ON tags FOR ALL USING (true);

-- Post tags: publicly readable
CREATE POLICY "Post tags are publicly readable" ON post_tags FOR SELECT USING (true);
CREATE POLICY "Service role can manage post tags" ON post_tags FOR ALL USING (true);

-- Likes: users can manage their own likes
CREATE POLICY "Likes are publicly readable" ON likes FOR SELECT USING (true);
CREATE POLICY "Users can manage own likes" ON likes FOR ALL USING (auth.uid() = user_id);

-- Saved posts: users can only see their own saved posts
CREATE POLICY "Users can manage own saved posts" ON saved_posts FOR ALL USING (auth.uid() = user_id);

-- Comments: visible comments are publicly readable; users can create/manage own
CREATE POLICY "Visible comments are publicly readable" ON comments FOR SELECT USING (status = 'visible');
CREATE POLICY "Authenticated users can create comments" ON comments FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own comments" ON comments FOR UPDATE USING (auth.uid() = user_id);

-- ─── Helper function to promote user to admin ─────────────────────────────────
-- Run manually: SELECT promote_to_admin('user@example.com');
CREATE OR REPLACE FUNCTION promote_to_admin(user_email TEXT)
RETURNS void AS $$
BEGIN
    UPDATE users SET role = 'admin'
    WHERE email = user_email;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
