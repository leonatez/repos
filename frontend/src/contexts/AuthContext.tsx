// @refresh reset
import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { Session, User as SupabaseUser } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'
import { setAuthToken } from '../lib/authToken'
import { User } from '../types'

interface AuthContextValue {
  user: User | null
  session: Session | null
  loading: boolean
  isAdmin: boolean
  login: (email: string, password: string) => Promise<void>
  signup: (email: string, password: string, username?: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchUserProfile = useCallback(async (supabaseUser: SupabaseUser) => {
    console.log('[Auth] fetchUserProfile — id:', supabaseUser.id, 'email:', supabaseUser.email)
    try {
      const { data, error } = await supabase
        .from('users')
        .select('*')
        .eq('id', supabaseUser.id)
        .single()

      console.log('[Auth] users table row:', data, 'error:', error)

      if (data) {
        setUser({
          id: supabaseUser.id,
          email: supabaseUser.email ?? '',
          username: data.username,
          avatar_url: data.avatar_url,
          role: data.role,
        })
        console.log('[Auth] user set — role:', data.role)
      } else {
        console.warn('[Auth] no row in users table for this user — defaulting to role=user')
        setUser({
          id: supabaseUser.id,
          email: supabaseUser.email ?? '',
          role: 'user',
        })
      }
    } catch (err) {
      console.error('[Auth] fetchUserProfile threw:', err)
      setUser({
        id: supabaseUser.id,
        email: supabaseUser.email ?? '',
        role: 'user',
      })
    }
  }, [])

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session }, error }) => {
      console.log('[Auth] getSession —', session ? `user: ${session.user.email}` : 'no session', error ? `error: ${error.message}` : '')
      setAuthToken(session?.access_token ?? null)
      setSession(session)
      if (session?.user) {
        fetchUserProfile(session.user).finally(() => setLoading(false))
      } else {
        setLoading(false)
      }
    })

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('[Auth] onAuthStateChange —', event, session ? `user: ${session.user.email}` : 'no session')
        setAuthToken(session?.access_token ?? null)
        setSession(session)
        if (session?.user) {
          await fetchUserProfile(session.user)
        } else {
          setUser(null)
        }
        setLoading(false)
      }
    )

    return () => subscription.unsubscribe()
  }, [fetchUserProfile])

  const login = async (email: string, password: string) => {
    console.log('[Auth] login attempt —', email)
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) {
      console.error('[Auth] login failed —', error.message, error)
      throw error
    }
    console.log('[Auth] login success — session expires:', data.session?.expires_at)
  }

  const signup = async (email: string, password: string, username?: string) => {
    console.log('[Auth] signup attempt —', email)
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { username: username || email.split('@')[0] } },
    })
    if (error) {
      console.error('[Auth] signup failed —', error.message, error)
      throw error
    }
    console.log('[Auth] signup response — user:', data.user?.email, 'session:', data.session ? 'present' : 'null (email confirmation required)')
  }

  const logout = async () => {
    console.log('[Auth] logout')
    const { error } = await supabase.auth.signOut()
    if (error) throw error
    setAuthToken(null)
    setUser(null)
    setSession(null)
  }

  const isAdmin = user?.role === 'admin'

  return (
    <AuthContext.Provider value={{ user, session, loading, isAdmin, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
