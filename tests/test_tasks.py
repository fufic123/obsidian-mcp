"""Tests for TaskService."""

from datetime import date

from app.services.tasks import TaskService


def test_create_task(task_service: TaskService) -> None:
    """Create a task note."""
    path = task_service.create_task("Fix the bug", due=date(2026, 4, 15), project="work")
    assert "fix-the-bug.md" in path


def test_list_tasks(task_service: TaskService) -> None:
    """List open tasks."""
    task_service.create_task("Task A", project="work")
    task_service.create_task("Task B", project="personal")
    task_service.create_task("Task C", project="work")

    all_tasks = task_service.list_tasks()
    assert len(all_tasks) == 3

    work_tasks = task_service.list_tasks(project="work")
    assert len(work_tasks) == 2


def test_list_tasks_empty(task_service: TaskService) -> None:
    """Return empty list when no tasks."""
    assert task_service.list_tasks() == []
