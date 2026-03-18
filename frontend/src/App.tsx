import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { LanguageProvider } from './contexts/LanguageContext'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Article from './pages/Article'
import TagPage from './pages/TagPage'
import SearchPage from './pages/SearchPage'
import FavoritesPage from './pages/FavoritesPage'
import LoginPage from './pages/LoginPage'
import AdminPanel from './pages/admin/AdminPanel'
import NewPost from './pages/admin/NewPost'
import EditPost from './pages/admin/EditPost'

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-bg-primary text-text-primary">
      <Navbar />
      <div className="flex-1">{children}</div>
      <footer className="border-t border-border mt-16 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-text-muted text-sm">
            &copy; {new Date().getFullYear()} Repos. Powered by Claude AI.
          </p>
        </div>
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <LanguageProvider>
          <Routes>
            {/* Public routes with navbar */}
            <Route
              path="/"
              element={
                <Layout>
                  <Home />
                </Layout>
              }
            />
            <Route
              path="/articles/:slug"
              element={
                <Layout>
                  <Article />
                </Layout>
              }
            />
            <Route
              path="/tag/:slug"
              element={
                <Layout>
                  <TagPage />
                </Layout>
              }
            />
            <Route
              path="/search"
              element={
                <Layout>
                  <SearchPage />
                </Layout>
              }
            />
            <Route
              path="/favorites"
              element={
                <Layout>
                  <FavoritesPage />
                </Layout>
              }
            />

            {/* Auth routes (no navbar layout needed) */}
            <Route path="/login" element={<LoginPage />} />

            {/* Admin routes */}
            <Route
              path="/admin"
              element={
                <Layout>
                  <AdminPanel />
                </Layout>
              }
            />
            <Route
              path="/admin/new"
              element={
                <Layout>
                  <NewPost />
                </Layout>
              }
            />
            <Route
              path="/admin/posts/:id/edit"
              element={
                <Layout>
                  <EditPost />
                </Layout>
              }
            />
          </Routes>
        </LanguageProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
