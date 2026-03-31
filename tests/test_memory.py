"""Tests for MemoryService."""

from app.adapters.vault import FileVaultService
from app.domain.models.notes import ConversationSummary, CoreNote, HighlightNote
from app.services.memory import MemoryService


def test_save_and_get_core(memory: MemoryService, vault: FileVaultService) -> None:
    """Save and retrieve core notes."""
    note = CoreNote(name="Role", description="User role", content="Senior engineer")
    memory.save_core(note)

    cores = memory.get_core_context()
    assert len(cores) == 1
    assert "Senior engineer" in cores[0]


def test_save_highlight(memory: MemoryService, vault: FileVaultService) -> None:
    """Save a highlight note."""
    note = HighlightNote(
        name="SSH Config",
        description="Multi-account SSH setup",
        content="Use Host aliases in ~/.ssh/config",
        tags=["ssh", "devops"],
    )
    path = memory.save_highlight(note)
    assert "ssh-config.md" in path
    assert vault.exists(vault.highlights_path / "ssh-config.md")


def test_save_conversation(memory: MemoryService, vault: FileVaultService) -> None:
    """Save a conversation with summary and archive."""
    note = ConversationSummary(
        title="How to setup MCP",
        key_points=["Use FastMCP", "Stdio transport"],
        full_content="Full conversation text here...",
    )
    path = memory.save_conversation(note)
    assert "summaries" in path

    # Archive should also exist
    archive = vault.conversations_path / "archive" / "how-to-setup-mcp.md"
    assert vault.exists(archive)


def test_get_relevant_context(memory: MemoryService, vault: FileVaultService) -> None:
    """Search returns relevant highlights."""
    note = HighlightNote(
        name="Python Async Patterns",
        description="asyncio best practices",
        content="Use asyncio.gather for concurrent tasks",
        tags=["python", "async"],
    )
    memory.save_highlight(note)

    results = memory.get_relevant_context("python")
    assert len(results) >= 1
    assert results[0].name == "Python Async Patterns"


def test_rebuild_index(memory: MemoryService, vault: FileVaultService) -> None:
    """Rebuild MEMORY.md from saved notes."""
    memory.save_core(CoreNote(name="Role", description="Engineer", content="..."))
    memory.save_highlight(
        HighlightNote(name="Tip", description="A tip", content="...", tags=[])
    )

    content = memory.rebuild_index()
    assert "# Memory Index" in content
    assert "Role" in content
    assert "Tip" in content
    assert vault.exists(vault.memory_path / "MEMORY.md")
