"""TaskNote model — task with frontmatter-based status."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from pydantic import BaseModel, Field

from app.domain.interfaces.note import INote
from app.domain.models.base import extract_frontmatter, render_frontmatter, slugify
from app.domain.models.priority import Priority
from app.domain.models.task_status import TaskStatus

_VALID_PRIORITY_VALUES = {p.value for p in Priority}
_VALID_STATUS_VALUES = {s.value for s in TaskStatus}


class TaskNote(BaseModel, INote):
    """Task note with frontmatter-based status."""

    title: str
    description: str = ""
    implementation: str = ""  # AI-written notes on what was done
    priority: Priority
    status: TaskStatus = TaskStatus.ACTIVE
    due: date | None = None
    project: str | None = None
    created: date = Field(default_factory=date.today)
    source_path: Path | None = Field(default=None, exclude=True)

    @classmethod
    def from_content(cls, content: str, source_path: Path | None = None) -> TaskNote | None:
        """Parse a TaskNote from raw markdown content. Returns None if content is not a task."""
        fields = extract_frontmatter(content)
        title = fields.get("name", "")
        if not title:
            return None
        priority_val = fields.get("priority", "medium")
        status_val = fields.get("status", "active")
        due_val = fields.get("due")
        return cls(
            title=title,
            description=fields.get("description", ""),
            implementation=fields.get("implementation", ""),
            priority=Priority(priority_val)
            if priority_val in _VALID_PRIORITY_VALUES
            else Priority.MEDIUM,
            status=TaskStatus(status_val)
            if status_val in _VALID_STATUS_VALUES
            else TaskStatus.ACTIVE,
            due=date.fromisoformat(due_val) if due_val else None,
            project=fields.get("project") or None,
            created=date.fromisoformat(c) if (c := fields.get("created")) else date.today(),
            source_path=source_path,
        )

    @property
    def done(self) -> bool:
        return self.status == TaskStatus.DONE

    def frontmatter(self) -> dict[str, object]:
        return {
            "name": self.title,
            "description": self.description or self.title,
            "implementation": self.implementation,
            "type": "task",
            "status": self.status,
            "priority": self.priority,
            "due": self.due,
            "project": self.project,
            "tags": [],
            "created": self.created,
        }

    def to_markdown(self) -> str:
        return f"{render_frontmatter(self.frontmatter())}\n"

    @property
    def slug(self) -> str:
        return slugify(self.title)
