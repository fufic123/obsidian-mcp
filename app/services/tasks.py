"""Task service — manages Obsidian Tasks format tasks."""

from datetime import date

from app.domain.interfaces.vault import IVaultService
from app.domain.models.notes import Priority, TaskNote

_VALID_PRIORITY_VALUES = {p.value for p in Priority}
_PRIORITY_ORDER = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}


class TaskService:
    """Manages tasks in Obsidian Tasks format."""

    def __init__(self, vault: IVaultService) -> None:
        self._vault = vault

    def create_task(
        self,
        title: str,
        priority: Priority,
        due: date | None = None,
        project: str | None = None,
    ) -> str:
        """Create a task note at tasks/{project}/slug.md. Returns the file path."""
        note = TaskNote(title=title, priority=priority, due=due, project=project)
        subfolder = project if project else "inbox"
        path = self._vault.tasks_path / subfolder / f"{note.slug}.md"
        self._vault.write(path, note.to_markdown())
        self.rebuild_index()
        return str(path)

    def list_tasks(self, project: str | None = None) -> list[TaskNote]:
        """List uncompleted tasks, optionally filtered by project."""
        files = self._vault.list_files(self._vault.tasks_path, recursive=True)
        tasks: list[TaskNote] = []
        for f in files:
            if f.name.startswith("TASKS"):
                continue
            content = self._vault.read(f)
            task = self._parse_task(content)
            if task and not task.done:
                if project is None or task.project == project:
                    tasks.append(task)
        tasks.sort(key=lambda t: _PRIORITY_ORDER[t.priority])
        return tasks

    def rebuild_index(self) -> str:
        """Regenerate tasks/TASKS.md index grouped by project and priority."""
        files = self._vault.list_files(self._vault.tasks_path, recursive=True)

        # Collect open tasks grouped by project
        by_project: dict[str, list[TaskNote]] = {}
        for f in files:
            if f.name.startswith("TASKS"):
                continue
            try:
                content = self._vault.read(f)
                task = self._parse_task(content)
                if task and not task.done:
                    key = task.project or "inbox"
                    by_project.setdefault(key, []).append(task)
            except Exception:
                continue

        # Sort tasks within each project by priority
        for tasks in by_project.values():
            tasks.sort(key=lambda t: _PRIORITY_ORDER[t.priority])

        lines = ["# Tasks\n"]
        for project in sorted(by_project):
            lines.append(f"## {project}\n")
            for t in by_project[project]:
                from app.domain.models.notes import _PRIORITY_EMOJI
                emoji = _PRIORITY_EMOJI[t.priority]
                due_str = f" 📅 {t.due.isoformat()}" if t.due else ""
                lines.append(f"- [ ] {t.title} {emoji}{due_str} #project/{project}")
            lines.append("")

        content = "\n".join(lines)
        index_path = self._vault.tasks_path / "TASKS.md"
        self._vault.write(index_path, content)
        return content

    def _parse_task(self, content: str) -> TaskNote | None:
        """Parse a task note from markdown content."""
        lines = content.splitlines()

        title = ""
        project: str | None = None
        priority: Priority = Priority.MEDIUM
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

        done = False
        due: date | None = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("- [x]"):
                done = True
            if "\U0001f4c5" in stripped:
                parts = stripped.split("\U0001f4c5")
                if len(parts) > 1:
                    date_str = parts[1].strip().split()[0]
                    try:
                        due = date.fromisoformat(date_str)
                    except ValueError:
                        pass

        if not title:
            return None

        return TaskNote(
            title=title,
            priority=priority,
            due=due,
            project=project,
            done=done,
            created=created,
        )
