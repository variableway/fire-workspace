"""Kimi (kimi.moonshot.cn) browser adapter — DOM-based content extraction."""

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Optional

from playwright.async_api import Page

from ...core.content import extract_code_blocks
from ...core.types import (
    ChatConversation,
    ChatMessage,
    CodeBlock,
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

# Kimi DOM selectors — may need updates if the frontend changes
KIMI_SELECTORS = {
    "message_container": '[class*="message"], [class*="msg-container"], [class*="chat-list"]',
    "user_message": '[class*="user-message"], [class*="human"], [class*="message-item-user"]',
    "assistant_message": '[class*="assistant-message"], [class*="bot"], [class*="message-item-assistant"]',
    "message_content": '[class*="markdown"], [class*="message-text"], [class*="msg-content"]',
    "conversation_list": '[class*="conversation"], [class*="chat-list"], nav a',
    "conversation_item": '[class*="conversation-item"], [class*="chat-item"]',
    "code_block": "pre code",
    "code_result": '[class*="result"], [class*="output"], [class*="execution"]',
    "image": '[class*="message"] img, [class*="markdown"] img',
}

KIMI_BASE_URL = "https://kimi.moonshot.cn"


class KimiBrowserAdapter(BrowserPlatformAdapter):
    """Browser adapter for Kimi (kimi.moonshot.cn).

    Extracts conversations including Python code execution results,
    images (matplotlib charts), and search references.
    """

    @property
    def platform(self) -> Platform:
        return Platform.KIMI

    def get_selectors(self) -> dict[str, str]:
        return KIMI_SELECTORS

    async def detect_platform(self, page: Page) -> bool:
        return "kimi.moonshot.cn" in (page.url or "")

    def platform_domains_match(self, url: str) -> bool:
        return "kimi.moonshot.cn" in url

    async def list_conversations(self, limit: int = 50) -> list[ConversationSummary]:
        """List conversations from Kimi sidebar."""
        page = await self.get_page(KIMI_BASE_URL)
        await self.session.ensure_login(page, "kimi")
        await page.wait_for_load_state("networkidle")

        selectors = self.get_selectors()
        items = await page.query_selector_all(selectors["conversation_item"])

        conversations = []
        for item in items[:limit]:
            link = await item.query_selector("a")
            title_el = await item.query_selector("span, [class*='title']")
            title = ""
            if title_el:
                title = (await title_el.text_content() or "").strip()

            href = ""
            if link:
                href = await link.get_attribute("href") or ""

            conv_id = ""
            if href:
                conv_id = href.rstrip("/").split("/")[-1]

            if title or conv_id:
                conversations.append(
                    ConversationSummary(
                        id=conv_id,
                        title=title or f"Conversation {conv_id}",
                        platform=Platform.KIMI,
                        url=f"{KIMI_BASE_URL}/chat/{conv_id}" if conv_id else None,
                    )
                )

        logger.info("Found %d Kimi conversations", len(conversations))
        return conversations

    async def get_conversation(self, conversation_id: str) -> ChatConversation:
        """Get a full conversation from Kimi by navigating to its page."""
        url = f"{KIMI_BASE_URL}/chat/{conversation_id}"
        page = await self.get_page(url)
        await self.session.ensure_login(page, "kimi")
        await page.wait_for_load_state("networkidle")

        # Wait for messages to load
        selectors = self.get_selectors()
        try:
            await page.wait_for_selector(selectors["message_content"], timeout=10000)
        except Exception:
            logger.warning("No message content found on page %s", url)

        # Scroll to load all messages
        await self.handle_dynamic_loading(page)

        # Extract messages
        messages = await self.extract_messages_from_page(page)

        # Extract title
        title = ""
        title_el = await page.query_selector("h1, [class*='title']")
        if title_el:
            title = (await title_el.text_content() or "").strip()
        if not title:
            title = f"Kimi Chat {conversation_id[:8]}"

        return ChatConversation(
            id=conversation_id,
            title=title,
            platform=Platform.KIMI,
            messages=messages,
            url=url,
        )

    async def extract_messages_from_page(self, page: Page) -> list[ChatMessage]:
        """Extract all messages from the current Kimi conversation page."""
        selectors = self.get_selectors()
        messages: list[ChatMessage] = []

        # Find all message containers
        containers = await page.query_selector_all(
            '[class*="message-item"], [class*="message"]'
        )

        for container in containers:
            role = await self._detect_role(container)
            if role is None:
                continue

            parts = await self._extract_parts(container, page)
            if not parts:
                continue

            messages.append(ChatMessage(role=role, parts=parts))

        logger.info("Extracted %d messages from Kimi page", len(messages))
        return messages

    async def _detect_role(self, container) -> Optional[Role]:
        """Detect whether a message container is from user or assistant."""
        class_attr = await container.get_attribute("class") or ""

        # Check for user message indicators
        user_patterns = ["user", "human", "self"]
        assistant_patterns = ["assistant", "bot", "ai", "kimi"]

        class_lower = class_attr.lower()
        if any(p in class_lower for p in user_patterns):
            return Role.USER
        if any(p in class_lower for p in assistant_patterns):
            return Role.ASSISTANT

        # Fallback: check data attributes
        data_role = await container.get_attribute("data-role") or await container.get_attribute(
            "data-message-author-role"
        )
        if data_role:
            if "user" in data_role.lower() or "human" in data_role.lower():
                return Role.USER
            if "assistant" in data_role.lower():
                return Role.ASSISTANT

        return None

    async def _extract_parts(self, container, page: Page) -> list[ContentPart]:
        """Extract all content parts from a message container."""
        parts: list[ContentPart] = []

        # 1. Extract text content (from markdown containers)
        content_els = await container.query_selector_all(
            '[class*="markdown"], [class*="msg-content"], [class*="message-text"]'
        )
        for el in content_els:
            # Get full HTML to parse code blocks
            html = await el.inner_html()
            text_content = (await el.text_content() or "").strip()

            if not text_content:
                continue

            # Extract code blocks separately
            code_els = await el.query_selector_all("pre code")
            if code_els:
                # Split text around code blocks
                parts.extend(await self._parse_mixed_content(el))
            else:
                if text_content:
                    parts.append(ContentPart(type=ContentType.TEXT, text=text_content))

        # 2. Extract images (matplotlib charts, etc.)
        if self.config.download_images:
            images = await self._extract_images(container, page)
            parts.extend(images)

        # 3. Extract code execution results
        result_parts = await self._extract_code_results(container)
        parts.extend(result_parts)

        return parts

    async def _parse_mixed_content(self, el) -> list[ContentPart]:
        """Parse an element containing both text and code blocks."""
        # Get full text and use the core content parser
        full_text = (await el.text_content() or "").strip()
        if not full_text:
            return []

        # Also get code blocks via DOM for better language detection
        dom_code_blocks = await self.extractor.get_code_blocks(el.owner_page, "pre code")

        if dom_code_blocks:
            parts: list[ContentPart] = []
            for cb in dom_code_blocks:
                parts.append(
                    ContentPart(
                        type=ContentType.CODE_BLOCK,
                        code_block=CodeBlock(language=cb["language"], code=cb["code"]),
                    )
                )
            # Add surrounding text
            code_text = "\n".join(cb["code"] for cb in dom_code_blocks)
            remaining = full_text.replace(code_text, "").strip() if code_text else full_text
            if remaining:
                parts.insert(0, ContentPart(type=ContentType.TEXT, text=remaining))
            return parts

        # Fallback to text-based parsing
        return extract_code_blocks(full_text)

    async def _extract_images(self, container, page: Page) -> list[ContentPart]:
        """Extract images from a message container."""
        parts: list[ContentPart] = []
        exclude = ["avatar", "icon", "logo", "emoji", "loading"]

        img_els = await container.query_selector_all("img")
        for img in img_els:
            src = await img.get_attribute("src") or ""
            if not src or any(p in src.lower() for p in exclude):
                continue

            alt = await img.get_attribute("alt") or ""

            # Download image
            local_path = await self.image_handler.download_image(page, src)

            parts.append(
                ContentPart(
                    type=ContentType.IMAGE,
                    image=ImageData(
                        src=src,
                        alt=alt,
                        local_path=local_path,
                    ),
                )
            )

        return parts

    async def _extract_code_results(self, container) -> list[ContentPart]:
        """Extract code execution results from containers."""
        parts: list[ContentPart] = []
        selectors = self.get_selectors()

        result_els = await container.query_selector_all(selectors["code_result"])
        for el in result_els:
            text = (await el.text_content() or "").strip()
            if text:
                parts.append(ContentPart(type=ContentType.TOOL_RESULT, text=f"```\n{text}\n```"))

        return parts


# Auto-register this adapter
register_browser_adapter(Platform.KIMI, KimiBrowserAdapter)
