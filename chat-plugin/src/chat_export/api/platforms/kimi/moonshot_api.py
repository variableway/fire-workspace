"""Kimi Moonshot API client — uses refresh_token for Kimi web conversations.

Based on the unofficial API analysis from kimi-plugin-analysis.md.
Fetches conversation history including rich content (code, images, search results).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

import httpx

from ....core.content import extract_code_blocks
from ....core.types import (
    ChatConversation,
    ChatMessage,
    CodeBlock,
    ContentPart,
    ContentType,
    ConversationSummary,
    ImageData,
    Platform,
    Role,
    SearchResult,
    ToolCall,
    ToolResult,
)
from ...base_adapter import APIPlatformAdapter
from ...runner import register_api_adapter

logger = logging.getLogger(__name__)

KIMI_API_BASE = "https://kimi.moonshot.cn/api"


class KimiMoonshotAdapter(APIPlatformAdapter):
    """API adapter for Kimi using the internal Moonshot API.

    Uses refresh_token from browser Local Storage to authenticate.
    Can list and retrieve full conversations with rich content.
    """

    def __init__(self, refresh_token: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self._refresh_token = refresh_token
        self._access_token: Optional[str] = None
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def platform(self) -> Platform:
        return Platform.KIMI

    async def authenticate(self) -> None:
        """Exchange refresh_token for access_token."""
        if not self._refresh_token:
            config = self.auth.get_config("kimi")
            self._refresh_token = config.refresh_token

        if not self._refresh_token:
            raise ValueError(
                "Kimi refresh_token not found. "
                "Set KIMI_REFRESH_TOKEN env var or pass refresh_token parameter. "
                "Get it from browser Local Storage on kimi.moonshot.cn."
            )

        self._client = httpx.AsyncClient(
            base_url=KIMI_API_BASE,
            timeout=self.config.request_timeout,
        )

        # Exchange refresh_token for access_token
        resp = await self._client.post(
            "/auth/token/refresh",
            json={"refresh_token": self._refresh_token},
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data.get("access_token")

        if not self._access_token:
            raise ValueError("Failed to obtain access_token from refresh_token")

        # Update client with auth header
        self._client.headers["Authorization"] = f"Bearer {self._access_token}"
        logger.info("Kimi API authenticated successfully")

    async def list_conversations(self, limit: int = 50) -> list[ConversationSummary]:
        """List conversations from Kimi."""
        await self._ensure_auth()
        await self.rate_limiter.acquire()

        resp = await self._client.get("/chat", params={"size": min(limit, 50)})
        resp.raise_for_status()
        data = resp.json()

        conversations = []
        items = data if isinstance(data, list) else data.get("items", data.get("chats", []))

        for item in items:
            conv_id = item.get("id", "")
            title = item.get("name", item.get("title", ""))
            updated = item.get("updated_at", item.get("updated_time"))

            conversations.append(
                ConversationSummary(
                    id=conv_id,
                    title=title or f"Conversation {conv_id[:8]}",
                    platform=Platform.KIMI,
                    url=f"https://kimi.moonshot.cn/chat/{conv_id}",
                    updated_at=datetime.fromisoformat(updated) if updated else None,
                )
            )

        logger.info("Listed %d Kimi conversations", len(conversations))
        return conversations

    async def get_conversation(self, conversation_id: str) -> ChatConversation:
        """Get a full conversation with all messages and rich content."""
        await self._ensure_auth()
        await self.rate_limiter.acquire()

        # Fetch conversation detail
        resp = await self._client.get(f"/chat/{conversation_id}")
        resp.raise_for_status()
        data = resp.json()

        title = data.get("name", data.get("title", f"Kimi Chat {conversation_id[:8]}"))

        # Fetch messages
        await self.rate_limiter.acquire()
        msg_resp = await self._client.get(
            f"/chat/{conversation_id}/message",
            params={"size": 100},
        )
        msg_resp.raise_for_status()
        msg_data = msg_resp.json()

        messages = self._parse_messages(msg_data)

        return ChatConversation(
            id=conversation_id,
            title=title,
            platform=Platform.KIMI,
            messages=messages,
            url=f"https://kimi.moonshot.cn/chat/{conversation_id}",
        )

    def _parse_messages(self, data) -> list[ChatMessage]:
        """Parse API response into ChatMessage objects."""
        messages: list[ChatMessage] = []
        items = data if isinstance(data, list) else data.get("items", [])

        for item in items:
            role_str = item.get("role", "").lower()
            if role_str == "user":
                role = Role.USER
            elif role_str == "assistant":
                role = Role.ASSISTANT
            elif role_str == "system":
                role = Role.SYSTEM
            else:
                continue

            parts = self._parse_message_parts(item)
            if parts:
                timestamp = item.get("created_at", item.get("created_time"))
                messages.append(
                    ChatMessage(
                        role=role,
                        parts=parts,
                        timestamp=datetime.fromisoformat(timestamp) if timestamp else None,
                        model=item.get("model"),
                    )
                )

        return messages

    def _parse_message_parts(self, item: dict) -> list[ContentPart]:
        """Parse a single message's content into ContentPart objects."""
        parts: list[ContentPart] = []

        # Text content
        text = item.get("content", "")
        if isinstance(text, str) and text.strip():
            parts.extend(extract_code_blocks(text))
        elif isinstance(text, list):
            for block in text:
                if isinstance(block, dict):
                    block_type = block.get("type", "")
                    if block_type == "text":
                        block_text = block.get("text", "")
                        if block_text.strip():
                            parts.extend(extract_code_blocks(block_text))
                    elif block_type == "image_url":
                        url = block.get("image_url", {}).get("url", "")
                        if url:
                            parts.append(
                                ContentPart(
                                    type=ContentType.IMAGE,
                                    image=ImageData(src=url),
                                )
                            )

        # Tool calls (code_runner, search, etc.)
        tool_calls = item.get("tool_calls", [])
        for tc in tool_calls:
            func = tc.get("function", {})
            tool_name = func.get("name", "unknown")
            try:
                arguments = json.loads(func.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {}

            parts.append(
                ContentPart(
                    type=ContentType.TOOL_CALL,
                    tool_call=ToolCall(
                        tool_name=tool_name,
                        arguments=arguments,
                        call_id=tc.get("id"),
                    ),
                )
            )

            # Extract code from code_runner calls
            if tool_name == "code_runner" and "code" in arguments:
                parts.append(
                    ContentPart(
                        type=ContentType.CODE_BLOCK,
                        code_block=CodeBlock(
                            language="python",
                            code=arguments["code"],
                        ),
                    )
                )

        # Search references
        references = item.get("references", item.get("search_results", []))
        for ref in references:
            parts.append(
                ContentPart(
                    type=ContentType.SEARCH_RESULT,
                    search_result=SearchResult(
                        title=ref.get("title", ""),
                        url=ref.get("url", ref.get("link", "")),
                        snippet=ref.get("snippet", ref.get("abstract", "")),
                    ),
                )
            )

        return parts

    async def _ensure_auth(self) -> None:
        if not self._client or not self._access_token:
            await self.authenticate()

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


register_api_adapter(Platform.KIMI, KimiMoonshotAdapter)
