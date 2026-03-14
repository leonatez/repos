import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { Bookmark, ArrowLeft } from 'lucide-react'
import { favoritesApi } from '../api/client'
import { PostSummary } from '../types'
import { useAuth } from '../contexts/AuthContext'
import ArticleCard from '../components/ArticleCard'

export default function FavoritesPage() {
  const { user, loading: authLoading } = useAuth()
  const [posts, setPosts] = useState<PostSummary[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user) return
    favoritesApi.list(12, 0)
      .then((res) => {
        setPosts(res.data.items)
        setTotal(res.data.total)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [user])

  if (!authLoading && !user) {
    return <Navigate to="/login" replace />
  }

  return (
    <main className="min-h-screen bg-bg-primary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-text-muted hover:text-accent mb-6 text-sm transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>

        <div className="flex items-center gap-3 mb-8">
          <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center">
            <Bookmark className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-text-primary">Saved Articles</h1>
            <p className="text-text-secondary text-sm">{total} saved article{total !== 1 ? 's' : ''}</p>
          </div>
        </div>

        {loading || authLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-72 bg-bg-secondary rounded-xl animate-pulse" />
            ))}
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-20 text-text-muted">
            <Bookmark className="w-16 h-16 mx-auto mb-4 opacity-20" />
            <p className="text-lg mb-2">No saved articles yet.</p>
            <p className="text-sm mb-6">Bookmark articles you want to read later.</p>
            <Link
              to="/"
              className="px-6 py-3 bg-accent hover:bg-accent-light text-bg-primary font-semibold rounded-xl transition-colors"
            >
              Browse Articles
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {posts.map((post) => (
              <ArticleCard key={post.id} post={post} />
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
