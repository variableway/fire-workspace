"""Gemini Google API adapter.

Note: Google Generative AI API has limited conversation management.
This adapter is primarily useful for API-created conversations.
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


class GeminiAPIAdapter(APIPlatformAdapter):
    """API adapter for Gemini via Google Generative AI SDK.

    Limitation: Cannot easily list or retrieve web UI conversations.
    Only useful for API-created conversations.
    """

    @property
    def platform(self) -> Platform:
        return Platform.GEMINI

    async def authenticate(self) -> None:
        api_key = self.auth.require_api_key("gemini")
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
        except ImportError:
            raise ImportError("Install google-generativeai: pip install google-generativeai")

    async def list_conversations(self, limit: int = 50) -> list[ConversationSummary]:
        """Not supported — Gemini API has no conversation listing."""
        logger.warning("Gemini API does not support listing conversations")
        return []

    async def get_conversation(self, conversation_id: str) -> ChatConversation:
        """Not supported — Gemini API has no conversation retrieval."""
        raise NotImplementedError(
            "Gemini API cannot retrieve conversations. "
            "Use the browser adapter for web conversations."
        )


register_api_adapter(Platform.GEMINI, GeminiAPIAdapter)
