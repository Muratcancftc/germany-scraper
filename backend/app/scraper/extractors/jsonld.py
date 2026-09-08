"""Deterministic JSON-LD / Schema.org extraction from raw HTML."""

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup


def _extract_jsonld_blocks(html: str) -> list[dict]:
    """Pull every <script type="application/ld+json"> block and parse it."""
    soup = BeautifulSoup(html, "lxml")
    blocks: list[dict] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            continue
        if isinstance(data, list):
            blocks.extend(d for d in data if isinstance(d, dict))
        elif isinstance(data, dict):
            blocks.append(data)
    return blocks

def _flatten_graph(node: dict) -> list[dict]:
    """Expand @graph nodes into individual dicts."""
    if "@graph" in node:
        return list(node["@graph"])
    return [node]

def _find_local_business(blocks: list[dict]) -> dict | None:
    """Return the most relevant business-type JSON-LD node."""
    business_types = (
        "LocalBusiness",
        "Organization",
        "Corporation",
        "Restaurant",
        "MedicalOrganization",
        "HealthClub",
        "Store",
        "ProfessionalService",
    )
    candidates: list[dict] = []
    for block in blocks:
        for node in _flatten_graph(block):
            types = node.get("@type")
            if isinstance(types, str):
                types = [types]
            if not isinstance(types, list):
                continue
            for t in types:
                if t in business_types:
                    candidates.append(node)
                    break
    if candidates:
        # Prefer nodes that carry contact data (name + at least one signal)
        ranked = sorted(
            candidates,
            key=lambda n: (
                bool(n.get("telephone")),
                bool(n.get("email")),
                bool(n.get("address")),
                bool(n.get("url")),
            ),
            reverse=True,
        )
        return ranked[0]
    return None

class JsonLdExtractor:
    """Extract company data from JSON-LD structured data."""

    def extract(self, html: str) -> dict[str, Any]:
        blocks = _extract_jsonld_blocks(html)
        if not blocks:
            return {}
        node = _find_local_business(blocks)
        if not node:
            return {}

        result: dict[str, Any] = {"found": True}
        name = node.get("name")
        if isinstance(name, str) and name.strip():
            result["name"] = name.strip()

        telephone = node.get("telephone")
        if isinstance(telephone, str) and telephone.strip():
            result["phone"] = telephone.strip()

        email = node.get("email")
        if isinstance(email, str) and email.strip():
            result["email"] = email.strip()

        url = node.get("url") or node.get("sameAs")
        if isinstance(url, str) and url.strip():
            result["website"] = url.strip()

        address = node.get("address")
        if isinstance(address, dict):
            addr = {
                "street": address.get("streetAddress"),
                "postal_code": address.get("postalCode"),
                "city": address.get("addressLocality"),
                "state": address.get("addressRegion"),
                "country": address.get("addressCountry"),
            }
            result["address"] = {k: v for k, v in addr.items() if v}

        geo = node.get("geo")
        if isinstance(geo, dict):
            result["latitude"] = geo.get("latitude")
            result["longitude"] = geo.get("longitude")

        return result
