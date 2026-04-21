"""Main entry point for API/SDK-based chat extraction."""

from __future__ import annotations

import logging
from pathlib import Path

from ..core.adapter_base import PlatformAdapter
from ..core.export.factory import get_formatter
from ..core.types import ChatConversation, Platform
from .base_adapter import APIPlatformAdapter
from .config import APIConfig

logger = logging.getLogger(__name__)

# Registry of API platform adapters
_API_ADAPTERS: dict[Platform, type[APIPlatformAdapter]] = {}


def register_api_adapter(platform: Platform, adapter_cls: type[APIPlatformAdapter]) -> None:
    """Register an API adapter for a platform."""
    _API_ADAPTERS[platform] = adapter_cls


def get_api_adapter(
    platform: Platform,
    config: APIConfig | None = None,
) -> APIPlatformAdapter:
    """Get an API adapter instance for a platform."""
    cls = _API_ADAPTERS.get(platform)
    if cls is None:
        available = ", ".join(p.value for p in _API_ADAPTERS)
        raise ValueError(f"No API adapter for '{platform.value}'. Available: {available}")
    return cls(config=config)


class APIRunner:
    """High-level runner for API/SDK-based chat extraction.

    Usage:
        runner = APIRunner()
        adapter = runner.get_adapter(Platform.KIMI)
        await adapter.authenticate()
        conv = await adapter.get_conversation("conv-id")
        await runner.export(conv, "json", output_dir=Path("./exports"))
    """

    def __init__(self, config: APIConfig | None = None):
        self.config = config or APIConfig()

    def get_adapter(self, platform: Platform) -> APIPlatformAdapter:
        """Get an API adapter for the specified platform."""
        return get_api_adapter(platform, config=self.config)

    async def export(
        self,
        conversation: ChatConversation,
        format: str = "json",
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
        format: str = "json",
        output_dir: Path | None = None,
        limit: int | None = None,
    ) -> list[Path]:
        """Export all conversations from a platform via API."""
        adapter = self.get_adapter(platform)
        await adapter.authenticate()
        paths = []
        async for conv in adapter.get_all_conversations():
            path = await self.export(conv, format, output_dir)
            paths.append(path)
            if limit and len(paths) >= limit:
                break
        await adapter.close()
        return paths
