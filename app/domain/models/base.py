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


def extract_frontmatter(content: str) -> dict[str, str]:
    """Extract key: value pairs from a YAML frontmatter block."""
    fields: dict[str, str] = {}
    in_fm = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped == "---":
            if not in_fm:
                in_fm = True
                continue
            break
        if in_fm and ":" in stripped:
            key, _, val = stripped.partition(":")
            fields[key.strip()] = val.strip()
    return fields


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
