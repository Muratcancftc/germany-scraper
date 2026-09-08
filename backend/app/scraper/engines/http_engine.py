"""HTTP-first page fetcher.

Scraping strategy: try plain HTTP first (fast, cheap, no browser). Only fall
back to a real browser (Camoufox) when the page cannot be fetched over HTTP or
when the content clearly requires JavaScript (bot challenge, empty body, etc.).

This is the default engine passed to sources. It keeps the same `get_html(url)`
contract the existing sources already use, so no source changes are required.
"""

from __future__ import annotations

import asyncio
import re

import httpx

from app.core.config import settings
from app.core.logging.logger import logger
from app.scraper.engines.camoufox_engine import camoufox_engine

# Heuristic markers of a bot-challenge / JS-gated page that HTTP cannot resolve.
_CHALLENGE_PATTERNS = (
    re.compile(r"just a moment", re.IGNORECASE),
    re.compile(r"checking your browser", re.IGNORECASE),
    re.compile(r"cf-chl[-_]challenge", re.IGNORECASE),
    re.compile(r"cloudflare", re.IGNORECASE),
    re.compile(r"enable javascript", re.IGNORECASE),
    re.compile(r"enablejs", re.IGNORECASE),
    re.compile(r"captcha", re.IGNORECASE),
)


class HttpEngine:
    """Fetches rendered HTML, preferring plain HTTP and falling back to Camoufox."""

    name = "http"

    def __init__(self):
        self._client: httpx.AsyncClient | None = None
        self._lock = asyncio.Lock()
        self._browser_used = False

    async def _get_client(self) -> httpx.AsyncClient:
        async with self._lock:
            if self._client is None or self._client.is_closed:
                self._client = httpx.AsyncClient(
                    follow_redirects=True,
                    timeout=settings.HTTP_TIMEOUT,
                    headers={
                        "User-Agent": settings.HTTP_USER_AGENT,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
                    },
                )
        return self._client

    async def close(self):
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:
                pass
            self._client = None

    @staticmethod
    def _looks_like_challenge(html: str) -> bool:
        if not html:
            return True
        body = html.lower()
        return any(p.search(body) for p in _CHALLENGE_PATTERNS)

    def browser_used(self) -> bool:
        return self._browser_used

    async def get_html(self, url: str, wait_for: str | None = None) -> str:
        """Return page HTML: HTTP first, Camoufox fallback when needed."""
        html = await self._fetch_http(url)
        if html is not None and not self._looks_like_challenge(html):
            return html

        logger.info("HTTP insufficient; falling back to Camoufox", url=url)
        self._browser_used = True
        try:
            return await camoufox_engine.get_html(url, wait_for=wait_for)
        except Exception as exc:
            logger.warning("Camoufox fallback failed", url=url, error=str(exc))
            if html is not None:
                return html
            raise

    async def _fetch_http(self, url: str) -> str | None:
        last_error: Exception | None = None
        for attempt in range(settings.HTTP_MAX_RETRIES + 1):
            if attempt:
                await asyncio.sleep(0.4 * attempt)
            try:
                client = await self._get_client()
                resp = await client.get(url)
                if resp.status_code >= 400:
                    logger.warning(
                        "HTTP status", url=url, status=resp.status_code, attempt=attempt
                    )
                    return None
                text = resp.text
                if not text or len(text.strip()) < 200:
                    return None
                return text
            except httpx.HTTPError as exc:
                last_error = exc
                logger.warning("HTTP request failed", url=url, error=str(exc), attempt=attempt)
        if last_error:
            logger.warning("HTTP exhausted retries", url=url, error=str(last_error))
        return None


http_engine = HttpEngine()
