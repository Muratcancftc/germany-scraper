"""Job service: creates jobs from catalog ids and submits them to the in-memory
queue. No database is used — cities/categories come from the static catalog and
job state lives in the in-memory job store."""

from __future__ import annotations

import asyncio

from fastapi import HTTPException

from app.core.catalog import category_by_id, city_by_id
from app.core.logging.logger import logger
from app.core.store.job_store import job_store
from app.scraper.scraper_manager import scraping_manager
from app.services.job.job_queue import JobTask, job_queue


class JobService:
    async def create_and_start(
        self,
        city_ids: list[int],
        category_ids: list[int],
        max_results: int = 0,
        max_concurrent_pages: int | None = None,
    ) -> int:
        city_pairs: list[tuple[int, str]] = []
        for cid in city_ids:
            city = city_by_id(cid)
            if not city:
                raise HTTPException(404, f"City {cid} not found")
            city_pairs.append((city.id, city.name))

        cat_info: list[tuple[int, str, list[str], list[str]]] = []
        for cid in category_ids:
            cat = category_by_id(cid)
            if not cat:
                raise HTTPException(404, f"Category {cid} not found")
            cat_info.append((cat.id, cat.name, cat.search_terms, cat.keywords))

        job = await job_store.create_job(len(city_pairs), len(cat_info))

        if max_concurrent_pages:
            scraping_manager.max_pages = max_concurrent_pages
            scraping_manager._semaphore = asyncio.Semaphore(max_concurrent_pages)

        task = JobTask(
            job_id=job.id,
            runner=scraping_manager,
            cities=city_pairs,
            categories=cat_info,
            max_results=max_results,
        )
        job_queue.submit(task)
        logger.info("Job submitted", job_id=job.id, cities=len(city_pairs), cats=len(cat_info))
        return job.id

    async def cancel(self, job_id: int) -> bool:
        return await job_queue.cancel(job_id)


job_service = JobService()
