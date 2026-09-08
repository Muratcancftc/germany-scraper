from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.core.catalog import CATEGORIES, CATEGORY_GROUPS, CITIES
from app.core.schemas import (
    CategoryResponse,
    CityResponse,
    CompanyResponse,
    CreateJobRequest,
    DashboardStats,
    ScrapeEventResponse,
    ScrapeJobResponse,
)
from app.core.store.job_store import job_store
from app.services.event.event_service import event_service
from app.services.export.export_service import export_service
from app.services.job.job_service import job_service

router = APIRouter(prefix="/api", tags=["scrape"])

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


# --- jobs ---------------------------------------------------------------
@router.post("/scrape/jobs", response_model=ScrapeJobResponse, status_code=201)
async def create_job(request: CreateJobRequest):
    job_id = await job_service.create_and_start(
        request.city_ids,
        request.category_ids,
        max_results=request.max_results or 0,
        max_concurrent_pages=request.max_concurrent_pages,
    )
    return ScrapeJobResponse.model_validate(await job_store.job_dict(job_id))


@router.get("/scrape/jobs", response_model=list[ScrapeJobResponse])
async def get_jobs():
    return [ScrapeJobResponse.model_validate(d) for d in await job_store.list_job_dicts()]


@router.get("/scrape/jobs/{job_id}", response_model=ScrapeJobResponse)
async def get_job(job_id: int):
    data = await job_store.job_dict(job_id)
    if not data:
        raise HTTPException(404, "Job not found")
    return ScrapeJobResponse.model_validate(data)


@router.post("/scrape/jobs/{job_id}/cancel")
async def cancel_job(job_id: int):
    cancelled = await job_service.cancel(job_id)
    if not cancelled:
        data = await job_store.job_dict(job_id)
        if data and data["status"] not in ("completed", "failed", "cancelled"):
            await job_store.update(job_id, status="cancelled")
            return {"status": "cancelled"}
        raise HTTPException(404, "Active job not found")
    return {"status": "cancelled"}


@router.get("/scrape/jobs/{job_id}/companies", response_model=list[CompanyResponse])
async def get_job_companies(
    job_id: int,
    has_email: bool = Query(False),
    has_phone: bool = Query(False),
    q: str = Query("", max_length=200),
):
    data = await job_store.job_dict(job_id)
    if not data:
        raise HTTPException(404, "Job not found")
    records = await job_store.results(job_id)
    if has_email:
        records = [r for r in records if r.get("email")]
    if has_phone:
        records = [r for r in records if r.get("phone")]
    if q:
        needle = q.lower()
        records = [
            r
            for r in records
            if needle in (r.get("name") or "").lower()
            or needle in (r.get("city") or "").lower()
            or needle in (r.get("category") or "").lower()
        ]
    return [CompanyResponse.model_validate(r) for r in records]


@router.get("/scrape/jobs/{job_id}/events", response_model=list[ScrapeEventResponse])
async def get_job_events(job_id: int):
    data = await job_store.job_dict(job_id)
    if not data:
        raise HTTPException(404, "Job not found")
    return [ScrapeEventResponse.model_validate(e) for e in event_service.get_events(job_id)]


# --- export -------------------------------------------------------------
@router.post("/scrape/jobs/{job_id}/export/excel")
async def export_excel(job_id: int):
    data = await job_store.job_dict(job_id)
    if not data:
        raise HTTPException(404, "Job not found")
    companies = await job_store.results(job_id)
    file_url = export_service.export_excel(job_id, companies)
    return {"status": "exported", "file_url": file_url, "count": len(companies)}


@router.post("/scrape/jobs/{job_id}/export/pdf")
async def export_pdf(job_id: int):
    data = await job_store.job_dict(job_id)
    if not data:
        raise HTTPException(404, "Job not found")
    companies = await job_store.results(job_id)
    file_url = export_service.export_pdf(job_id, companies, data)
    return {"status": "exported", "file_url": file_url, "count": len(companies)}


@router.get("/exports/{filename}")
async def get_export(filename: str):
    return await export_service.serve(filename)


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
