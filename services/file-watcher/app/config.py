"""Configuration for file watcher service."""
import os
from pathlib import Path


class Settings:
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://ragenie:ragenie_dev_password@localhost:5432/ragenie')

    # File paths
    RAGBOT_DATA_PATH: Path = Path(os.getenv('RAGBOT_DATA_PATH', '/data/ragbot-data'))

    # Watcher settings
    POLLING_INTERVAL: int = int(os.getenv('POLLING_INTERVAL', '5'))  # seconds

    # File patterns
    INCLUDE_EXTENSIONS: tuple = ('.md', '.txt')
    EXCLUDE_PATTERNS: tuple = (
        '.git',
        '__pycache__',
        '.DS_Store',
        'node_modules',
        '.pytest_cache',
    )

    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')


settings = Settings()
