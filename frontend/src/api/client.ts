import axios from 'axios'
import { getAuthToken } from '../lib/authToken'

const apiClient = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Attach Supabase JWT token to every request (synchronous — no async hang)
apiClient.interceptors.request.use((config) => {
  const token = getAuthToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
    console.debug(`[API] ${config.method?.toUpperCase()} ${config.url} — JWT attached`)
  } else {
    console.warn(`[API] ${config.method?.toUpperCase()} ${config.url} — no session, request will be unauthenticated`)
  }
  return config
})

// Log responses and handle auth errors globally
apiClient.interceptors.response.use(
  (response) => {
    console.debug(`[API] ← ${response.status} ${response.config.url}`)
    return response
  },
  (error) => {
    const status = error.response?.status
    const url = error.config?.url
    const detail = error.response?.data?.detail ?? error.message
    console.error(`[API] ✗ ${status ?? 'ERR'} ${url} — ${detail}`)
    return Promise.reject(error)
  }
)

export default apiClient

// ─── API Functions ────────────────────────────────────────────────────────────

export const postsApi = {
  list: (limit = 12, offset = 0) =>
    apiClient.get('/posts', { params: { limit, offset } }),

  getBySlug: (slug: string) =>
    apiClient.get(`/posts/${slug}`),

  toggleLike: (postId: string) =>
    apiClient.post(`/posts/${postId}/like`),

  toggleSave: (postId: string) =>
    apiClient.post(`/posts/${postId}/save`),
}

export const tagsApi = {
  list: () => apiClient.get('/tags'),
  getPostsByTag: (slug: string, limit = 12, offset = 0) =>
    apiClient.get(`/tags/${slug}/posts`, { params: { limit, offset } }),
}

export const commentsApi = {
  list: (postId: string) =>
    apiClient.get(`/posts/${postId}/comments`),

  create: (postId: string, content: string) =>
    apiClient.post(`/posts/${postId}/comments`, { content }),
}

export const searchApi = {
  search: (q: string, limit = 12, offset = 0) =>
    apiClient.get('/search', { params: { q, limit, offset } }),
}

export const favoritesApi = {
  list: (limit = 12, offset = 0) =>
    apiClient.get('/favorites', { params: { limit, offset } }),
}

export const adminApi = {
  submit: (text: string) =>
    apiClient.post('/admin/submit', { text }),

  listPosts: (limit = 20, offset = 0) =>
    apiClient.get('/admin/posts', { params: { limit, offset } }),

  updatePost: (id: string, data: Record<string, unknown>) =>
    apiClient.put(`/admin/posts/${id}`, data),

  publishPost: (id: string) =>
    apiClient.post(`/admin/posts/${id}/publish`),

  deleteComment: (id: string) =>
    apiClient.delete(`/admin/comments/${id}`),
}
