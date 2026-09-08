"""Directory-based source: searches an online directory for businesses."""

from __future__ import annotations

from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

from app.core.logging.logger import logger
from app.scraper.extractors.company_data import CompanyDataExtractor
from app.scraper.extractors.pages import PageDiscovery
from app.scraper.normalizers.normalizer import normalize_website
from app.scraper.sources.base import BaseSource, CompanyCandidate


class DirectorySource(BaseSource):
    """Reference implementation against a generic directory site.

    The host and URL patterns are configuration-driven so the adapter can be
    pointed at different directories without code changes. Without a matching
    directory the source simply returns no results.
    """

    name = "directory"

    def __init__(self, host: str = "www.gelbeseiten.de", search_path: str = "/suche/{query}"):
        self.host = host
        self.search_path = search_path
        self.extractor = CompanyDataExtractor()
        self.discovery = PageDiscovery()

    def supports(self, city: str, category: str) -> bool:
        return bool(city and category)

    def get_search_query(self, city: str, category: str) -> str:
        return f"{category} {city}"

    def _search_url(self, query: str) -> str:
        path = self.search_path.replace("{query}", quote(query))
        return f"https://{self.host}{path}"

    async def search(
        self,
        city: str,
        category: str,
        search_terms: list[str],
        engine,
        max_results: int = 0,
    ) -> list[str]:
        """Search the directory for each German search term of the category."""
        terms = search_terms or [category]
        result_urls: list[str] = []
        seen: set[str] = set()
        per_term = max_results if max_results else 0

        for term in terms:
            query = self.get_search_query(city, term)
            url = self._search_url(query)
            try:
                html = await engine.get_html(url)
            except Exception as exc:
                logger.warning("Directory search failed", url=url, error=str(exc))
                continue

            for candidate in self._parse_result_links(html):
                if candidate not in seen:
                    seen.add(candidate)
                    result_urls.append(candidate)
            if per_term and len(result_urls) >= per_term:
                break

        return result_urls

    def _parse_result_links(self, html: str) -> list[str]:
        soup = BeautifulSoup(html, "lxml")
        result_urls: list[str] = []
        seen: set[str] = set()
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not a.get_text(" ", strip=True):
                continue
            if any(x in href for x in (".pdf", ".png", ".jpg", "javascript:", "#")):
                continue
            url = urljoin(f"https://{self.host}", href)
            slug = url.rstrip("/").split("/")[-1].lower()
            if len(slug) > 2 and url not in seen:
                seen.add(url)
                result_urls.append(url)
        return result_urls

    async def extract_company(self, url, engine, city="", category="") -> CompanyCandidate | None:
        try:
            html = await engine.get_html(url)
        except Exception as exc:
            logger.warning("Company page failed", url=url, error=str(exc))
            return None

        data = self.extractor.extract(html, page_url=url)
        website = normalize_website(data.get("website"))
        name = data.get("name") or self._infer_name_from_url(url)

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
            source_url=url,
            full_address=", ".join(
                filter(None, [
                    data.get("address", {}).get("street"),
                    data.get("address", {}).get("postal_code"),
                    data.get("address", {}).get("city"),
                ])
            ) or None,
        )

        if website:
            await self._enrich_from_website(candidate, website, engine)

        return candidate

    async def _enrich_from_website(self, candidate, website, engine):
        """Fetch contact/impressum pages to fill missing email/phone."""
        if candidate.email and candidate.phone:
            return
        try:
            html = await engine.get_html(website)
        except Exception:
            return
        discovered = self.discovery.discover(website, html)
        for key in ("impressum", "contact", "about"):
            page_url = discovered.get(key)
            if not page_url or (candidate.email and candidate.phone):
                continue
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
        from urllib.parse import unquote

        slug = unquote(url.rstrip("/").split("/")[-1])
        return slug.replace("-", " ").replace("_", " ").strip().title()
