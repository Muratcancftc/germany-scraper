"""Shared Camoufox browser management with context pooling and lifecycle control.

On Vercel Functions the filesystem is read-only except `/tmp`. Camoufox stores
its browser in a user cache dir (`XDG_CACHE_HOME/camoufox`). We point
`XDG_CACHE_HOME` directly at the bundled read-only cache directory
(`.camoufox_cache`, created by the build-time `camoufox fetch`) so the browser
is *read* from the bundle and nothing needs to be copied to /tmp (the browser
bundle is ~600 MB and would not fit in /tmp).
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

# Must be set before importing camoufox internals so the data dir resolves to the
# bundled cache. On Vercel the bundle lives next to the project (read-only).
_IS_SERVERLESS = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))
if _IS_SERVERLESS:
    _bundle_candidates = [
        Path(os.getcwd()) / ".camoufox_cache",
        Path("/var/task/.camoufox_cache"),
        Path(__file__).resolve().parent.parent.parent.parent / ".camoufox_cache",
    ]
    _bundle_cache = next((p for p in _bundle_candidates if (p / "camoufox").exists()), None)
    if _bundle_cache is not None:
        os.environ["XDG_CACHE_HOME"] = str(_bundle_cache)

from camoufox.async_api import AsyncCamoufox  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.logging.logger import logger  # noqa: E402


class BrowserManager:
    """Owns a single Camoufox browser, reuses contexts via a pool."""

    def __init__(self):
        self._session: AsyncCamoufox | None = None
        self._browser = None
        self._context_pool: list = []
        self._lock = asyncio.Lock()
        self._closed = False

    async def _ensure_browser(self):
        async with self._lock:
            if self._browser is None and not self._closed:
                logger.info("Starting Camoufox browser")
                self._session = AsyncCamoufox(
                    headless=settings.CAMOUFOX_HEADLESS,
                    humanize=settings.CAMOUFOX_HUMANIZE,
                    os="linux" if _IS_SERVERLESS else "windows",
                )
                self._browser = await self._session.__aenter__()

    async def acquire_context(self):
        await self._ensure_browser()
        if self._context_pool:
            return self._context_pool.pop()
        context = await self._browser.new_context(
            viewport={"width": 1366, "height": 900},
            locale="de-DE",
            timezone_id="Europe/Berlin",
        )
        await self._install_blocking(context)
        return context

    @staticmethod
    async def _install_blocking(context) -> None:
        """Block heavy/tracking resources while keeping JavaScript enabled.

        Images, media, fonts and analytics/tracking/advertisement requests are
        aborted; the page's own JS and HTML/CSS still load so JS-rendered
        content can be extracted.
        """
        blocked_resource_types = {"image", "media", "font"}
        blocked_url_keywords = (
            "analytics",
            "tracking",
            "telemetry",
            "advert",
            "ads",
            "adserver",
            "doubleclick",
            "googletag",
            "facebook",
            "hotjar",
            "mixpanel",
            "segment",
            "gtag",
            "google-analytics",
            "mc.yandex",
            "sentry",
            "metrics",
            "beacon",
            "pixel",
        )

        async def route_handler(route):
            req = route.request
            if req.resource_type in blocked_resource_types:
                await route.abort()
                return
            url = req.url.lower()
            if req.resource_type == "script" or req.resource_type == "other":
                if any(k in url for k in blocked_url_keywords):
                    await route.abort()
                    return
            await route.continue_()

        await context.route("**/*", route_handler)

    def release_context(self, context):
        self._context_pool.append(context)
        # Keep pool bounded
        if len(self._context_pool) > settings.MAX_CONCURRENT_PAGES:
            asyncio.create_task(self._close_context(self._context_pool.pop(0)))

    async def _close_context(self, context):
        try:
            await context.close()
        except Exception:
            pass

    async def close(self):
        if self._browser is not None:
            async with self._lock:
                self._closed = True
                for ctx in self._context_pool:
                    try:
                        await ctx.close()
                    except Exception:
                        pass
                self._context_pool = []
                if self._session is not None:
                    try:
                        await self._session.__aexit__(None, None, None)
                    except Exception:
                        pass
                self._session = None
                self._browser = None


browser_manager = BrowserManager()
