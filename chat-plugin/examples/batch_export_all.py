"""Example: Batch export from multiple platforms.

Usage:
    python examples/batch_export_all.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chat_export.api.runner import APIRunner
from chat_export.browser.runner import BrowserRunner
from chat_export.core.types import Platform


async def browser_export():
    """Export from all platforms via browser."""
    runner = BrowserRunner()
    try:
        for platform in [Platform.KIMI, Platform.CHATGPT]:
            print(f"\n--- Exporting from {platform.value} via browser ---")
            try:
                paths = await runner.export_all(
                    platform, "markdown", Path(f"./exports/{platform.value}/browser")
                )
                print(f"Exported {len(paths)} conversations")
            except Exception as e:
                print(f"Error: {e}")
    finally:
        await runner.close()


async def api_export():
    """Export from all platforms via API."""
    runner = APIRunner()
    try:
        for platform in [Platform.KIMI, Platform.CHATGPT]:
            print(f"\n--- Exporting from {platform.value} via API ---")
            try:
                paths = await runner.export_all(
                    platform, "json", Path(f"./exports/{platform.value}/api")
                )
                print(f"Exported {len(paths)} conversations")
            except Exception as e:
                print(f"Error: {e}")
    finally:
        pass


async def main():
    print("=== Browser Export ===")
    await browser_export()

    print("\n=== API Export ===")
    await api_export()


if __name__ == "__main__":
    asyncio.run(main())
