"""Job queue: runs scraping jobs in-process with concurrency limits."""

from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.core.config import settings
from app.core.logging.logger import logger

if TYPE_CHECKING:
    from app.scraper.scraper_manager import ScrapingManager

@dataclass
class JobTask:
    job_id: int
    runner: ScrapingManager
    cities: list[tuple[int, str]]
    categories: list[tuple[int, str, list[str], list[str]]]
    max_results: int = 0
    task: asyncio.Task | None = None

class JobQueue:
    """Serializes concurrent jobs up to MAX_CONCURRENT_JOBS."""

    def __init__(self, max_concurrent: int = 0):
        self.max_concurrent = max_concurrent or settings.MAX_CONCURRENT_JOBS
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        self._active: dict[int, JobTask] = {}
        self._queue: deque[JobTask] = deque()
        self._lock = asyncio.Lock()

    def submit(self, task: JobTask) -> None:
        task.task = asyncio.create_task(self._run(task))

    async def _run(self, task: JobTask) -> None:
        await self._semaphore.acquire()
        async with self._lock:
            self._active[task.job_id] = task
        try:
            await task.runner.run_job(
                task.job_id,
                task.cities,
                task.categories,
                max_results=task.max_results,
            )
        except Exception as exc:
            logger.exception("Job crashed", job_id=task.job_id, error=str(exc))
            await task.runner.fail_job(task.job_id, str(exc))
        finally:
            self._semaphore.release()
            async with self._lock:
                self._active.pop(task.job_id, None)

    async def cancel(self, job_id: int) -> bool:
        task = self._active.get(job_id)
        if not task or not task.task:
            return False
        task.task.cancel()
        return True

    def is_active(self, job_id: int) -> bool:
        return job_id in self._active

job_queue = JobQueue()
