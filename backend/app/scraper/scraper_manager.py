"""ScrapingManager orchestrates one scraping job end-to-end, fully in-memory.

Flow for each (city, category) combination:
  source.search() -> company urls
    -> for each url: source.extract_company()
      -> normalize -> validate category -> dedupe/merge -> store in memory
      -> emit realtime event

Errors on individual companies never abort the job. Concurrency of page
loading is bounded by MAX_CONCURRENT_PAGES. No database is used.
"""

import asyncio
from datetime import datetime

from app.core.config import settings
from app.core.logging.logger import logger
from app.core.store.job_store import CompanyRecord, job_store
from app.scraper.deduplication.deduplicator import deduplicator
from app.scraper.engines.camoufox_engine import camoufox_engine
from app.scraper.engines.http_engine import http_engine
from app.scraper.normalizers.pipeline import normalize_candidate
from app.scraper.sources import iter_sources
from app.scraper.validators.candidate_validator import candidate_validator
from app.scraper.validators.category_validator import category_validator
from app.services.event.event_service import event_service
from app.services.persistence.supabase_store import supabase_store


class ScrapingManager:
    def __init__(self, max_pages: int = 0):
        self.max_pages = max_pages or settings.MAX_CONCURRENT_PAGES
        self._semaphore = asyncio.Semaphore(self.max_pages)

    async def run_job(
        self,
        job_id: int,
        cities: list[tuple[int, str]],
        categories: list[tuple[int, str, list[str], list[str]]],
        max_results: int = 0,
    ) -> None:
        await self._set_status(job_id, "starting")
        await event_service.emit(job_id, "job_started", "Scraping gestartet")
        await self._set_status(job_id, "running")
        await self._persist_job(job_id)

        total_combos = len(cities) * len(categories)
        combo_idx = 0
        sources = iter_sources()

        try:
            for city_id, city_name in cities:
                for cat_id, cat_name, search_terms, cat_keywords in categories:
                    combo_idx += 1
                    await self._process_combination(
                        job_id,
                        city_name,
                        cat_name,
                        search_terms,
                        cat_keywords,
                        sources,
                        max_results,
                    )
                    progress = (combo_idx / total_combos) * 100 if total_combos else 100
                    await event_service.emit(
                        job_id,
                        "progress",
                        f"Fortschritt {progress:.0f}%",
                        progress=progress,
                    )
                    await asyncio.sleep(settings.REQUEST_DELAY_MS / 1000)

            await self._set_status(job_id, "completed")
            await event_service.emit(
                job_id, "job_completed", "Scraping abgeschlossen", progress=100
            )
            await self._persist_job(job_id)
        except asyncio.CancelledError:
            await self._set_status(job_id, "cancelled")
            await event_service.emit(job_id, "job_cancelled", "Scraping abgebrochen")
            await self._persist_job(job_id)
            raise
        except Exception as exc:
            logger.exception("Job failed", job_id=job_id)
            await self.fail_job(job_id, str(exc))
            await self._persist_job(job_id)
        finally:
            await http_engine.close()
            await camoufox_engine.close()

    async def fail_job(self, job_id: int, error: str) -> None:
        await self._set_status(job_id, "failed")
        await event_service.emit(job_id, "job_failed", f"Fehler: {error}")

    async def _process_combination(
        self,
        job_id: int,
        city: str,
        category: str,
        search_terms: list[str],
        category_keywords: list[str],
        sources,
        max_results: int,
    ) -> None:
        await event_service.emit(
            job_id,
            "search_started",
            f"{city} / {category} wird gesucht",
            city=city,
            category=category,
        )

        all_urls: list[tuple[object, str]] = []
        for source in sources:
            if not source.supports(city, category):
                continue
            try:
                urls = await source.search(
                    city, category, search_terms, http_engine, max_results
                )
                for url in urls:
                    all_urls.append((source, url))
                if urls:
                    await event_service.emit(
                        job_id,
                        "search_completed",
                        f"{len(urls)} Ergebnisse von {source.name}",
                        city=city,
                        category=category,
                    )
            except Exception as exc:
                logger.warning("Source search failed", source=source.name, error=str(exc))
                await event_service.emit(
                    job_id,
                    "page_failed",
                    f"Quelle {source.name} fehlgeschlagen",
                    city=city,
                    category=category,
                )

        if not all_urls:
            await event_service.emit(
                job_id,
                "search_completed",
                "Keine Ergebnisse gefunden",
                city=city,
                category=category,
            )
            return

        await self._update_counts(job_id, found=len(all_urls))

        if max_results and max_results > 0:
            all_urls = all_urls[:max_results]

        async def process(pair):
            src, url = pair
            async with self._semaphore:
                await self._process_url(job_id, url, src, city, category, category_keywords)

        tasks = [asyncio.create_task(process(pair)) for pair in all_urls]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _process_url(
        self, job_id, url, source, city, category, category_keywords
    ) -> None:
        await event_service.emit(
            job_id,
            "company_processing",
            f"Unternehmen wird verarbeitet: {url}",
            city=city,
            category=category,
        )
        try:
            candidate = await source.extract_company(
                url, http_engine, city=city, category=category
            )
        except Exception as exc:
            logger.warning("Extraction failed", url=url, error=str(exc))
            await event_service.emit(
                job_id,
                "company_failed",
                "Fehler beim Abrufen dieser Seite",
                city=city,
                category=category,
            )
            await self._update_counts(job_id, failed=1)
            return

        errors = candidate_validator.validate(candidate)
        if errors:
            await self._update_counts(job_id, failed=1)
            return

        candidate = normalize_candidate(candidate)

        if not category_validator.validate(candidate, category_keywords):
            await event_service.emit(
                job_id,
                "company_rejected",
                f"Kategorie-Prüfung: {candidate.name} übersprungen",
                city=city,
                category=category,
                company_name=candidate.name,
            )
            await self._update_counts(job_id, rejected=1)
            return

        record = CompanyRecord(
            name=candidate.name,
            category=category,
            phone=candidate.phone,
            email=candidate.email,
            website=candidate.website,
            street=candidate.street,
            house_number=candidate.house_number,
            postal_code=candidate.postal_code,
            city=candidate.city or city,
            state=candidate.state,
            country=candidate.country or "DE",
            source=candidate.source or source.name,
            source_url=candidate.source_url or url,
        )

        job = await job_store.get(job_id)
        if job is None:
            return

        # Persistent dedup (cross-job): if this company already exists in
        # Supabase, treat it as a duplicate regardless of the in-memory scope.
        if supabase_store.enabled():
            existing_db = await supabase_store.find_company(record)
            if existing_db:
                await self._update_counts(job_id, duplicates=1)
                await event_service.emit(
                    job_id,
                    "company_duplicate",
                    f"Bereits vorhanden: {record.name}",
                    city=city,
                    category=category,
                    company_name=record.name,
                )
                return

        decision = deduplicator.find_duplicate(job, record)
        if decision.is_duplicate and decision.existing:
            merged = deduplicator.merge_into(decision.existing, record)
            if merged:
                await self._update_counts(job_id, merged=1)
                await event_service.emit(
                    job_id,
                    "company_merged",
                    f"Duplikat erweitert: {record.name}",
                    city=city,
                    category=category,
                    company_name=record.name,
                    payload={"company": job_store._record_dict(decision.existing)},
                )
            else:
                await self._update_counts(job_id, duplicates=1)
                await event_service.emit(
                    job_id,
                    "company_duplicate",
                    f"Duplikat übersprungen: {record.name}",
                    city=city,
                    category=category,
                    company_name=record.name,
                )
            return

        deduplicator.register(job, record)
        job.results.append(record)
        await self._update_counts(job_id, added=1)
        await event_service.emit(
            job_id,
            "company_added",
            f"Firma gespeichert: {record.name}",
            city=city,
            category=category,
            company_name=record.name,
            payload={"company": job_store._record_dict(record)},
        )
        if supabase_store.enabled():
            row = await supabase_store.save_company(record)
            if row and row.get("id") is not None:
                await supabase_store.link_company_to_job(job_id, row["id"])

    # --- helpers --------------------------------------------------------
    async def _persist_job(self, job_id: int) -> None:
        if not supabase_store.enabled():
            return
        job = await job_store.get(job_id)
        if not job:
            return
        await supabase_store.save_job(
            job_id,
            status=job.status,
            city_count=job.city_count,
            category_count=job.category_count,
            total_found=job.total_found,
            total_added=job.total_added,
            total_duplicates=job.total_duplicates,
            total_merged=job.total_merged,
            total_failed=job.total_failed,
        )

    async def _set_status(self, job_id: int, status: str) -> None:
        now = datetime.utcnow().isoformat()
        fields: dict = {"status": status}
        if status == "running":
            fields["started_at"] = now
        if status in ("completed", "failed", "cancelled"):
            fields["completed_at"] = now
        await job_store.update(job_id, **fields)

    async def _update_counts(self, job_id: int, **deltas) -> None:
        job = await job_store.get(job_id)
        if not job:
            return
        updates: dict = {}
        for field, value in deltas.items():
            updates[f"total_{field}"] = getattr(job, f"total_{field}", 0) + value
        await job_store.update(job_id, **updates)


scraping_manager = ScrapingManager()
