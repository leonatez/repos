"""
Quick validation: can Gemini reference + link to related posts when given context?

Run from /backend:
    python -m scripts.test_memory_prompt
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import google.generativeai as genai

# Load .env from the backend directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    sys.exit("ERROR: GEMINI_API_KEY not found in .env")

genai.configure(api_key=api_key)
MODEL = "gemini-2.0-flash"

DUMMY_RELATED_POSTS = [
    {
        "title_en": "Getting Started with LlamaIndex: Build Your First RAG Pipeline",
        "slug": "getting-started-llamaindex-rag-pipeline",
        "tags": ["rag", "llm", "python", "vector-db", "llamaindex"],
        "summary_en": "A hands-on guide to LlamaIndex: document loaders, vector indices, and query engines for building production-grade RAG systems.",
    },
    {
        "title_en": "Chroma vs Qdrant: Which Vector Database Should You Use?",
        "slug": "chroma-vs-qdrant-vector-database-comparison",
        "tags": ["vector-db", "embeddings", "python", "chroma", "qdrant"],
        "summary_en": "Benchmarks, tradeoffs, and use-case recommendations between two popular open-source vector databases.",
    },
    {
        "title_en": "OpenAI Function Calling: A Practical Guide",
        "slug": "openai-function-calling-practical-guide",
        "tags": ["openai", "llm", "function-calling", "python", "api"],
        "summary_en": "How to use OpenAI's function calling feature to build structured, tool-augmented LLM applications.",
    },
]

TOPIC_INPUT = """
LangChain just released v0.3 with a major refactor.
It's now the most popular framework for building LLM-powered apps —
agents, RAG pipelines, chains, tool use.
Over 80k GitHub stars. The new LCEL (LangChain Expression Language)
makes composing chains much cleaner.
"""


def build_related_context(posts: list) -> str:
    if not posts:
        return ""
    lines = ["--- RELATED ARTICLES ALREADY PUBLISHED ON THIS SITE ---"]
    for i, p in enumerate(posts, 1):
        lines.append(
            f"{i}. Title: \"{p['title_en']}\"\n"
            f"   URL: /posts/{p['slug']}\n"
            f"   Tags: {', '.join(p['tags'])}\n"
            f"   Summary: {p['summary_en']}"
        )
    lines.append("--- END RELATED ARTICLES ---")
    lines.append("")
    lines.append("Instructions for using related articles:")
    lines.append("- Where the topic overlaps with a related article, embed a markdown link: [Post Title](/posts/slug)")
    lines.append("- Draw natural comparisons (e.g. \"unlike LlamaIndex which we covered previously...\")")
    lines.append("- Do NOT re-explain concepts already covered in a linked post — refer readers there instead")
    lines.append("- Optionally add a '## Related Reading' section at the end with 2-3 of the most relevant links")
    return "\n".join(lines)


async def test_memory_prompt():
    related_block = build_related_context(DUMMY_RELATED_POSTS)

    prompt = f"""You are an expert technical writer for a bilingual tech magazine targeting Vietnamese developers.

An admin has pasted the following content as inspiration for a new article:

--- ORIGINAL CONTENT ---
{TOPIC_INPUT.strip()}
--- END ORIGINAL CONTENT ---

{related_block}

Write a SHORT English-only blog article (300-400 words, markdown format) about LangChain v0.3.
The article must naturally reference and link to at least 2 of the related articles above where relevant.

Return only the markdown article, no JSON."""

    print("=" * 60)
    print("PROMPT SENT TO GEMINI")
    print("=" * 60)
    print(prompt)
    print()

    model = genai.GenerativeModel(MODEL)
    response = model.generate_content(prompt)
    output = response.text.strip()

    print("=" * 60)
    print("GEMINI OUTPUT")
    print("=" * 60)
    print(output)
    print()

    # Quick validation checks
    print("=" * 60)
    print("VALIDATION")
    print("=" * 60)
    links_found = [slug for p in DUMMY_RELATED_POSTS if f"/posts/{p['slug']}" in output]
    print(f"Related posts linked: {len(links_found)}/{len(DUMMY_RELATED_POSTS)}")
    for slug in links_found:
        print(f"  ✓ /posts/{slug}")
    missing = [p["slug"] for p in DUMMY_RELATED_POSTS if f"/posts/{p['slug']}" not in output]
    for slug in missing:
        print(f"  - /posts/{slug}  (not linked)")
    passed = len(links_found) >= 2
    print()
    print(f"RESULT: {'PASS ✓' if passed else 'FAIL ✗'}  ({len(links_found)} links found, need >= 2)")


if __name__ == "__main__":
    asyncio.run(test_memory_prompt())
