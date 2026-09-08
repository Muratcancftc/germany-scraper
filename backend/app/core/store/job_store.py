"""In-memory job store.

Holds all scraping state for active jobs: results, deduplication sets,
progress counters and the event log. No database is used. State is lost when
the process exits — acceptable for this version (results are kept until the
user exports them).
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from itertools import count

from app.core.logging.logger import logger


@dataclass
class CompanyRecord:
    name: str
    category: str = ""
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    street: str | None = None
    house_number: str | None = None
    postal_code: str | None = None
    city: str | None = None
    state: str | None = None
    country: str = "DE"
    source: str = ""
    source_url: str | None = None
    found_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class JobState:
    id: int
    status: str = "queued"  # queued|starting|running|completed|failed|cancelled
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: str | None = None
    completed_at: str | None = None
    city_count: int = 0
    category_count: int = 0
    total_found: int = 0
    total_added: int = 0
    total_duplicates: int = 0
    total_merged: int = 0
    total_failed: int = 0
    total_rejected: int = 0
    current: str = ""  # human-readable "currently processing" message
    # dedup keys -> company record for merge
    by_website: dict[str, CompanyRecord] = field(default_factory=dict)
    by_phone: dict[str, CompanyRecord] = field(default_factory=dict)
    by_email: dict[str, CompanyRecord] = field(default_factory=dict)
    by_name_city: dict[tuple[str, str], CompanyRecord] = field(default_factory=dict)
    results: list[CompanyRecord] = field(default_factory=list)


class JobStore:
    """Thread-safe in-memory storage for all jobs."""

    def __init__(self):
        self._counter = count(1)
        self._jobs: dict[int, JobState] = {}
        self._lock = asyncio.Lock()

    async def create_job(self, city_count: int, category_count: int) -> JobState:
        async with self._lock:
            job = JobState(
                id=next(self._counter),
                city_count=city_count,
                category_count=category_count,
            )
            self._jobs[job.id] = job
            logger.info("Job created", job_id=job.id)
            return job

    async def get(self, job_id: int) -> JobState | None:
        return self._jobs.get(job_id)

    async def list_jobs(self) -> list[JobState]:
        jobs = sorted(self._jobs.values(), key=lambda j: j.id, reverse=True)
        return jobs

    async def update(self, job_id: int, **fields) -> None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job:
                for k, v in fields.items():
                    setattr(job, k, v)

    async def delete(self, job_id: int) -> None:
        async with self._lock:
            self._jobs.pop(job_id, None)

    def _snapshot_job(self, job: JobState) -> dict:
        return {
            "id": job.id,
            "status": job.status,
            "created_at": job.created_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "city_count": job.city_count,
            "category_count": job.category_count,
            "total_found": job.total_found,
            "total_added": job.total_added,
            "total_duplicates": job.total_duplicates,
            "total_merged": job.total_merged,
            "total_failed": job.total_failed,
            "total_rejected": job.total_rejected,
            "current": job.current,
        }

    async def job_dict(self, job_id: int) -> dict | None:
        job = self._jobs.get(job_id)
        return self._snapshot_job(job) if job else None

    async def list_job_dicts(self) -> list[dict]:
        return [self._snapshot_job(j) for j in await self.list_jobs()]

    async def results(self, job_id: int) -> list[dict]:
        job = self._jobs.get(job_id)
        if not job:
            return []
        return [self._record_dict(r) for r in job.results]

    @staticmethod
    def _record_dict(r: CompanyRecord) -> dict:
        return {
            "id": hash((r.name, r.website, r.phone)),
            "name": r.name,
            "category": r.category,
            "phone": r.phone,
            "email": r.email,
            "website": r.website,
            "street": r.street,
            "house_number": r.house_number,
            "postal_code": r.postal_code,
            "city": r.city,
            "state": r.state,
            "country": r.country,
            "source": r.source,
            "source_url": r.source_url,
            "found_at": r.found_at,
            "phone_verified": bool(r.phone),
            "email_verified": bool(r.email),
            "website_verified": bool(r.website),
        }


job_store = JobStore()
