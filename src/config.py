"""Configuration management for osu! Beatmap Downloader."""

import json
import os
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class Config:
    """Application configuration."""
    client_id: int = 0
    client_secret: str = ""
    download_path: str = ""
    cache_path: str = ""
    mirror_url: str = "https://catboy.best"
    max_concurrent_downloads: int = 3

    def is_valid(self) -> bool:
        """Check if OAuth credentials are configured."""
        return self.client_id > 0 and len(self.client_secret) > 0


class ConfigManager:
    """Manages application configuration."""

    DEFAULT_CONFIG_NAME = "config.json"

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize config manager.

        Args:
            config_dir: Directory to store config. Defaults to app directory.
        """
        if config_dir is None:
            # Use app directory for config
            config_dir = Path(__file__).parent.parent

        self.config_dir = Path(config_dir)
        self.config_path = self.config_dir / self.DEFAULT_CONFIG_NAME
        self._config: Optional[Config] = None

        # Set up default paths
        self._default_download_path = self.config_dir / "downloads"
        self._default_cache_path = self.config_dir / "cache"

    def load(self) -> Config:
        """Load configuration from file or create default."""
        if self._config is not None:
            return self._config

        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                self._config = Config(**data)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Error loading config: {e}")
                self._config = self._create_default()
        else:
            self._config = self._create_default()

        # Ensure directories exist
        self._ensure_directories()

        return self._config

    def save(self, config: Config) -> None:
        """Save configuration to file."""
        self._config = config
        self._ensure_directories()

        with open(self.config_path, 'w') as f:
            json.dump(asdict(config), f, indent=2)

    def _create_default(self) -> Config:
        """Create default configuration."""
        return Config(
            download_path=str(self._default_download_path),
            cache_path=str(self._default_cache_path)
        )

    def _ensure_directories(self) -> None:
        """Ensure required directories exist."""
        if self._config:
            Path(self._config.download_path).mkdir(parents=True, exist_ok=True)
            Path(self._config.cache_path).mkdir(parents=True, exist_ok=True)
