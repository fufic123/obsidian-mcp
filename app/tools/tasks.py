"""MCP tool wrappers for task operations."""

from datetime import date

from fastmcp import FastMCP

from app.domain.models.notes import Priority
from app.services.tasks import TaskService

_PRIORITY_ORDER: dict[Priority, int] = {
    Priority.HIGH: 0,
    Priority.MEDIUM: 1,
    Priority.LOW: 2,
}


def register_task_tools(mcp: FastMCP, tasks: TaskService) -> None:
    """Register task-related MCP tools."""

    @mcp.tool()
    def create_task(
        title: str,
        priority: Priority,
        due: str | None = None,
        project: str | None = None,
    ) -> str:
        """Create a task in Obsidian Tasks format.

        priority: task urgency — 'high' (⏫), 'medium' (🔼), or 'low' (🔽).
        """
        due_date = date.fromisoformat(due) if due else None
        path = tasks.create_task(title=title, priority=priority, due=due_date, project=project)
        return f"Created task: {path}"

    @mcp.tool()
    def list_tasks(project: str | None = None) -> str:
        """List uncompleted tasks sorted by priority, optionally filtered by project."""
        task_list = tasks.list_tasks(project=project)
        if not task_list:
            return "No open tasks found."
        task_list.sort(key=lambda t: _PRIORITY_ORDER[t.priority])
        lines: list[str] = []
        for t in task_list:
            due_str = f" (due: {t.due.isoformat()})" if t.due else ""
            proj_str = f" [{t.project}]" if t.project else ""
            lines.append(f"- [ ] [{t.priority.value}] {t.title}{due_str}{proj_str}")
        return "\n".join(lines)
