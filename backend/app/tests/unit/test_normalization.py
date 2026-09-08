from app.scraper.normalizers.normalizer import (
    extract_plz,
    normalize_email,
    normalize_house_number,
    normalize_phone,
    normalize_website,
)


def test_normalize_phone():
    assert normalize_phone("0231 123456") == "+49231123456"
    assert normalize_phone("+49 231 123456") == "+49231123456"
    assert normalize_phone("0049 231 123456") == "+49231123456"
    assert normalize_phone("") is None
    assert normalize_phone(None) is None
    assert normalize_phone("123") is None  # too short


def test_normalize_email():
    assert normalize_email("TEST@Example.DE") == "test@example.de"
    assert normalize_email(" info [at] firma.de ") == "info@firma.de"
    assert normalize_email("") is None
    assert normalize_email("kein@email") is None


def test_normalize_website():
    assert normalize_website("example.de") == "https://example.de"
    assert normalize_website("https://example.de") == "https://example.de"
    assert normalize_website("https://www.example.de/") == "https://example.de"
    assert normalize_website("") is None
    assert normalize_website(None) is None


def test_plz_and_house_number():
    assert extract_plz("Musterstraße 1, 44135 Dortmund") == "44135"
    assert normalize_house_number("25a") == "25a"
    assert normalize_house_number(None) is None
