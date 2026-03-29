import base64
import re
import httpx
from urllib.parse import urlparse
from typing import Optional
from config import settings

_IMAGE_EXTENSIONS = r"\.(?:png|jpg|jpeg|gif|webp|svg|bmp|ico)"
_MD_ABS_IMG_RE = re.compile(
    r"!\[[^\]]*\]\((https?://[^\s)]+?" + _IMAGE_EXTENSIONS + r"[^\s)]*)\)",
    re.IGNORECASE,
)
_HTML_ABS_IMG_RE = re.compile(
    r'<img[^>]+src=["\']?(https?://[^\s"\'>\)]+)["\']?',
    re.IGNORECASE,
)
_MD_REL_IMG_RE = re.compile(
    r"!\[[^\]]*\]\((?!https?://)([^\s)\#?]+?" + _IMAGE_EXTENSIONS + r"[^\s)]*)\)",
    re.IGNORECASE,
)


def extract_readme_images(readme_content: str, owner: str, repo_name: str) -> list[str]:
    """Extract image URLs from README markdown. Converts relative paths to absolute raw.githubusercontent.com URLs."""
    seen: set[str] = set()
    images: list[str] = []

    def add(url: str) -> None:
        url = url.strip().rstrip(")")
        if url and url not in seen:
            seen.add(url)
            images.append(url)

    for m in _MD_ABS_IMG_RE.finditer(readme_content):
        add(m.group(1))

    for m in _HTML_ABS_IMG_RE.finditer(readme_content):
        url = m.group(1)
        if re.search(_IMAGE_EXTENSIONS, url, re.IGNORECASE) or "githubusercontent" in url:
            add(url)

    for m in _MD_REL_IMG_RE.finditer(readme_content):
        rel = m.group(1).lstrip("./")
        add(f"https://raw.githubusercontent.com/{owner}/{repo_name}/HEAD/{rel}")

    return images[:20]


def parse_github_url(github_url: str) -> tuple[str, str]:
    """Extract owner and repo name from GitHub URL."""
    parsed = urlparse(github_url)
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) < 2:
        raise ValueError(f"Invalid GitHub URL: {github_url}")
    owner = path_parts[0]
    repo = path_parts[1].removesuffix(".git")
    return owner, repo


async def fetch_repo_info(github_url: str) -> dict:
    """
    Fetch repository information from GitHub API.
    Returns dict with name, description, stars, language, topics,
    readme, url, owner, repo_name, gallery_images.
    """
    owner, repo_name = parse_github_url(github_url)

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "AI-GitHub-Digest/1.0",
    }
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Fetch repo metadata
        repo_resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo_name}",
            headers=headers,
        )
        repo_resp.raise_for_status()
        repo_data = repo_resp.json()

        # Fetch README
        readme_content = ""
        try:
            readme_resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo_name}/readme",
                headers=headers,
            )
            readme_resp.raise_for_status()
            readme_data = readme_resp.json()
            encoded_content = readme_data.get("content", "")
            # GitHub API returns base64 encoded content with newlines
            readme_content = base64.b64decode(
                encoded_content.replace("\n", "")
            ).decode("utf-8", errors="replace")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                readme_content = "No README available."
            else:
                readme_content = "Could not fetch README."
        except Exception:
            readme_content = "Could not fetch README."

        gallery_images = extract_readme_images(readme_content, owner, repo_name)

        return {
            "name": repo_data.get("name", repo_name),
            "description": repo_data.get("description") or "",
            "stars": repo_data.get("stargazers_count", 0),
            "forks": repo_data.get("forks_count", 0),
            "language": repo_data.get("language") or "Unknown",
            "topics": repo_data.get("topics", []),
            "readme": readme_content[:8000],  # Limit README length
            "url": repo_data.get("html_url", github_url),
            "owner": owner,
            "repo_name": repo_name,
            "homepage": repo_data.get("homepage") or "",
            "license": (repo_data.get("license") or {}).get("name", ""),
            "open_issues": repo_data.get("open_issues_count", 0),
            "watchers": repo_data.get("watchers_count", 0),
            "gallery_images": gallery_images,
        }
