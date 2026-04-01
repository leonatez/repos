"""
Post memory: builds the "related articles" context block injected into AI prompts.

Usage:
    from services.post_memory import build_related_context
    context = build_related_context(related_posts)   # "" if list is empty
"""


def build_related_context(related_posts: list) -> str:
    """
    Format a list of related post dicts into the prompt block Gemini uses
    to reference and link to existing articles.

    Each post dict must have: title_en, slug, summary_en, tags (list[str]).
    Returns an empty string when there are no related posts so callers can
    safely concatenate without guards.
    """
    if not related_posts:
        return ""

    lines = ["--- RELATED ARTICLES ALREADY PUBLISHED ON THIS SITE ---"]
    for i, p in enumerate(related_posts, 1):
        tag_str = ", ".join(p.get("tags", []))
        lines.append(
            f"{i}. Title: \"{p['title_en']}\"\n"
            f"   URL: /posts/{p['slug']}\n"
            f"   Tags: {tag_str}\n"
            f"   Summary: {p.get('summary_en', '')}"
        )
    lines += [
        "--- END RELATED ARTICLES ---",
        "",
        "Instructions for using related articles:",
        "- ONLY link to the exact URLs listed above. Do NOT invent, guess, or create any other internal links.",
        "- Where this topic overlaps with a related article, embed a markdown link using the exact URL: [Post Title](/posts/slug)",
        "- Draw natural comparisons where helpful (e.g. \"unlike LlamaIndex which we covered previously...\")",
        "- Do NOT re-explain concepts already covered in a linked post — refer readers there instead",
        "- Add a '## Related Reading' section at the end listing the most relevant 2-3 links from the list above only",
    ]
    return "\n".join(lines)
