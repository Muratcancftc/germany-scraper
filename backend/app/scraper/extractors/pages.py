"""Discover contact / impressum / about pages on a company website."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

CONTACT_PATHS = [
    "kontakt", "contact", "kontaktieren", "impressum", "ueber-uns",
    "ueber-uns/", "team", "about", "about-us", "legal", "impressum/",
]

CONTACT_ANCHOR_RE = re.compile(
    r"(kontakt|contact|impressum|über\s?uns|ueber\s?uns|team|about(\s?us)?|legal)",
    re.IGNORECASE,
)

class PageDiscovery:
    """Find relevant pages (contact, impressum, about) within a website."""

    def discover(self, base_url: str, html: str) -> dict[str, str]:
        """Return a mapping of known page types to absolute URLs found in HTML."""
        found: dict[str, str] = {}
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith(("javascript:", "#", "mailto:", "tel:")):
                continue
            text = (a.get_text(" ", strip=True) or "").lower()
            url = urljoin(base_url, href)
            path = urlparse(url).path.lower()

            combined = f"{text} {path}"

            if "impressum" in combined and "impressum" not in found:
                found["impressum"] = url
            elif "kontakt" in combined or "contact" in path and "contact" not in found:
                found["contact"] = url
            elif ("über uns" in combined or "ueber uns" in combined
                  or "about" in combined) and "about" not in found:
                found["about"] = url

        return found

    def candidate_contact_urls(self, base_url: str) -> list[str]:
        """Return likely URLs to try even without an anchor link."""
        candidates = []
        for path in ("kontakt", "kontakt/", "contact", "contact/",
                     "impressum", "impressum/", "ueber-uns", "ueber-uns/",
                     "about", "about-us"):
            candidates.append(urljoin(base_url, path))
        return candidates

    def is_external(self, url: str, base_url: str) -> bool:
        return urlparse(url).netloc != urlparse(base_url).netloc
