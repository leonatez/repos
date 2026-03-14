import json
import re
from typing import List, Optional

import google.generativeai as genai

from config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

MODEL = "gemini-3.1-flash-lite-preview"

# Matches https://github.com/owner/repo  (owner + repo — preferred)
_GITHUB_REPO_RE = re.compile(r"https?://github\.com/([\w\-\.]+)/([\w\-\.]+)")
# Matches https://github.com/owner  or  https://github.com/owner/  (org/user only)
_GITHUB_ORG_RE = re.compile(r"https?://github\.com/([\w\-\.]+)/?(?!\S)")


def extract_github_urls(text: str) -> List[str]:
    """
    Extract all unique GitHub URLs from the input text.

    Finds both full repo URLs (github.com/owner/repo) and bare org/user URLs
    (github.com/owner or github.com/owner/).  Deduplicates and returns in
    order of appearance.

    Falls back to Gemini when regex finds nothing (handles shortened links, etc.)
    """
    seen: dict[str, bool] = {}

    # Full repo URLs first (owner/repo)
    for owner, repo in _GITHUB_REPO_RE.findall(text):
        url = f"https://github.com/{owner}/{repo}"
        seen[url] = True

    # Org/user-only URLs — only if not already covered by a repo match
    for m in _GITHUB_ORG_RE.finditer(text):
        owner = m.group(1)
        org_url = f"https://github.com/{owner}"
        # Skip if we already have a repo URL for this owner, or if it's a common non-org path
        if org_url not in seen and not any(u.startswith(org_url + "/") for u in seen):
            seen[org_url] = True

    if seen:
        return list(seen.keys())

    # Gemini fallback — only when regex found nothing (shortened links, bare names, etc.)
    prompt = f"""You are a URL extraction assistant. Extract ALL GitHub repository URLs from the text below.

Text:
{text}

Instructions:
- Find every GitHub repository URL (format: https://github.com/owner/repo)
- Include only repository root URLs, not links to files, issues, or PRs
- Return one URL per line
- If no GitHub repository URL exists, return exactly: NONE

Response:"""

    try:
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(prompt)
        lines = response.text.strip().splitlines()
        urls = []
        gemini_seen: set[str] = set()
        for line in lines:
            line = line.strip()
            if not line or line == "NONE":
                continue
            m = _GITHUB_REPO_RE.search(line)
            if m:
                url = f"https://github.com/{m.group(1)}/{m.group(2)}"
                if url not in gemini_seen:
                    gemini_seen.add(url)
                    urls.append(url)
        return urls
    except Exception:
        return []


# Keep the single-URL variant for backward compatibility
def extract_github_url(text: str) -> Optional[str]:
    urls = extract_github_urls(text)
    return urls[0] if urls else None


async def analyze_and_generate_article(repo_info: dict) -> dict:
    """
    Use Gemini to analyze a GitHub repository and generate a bilingual
    (Vietnamese + English) blog article.
    Returns a dict with title_vi, title_en, summary_vi, summary_en,
    content_markdown_vi, content_markdown_en, and tags.
    """
    repo_context = f"""
Repository Name: {repo_info['name']}
GitHub URL: {repo_info['url']}
Owner: {repo_info['owner']}
Description: {repo_info['description']}
Primary Language: {repo_info['language']}
Stars: {repo_info['stars']}
Forks: {repo_info.get('forks', 0)}
Topics/Tags: {', '.join(repo_info.get('topics', []))}
License: {repo_info.get('license', 'Not specified')}
Homepage: {repo_info.get('homepage', '')}

README Content:
{repo_info.get('readme', 'No README available')}
"""

    prompt = f"""You are an expert technical writer creating a bilingual blog article about a GitHub repository for a tech magazine targeting Vietnamese developers.

Here is the repository information:
{repo_context}

Please analyze this repository thoroughly and create a comprehensive, high-quality bilingual blog article. Your response must be a valid JSON object with exactly these fields:

{{
  "title_vi": "Tiêu đề bài viết bằng tiếng Việt (hấp dẫn, SEO-friendly)",
  "title_en": "Article title in English (engaging, SEO-friendly)",
  "summary_vi": "Tóm tắt ngắn gọn 2-3 câu bằng tiếng Việt mô tả repo này làm gì và tại sao nó thú vị",
  "summary_en": "Short 2-3 sentence summary in English describing what this repo does and why it's interesting",
  "content_markdown_vi": "Nội dung bài viết đầy đủ bằng tiếng Việt (markdown format)",
  "content_markdown_en": "Full article content in English (markdown format)",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
}}

Requirements for the article content (both languages):
1. **Introduction** — Hook the reader, explain what the project is
2. **Problem Statement** — What problem does this project solve?
3. **Key Features** — Bullet list of the most impressive features
4. **How It Works** — Technical explanation of the architecture/approach
5. **Example Usage** — Code examples or usage instructions from the README
6. **Why It's Interesting** — Your analysis of why developers should care
7. **GitHub Repository** — Link back to the repo

For tags: generate 5-8 relevant technical tags (e.g., "python", "ai", "machine-learning", "api", etc.)

The Vietnamese content should be natural, fluent Vietnamese — not a literal translation.
The English content should be engaging tech journalism style.
Each article should be at least 800 words per language.

Return ONLY the JSON object, no other text."""

    model = genai.GenerativeModel(
        MODEL,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            max_output_tokens=8192,
        ),
    )

    response = model.generate_content(prompt)
    collected_text = response.text.strip()

    # Strip markdown code fences if present
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", collected_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        json_match = re.search(r"\{.*\}", collected_text, re.DOTALL)
        json_str = json_match.group(0) if json_match else collected_text

    try:
        result = json.loads(json_str)
    except json.JSONDecodeError:
        result = {
            "title_vi": f"Khám phá {repo_info['name']}: {repo_info.get('description', 'Dự án mã nguồn mở thú vị')}",
            "title_en": f"Exploring {repo_info['name']}: {repo_info.get('description', 'An interesting open source project')}",
            "summary_vi": repo_info.get("description", "Một dự án mã nguồn mở thú vị trên GitHub."),
            "summary_en": repo_info.get("description", "An interesting open source project on GitHub."),
            "content_markdown_vi": f"# {repo_info['name']}\n\n{repo_info.get('description', '')}\n\n{collected_text}",
            "content_markdown_en": f"# {repo_info['name']}\n\n{repo_info.get('description', '')}\n\n{collected_text}",
            "tags": repo_info.get("topics", ["github", "open-source"])[:8],
        }

    if not isinstance(result.get("tags"), list):
        result["tags"] = repo_info.get("topics", ["github", "open-source"])[:8]

    return result
