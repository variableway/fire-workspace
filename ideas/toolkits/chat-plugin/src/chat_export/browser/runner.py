"""Main entry point for browser-based chat extraction."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Optional

from ..core.adapter_base import PlatformAdapter
from ..core.export.factory import get_formatter
from ..core.types import ChatConversation, Platform
from .base_adapter import BrowserPlatformAdapter
from .browser_manager import BrowserManager
from .config import BrowserConfig

logger = logging.getLogger(__name__)

# Registry of browser platform adapters
_BROWSER_ADAPTERS: dict[Platform, type[BrowserPlatformAdapter]] = {}


def register_browser_adapter(platform: Platform, adapter_cls: type[BrowserPlatformAdapter]) -> None:
    """Register a browser adapter for a platform."""
    _BROWSER_ADAPTERS[platform] = adapter_cls


def get_browser_adapter(
    platform: Platform,
    config: BrowserConfig | None = None,
    browser_manager: BrowserManager | None = None,
) -> BrowserPlatformAdapter:
    """Get a browser adapter instance for a platform."""
    cls = _BROWSER_ADAPTERS.get(platform)
    if cls is None:
        available = ", ".join(p.value for p in _BROWSER_ADAPTERS)
        raise ValueError(f"No browser adapter for '{platform.value}'. Available: {available}")
    return cls(browser_manager=browser_manager, config=config)


class BrowserRunner:
    """High-level runner for browser-based chat extraction.

    Usage:
        runner = BrowserRunner(headless=False)
        adapter = runner.get_adapter(Platform.KIMI)
        conv = await adapter.get_conversation("conv-id")
        await runner.export(conv, "markdown", output_dir=Path("./exports"))
        await runner.close()
    """

    def __init__(self, config: BrowserConfig | None = None):
        self.config = config or BrowserConfig()
        self.browser = BrowserManager(self.config)

    def get_adapter(self, platform: Platform) -> BrowserPlatformAdapter:
        """Get a browser adapter for the specified platform."""
        return get_browser_adapter(platform, config=self.config, browser_manager=self.browser)

    async def export(
        self,
        conversation: ChatConversation,
        format: str = "markdown",
        output_dir: Path | None = None,
    ) -> Path:
        """Export a conversation to a file."""
        output_dir = output_dir or Path("./exports")
        output_dir.mkdir(parents=True, exist_ok=True)

        formatter = get_formatter(format)
        content = formatter.format_conversation(conversation)
        filename = formatter.format_filename(conversation)
        filepath = output_dir / filename

        filepath.write_text(content, encoding="utf-8")
        logger.info("Exported %s to %s", conversation.title, filepath)
        return filepath

    async def export_all(
        self,
        platform: Platform,
        format: str = "markdown",
        output_dir: Path | None = None,
        limit: int | None = None,
    ) -> list[Path]:
        """Export all conversations from a platform."""
        adapter = self.get_adapter(platform)
        paths = []
        async for conv in adapter.get_all_conversations():
            path = await self.export(conv, format, output_dir)
            paths.append(path)
            if limit and len(paths) >= limit:
                break
        await adapter.close()
        return paths

    async def close(self) -> None:
        await self.browser.close()
