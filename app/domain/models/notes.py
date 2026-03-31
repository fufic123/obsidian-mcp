"""Note models for all vault note types."""

from abc import ABC, abstractmethod
from datetime import date
from re import sub

from pydantic import BaseModel, Field


class INote(ABC):
    """Base contract for all vault note types."""

    @abstractmethod
    def to_markdown(self) -> str:
        """Render note as markdown string with frontmatter."""
        ...

    @abstractmethod
    def frontmatter(self) -> dict[str, object]:
        """Return frontmatter fields as dict."""
        ...

    @property
    @abstractmethod
    def slug(self) -> str:
        """URL-safe filename without extension."""
        ...


def _slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = sub(r"[^\w\s-]", "", text)
    return sub(r"[-\s]+", "-", text).strip("-")


def _render_frontmatter(fields: dict[str, object]) -> str:
    """Render a dict as YAML frontmatter block."""
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, list):
            lines.append(f"{key}: [{', '.join(str(v) for v in value)}]")
        elif isinstance(value, date):
            lines.append(f"{key}: {value.isoformat()}")
        elif value is None:
            continue
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


class HighlightNote(BaseModel, INote):
    """Atomic insight, decision or knowledge piece."""

    name: str
    description: str
    content: str
    tags: list[str] = Field(default_factory=list)
    project: str | None = None
    created: date = Field(default_factory=date.today)

    def frontmatter(self) -> dict[str, object]:
        """Return frontmatter fields."""
        return {
            "name": self.name,
            "description": self.description,
            "type": "highlight",
            "project": self.project,
            "tags": self.tags,
            "created": self.created,
        }

    def to_markdown(self) -> str:
        """Render as markdown with frontmatter."""
        return f"{_render_frontmatter(self.frontmatter())}\n\n{self.content}\n"

    @property
    def slug(self) -> str:
        """URL-safe filename."""
        return _slugify(self.name)


class CoreNote(BaseModel, INote):
    """Persistent context about the user."""

    name: str
    description: str
    content: str
    created: date = Field(default_factory=date.today)

    def frontmatter(self) -> dict[str, object]:
        """Return frontmatter fields."""
        return {
            "name": self.name,
            "description": self.description,
            "type": "core",
            "tags": [],
            "created": self.created,
        }

    def to_markdown(self) -> str:
        """Render as markdown with frontmatter."""
        return f"{_render_frontmatter(self.frontmatter())}\n\n{self.content}\n"

    @property
    def slug(self) -> str:
        """URL-safe filename."""
        return _slugify(self.name)


class ConversationSummary(BaseModel, INote):
    """Q&A summary of an AI conversation."""

    title: str
    key_points: list[str]
    full_content: str
    project: str | None = None
    tags: list[str] = Field(default_factory=list)
    created: date = Field(default_factory=date.today)

    def frontmatter(self) -> dict[str, object]:
        """Return frontmatter fields."""
        return {
            "name": self.title,
            "description": "; ".join(self.key_points[:3]),
            "type": "conversation",
            "project": self.project,
            "tags": self.tags,
            "created": self.created,
        }

    def to_markdown(self) -> str:
        """Render as callout-formatted markdown."""
        fm = _render_frontmatter(self.frontmatter())
        points = "\n".join(f"- {p}" for p in self.key_points)
        body = (
            f"## {self.title}\n\n"
            f"> [!summary] Key Points\n"
            f">\n"
            f"> {points}\n"
            f">\n"
            f"> > [!note]- Full Conversation\n"
            f"> > {self.full_content}\n"
        )
        return f"{fm}\n\n{body}\n"

    @property
    def slug(self) -> str:
        """URL-safe filename."""
        return _slugify(self.title)


class DailyNote(BaseModel, INote):
    """Daily journal entry."""

    content: str = ""
    note_date: date = Field(default_factory=date.today)

    def frontmatter(self) -> dict[str, object]:
        """Return frontmatter fields."""
        return {
            "name": self.note_date.isoformat(),
            "description": f"Daily note for {self.note_date.isoformat()}",
            "type": "daily",
            "tags": [],
            "created": self.note_date,
        }

    def to_markdown(self) -> str:
        """Render as markdown with frontmatter."""
        fm = _render_frontmatter(self.frontmatter())
        body = self.content or f"# {self.note_date.isoformat()}\n"
        return f"{fm}\n\n{body}\n"

    @property
    def slug(self) -> str:
        """Date-based filename."""
        return self.note_date.isoformat()


class TaskNote(BaseModel, INote):
    """Obsidian Tasks compatible task."""

    title: str
    due: date | None = None
    project: str | None = None
    done: bool = False
    created: date = Field(default_factory=date.today)

    def frontmatter(self) -> dict[str, object]:
        """Return frontmatter fields."""
        return {
            "name": self.title,
            "description": self.title,
            "type": "task",
            "project": self.project,
            "tags": [],
            "created": self.created,
        }

    def to_markdown(self) -> str:
        """Render as Obsidian Tasks format."""
        fm = _render_frontmatter(self.frontmatter())
        checkbox = "x" if self.done else " "
        line = f"- [{checkbox}] {self.title}"
        if self.due:
            line += f" 📅 {self.due.isoformat()}"
        if self.project:
            line += f" #project/{self.project}"
        return f"{fm}\n\n{line}\n"

    @property
    def slug(self) -> str:
        """URL-safe filename."""
        return _slugify(self.title)
