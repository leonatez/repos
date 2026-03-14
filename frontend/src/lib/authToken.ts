/**
 * Module-level token cache — set by AuthContext on every session change.
 * Allows api/client.ts to read the token synchronously without calling
 * supabase.auth.getSession() (which can hang if Supabase is slow).
 */
let currentToken: string | null = null

export function setAuthToken(token: string | null) {
  currentToken = token
}

export function getAuthToken(): string | null {
  return currentToken
}
