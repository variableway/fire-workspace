"""JSON export formatter."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime

from ..types import ChatConversation
from .base import ExportFormatter


class _DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return f"<bytes len={len(obj)}>"
        return super().default(obj)


class JSONFormatter(ExportFormatter):
    """Export conversations as structured JSON preserving all metadata."""

    def format_conversation(self, conversation: ChatConversation) -> str:
        data = self._to_dict(conversation)
        return json.dumps(data, indent=2, ensure_ascii=False, cls=_DateTimeEncoder)

    def file_extension(self) -> str:
        return "json"

    def _to_dict(self, conv: ChatConversation) -> dict:
        return {
            "id": conv.id,
            "title": conv.title,
            "platform": conv.platform.value,
            "url": conv.url,
            "created_at": conv.created_at.isoformat() if conv.created_at else None,
            "updated_at": conv.updated_at.isoformat() if conv.updated_at else None,
            "model": conv.model,
            "message_count": conv.message_count,
            "messages": [self._message_to_dict(m) for m in conv.messages],
            "metadata": conv.metadata,
        }

    def _message_to_dict(self, msg) -> dict:
        result = {
            "role": msg.role.value,
            "parts": [],
        }
        if msg.timestamp:
            result["timestamp"] = msg.timestamp.isoformat()
        if msg.model:
            result["model"] = msg.model

        for part in msg.parts:
            p: dict = {"type": part.type.value}
            if part.text:
                p["text"] = part.text
            if part.code_block:
                p["code_block"] = {
                    "language": part.code_block.language,
                    "code": part.code_block.code,
                    "output": part.code_block.output,
                }
            if part.image:
                p["image"] = {
                    "src": part.image.src,
                    "alt": part.image.alt,
                }
            if part.search_result:
                p["search_result"] = {
                    "title": part.search_result.title,
                    "url": part.search_result.url,
                    "snippet": part.search_result.snippet,
                }
            if part.tool_call:
                p["tool_call"] = {
                    "tool_name": part.tool_call.tool_name,
                    "arguments": part.tool_call.arguments,
                    "call_id": part.tool_call.call_id,
                }
            if part.tool_result:
                p["tool_result"] = {
                    "call_id": part.tool_result.call_id,
                    "output": part.tool_result.output,
                }
            if part.file_attachment:
                p["file_attachment"] = {
                    "filename": part.file_attachment.filename,
                    "file_type": part.file_attachment.file_type,
                    "url": part.file_attachment.url,
                }
            result["parts"].append(p)

        return result
