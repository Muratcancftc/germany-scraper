"""Source adapter registry.

Add new sources by subclassing :class:`BaseSource` and registering an instance
here. The rest of the system (scraper manager, pipeline) only depends on the
abstract interface, so new sources never break existing code.
"""

from __future__ import annotations

from app.scraper.sources.base import BaseSource, CompanyCandidate
from app.scraper.sources.directory import DirectorySource
from app.scraper.sources.website import WebsiteSource


class SourceRegistry:
    def __init__(self):
        self._sources: dict[str, BaseSource] = {}

    def register(self, source: BaseSource) -> None:
        self._sources[source.name] = source

    def get(self, name: str) -> BaseSource | None:
        return self._sources.get(name)

    def all(self) -> list[BaseSource]:
        return list(self._sources.values())


registry = SourceRegistry()
registry.register(DirectorySource())
registry.register(WebsiteSource())


def get_source(name: str) -> BaseSource | None:
    return registry.get(name)


def iter_sources() -> list[BaseSource]:
    return registry.all()


__all__ = [
    "BaseSource",
    "CompanyCandidate",
    "registry",
    "get_source",
    "iter_sources",
]
