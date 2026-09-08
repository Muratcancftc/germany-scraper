from __future__ import annotations

import asyncio

from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import StreamingResponse

from app.core.catalog import CATEGORIES, CATEGORY_GROUPS, CITIES, category_by_id, city_by_id
from app.core.schemas import (
    CategoryResponse,
    CityResponse,
    CreateJobRequest,
    DashboardStats,
    ScrapeEventResponse,
)
from app.core.store.job_store import job_store
from app.scraper.scraper_manager import scraping_manager
from app.services.event.event_service import event_service, subscribe, unsubscribe
from app.services.export.export_service import export_service

router = APIRouter(prefix="/api", tags=["scrape"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _sse(event: dict) -> str:
    import json

    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


# --- cities & categories (from static in-memory catalog) ------------------
@router.get("/cities", response_model=list[CityResponse])
async def get_cities():
    return [
        CityResponse(id=c.id, name=c.name, slug=c.slug, state=c.state, active=True)
        for c in CITIES
    ]


@router.get("/categories", response_model=list[CategoryResponse])
async def get_categories():
    return [
        CategoryResponse(
            id=c.id,
            name=c.name,
            slug=c.slug,
            group=CATEGORY_GROUPS.get(c.group, c.group),
            description=c.description,
            search_terms=c.search_terms,
            keywords=c.keywords,
            active=True,
        )
        for c in CATEGORIES
    ]


# --- jobs: run inline and stream SSE events ---------------------------------
@router.post("/scrape/jobs")
async def create_job(request: CreateJobRequest):
    """Start a scraping job and stream its events as SSE.

    The job runs synchronously inside this single request (Vercel Functions are
    stateless, so there is no background worker to poll). The frontend reads the
    `text/event-stream` response and renders results live.
    """
    city_pairs: list[tuple[int, str]] = []
    for cid in request.city_ids:
        city = city_by_id(cid)
        if not city:
            raise HTTPException(404, f"City {cid} not found")
        city_pairs.append((city.id, city.name))

    cat_info: list[tuple[int, str, list[str], list[str]]] = []
    for cid in request.category_ids:
        cat = category_by_id(cid)
        if not cat:
            raise HTTPException(404, f"Category {cid} not found")
        cat_info.append((cat.id, cat.name, cat.search_terms, cat.keywords))

    job = await job_store.create_job(len(city_pairs), len(cat_info))
    job_id = job.id

    q = subscribe(job_id)
    task = asyncio.create_task(
        scraping_manager.run_job(
            job_id,
            city_pairs,
            cat_info,
            max_results=request.max_results or 0,
        )
    )

    async def event_stream():
        try:
            yield _sse({"event_type": "job_started", "job_id": job_id})
            while True:
                event = await q.get()
                yield _sse(event)
                if event["event_type"] in ("job_completed", "job_failed", "job_cancelled"):
                    break
        finally:
            if not task.done():
                task.cancel()
            unsubscribe(job_id, q)
            event_service.clear(job_id)

    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=SSE_HEADERS)


@router.get("/scrape/jobs/{job_id}/events", response_model=list[ScrapeEventResponse])
async def get_job_events(job_id: int):
    return [ScrapeEventResponse.model_validate(e) for e in event_service.get_events(job_id)]


@router.get("/scrape/jobs/{job_id}", response_model=dict)
async def get_job(job_id: int):
    data = await job_store.job_dict(job_id)
    if not data:
        raise HTTPException(404, "Job not found")
    return data


# --- export (stateless: companies come in the request body) -----------------
@router.post("/scrape/export/excel")
async def export_excel(companies: list[dict] = Body(..., embed=True)):
    return export_service.export_excel(companies)


@router.post("/scrape/export/pdf")
async def export_pdf(companies: list[dict] = Body(..., embed=True)):
    return export_service.export_pdf(companies)


# --- dashboard ----------------------------------------------------------
@router.get("/dashboard/stats", response_model=DashboardStats)
async def dashboard_stats():
    jobs = await job_store.list_jobs()
    total_companies = sum(j.total_added for j in jobs)
    active_scrapes = sum(1 for j in jobs if j.status in ("queued", "starting", "running"))
    completed = sum(1 for j in jobs if j.status == "completed")
    total_jobs = len(jobs)
    success_rate = round((completed / total_jobs * 100) if total_jobs else 0, 1)
    return DashboardStats(
        total_companies=total_companies,
        today_found=total_companies,
        active_scrapes=active_scrapes,
        success_rate=success_rate,
    )
