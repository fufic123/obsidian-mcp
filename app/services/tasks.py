"""Task service — manages Obsidian Tasks format tasks."""

from datetime import date

from app.domain.interfaces.vault import IVaultService
from app.domain.models.notes import TaskNote


class TaskService:
    """Manages tasks in Obsidian Tasks format."""

    def __init__(self, vault: IVaultService) -> None:
        self._vault = vault

    def create_task(
        self,
        title: str,
        due: date | None = None,
        project: str | None = None,
    ) -> str:
        """Create a task note. Returns the file path."""
        note = TaskNote(title=title, due=due, project=project)
        path = self._vault.tasks_path / f"{note.slug}.md"
        self._vault.write(path, note.to_markdown())
        return str(path)

    def list_tasks(self, project: str | None = None) -> list[TaskNote]:
        """List uncompleted tasks, optionally filtered by project."""
        files = self._vault.list_files(self._vault.tasks_path)
        tasks: list[TaskNote] = []
        for f in files:
            if f.name.startswith("INDEX"):
                continue
            content = self._vault.read(f)
            task = self._parse_task(content)
            if task and not task.done:
                if project is None or task.project == project:
                    tasks.append(task)
        return tasks

    def _parse_task(self, content: str) -> TaskNote | None:
        """Parse a task note from markdown content."""
        lines = content.splitlines()

        # Extract frontmatter
        title = ""
        project: str | None = None
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
                elif stripped.startswith("project:"):
                    val = stripped[8:].strip()
                    project = val if val else None
                elif stripped.startswith("created:"):
                    try:
                        created = date.fromisoformat(stripped[8:].strip())
                    except ValueError:
                        pass

        # Parse task line
        done = False
        due: date | None = None
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("- [x]"):
                done = True
                title = title or stripped[5:].strip().split(" \U0001f4c5")[0]
            elif stripped.startswith("- [ ]"):
                title = title or stripped[5:].strip().split(" \U0001f4c5")[0]

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
            due=due,
            project=project,
            done=done,
            created=created,
        )
