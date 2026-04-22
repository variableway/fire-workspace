"""Browser automation configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class BrowserConfig:
    """Configuration for browser automation."""

    headless: bool = False
    profile_dir: Path = field(default_factory=lambda: Path.home() / ".cache" / "chat-export" / "browser-profile")
    timeout: int = 30_000  # ms
    slow_mo: int = 0  # ms delay between actions

    # Stealth options
    disable_webdriver_flag: bool = True

    # Image handling
    download_images: bool = True
    image_output_dir: Path = field(default_factory=lambda: Path("./exports/images"))

    # Scroll behavior
    scroll_timeout: int = 2000  # ms to wait after each scroll
    max_scrolls: int = 50
