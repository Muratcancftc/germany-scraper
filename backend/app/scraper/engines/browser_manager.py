"""Shared Camoufox browser management with context pooling and lifecycle control.

On Vercel Functions the filesystem is read-only except `/tmp`. Camoufox stores
its browser in a user cache dir (`XDG_CACHE_HOME/camoufox`). We point
`XDG_CACHE_HOME` at a writable temp dir and, on first use, copy the browser from
the bundled read-only location (downloaded at build time via `camoufox fetch`)
into `/tmp` so the browser can run.
"""

from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path

# Must be set before importing camoufox internals so the data dir resolves to /tmp.
if os.environ.get("VERCEL"):
    _bundle_cache = os.path.join(os.getcwd(), ".camoufox_cache")
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/camoufox")
    _cache_root = Path(os.environ["XDG_CACHE_HOME"])
    if not (_cache_root / "camoufox").exists() and Path(_bundle_cache).exists():
        try:
            shutil.copytree(_bundle_cache, _cache_root, dirs_exist_ok=True)
        except Exception:
            pass

from camoufox.async_api import AsyncCamoufox

from app.core.config import settings
from app.core.logging.logger import logger


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
                    os="linux" if os.environ.get("VERCEL") else "windows",
                )
                self._browser = await self._session.__aenter__()

    async def acquire_context(self):
        await self._ensure_browser()
        if self._context_pool:
            return self._context_pool.pop()
        return await self._browser.new_context(
            viewport={"width": 1366, "height": 900},
            locale="de-DE",
            timezone_id="Europe/Berlin",
        )

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
