"""Image download and conversion utilities for browser adapters."""

from __future__ import annotations

import base64
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from playwright.async_api import Page

logger = logging.getLogger(__name__)


class ImageHandler:
    """Handles downloading images and converting to base64 for embedding."""

    def __init__(self, output_dir: Path | None = None):
        self.output_dir = output_dir or Path("./exports/images")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def download_image(
        self, page: Page, src: str, filename: str | None = None
    ) -> Optional[str]:
        """Download an image and return the local file path.

        Handles both regular URLs and blob/data URLs.
        """
        try:
            if src.startswith("data:"):
                return self._save_data_url(src, filename)

            if src.startswith("blob:"):
                return await self._save_blob_url(page, src, filename)

            # Regular URL — fetch via page context to include cookies
            return await self._fetch_via_page(page, src, filename)

        except Exception as e:
            logger.warning("Failed to download image %s: %s", src[:100], e)
            return None

    async def to_data_url(self, page: Page, src: str) -> Optional[str]:
        """Convert an image to a base64 data URL."""
        if src.startswith("data:"):
            return src

        try:
            response = await page.request.get(src)
            content_type = response.headers.get("content-type", "image/png")
            body = await response.body()
            b64 = base64.b64encode(body).decode("ascii")
            return f"data:{content_type};base64,{b64}"
        except Exception as e:
            logger.warning("Failed to convert image to data URL: %s", e)
            return None

    def _save_data_url(self, data_url: str, filename: str | None = None) -> str:
        """Save a data URL to a file."""
        # Parse data URL: data:image/png;base64,xxxxx
        header, data = data_url.split(",", 1)
        ext = "png"
        if "image/jpeg" in header:
            ext = "jpg"
        elif "image/gif" in header:
            ext = "gif"
        elif "image/webp" in header:
            ext = "webp"

        if not filename:
            import hashlib

            filename = hashlib.md5(data.encode()).hexdigest()[:12]

        filepath = self.output_dir / f"{filename}.{ext}"
        filepath.write_bytes(base64.b64decode(data))
        return str(filepath)

    async def _save_blob_url(self, page: Page, blob_url: str, filename: str | None = None) -> Optional[str]:
        """Save a blob URL by converting to data URL in the browser."""
        try:
            data_url = await page.evaluate(
                """async (url) => {
                    const response = await fetch(url);
                    const blob = await response.blob();
                    return new Promise((resolve) => {
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result);
                        reader.readAsDataURL(blob);
                    });
                }""",
                blob_url,
            )
            if data_url:
                return self._save_data_url(data_url, filename)
        except Exception as e:
            logger.warning("Failed to save blob URL: %s", e)
        return None

    async def _fetch_via_page(self, page: Page, url: str, filename: str | None = None) -> Optional[str]:
        """Fetch an image via the page context (includes auth cookies)."""
        import hashlib

        response = await page.request.get(url)
        if response.status != 200:
            return None

        content_type = response.headers.get("content-type", "image/png")
        ext = "png"
        if "jpeg" in content_type:
            ext = "jpg"
        elif "gif" in content_type:
            ext = "gif"
        elif "webp" in content_type:
            ext = "webp"

        body = await response.body()
        if not filename:
            filename = hashlib.md5(body).hexdigest()[:12]

        filepath = self.output_dir / f"{filename}.{ext}"
        filepath.write_bytes(body)
        return str(filepath)
