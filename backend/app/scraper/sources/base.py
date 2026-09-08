from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.scraper.extractors.company_data import CompanyDataExtractor


@dataclass
class CompanyCandidate:
    """Normalized, validated company data produced by a source."""

    name: str = ""
    phone: str | None = None
    email: str | None = None
    website: str | None = None
    street: str | None = None
    house_number: str | None = None
    postal_code: str | None = None
    city: str | None = None
    state: str | None = None
    country: str = "DE"
    category: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    source: str = ""
    source_url: str | None = None
    full_address: str | None = None

class BaseSource(ABC):
    """Adapter contract every scraping source must implement.

    New sources can be added without modifying existing ones. Each source
    produces :class:`CompanyCandidate` objects that flow into the common
    normalize -> validate -> deduplicate -> save pipeline.
    """

    name: str = "base"
    extractor: CompanyDataExtractor = CompanyDataExtractor()

    @abstractmethod
    def supports(self, city: str, category: str) -> bool:
        """Whether this source can handle the given city/category combo."""

    @abstractmethod
    def get_search_query(self, city: str, category: str) -> str:
        """Build a deterministic search query for the source."""

    @abstractmethod
    async def search(
        self,
        city: str,
        category: str,
        search_terms: list[str],
        engine,
        max_results: int = 0,
    ) -> list[str]:
        """Return a list of company detail page URLs to process."""

    @abstractmethod
    async def extract_company(
        self,
        url: str,
        engine,
        city: str = "",
        category: str = "",
    ) -> CompanyCandidate | None:
        """Load a detail page and return a CompanyCandidate or None."""
