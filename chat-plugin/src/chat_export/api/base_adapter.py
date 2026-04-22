"""Abstract base class for API/SDK-based platform adapters."""

from __future__ import annotations

from abc import abstractmethod

from ..core.adapter_base import PlatformAdapter
from ..core.types import Platform
from .auth import AuthHandler
from .config import APIConfig
from .rate_limiter import RateLimiter


class APIPlatformAdapter(PlatformAdapter):
    """Base class for API/SDK-based platform adapters.

    Provides shared logic for authentication, rate limiting,
    and pagination. Subclasses implement platform-specific API calls.
    """

    def __init__(self, auth: AuthHandler | None = None, config: APIConfig | None = None):
        self.config = config or APIConfig()
        self.auth = auth or AuthHandler()
        self.rate_limiter = RateLimiter(self.config.requests_per_minute)

    @property
    @abstractmethod
    def platform(self) -> Platform:
        """Which platform this adapter handles."""

    @abstractmethod
    async def authenticate(self) -> None:
        """Set up authentication (token refresh, API key validation, etc.)."""

    async def close(self) -> None:
        """Clean up HTTP clients. Default: no-op."""
