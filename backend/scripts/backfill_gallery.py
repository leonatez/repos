"""
Backfill gallery_images for existing posts by re-fetching each repo's README from GitHub.

Usage (run from backend/ directory):
    python -m scripts.backfill_gallery           # only posts with empty gallery_images
    python -m scripts.backfill_gallery --force   # refresh all posts

Always uses Supabase (ignores DATABASE env var — backfill is a one-off data repair).
"""
import asyncio
import base64
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from supabase import create_client
from config import settings
from services.github_service import extract_readme_images, parse_github_url


async def fetch_readme(owner: str, repo_name: str, client: httpx.AsyncClient) -> str:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "AI-GitHub-Digest/1.0",
    }
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    try:
        resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo_name}/readme",
            headers=headers,
        )
        resp.raise_for_status()
        encoded = resp.json().get("content", "")
        return base64.b64decode(encoded.replace("\n", "")).decode("utf-8", errors="replace")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return ""
        raise
    except Exception:
        return ""


async def backfill(force: bool = False):
    sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

    # Fetch all posts with their github_url
    print("Fetching posts from Supabase...")
    result = sb.table("posts").select("id, slug, gallery_images, github_repositories(github_url)").execute()
    all_posts = result.data
    print(f"  Total posts: {len(all_posts)}")

    if force:
        to_update = all_posts
        print(f"  --force: will refresh all {len(to_update)} posts")
    else:
        to_update = [
            p for p in all_posts
            if not p.get("gallery_images") or p["gallery_images"] == [] or p["gallery_images"] == "[]"
        ]
        print(f"  Posts needing backfill: {len(to_update)}")

    if not to_update:
        print("Nothing to do.")
        return

    updated = 0
    skipped = 0
    errors = 0

    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, post in enumerate(to_update, 1):
            repo = post.get("github_repositories")
            github_url = repo.get("github_url") if repo else None

            if not github_url:
                print(f"  [{i}/{len(to_update)}] SKIP  {post['slug']} — no github_url")
                skipped += 1
                continue

            try:
                owner, repo_name = parse_github_url(github_url)
            except ValueError:
                print(f"  [{i}/{len(to_update)}] SKIP  {post['slug']} — invalid github_url: {github_url}")
                skipped += 1
                continue

            try:
                readme = await fetch_readme(owner, repo_name, client)
                images = extract_readme_images(readme, owner, repo_name)

                sb.table("posts").update({"gallery_images": images}).eq("id", post["id"]).execute()

                status = f"{len(images)} images" if images else "0 images"
                print(f"  [{i}/{len(to_update)}] OK    {post['slug']} — {status}")
                updated += 1

            except Exception as e:
                print(f"  [{i}/{len(to_update)}] ERROR {post['slug']} — {e}")
                errors += 1

            # Avoid hitting GitHub rate limit
            await asyncio.sleep(0.5)

    print(f"\nDone. updated={updated}  skipped={skipped}  errors={errors}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill gallery_images for all posts")
    parser.add_argument("--force", action="store_true", help="Refresh all posts, not just empty ones")
    args = parser.parse_args()
    asyncio.run(backfill(force=args.force))
