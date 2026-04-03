"""Performance tracking service — records agent tool calls and session stats."""

import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

from app.domain.interfaces.performance import IPerformanceService
from app.domain.interfaces.vault import IVaultService
from app.domain.models.agent_session import AgentSession
from app.domain.models.base import render_frontmatter
from app.domain.models.tool_call_record import ToolCallRecord
from app.services.cost_estimator import CostEstimator


class PerformanceService(IPerformanceService):
    """Persists agent performance data as markdown session files in the vault."""

    def __init__(self, vault: IVaultService, cost_estimator: CostEstimator) -> None:
        self._vault = vault
        self._cost_estimator = cost_estimator

    def start_session(self, agent_name: str, model: str) -> str:
        session = AgentSession(agent_name=agent_name, model=model)
        path = self._vault.performance_path / "sessions" / f"{session.slug}.md"
        self._vault.write(path, session.to_markdown())
        return session.session_id

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
        path = self.__find_session_file(session_id)
        if path is None:
            return

        content = self._vault.read(path)
        session = AgentSession.from_content(content)
        if session is None:
            return

        estimated_cost: float | None = None
        if input_tokens is not None and output_tokens is not None:
            estimated_cost = self._cost_estimator.estimate(
                session.model, input_tokens, output_tokens
            )

        record = ToolCallRecord(
            tool_name=tool_name,
            agent_name=session.agent_name,
            model=session.model,
            session_id=session_id,
            duration_ms=duration_ms,
            status=status,
            error=error,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost,
        )

        session.total_tool_calls += 1
        if input_tokens:
            session.total_input_tokens += input_tokens
        if output_tokens:
            session.total_output_tokens += output_tokens
        if estimated_cost:
            session.total_cost_usd += estimated_cost

        updated = self.__replace_frontmatter(content, render_frontmatter(session.frontmatter()))
        updated = updated.rstrip("\n") + "\n" + record.to_table_row() + "\n"
        self._vault.write(path, updated)

    def end_session(self, session_id: str) -> None:
        path = self.__find_session_file(session_id)
        if path is None:
            return

        content = self._vault.read(path)
        session = AgentSession.from_content(content)
        if session is None:
            return

        session.ended_at = datetime.now(UTC)
        session.status = "completed"
        updated = self.__replace_frontmatter(content, render_frontmatter(session.frontmatter()))
        self._vault.write(path, updated)

    def get_session(self, session_id: str) -> AgentSession | None:
        path = self.__find_session_file(session_id)
        if path is None:
            return None
        return AgentSession.from_content(self._vault.read(path))

    def get_stats(self, agent_name: str | None = None, days: int = 7) -> str:
        sessions = self.__load_recent_sessions(days)
        if agent_name:
            sessions = [s for s in sessions if s.agent_name == agent_name]
        if not sessions:
            return f"No sessions in the last {days} days."

        total_calls = sum(s.total_tool_calls for s in sessions)
        total_cost = sum(s.total_cost_usd for s in sessions)
        total_input = sum(s.total_input_tokens for s in sessions)
        total_output = sum(s.total_output_tokens for s in sessions)
        completed = sum(1 for s in sessions if s.status == "completed")

        lines = [
            f"Period: last {days} days",
            f"Sessions: {len(sessions)} ({completed} completed,"
            f" {len(sessions) - completed} active)",
            f"Total tool calls: {total_calls}",
            f"Total tokens: {total_input:,} in / {total_output:,} out",
            f"Total cost: ${total_cost:.4f}",
        ]
        if sessions:
            lines.append(f"Average cost per session: ${total_cost / len(sessions):.4f}")
        return "\n".join(lines)

    def get_dashboard(self) -> str:
        sessions = self.__load_recent_sessions(days=30)
        if not sessions:
            return "No sessions recorded yet."

        by_agent: dict[str, list[AgentSession]] = {}
        for session in sessions:
            by_agent.setdefault(session.agent_name, []).append(session)

        lines = ["PERFORMANCE DASHBOARD — last 30 days", ""]
        for agent, agent_sessions in sorted(by_agent.items()):
            total_cost = sum(s.total_cost_usd for s in agent_sessions)
            total_calls = sum(s.total_tool_calls for s in agent_sessions)
            lines.append(
                f"{agent}: {len(agent_sessions)} sessions, {total_calls} calls, ${total_cost:.4f}"
            )

        lines += ["", "Recent sessions:"]
        for session in sorted(sessions, key=lambda s: s.started_at, reverse=True)[:10]:
            date_str = session.started_at.strftime("%Y-%m-%d %H:%M")
            duration = f"{session.duration_seconds:.0f}s" if session.duration_seconds else "active"
            lines.append(
                f"  {date_str} {session.agent_name}/{session.model}"
                f" → {session.total_tool_calls} calls"
                f" ${session.total_cost_usd:.4f} ({duration})"
            )

        return "\n".join(lines)

    def __find_session_file(self, session_id: str) -> Path | None:
        sessions_path = self._vault.performance_path / "sessions"
        for f in self._vault.list_files(sessions_path):
            if f.stem.endswith(f"-{session_id}"):
                return f
        return None

    def __load_recent_sessions(self, days: int) -> list[AgentSession]:
        cutoff = datetime.now(UTC) - timedelta(days=days)
        sessions: list[AgentSession] = []
        for f in self._vault.list_files(self._vault.performance_path / "sessions"):
            try:
                session = AgentSession.from_content(self._vault.read(f))
                if session is None:
                    continue
                started = session.started_at
                if started.tzinfo is None:
                    started = started.replace(tzinfo=UTC)
                if started >= cutoff:
                    sessions.append(session)
            except Exception:
                continue
        return sessions

    @staticmethod
    def __replace_frontmatter(content: str, new_frontmatter: str) -> str:
        """Swap out the frontmatter block while keeping the body intact."""
        parts = re.split(r"\n---\n", content, maxsplit=1)
        body = parts[1] if len(parts) == 2 else "\n"
        return f"{new_frontmatter}\n{body}"
