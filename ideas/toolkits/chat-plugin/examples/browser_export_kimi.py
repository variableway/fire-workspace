"""Example: Export Kimi conversations via browser automation.

Usage:
    python examples/browser_export_kimi.py

Requires: pip install playwright && playwright install chromium
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chat_export.browser.config import BrowserConfig
from chat_export.browser.runner import BrowserRunner
from chat_export.core.types import Platform


async def main():
    # Configure browser (headless=False for first run to log in)
    config = BrowserConfig(
        headless=False,  # Set True after first login
        download_images=True,
        image_output_dir=Path("./exports/kimi/images"),
    )

    runner = BrowserRunner(config)

    try:
        # List conversations
        adapter = runner.get_adapter(Platform.KIMI)
        conversations = await adapter.list_conversations(limit=10)
        print(f"Found {len(conversations)} conversations:")
        for c in conversations:
            print(f"  [{c.id[:8]}] {c.title}")

        if conversations:
            # Export the first conversation
            conv = await adapter.get_conversation(conversations[0].id)
            path = await runner.export(conv, "markdown", Path("./exports/kimi"))
            print(f"\nExported to: {path}")
            print(f"Messages: {conv.message_count}")

    finally:
        await runner.close()


if __name__ == "__main__":
    asyncio.run(main())
