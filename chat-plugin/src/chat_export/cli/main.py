"""CLI interface for chat-export."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ..core.export.factory import available_formats
from ..core.types import Platform

console = Console()


def _run(coro):
    """Run an async function from sync Click callback."""
    return asyncio.run(coro)


@click.group()
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool):
    """Chat Export — Extract conversations from AI chat platforms."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


# ── Browser commands ──────────────────────────────────────────


@cli.group()
def browser():
    """Browser automation approach (Playwright)."""


@browser.command("list")
@click.option("--platform", "-p", type=click.Choice(["kimi", "chatgpt", "claude", "gemini"]), required=True)
@click.option("--limit", "-n", default=20, help="Max conversations to list")
def browser_list(platform: str, limit: int):
    """List conversations from a platform via browser."""
    from ..browser.runner import BrowserRunner

    async def _list():
        runner = BrowserRunner()
        try:
            adapter = runner.get_adapter(Platform(platform))
            convs = await adapter.list_conversations(limit)
            table = Table(title=f"{platform.title()} Conversations")
            table.add_column("ID", style="dim")
            table.add_column("Title")
            table.add_column("URL", style="blue")
            for c in convs:
                table.add_row(c.id[:12], c.title, c.url or "")
            console.print(table)
        finally:
            await runner.close()

    _run(_list())


@browser.command("export")
@click.option("--platform", "-p", type=click.Choice(["kimi", "chatgpt", "claude", "gemini"]), required=True)
@click.option("--conversation-id", "-c", help="Specific conversation ID to export")
@click.option("--format", "-f", "fmt", type=click.Choice(available_formats()), default="markdown")
@click.option("--output", "-o", default="./exports", help="Output directory")
@click.option("--limit", "-n", default=None, type=int, help="Max conversations to export (omit for single)")
def browser_export(platform: str, conversation_id: str | None, fmt: str, output: str, limit: int | None):
    """Export conversations from a platform via browser."""
    from ..browser.runner import BrowserRunner

    async def _export():
        runner = BrowserRunner()
        try:
            adapter = runner.get_adapter(Platform(platform))
            output_dir = Path(output)

            if conversation_id:
                conv = await adapter.get_conversation(conversation_id)
                path = await runner.export(conv, fmt, output_dir)
                console.print(f"Exported: [green]{path}[/green]")
            else:
                paths = await runner.export_all(Platform(platform), fmt, output_dir, limit)
                console.print(f"Exported {len(paths)} conversations to {output_dir}")
        finally:
            await runner.close()

    _run(_export())


# ── API commands ──────────────────────────────────────────────


@cli.group()
def api():
    """API/SDK approach (direct API calls)."""


@api.command("list")
@click.option("--platform", "-p", type=click.Choice(["kimi", "chatgpt"]), required=True)
@click.option("--limit", "-n", default=20, help="Max conversations to list")
def api_list(platform: str, limit: int):
    """List conversations from a platform via API."""
    from ..api.runner import APIRunner

    async def _list():
        runner = APIRunner()
        try:
            adapter = runner.get_adapter(Platform(platform))
            await adapter.authenticate()
            convs = await adapter.list_conversations(limit)
            table = Table(title=f"{platform.title()} Conversations (API)")
            table.add_column("ID", style="dim")
            table.add_column("Title")
            for c in convs:
                table.add_row(c.id[:12], c.title)
            console.print(table)
        finally:
            pass

    _run(_list())


@api.command("export")
@click.option("--platform", "-p", type=click.Choice(["kimi", "chatgpt"]), required=True)
@click.option("--conversation-id", "-c", required=True, help="Conversation ID to export")
@click.option("--format", "-f", "fmt", type=click.Choice(available_formats()), default="json")
@click.option("--output", "-o", default="./exports", help="Output directory")
def api_export(platform: str, conversation_id: str, fmt: str, output: str):
    """Export a conversation from a platform via API."""
    from ..api.runner import APIRunner

    async def _export():
        runner = APIRunner()
        try:
            adapter = runner.get_adapter(Platform(platform))
            await adapter.authenticate()
            conv = await adapter.get_conversation(conversation_id)
            path = await runner.export(conv, fmt, Path(output))
            console.print(f"Exported: [green]{path}[/green]")
        finally:
            pass

    _run(_export())


# ── Kimi Agent SDK command ────────────────────────────────────


@cli.command("kimi-extract")
@click.option("--prompt", "-p", required=True, help="Prompt to send to Kimi")
@click.option("--format", "-f", "fmt", type=click.Choice(available_formats()), default="json")
@click.option("--output", "-o", default="./exports", help="Output directory")
def kimi_extract(prompt: str, fmt: str, output: str):
    """Extract code from Kimi via Agent SDK (captures tool_calls)."""
    from ..api.runner import APIRunner

    async def _extract():
        runner = APIRunner()
        try:
            from ..api.platforms.kimi.agent_sdk import KimiAgentSDKAdapter

            adapter = KimiAgentSDKAdapter()
            await adapter.authenticate()
            conv = await adapter.prompt_and_capture(prompt)
            path = await runner.export(conv, fmt, Path(output))
            console.print(f"Exported: [green]{path}[/green]")
            console.print(f"Messages: {conv.message_count}")
        finally:
            pass

    _run(_extract())


if __name__ == "__main__":
    cli()
