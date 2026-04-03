"""MCP tool wrappers for task operations."""

from datetime import date

from fastmcp import FastMCP

from app.domain.models.notes import Priority
from app.services.tasks import TaskService


def register_task_tools(mcp: FastMCP, tasks: TaskService) -> None:
    """Register task-related MCP tools."""

    @mcp.tool()
    def create_task(
        title: str,
        description: str,
        priority: Priority,
        due: str | None = None,
        project: str | None = None,
    ) -> str:
        """Create a task in Obsidian Tasks format.

        title: short name (3-6 words), shown in TASKS.md index.
        description: one sentence for AI — what needs to be done and why.
        Saved to tasks/{project}/slug.md. Rebuilds TASKS.md automatically.
        priority: 'high' (⏫), 'medium' (🔼), or 'low' (🔽).
        """
        due_date = date.fromisoformat(due) if due else None
        path = tasks.create_task(
            title=title, description=description, priority=priority, due=due_date, project=project
        )
        return f"Created task: {path}"

    @mcp.tool()
    def list_tasks(project: str | None = None) -> str:
        """List uncompleted tasks sorted by priority, optionally filtered by project."""
        task_list = tasks.list_tasks(project=project)
        if not task_list:
            return "No open tasks found."
        lines: list[str] = []
        for t in task_list:
            due_str = f" (due: {t.due.isoformat()})" if t.due else ""
            proj_str = f" [{t.project}]" if t.project else ""
            lines.append(f"- [ ] [{t.priority.value}] {t.title}{due_str}{proj_str}")
        return "\n".join(lines)

    @mcp.tool()
    def complete_task(title: str) -> str:
        """Mark a task as done by its title. Works regardless of who created it.

        Finds the task file by title slug, sets - [x], rebuilds TASKS.md index.
        """
        path = tasks.complete_task(title)
        return f"Completed: {path}"

    @mcp.tool()
    def rebuild_tasks_index() -> str:
        """Regenerate tasks/TASKS.md from source files. Call after manual edits in Obsidian."""
        return tasks.rebuild_index()
