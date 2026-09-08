"""Realtime event service: per-job asyncio queues consumed by SSE streams.

On Vercel Functions every request runs in an isolated invocation, so events are
delivered to whichever SSE stream is subscribed to a job inside the same request
that runs the job. A per-job queue (asyncio.Queue) is created by the SSE endpoint
and fed by this service; the stream generator drains it. No database is used.
"""

from __future__ import annotations

import asyncio
from datetime import datetime

# job_id -> list of subscriber queues
_subscribers: dict[int, list[asyncio.Queue]] = {}
_subscribers_lock = asyncio.Lock()

MAX_EVENTS_PER_JOB = 2000
_job_events: dict[int, list[dict]] = {}


def subscribe(job_id: int) -> asyncio.Queue:
    """Register a queue for a job and return it. The SSE generator drains it."""
    q: asyncio.Queue = asyncio.Queue(maxsize=0)
    _subscribers.setdefault(job_id, []).append(q)
    return q


def unsubscribe(job_id: int, q: asyncio.Queue) -> None:
    subs = _subscribers.get(job_id)
    if subs and q in subs:
        subs.remove(q)
        if not subs:
            _subscribers.pop(job_id, None)


def _log_event(job_id: int, event: dict) -> None:
    log = _job_events.setdefault(job_id, [])
    log.append(event)
    if len(log) > MAX_EVENTS_PER_JOB:
        del log[: len(log) - MAX_EVENTS_PER_JOB]


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

        for q in _subscribers.get(job_id, []):
            try:
                q.put_nowait(event)
            except Exception:
                pass

    def get_events(self, job_id: int, limit: int = 500) -> list[dict]:
        events = _job_events.get(job_id, [])
        return events[-limit:]

    def clear(self, job_id: int) -> None:
        _job_events.pop(job_id, None)


event_service = EventService()
