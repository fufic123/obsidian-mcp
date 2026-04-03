"""Tests for TaskService."""

from datetime import date

from app.domain.models.notes import Priority
from app.services.tasks import TaskService


def test_create_task(task_service: TaskService) -> None:
    """Create a task note."""
    path = task_service.create_task(
        "Fix the bug",
        description="Reproduce and fix the crash in vault reader",
        priority=Priority.HIGH,
        due=date(2026, 4, 15),
        project="work",
    )
    assert "fix-the-bug.md" in path


def test_list_tasks(task_service: TaskService) -> None:
    """List open tasks."""
    task_service.create_task(
        "Task A", description="First task", priority=Priority.MEDIUM, project="work"
    )
    task_service.create_task(
        "Task B", description="Second task", priority=Priority.LOW, project="personal"
    )
    task_service.create_task(
        "Task C", description="Third task", priority=Priority.HIGH, project="work"
    )

    all_tasks = task_service.list_tasks()
    assert len(all_tasks) == 3

    work_tasks = task_service.list_tasks(project="work")
    assert len(work_tasks) == 2


def test_list_tasks_empty(task_service: TaskService) -> None:
    """Return empty list when no tasks."""
    assert task_service.list_tasks() == []
