"""ChatGPT backend API client — uses session token for web conversations.

Uses ChatGPT's internal backend-api to list and retrieve conversations.
This is an unofficial API and may break at any time.
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
    ContentPart,
    ContentType,
    ConversationSummary,
    Platform,
    Role,
)
from ...base_adapter import APIPlatformAdapter
from ...runner import register_api_adapter

logger = logging.getLogger(__name__)

CHATGPT_API_BASE = "https://chatgpt.com/backend-api"


class ChatGPTAPIAdapter(APIPlatformAdapter):
    """API adapter for ChatGPT using the internal backend-api.

    Uses session token from browser cookies (__Secure-next-auth.session-token).
    """

    def __init__(self, session_token: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self._session_token = session_token
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def platform(self) -> Platform:
        return Platform.CHATGPT

    async def authenticate(self) -> None:
        """Set up HTTP client with session token."""
        if not self._session_token:
            config = self.auth.get_config("chatgpt")
            self._session_token = config.session_token

        if not self._session_token:
            raise ValueError(
                "ChatGPT session token not found. "
                "Set CHATGPT_SESSION_TOKEN env var or pass session_token parameter."
            )

        self._client = httpx.AsyncClient(
            base_url=CHATGPT_API_BASE,
            timeout=self.config.request_timeout,
            cookies={"__Secure-next-auth.session-token": self._session_token},
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
            },
        )
        logger.info("ChatGPT API client initialized")

    async def list_conversations(self, limit: int = 50) -> list[ConversationSummary]:
        """List conversations from ChatGPT."""
        await self._ensure_auth()
        await self.rate_limiter.acquire()

        resp = await self._client.get(
            "/conversations",
            params={"offset": 0, "limit": min(limit, 28)},
        )
        resp.raise_for_status()
        data = resp.json()

        conversations = []
        for item in data.get("items", []):
            conv_id = item.get("id", "")
            title = item.get("title", "")

            conversations.append(
                ConversationSummary(
                    id=conv_id,
                    title=title or f"Chat {conv_id[:8]}",
                    platform=Platform.CHATGPT,
                    url=f"https://chatgpt.com/c/{conv_id}",
                    updated_at=datetime.fromtimestamp(item.get("update_time", 0))
                    if item.get("update_time")
                    else None,
                )
            )

        logger.info("Listed %d ChatGPT conversations", len(conversations))
        return conversations

    async def get_conversation(self, conversation_id: str) -> ChatConversation:
        """Get a full conversation from ChatGPT."""
        await self._ensure_auth()
        await self.rate_limiter.acquire()

        resp = await self._client.get(f"/conversation/{conversation_id}")
        resp.raise_for_status()
        data = resp.json()

        title = data.get("title", f"ChatGPT Chat {conversation_id[:8]}")

        # Parse message mapping
        messages = []
        mapping = data.get("mapping", {})
        if mapping:
            # Sort by creation order
            nodes = sorted(
                mapping.values(),
                key=lambda n: n.get("message", {}).get("create_time") or 0,
            )

            for node in nodes:
                msg = node.get("message", {})
                if not msg:
                    continue

                role_str = msg.get("author", {}).get("role", "")
                if role_str == "user":
                    role = Role.USER
                elif role_str == "assistant":
                    role = Role.ASSISTANT
                elif role_str == "system":
                    continue
                else:
                    continue

                # Extract content
                content = msg.get("content", {})
                parts = []
                content_parts = content.get("parts", [])

                for part in content_parts:
                    if isinstance(part, str) and part.strip():
                        parts.extend(extract_code_blocks(part))
                    elif isinstance(part, dict):
                        # Handle images, code, etc.
                        if part.get("content_type") == "image_asset_pointer":
                            parts.append(
                                ContentPart(
                                    type=ContentType.IMAGE,
                                    image=ImageData(src=str(part.get("asset_pointer", ""))),
                                )
                            )

                if parts:
                    create_time = msg.get("create_time")
                    messages.append(
                        ChatMessage(
                            role=role,
                            parts=parts,
                            timestamp=datetime.fromtimestamp(create_time) if create_time else None,
                            model=msg.get("model_slug"),
                        )
                    )

        return ChatConversation(
            id=conversation_id,
            title=title,
            platform=Platform.CHATGPT,
            messages=messages,
            url=f"https://chatgpt.com/c/{conversation_id}",
        )

    async def _ensure_auth(self) -> None:
        if not self._client:
            await self.authenticate()

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None


register_api_adapter(Platform.CHATGPT, ChatGPTAPIAdapter)
