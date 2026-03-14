import { useState, FormEvent } from 'react'
import { Navigate, Link } from 'react-router-dom'
import { Github, Eye, EyeOff, AlertCircle } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

type Mode = 'login' | 'signup'

export default function LoginPage() {
  const { user, loading: authLoading, login, signup } = useAuth()
  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  if (!authLoading && user) {
    return <Navigate to="/" replace />
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setLoading(true)

    try {
      if (mode === 'login') {
        await login(email, password)
      } else {
        await signup(email, password, username)
        setSuccess('Account created! Please check your email to confirm your account.')
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'An error occurred'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-bg-primary flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="inline-flex items-center gap-2 mb-6">
            <div className="w-10 h-10 bg-accent rounded-xl flex items-center justify-center">
              <Github className="w-6 h-6 text-bg-primary" />
            </div>
            <span className="font-bold text-text-primary text-xl">
              <span className="text-accent">AI</span> Digest
            </span>
          </Link>
          <h1 className="text-2xl font-bold text-text-primary">
            {mode === 'login' ? 'Welcome back' : 'Create an account'}
          </h1>
          <p className="text-text-secondary mt-2 text-sm">
            {mode === 'login'
              ? 'Sign in to like, save, and comment on articles'
              : 'Join to like, save, and comment on articles'}
          </p>
        </div>

        {/* Form card */}
        <div className="bg-bg-secondary border border-border rounded-2xl p-8">
          {error && (
            <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-xl mb-6">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}

          {success && (
            <div className="p-4 bg-accent/10 border border-accent/30 rounded-xl mb-6">
              <p className="text-accent text-sm">{success}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {mode === 'signup' && (
              <div>
                <label className="block text-sm font-medium text-text-secondary mb-2">
                  Username
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="your_username"
                  className="w-full px-4 py-3 bg-bg-primary border border-border rounded-xl text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-colors"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className="w-full px-4 py-3 bg-bg-primary border border-border rounded-xl text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-colors"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  minLength={6}
                  className="w-full px-4 py-3 pr-12 bg-bg-primary border border-border rounded-xl text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-colors"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary p-1"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-accent hover:bg-accent-light disabled:opacity-60 disabled:cursor-not-allowed text-bg-primary font-semibold rounded-xl transition-colors text-sm"
            >
              {loading
                ? (mode === 'login' ? 'Signing in...' : 'Creating account...')
                : (mode === 'login' ? 'Sign In' : 'Create Account')
              }
            </button>
          </form>

          {/* Mode toggle */}
          <div className="mt-6 text-center text-sm text-text-muted">
            {mode === 'login' ? (
              <>
                Don't have an account?{' '}
                <button
                  onClick={() => { setMode('signup'); setError(null); setSuccess(null) }}
                  className="text-accent hover:underline font-medium"
                >
                  Sign up
                </button>
              </>
            ) : (
              <>
                Already have an account?{' '}
                <button
                  onClick={() => { setMode('login'); setError(null); setSuccess(null) }}
                  className="text-accent hover:underline font-medium"
                >
                  Sign in
                </button>
              </>
            )}
          </div>
        </div>

        <div className="text-center mt-6">
          <Link to="/" className="text-text-muted hover:text-text-secondary text-sm transition-colors">
            ← Back to homepage
          </Link>
        </div>
      </div>
    </main>
  )
}
