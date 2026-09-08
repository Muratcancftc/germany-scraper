"""Validation rules applied to a CompanyCandidate before saving."""

from __future__ import annotations

from app.scraper.sources.base import CompanyCandidate


class CandidateValidator:
    """Deterministic validity checks. Never invents data."""

    MIN_NAME_LENGTH = 2

    def validate(self, candidate: CompanyCandidate | None) -> list[str]:
        """Return a list of reasons the candidate is invalid (empty = valid)."""
        errors: list[str] = []
        if candidate is None:
            return ["candidate_is_none"]
        if not candidate.name or len(candidate.name.strip()) < self.MIN_NAME_LENGTH:
            errors.append("missing_name")
        return errors

candidate_validator = CandidateValidator()
