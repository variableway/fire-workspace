"""Claude (claude.ai) browser adapter — DOM-based content extraction."""

from __future__ import annotations

import logging
from datetime import datetime

from playwright.async_api import Page

from ...core.types import (
    ChatConversation,
    ChatMessage,
    ContentPart,
    ContentType,
    ConversationSummary,
    ImageData,
    Platform,
    Role,
)
from ..base_adapter import BrowserPlatformAdapter
from ..runner import register_browser_adapter

logger = logging.getLogger(__name__)

CLAUDE_SELECTORS = {
    "message_container": '[class*="conversation"], [data-testid="conversation-turns"]',
    "user_message": '[data-testid="human-message"], [font-style="normal"]',
    "assistant_message": '[data-testid="assistant-message"], [class*="assistant"]',
    "message_content": ".prose, [class*='markdown']",
    "conversation_list": 'nav a, [class*="conversation"]',
    "conversation_item": 'a[href*="/chat/"]',
}

CLAUDE_BASE_URL = "https://claude.ai"


class ClaudeBrowserAdapter(BrowserPlatformAdapter):
    """Browser adapter for Claude (claude.ai).

    Note: Claude's DOM changes frequently. Selectors may need updating.
    """

    @property
    def platform(self) -> Platform:
        return Platform.CLAUDE

    def get_selectors(self) -> dict[str, str]:
        return CLAUDE_SELECTORS

    async def detect_platform(self, page: Page) -> bool:
        return "claude.ai" in (page.url or "")

    def platform_domains_match(self, url: str) -> bool:
        return "claude.ai" in url

    async def list_conversations(self, limit: int = 50) -> list[ConversationSummary]:
        """List conversations from Claude sidebar."""
        page = await self.get_page(CLAUDE_BASE_URL)
        await self.session.ensure_login(page, "claude")
        await page.wait_for_load_state("networkidle")

        selectors = self.get_selectors()
        items = await page.query_selector_all(selectors["conversation_item"])

        conversations = []
        for item in items[:limit]:
            href = await item.get_attribute("href") or ""
            title = (await item.text_content() or "").strip()

            conv_id = ""
            if "/chat/" in href:
                conv_id = href.rstrip("/").split("/chat/")[-1]

            if title or conv_id:
                conversations.append(
                    ConversationSummary(
                        id=conv_id,
                        title=title or f"Chat {conv_id[:8]}",
                        platform=Platform.CLAUDE,
                        url=f"{CLAUDE_BASE_URL}/chat/{conv_id}" if conv_id else None,
                    )
                )

        logger.info("Found %d Claude conversations", len(conversations))
        return conversations

    async def get_conversation(self, conversation_id: str) -> ChatConversation:
        """Get a full conversation from Claude."""
        url = f"{CLAUDE_BASE_URL}/chat/{conversation_id}"
        page = await self.get_page(url)
        await self.session.ensure_login(page, "claude")
        await page.wait_for_load_state("networkidle")

        try:
            await page.wait_for_selector(
                self.get_selectors()["message_content"], timeout=10000
            )
        except Exception:
            logger.warning("No message content found on page %s", url)

        await self.handle_dynamic_loading(page)
        messages = await self.extract_messages_from_page(page)

        title = ""
        title_el = await page.query_selector("h1, [class*='title']")
        if title_el:
            title = (await title_el.text_content() or "").strip()
        if not title:
            title = f"Claude Chat {conversation_id[:8]}"

        return ChatConversation(
            id=conversation_id,
            title=title,
            platform=Platform.CLAUDE,
            messages=messages,
            url=url,
        )

    async def extract_messages_from_page(self, page: Page) -> list[ChatMessage]:
        """Extract all messages from Claude page."""
        messages: list[ChatMessage] = []

        # Claude uses font-style to distinguish roles
        # Human messages: normal font-style, Assistant: italic or different class
        containers = await page.query_selector_all(
            '[class*="message"], [class*="turn"]'
        )

        for container in containers:
            class_attr = await container.get_attribute("class") or ""
            class_lower = class_attr.lower()

            if "human" in class_lower or "user" in class_lower:
                role = Role.USER
            elif "assistant" in class_lower or "ai" in class_lower:
                role = Role.ASSISTANT
            else:
                # Fallback: check data attributes
                data_role = await container.get_attribute("data-testid") or ""
                if "human" in data_role:
                    role = Role.USER
                elif "assistant" in data_role:
                    role = Role.ASSISTANT
                else:
                    continue

            parts = []
            content_els = await container.query_selector_all(
                ".prose, [class*='markdown'], [class*='content']"
            )
            for el in content_els:
                text = (await el.text_content() or "").strip()
                if text:
                    from ...core.content import extract_code_blocks

                    parts.extend(extract_code_blocks(text))

            if self.config.download_images:
                img_els = await container.query_selector_all("img")
                for img in img_els:
                    src = await img.get_attribute("src") or ""
                    alt = await img.get_attribute("alt") or ""
                    if src and all(x not in src.lower() for x in ["avatar", "icon", "logo"]):
                        local_path = await self.image_handler.download_image(page, src)
                        parts.append(
                            ContentPart(
                                type=ContentType.IMAGE,
                                image=ImageData(src=src, alt=alt, local_path=local_path),
                            )
                        )

            if parts:
                messages.append(ChatMessage(role=role, parts=parts))

        logger.info("Extracted %d messages from Claude page", len(messages))
        return messages


register_browser_adapter(Platform.CLAUDE, ClaudeBrowserAdapter)
