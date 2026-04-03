"""Task service — manages Obsidian Tasks format tasks."""

from datetime import date
from pathlib import Path

from app.domain.exceptions.vault import VaultReadError
from app.domain.interfaces.vault import IVaultService
from app.domain.models.notes import Priority, TaskNote, TaskStatus, _slugify

_VALID_PRIORITY_VALUES = {p.value for p in Priority}
_VALID_STATUS_VALUES = {s.value for s in TaskStatus}
_PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}


class TaskService:
    """Manages tasks in Obsidian Tasks format."""

    def __init__(self, vault: IVaultService) -> None:
        self._vault = vault

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
        subfolder = project if project else "inbox"
        path = self._vault.tasks_path / subfolder / f"{note.slug}.md"
        self._vault.write(path, note.to_markdown())
        self.rebuild_index()
        return str(path)

    def complete_task(self, title: str) -> str:
        """Mark a task done and move to tasks/{project}/archive/. Rebuilds index."""
        slug = _slugify(title)
        path = self._find_task_file(slug)
        if path is None:
            raise VaultReadError(f"Task not found: {title!r}")

        content = self._vault.read(path)
        updated = content.replace("status: active", "status: done", 1)
        self._vault.write(path, updated)
        archive_path = path.parent / "archive" / path.name
        self._vault.move(path, archive_path)
        self.rebuild_index()
        return str(archive_path)

    def list_tasks(self, project: str | None = None) -> list[TaskNote]:
        """List open tasks. Always rebuilds index from source files first."""
        self.rebuild_index()
        tasks: list[TaskNote] = []
        for f in self._open_task_files():
            task = self._parse_task(self._vault.read(f), source_path=f)
            if task and not task.done:
                if project is None or task.project == project:
                    tasks.append(task)
        tasks.sort(key=lambda t: _PRIORITY_ORDER[t.priority])
        return tasks

    def rebuild_index(self) -> str:
        """Regenerate tasks/TASKS.md. Source of truth = individual .md files."""
        by_project: dict[str, list[TaskNote]] = {}
        for f in self._open_task_files():
            try:
                task = self._parse_task(self._vault.read(f), source_path=f)
                if task and not task.done:
                    key = task.project or "inbox"
                    by_project.setdefault(key, []).append(task)
            except Exception:
                continue

        for tasks in by_project.values():
            tasks.sort(key=lambda t: _PRIORITY_ORDER[t.priority])

        lines = ["# Tasks\n"]
        for project in sorted(by_project):
            lines.append(f"## Project: {project}\n")
            current_priority: Priority | None = None
            for t in by_project[project]:
                if t.priority != current_priority:
                    current_priority = t.priority
                    lines.append(f"### Priority: {t.priority}\n")
                rel = (
                    t.source_path.relative_to(self._vault.tasks_path)
                    if t.source_path
                    else Path(t.slug + ".md")
                )
                desc = t.description or t.title
                due_str = f" (due:{t.due.isoformat()})" if t.due else ""
                lines.append(f"- [{t.title}]({rel}) — {desc}{due_str}")
            lines.append("")

        content = "\n".join(lines)
        self._vault.write(self._vault.tasks_path / "TASKS.md", content)
        return content

    def _open_task_files(self) -> list[Path]:
        """All task files excluding TASKS.md index and archive subfolders."""
        return [
            f
            for f in self._vault.list_files(self._vault.tasks_path, recursive=True)
            if f.name != "TASKS.md" and "archive" not in f.parts
        ]

    def _find_task_file(self, slug: str) -> Path | None:
        """Find task file by slug — matches filename stem or frontmatter name slug."""
        for f in self._vault.list_files(self._vault.tasks_path, recursive=True):
            if f.name == "TASKS.md" or "archive" in f.parts:
                continue
            if f.stem == slug:
                return f
            try:
                task = self._parse_task(self._vault.read(f))
                if task and _slugify(task.title) == slug:
                    return f
            except Exception:
                continue
        return None

    def _parse_task(self, content: str, source_path: Path | None = None) -> TaskNote | None:
        """Parse a task note from markdown content."""
        lines = content.splitlines()

        title = ""
        description = ""
        project: str | None = None
        priority: Priority = Priority.MEDIUM
        status: TaskStatus = TaskStatus.ACTIVE
        due: date | None = None
        created = date.today()
        in_frontmatter = False
        for line in lines:
            stripped = line.strip()
            if stripped == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                else:
                    break
            if in_frontmatter:
                if stripped.startswith("name:"):
                    title = stripped[5:].strip()
                elif stripped.startswith("description:"):
                    description = stripped[12:].strip()
                elif stripped.startswith("status:"):
                    val = stripped[7:].strip()
                    if val in _VALID_STATUS_VALUES:
                        status = TaskStatus(val)
                elif stripped.startswith("priority:"):
                    val = stripped[9:].strip()
                    if val in _VALID_PRIORITY_VALUES:
                        priority = Priority(val)
                elif stripped.startswith("project:"):
                    val = stripped[8:].strip()
                    project = val if val else None
                elif stripped.startswith("created:"):
                    try:
                        created = date.fromisoformat(stripped[8:].strip())
                    except ValueError:
                        pass
                elif stripped.startswith("due:"):
                    try:
                        due = date.fromisoformat(stripped[4:].strip())
                    except ValueError:
                        pass

        if not title:
            return None

        return TaskNote(
            title=title,
            description=description,
            priority=priority,
            status=status,
            due=due,
            project=project,
            created=created,
            source_path=source_path,
        )
