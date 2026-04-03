"""Performance tracking service interface."""

from abc import ABC, abstractmethod
from typing import Literal

from app.domain.models.agent_session import AgentSession


class IPerformanceService(ABC):
    @abstractmethod
    def start_session(self, agent_name: str, model: str) -> str:
        """Create a new tracking session. Returns session_id."""
        ...

    @abstractmethod
    def record_tool_call(
        self,
        session_id: str,
        tool_name: str,
        duration_ms: float,
        status: Literal["ok", "error"],
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        error: str | None = None,
    ) -> None:
        """Append a tool call record to the session file and update running totals."""
        ...

    @abstractmethod
    def end_session(self, session_id: str) -> None:
        """Mark the session as completed and record ended_at."""
        ...

    @abstractmethod
    def get_session(self, session_id: str) -> AgentSession | None:
        """Return session metadata parsed from its file."""
        ...

    @abstractmethod
    def get_stats(self, agent_name: str | None = None, days: int = 7) -> str:
        """Return aggregated stats for recent sessions."""
        ...

    @abstractmethod
    def get_dashboard(self) -> str:
        """Return a full performance dashboard grouped by agent."""
        ...

    @abstractmethod
    def end_all_active_sessions(self) -> None:
        """Mark all active sessions as completed. Called automatically on process exit."""
        ...
