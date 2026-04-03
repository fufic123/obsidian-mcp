"""TaskNote model — task with frontmatter-based status."""

from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field

from app.domain.interfaces.note import INote
from app.domain.models.base import render_frontmatter, slugify
from app.domain.models.priority import Priority
from app.domain.models.task_status import TaskStatus


class TaskNote(BaseModel, INote):
    """Task note with frontmatter-based status."""

    title: str
    description: str = ""
    priority: Priority
    status: TaskStatus = TaskStatus.ACTIVE
    due: date | None = None
    project: str | None = None
    created: date = Field(default_factory=date.today)
    source_path: Path | None = Field(default=None, exclude=True)

    @property
    def done(self) -> bool:
        return self.status == TaskStatus.DONE

    def frontmatter(self) -> dict[str, object]:
        return {
            "name": self.title,
            "description": self.description or self.title,
            "type": "task",
            "status": self.status,
            "priority": self.priority,
            "project": self.project,
            "tags": [],
            "created": self.created,
        }

    def to_markdown(self) -> str:
        return f"{render_frontmatter(self.frontmatter())}\n"

    @property
    def slug(self) -> str:
        return slugify(self.title)
