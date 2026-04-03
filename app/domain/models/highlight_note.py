"""HighlightNote model — atomic insight, decision or knowledge piece."""

from datetime import date

from pydantic import BaseModel, Field

from app.domain.interfaces.note import INote
from app.domain.models.base import render_frontmatter, slugify


class HighlightNote(BaseModel, INote):
    """Atomic insight, decision or knowledge piece."""

    name: str
    description: str
    content: str
    tags: list[str] = Field(default_factory=list)
    project: str | None = None
    created: date = Field(default_factory=date.today)

    def frontmatter(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "type": "highlight",
            "project": self.project,
            "tags": self.tags,
            "created": self.created,
        }

    def to_markdown(self) -> str:
        return f"{render_frontmatter(self.frontmatter())}\n\n{self.content}\n"

    @property
    def slug(self) -> str:
        return slugify(self.name)
