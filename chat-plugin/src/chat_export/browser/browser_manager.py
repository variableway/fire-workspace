"""Playwright browser lifecycle management with persistent profiles."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from playwright.async_api import BrowserContext, Page, Playwright, async_playwright

from .config import BrowserConfig

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages Playwright browser lifecycle with persistent login state.

    Uses persistent context so users log in once and sessions persist
    between runs.
    """

    def __init__(self, config: BrowserConfig | None = None):
        self.config = config or BrowserConfig()
        self._playwright: Optional[Playwright] = None
        self._context: Optional[BrowserContext] = None

    async def start(self) -> BrowserContext:
        """Launch browser with persistent context. Returns the context."""
        if self._context:
            return self._context

        self._playwright = await async_playwright().start()

        # Ensure profile directory exists
        self.config.profile_dir.mkdir(parents=True, exist_ok=True)

        launch_args = []
        if self.config.disable_webdriver_flag:
            launch_args.append("--disable-blink-features=AutomationControlled")

        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.config.profile_dir),
            headless=self.config.headless,
            slow_mo=self.config.slow_mo,
            args=launch_args,
            viewport={"width": 1280, "height": 900},
            locale="zh-CN",
        )

        logger.info("Browser started with profile: %s", self.config.profile_dir)
        return self._context

    async def new_page(self, url: str | None = None) -> Page:
        """Create a new page, optionally navigating to a URL."""
        context = await self.start()
        page = await context.new_page()
        page.set_default_timeout(self.config.timeout)

        # Inject stealth script to hide webdriver flag
        if self.config.disable_webdriver_flag:
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

        if url:
            await page.goto(url, wait_until="domcontentloaded")
        return page

    async def get_existing_page(self, url_pattern: str) -> Page | None:
        """Find an existing page matching a URL pattern."""
        if not self._context:
            return None
        for page in self._context.pages:
            if page.url and url_pattern in page.url:
                return page
        return None

    async def close(self) -> None:
        """Close browser and cleanup."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Browser closed")
