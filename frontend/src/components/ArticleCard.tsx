import { Link } from 'react-router-dom'
import { Eye, Heart, Calendar, Star } from 'lucide-react'
import { PostSummary } from '../types'
import { useLanguage } from '../contexts/LanguageContext'
import { generateThumbnail } from '../lib/thumbnail'

interface ArticleCardProps {
  post: PostSummary
  featured?: boolean
}

function formatDate(dateStr: string | undefined): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export default function ArticleCard({ post, featured = false }: ArticleCardProps) {
  const { language } = useLanguage()

  const title = language === 'vi' ? post.title_vi : post.title_en
  const summary = language === 'vi' ? post.summary_vi : post.summary_en
  const thumbnail = post.repo?.github_url
    ? generateThumbnail(post.repo.github_url)
    : post.cover_image || '/default-thumbnail.png'

  if (featured) {
    return (
      <Link to={`/articles/${post.slug}`} className="group block">
        <article className="relative rounded-2xl overflow-hidden bg-bg-secondary border border-border hover:border-accent/50 transition-all duration-300 hover:shadow-lg hover:shadow-accent/10">
          {/* Thumbnail */}
          <div className="relative h-64 sm:h-80 overflow-hidden">
            <img
              src={thumbnail}
              alt={title}
              className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
              onError={(e) => {
                const img = e.target as HTMLImageElement
                img.src = 'https://via.placeholder.com/1200x600/1e293b/14b8a6?text=GitHub+Repo'
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-bg-primary via-bg-primary/40 to-transparent" />

            {/* Featured badge */}
            <div className="absolute top-4 left-4">
              <span className="px-3 py-1 bg-accent text-bg-primary text-xs font-bold rounded-full uppercase tracking-wide">
                Featured
              </span>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            {/* Tags */}
            {post.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {post.tags.slice(0, 4).map((tag) => (
                  <span
                    key={tag.id}
                    className="px-2 py-0.5 bg-accent/10 text-accent text-xs rounded-full border border-accent/20"
                  >
                    {tag.name}
                  </span>
                ))}
              </div>
            )}

            <h2 className="text-xl sm:text-2xl font-bold text-text-primary mb-2 group-hover:text-accent transition-colors line-clamp-2">
              {title}
            </h2>

            {summary && (
              <p className="text-text-secondary text-sm leading-relaxed line-clamp-2 mb-4">
                {summary}
              </p>
            )}

            {/* Meta */}
            <div className="flex items-center gap-4 text-text-muted text-xs">
              <span className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" />
                {formatDate(post.published_at || post.created_at)}
              </span>
              <span className="flex items-center gap-1">
                <Eye className="w-3.5 h-3.5" />
                {post.views.toLocaleString()}
              </span>
              <span className="flex items-center gap-1">
                <Heart className="w-3.5 h-3.5" />
                {post.likes_count}
              </span>
            </div>
          </div>
        </article>
      </Link>
    )
  }

  return (
    <Link to={`/articles/${post.slug}`} className="group block">
      <article className="h-full rounded-xl overflow-hidden bg-bg-secondary border border-border hover:border-accent/50 transition-all duration-300 hover:shadow-lg hover:shadow-accent/10 flex flex-col">
        {/* Thumbnail */}
        <div className="relative h-44 overflow-hidden shrink-0">
          <img
            src={thumbnail}
            alt={title}
            className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
            onError={(e) => {
              const img = e.target as HTMLImageElement
              img.src = 'https://via.placeholder.com/800x400/1e293b/14b8a6?text=GitHub+Repo'
            }}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-bg-secondary/90 to-transparent" />
        </div>

        {/* Content */}
        <div className="p-4 flex flex-col flex-1">
          {/* Tags */}
          {post.tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-2">
              {post.tags.slice(0, 3).map((tag) => (
                <span
                  key={tag.id}
                  className="px-2 py-0.5 bg-accent/10 text-accent text-xs rounded-full border border-accent/20"
                >
                  {tag.name}
                </span>
              ))}
              {post.tags.length > 3 && (
                <span className="px-2 py-0.5 bg-bg-tertiary text-text-muted text-xs rounded-full">
                  +{post.tags.length - 3}
                </span>
              )}
            </div>
          )}

          <h3 className="font-semibold text-text-primary mb-1.5 group-hover:text-accent transition-colors line-clamp-2 flex-1">
            {title}
          </h3>

          {summary && (
            <p className="text-text-secondary text-xs leading-relaxed line-clamp-2 mb-3">
              {summary}
            </p>
          )}

          {/* Meta */}
          <div className="flex items-center justify-between text-text-muted text-xs mt-auto pt-3 border-t border-border">
            <span className="flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {formatDate(post.published_at || post.created_at)}
            </span>
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1">
                <Eye className="w-3 h-3" />
                {post.views}
              </span>
              <span className={`flex items-center gap-1 ${post.is_liked ? 'text-red-400' : ''}`}>
                <Heart className={`w-3 h-3 ${post.is_liked ? 'fill-current' : ''}`} />
                {post.likes_count}
              </span>
            </div>
          </div>
        </div>
      </article>
    </Link>
  )
}
