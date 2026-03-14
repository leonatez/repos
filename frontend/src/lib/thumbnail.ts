/**
 * Generate a GitHub OpenGraph thumbnail URL from a GitHub repo URL.
 * Uses today's date as a cache-busting hash.
 */
export function generateThumbnail(githubUrl: string): string {
  try {
    const url = new URL(githubUrl)
    const parts = url.pathname.replace(/^\//, '').split('/')
    const owner = parts[0]
    const repo = parts[1]
    if (!owner || !repo) throw new Error('Invalid URL')
    const today = new Date()
    const dateHash = today.toISOString().slice(0, 10).replace(/-/g, '')
    return `https://opengraph.githubassets.com/${dateHash}/${owner}/${repo}`
  } catch {
    return '/default-thumbnail.png'
  }
}

/**
 * Extract owner/repo from a GitHub URL.
 */
export function extractOwnerRepo(githubUrl: string): { owner: string; repo: string } | null {
  try {
    const url = new URL(githubUrl)
    const parts = url.pathname.replace(/^\//, '').split('/')
    if (parts.length >= 2) {
      return { owner: parts[0], repo: parts[1] }
    }
    return null
  } catch {
    return null
  }
}
