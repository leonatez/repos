import { useEffect, useState } from 'react'
import { useParams, Link, Navigate } from 'react-router-dom'
import {
  Heart, Bookmark, Eye, Calendar, ExternalLink,
  Tag as TagIcon, ArrowLeft, Github, Star
} from 'lucide-react'
import { postsApi } from '../api/client'
import { Post } from '../types'
import { useAuth } from '../contexts/AuthContext'
import { useLanguage } from '../contexts/LanguageContext'
import { generateThumbnail } from '../lib/thumbnail'
import LanguageToggle from '../components/LanguageToggle'
import MarkdownRenderer from '../components/MarkdownRenderer'
import CommentSection from '../components/CommentSection'

export default function Article() {
  const { slug } = useParams<{ slug: string }>()
  const { user } = useAuth()
  const { language } = useLanguage()
  const [post, setPost] = useState<Post | null>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [liking, setLiking] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!slug) return
    setLoading(true)
    postsApi.getBySlug(slug)
      .then((res) => setPost(res.data))
      .catch((err) => {
        if (err.response?.status === 404) setNotFound(true)
      })
      .finally(() => setLoading(false))
  }, [slug])

  const handleLike = async () => {
    if (!user || !post || liking) return
    setLiking(true)
    try {
      const res = await postsApi.toggleLike(post.id)
      setPost((prev) =>
        prev
          ? {
              ...prev,
              is_liked: res.data.liked,
              likes_count: res.data.likes_count,
            }
          : prev
      )
    } catch (err) {
      console.error(err)
    } finally {
      setLiking(false)
    }
  }

  const handleSave = async () => {
    if (!user || !post || saving) return
    setSaving(true)
    try {
      const res = await postsApi.toggleSave(post.id)
      setPost((prev) =>
        prev ? { ...prev, is_saved: res.data.saved } : prev
      )
    } catch (err) {
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  if (notFound) return <Navigate to="/" replace />

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-primary">
        <div className="max-w-4xl mx-auto px-4 py-8 space-y-6 animate-pulse">
          <div className="h-64 bg-bg-secondary rounded-2xl" />
          <div className="h-8 bg-bg-secondary rounded w-3/4" />
          <div className="h-4 bg-bg-secondary rounded w-1/2" />
          <div className="space-y-3">
            {Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="h-4 bg-bg-secondary rounded" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!post) return null

  const title = language === 'vi' ? post.title_vi : post.title_en
  const summary = language === 'vi' ? post.summary_vi : post.summary_en
  const content = language === 'vi' ? post.content_markdown_vi : post.content_markdown_en
  const thumbnail = post.repo?.github_url
    ? generateThumbnail(post.repo.github_url)
    : post.cover_image

  const publishedDate = post.published_at
    ? new Date(post.published_at).toLocaleDateString('en-US', {
        year: 'numeric', month: 'long', day: 'numeric',
      })
    : new Date(post.created_at).toLocaleDateString('en-US', {
        year: 'numeric', month: 'long', day: 'numeric',
      })

  return (
    <main className="min-h-screen bg-bg-primary">
      {/* Hero thumbnail */}
      {thumbnail && (
        <div className="relative h-64 sm:h-80 lg:h-96 overflow-hidden">
          <img
            src={thumbnail}
            alt={title}
            className="w-full h-full object-cover"
            onError={(e) => {
              const img = e.target as HTMLImageElement
              img.style.display = 'none'
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-b from-bg-primary/30 via-bg-primary/20 to-bg-primary" />
        </div>
      )}

      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        {/* Back link */}
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-text-muted hover:text-accent mb-8 text-sm transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>

        <article>
          {/* Tags */}
          {post.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-4">
              {post.tags.map((tag) => (
                <Link
                  key={tag.id}
                  to={`/tag/${tag.slug}`}
                  className="flex items-center gap-1 px-3 py-1 bg-accent/10 text-accent text-xs rounded-full border border-accent/20 hover:bg-accent/20 transition-colors"
                >
                  <TagIcon className="w-3 h-3" />
                  {tag.name}
                </Link>
              ))}
            </div>
          )}

          {/* Title */}
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-text-primary mb-4 leading-tight">
            {title}
          </h1>

          {/* Summary */}
          {summary && (
            <p className="text-text-secondary text-lg leading-relaxed mb-6 border-l-4 border-accent pl-4">
              {summary}
            </p>
          )}

          {/* Meta bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 pb-6 mb-8 border-b border-border">
            <div className="flex items-center gap-4 text-text-muted text-sm">
              <span className="flex items-center gap-1.5">
                <Calendar className="w-4 h-4" />
                {publishedDate}
              </span>
              <span className="flex items-center gap-1.5">
                <Eye className="w-4 h-4" />
                {post.views.toLocaleString()} views
              </span>
            </div>

            <div className="flex items-center gap-3">
              <LanguageToggle />

              {/* Like button */}
              <button
                onClick={handleLike}
                disabled={!user || liking}
                title={user ? (post.is_liked ? 'Unlike' : 'Like') : 'Sign in to like'}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-all duration-200 ${
                  post.is_liked
                    ? 'bg-red-500/10 border-red-500/30 text-red-400 hover:bg-red-500/20'
                    : 'bg-bg-secondary border-border text-text-secondary hover:border-accent/50 hover:text-accent'
                } ${!user ? 'opacity-60 cursor-not-allowed' : ''}`}
              >
                <Heart
                  className={`w-4 h-4 ${post.is_liked ? 'fill-current' : ''}`}
                />
                {post.likes_count}
              </button>

              {/* Save button */}
              <button
                onClick={handleSave}
                disabled={!user || saving}
                title={user ? (post.is_saved ? 'Unsave' : 'Save') : 'Sign in to save'}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg border text-sm font-medium transition-all duration-200 ${
                  post.is_saved
                    ? 'bg-accent/10 border-accent/30 text-accent'
                    : 'bg-bg-secondary border-border text-text-secondary hover:border-accent/50 hover:text-accent'
                } ${!user ? 'opacity-60 cursor-not-allowed' : ''}`}
              >
                <Bookmark
                  className={`w-4 h-4 ${post.is_saved ? 'fill-current' : ''}`}
                />
                {post.is_saved ? 'Saved' : 'Save'}
              </button>
            </div>
          </div>

          {/* Main content */}
          {content ? (
            <MarkdownRenderer content={content} className="mb-12" />
          ) : (
            <p className="text-text-secondary italic mb-12">No content available.</p>
          )}

          {/* Repo link */}
          {post.repo?.github_url && (
            <div className="my-10 p-6 bg-bg-secondary border border-border rounded-2xl">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center">
                  <Github className="w-5 h-5 text-accent" />
                </div>
                <div>
                  <h3 className="text-text-primary font-semibold">GitHub Repository</h3>
                  <p className="text-text-muted text-sm">{post.repo.repo_name}</p>
                </div>
              </div>
              <a
                href={post.repo.github_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 mt-2 px-5 py-2.5 bg-accent hover:bg-accent-light text-bg-primary font-semibold text-sm rounded-lg transition-colors"
              >
                <Star className="w-4 h-4" />
                View on GitHub
                <ExternalLink className="w-3.5 h-3.5 ml-1" />
              </a>
            </div>
          )}
        </article>

        {/* Comments */}
        <CommentSection postId={post.id} />
      </div>
    </main>
  )
}
