"""Tests for TaskService — full CRUD and lifecycle behaviour."""

from datetime import date

import pytest

from app.domain.exceptions.vault import VaultReadError
from app.domain.models.priority import Priority
from app.services.tasks import TaskService


def test_create_task(task_service: TaskService) -> None:
    """Creating a task returns a path containing the slugified title."""
    path = task_service.create_task(
        "Fix the bug",
        description="Reproduce and fix the crash in vault reader",
        priority=Priority.HIGH,
        due=date(2026, 4, 15),
        project="work",
    )
    assert "fix-the-bug.md" in path


def test_list_tasks(task_service: TaskService) -> None:
    """All open tasks are returned; filtering by project works."""
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
    """Return empty list when no tasks exist."""
    assert task_service.list_tasks() == []


def test_list_tasks_sorted_by_priority(task_service: TaskService) -> None:
    """list_tasks returns tasks ordered high → medium → low within the same project."""
    task_service.create_task("Low task", description="desc", priority=Priority.LOW, project="work")
    task_service.create_task(
        "High task", description="desc", priority=Priority.HIGH, project="work"
    )
    task_service.create_task(
        "Med task", description="desc", priority=Priority.MEDIUM, project="work"
    )

    tasks = task_service.list_tasks(project="work")
    priorities = [t.priority for t in tasks]
    assert priorities == [Priority.HIGH, Priority.MEDIUM, Priority.LOW]


def test_get_task_returns_correct_task(task_service: TaskService) -> None:
    """get_task finds a task by its title and returns the full TaskNote."""
    task_service.create_task("My Feature", description="Build it", priority=Priority.MEDIUM)
    task = task_service.get_task("My Feature")
    assert task.title == "My Feature"
    assert task.description == "Build it"


def test_get_task_raises_when_not_found(task_service: TaskService) -> None:
    """get_task raises VaultReadError for a title that does not exist."""
    with pytest.raises(VaultReadError):
        task_service.get_task("Ghost task")


def test_complete_task_moves_to_archive(task_service: TaskService) -> None:
    """complete_task sets status=done and moves the file into archive/."""
    task_service.create_task("Deploy fix", description="Deploy to prod", priority=Priority.HIGH)
    archive_path = task_service.complete_task("Deploy fix")
    assert "archive" in archive_path


def test_complete_task_excluded_from_open_list(task_service: TaskService) -> None:
    """A completed task no longer appears in list_tasks."""
    task_service.create_task("Done thing", description="desc", priority=Priority.LOW)
    task_service.complete_task("Done thing")
    assert task_service.list_tasks() == []


def test_reopen_task_moves_back_from_archive(task_service: TaskService) -> None:
    """reopen_task restores the task to active status and moves it out of archive/."""
    task_service.create_task("Archive me", description="desc", priority=Priority.MEDIUM)
    task_service.complete_task("Archive me")
    task_service.reopen_task("Archive me")
    tasks = task_service.list_tasks()
    assert any(t.title == "Archive me" for t in tasks)


def test_delete_task_removes_it(task_service: TaskService) -> None:
    """delete_task removes the file so the task can no longer be retrieved."""
    task_service.create_task("Temp task", description="delete me", priority=Priority.LOW)
    task_service.delete_task("Temp task")
    assert task_service.list_tasks() == []


def test_update_task_changes_description(task_service: TaskService) -> None:
    """update_task persists a new description on the task."""
    task_service.create_task("Updateable", description="original", priority=Priority.LOW)
    task_service.update_task("Updateable", description="updated description")
    task = task_service.get_task("Updateable")
    assert task.description == "updated description"


def test_update_task_saves_implementation(task_service: TaskService) -> None:
    """update_task persists an implementation note that is readable via get_task."""
    task_service.create_task("Ship feature", description="ship it", priority=Priority.HIGH)
    task_service.update_task(
        "Ship feature",
        implementation="Added endpoint, wrote migration, deployed to staging.",
    )
    task = task_service.get_task("Ship feature")
    assert "migration" in task.implementation


def test_update_task_renames_file_on_title_change(task_service: TaskService) -> None:
    """Changing the title moves the task file to a new slug-based path."""
    task_service.create_task("Old name", description="desc", priority=Priority.LOW)
    new_path = task_service.update_task("Old name", new_title="New name")
    assert "new-name" in new_path
    task = task_service.get_task("New name")
    assert task.title == "New name"


def test_update_task_changes_priority(task_service: TaskService) -> None:
    """update_task can change a task's priority."""
    task_service.create_task("Reprioritise me", description="desc", priority=Priority.LOW)
    task_service.update_task("Reprioritise me", priority=Priority.HIGH)
    task = task_service.get_task("Reprioritise me")
    assert task.priority == Priority.HIGH


def test_task_with_due_date_preserved_on_round_trip(task_service: TaskService) -> None:
    """A task created with a due date retains it after saving and retrieval."""
    due = date(2026, 6, 1)
    task_service.create_task("Deadline task", description="desc", priority=Priority.HIGH, due=due)
    task = task_service.get_task("Deadline task")
    assert task.due == due


def test_completed_task_appears_in_get_task(task_service: TaskService) -> None:
    """get_task can retrieve a done task from the archive."""
    task_service.create_task("Done task", description="desc", priority=Priority.LOW)
    task_service.complete_task("Done task")
    task = task_service.get_task("Done task")
    assert task.title == "Done task"
