"""Abstract base class for all platform adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from .types import ChatConversation, ConversationSummary, Platform


class PlatformAdapter(ABC):
    """Base class for ALL platform adapters (both browser and API).

    Each concrete adapter handles platform-specific quirks internally,
    but exposes the same interface so downstream code (export, search)
    is identical regardless of extraction method.
    """

    @property
    @abstractmethod
    def platform(self) -> Platform:
        """Which platform this adapter handles."""

    @abstractmethod
    async def list_conversations(self, limit: int = 50) -> list[ConversationSummary]:
        """List available conversations."""

    @abstractmethod
    async def get_conversation(self, conversation_id: str) -> ChatConversation:
        """Get a single conversation with full message content."""

    async def get_all_conversations(self) -> AsyncIterator[ChatConversation]:
        """Iterate over all conversations."""
        summaries = await self.list_conversations()
        for summary in summaries:
            yield await self.get_conversation(summary.id)

    @abstractmethod
    async def close(self) -> None:
        """Clean up resources (browser pages, HTTP clients, etc.)."""
