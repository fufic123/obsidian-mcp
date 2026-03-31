"""MCP tool wrappers for task operations."""

from datetime import date

from fastmcp import FastMCP

from app.services.tasks import TaskService


def register_task_tools(mcp: FastMCP, tasks: TaskService) -> None:
    """Register task-related MCP tools."""

    @mcp.tool()
    def create_task(
        title: str,
        due: str | None = None,
        project: str | None = None,
    ) -> str:
        """Create a task in Obsidian Tasks format."""
        due_date = date.fromisoformat(due) if due else None
        path = tasks.create_task(title=title, due=due_date, project=project)
        return f"Created task: {path}"

    @mcp.tool()
    def list_tasks(project: str | None = None) -> str:
        """List uncompleted tasks, optionally filtered by project."""
        task_list = tasks.list_tasks(project=project)
        if not task_list:
            return "No open tasks found."
        lines: list[str] = []
        for t in task_list:
            due_str = f" (due: {t.due.isoformat()})" if t.due else ""
            proj_str = f" [{t.project}]" if t.project else ""
            lines.append(f"- [ ] {t.title}{due_str}{proj_str}")
        return "\n".join(lines)
