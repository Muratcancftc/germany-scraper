"""Deterministic category validation.

Checks whether a scraped company actually belongs to the requested category
using keyword matching against the category's `keywords` (no AI). Only signals
that were actually extracted from the page are used; nothing is invented.
"""

from __future__ import annotations

from app.scraper.sources.base import CompanyCandidate


def _text_signals(candidate: CompanyCandidate) -> list[str]:
    """Collect the textual signals we can deterministically inspect."""
    signals: list[str] = []
    if candidate.name:
        signals.append(candidate.name)
    if candidate.full_address:
        signals.append(candidate.full_address)
    # category field (from source/structured data) is a strong signal
    if candidate.category:
        signals.append(candidate.category)
    return [s.lower() for s in signals if s]

class CategoryValidator:
    """Validates a candidate against a category's keyword dictionary."""

    # Some generic words are too weak to validate on their own.
    WEAK_KEYWORDS = {"gemeinde", "stadt", "kirche", "verein", "pflege"}

    def validate(
        self, candidate: CompanyCandidate | None, keywords: list[str]
    ) -> bool:
        """Return True if the candidate plausibly belongs to the category.

        A candidate is accepted if any *strong* keyword is found in its name,
        category field, or full address. Missing data simply means the check
        cannot confirm — it never invents a match.
        """
        if candidate is None or not keywords:
            return True  # no category validation configured -> accept

        signals = _text_signals(candidate)
        if not signals:
            return True  # nothing to check against, don't over-reject

        for keyword in keywords:
            kw = keyword.strip().lower()
            if not kw or kw in self.WEAK_KEYWORDS:
                continue
            for signal in signals:
                if kw in signal:
                    return True
        return False

category_validator = CategoryValidator()
