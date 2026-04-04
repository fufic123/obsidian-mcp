"""MCP tool wrappers for task operations."""

from datetime import date

from fastmcp import FastMCP

from app.domain.models.priority import Priority
from app.services.tasks import TaskService


class TaskTools:
    def __init__(self, tasks: TaskService, mcp: FastMCP) -> None:
        self._tasks = tasks
        mcp.tool()(self.get_task)
        mcp.tool()(self.create_task)
        mcp.tool()(self.list_tasks)
        mcp.tool()(self.complete_task)
        mcp.tool()(self.reopen_task)
        mcp.tool()(self.update_task)
        mcp.tool()(self.delete_task)
        mcp.tool()(self.rebuild_tasks_index)

    def get_task(self, title: str) -> str:
        """Read full task details by title, including description, status, and implementation notes.

        Searches both active and archived (done) tasks.
        Call before starting work on a task to check what was previously decided or built.
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
        """Create a new task file and rebuild TASKS.md.

        Call list_tasks first — never create a task that already exists.
        title: 3-6 word noun phrase, no verbs. Example: "MCP auth refactor".
        description: one AI-facing sentence — what needs doing and why.
        priority: 'high' | 'medium' | 'low'.
        due: ISO date string, e.g. "2026-05-01".
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
        """List all open tasks sorted high → medium → low, optionally filtered by project.

        Rebuilds TASKS.md before returning — do NOT call rebuild_tasks_index separately.
        Call before create_task to check for duplicates.
        Does NOT return done/archived tasks — use get_task(title) to read a specific done task.
        """
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
        """Mark a task done: sets status=done, moves to archive/, rebuilds index.

        Call update_task(title, implementation=...) BEFORE this to record what was built.
        A completed task without an implementation note is considered incomplete.
        """
        path = self._tasks.complete_task(title)
        return f"Completed: {path}"

    def reopen_task(self, title: str) -> str:
        """Reopen a done task: sets status=active, moves it back out of archive/."""
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
        """Update any fields on an active or done task. Only pass fields you want to change.

        implementation: write here before calling complete_task — describe what was built,
          what decisions were made, and what changed. One paragraph. Never leave it empty.
        new_title: renames the task and moves the file to the new slug path.
        project: moves the file to the new project subfolder.
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
        """Permanently delete a task file (active or done). Cannot be undone.

        Use only when a task is truly irrelevant — not when it's finished.
        For finished work use complete_task so the history is preserved in archive/.
        """
        path = self._tasks.delete_task(title)
        return f"Deleted: {path}"

    def rebuild_tasks_index(self) -> str:
        """Regenerate TASKS.md from source files — call only when explicitly asked.

        create_task, complete_task, update_task, and list_tasks all rebuild automatically.
        Only call this after manually editing task files in Obsidian outside the MCP.
        """
        return self._tasks.rebuild_index()
