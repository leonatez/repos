import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Tag as TagIcon, ArrowLeft } from 'lucide-react'
import { tagsApi } from '../api/client'
import { PostSummary, Tag } from '../types'
import ArticleCard from '../components/ArticleCard'

export default function TagPage() {
  const { slug } = useParams<{ slug: string }>()
  const [posts, setPosts] = useState<PostSummary[]>([])
  const [tag, setTag] = useState<Tag | null>(null)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!slug) return
    setLoading(true)
    tagsApi.getPostsByTag(slug, 12, 0)
      .then((res) => {
        const data = res.data
        setPosts(data.items)
        setTag(data.tag)
        setTotal(data.total)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [slug])

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

        {/* Tag header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center">
              <TagIcon className="w-5 h-5 text-accent" />
            </div>
            <h1 className="text-3xl font-bold text-text-primary">
              #{tag?.name || slug}
            </h1>
          </div>
          <p className="text-text-secondary ml-13">
            {total} article{total !== 1 ? 's' : ''} tagged with this topic
          </p>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-72 bg-bg-secondary rounded-xl animate-pulse" />
            ))}
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-20 text-text-muted">
            <TagIcon className="w-16 h-16 mx-auto mb-4 opacity-20" />
            <p className="text-lg">No articles found for this tag.</p>
            <Link to="/" className="mt-4 inline-block text-accent hover:underline">
              Browse all articles
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
