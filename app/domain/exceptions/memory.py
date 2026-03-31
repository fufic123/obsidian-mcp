"""Memory-related exceptions."""


class InvalidNoteError(Exception):
    """Note data is invalid or incomplete."""


class IndexOverflowError(Exception):
    """MEMORY.md exceeds size limits."""
