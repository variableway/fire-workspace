"""DOM content extraction utilities for browser adapters."""

from __future__ import annotations

import logging
import re

from playwright.async_api import Page

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Utilities for extracting structured content from chat page DOMs."""

    async def scroll_to_load_all(self, page: Page, max_scrolls: int = 50, timeout: int = 2000) -> None:
        """Scroll the page to trigger lazy-loaded content."""
        prev_height = 0
        for _ in range(max_scrolls):
            curr_height = await page.evaluate("document.body.scrollHeight")
            if curr_height == prev_height:
                break
            prev_height = curr_height
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(timeout)

    async def get_all_text_content(self, page: Page, selector: str) -> list[str]:
        """Extract text content from all elements matching a selector."""
        elements = await page.query_selector_all(selector)
        texts = []
        for el in elements:
            text = await el.text_content()
            if text and text.strip():
                texts.append(text.strip())
        return texts

    async def get_images(
        self, page: Page, selector: str, exclude_patterns: list[str] | None = None
    ) -> list[dict]:
        """Extract image sources from elements matching a selector.

        Args:
            page: The page to extract from.
            selector: CSS selector for image elements.
            exclude_patterns: URL patterns to exclude (e.g., avatars, icons).

        Returns:
            List of dicts with 'src' and 'alt' keys.
        """
        elements = await page.query_selector_all(selector)
        images = []
        exclude = exclude_patterns or ["avatar", "icon", "logo", "emoji"]

        for el in elements:
            src = await el.get_attribute("src")
            if not src:
                continue
            # Skip small icons and avatars
            if any(pat in src.lower() for pat in exclude):
                continue
            alt = await el.get_attribute("alt") or ""
            images.append({"src": src, "alt": alt})

        return images

    async def get_code_blocks(self, page: Page, selector: str = "pre code") -> list[dict]:
        """Extract code blocks from the page.

        Returns list of dicts with 'language' and 'code' keys.
        """
        elements = await page.query_selector_all(selector)
        blocks = []
        for el in elements:
            # Get language from class like "language-python"
            class_attr = await el.get_attribute("class") or ""
            language = "text"
            lang_match = re.search(r"language-(\w+)", class_attr)
            if lang_match:
                language = lang_match.group(1)

            code = await el.text_content()
            if code and code.strip():
                blocks.append({"language": language, "code": code.strip()})

        return blocks

    async def get_inner_html(self, page: Page, selector: str) -> str | None:
        """Get innerHTML of the first matching element."""
        el = await page.query_selector(selector)
        if el:
            return await el.inner_html()
        return None
