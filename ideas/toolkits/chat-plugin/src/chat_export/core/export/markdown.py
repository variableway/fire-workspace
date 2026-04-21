"""Markdown export formatter."""

from __future__ import annotations

from datetime import datetime

from ..types import ChatConversation, ChatMessage, ContentType, Role
from .base import ExportFormatter


class MarkdownFormatter(ExportFormatter):
    """Export conversations as Markdown with embedded images and code blocks."""

    def format_conversation(self, conversation: ChatConversation) -> str:
        lines: list[str] = []

        # Header
        lines.append(f"# {conversation.title}")
        lines.append("")

        meta_parts = [f"Platform: {conversation.platform.value}"]
        if conversation.model:
            meta_parts.append(f"Model: {conversation.model}")
        if conversation.created_at:
            meta_parts.append(f"Created: {conversation.created_at.isoformat()}")
        if conversation.url:
            meta_parts.append(f"URL: {conversation.url}")
        lines.append(f"> {' | '.join(meta_parts)}")
        lines.append("")

        lines.append("---")
        lines.append("")

        # Messages
        for msg in conversation.messages:
            lines.append(self._format_message(msg))
            lines.append("")

        return "\n".join(lines)

    def file_extension(self) -> str:
        return "md"

    def _format_message(self, msg: ChatMessage) -> str:
        role_label = {
            Role.USER: "**User**",
            Role.ASSISTANT: "**Assistant**",
            Role.SYSTEM: "**System**",
            Role.TOOL: "**Tool**",
        }.get(msg.role, f"**{msg.role.value}**")

        timestamp = ""
        if msg.timestamp:
            timestamp = f" <small>{msg.timestamp.strftime('%Y-%m-%d %H:%M')}</small>"

        parts = [f"### {role_label}{timestamp}", ""]

        for part in msg.parts:
            formatted = self._format_content_part(part)
            if formatted:
                parts.append(formatted)
                parts.append("")

        return "\n".join(parts)

    def _format_content_part(self, part) -> str:
        if part.type == ContentType.TEXT and part.text:
            return part.text

        if part.type == ContentType.CODE_BLOCK and part.code_block:
            cb = part.code_block
            lines = [f"```{cb.language}", cb.code, "```"]
            if cb.output:
                lines.append("")
                lines.append("**Output:**")
                lines.append("```")
                lines.append(cb.output)
                lines.append("```")
            return "\n".join(lines)

        if part.type == ContentType.IMAGE and part.image:
            img = part.image
            src = img.local_path or img.data_url or img.src
            return f"![{img.alt}]({src})"

        if part.type == ContentType.SEARCH_RESULT and part.search_result:
            sr = part.search_result
            return f"- [{sr.title}]({sr.url})\n  {sr.snippet}"

        if part.type == ContentType.TOOL_CALL and part.tool_call:
            tc = part.tool_call
            lines = ["<details>", f"<summary>Tool Call: {tc.tool_name}</summary>", ""]
            import json

            lines.append("```json")
            lines.append(json.dumps(tc.arguments, indent=2, ensure_ascii=False))
            lines.append("```")
            lines.append("</details>")
            return "\n".join(lines)

        if part.type == ContentType.TOOL_RESULT and part.tool_result:
            tr = part.tool_result
            lines = [f"**Tool Result** (`{tr.call_id}`):", "", tr.output]
            for img in tr.images:
                src = img.local_path or img.data_url or img.src
                lines.append(f"![{img.alt}]({src})")
            return "\n".join(lines)

        if part.type == ContentType.FILE_ATTACHMENT and part.file_attachment:
            fa = part.file_attachment
            src = fa.local_path or fa.url or ""
            return f"[{fa.filename}]({src})"

        return ""
