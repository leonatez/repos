from datetime import datetime
from urllib.parse import urlparse


def generate_github_thumbnail(repo_url: str) -> str:
    """Generate GitHub OpenGraph thumbnail URL with date-based cache busting."""
    try:
        parts = urlparse(repo_url).path.strip("/").split("/")
        owner = parts[0]
        repo = parts[1]
        date_hash = datetime.utcnow().strftime("%Y%m%d")
        return f"https://opengraph.githubassets.com/{date_hash}/{owner}/{repo}"
    except Exception:
        return "/static/default-repo-thumbnail.png"
