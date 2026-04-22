"""Authentication handling for API adapters."""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class AuthConfig:
    """Authentication configuration for a specific platform."""

    api_key: Optional[str] = None
    refresh_token: Optional[str] = None
    session_token: Optional[str] = None
    base_url: Optional[str] = None


class AuthHandler:
    """Manages authentication credentials for API calls.

    Supports loading from environment variables and .env files.
    """

    # Environment variable mappings per platform
    ENV_MAP: dict[str, dict[str, str]] = {
        "kimi": {
            "api_key": "MOONSHOT_API_KEY",
            "refresh_token": "KIMI_REFRESH_TOKEN",
            "base_url": "MOONSHOT_BASE_URL",
        },
        "chatgpt": {
            "api_key": "OPENAI_API_KEY",
            "session_token": "CHATGPT_SESSION_TOKEN",
        },
        "claude": {
            "api_key": "ANTHROPIC_API_KEY",
        },
        "gemini": {
            "api_key": "GOOGLE_API_KEY",
        },
    }

    def __init__(self):
        self._configs: dict[str, AuthConfig] = {}

    def load_from_env(self, platform: str) -> AuthConfig:
        """Load auth configuration from environment variables."""
        env_map = self.ENV_MAP.get(platform, {})
        config = AuthConfig(
            api_key=os.environ.get(env_map.get("api_key", "")) or None,
            refresh_token=os.environ.get(env_map.get("refresh_token", "")) or None,
            session_token=os.environ.get(env_map.get("session_token", "")) or None,
            base_url=os.environ.get(env_map.get("base_url", "")) or None,
        )
        self._configs[platform] = config
        return config

    def get_config(self, platform: str) -> AuthConfig:
        """Get auth config, loading from env if not cached."""
        if platform not in self._configs:
            self.load_from_env(platform)
        return self._configs[platform]

    def set_config(self, platform: str, config: AuthConfig) -> None:
        """Manually set auth config for a platform."""
        self._configs[platform] = config

    def require_api_key(self, platform: str) -> str:
        """Get API key for a platform, raising if not configured."""
        config = self.get_config(platform)
        if not config.api_key:
            env_var = self.ENV_MAP.get(platform, {}).get("api_key", f"{platform.upper()}_API_KEY")
            raise ValueError(
                f"API key not found for {platform}. "
                f"Set the {env_var} environment variable or call auth.set_config()."
            )
        return config.api_key
