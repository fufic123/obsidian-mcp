"""Shared helpers for note models."""

from datetime import date
from enum import Enum
from re import sub
from typing import Any


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = sub(r"[^\w\s-]", "", text)
    return sub(r"[-\s]+", "-", text).strip("-")


def render_frontmatter(fields: dict[str, Any]) -> str:
    """Render a dict as YAML frontmatter block."""
    lines = ["---"]
    for key, value in fields.items():
        if value is None:
            continue
        elif isinstance(value, list):
            lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
        elif isinstance(value, date):
            lines.append(f"{key}: {value.isoformat()}")
        elif isinstance(value, Enum):
            lines.append(f"{key}: {value.value}")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)
