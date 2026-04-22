"""ChatGPT (chatgpt.com) browser adapter — DOM-based content extraction."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

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

CHATGPT_SELECTORS = {
    "message_container": '[data-testid="conversation-turns"]',
    "user_message": '[data-message-author-role="user"]',
    "assistant_message": '[data-message-author-role="assistant"]',
    "message_content": ".markdown",
    "conversation_list": "nav a",
    "conversation_item": "nav a[href*='/c/']",
    "code_block": "pre code",
}

CHATGPT_BASE_URL = "https://chatgpt.com"


class ChatGPTBrowserAdapter(BrowserPlatformAdapter):
    """Browser adapter for ChatGPT (chatgpt.com)."""

    @property
    def platform(self) -> Platform:
        return Platform.CHATGPT

    def get_selectors(self) -> dict[str, str]:
        return CHATGPT_SELECTORS

    async def detect_platform(self, page: Page) -> bool:
        return "chatgpt.com" in (page.url or "")

    def platform_domains_match(self, url: str) -> bool:
        return "chatgpt.com" in url

    async def list_conversations(self, limit: int = 50) -> list[ConversationSummary]:
        """List conversations from ChatGPT sidebar."""
        page = await self.get_page(CHATGPT_BASE_URL)
        await self.session.ensure_login(page, "chatgpt")
        await page.wait_for_load_state("networkidle")

        selectors = self.get_selectors()
        items = await page.query_selector_all(selectors["conversation_item"])

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
                        title=title or f"Chat {conv_id[:8]}",
                        platform=Platform.CHATGPT,
                        url=f"{CHATGPT_BASE_URL}/c/{conv_id}" if conv_id else None,
                    )
                )

        logger.info("Found %d ChatGPT conversations", len(conversations))
        return conversations

    async def get_conversation(self, conversation_id: str) -> ChatConversation:
        """Get a full conversation from ChatGPT."""
        url = f"{CHATGPT_BASE_URL}/c/{conversation_id}"
        page = await self.get_page(url)
        await self.session.ensure_login(page, "chatgpt")
        await page.wait_for_load_state("networkidle")

        selectors = self.get_selectors()
        try:
            await page.wait_for_selector(selectors["message_content"], timeout=10000)
        except Exception:
            logger.warning("No message content found on page %s", url)

        await self.handle_dynamic_loading(page)
        messages = await self.extract_messages_from_page(page)

        title = ""
        title_el = await page.query_selector("h1")
        if title_el:
            title = (await title_el.text_content() or "").strip()
        if not title:
            title = f"ChatGPT Chat {conversation_id[:8]}"

        return ChatConversation(
            id=conversation_id,
            title=title,
            platform=Platform.CHATGPT,
            messages=messages,
            url=url,
        )

    async def extract_messages_from_page(self, page: Page) -> list[ChatMessage]:
        """Extract all messages from ChatGPT page."""
        selectors = self.get_selectors()
        messages: list[ChatMessage] = []

        # Find message containers with role attributes
        containers = await page.query_selector_all("[data-message-author-role]")

        for container in containers:
            role_attr = await container.get_attribute("data-message-author-role")
            if role_attr == "user":
                role = Role.USER
            elif role_attr == "assistant":
                role = Role.ASSISTANT
            else:
                continue

            parts = []
            content_els = await container.query_selector_all(selectors["message_content"])
            for el in content_els:
                text = (await el.text_content() or "").strip()
                if text:
                    # Check for code blocks
                    code_els = await el.query_selector_all("pre code")
                    if code_els:
                        from ...core.content import extract_code_blocks

                        parts.extend(extract_code_blocks(text))
                    else:
                        parts.append(ContentPart(type=ContentType.TEXT, text=text))

            # Extract images
            if self.config.download_images:
                img_els = await container.query_selector_all("img")
                for img in img_els:
                    src = await img.get_attribute("src") or ""
                    alt = await img.get_attribute("alt") or ""
                    if src and "avatar" not in src.lower() and "icon" not in src.lower():
                        local_path = await self.image_handler.download_image(page, src)
                        parts.append(
                            ContentPart(
                                type=ContentType.IMAGE,
                                image=ImageData(src=src, alt=alt, local_path=local_path),
                            )
                        )

            if parts:
                messages.append(ChatMessage(role=role, parts=parts))

        logger.info("Extracted %d messages from ChatGPT page", len(messages))
        return messages


register_browser_adapter(Platform.CHATGPT, ChatGPTBrowserAdapter)
