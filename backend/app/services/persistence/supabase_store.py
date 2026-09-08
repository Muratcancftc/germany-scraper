"""Supabase persistence via direct Postgres (asyncpg): persistent dedup + history.

When a Supabase Postgres connection string is configured, companies are stored
with a normalized `dedup_key` (website > phone > email > name+city). This gives
cross-job deduplication: the same company found in a later scrape is skipped
instead of added again. Jobs and their companies are persisted so the Ergebnisse
and Historie pages keep data across reloads.

If no connection string is configured, the app degrades gracefully to the
in-memory-only behavior (no persistence, job-scoped dedup).
"""

from __future__ import annotations

import asyncio

import asyncpg

from app.core.config import settings
from app.core.logging.logger import logger
from app.core.store.job_store import CompanyRecord

_pool: asyncpg.Pool | None = None
_pool_lock = asyncio.Lock()


async def _get_pool() -> asyncpg.Pool | None:
    global _pool
    if not settings.supabase_enabled:
        return None
    if _pool is not None:
        return _pool
    async with _pool_lock:
        if _pool is None:
            _pool = await asyncpg.create_pool(
                dsn=settings.SUPABASE_DATABASE_URL,
                ssl="require",
                min_size=1,
                max_size=4,
                timeout=20,
            )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


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
        key = dedup_key_for(record)
        if not key:
            return None
        pool = await _get_pool()
        if pool is None:
            return None
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM companies WHERE dedup_key = $1 LIMIT 1", key
                )
            return dict(row) if row else None
        except Exception as exc:
            logger.warning("Supabase find failed", error=str(exc))
            return None

    async def save_company(self, record: CompanyRecord) -> dict | None:
        """Insert or update a company. Returns the stored row (or None on failure)."""
        key = dedup_key_for(record)
        if not key:
            return None
        pool = await _get_pool()
        if pool is None:
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
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO companies (
                      dedup_key, name, phone, email, website, street, house_number,
                      postal_code, city, state, country, category, source, source_url
                    ) VALUES (
                      $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14
                    )
                    ON CONFLICT (dedup_key) DO UPDATE SET
                      name = EXCLUDED.name,
                      phone = COALESCE(companies.phone, EXCLUDED.phone),
                      email = COALESCE(companies.email, EXCLUDED.email),
                      website = COALESCE(companies.website, EXCLUDED.website),
                      street = COALESCE(companies.street, EXCLUDED.street),
                      house_number = COALESCE(companies.house_number, EXCLUDED.house_number),
                      postal_code = COALESCE(companies.postal_code, EXCLUDED.postal_code),
                      city = COALESCE(companies.city, EXCLUDED.city),
                      state = COALESCE(companies.state, EXCLUDED.state),
                      country = COALESCE(companies.country, EXCLUDED.country),
                      category = COALESCE(companies.category, EXCLUDED.category),
                      source = COALESCE(companies.source, EXCLUDED.source)
                    RETURNING *
                    """,
                    payload["dedup_key"],
                    payload["name"],
                    payload["phone"],
                    payload["email"],
                    payload["website"],
                    payload["street"],
                    payload["house_number"],
                    payload["postal_code"],
                    payload["city"],
                    payload["state"],
                    payload["country"],
                    payload["category"],
                    payload["source"],
                    payload["source_url"],
                )
            return dict(row) if row else None
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
        pool = await _get_pool()
        if pool is None:
            return
        payload = {
            "status": status,
            "city_count": city_count,
            "category_count": category_count,
            "total_found": counts.get("total_found", 0),
            "total_added": counts.get("total_added", 0),
            "total_duplicates": counts.get("total_duplicates", 0),
            "total_merged": counts.get("total_merged", 0),
            "total_failed": counts.get("total_failed", 0),
            "completed_at": (
                "now()" if status in ("completed", "failed", "cancelled") else None
            ),
        }
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO jobs (
                      id, status, city_count, category_count, total_found,
                      total_added, total_duplicates, total_merged, total_failed, completed_at
                    ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,
                      CASE WHEN $10 THEN now() ELSE NULL END)
                    ON CONFLICT (id) DO UPDATE SET
                      status = EXCLUDED.status,
                      city_count = EXCLUDED.city_count,
                      category_count = EXCLUDED.category_count,
                      total_found = EXCLUDED.total_found,
                      total_added = EXCLUDED.total_added,
                      total_duplicates = EXCLUDED.total_duplicates,
                      total_merged = EXCLUDED.total_merged,
                      total_failed = EXCLUDED.total_failed,
                      completed_at = COALESCE(jobs.completed_at, EXCLUDED.completed_at)
                    """,
                    job_id,
                    payload["status"],
                    payload["city_count"],
                    payload["category_count"],
                    payload["total_found"],
                    payload["total_added"],
                    payload["total_duplicates"],
                    payload["total_merged"],
                    payload["total_failed"],
                    status in ("completed", "failed", "cancelled"),
                )
        except Exception as exc:
            logger.warning("Supabase save_job failed", error=str(exc))

    async def link_company_to_job(self, job_id: int, company_id) -> None:
        if company_id is None:
            return
        pool = await _get_pool()
        if pool is None:
            return
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO job_companies (job_id, company_id) VALUES ($1,$2) "
                    "ON CONFLICT (job_id, company_id) DO NOTHING",
                    job_id,
                    company_id,
                )
        except Exception as exc:
            logger.warning("Supabase link failed", error=str(exc))

    async def list_companies(self, limit: int = 500) -> list[dict]:
        pool = await _get_pool()
        if pool is None:
            return []
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM companies ORDER BY found_at DESC LIMIT $1", limit
                )
            return [dict(r) for r in rows]
        except Exception as exc:
            logger.warning("Supabase list_companies failed", error=str(exc))
            return []

    async def list_jobs(self, limit: int = 100) -> list[dict]:
        pool = await _get_pool()
        if pool is None:
            return []
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT * FROM jobs ORDER BY created_at DESC LIMIT $1", limit
                )
            return [dict(r) for r in rows]
        except Exception as exc:
            logger.warning("Supabase list_jobs failed", error=str(exc))
            return []

    async def companies_for_job(self, job_id: int) -> list[dict]:
        pool = await _get_pool()
        if pool is None:
            return []
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT c.* FROM companies c
                    JOIN job_companies jc ON jc.company_id = c.id
                    WHERE jc.job_id = $1
                    ORDER BY c.found_at DESC
                    """,
                    job_id,
                )
            return [dict(r) for r in rows]
        except Exception as exc:
            logger.warning("Supabase companies_for_job failed", error=str(exc))
            return []

    async def delete_company(self, company_id) -> bool:
        """Delete a company by id. Returns True if a row was deleted."""
        if company_id is None:
            return False
        pool = await _get_pool()
        if pool is None:
            return False
        try:
            async with pool.acquire() as conn:
                result = await conn.execute(
                    "DELETE FROM companies WHERE id = $1", company_id
                )
            # asyncpg returns a status string like "DELETE 1"
            return "DELETE 1" in str(result)
        except Exception as exc:
            logger.warning("Supabase delete_company failed", error=str(exc))
            return False


supabase_store = SupabaseStore()
