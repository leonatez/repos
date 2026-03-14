import { useState, useEffect, FormEvent } from 'react'
import { MessageSquare, Send, User, Trash2 } from 'lucide-react'
import { commentsApi, adminApi } from '../api/client'
import { Comment } from '../types'
import { useAuth } from '../contexts/AuthContext'

interface CommentSectionProps {
  postId: string
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function CommentSection({ postId }: CommentSectionProps) {
  const { user, isAdmin } = useAuth()
  const [comments, setComments] = useState<Comment[]>([])
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    commentsApi.list(postId)
      .then((res) => setComments(res.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [postId])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!content.trim() || !user) return

    setSubmitting(true)
    setError(null)
    try {
      const res = await commentsApi.create(postId, content.trim())
      setComments((prev) => [...prev, res.data])
      setContent('')
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to post comment'
      setError(message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (commentId: string) => {
    if (!isAdmin) return
    try {
      await adminApi.deleteComment(commentId)
      setComments((prev) => prev.filter((c) => c.id !== commentId))
    } catch (err) {
      console.error('Failed to delete comment:', err)
    }
  }

  return (
    <section className="mt-12">
      <h2 className="flex items-center gap-2 text-xl font-bold text-text-primary mb-6 pb-4 border-b border-border">
        <MessageSquare className="w-5 h-5 text-accent" />
        Comments ({comments.length})
      </h2>

      {/* Comment form */}
      {user ? (
        <form onSubmit={handleSubmit} className="mb-8">
          <div className="flex items-start gap-3">
            <div className="w-9 h-9 rounded-full bg-accent/20 flex items-center justify-center shrink-0 mt-1">
              <User className="w-5 h-5 text-accent" />
            </div>
            <div className="flex-1">
              <textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Share your thoughts..."
                rows={3}
                maxLength={2000}
                className="w-full bg-bg-secondary border border-border rounded-xl p-4 text-text-primary placeholder:text-text-muted text-sm resize-none focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-colors"
              />
              {error && (
                <p className="text-red-400 text-xs mt-1">{error}</p>
              )}
              <div className="flex items-center justify-between mt-2">
                <span className="text-text-muted text-xs">{content.length}/2000</span>
                <button
                  type="submit"
                  disabled={!content.trim() || submitting}
                  className="flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent-light disabled:opacity-50 disabled:cursor-not-allowed text-bg-primary font-medium text-sm rounded-lg transition-colors"
                >
                  <Send className="w-4 h-4" />
                  {submitting ? 'Posting...' : 'Post Comment'}
                </button>
              </div>
            </div>
          </div>
        </form>
      ) : (
        <div className="mb-8 p-4 bg-bg-secondary border border-border rounded-xl text-center">
          <p className="text-text-secondary text-sm">
            <a href="/login" className="text-accent hover:underline">Sign in</a> to leave a comment.
          </p>
        </div>
      )}

      {/* Comments list */}
      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex gap-3">
              <div className="w-9 h-9 rounded-full bg-bg-tertiary animate-pulse shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-bg-tertiary rounded animate-pulse w-32" />
                <div className="h-16 bg-bg-tertiary rounded-xl animate-pulse" />
              </div>
            </div>
          ))}
        </div>
      ) : comments.length === 0 ? (
        <div className="text-center py-12 text-text-muted">
          <MessageSquare className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p>No comments yet. Be the first to share your thoughts!</p>
        </div>
      ) : (
        <div className="space-y-5">
          {comments.map((comment) => (
            <div key={comment.id} className="flex gap-3 group">
              <div className="w-9 h-9 rounded-full bg-accent/20 flex items-center justify-center shrink-0">
                {comment.avatar_url ? (
                  <img
                    src={comment.avatar_url}
                    alt={comment.username || 'User'}
                    className="w-9 h-9 rounded-full object-cover"
                  />
                ) : (
                  <User className="w-5 h-5 text-accent" />
                )}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-text-primary">
                      {comment.username || 'Anonymous'}
                    </span>
                    <span className="text-text-muted text-xs">
                      {formatDate(comment.created_at)}
                    </span>
                  </div>
                  {isAdmin && (
                    <button
                      onClick={() => handleDelete(comment.id)}
                      className="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-300 p-1 transition-all"
                      title="Delete comment"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>
                <div className="bg-bg-secondary border border-border rounded-xl p-4">
                  <p className="text-text-secondary text-sm leading-relaxed whitespace-pre-wrap">
                    {comment.content}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
