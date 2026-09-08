"""In-memory duplicate detection with field-level merge.

Duplicate detection order (deterministic, per job):
1. Normalized website
2. Normalized phone
3. Email
4. Normalized name + city

Duplicate keys are kept in the job's in-memory state so each job has its own
deduplication scope. When a duplicate is found, missing fields are merged into
the existing record instead of creating a new one.
"""

from dataclasses import dataclass

from app.core.store.job_store import CompanyRecord, JobState


@dataclass
class DedupDecision:
    is_duplicate: bool
    existing: CompanyRecord | None = None
    match_type: str | None = None


def _name_key(name: str) -> str:
    import re

    key = name.lower()
    key = re.sub(r"[^a-z0-9äöüß ]", "", key)
    return " ".join(key.split())


class Deduplicator:
    """Detects duplicates within a single job's in-memory state and merges."""

    def find_duplicate(self, job: JobState, candidate: CompanyRecord) -> DedupDecision:
        if candidate.website:
            existing = job.by_website.get(candidate.website)
            if existing:
                return DedupDecision(True, existing, "website")
        if candidate.phone:
            existing = job.by_phone.get(candidate.phone)
            if existing:
                return DedupDecision(True, existing, "phone")
        if candidate.email:
            existing = job.by_email.get(candidate.email)
            if existing:
                return DedupDecision(True, existing, "email")
        if candidate.name and candidate.city:
            existing = job.by_name_city.get((_name_key(candidate.name), candidate.city))
            if existing:
                return DedupDecision(True, existing, "name_city")
        return DedupDecision(False)

    def register(self, job: JobState, record: CompanyRecord) -> None:
        if record.website:
            job.by_website[record.website] = record
        if record.phone:
            job.by_phone[record.phone] = record
        if record.email:
            job.by_email[record.email] = record
        if record.name and record.city:
            job.by_name_city[(_name_key(record.name), record.city)] = record

    def merge_into(self, existing: CompanyRecord, candidate: CompanyRecord) -> bool:
        """Fill missing fields on the existing record from the candidate."""
        changed = False
        if not existing.phone and candidate.phone:
            existing.phone = candidate.phone
            changed = True
        if not existing.email and candidate.email:
            existing.email = candidate.email
            changed = True
        if not existing.website and candidate.website:
            existing.website = candidate.website
            changed = True
        if not existing.street and candidate.street:
            existing.street = candidate.street
            changed = True
        if not existing.postal_code and candidate.postal_code:
            existing.postal_code = candidate.postal_code
            changed = True
        if not existing.state and candidate.state:
            existing.state = candidate.state
            changed = True
        if not existing.category and candidate.category:
            existing.category = candidate.category
            changed = True
        if not existing.source_url and candidate.source_url:
            existing.source_url = candidate.source_url
            changed = True
        return changed


deduplicator = Deduplicator()
