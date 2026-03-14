import re
import uuid


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    # Replace Vietnamese diacritics with ASCII equivalents
    replacements = {
        "à": "a", "á": "a", "ả": "a", "ã": "a", "ạ": "a",
        "ă": "a", "ắ": "a", "ặ": "a", "ẳ": "a", "ẵ": "a", "ằ": "a",
        "â": "a", "ấ": "a", "ầ": "a", "ẩ": "a", "ẫ": "a", "ậ": "a",
        "đ": "d",
        "è": "e", "é": "e", "ẻ": "e", "ẽ": "e", "ẹ": "e",
        "ê": "e", "ế": "e", "ề": "e", "ể": "e", "ễ": "e", "ệ": "e",
        "ì": "i", "í": "i", "ỉ": "i", "ĩ": "i", "ị": "i",
        "ò": "o", "ó": "o", "ỏ": "o", "õ": "o", "ọ": "o",
        "ô": "o", "ố": "o", "ồ": "o", "ổ": "o", "ỗ": "o", "ộ": "o",
        "ơ": "o", "ớ": "o", "ờ": "o", "ở": "o", "ỡ": "o", "ợ": "o",
        "ù": "u", "ú": "u", "ủ": "u", "ũ": "u", "ụ": "u",
        "ư": "u", "ứ": "u", "ừ": "u", "ử": "u", "ữ": "u", "ự": "u",
        "ỳ": "y", "ý": "y", "ỷ": "y", "ỹ": "y", "ỵ": "y",
    }
    for vi, en in replacements.items():
        text = text.replace(vi, en)

    # Replace non-alphanumeric with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text


def generate_unique_slug(title: str) -> str:
    """Generate a unique slug from a title by appending a short UUID suffix."""
    base_slug = slugify(title)
    # Truncate base slug to 80 chars to leave room for suffix
    if len(base_slug) > 80:
        base_slug = base_slug[:80].rstrip("-")
    suffix = str(uuid.uuid4())[:8]
    return f"{base_slug}-{suffix}"


def slugify_tag(name: str) -> str:
    """Generate a slug for a tag name."""
    return slugify(name)
