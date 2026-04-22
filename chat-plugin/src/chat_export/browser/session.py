"""Login state and session management for browser adapters."""

from __future__ import annotations

import logging
from typing import Optional

from playwright.async_api import Page

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages login sessions for different platforms.

    Checks if a user is logged in and provides guidance
    for manual login when needed.
    """

    # Platform login check selectors
    LOGIN_INDICATORS: dict[str, dict[str, str]] = {
        "kimi": {
            "logged_in": '[class*="user"], [class*="avatar"], [data-testid="user-menu"]',
            "login_url": "https://kimi.moonshot.cn",
        },
        "chatgpt": {
            "logged_in": '[data-testid="profile-button"], img[alt*="User"]',
            "login_url": "https://chatgpt.com",
        },
        "claude": {
            "logged_in": 'button[aria-label="User menu"], [data-testid="user-menu"]',
            "login_url": "https://claude.ai",
        },
        "gemini": {
            "logged_in": 'img[alt*="Account"], [data-ogsr-up]',
            "login_url": "https://gemini.google.com",
        },
    }

    async def check_login(self, page: Page, platform: str) -> bool:
        """Check if the user is logged in on the current page."""
        indicators = self.LOGIN_INDICATORS.get(platform)
        if not indicators:
            return False

        try:
            element = await page.query_selector(indicators["logged_in"])
            return element is not None
        except Exception:
            return False

    async def ensure_login(self, page: Page, platform: str) -> bool:
        """Ensure user is logged in. Opens login page if needed.

        Returns True if login is confirmed, False if manual login is required.
        """
        if await self.check_login(page, platform):
            return True

        indicators = self.LOGIN_INDICATORS.get(platform)
        if indicators:
            logger.info("Not logged in to %s. Navigating to login page...", platform)
            await page.goto(indicators["login_url"], wait_until="domcontentloaded")
            logger.info(
                "Please log in manually in the browser window. "
                "Press Enter in the terminal when done."
            )
            # In non-interactive mode, just wait and check periodically
            for _ in range(30):  # Wait up to 60 seconds
                await page.wait_for_timeout(2000)
                if await self.check_login(page, platform):
                    logger.info("Login confirmed for %s", platform)
                    return True

            logger.warning("Login timeout for %s", platform)
            return False

        return False
