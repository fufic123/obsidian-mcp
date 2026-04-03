"""MCP tool wrappers for task operations."""

from datetime import date

from fastmcp import FastMCP

from app.domain.models.notes import Priority
from app.services.tasks import TaskService


def register_task_tools(mcp: FastMCP, tasks: TaskService) -> None:
    """Register task-related MCP tools."""

    @mcp.tool()
    def get_task(title: str) -> str:
        """Read a task by title — returns full details including description and status.

        Searches both active and done (archive) tasks via TASKS.md index.
        """
        task = tasks.get_task(title)
        lines = [
            f"name: {task.title}",
            f"status: {task.status}",
            f"priority: {task.priority}",
            f"description: {task.description}",
        ]
        if task.due:
            lines.append(f"due: {task.due.isoformat()}")
        if task.project:
            lines.append(f"project: {task.project}")
        if task.source_path:
            lines.append(f"path: {task.source_path}")
        return "\n".join(lines)

    @mcp.tool()
    def create_task(
        title: str,
        description: str,
        priority: Priority,
        due: str | None = None,
        project: str | None = None,
    ) -> str:
        """Create a task in tasks/{project}/slug.md. Rebuilds TASKS.md automatically.

        title: short noun phrase (3-6 words).
        description: one sentence for AI — what needs to be done and why.
        priority: 'high', 'medium', or 'low'.
        """
        due_date = date.fromisoformat(due) if due else None
        path = tasks.create_task(
            title=title, description=description, priority=priority, due=due_date, project=project
        )
        return f"Created: {path}"

    @mcp.tool()
    def list_tasks(project: str | None = None) -> str:
        """List open tasks sorted by priority, optionally filtered by project."""
        task_list = tasks.list_tasks(project=project)
        if not task_list:
            return "No open tasks found."
        lines: list[str] = []
        for t in task_list:
            due_str = f" (due:{t.due.isoformat()})" if t.due else ""
            proj_str = f" [{t.project}]" if t.project else ""
            lines.append(f"- [{t.priority.value}] {t.title}{due_str}{proj_str}")
        return "\n".join(lines)

    @mcp.tool()
    def complete_task(title: str) -> str:
        """Mark a task done: sets status=done, moves to archive/. Rebuilds index."""
        path = tasks.complete_task(title)
        return f"Completed: {path}"

    @mcp.tool()
    def reopen_task(title: str) -> str:
        """Reopen a done task: sets status=active, moves back from archive/."""
        path = tasks.reopen_task(title)
        return f"Reopened: {path}"

    @mcp.tool()
    def update_task(
        title: str,
        new_title: str | None = None,
        description: str | None = None,
        priority: Priority | None = None,
        due: str | None = None,
        project: str | None = None,
    ) -> str:
        """Update any fields of an active task. Only pass fields you want to change."""
        due_date = date.fromisoformat(due) if due else None
        path = tasks.update_task(
            title=title,
            new_title=new_title,
            description=description,
            priority=priority,
            due=due_date,
            project=project,
        )
        return f"Updated: {path}"

    @mcp.tool()
    def delete_task(title: str) -> str:
        """Permanently delete a task file (active or done)."""
        path = tasks.delete_task(title)
        return f"Deleted: {path}"

    @mcp.tool()
    def rebuild_tasks_index() -> str:
        """Regenerate TASKS.md from source files. Call after manual edits in Obsidian."""
        return tasks.rebuild_index()
