"""Core data types shared by browser and API approaches."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Platform(str, Enum):
    KIMI = "kimi"
    CHATGPT = "chatgpt"
    CLAUDE = "claude"
    GEMINI = "gemini"


class Role(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ContentType(str, Enum):
    TEXT = "text"
    CODE_BLOCK = "code_block"
    IMAGE = "image"
    FILE_ATTACHMENT = "file_attachment"
    SEARCH_RESULT = "search_result"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


@dataclass
class CodeBlock:
    language: str
    code: str
    output: Optional[str] = None
    output_images: list[str] = field(default_factory=list)  # base64 or local paths


@dataclass
class ImageData:
    src: str  # Original URL or path
    alt: str = ""
    local_path: Optional[str] = None  # After download
    data_url: Optional[str] = None  # Base64 data URL


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str = ""


@dataclass
class ToolCall:
    tool_name: str
    arguments: dict
    call_id: Optional[str] = None


@dataclass
class ToolResult:
    call_id: str
    output: str
    images: list[ImageData] = field(default_factory=list)


@dataclass
class FileAttachment:
    filename: str
    file_type: str  # MIME type
    url: Optional[str] = None
    local_path: Optional[str] = None


@dataclass
class ContentPart:
    type: ContentType
    text: Optional[str] = None
    code_block: Optional[CodeBlock] = None
    image: Optional[ImageData] = None
    search_result: Optional[SearchResult] = None
    tool_call: Optional[ToolCall] = None
    tool_result: Optional[ToolResult] = None
    file_attachment: Optional[FileAttachment] = None


@dataclass
class ChatMessage:
    role: Role
    parts: list[ContentPart]
    timestamp: Optional[datetime] = None
    model: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def text_content(self) -> str:
        return "\n".join(
            p.text for p in self.parts if p.type == ContentType.TEXT and p.text
        )

    @property
    def code_blocks(self) -> list[CodeBlock]:
        return [p.code_block for p in self.parts if p.code_block is not None]

    @property
    def images(self) -> list[ImageData]:
        return [p.image for p in self.parts if p.image is not None]


@dataclass
class ConversationSummary:
    id: str
    title: str
    platform: Platform
    url: Optional[str] = None
    updated_at: Optional[datetime] = None


@dataclass
class ChatConversation:
    id: str
    title: str
    platform: Platform
    messages: list[ChatMessage]
    url: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    @property
    def message_count(self) -> int:
        return len(self.messages)
