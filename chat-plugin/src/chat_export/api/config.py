"""API/SDK approach configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class APIConfig:
    """Configuration for API/SDK-based extraction."""

    # Rate limiting
    requests_per_minute: int = 30
    concurrent_requests: int = 3

    # Pagination
    page_size: int = 20

    # Output
    download_images: bool = True
    image_output_dir: Path = field(default_factory=lambda: Path("./exports/images"))

    # Timeouts
    request_timeout: int = 60  # seconds
