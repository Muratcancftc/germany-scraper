from app.scraper.normalizers.normalizer import (
    normalize_email,
    normalize_house_number,
    normalize_phone,
    normalize_website,
)
from app.scraper.sources.base import CompanyCandidate


def normalize_candidate(candidate: CompanyCandidate) -> CompanyCandidate:
    """Normalize candidate fields in place and return it."""
    candidate.phone = normalize_phone(candidate.phone)
    candidate.email = normalize_email(candidate.email)
    candidate.website = normalize_website(candidate.website)
    candidate.house_number = normalize_house_number(candidate.house_number)
    if candidate.name:
        candidate.name = " ".join(candidate.name.split())
    return candidate
