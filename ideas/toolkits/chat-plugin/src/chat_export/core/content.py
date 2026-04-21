"""Content extraction helpers for parsing DOM and API responses."""

from __future__ import annotations

import re
from typing import Optional

from .types import CodeBlock, ContentPart, ContentType


def extract_code_blocks(text: str) -> list[ContentPart]:
    """Extract fenced code blocks from markdown-like text.

    Returns ContentParts of type CODE_BLOCK for each found block,
    and TEXT parts for the text between blocks.
    """
    parts: list[ContentPart] = []
    pattern = re.compile(r"```(\w*)\n(.*?)```", re.DOTALL)
    last_end = 0

    for match in pattern.finditer(text):
        # Text before this code block
        if match.start() > last_end:
            between = text[last_end : match.start()].strip()
            if between:
                parts.append(ContentPart(type=ContentType.TEXT, text=between))

        language = match.group(1) or "text"
        code = match.group(2)
        parts.append(
            ContentPart(
                type=ContentType.CODE_BLOCK,
                code_block=CodeBlock(language=language, code=code),
            )
        )
        last_end = match.end()

    # Remaining text after last code block
    if last_end < len(text):
        remaining = text[last_end:].strip()
        if remaining:
            parts.append(ContentPart(type=ContentType.TEXT, text=remaining))

    # No code blocks found — return the whole text as one part
    if not parts and text.strip():
        parts.append(ContentPart(type=ContentType.TEXT, text=text.strip()))

    return parts


def extract_tool_call_code(arguments: dict) -> Optional[str]:
    """Extract Python code from a tool_call's function arguments.

    Handles common patterns like Kimi's code_runner tool.
    """
    if "code" in arguments:
        return arguments["code"]
    if "source" in arguments:
        return arguments["source"]
    if "script" in arguments:
        return arguments["script"]
    return None
