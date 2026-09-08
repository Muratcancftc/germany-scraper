"""Website source: given a known company website, extract full company data."""

from __future__ import annotations

from app.core.logging.logger import logger
from app.scraper.extractors.company_data import CompanyDataExtractor
from app.scraper.extractors.pages import PageDiscovery
from app.scraper.normalizers.normalizer import normalize_website
from app.scraper.sources.base import BaseSource, CompanyCandidate


class WebsiteSource(BaseSource):
    """Processes a company's own website (often reached from a directory).

    Extracts name, contact details, and address directly from the homepage
    plus contact/impressum pages when available.
    """

    name = "website"

    def __init__(self):
        self.extractor = CompanyDataExtractor()
        self.discovery = PageDiscovery()

    def supports(self, city: str, category: str) -> bool:
        return True

    def get_search_query(self, city: str, category: str) -> str:
        return f"{category} {city}"

    async def search(
        self,
        city: str,
        category: str,
        search_terms: list[str],
        engine,
        max_results: int = 0,
    ) -> list[str]:
        # Website source receives explicit URLs, so no bulk search.
        return []

    async def extract_company(self, url, engine, city="", category="") -> CompanyCandidate | None:
        website = normalize_website(url)
        if not website:
            return None
        try:
            html = await engine.get_html(website)
        except Exception as exc:
            logger.warning("Website load failed", url=website, error=str(exc))
            return None

        data = self.extractor.extract(html, page_url=website)
        name = data.get("name") or self._infer_name_from_url(website)

        candidate = CompanyCandidate(
            name=name,
            phone=data.get("phone"),
            email=data.get("email"),
            website=website,
            street=data.get("address", {}).get("street"),
            house_number=data.get("address", {}).get("house_number"),
            postal_code=data.get("address", {}).get("postal_code"),
            city=city or data.get("address", {}).get("city"),
            state=data.get("address", {}).get("state"),
            country="DE",
            category=category,
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            source=self.name,
            source_url=website,
            full_address=", ".join(
                filter(None, [
                    data.get("address", {}).get("street"),
                    data.get("address", {}).get("postal_code"),
                    data.get("address", {}).get("city"),
                ])
            ) or None,
        )

        await self._enrich_from_website(candidate, website, html, engine)
        return candidate

    async def _enrich_from_website(self, candidate, website, home_html, engine):
        if candidate.email and candidate.phone and candidate.street:
            return
        discovered = self.discovery.discover(website, home_html)
        for key in ("impressum", "contact", "about"):
            page_url = discovered.get(key)
            if not page_url:
                continue
            if candidate.email and candidate.phone and candidate.street:
                break
            try:
                page_html = await engine.get_html(page_url)
            except Exception:
                continue
            page_data = self.extractor.extract(page_html, page_url=page_url)
            candidate.email = candidate.email or page_data.get("email")
            candidate.phone = candidate.phone or page_data.get("phone")
            if not candidate.street:
                addr = page_data.get("address", {})
                candidate.street = addr.get("street") or candidate.street
                candidate.postal_code = addr.get("postal_code") or candidate.postal_code

    @staticmethod
    def _infer_name_from_url(url: str) -> str:
        from urllib.parse import urlparse

        netloc = urlparse(url).netloc
        host = netloc.split(".")[0]
        return host.replace("-", " ").replace("_", " ").strip().title()
