"""Deterministic extraction of company data from rendered HTML."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from app.scraper.extractors.jsonld import JsonLdExtractor


class CompanyDataExtractor:
    """Combines JSON-LD, meta tags and DOM heuristics into one extractor."""

    def __init__(self, base_url: str = ""):
        self.base_url = base_url
        self.jsonld = JsonLdExtractor()

    def extract(self, html: str, page_url: str = "") -> dict:
        base = page_url or self.base_url
        result: dict = {}

        jsonld_data = self.jsonld.extract(html)
        result.update(jsonld_data)

        soup = BeautifulSoup(html, "lxml")

        if not result.get("name"):
            name = self._extract_name(soup)
            if name:
                result["name"] = name

        if not result.get("website"):
            website = self._extract_website(soup, base)
            if website:
                result["website"] = website

        if not result.get("phone"):
            phones = self._extract_phones(soup)
            if phones:
                result["phone"] = phones[0]

        if not result.get("email"):
            emails = self._extract_emails(soup)
            if emails:
                result["email"] = emails[0]

        if not result.get("address"):
            addr = self._extract_address(soup)
            if addr:
                result["address"] = addr

        return {k: v for k, v in result.items() if k not in ("found",) or k == "found"}

    # --- name -----------------------------------------------------------
    def _extract_name(self, soup: BeautifulSoup) -> str | None:
        og = soup.find("meta", attrs={"property": "og:site_name"})
        if og and og.get("content"):
            return og["content"].strip()
        h1 = soup.find("h1")
        if h1:
            text = h1.get_text(" ", strip=True)
            if text and len(text) <= 200:
                return text
        title = soup.find("title")
        if title and title.string:
            text = title.string.strip()
            text = re.split(r"\s[|\-–—]\s", text)[0].strip()
            if text:
                return text
        return None

    # --- website --------------------------------------------------------
    def _extract_website(self, soup: BeautifulSoup, base: str) -> str | None:
        og = soup.find("meta", attrs={"property": "og:url"})
        if og and og.get("content"):
            return og["content"].strip()
        canonical = soup.find("link", attrs={"rel": "canonical"})
        if canonical and canonical.get("href"):
            return canonical["href"].strip()
        return None

    # --- phones ---------------------------------------------------------
    def _extract_phones(self, soup: BeautifulSoup) -> list[str]:
        phones: list[str] = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().startswith("tel:"):
                value = href[4:].strip()
                if value:
                    phones.append(value)
        if phones:
            return phones
        tel_re = re.compile(
            r"[+]?(?:49|0049)[\s\-()]*(?:\(0\)[\s\-()]*)?"
            r"\d{2,5}[\s\-()]*\d{3,8}(?:[\s\-()]*\d+){0,3}"
        )
        for match in tel_re.findall(soup.get_text(" ")):
            cleaned = re.sub(r"[^\d+]", "", match)
            if len(cleaned) >= 9:
                phones.append(match)
        return list(dict.fromkeys(phones))

    # --- emails ---------------------------------------------------------
    def _extract_emails(self, soup: BeautifulSoup) -> list[str]:
        emails: list[str] = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if href.lower().startswith("mailto:"):
                value = href[7:].strip()
                if value and "@" in value:
                    emails.append(value)
        if emails:
            return emails
        pattern = re.compile(
            r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
        )
        emails = pattern.findall(soup.get_text(" "))
        return list(dict.fromkeys(emails))

    # --- address --------------------------------------------------------
    def _extract_address(self, soup: BeautifulSoup) -> dict | None:
        body_text = soup.get_text(" ")
        plz = re.search(r"\b(\d{5})\b", body_text)
        result: dict = {}
        if plz:
            result["postal_code"] = plz.group(1)
        street = re.search(
            r"\b([A-ZÄÖÜ][\wäöüß\.\- ]{2,}(?:straße|str\.|strasse|weg|platz|"
            r"allee|gasse))\s+(\d+[a-z]?)\b",
            body_text,
            re.IGNORECASE,
        )
        if street:
            result["street"] = street.group(1).strip()
            result["house_number"] = street.group(2)
        return result or None
