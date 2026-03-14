import { useEffect, useState, FormEvent } from 'react'
import { useParams, Link, Navigate, useNavigate } from 'react-router-dom'
import {
  ArrowLeft, Save, CheckCircle, Eye, Edit3,
  AlertCircle, Globe, Languages
} from 'lucide-react'
import { adminApi } from '../../api/client'
import { Post } from '../../types'
import { useAuth } from '../../contexts/AuthContext'
import MarkdownRenderer from '../../components/MarkdownRenderer'

type PreviewLang = 'vi' | 'en'
type ActiveTab = 'edit' | 'preview'

export default function EditPost() {
  const { id } = useParams<{ id: string }>()
  const { user, isAdmin, loading: authLoading } = useAuth()
  const navigate = useNavigate()

  const [post, setPost] = useState<Post | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [success, setSuccess] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [previewLang, setPreviewLang] = useState<PreviewLang>('en')
  const [activeTab, setActiveTab] = useState<ActiveTab>('edit')

  // Form fields
  const [titleVi, setTitleVi] = useState('')
  const [titleEn, setTitleEn] = useState('')
  const [summaryVi, setSummaryVi] = useState('')
  const [summaryEn, setSummaryEn] = useState('')
  const [contentVi, setContentVi] = useState('')
  const [contentEn, setContentEn] = useState('')
  const [tags, setTags] = useState('')

  useEffect(() => {
    if (!id || !isAdmin) return
    adminApi.listPosts(100, 0)
      .then((res) => {
        const found = res.data.items.find((p: Post) => p.id === id)
        if (found) {
          setPost(found)
          setTitleVi(found.title_vi || '')
          setTitleEn(found.title_en || '')
          setSummaryVi(found.summary_vi || '')
          setSummaryEn(found.summary_en || '')
          setContentVi(found.content_markdown_vi || '')
          setContentEn(found.content_markdown_en || '')
          setTags((found.tags || []).map((t: { name: string }) => t.name).join(', '))
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [id, isAdmin])

  if (!authLoading && (!user || !isAdmin)) {
    return <Navigate to="/" replace />
  }

  const handleSave = async (e: FormEvent) => {
    e.preventDefault()
    if (!id) return

    setSaving(true)
    setError(null)
    setSuccess(null)

    const tagList = tags.split(',').map((t) => t.trim()).filter(Boolean)

    try {
      await adminApi.updatePost(id, {
        title_vi: titleVi,
        title_en: titleEn,
        summary_vi: summaryVi,
        summary_en: summaryEn,
        content_markdown_vi: contentVi,
        content_markdown_en: contentEn,
        tags: tagList,
      })
      setSuccess('Article saved successfully!')
      setTimeout(() => setSuccess(null), 3000)
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to save')
    } finally {
      setSaving(false)
    }
  }

  const handlePublish = async () => {
    if (!id) return
    setPublishing(true)
    setError(null)
    try {
      await adminApi.publishPost(id)
      setSuccess('Article published successfully!')
      setPost((prev) => prev ? { ...prev, status: 'published' } : prev)
      setTimeout(() => navigate('/admin'), 2000)
    } catch (err: unknown) {
      setError((err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Failed to publish')
    } finally {
      setPublishing(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-text-muted">Loading...</div>
      </div>
    )
  }

  if (!post) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="text-center">
          <p className="text-text-muted mb-4">Article not found.</p>
          <Link to="/admin" className="text-accent hover:underline">Back to Admin</Link>
        </div>
      </div>
    )
  }

  const previewTitle = previewLang === 'vi' ? titleVi : titleEn
  const previewSummary = previewLang === 'vi' ? summaryVi : summaryEn
  const previewContent = previewLang === 'vi' ? contentVi : contentEn

  return (
    <main className="min-h-screen bg-bg-primary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {/* Header */}
        <div className="flex items-center justify-between gap-4 mb-8">
          <div className="flex items-center gap-3">
            <Link to="/admin" className="text-text-muted hover:text-accent transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-xl font-bold text-text-primary">Edit Article</h1>
              <p className="text-text-muted text-xs">
                Status: <span className={post.status === 'published' ? 'text-green-400' : 'text-yellow-400'}>
                  {post.status}
                </span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {post.status === 'draft' && (
              <button
                onClick={handlePublish}
                disabled={publishing}
                className="flex items-center gap-2 px-4 py-2 bg-green-500/10 hover:bg-green-500/20 text-green-400 border border-green-500/30 rounded-xl text-sm font-medium transition-colors disabled:opacity-60"
              >
                <Globe className="w-4 h-4" />
                {publishing ? 'Publishing...' : 'Publish'}
              </button>
            )}
            {post.status === 'published' && (
              <Link
                to={`/articles/${post.slug}`}
                target="_blank"
                className="flex items-center gap-2 px-4 py-2 bg-accent/10 hover:bg-accent/20 text-accent border border-accent/30 rounded-xl text-sm font-medium transition-colors"
              >
                <Eye className="w-4 h-4" />
                View Live
              </Link>
            )}
          </div>
        </div>

        {/* Alerts */}
        {error && (
          <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-xl mb-6">
            <AlertCircle className="w-5 h-5 text-red-400 shrink-0" />
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}
        {success && (
          <div className="flex items-center gap-3 p-4 bg-green-500/10 border border-green-500/30 rounded-xl mb-6">
            <CheckCircle className="w-5 h-5 text-green-400" />
            <p className="text-green-400 text-sm">{success}</p>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          <button
            onClick={() => setActiveTab('edit')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'edit'
                ? 'bg-accent text-bg-primary'
                : 'bg-bg-secondary text-text-secondary hover:text-text-primary border border-border'
            }`}
          >
            <Edit3 className="w-4 h-4" />
            Edit
          </button>
          <button
            onClick={() => setActiveTab('preview')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === 'preview'
                ? 'bg-accent text-bg-primary'
                : 'bg-bg-secondary text-text-secondary hover:text-text-primary border border-border'
            }`}
          >
            <Eye className="w-4 h-4" />
            Preview
          </button>
        </div>

        {activeTab === 'edit' ? (
          <form onSubmit={handleSave} className="space-y-6">
            {/* Tags */}
            <div className="bg-bg-secondary border border-border rounded-2xl p-6">
              <label className="block text-sm font-semibold text-text-primary mb-2">
                Tags (comma-separated)
              </label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="python, ai, machine-learning, api"
                className="w-full px-4 py-3 bg-bg-primary border border-border rounded-xl text-text-primary placeholder:text-text-muted text-sm focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-colors"
              />
            </div>

            {/* Bilingual titles and summaries */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Vietnamese */}
              <div className="bg-bg-secondary border border-border rounded-2xl p-6 space-y-4">
                <h3 className="font-semibold text-text-primary flex items-center gap-2">
                  <span className="px-2 py-0.5 bg-accent text-bg-primary text-xs rounded font-bold">VI</span>
                  Tiếng Việt
                </h3>
                <div>
                  <label className="block text-xs text-text-muted mb-1.5">Tiêu đề</label>
                  <input
                    type="text"
                    value={titleVi}
                    onChange={(e) => setTitleVi(e.target.value)}
                    className="w-full px-3 py-2.5 bg-bg-primary border border-border rounded-xl text-text-primary text-sm focus:outline-none focus:border-accent transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs text-text-muted mb-1.5">Tóm tắt</label>
                  <textarea
                    value={summaryVi}
                    onChange={(e) => setSummaryVi(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2.5 bg-bg-primary border border-border rounded-xl text-text-primary text-sm resize-none focus:outline-none focus:border-accent transition-colors"
                  />
                </div>
              </div>

              {/* English */}
              <div className="bg-bg-secondary border border-border rounded-2xl p-6 space-y-4">
                <h3 className="font-semibold text-text-primary flex items-center gap-2">
                  <span className="px-2 py-0.5 bg-blue-500 text-white text-xs rounded font-bold">EN</span>
                  English
                </h3>
                <div>
                  <label className="block text-xs text-text-muted mb-1.5">Title</label>
                  <input
                    type="text"
                    value={titleEn}
                    onChange={(e) => setTitleEn(e.target.value)}
                    className="w-full px-3 py-2.5 bg-bg-primary border border-border rounded-xl text-text-primary text-sm focus:outline-none focus:border-accent transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs text-text-muted mb-1.5">Summary</label>
                  <textarea
                    value={summaryEn}
                    onChange={(e) => setSummaryEn(e.target.value)}
                    rows={3}
                    className="w-full px-3 py-2.5 bg-bg-primary border border-border rounded-xl text-text-primary text-sm resize-none focus:outline-none focus:border-accent transition-colors"
                  />
                </div>
              </div>
            </div>

            {/* Content editors */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-bg-secondary border border-border rounded-2xl p-6">
                <label className="flex items-center gap-2 text-sm font-semibold text-text-primary mb-3">
                  <span className="px-2 py-0.5 bg-accent text-bg-primary text-xs rounded font-bold">VI</span>
                  Nội dung (Markdown)
                </label>
                <textarea
                  value={contentVi}
                  onChange={(e) => setContentVi(e.target.value)}
                  rows={20}
                  className="w-full px-3 py-2.5 bg-bg-primary border border-border rounded-xl text-text-primary text-sm font-mono resize-y focus:outline-none focus:border-accent transition-colors"
                />
              </div>

              <div className="bg-bg-secondary border border-border rounded-2xl p-6">
                <label className="flex items-center gap-2 text-sm font-semibold text-text-primary mb-3">
                  <span className="px-2 py-0.5 bg-blue-500 text-white text-xs rounded font-bold">EN</span>
                  Content (Markdown)
                </label>
                <textarea
                  value={contentEn}
                  onChange={(e) => setContentEn(e.target.value)}
                  rows={20}
                  className="w-full px-3 py-2.5 bg-bg-primary border border-border rounded-xl text-text-primary text-sm font-mono resize-y focus:outline-none focus:border-accent transition-colors"
                />
              </div>
            </div>

            {/* Save button */}
            <div className="flex items-center gap-4">
              <button
                type="submit"
                disabled={saving}
                className="flex items-center gap-2 px-6 py-3 bg-accent hover:bg-accent-light disabled:opacity-60 text-bg-primary font-semibold rounded-xl transition-colors"
              >
                <Save className="w-4 h-4" />
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
            </div>
          </form>
        ) : (
          /* Preview mode */
          <div>
            <div className="flex items-center gap-2 mb-6">
              <Languages className="w-4 h-4 text-accent" />
              <span className="text-text-secondary text-sm">Preview Language:</span>
              <div className="flex gap-1 bg-bg-secondary rounded-lg p-1">
                <button
                  onClick={() => setPreviewLang('vi')}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    previewLang === 'vi' ? 'bg-accent text-bg-primary' : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  VI
                </button>
                <button
                  onClick={() => setPreviewLang('en')}
                  className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    previewLang === 'en' ? 'bg-accent text-bg-primary' : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  EN
                </button>
              </div>
            </div>

            <div className="bg-bg-secondary border border-border rounded-2xl p-8 max-w-4xl">
              <h1 className="text-3xl font-bold text-text-primary mb-3">{previewTitle}</h1>
              {previewSummary && (
                <p className="text-text-secondary text-lg mb-6 border-l-4 border-accent pl-4">{previewSummary}</p>
              )}
              {previewContent ? (
                <MarkdownRenderer content={previewContent} />
              ) : (
                <p className="text-text-muted italic">No content yet.</p>
              )}
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
