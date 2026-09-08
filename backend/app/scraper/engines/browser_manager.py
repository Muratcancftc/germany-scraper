"""Shared Camoufox browser management with context pooling and lifecycle control.

Vercel Functions have a read-only filesystem with a writable /tmp limited to
~500 MB, while the Camoufox browser bundle is ~600 MB. Copying the whole bundle
into /tmp is impossible.

Camoufox only ever *reads* the browser binary; the only writes it needs are
small: a `config.json` (active version pointer) and a `fontconfig` cache. So we
give Camoufox a *writable* install dir in /tmp and symlink the read-only
`browsers/` directory from the build-time bundle. This keeps the 600 MB binary
read directly from the deployment while all writes land in /tmp.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from pathlib import Path

# Must be set before importing camoufox internals so the data dir resolves to /tmp.
_IS_SERVERLESS = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))
if _IS_SERVERLESS:
    os.environ.setdefault("XDG_CACHE_HOME", "/tmp/camoufox")

from camoufox.async_api import AsyncCamoufox  # noqa: E402
from camoufox.multiversion import COMPAT_FLAG, CONFIG_FILE  # noqa: E402
from camoufox.pkgman import INSTALL_DIR  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.logging.logger import logger  # noqa: E402


def _bundle_cache_candidates() -> list[Path]:
    return [
        Path(os.getcwd()) / ".camoufox_cache" / "camoufox",
        Path("/var/task/.camoufox_cache") / "camoufox",
        Path(__file__).resolve().parent.parent.parent.parent / ".camoufox_cache" / "camoufox",
    ]


def _setup_serverless_layout() -> None:
    """Give Camoufox a writable install dir: symlink browsers from the bundle."""
    if not _IS_SERVERLESS:
        return
    if INSTALL_DIR.exists() and (INSTALL_DIR / "browsers").exists():
        return

    bundle = next((p for p in _bundle_cache_candidates() if (p / "browsers").exists()), None)
    if bundle is None:
        logger.warning("Bundled Camoufox browser not found; browser fallback unavailable")
        return

    try:
        INSTALL_DIR.mkdir(parents=True, exist_ok=True)
        # Symlink the read-only browser binaries into the writable install dir.
        try:
            (INSTALL_DIR / "browsers").symlink_to(bundle / "browsers", target_is_directory=True)
        except OSError:
            # Fallback if symlinks are not permitted: hard link or copy.
            shutil.copytree(bundle / "browsers", INSTALL_DIR / "browsers", dirs_exist_ok=True)

        # The build-time fetch wrote a config.json with active_version — reuse it.
        src_config = bundle / "config.json"
        if src_config.exists() and not CONFIG_FILE.exists():
            shutil.copy2(src_config, CONFIG_FILE)

        # COMPAT_FLAG marks the data dir as compatible (skips cleanup/rmtree).
        if not COMPAT_FLAG.exists():
            try:
                COMPAT_FLAG.write_text("1")
            except Exception:
                pass

        # If no active_version yet, point it at the first installed browser.
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
            except Exception:
                data = {}
        else:
            data = {}
        if not data.get("active_version"):
            candidates = sorted(
                (INSTALL_DIR / "browsers").rglob("version.json"),
                reverse=True,
            )
            if candidates:
                rel = candidates[0].parent.relative_to(INSTALL_DIR).as_posix()
                data["active_version"] = rel
                CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
                CONFIG_FILE.write_text(json.dumps(data))

        logger.info("Camoufox /tmp layout ready", install_dir=str(INSTALL_DIR))
    except Exception as exc:
        logger.warning("Could not set up Camoufox /tmp layout", error=str(exc))


_setup_serverless_layout()


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
                _setup_serverless_layout()
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
