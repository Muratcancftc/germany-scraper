"""Realtime event service: keeps an in-memory event log per job and broadcasts
over WebSocket. No database is used."""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime

from app.core.logging.logger import logger

# Pluggable async broadcaster (set by the websocket router to avoid circular imports)
Broadcaster = Callable[[int, dict], Awaitable[None]]
_broadcaster: Broadcaster | None = None
_broadcaster_lock = asyncio.Lock()


def set_broadcaster(fn: Broadcaster) -> None:
    global _broadcaster
    _broadcaster = fn


# In-memory event log per job (bounded to avoid unbounded growth).
MAX_EVENTS_PER_JOB = 2000
_job_events: dict[int, list[dict]] = {}


def _log_event(job_id: int, event: dict) -> None:
    log = _job_events.setdefault(job_id, [])
    log.append(event)
    if len(log) > MAX_EVENTS_PER_JOB:
        del log[: len(log) - MAX_EVENTS_PER_JOB]


def _clear_job(job_id: int) -> None:
    _job_events.pop(job_id, None)


class EventService:
    async def emit(
        self,
        job_id: int,
        event_type: str,
        message: str = "",
        city: str | None = None,
        category: str | None = None,
        company_name: str | None = None,
        progress: float = 0.0,
        payload: dict | None = None,
    ) -> None:
        event = {
            "id": len(_job_events.get(job_id, [])),
            "job_id": job_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "city": city,
            "category": category,
            "company_name": company_name,
            "message": message,
            "progress": progress,
            **({"payload": payload} if payload else {}),
        }
        _log_event(job_id, event)

        if _broadcaster:
            try:
                await _broadcaster(job_id, event)
            except Exception as exc:
                logger.debug("WS broadcast failed", error=str(exc))

    def get_events(self, job_id: int, limit: int = 500) -> list[dict]:
        events = _job_events.get(job_id, [])
        return events[-limit:]

    def clear(self, job_id: int) -> None:
        _clear_job(job_id)


event_service = EventService()
