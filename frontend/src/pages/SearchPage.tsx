import { useEffect, useState, FormEvent } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { Search, ArrowLeft } from 'lucide-react'
import { searchApi } from '../api/client'
import { PostSummary } from '../types'
import ArticleCard from '../components/ArticleCard'

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const query = searchParams.get('q') || ''
  const [inputValue, setInputValue] = useState(query)
  const [posts, setPosts] = useState<PostSummary[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setInputValue(query)
    if (!query.trim()) {
      setPosts([])
      setTotal(0)
      return
    }
    setLoading(true)
    searchApi.search(query)
      .then((res) => {
        const data = res.data
        setPosts(data.items)
        setTotal(data.total)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [query])

  const handleSearch = (e: FormEvent) => {
    e.preventDefault()
    if (inputValue.trim()) {
      setSearchParams({ q: inputValue.trim() })
    }
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

        {/* Search bar */}
        <form onSubmit={handleSearch} className="mb-8">
          <div className="relative max-w-2xl">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Search articles, tags, repositories..."
              className="w-full pl-12 pr-4 py-4 bg-bg-secondary border border-border rounded-2xl text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent text-lg transition-colors"
            />
          </div>
        </form>

        {/* Results header */}
        {query && !loading && (
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-text-primary">
              {total > 0 ? (
                <>
                  <span className="text-accent">{total}</span> result{total !== 1 ? 's' : ''} for "
                  <span className="text-accent">{query}</span>"
                </>
              ) : (
                <>
                  No results for "<span className="text-accent">{query}</span>"
                </>
              )}
            </h1>
          </div>
        )}

        {/* Results grid */}
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-72 bg-bg-secondary rounded-xl animate-pulse" />
            ))}
          </div>
        ) : posts.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {posts.map((post) => (
              <ArticleCard key={post.id} post={post} />
            ))}
          </div>
        ) : query ? (
          <div className="text-center py-20 text-text-muted">
            <Search className="w-16 h-16 mx-auto mb-4 opacity-20" />
            <p className="text-lg mb-2">No articles found.</p>
            <p className="text-sm">Try different keywords or browse by tags.</p>
          </div>
        ) : (
          <div className="text-center py-20 text-text-muted">
            <Search className="w-16 h-16 mx-auto mb-4 opacity-20" />
            <p className="text-lg">Enter a keyword to search articles.</p>
          </div>
        )}
      </div>
    </main>
  )
}
