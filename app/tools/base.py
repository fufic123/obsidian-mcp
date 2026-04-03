"""Base class for all MCP tool groups — provides optional performance tracking."""

import functools
import time
from collections.abc import Callable
from typing import Any, TypeVar

from app.domain.interfaces.performance import IPerformanceService

F = TypeVar("F", bound=Callable[..., Any])


class BaseTools:
    """Wraps tool methods with optional performance tracking."""

    def __init__(
        self,
        performance_service: IPerformanceService | None,
        agent_name: str,
        model: str,
    ) -> None:
        self.__performance_service = performance_service
        self.__agent_name = agent_name
        self.__model = model
        self.__session_id: str | None = None
        if performance_service is not None:
            self.__session_id = performance_service.start_session(agent_name, model)

    def _wrap(self, fn: F) -> F:
        """Return fn wrapped with timing and performance recording if tracking is enabled."""
        if self.__performance_service is None:
            return fn

        performance_service = self.__performance_service
        session_id = self.__session_id

        @functools.wraps(fn)
        def tracked(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000
                if session_id:
                    performance_service.record_tool_call(
                        session_id=session_id,
                        tool_name=fn.__name__,
                        duration_ms=duration_ms,
                        status="ok",
                    )
                return result
            except Exception as exc:
                duration_ms = (time.perf_counter() - start) * 1000
                if session_id:
                    performance_service.record_tool_call(
                        session_id=session_id,
                        tool_name=fn.__name__,
                        duration_ms=duration_ms,
                        status="error",
                        error=str(exc),
                    )
                raise

        return tracked  # type: ignore[return-value]
