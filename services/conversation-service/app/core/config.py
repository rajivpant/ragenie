"""Application configuration."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "RaGenie Conversation Service"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str

    # Qdrant
    QDRANT_HOST: str
    QDRANT_PORT: int
    QDRANT_COLLECTION: str = "ragenie_documents"

    # Auth
    AUTH_SERVICE_URL: str = "http://auth-service:8000"

    # Document Service
    DOCUMENT_SERVICE_URL: str = "http://document-service:8000"

    # LLM Gateway
    LLM_GATEWAY_URL: str = "http://llm-gateway-service:8000"

    # RAG Configuration
    RAG_TOP_K: int = 5  # Number of top documents to retrieve
    RAG_SIMILARITY_THRESHOLD: float = 0.7  # Minimum similarity score

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
