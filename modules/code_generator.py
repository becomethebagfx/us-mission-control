"""
Website Builder — Code Generator
Parses LLM plans into concrete file changes.
"""

import re
from typing import Optional


def apply_plan(plan: list, site_html: dict) -> list:
    """Apply a plan to site HTML files.

    Args:
        plan: List of change objects from LLM
            [{"file": str, "action": str, "old_text": str, "new_text": str, "selector": str}]
        site_html: Dict of {file_path: html_content}

    Returns:
        List of {"path": str, "content": str, "action": str, "description": str}
    """
    changes = []

    for step in plan:
        file_path = step.get("file", "")
        action = step.get("action", "replace")
        old_text = step.get("old_text", "")
        new_text = step.get("new_text", "")
        selector = step.get("selector", "")

        # Normalize file path
        if not file_path.startswith("public/"):
            file_path = f"public/{file_path}"

        # Get current content
        content = site_html.get(file_path)
        if content is None:
            # Try without public/ prefix
            alt_path = file_path.replace("public/", "", 1)
            content = site_html.get(alt_path)
            if content is None:
                changes.append({
                    "path": file_path,
                    "content": None,
                    "action": "error",
                    "description": f"File not found: {file_path}",
                })
                continue

        if action == "replace" and old_text and new_text:
            new_content = content.replace(old_text, new_text, 1)
            if new_content == content:
                changes.append({
                    "path": file_path,
                    "content": None,
                    "action": "error",
                    "description": f"Could not find text to replace in {file_path}",
                })
                continue
            changes.append({
                "path": file_path,
                "content": new_content,
                "action": "replace",
                "description": selector or f"Replace text in {file_path}",
            })

        elif action == "insert" and new_text:
            # Insert after old_text (marker)
            if old_text:
                idx = content.find(old_text)
                if idx == -1:
                    changes.append({
                        "path": file_path,
                        "content": None,
                        "action": "error",
                        "description": f"Could not find insertion point in {file_path}",
                    })
                    continue
                insert_pos = idx + len(old_text)
                new_content = content[:insert_pos] + new_text + content[insert_pos:]
            else:
                # Append before </body>
                new_content = content.replace("</body>", new_text + "\n</body>")
            changes.append({
                "path": file_path,
                "content": new_content,
                "action": "insert",
                "description": selector or f"Insert content in {file_path}",
            })

        elif action == "delete" and old_text:
            new_content = content.replace(old_text, "", 1)
            changes.append({
                "path": file_path,
                "content": new_content,
                "action": "delete",
                "description": selector or f"Remove content from {file_path}",
            })

    return changes


def validate_html(html: str) -> list:
    """Basic HTML validation. Returns list of warnings."""
    warnings = []

    # Check for unclosed tags (simplified)
    void_elements = {"br", "hr", "img", "input", "meta", "link", "area", "base", "col", "embed", "source", "track", "wbr"}
    open_tags = re.findall(r"<([a-z][a-z0-9]*)\b[^>]*(?<!/)>", html, re.IGNORECASE)
    close_tags = re.findall(r"</([a-z][a-z0-9]*)>", html, re.IGNORECASE)

    open_stack = []
    for tag in open_tags:
        tag_lower = tag.lower()
        if tag_lower not in void_elements:
            open_stack.append(tag_lower)

    for tag in close_tags:
        tag_lower = tag.lower()
        if tag_lower in open_stack:
            open_stack.remove(tag_lower)

    if open_stack:
        warnings.append(f"Potentially unclosed tags: {', '.join(open_stack[:5])}")

    return warnings


def generate_diff_preview(old_content: str, new_content: str, context_lines: int = 3) -> str:
    """Generate a simple diff preview for display."""
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()

    diff_parts = []
    i = 0
    j = 0

    while i < len(old_lines) and j < len(new_lines):
        if old_lines[i] == new_lines[j]:
            i += 1
            j += 1
            continue

        # Found a difference — show context
        start = max(0, i - context_lines)
        diff_parts.append(f"--- Line {i + 1} ---")
        for k in range(start, i):
            diff_parts.append(f"  {old_lines[k]}")
        # Show removed lines
        removed_start = i
        while i < len(old_lines) and (j >= len(new_lines) or old_lines[i] != new_lines[j]):
            diff_parts.append(f"- {old_lines[i]}")
            i += 1
        # Show added lines
        added_start = j
        while j < len(new_lines) and (i >= len(old_lines) or new_lines[j] != old_lines[i]):
            diff_parts.append(f"+ {new_lines[j]}")
            j += 1
        break  # Show first diff only for preview

    if not diff_parts:
        return "No visible changes"

    return "\n".join(diff_parts[:20])  # Limit preview length
