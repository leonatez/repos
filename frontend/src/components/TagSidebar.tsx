import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Tag as TagIcon } from 'lucide-react'
import { tagsApi } from '../api/client'
import { Tag } from '../types'

export default function TagSidebar() {
  const [tags, setTags] = useState<Tag[]>([])
  const [loading, setLoading] = useState(true)
  const { slug: activeSlug } = useParams<{ slug?: string }>()

  useEffect(() => {
    tagsApi.list()
      .then((res) => setTags(res.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  return (
    <aside className="bg-bg-secondary rounded-xl border border-border p-5">
      <h3 className="flex items-center gap-2 text-text-primary font-semibold mb-4">
        <TagIcon className="w-4 h-4 text-accent" />
        Browse Topics
      </h3>

      {loading ? (
        <div className="flex flex-col gap-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-8 bg-bg-tertiary rounded-lg animate-pulse" />
          ))}
        </div>
      ) : tags.length === 0 ? (
        <p className="text-text-muted text-sm">No tags yet.</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {tags.map((tag) => (
            <Link
              key={tag.id}
              to={`/tag/${tag.slug}`}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all duration-200 border ${
                activeSlug === tag.slug
                  ? 'bg-accent text-bg-primary border-accent'
                  : 'bg-bg-tertiary text-text-secondary border-border hover:border-accent/50 hover:text-accent hover:bg-accent/5'
              }`}
            >
              {tag.name}
            </Link>
          ))}
        </div>
      )}
    </aside>
  )
}
