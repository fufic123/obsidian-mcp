"""DailyNote model — daily journal entry."""

from datetime import date

from pydantic import BaseModel, Field

from app.domain.interfaces.note import INote
from app.domain.models.base import render_frontmatter, slugify


class DailyNote(BaseModel, INote):
    """Daily journal entry."""

    content: str = ""
    note_date: date = Field(default_factory=date.today)

    def frontmatter(self) -> dict[str, object]:
        return {
            "name": self.note_date.isoformat(),
            "description": f"Daily note for {self.note_date.isoformat()}",
            "type": "daily",
            "tags": [],
            "created": self.note_date,
        }

    def to_markdown(self) -> str:
        fm = render_frontmatter(self.frontmatter())
        body = self.content or f"# {self.note_date.isoformat()}\n"
        return f"{fm}\n\n{body}\n"

    @property
    def slug(self) -> str:
        return slugify(self.note_date.isoformat())
