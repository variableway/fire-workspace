"""Abstract base class for browser-based platform adapters."""

from __future__ import annotations

from abc import abstractmethod
from typing import Optional

from playwright.async_api import Page

from ..core.adapter_base import PlatformAdapter
from ..core.types import ChatMessage, Platform
from .browser_manager import BrowserManager
from .config import BrowserConfig
from .content_extractor import ContentExtractor
from .image_handler import ImageHandler
from .session import SessionManager


class BrowserPlatformAdapter(PlatformAdapter):
    """Base class for browser-based platform adapters.

    Provides shared browser logic (page navigation, content loading,
    image handling). Subclasses implement platform-specific DOM selectors.
    """

    def __init__(
        self,
        browser_manager: BrowserManager | None = None,
        config: BrowserConfig | None = None,
    ):
        self.config = config or BrowserConfig()
        self.browser = browser_manager or BrowserManager(self.config)
        self.session = SessionManager()
        self.extractor = ContentExtractor()
        self.image_handler = ImageHandler(self.config.image_output_dir)
        self._page: Optional[Page] = None

    @property
    @abstractmethod
    def platform(self) -> Platform:
        """Which platform this adapter handles."""

    @abstractmethod
    async def detect_platform(self, page: Page) -> bool:
        """Check if the current page is this platform."""

    @abstractmethod
    async def extract_messages_from_page(self, page: Page) -> list[ChatMessage]:
        """Extract all messages from the current page DOM."""

    @abstractmethod
    def get_selectors(self) -> dict[str, str]:
        """Return platform-specific CSS selectors.

        Expected keys:
        - 'message_container': Container holding all messages
        - 'user_message': Selector for user messages
        - 'assistant_message': Selector for assistant messages
        - 'message_content': Selector for message body content
        - 'conversation_list': Selector for sidebar conversation list
        - 'conversation_item': Selector for individual conversation items
        """

    async def get_page(self, url: str | None = None) -> Page:
        """Get or create a page, navigating to URL if provided."""
        if url and self._page and self.platform_domains_match(url):
            return self._page
        self._page = await self.browser.new_page(url)
        return self._page

    def platform_domains_match(self, url: str) -> bool:
        """Check if a URL matches this platform's domains."""
        return False

    async def handle_dynamic_loading(self, page: Page) -> None:
        """Scroll and wait for dynamically loaded content."""
        await self.extractor.scroll_to_load_all(
            page,
            max_scrolls=self.config.max_scrolls,
            timeout=self.config.scroll_timeout,
        )

    async def close(self) -> None:
        """Close the browser."""
        await self.browser.close()
