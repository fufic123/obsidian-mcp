"""CoreNote model — persistent context about the user."""

from datetime import date

from pydantic import BaseModel, Field

from app.domain.interfaces.note import INote
from app.domain.models.base import render_frontmatter, slugify


class CoreNote(BaseModel, INote):
    """Persistent context about the user."""

    name: str
    description: str
    content: str
    created: date = Field(default_factory=date.today)

    def frontmatter(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "type": "core",
            "tags": [],
            "created": self.created,
        }

    def to_markdown(self) -> str:
        return f"{render_frontmatter(self.frontmatter())}\n\n{self.content}\n"

    @property
    def slug(self) -> str:
        return slugify(self.name)
