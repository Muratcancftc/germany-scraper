from app.scraper.sources.base import CompanyCandidate
from app.scraper.validators.category_validator import CategoryValidator

FITNESS_KEYWORDS = [
    "fitness", "fitnessstudio", "fitnesscenter", "gym", "sportstudio",
]


def test_category_match_on_name():
    validator = CategoryValidator()
    candidate = CompanyCandidate(name="FitX Fitnessstudio Dortmund", category="Fitnessstudio")
    assert validator.validate(candidate, FITNESS_KEYWORDS) is True


def test_category_reject_unrelated():
    validator = CategoryValidator()
    candidate = CompanyCandidate(name="Steuerberatung Meier GmbH", category="Steuerberatung")
    assert validator.validate(candidate, FITNESS_KEYWORDS) is False


def test_category_accept_when_no_signals():
    validator = CategoryValidator()
    candidate = CompanyCandidate(name="")  # no signals to check
    assert validator.validate(candidate, FITNESS_KEYWORDS) is True


def test_category_accept_when_no_keywords():
    validator = CategoryValidator()
    candidate = CompanyCandidate(name="Beliebiges Unternehmen")
    assert validator.validate(candidate, []) is True
