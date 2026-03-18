import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL as string
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY as string

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error(
    'Missing Supabase env vars. Create frontend/.env with VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.'
  )
}

const COOKIE_MAX_AGE = 60 * 60 * 24 * 30 // 30 days in seconds

const isSecure = typeof location !== 'undefined' && location.protocol === 'https:'

function getCookie(name: string): string | null {
  try {
    const match = document.cookie.match(new RegExp('(?:^|;\\s*)' + name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '=([^;]*)'))
    return match ? decodeURIComponent(match[1]) : null
  } catch {
    return null
  }
}

function setCookie(name: string, value: string) {
  const secure = isSecure ? ';Secure' : ''
  document.cookie = `${name}=${encodeURIComponent(value)};max-age=${COOKIE_MAX_AGE};path=/;SameSite=Lax${secure}`
}

function deleteCookie(name: string) {
  document.cookie = `${name}=;max-age=0;path=/`
}

const cookieStorage = {
  getItem(key: string): string | null {
    return getCookie(key)
  },
  setItem(key: string, value: string): void {
    setCookie(key, value)
  },
  removeItem(key: string): void {
    deleteCookie(key)
  },
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    storage: cookieStorage,
    persistSession: true,
    autoRefreshToken: true,
  },
})
