"""Claude Anthropic API adapter.

Note: Anthropic API does not have conversation listing endpoints.
This adapter is primarily useful for conversations created via the API.
For web conversations, use the browser adapter or email export.
"""

from __future__ import annotations

import logging
from typing import Optional

from ....core.types import (
    ChatConversation,
    ConversationSummary,
    Platform,
)
from ...base_adapter import APIPlatformAdapter
from ...runner import register_api_adapter

logger = logging.getLogger(__name__)


class ClaudeAPIAdapter(APIPlatformAdapter):
    """API adapter for Claude via Anthropic SDK.

    Limitation: Cannot list or retrieve web UI conversations.
    Only useful for API-created conversations.
    """

    @property
    def platform(self) -> Platform:
        return Platform.CLAUDE

    async def authenticate(self) -> None:
        api_key = self.auth.require_api_key("claude")
        try:
            import anthropic

            self._client = anthropic.AsyncAnthropic(api_key=api_key)
        except ImportError:
            raise ImportError("Install anthropic package: pip install anthropic")

    async def list_conversations(self, limit: int = 50) -> list[ConversationSummary]:
        """Not supported — Anthropic API has no conversation listing."""
        logger.warning("Anthropic API does not support listing conversations")
        return []

    async def get_conversation(self, conversation_id: str) -> ChatConversation:
        """Not supported — Anthropic API has no conversation retrieval."""
        raise NotImplementedError(
            "Anthropic API cannot retrieve conversations. "
            "Use the browser adapter for web conversations."
        )


register_api_adapter(Platform.CLAUDE, ClaudeAPIAdapter)
