import { useState, FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Search, Github, LogOut, Bookmark, Settings, Menu, X } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import LanguageToggle from './LanguageToggle'

export default function Navbar() {
  const { user, isAdmin, logout } = useAuth()
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [mobileOpen, setMobileOpen] = useState(false)

  const handleSearch = (e: FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`)
      setQuery('')
      setMobileOpen(false)
    }
  }

  return (
    <nav className="sticky top-0 z-50 bg-bg-primary/95 backdrop-blur-sm border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 shrink-0">
            <div className="w-8 h-8 bg-accent rounded-lg flex items-center justify-center">
              <Github className="w-5 h-5 text-bg-primary" />
            </div>
            <span className="font-bold text-text-primary text-lg hidden sm:block">
              Repos
            </span>
          </Link>

          {/* Desktop search */}
          <form onSubmit={handleSearch} className="hidden md:flex flex-1 max-w-xl mx-8">
            <div className="relative w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search articles, tags, repos..."
                className="w-full pl-10 pr-4 py-2 bg-bg-secondary border border-border rounded-lg text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-colors"
              />
            </div>
          </form>

          {/* Desktop nav items */}
          <div className="hidden md:flex items-center gap-4">
            <LanguageToggle />

            {user ? (
              <>
                <Link
                  to="/favorites"
                  className="text-text-secondary hover:text-accent transition-colors p-1.5 rounded-md hover:bg-bg-secondary"
                  title="Saved Articles"
                >
                  <Bookmark className="w-5 h-5" />
                </Link>

                {isAdmin && (
                  <Link
                    to="/admin"
                    className="text-text-secondary hover:text-accent transition-colors p-1.5 rounded-md hover:bg-bg-secondary"
                    title="Admin Panel"
                  >
                    <Settings className="w-5 h-5" />
                  </Link>
                )}

                <div className="flex items-center gap-2 pl-2 border-l border-border">
                  <span className="text-sm text-text-secondary">
                    {user.username || user.email?.split('@')[0]}
                  </span>
                  <button
                    onClick={logout}
                    className="text-text-secondary hover:text-red-400 transition-colors p-1.5 rounded-md hover:bg-bg-secondary"
                    title="Logout"
                  >
                    <LogOut className="w-5 h-5" />
                  </button>
                </div>
              </>
            ) : (
              <Link
                to="/login"
                className="px-4 py-2 bg-accent hover:bg-accent-light text-bg-primary font-medium text-sm rounded-lg transition-colors"
              >
                Sign In
              </Link>
            )}
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden text-text-secondary hover:text-text-primary p-2"
            onClick={() => setMobileOpen(!mobileOpen)}
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div className="md:hidden pb-4 space-y-3 border-t border-border pt-4">
            <form onSubmit={handleSearch} className="flex">
              <div className="relative w-full">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search articles..."
                  className="w-full pl-10 pr-4 py-2 bg-bg-secondary border border-border rounded-lg text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent"
                />
              </div>
            </form>

            <LanguageToggle />

            {user ? (
              <div className="flex flex-col gap-2">
                <Link
                  to="/favorites"
                  className="flex items-center gap-2 text-text-secondary hover:text-accent py-2"
                  onClick={() => setMobileOpen(false)}
                >
                  <Bookmark className="w-4 h-4" />
                  Saved Articles
                </Link>
                {isAdmin && (
                  <Link
                    to="/admin"
                    className="flex items-center gap-2 text-text-secondary hover:text-accent py-2"
                    onClick={() => setMobileOpen(false)}
                  >
                    <Settings className="w-4 h-4" />
                    Admin Panel
                  </Link>
                )}
                <button
                  onClick={() => { logout(); setMobileOpen(false) }}
                  className="flex items-center gap-2 text-red-400 py-2 text-left"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="block w-full text-center px-4 py-2 bg-accent text-bg-primary font-medium text-sm rounded-lg"
                onClick={() => setMobileOpen(false)}
              >
                Sign In
              </Link>
            )}
          </div>
        )}
      </div>
    </nav>
  )
}
