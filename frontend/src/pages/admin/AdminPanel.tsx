import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import {
  Settings, Plus, Eye, Edit, CheckCircle, Clock,
  FileText, Rss, ArrowLeft
} from 'lucide-react'
import { adminApi } from '../../api/client'
import { PostSummary } from '../../types'
import { useAuth } from '../../contexts/AuthContext'

function StatusBadge({ status }: { status: string }) {
  if (status === 'published') {
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-green-500/10 text-green-400 border border-green-500/20 rounded-full text-xs font-medium">
        <CheckCircle className="w-3 h-3" />
        Published
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 rounded-full text-xs font-medium">
      <Clock className="w-3 h-3" />
      Draft
    </span>
  )
}

export default function AdminPanel() {
  const { user, isAdmin, loading: authLoading } = useAuth()
  const [posts, setPosts] = useState<PostSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [publishing, setPublishing] = useState<string | null>(null)

  useEffect(() => {
    if (!isAdmin) return
    adminApi.listPosts(50, 0)
      .then((res) => setPosts(res.data.items))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [isAdmin])

  if (!authLoading && (!user || !isAdmin)) {
    return <Navigate to="/" replace />
  }

  const handlePublish = async (postId: string) => {
    setPublishing(postId)
    try {
      await adminApi.publishPost(postId)
      setPosts((prev) =>
        prev.map((p) =>
          p.id === postId
            ? { ...p, status: 'published', published_at: new Date().toISOString() }
            : p
        )
      )
    } catch (err) {
      console.error('Failed to publish:', err)
    } finally {
      setPublishing(null)
    }
  }

  const drafts = posts.filter((p) => p.status === 'draft')
  const published = posts.filter((p) => p.status === 'published')

  return (
    <main className="min-h-screen bg-bg-primary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-text-muted hover:text-accent transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center">
              <Settings className="w-5 h-5 text-accent" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-text-primary">Admin Panel</h1>
              <p className="text-text-muted text-sm">Manage articles and content</p>
            </div>
          </div>

          <Link
            to="/admin/new"
            className="flex items-center gap-2 px-5 py-2.5 bg-accent hover:bg-accent-light text-bg-primary font-semibold text-sm rounded-xl transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Article
          </Link>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          <div className="bg-bg-secondary border border-border rounded-xl p-5">
            <div className="flex items-center gap-3">
              <FileText className="w-8 h-8 text-accent" />
              <div>
                <div className="text-2xl font-bold text-text-primary">{posts.length}</div>
                <div className="text-text-muted text-sm">Total Articles</div>
              </div>
            </div>
          </div>
          <div className="bg-bg-secondary border border-border rounded-xl p-5">
            <div className="flex items-center gap-3">
              <Rss className="w-8 h-8 text-green-400" />
              <div>
                <div className="text-2xl font-bold text-text-primary">{published.length}</div>
                <div className="text-text-muted text-sm">Published</div>
              </div>
            </div>
          </div>
          <div className="bg-bg-secondary border border-border rounded-xl p-5">
            <div className="flex items-center gap-3">
              <Clock className="w-8 h-8 text-yellow-400" />
              <div>
                <div className="text-2xl font-bold text-text-primary">{drafts.length}</div>
                <div className="text-text-muted text-sm">Drafts</div>
              </div>
            </div>
          </div>
        </div>

        {/* Posts table */}
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="h-16 bg-bg-secondary rounded-xl animate-pulse" />
            ))}
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-20 text-text-muted">
            <FileText className="w-16 h-16 mx-auto mb-4 opacity-20" />
            <p className="text-lg mb-4">No articles yet.</p>
            <Link
              to="/admin/new"
              className="px-6 py-3 bg-accent text-bg-primary font-semibold rounded-xl"
            >
              Generate First Article
            </Link>
          </div>
        ) : (
          <div className="bg-bg-secondary border border-border rounded-2xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left px-6 py-4 text-text-muted text-sm font-medium">Article</th>
                  <th className="text-left px-6 py-4 text-text-muted text-sm font-medium hidden sm:table-cell">Status</th>
                  <th className="text-left px-6 py-4 text-text-muted text-sm font-medium hidden md:table-cell">Views</th>
                  <th className="text-left px-6 py-4 text-text-muted text-sm font-medium hidden lg:table-cell">Created</th>
                  <th className="text-right px-6 py-4 text-text-muted text-sm font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {posts.map((post) => (
                  <tr key={post.id} className="hover:bg-bg-tertiary/30 transition-colors">
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-text-primary font-medium text-sm line-clamp-1">
                          {post.title_en}
                        </p>
                        <p className="text-text-muted text-xs mt-0.5 line-clamp-1">
                          {post.title_vi}
                        </p>
                      </div>
                    </td>
                    <td className="px-6 py-4 hidden sm:table-cell">
                      <StatusBadge status={post.status} />
                    </td>
                    <td className="px-6 py-4 text-text-secondary text-sm hidden md:table-cell">
                      <span className="flex items-center gap-1">
                        <Eye className="w-3.5 h-3.5" />
                        {post.views}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-text-muted text-xs hidden lg:table-cell">
                      {new Date(post.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 justify-end">
                        {post.status === 'draft' && (
                          <button
                            onClick={() => handlePublish(post.id)}
                            disabled={publishing === post.id}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/10 hover:bg-green-500/20 text-green-400 border border-green-500/20 rounded-lg text-xs font-medium transition-colors disabled:opacity-60"
                          >
                            <CheckCircle className="w-3.5 h-3.5" />
                            {publishing === post.id ? '...' : 'Publish'}
                          </button>
                        )}
                        <Link
                          to={`/admin/posts/${post.id}/edit`}
                          className="flex items-center gap-1.5 px-3 py-1.5 bg-bg-tertiary hover:bg-border text-text-secondary rounded-lg text-xs font-medium transition-colors"
                        >
                          <Edit className="w-3.5 h-3.5" />
                          Edit
                        </Link>
                        {post.status === 'published' && (
                          <Link
                            to={`/articles/${post.slug}`}
                            className="flex items-center gap-1.5 px-3 py-1.5 bg-accent/10 hover:bg-accent/20 text-accent border border-accent/20 rounded-lg text-xs font-medium transition-colors"
                            target="_blank"
                          >
                            <Eye className="w-3.5 h-3.5" />
                            View
                          </Link>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </main>
  )
}
