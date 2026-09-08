"""Deterministic normalization of raw scraped company fields."""

from __future__ import annotations

import re
from urllib.parse import urlparse

EMAIL_SPACED_RE = re.compile(
    r"([a-zA-Z0-9._%+\-]+)\s*(?:\[at\]|\(at\)|@|\sat\s)\s*([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})"
)

def normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    cleaned = re.sub(r"[^\d+]", "", phone)
    if not cleaned or len(cleaned) < 9:
        return None
    if cleaned.startswith("0049"):
        cleaned = "+49" + cleaned[4:]
    elif cleaned.startswith("49") and not cleaned.startswith("+49"):
        cleaned = "+" + cleaned
    elif cleaned.startswith("0"):
        cleaned = "+49" + cleaned[1:]
    return cleaned

def normalize_email(email: str | None) -> str | None:
    if not email:
        return None
    value = email.strip().lower()
    value = value.replace("%40", "@").replace(" [at] ", "@").replace("(at)", "@")
    m = EMAIL_SPACED_RE.search(value)
    if m and "@" not in value:
        value = f"{m.group(1)}@{m.group(2)}"
    if "@" not in value:
        return None
    # Require a domain that contains a dot (valid TLD-like part).
    local, _, domain = value.partition("@")
    if not local or "." not in domain:
        return None
    return value

def normalize_website(website: str | None) -> str | None:
    if not website:
        return None
    value = website.strip().lower()
    value = value.split("?")[0].rstrip("/")
    if value.startswith("//"):
        value = "https:" + value
    elif not value.startswith(("http://", "https://")):
        value = "https://" + value
    parsed = urlparse(value)
    if not parsed.netloc or "." not in parsed.netloc:
        return None
    netloc = parsed.netloc
    if netloc.startswith("www."):
        netloc = netloc[4:]
        value = f"{parsed.scheme}://{netloc}{parsed.path}"
    return value

def normalize_house_number(raw: str | None) -> str | None:
    if not raw:
        return None
    m = re.match(r"(\d+\s*[a-zA-Z]?)", str(raw).strip())
    return m.group(1) if m else None

def extract_plz(raw: str | None) -> str | None:
    if not raw:
        return None
    m = re.search(r"\b(\d{5})\b", str(raw))
    return m.group(1) if m else None
