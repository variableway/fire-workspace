"""Gemini (gemini.google.com) browser adapter — DOM-based content extraction."""

from __future__ import annotations

import logging

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

GEMINI_SELECTORS = {
    "message_container": '[class*="conversation"], [class*="turn"]',
    "user_message": '[class*="user-query"], [class*="human"]',
    "assistant_message": '[class*="model-response"], [class*="assistant"]',
    "message_content": '[class*="message-content"], [class*="response"]',
    "conversation_item": 'a[href*="/app/"]',
}

GEMINI_BASE_URL = "https://gemini.google.com"


class GeminiBrowserAdapter(BrowserPlatformAdapter):
    """Browser adapter for Gemini (gemini.google.com)."""

    @property
    def platform(self) -> Platform:
        return Platform.GEMINI

    def get_selectors(self) -> dict[str, str]:
        return GEMINI_SELECTORS

    async def detect_platform(self, page: Page) -> bool:
        return "gemini.google.com" in (page.url or "")

    def platform_domains_match(self, url: str) -> bool:
        return "gemini.google.com" in url

    async def list_conversations(self, limit: int = 50) -> list[ConversationSummary]:
        """List conversations from Gemini sidebar."""
        page = await self.get_page(GEMINI_BASE_URL)
        await self.session.ensure_login(page, "gemini")
        await page.wait_for_load_state("networkidle")

        # Gemini uses a different conversation navigation pattern
        # Conversation list is in the sidebar
        items = await page.query_selector_all(self.get_selectors()["conversation_item"])

        conversations = []
        for item in items[:limit]:
            href = await item.get_attribute("href") or ""
            title = (await item.text_content() or "").strip()

            conv_id = ""
            if href:
                conv_id = href.rstrip("/").split("/")[-1]

            if title or conv_id:
                conversations.append(
                    ConversationSummary(
                        id=conv_id,
                        title=title or f"Gemini Chat {conv_id[:8]}",
                        platform=Platform.GEMINI,
                        url=f"{GEMINI_BASE_URL}/app/{conv_id}" if conv_id else None,
                    )
                )

        logger.info("Found %d Gemini conversations", len(conversations))
        return conversations

    async def get_conversation(self, conversation_id: str) -> ChatConversation:
        """Get a full conversation from Gemini."""
        url = f"{GEMINI_BASE_URL}/app/{conversation_id}"
        page = await self.get_page(url)
        await self.session.ensure_login(page, "gemini")
        await page.wait_for_load_state("networkidle")

        await self.handle_dynamic_loading(page)
        messages = await self.extract_messages_from_page(page)

        title = ""
        title_el = await page.query_selector("h1, [class*='title']")
        if title_el:
            title = (await title_el.text_content() or "").strip()
        if not title:
            title = f"Gemini Chat {conversation_id[:8]}"

        return ChatConversation(
            id=conversation_id,
            title=title,
            platform=Platform.GEMINI,
            messages=messages,
            url=url,
        )

    async def extract_messages_from_page(self, page: Page) -> list[ChatMessage]:
        """Extract all messages from Gemini page."""
        messages: list[ChatMessage] = []

        # Gemini uses turn-based layout
        turns = await page.query_selector_all('[class*="turn"], [class*="conversation-turn"]')

        for turn in turns:
            # Detect role
            class_attr = (await turn.get_attribute("class") or "").lower()
            if "user" in class_attr or "query" in class_attr:
                role = Role.USER
            elif "model" in class_attr or "response" in class_attr:
                role = Role.ASSISTANT
            else:
                continue

            parts = []
            content_els = await turn.query_selector_all(
                '[class*="message-content"], [class*="response-content"]'
            )
            for el in content_els:
                text = (await el.text_content() or "").strip()
                if text:
                    from ...core.content import extract_code_blocks

                    parts.extend(extract_code_blocks(text))

            if self.config.download_images:
                img_els = await turn.query_selector_all("img")
                for img in img_els:
                    src = await img.get_attribute("src") or ""
                    alt = await img.get_attribute("alt") or ""
                    if src and all(x not in src.lower() for x in ["avatar", "icon", "logo", "gstatic"]):
                        local_path = await self.image_handler.download_image(page, src)
                        parts.append(
                            ContentPart(
                                type=ContentType.IMAGE,
                                image=ImageData(src=src, alt=alt, local_path=local_path),
                            )
                        )

            if parts:
                messages.append(ChatMessage(role=role, parts=parts))

        logger.info("Extracted %d messages from Gemini page", len(messages))
        return messages


register_browser_adapter(Platform.GEMINI, GeminiBrowserAdapter)
