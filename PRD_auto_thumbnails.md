# Feature Specification — GitHub OpenGraph Thumbnail Support

## Feature Name
GitHub Repository Thumbnail via OpenGraph

---

# 1. Objective

Automatically generate a **thumbnail image for each article** using the GitHub OpenGraph image of the associated repository.

This avoids the need for manually uploading thumbnails while ensuring every article has a consistent visual preview.

The system will dynamically generate the thumbnail URL using the GitHub OpenGraph service and include a **date-based hash** to prevent caching issues.

---

# 2. Background

GitHub provides an OpenGraph image endpoint that generates preview images for repositories.

Example format:
https://opengraph.githubassets.com/<hash>/<owner>/<repo>

Example:https://opengraph.githubassets.com/1/crewAIInc/crewAI


The `<hash>` parameter is not validated and can be any string.  
It is commonly used to **bypass cache**.

To ensure the thumbnail updates if the repository changes, the system will generate a **date-based hash**.

Example:
https://opengraph.githubassets.com/20260313/crewAIInc/crewAI


---

# 3. Functional Requirements

### FR1 — Automatic Thumbnail Generation

When displaying an article, the system must automatically generate the thumbnail URL using:

- repository owner
- repository name
- current date

Example generated thumbnail:
https://opengraph.githubassets.com/20260313/crewAIInc/crewAI


---

### FR2 — No Thumbnail Storage

The system **must not store thumbnails in the database**.

Instead, the thumbnail URL is generated dynamically from the repository URL.

Example stored repository URL:
https://github.com/crewAIInc/crewAI


Generated thumbnail:
https://opengraph.githubassets.com/{date}/crewAIInc/crewAI


---

### FR3 — Date-Based Cache Busting

The `<hash>` parameter should be generated using the current date.

Format:
YYYYMMDD

Example: 20260313


This ensures:

- GitHub preview images refresh periodically
- browsers do not cache outdated thumbnails

---

# 4. Implementation Logic

## Step 1 — Parse Repository URL

Input:
https://github.com/owner/repo


Extract:


owner
repo


---

## Step 2 — Generate Date Hash

Example format:


YYYYMMDD


Example value:


20260313


---

## Step 3 — Generate OpenGraph Thumbnail URL

Final format:


https://opengraph.githubassets.com/{date}/{owner}/{repo}


Example:


https://opengraph.githubassets.com/20260313/crewAIInc/crewAI


---

# 5. Backend Helper Function (FastAPI / Python)

Example implementation:

```python
from datetime import datetime
from urllib.parse import urlparse

def generate_github_thumbnail(repo_url: str):
    parts = urlparse(repo_url).path.strip("/").split("/")
    owner = parts[0]
    repo = parts[1]

    date_hash = datetime.utcnow().strftime("%Y%m%d")

    return f"https://opengraph.githubassets.com/{date_hash}/{owner}/{repo}"

Example usage:

generate_github_thumbnail("https://github.com/crewAIInc/crewAI")

Output:

https://opengraph.githubassets.com/20260313/crewAIInc/crewAI
6. Frontend Usage

Use the generated URL as:

Article Thumbnail
<img src="{thumbnail_url}" />
Article Card Preview
<ArticleCard
  title="CrewAI: AI Agent Framework"
  thumbnail="https://opengraph.githubassets.com/20260313/crewAIInc/crewAI"
/>
SEO OpenGraph Meta Tags
<meta property="og:image"
content="https://opengraph.githubassets.com/20260313/crewAIInc/crewAI">

This ensures the correct image appears when the article is shared on:

Facebook

LinkedIn

Twitter

Slack

7. Performance Impact

The system does not download or store images.

The image is served directly from GitHub’s CDN:

githubassets.com

Advantages:

zero storage cost

zero image processing

minimal backend load

8. Edge Cases
Case 1 — Invalid GitHub URL

If parsing fails:

Fallback thumbnail:

/static/default-repo-thumbnail.png
Case 2 — Private Repository

GitHub OpenGraph may not render images for private repositories.

Fallback to default thumbnail.
