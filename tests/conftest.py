"""Shared test fixtures."""

from pathlib import Path

import pytest

from app.adapters.index import IndexService
from app.adapters.search import FrontmatterSearchService
from app.adapters.vault import FileVaultService
from app.domain.models.config import MemoryConfig
from app.services.memory import MemoryService
from app.services.productivity import ProductivityService
from app.services.tasks import TaskService


@pytest.fixture()
def vault_root(tmp_path: Path) -> Path:
    """Create a temporary vault directory structure."""
    dirs = [
        "memory/core",
        "memory/highlights",
        "memory/conversations/summaries",
        "memory/conversations/archive",
        "tasks",
        "daily",
    ]
    for d in dirs:
        (tmp_path / d).mkdir(parents=True)
    return tmp_path


@pytest.fixture()
def vault(vault_root: Path) -> FileVaultService:
    """Create a FileVaultService backed by tmp_path."""
    return FileVaultService(vault_root)


@pytest.fixture()
def config() -> MemoryConfig:
    """Default memory config for tests."""
    return MemoryConfig()


@pytest.fixture()
def search(vault: FileVaultService, config: MemoryConfig) -> FrontmatterSearchService:
    """Create a FrontmatterSearchService."""
    return FrontmatterSearchService(vault, config)


@pytest.fixture()
def index(vault: FileVaultService, config: MemoryConfig) -> IndexService:
    """Create an IndexService."""
    return IndexService(vault, config)


@pytest.fixture()
def memory(
    vault: FileVaultService,
    search: FrontmatterSearchService,
    index: IndexService,
) -> MemoryService:
    """Create a MemoryService."""
    return MemoryService(vault, search, index)


@pytest.fixture()
def task_service(vault: FileVaultService) -> TaskService:
    """Create a TaskService."""
    return TaskService(vault)


@pytest.fixture()
def productivity(vault: FileVaultService) -> ProductivityService:
    """Create a ProductivityService."""
    return ProductivityService(vault)
