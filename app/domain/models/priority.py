"""Task priority enum."""

from enum import StrEnum


class Priority(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


PRIORITY_EMOJI: dict[Priority, str] = {
    Priority.HIGH: "⏫",
    Priority.MEDIUM: "🔼",
    Priority.LOW: "🔽",
}
