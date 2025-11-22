"""Configuration for embedding worker service."""
import os
from pathlib import Path


class Settings:
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = os.getenv('DATABASE_URL', 'postgresql://ragenie:ragenie_dev_password@localhost:5432/ragenie')

    # Redis
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379/5')

    # Qdrant
    QDRANT_HOST: str = os.getenv('QDRANT_HOST', 'localhost')
    QDRANT_PORT: int = int(os.getenv('QDRANT_PORT', '6333'))
    QDRANT_COLLECTION: str = 'ragenie_documents'

    # File paths
    RAGBOT_DATA_PATH: Path = Path(os.getenv('RAGBOT_DATA_PATH', '/data/ragbot-data'))

    # MinIO (for user uploads, not ragbot-data)
    MINIO_ENDPOINT: str = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
    MINIO_ACCESS_KEY: str = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
    MINIO_SECRET_KEY: str = os.getenv('MINIO_SECRET_KEY', 'minioadmin123')
    MINIO_BUCKET: str = 'ragenie-documents'

    # OpenAI
    OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY', '')

    # Embedding settings
    EMBEDDING_MODEL: str = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
    EMBEDDING_DIMENSIONS: int = 1536  # For text-embedding-3-small
    CHUNK_SIZE: int = int(os.getenv('CHUNK_SIZE', '512'))
    CHUNK_OVERLAP: int = int(os.getenv('CHUNK_OVERLAP', '50'))

    # Worker settings
    BATCH_SIZE: int = int(os.getenv('BATCH_SIZE', '10'))  # Process N jobs at a time
    POLL_INTERVAL: int = int(os.getenv('POLL_INTERVAL', '5'))  # Seconds between queue checks
    MAX_RETRIES: int = int(os.getenv('MAX_RETRIES', '3'))

    # Cache settings
    CACHE_TTL: int = int(os.getenv('CACHE_TTL', '1800'))  # 30 minutes in seconds

    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')


settings = Settings()
