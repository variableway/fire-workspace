"""Abstract base for export formatters."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..types import ChatConversation


class ExportFormatter(ABC):
    """Base class for all export format implementations."""

    @abstractmethod
    def format_conversation(self, conversation: ChatConversation) -> str:
        """Convert a conversation to the target format string."""

    @abstractmethod
    def file_extension(self) -> str:
        """Return the file extension (without dot), e.g. 'md'."""

    def format_filename(self, conversation: ChatConversation) -> str:
        """Generate a safe filename for the conversation."""
        safe_title = "".join(
            c if c.isalnum() or c in (" ", "-", "_") else "_" for c in conversation.title
        ).strip()
        return f"{safe_title}.{self.file_extension()}"
