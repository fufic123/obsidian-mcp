"""Tests for MemoryService."""

from app.adapters.vault import FileVaultService
from app.domain.models.conversation_note import ConversationSummary
from app.domain.models.core_note import CoreNote
from app.domain.models.highlight_note import HighlightNote
from app.services.memory import MemoryService


def test_save_and_get_core(memory: MemoryService, vault: FileVaultService) -> None:
    """Save and retrieve core notes."""
    note = CoreNote(name="Role", description="User role", content="Senior engineer")
    memory.save_core(note)

    cores = memory.get_core_context()
    assert len(cores) == 1
    assert "Senior engineer" in cores[0]


def test_save_highlight_without_project_goes_to_general(
    memory: MemoryService, vault: FileVaultService
) -> None:
    """A highlight without a project is saved under highlights/general/."""
    note = HighlightNote(
        name="SSH Config",
        description="Multi-account SSH setup",
        content="Use Host aliases in ~/.ssh/config",
        tags=["ssh", "devops"],
    )
    path = memory.save_highlight(note)
    assert "ssh-config.md" in path
    assert vault.exists(vault.highlights_path / "general" / "ssh-config.md")


def test_save_highlight_with_project_goes_to_project_subfolder(
    memory: MemoryService, vault: FileVaultService
) -> None:
    """A highlight with a project is saved under highlights/{project}/."""
    note = HighlightNote(
        name="MCP Auth Pattern",
        description="Auth pattern for MCP tools",
        content="Use session tokens stored in vault",
        tags=["auth", "mcp"],
        project="obsidian-mcp",
    )
    path = memory.save_highlight(note)
    assert "mcp-auth-pattern.md" in path
    assert vault.exists(vault.highlights_path / "obsidian-mcp" / "mcp-auth-pattern.md")


def test_save_highlight_rebuilds_highlights_index(
    memory: MemoryService, vault: FileVaultService
) -> None:
    """Saving a highlight creates/updates HIGHLIGHTS.md."""
    note = HighlightNote(name="Tip", description="A tip", content="...", project="work")
    memory.save_highlight(note)
    assert vault.exists(vault.highlights_path / "HIGHLIGHTS.md")
    content = vault.read(vault.highlights_path / "HIGHLIGHTS.md")
    assert "Tip" in content
    assert "work" in content


def test_highlights_index_groups_by_project(memory: MemoryService, vault: FileVaultService) -> None:
    """HIGHLIGHTS.md lists notes under their respective project headings."""
    memory.save_highlight(
        HighlightNote(name="Alpha", description="d", content="c", project="proj-a")
    )
    memory.save_highlight(
        HighlightNote(name="Beta", description="d", content="c", project="proj-b")
    )
    content = vault.read(vault.highlights_path / "HIGHLIGHTS.md")
    assert "proj-a" in content
    assert "proj-b" in content
    assert "Alpha" in content
    assert "Beta" in content


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
    """MEMORY.md links to HIGHLIGHTS.md rather than listing individual highlights."""
    memory.save_core(CoreNote(name="Role", description="Engineer", content="..."))
    memory.save_highlight(HighlightNote(name="Tip", description="A tip", content="...", tags=[]))

    content = memory.rebuild_index()
    assert "# Memory Index" in content
    assert "Role" in content
    # Highlights appear as a link to HIGHLIGHTS.md, not as individual entries
    assert "HIGHLIGHTS.md" in content
    assert vault.exists(vault.memory_path / "MEMORY.md")
