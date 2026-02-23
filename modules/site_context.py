"""
Website Builder — Site Context
Reads target site HTML and builds context for the LLM.
"""

import re
from pathlib import Path
from typing import Optional

# Map site slugs to filesystem paths
WEBSITES_DIR = Path(__file__).parent.parent.parent.parent / "websites"

SITE_REGISTRY = {
    "us-exteriors": {
        "name": "US Exteriors",
        "url": "https://us-exteriors.onrender.com",
        "repo": "US-Websites/us-exteriors-site",
        "dir": "us-exteriors",
    },
    "us-drywall": {
        "name": "US Drywall",
        "url": "https://us-drywall.onrender.com",
        "repo": "US-Websites/us-drywall-site",
        "dir": "us-drywall",
    },
}


def get_available_sites() -> list:
    """Return list of available sites with metadata."""
    sites = []
    for slug, info in SITE_REGISTRY.items():
        site_dir = WEBSITES_DIR / info["dir"] / "public"
        pages = _get_page_inventory(site_dir) if site_dir.exists() else []
        sites.append({
            "slug": slug,
            "name": info["name"],
            "url": info["url"],
            "repo": info["repo"],
            "page_count": len(pages),
            "available": site_dir.exists(),
        })
    return sites


def get_site_context(site_slug: str) -> Optional[dict]:
    """Build full context for a site, for the LLM system prompt."""
    info = SITE_REGISTRY.get(site_slug)
    if not info:
        return None

    site_dir = WEBSITES_DIR / info["dir"] / "public"
    if not site_dir.exists():
        return None

    pages = _get_page_inventory(site_dir)

    return {
        "slug": site_slug,
        "name": info["name"],
        "url": info["url"],
        "repo": info["repo"],
        "pages": pages,
    }


def get_page_html(site_slug: str, page_path: str) -> Optional[str]:
    """Read the HTML content of a specific page."""
    info = SITE_REGISTRY.get(site_slug)
    if not info:
        return None

    site_dir = WEBSITES_DIR / info["dir"] / "public"
    # Normalize path
    if not page_path.endswith("index.html"):
        page_path = page_path.rstrip("/") + "/index.html"
    if page_path.startswith("/"):
        page_path = page_path[1:]

    full_path = site_dir / page_path
    if not full_path.exists():
        return None

    # Security: ensure path is within site_dir
    try:
        full_path.resolve().relative_to(site_dir.resolve())
    except ValueError:
        return None

    return full_path.read_text(encoding="utf-8")


def _get_page_inventory(site_dir: Path) -> list:
    """Scan a site directory and build a page inventory."""
    pages = []
    for html_file in sorted(site_dir.rglob("index.html")):
        rel_path = str(html_file.relative_to(site_dir))
        title = _extract_title(html_file)
        pages.append({
            "path": rel_path,
            "title": title,
            "size_kb": round(html_file.stat().st_size / 1024, 1),
        })
    return pages


def _extract_title(html_path: Path) -> str:
    """Extract the <title> from an HTML file."""
    try:
        content = html_path.read_text(encoding="utf-8")
        match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group(1).strip()
            # Clean up common patterns
            title = title.split(" — ")[0].split(" | ")[0].strip()
            return title
    except Exception:
        pass
    return "Untitled"
