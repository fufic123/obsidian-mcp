"""ConversationSummary model — Q&A summary of an AI conversation."""

from datetime import date

from pydantic import BaseModel, Field

from app.domain.interfaces.note import INote
from app.domain.models.base import render_frontmatter, slugify


class ConversationSummary(BaseModel, INote):
    """Q&A summary of an AI conversation."""

    title: str
    key_points: list[str]
    full_content: str
    project: str | None = None
    tags: list[str] = Field(default_factory=list)
    created: date = Field(default_factory=date.today)

    def frontmatter(self) -> dict[str, object]:
        return {
            "name": self.title,
            "description": "; ".join(self.key_points[:3]),
            "type": "conversation",
            "project": self.project,
            "tags": self.tags,
            "created": self.created,
        }

    def to_markdown(self) -> str:
        fm = render_frontmatter(self.frontmatter())
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
        return slugify(self.title)
