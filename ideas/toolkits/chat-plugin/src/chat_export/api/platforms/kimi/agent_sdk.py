"""Kimi Agent SDK integration — extract code from tool_calls via SDK.

Uses the official kimi-agent-sdk to interact with Kimi's agent runtime,
intercepting tool calls (especially code_runner) to extract Python code.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Optional

from ....core.content import extract_tool_call_code
from ....core.types import (
    ChatConversation,
    ChatMessage,
    ContentPart,
    ContentType,
    ConversationSummary,
    Platform,
    Role,
    ToolCall,
)
from ...base_adapter import APIPlatformAdapter
from ...runner import register_api_adapter

logger = logging.getLogger(__name__)


class KimiAgentSDKAdapter(APIPlatformAdapter):
    """API adapter using kimi-agent-sdk for tool call extraction.

    This adapter creates NEW conversations via the SDK and captures
    all tool calls made during the conversation. It cannot access
    existing web conversations — use KimiMoonshotAdapter for that.

    Primary use case: extracting internal Python code that Kimi
    generates when analyzing files (music, data, etc.).
    """

    def __init__(self, work_dir: str = ".", **kwargs):
        super().__init__(**kwargs)
        self.work_dir = work_dir
        self._session = None
        self._captured_tool_calls: list[dict] = []
        self._captured_messages: list[str] = []

    @property
    def platform(self) -> Platform:
        return Platform.KIMI

    async def authenticate(self) -> None:
        """Verify kimi-agent-sdk is installed and configured."""
        try:
            from kimi_agent_sdk import Session  # noqa: F401
        except ImportError:
            raise ImportError(
                "kimi-agent-sdk is not installed. "
                "Install it with: pip install kimi-agent-sdk"
            )

        api_key = self.auth.get_config("kimi").api_key
        if not api_key:
            logger.info(
                "No MOONSHOT_API_KEY set — kimi-agent-sdk will use "
                "its default configuration or environment variables."
            )

    async def list_conversations(self, limit: int = 50) -> list[ConversationSummary]:
        """Not supported by Agent SDK — it creates new conversations only."""
        logger.warning("Agent SDK does not support listing existing conversations")
        return []

    async def get_conversation(self, conversation_id: str) -> ChatConversation:
        """Not supported by Agent SDK — use prompt_and_capture() instead."""
        raise NotImplementedError(
            "Agent SDK cannot retrieve existing conversations. "
            "Use prompt_and_capture() for new conversations."
        )

    async def prompt_and_capture(
        self,
        prompt_text: str,
        auto_approve: bool = True,
    ) -> ChatConversation:
        """Send a prompt via the Agent SDK and capture all tool calls.

        This is the primary method for extracting Kimi's internal code.
        Returns a ChatConversation with all tool calls captured as
        ContentPart objects.

        Args:
            prompt_text: The prompt to send to Kimi.
            auto_approve: Whether to auto-approve all tool calls.

        Returns:
            ChatConversation with captured tool calls and responses.
        """
        from kimi_agent_sdk import ApprovalRequest, Session, TextPart

        self._captured_tool_calls = []
        self._captured_messages = []

        async with await Session.create() as session:
            self._session = session
            messages: list[ChatMessage] = []

            async for wire_msg in session.prompt(prompt_text):
                if isinstance(wire_msg, TextPart):
                    self._captured_messages.append(wire_msg.text)

                elif isinstance(wire_msg, ApprovalRequest):
                    tool_info = self._extract_from_approval(wire_msg)
                    if tool_info:
                        self._captured_tool_calls.append(tool_info)

                        # Add tool call as a message
                        messages.append(
                            ChatMessage(
                                role=Role.ASSISTANT,
                                parts=[
                                    ContentPart(
                                        type=ContentType.TOOL_CALL,
                                        tool_call=ToolCall(
                                            tool_name=tool_info["tool_name"],
                                            arguments=tool_info.get("arguments", {}),
                                            call_id=tool_info.get("call_id"),
                                        ),
                                    )
                                ],
                            )
                        )

                    if auto_approve:
                        wire_msg.resolve("approve")

        # Build final assistant message from captured text
        full_text = "".join(self._captured_messages)
        if full_text:
            from ....core.content import extract_code_blocks

            text_parts = extract_code_blocks(full_text)
            messages.append(
                ChatMessage(
                    role=Role.ASSISTANT,
                    parts=text_parts,
                )
            )

        return ChatConversation(
            id="agent-sdk-session",
            title=prompt_text[:80],
            platform=Platform.KIMI,
            messages=messages,
        )

    async def extract_code_from_files(
        self,
        file_description: str,
        analysis_prompt: str,
    ) -> dict:
        """Analyze files via Agent SDK and extract all generated Python code.

        Convenience method for the Task 3 use case: extracting Kimi's
        internal analysis code when processing uploaded files.

        Args:
            file_description: Description of the files to analyze.
            analysis_prompt: What analysis to perform.

        Returns:
            Dict with 'conversation', 'extracted_code', 'tool_calls'.
        """
        full_prompt = f"{analysis_prompt}\n\nFiles:\n{file_description}"
        conv = await self.prompt_and_capture(full_prompt)

        extracted_code = []
        tool_call_summaries = []

        for msg in conv.messages:
            for part in msg.parts:
                if part.type == ContentType.TOOL_CALL and part.tool_call:
                    tc = part.tool_call
                    code = extract_tool_call_code(tc.arguments)
                    if code:
                        extracted_code.append(
                            {
                                "tool_name": tc.tool_name,
                                "code": code,
                                "arguments": tc.arguments,
                            }
                        )
                    tool_call_summaries.append(
                        {
                            "tool_name": tc.tool_name,
                            "has_code": code is not None,
                            "arguments_keys": list(tc.arguments.keys()),
                        }
                    )

        return {
            "conversation": conv,
            "extracted_code": extracted_code,
            "tool_calls": tool_call_summaries,
        }

    def _extract_from_approval(self, req) -> dict | None:
        """Extract tool call info from an ApprovalRequest."""
        try:
            info = {
                "tool_name": getattr(req, "tool_name", "unknown"),
            }

            if hasattr(req, "function_arguments"):
                args = req.function_arguments
                if isinstance(args, str):
                    args = json.loads(args)
                info["arguments"] = args

            if hasattr(req, "call_id"):
                info["call_id"] = req.call_id

            return info
        except Exception as e:
            logger.warning("Failed to extract tool info from approval: %s", e)
            return None

    async def close(self) -> None:
        self._session = None


register_api_adapter(Platform.KIMI, KimiAgentSDKAdapter)
