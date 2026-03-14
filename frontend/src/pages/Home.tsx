import { useEffect, useState } from 'react'
import { TrendingUp, Rss } from 'lucide-react'
import { postsApi } from '../api/client'
import { PostSummary } from '../types'
import ArticleCard from '../components/ArticleCard'
import TagSidebar from '../components/TagSidebar'
import LanguageToggle from '../components/LanguageToggle'

const LIMIT = 9

export default function Home() {
  const [posts, setPosts] = useState<PostSummary[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)

  useEffect(() => {
    postsApi.list(LIMIT + 1, 0)
      .then((res) => {
        const data = res.data
        setPosts(data.items)
        setTotal(data.total)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const loadMore = async () => {
    setLoadingMore(true)
    const newOffset = offset + LIMIT + 1
    try {
      const res = await postsApi.list(LIMIT, newOffset)
      setPosts((prev) => [...prev, ...res.data.items])
      setOffset(newOffset)
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingMore(false)
    }
  }

  const featured = posts[0]
  const rest = posts.slice(1)

  return (
    <main className="min-h-screen bg-bg-primary">
      {/* Hero header */}
      <div className="bg-gradient-to-b from-bg-secondary to-bg-primary border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <Rss className="w-5 h-5 text-accent" />
                <span className="text-accent text-sm font-semibold uppercase tracking-widest">
                  AI GitHub Repo Digest
                </span>
              </div>
              <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-text-primary mb-4 leading-tight">
                Discover the{' '}
                <span className="text-accent">Best GitHub</span>
                <br className="hidden sm:block" /> Repositories
              </h1>
              <p className="text-text-secondary text-lg max-w-2xl">
                AI-powered bilingual articles about the most interesting open source projects,
                curated for Vietnamese and global developers.
              </p>
            </div>
            <LanguageToggle className="shrink-0 hidden sm:flex" />
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {loading ? (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            <div className="lg:col-span-3 space-y-6">
              <div className="h-80 bg-bg-secondary rounded-2xl animate-pulse" />
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i} className="h-72 bg-bg-secondary rounded-xl animate-pulse" />
                ))}
              </div>
            </div>
            <div className="lg:col-span-1 h-64 bg-bg-secondary rounded-xl animate-pulse" />
          </div>
        ) : posts.length === 0 ? (
          <div className="text-center py-24">
            <div className="w-20 h-20 bg-bg-secondary rounded-2xl flex items-center justify-center mx-auto mb-6">
              <TrendingUp className="w-10 h-10 text-accent" />
            </div>
            <h2 className="text-2xl font-bold text-text-primary mb-3">No articles yet</h2>
            <p className="text-text-secondary">
              New articles will appear here once they are published.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
            {/* Main content */}
            <div className="lg:col-span-3 space-y-8">
              {/* Featured article */}
              {featured && (
                <div>
                  <div className="flex items-center gap-2 mb-4">
                    <TrendingUp className="w-4 h-4 text-accent" />
                    <h2 className="text-text-secondary text-sm font-semibold uppercase tracking-wider">
                      Latest
                    </h2>
                  </div>
                  <ArticleCard post={featured} featured />
                </div>
              )}

              {/* Article grid */}
              {rest.length > 0 && (
                <div>
                  <h2 className="text-text-secondary text-sm font-semibold uppercase tracking-wider mb-4">
                    More Articles
                  </h2>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                    {rest.map((post) => (
                      <ArticleCard key={post.id} post={post} />
                    ))}
                  </div>
                </div>
              )}

              {/* Load more */}
              {posts.length < total && (
                <div className="text-center pt-4">
                  <button
                    onClick={loadMore}
                    disabled={loadingMore}
                    className="px-8 py-3 bg-bg-secondary hover:bg-bg-tertiary border border-border hover:border-accent/50 text-text-primary font-medium rounded-xl transition-all duration-200 disabled:opacity-50"
                  >
                    {loadingMore ? 'Loading...' : 'Load More Articles'}
                  </button>
                </div>
              )}
            </div>

            {/* Sidebar */}
            <div className="lg:col-span-1">
              <div className="sticky top-24">
                <TagSidebar />
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
