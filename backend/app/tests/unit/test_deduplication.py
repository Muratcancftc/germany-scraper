from app.core.store.job_store import CompanyRecord, JobState
from app.scraper.deduplication.deduplicator import Deduplicator


def test_find_duplicate_by_website():
    dedup = Deduplicator()
    job = JobState(id=1)
    first = CompanyRecord(name="ABC", website="https://example.de")
    dedup.register(job, first)

    dup = CompanyRecord(name="ABC", website="https://example.de")
    decision = dedup.find_duplicate(job, dup)
    assert decision.is_duplicate is True
    assert decision.match_type == "website"


def test_merge_into_fills_missing_fields():
    dedup = Deduplicator()
    existing = CompanyRecord(name="ABC", phone="+49 231 123456", website="https://abc.de")
    candidate = CompanyRecord(name="ABC", phone="+49 231 123456", email="info@abc.de", website="https://abc.de")

    changed = dedup.merge_into(existing, candidate)
    assert changed is True
    assert existing.email == "info@abc.de"


def test_merge_into():
    dedup = Deduplicator()
    candidate = CompanyRecord(name="Test GmbH", email="info@test.de")
    existing = CompanyRecord(name="Test GmbH")

    changed = dedup.merge_into(existing, candidate)
    assert changed is True
    assert existing.email == "info@test.de"
    assert existing.phone is None
