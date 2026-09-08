"""Supabase persistence: persistent dedup + job history (optional).

When Supabase env vars are configured, companies are stored with a normalized
`dedup_key` (website > phone > email > name+city). This gives cross-job
deduplication: the same company found in a later scrape is updated/merged
instead of added again. Jobs and their companies are persisted so the Ergebnisse
and Historie pages keep data across reloads.

If Supabase is not configured, the app degrades gracefully to the in-memory-only
behavior (no persistence, job-scoped dedup).
"""

from __future__ import annotations

import asyncio

from app.core.config import settings
from app.core.logging.logger import logger
from app.core.store.job_store import CompanyRecord

_client = None
_client_lock = asyncio.Lock()


async def _get_client():
    global _client
    if _client is not None:
        return _client
    async with _client_lock:
        if _client is None:
            from supabase import create_async_client

            _client = await create_async_client(
                settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY
            )
    return _client


def dedup_key_for(record: CompanyRecord) -> str | None:
    """Deterministic dedup key: website > phone > email > name+city."""
    if record.website:
        return f"w:{record.website}"
    if record.phone:
        return f"p:{record.phone}"
    if record.email:
        return f"e:{record.email}"
    if record.name and record.city:
        name = " ".join(record.name.lower().split())
        return f"n:{name}|{record.city}"
    return None


class SupabaseStore:
    def enabled(self) -> bool:
        return settings.supabase_enabled

    async def find_company(self, record: CompanyRecord) -> dict | None:
        """Look up an existing company by its dedup key (persistent dedup)."""
        if not self.enabled():
            return None
        key = dedup_key_for(record)
        if not key:
            return None
        try:
            client = await _get_client()
            resp = (
                await client.table("companies")
                .select("*")
                .eq("dedup_key", key)
                .limit(1)
                .execute()
            )
            rows = resp.data or []
            return rows[0] if rows else None
        except Exception as exc:
            logger.warning("Supabase find failed", error=str(exc))
            return None

    async def save_company(self, record: CompanyRecord) -> dict | None:
        """Insert or update a company. Returns the stored row (or None on failure)."""
        if not self.enabled():
            return None
        key = dedup_key_for(record)
        if not key:
            return None
        payload = {
            "dedup_key": key,
            "name": record.name,
            "phone": record.phone,
            "email": record.email,
            "website": record.website,
            "street": record.street,
            "house_number": record.house_number,
            "postal_code": record.postal_code,
            "city": record.city,
            "state": record.state,
            "country": record.country or "DE",
            "category": record.category,
            "source": record.source,
            "source_url": record.source_url,
        }
        try:
            client = await _get_client()
            resp = (
                await client.table("companies")
                .upsert(payload, on_conflict="dedup_key")
                .execute()
            )
            rows = resp.data or []
            return rows[0] if rows else None
        except Exception as exc:
            logger.warning("Supabase save failed", error=str(exc))
            return None

    async def save_job(
        self,
        job_id: int,
        status: str,
        city_count: int = 0,
        category_count: int = 0,
        **counts,
    ) -> None:
        if not self.enabled():
            return
        payload = {
            "id": job_id,
            "status": status,
            "city_count": city_count,
            "category_count": category_count,
            "total_found": counts.get("total_found", 0),
            "total_added": counts.get("total_added", 0),
            "total_duplicates": counts.get("total_duplicates", 0),
            "total_merged": counts.get("total_merged", 0),
            "total_failed": counts.get("total_failed", 0),
            "completed_at": "now()" if status in ("completed", "failed", "cancelled") else None,
        }
        try:
            client = await _get_client()
            await client.table("jobs").upsert(payload, on_conflict="id").execute()
        except Exception as exc:
            logger.warning("Supabase save_job failed", error=str(exc))

    async def link_company_to_job(self, job_id: int, company_id) -> None:
        if not self.enabled() or company_id is None:
            return
        try:
            client = await _get_client()
            await client.table("job_companies").upsert(
                {"job_id": job_id, "company_id": company_id}, on_conflict="job_id,company_id"
            ).execute()
        except Exception as exc:
            logger.warning("Supabase link failed", error=str(exc))

    async def list_companies(self, limit: int = 500) -> list[dict]:
        if not self.enabled():
            return []
        try:
            client = await _get_client()
            resp = await (
                client.table("companies")
                .select("*")
                .order("found_at", desc=True)
                .limit(limit)
                .execute()
            )
            return resp.data or []
        except Exception as exc:
            logger.warning("Supabase list_companies failed", error=str(exc))
            return []

    async def list_jobs(self, limit: int = 100) -> list[dict]:
        if not self.enabled():
            return []
        try:
            client = await _get_client()
            resp = await (
                client.table("jobs")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return resp.data or []
        except Exception as exc:
            logger.warning("Supabase list_jobs failed", error=str(exc))
            return []

    async def companies_for_job(self, job_id: int) -> list[dict]:
        if not self.enabled():
            return []
        try:
            client = await _get_client()
            links = await (
                client.table("job_companies")
                .select("company_id")
                .eq("job_id", job_id)
                .execute()
            )
            ids = [row["company_id"] for row in (links.data or [])]
            if not ids:
                return []
            # Fetch in chunks (Supabase URL length limit).
            companies: list[dict] = []
            for i in range(0, len(ids), 100):
                chunk = ids[i : i + 100]
                resp = await client.table("companies").select("*").in_("id", chunk).execute()
                companies.extend(resp.data or [])
            return companies
        except Exception as exc:
            logger.warning("Supabase companies_for_job failed", error=str(exc))
            return []


supabase_store = SupabaseStore()
