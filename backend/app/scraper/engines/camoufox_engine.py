"""Camoufox engine: renders pages and returns extracted HTML/DOM content."""

from __future__ import annotations

from app.core.config import settings
from app.scraper.engines.browser_manager import browser_manager


class CamoufoxEngine:
    """Loads a page via Camoufox, waits for JS, returns rendered HTML."""

    async def get_html(self, url: str, wait_for: str | None = None) -> str:
        context = await browser_manager.acquire_context()
        page = await context.new_page()
        try:
            await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=settings.NAVIGATION_TIMEOUT,
            )
            await page.wait_for_load_state("networkidle", timeout=settings.PAGE_TIMEOUT)
            if wait_for:
                try:
                    await page.wait_for_selector(wait_for, timeout=settings.PAGE_TIMEOUT)
                except Exception:
                    pass
            html = await page.content()
            return html
        finally:
            try:
                await page.close()
            finally:
                browser_manager.release_context(context)

    async def close(self):
        await browser_manager.close()

camoufox_engine = CamoufoxEngine()
