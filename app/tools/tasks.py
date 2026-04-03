"""MCP tool wrappers for task operations."""

from datetime import date

from fastmcp import FastMCP

from app.domain.interfaces.performance import IPerformanceService
from app.domain.models.priority import Priority
from app.services.tasks import TaskService
from app.tools.base import BaseTools


class TaskTools(BaseTools):
    def __init__(
        self,
        tasks: TaskService,
        mcp: FastMCP,
        performance_service: IPerformanceService | None = None,
        session_id: str | None = None,
    ) -> None:
        super().__init__(performance_service, session_id)
        self._tasks = tasks
        mcp.tool()(self._wrap(self.get_task))
        mcp.tool()(self._wrap(self.create_task))
        mcp.tool()(self._wrap(self.list_tasks))
        mcp.tool()(self._wrap(self.complete_task))
        mcp.tool()(self._wrap(self.reopen_task))
        mcp.tool()(self._wrap(self.update_task))
        mcp.tool()(self._wrap(self.delete_task))
        mcp.tool()(self._wrap(self.rebuild_tasks_index))

    def get_task(self, title: str) -> str:
        """Read a task by title — returns full details including description and status.

        Searches both active and done (archive) tasks via TASKS.md index.
        """
        task = self._tasks.get_task(title)
        lines = [
            f"name: {task.title}",
            f"status: {task.status}",
            f"priority: {task.priority}",
            f"description: {task.description}",
        ]
        if task.implementation:
            lines.append(f"implementation: {task.implementation}")
        if task.due:
            lines.append(f"due: {task.due.isoformat()}")
        if task.project:
            lines.append(f"project: {task.project}")
        if task.source_path:
            lines.append(f"path: {task.source_path}")
        return "\n".join(lines)

    def create_task(
        self,
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
        path = self._tasks.create_task(
            title=title,
            description=description,
            priority=priority,
            due=due_date,
            project=project,
        )
        return f"Created: {path}"

    def list_tasks(self, project: str | None = None) -> str:
        """List open tasks sorted by priority, optionally filtered by project."""
        task_list = self._tasks.list_tasks(project=project)
        if not task_list:
            return "No open tasks found."
        lines: list[str] = []
        for t in task_list:
            due_str = f" (due:{t.due.isoformat()})" if t.due else ""
            proj_str = f" [{t.project}]" if t.project else ""
            lines.append(f"- [{t.priority.value}] {t.title}{due_str}{proj_str}")
        return "\n".join(lines)

    def complete_task(self, title: str) -> str:
        """Mark a task done: sets status=done, moves to archive/. Rebuilds index."""
        path = self._tasks.complete_task(title)
        return f"Completed: {path}"

    def reopen_task(self, title: str) -> str:
        """Reopen a done task: sets status=active, moves back from archive/."""
        path = self._tasks.reopen_task(title)
        return f"Reopened: {path}"

    def update_task(
        self,
        title: str,
        new_title: str | None = None,
        description: str | None = None,
        implementation: str | None = None,
        priority: Priority | None = None,
        due: str | None = None,
        project: str | None = None,
    ) -> str:
        """Update any fields of an active or done task. Only pass fields you want to change.

        implementation: AI-written summary of what was done — use this when completing work.
        """
        due_date = date.fromisoformat(due) if due else None
        path = self._tasks.update_task(
            title=title,
            new_title=new_title,
            description=description,
            implementation=implementation,
            priority=priority,
            due=due_date,
            project=project,
        )
        return f"Updated: {path}"

    def delete_task(self, title: str) -> str:
        """Permanently delete a task file (active or done)."""
        path = self._tasks.delete_task(title)
        return f"Deleted: {path}"

    def rebuild_tasks_index(self) -> str:
        """Regenerate TASKS.md from source files. Call after manual edits in Obsidian."""
        return self._tasks.rebuild_index()
