"""Productivity service — daily notes and MOC generation."""

from datetime import date

from app.domain.interfaces.vault import IVaultService
from app.domain.models.daily_note import DailyNote


class ProductivityService:
    """Manages daily notes and Map of Content generation."""

    def __init__(self, vault: IVaultService) -> None:
        self._vault = vault

    def create_daily_note(self, content: str | None = None) -> str:
        """Create or update today's daily note. Returns the file path."""
        note = DailyNote(content=content or "", note_date=date.today())
        path = self._vault.daily_path / f"{note.slug}.md"

        # If note exists, append content
        if self._vault.exists(path) and content:
            existing = self._vault.read(path)
            updated = f"{existing}\n\n{content}\n"
            self._vault.write(path, updated)
        else:
            self._vault.write(path, note.to_markdown())

        return str(path)

    def generate_moc(self, folder: str) -> str:
        """Generate Map of Content for a vault folder. Returns the MOC content."""
        folder_path = self._vault.root / folder
        files = self._vault.list_files(folder_path)

        lines = [f"# Map of Content: {folder}\n"]
        for f in files:
            if f.name == "MOC.md":
                continue
            name = f.stem.replace("-", " ").title()
            try:
                rel = f.relative_to(self._vault.root)
            except ValueError:
                rel = f
            lines.append(f"- [[{rel}|{name}]]")

        content = "\n".join(lines) + "\n"
        moc_path = folder_path / "MOC.md"
        self._vault.write(moc_path, content)
        return content
