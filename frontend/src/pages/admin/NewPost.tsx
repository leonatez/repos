import { useState, FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import {
  Sparkles, ArrowLeft, CheckCircle, AlertCircle,
  Github, Loader, FileText, XCircle
} from 'lucide-react'
import { adminApi } from '../../api/client'
import { Post } from '../../types'
import { useAuth } from '../../contexts/AuthContext'

type Step = 'input' | 'processing' | 'done' | 'error'

interface SubmitResult {
  posts: Post[]
  total: number
  errors: { url: string; detail: string }[]
}

const PROCESSING_MESSAGES = [
  'Extracting GitHub URLs from text...',
  'Fetching repository information from GitHub...',
  'Analyzing repositories with AI (this may take a minute)...',
  'Generating bilingual articles...',
  'Saving to database...',
]

export default function NewPost() {
  const { user, isAdmin, loading: authLoading } = useAuth()
  const navigate = useNavigate()
  const [text, setText] = useState('')
  const [step, setStep] = useState<Step>('input')
  const [messageIndex, setMessageIndex] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<SubmitResult | null>(null)

  if (!authLoading && (!user || !isAdmin)) {
    return <Navigate to="/" replace />
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!text.trim()) return

    setStep('processing')
    setError(null)
    setMessageIndex(0)

    const delays = [3000, 8000, 35000, 35000]
    const timeouts: ReturnType<typeof setTimeout>[] = []
    const scheduleNext = (idx: number) => {
      if (idx >= delays.length) return
      const t = setTimeout(() => {
        setMessageIndex(idx + 1)
        scheduleNext(idx + 1)
      }, delays[idx])
      timeouts.push(t)
    }
    scheduleNext(0)
    const clearAll = () => timeouts.forEach(clearTimeout)

    try {
      const res = await adminApi.submit(text.trim())
      clearAll()
      setResult(res.data)
      setStep('done')
    } catch (err: unknown) {
      clearAll()
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        (err instanceof Error ? err.message : 'Something went wrong')
      setError(msg)
      setStep('error')
    }
  }

  return (
    <main className="min-h-screen bg-bg-primary">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <Link to="/admin" className="text-text-muted hover:text-accent transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div className="w-10 h-10 bg-accent/10 rounded-xl flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-accent" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Generate New Articles</h1>
            <p className="text-text-muted text-sm">Paste text containing one or more GitHub URLs</p>
          </div>
        </div>

        {/* Input step */}
        {step === 'input' && (
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="bg-bg-secondary border border-border rounded-2xl p-6">
              <label className="block text-text-primary font-semibold mb-3">
                Text with GitHub URLs
              </label>
              <p className="text-text-muted text-sm mb-4">
                Paste a tweet, LinkedIn post, HackerNews thread, or any text containing GitHub repository URLs.
                Multiple URLs are supported — each repo gets its own bilingual article.
              </p>
              <textarea
                value={text}
                onChange={(e) => setText(e.target.value)}
                rows={8}
                placeholder={`Example (multiple URLs supported):\n\nCheck out these awesome AI tools:\nhttps://github.com/owner/repo-one\nhttps://github.com/another/repo-two\n\nBoth are incredible for developers!`}
                className="w-full bg-bg-primary border border-border rounded-xl p-4 text-text-primary placeholder:text-text-muted text-sm resize-none focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-colors font-mono"
              />
              <p className="text-text-muted text-xs mt-2">{text.length} characters</p>
            </div>

            <div className="flex items-center gap-4">
              <button
                type="submit"
                disabled={!text.trim()}
                className="flex items-center gap-2 px-6 py-3 bg-accent hover:bg-accent-light disabled:opacity-50 disabled:cursor-not-allowed text-bg-primary font-semibold rounded-xl transition-colors"
              >
                <Sparkles className="w-4 h-4" />
                Generate Articles
              </button>
              <Link
                to="/admin"
                className="px-6 py-3 bg-bg-secondary border border-border hover:border-accent/50 text-text-secondary rounded-xl transition-colors"
              >
                Cancel
              </Link>
            </div>
          </form>
        )}

        {/* Processing step */}
        {step === 'processing' && (
          <div className="bg-bg-secondary border border-border rounded-2xl p-10 text-center">
            <div className="w-16 h-16 bg-accent/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <Loader className="w-8 h-8 text-accent animate-spin" />
            </div>
            <h2 className="text-xl font-bold text-text-primary mb-3">Processing...</h2>
            <p className="text-text-secondary text-sm mb-8 max-w-md mx-auto">
              The AI is analyzing repositories and generating articles. Multiple repos are processed in parallel.
              This typically takes 30–120 seconds.
            </p>

            <div className="text-left max-w-sm mx-auto space-y-3">
              {PROCESSING_MESSAGES.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex items-center gap-3 text-sm transition-all duration-500 ${
                    idx < messageIndex
                      ? 'text-accent'
                      : idx === messageIndex
                      ? 'text-text-primary'
                      : 'text-text-muted opacity-40'
                  }`}
                >
                  {idx < messageIndex ? (
                    <CheckCircle className="w-4 h-4 shrink-0" />
                  ) : idx === messageIndex ? (
                    <Loader className="w-4 h-4 shrink-0 animate-spin" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-text-muted shrink-0" />
                  )}
                  {msg}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error step */}
        {step === 'error' && (
          <div className="bg-bg-secondary border border-border rounded-2xl p-8">
            <div className="flex items-start gap-4 mb-6">
              <div className="w-12 h-12 bg-red-500/10 rounded-xl flex items-center justify-center shrink-0">
                <AlertCircle className="w-6 h-6 text-red-400" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-text-primary mb-2">Generation Failed</h2>
                <p className="text-red-400 text-sm">{error}</p>
              </div>
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => setStep('input')}
                className="px-5 py-2.5 bg-accent hover:bg-accent-light text-bg-primary font-semibold rounded-xl transition-colors"
              >
                Try Again
              </button>
              <Link
                to="/admin"
                className="px-5 py-2.5 bg-bg-tertiary text-text-secondary rounded-xl"
              >
                Back to Admin
              </Link>
            </div>
          </div>
        )}

        {/* Success step */}
        {step === 'done' && result && (
          <div className="space-y-6">
            {/* Summary banner */}
            <div className="bg-bg-secondary border border-green-500/30 rounded-2xl p-6">
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 bg-green-500/10 rounded-xl flex items-center justify-center shrink-0">
                  <CheckCircle className="w-6 h-6 text-green-400" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-text-primary mb-1">
                    {result.total === 1
                      ? '1 Article Generated!'
                      : `${result.total} Articles Generated!`}
                  </h2>
                  <p className="text-text-secondary text-sm">
                    {result.total > 0 && 'All drafts are saved — review and publish each one when ready.'}
                    {result.errors.length > 0 && (
                      <span className="text-yellow-400 ml-1">
                        {result.errors.length} URL{result.errors.length > 1 ? 's' : ''} failed.
                      </span>
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* Generated post cards */}
            {result.posts.map((post) => (
              <div
                key={post.id}
                className="bg-bg-secondary border border-border rounded-2xl p-5"
              >
                <div className="flex items-center gap-2 mb-3">
                  <Github className="w-4 h-4 text-accent" />
                  <span className="text-text-muted text-xs uppercase tracking-wider">Draft Article</span>
                </div>
                <h3 className="text-lg font-bold text-text-primary mb-1">{post.title_en}</h3>
                <p className="text-text-secondary text-sm mb-2">{post.title_vi}</p>
                {post.summary_en && (
                  <p className="text-text-muted text-sm leading-relaxed line-clamp-2">{post.summary_en}</p>
                )}
                {post.tags && post.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3 mb-4">
                    {post.tags.map((tag) => (
                      <span
                        key={tag.id}
                        className="px-2 py-0.5 bg-accent/10 text-accent text-xs rounded-full border border-accent/20"
                      >
                        {tag.name}
                      </span>
                    ))}
                  </div>
                )}
                <Link
                  to={`/admin/posts/${post.id}/edit`}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent-light text-bg-primary font-semibold text-sm rounded-xl transition-colors"
                >
                  <FileText className="w-4 h-4" />
                  Review & Edit
                </Link>
              </div>
            ))}

            {/* Per-URL errors */}
            {result.errors.length > 0 && (
              <div className="bg-bg-secondary border border-red-500/20 rounded-2xl p-5 space-y-3">
                <div className="flex items-center gap-2 mb-1">
                  <XCircle className="w-4 h-4 text-red-400" />
                  <span className="text-red-400 text-sm font-semibold">Failed URLs</span>
                </div>
                {result.errors.map((err) => (
                  <div key={err.url} className="text-sm">
                    <p className="text-text-secondary font-mono break-all">{err.url}</p>
                    <p className="text-red-400 text-xs mt-0.5">{err.detail}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-wrap gap-3">
              <button
                onClick={() => { setText(''); setStep('input'); setResult(null) }}
                className="px-5 py-2.5 bg-accent hover:bg-accent-light text-bg-primary font-semibold rounded-xl transition-colors"
              >
                Generate More
              </button>
              <Link
                to="/admin"
                className="px-5 py-2.5 border border-border hover:border-accent/50 text-text-secondary rounded-xl transition-colors"
              >
                Back to Admin
              </Link>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
