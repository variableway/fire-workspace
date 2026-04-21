"""Factory for creating export formatters by format name."""

from __future__ import annotations

from .base import ExportFormatter
from .json_export import JSONFormatter
from .markdown import MarkdownFormatter

_FORMATTERS: dict[str, type[ExportFormatter]] = {
    "markdown": MarkdownFormatter,
    "md": MarkdownFormatter,
    "json": JSONFormatter,
}


def get_formatter(format_name: str) -> ExportFormatter:
    """Get an export formatter instance by format name.

    Supported: 'markdown', 'md', 'json'
    """
    cls = _FORMATTERS.get(format_name.lower())
    if cls is None:
        supported = ", ".join(sorted(set(_FORMATTERS.keys())))
        raise ValueError(f"Unknown format '{format_name}'. Supported: {supported}")
    return cls()


def available_formats() -> list[str]:
    """Return unique available format names."""
    return sorted({cls().file_extension() for cls in set(_FORMATTERS.values())})
