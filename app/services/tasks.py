"""Task service — manages Obsidian Tasks format tasks."""

import re
from datetime import date
from pathlib import Path

from app.domain.exceptions.vault import VaultReadError
from app.domain.interfaces.vault import IVaultService
from app.domain.models.base import slugify as _slugify
from app.domain.models.priority import Priority
from app.domain.models.task_note import TaskNote
from app.domain.models.task_status import TaskStatus

_PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}

# Matches markdown links: [title](path)
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


class TaskService:
    """Manages tasks in Obsidian Tasks format."""

    def __init__(self, vault: IVaultService) -> None:
        self._vault = vault

    def get_task(self, title: str) -> TaskNote:
        """Return a parsed TaskNote by title (active or done)."""
        path = self.__resolve_path(title, anywhere=True)
        task = TaskNote.from_content(self._vault.read(path), source_path=path)
        if task is None:
            raise VaultReadError(f"Could not parse task: {title!r}")
        return task

    def create_task(
        self,
        title: str,
        description: str,
        priority: Priority,
        due: date | None = None,
        project: str | None = None,
    ) -> str:
        """Create a task note at tasks/{project}/slug.md. Returns the file path."""
        note = TaskNote(
            title=title, description=description, priority=priority, due=due, project=project
        )
        subfolder = project or "inbox"
        path = self._vault.tasks_path / subfolder / f"{note.slug}.md"
        self._vault.write(path, note.to_markdown())
        self.rebuild_index()
        return str(path)

    def complete_task(self, title: str) -> str:
        """Set status: done and move to archive/. Rebuilds index."""
        path = self.__resolve_path(title)
        content = self.__patch_frontmatter(self._vault.read(path), "status", TaskStatus.DONE)
        self._vault.write(path, content)
        archive_path = path.parent / "archive" / path.name
        self._vault.move(path, archive_path)
        self.rebuild_index()
        return str(archive_path)

    def reopen_task(self, title: str) -> str:
        """Set status: active and move back from archive/. Rebuilds index."""
        path = self.__resolve_path(title, anywhere=True)
        content = self.__patch_frontmatter(self._vault.read(path), "status", TaskStatus.ACTIVE)
        self._vault.write(path, content)
        if "archive" in path.parts:
            active_path = path.parent.parent / path.name
            self._vault.move(path, active_path)
        self.rebuild_index()
        return str(path)

    def update_task(
        self,
        title: str,
        new_title: str | None = None,
        description: str | None = None,
        priority: Priority | None = None,
        due: date | None = None,
        project: str | None = None,
    ) -> str:
        """Patch any frontmatter fields. Renames/moves file if title or project changes."""
        path = self.__resolve_path(title)
        content = self._vault.read(path)

        if description is not None:
            content = self.__patch_frontmatter(content, "description", description)
        if priority is not None:
            content = self.__patch_frontmatter(content, "priority", priority)
        if due is not None:
            content = self.__patch_frontmatter(content, "due", due.isoformat())
        if new_title is not None:
            content = self.__patch_frontmatter(content, "name", new_title)

        self._vault.write(path, content)

        new_path = self.__relocated_path(path, new_title or title, project)
        if new_path != path:
            self._vault.move(path, new_path)

        self.rebuild_index()
        return str(new_path)

    def delete_task(self, title: str) -> str:
        """Delete a task file (active or done). Rebuilds index."""
        path = self.__resolve_path(title, anywhere=True)
        self._vault.delete(path)
        self.rebuild_index()
        return str(path)

    def list_tasks(self, project: str | None = None) -> list[TaskNote]:
        """List open tasks sorted by priority."""
        self.rebuild_index()
        tasks: list[TaskNote] = []
        for f in self.__open_task_files():
            task = TaskNote.from_content(self._vault.read(f), source_path=f)
            if task and not task.done:
                if project is None or task.project == project:
                    tasks.append(task)
        tasks.sort(key=lambda t: _PRIORITY_ORDER[t.priority])
        return tasks

    def rebuild_index(self) -> str:
        """Regenerate tasks/TASKS.md. Source of truth = individual .md files."""
        by_project: dict[str, list[TaskNote]] = {}
        done_by_project: dict[str, list[TaskNote]] = {}

        for f in self._vault.list_files(self._vault.tasks_path, recursive=True):
            if f.name == "TASKS.md":
                continue
            try:
                task = TaskNote.from_content(self._vault.read(f), source_path=f)
                if not task:
                    continue
                key = task.project or "inbox"
                if "archive" in f.parts or task.done:
                    done_by_project.setdefault(key, []).append(task)
                else:
                    by_project.setdefault(key, []).append(task)
            except Exception:
                continue

        for tasks in by_project.values():
            tasks.sort(key=lambda t: _PRIORITY_ORDER[t.priority])

        lines = ["# Tasks\n"]
        lines += self.__render_active_section(by_project)
        lines += self.__render_done_section(done_by_project)

        content = "\n".join(lines)
        self._vault.write(self._vault.tasks_path / "TASKS.md", content)
        return content

    def __index_links(self) -> dict[str, Path]:
        """Return {title_slug: absolute_path} parsed from TASKS.md."""
        index_path = self._vault.tasks_path / "TASKS.md"
        if not self._vault.exists(index_path):
            return {}
        links: dict[str, Path] = {}
        for line in self._vault.read(index_path).splitlines():
            m = _LINK_RE.search(line)
            if m:
                slug = _slugify(m.group(1))
                links[slug] = self._vault.tasks_path / m.group(2)
        return links

    def __resolve_path(self, title: str, anywhere: bool = False) -> Path:
        """Resolve task file path from TASKS.md index. Raises VaultReadError if not found."""
        slug = _slugify(title)
        path = self.__index_links().get(slug)
        if path and self._vault.exists(path):
            if anywhere or "archive" not in path.parts:
                return path
        raise VaultReadError(f"Task not found: {title!r}")

    def __open_task_files(self) -> list[Path]:
        """Task files excluding TASKS.md and archive/ subfolders."""
        return [
            f
            for f in self._vault.list_files(self._vault.tasks_path, recursive=True)
            if f.name != "TASKS.md" and "archive" not in f.parts
        ]

    def __relocated_path(self, current: Path, title: str, project: str | None) -> Path:
        """Return the expected path for a task after title/project change."""
        slug = _slugify(title)
        subfolder = project if project is not None else current.parent.name
        return self._vault.tasks_path / subfolder / f"{slug}.md"

    def __render_active_section(self, by_project: dict[str, list[TaskNote]]) -> list[str]:
        lines: list[str] = []
        for project in sorted(by_project):
            lines.append(f"## Project: {project}\n")
            current_priority: Priority | None = None
            for t in by_project[project]:
                if t.priority != current_priority:
                    current_priority = t.priority
                    lines.append(f"### Priority: {t.priority}\n")
                lines.append(self.__render_link(t))
            lines.append("")
        return lines

    def __render_done_section(self, done_by_project: dict[str, list[TaskNote]]) -> list[str]:
        if not done_by_project:
            return []
        lines: list[str] = ["## Done\n"]
        for project in sorted(done_by_project):
            lines.append(f"### Project: {project}\n")
            for t in done_by_project[project]:
                lines.append(self.__render_link(t))
            lines.append("")
        return lines

    def __render_link(self, task: TaskNote) -> str:
        rel = (
            task.source_path.relative_to(self._vault.tasks_path)
            if task.source_path
            else Path(task.slug + ".md")
        )
        desc = task.description or task.title
        due_str = f" (due:{task.due.isoformat()})" if task.due else ""
        return f"- [{task.title}]({rel}) — {desc}{due_str}"

    @staticmethod
    def __patch_frontmatter(content: str, field: str, value: object) -> str:
        """Replace a single frontmatter field value, preserving everything else."""
        return re.sub(
            rf"^({re.escape(field)}:\s*).*$",
            rf"\g<1>{value}",
            content,
            count=1,
            flags=re.MULTILINE,
        )
