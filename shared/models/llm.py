"""LLM provider and model database models."""
from typing import Optional
from decimal import Decimal

from sqlalchemy import String, Text, Integer, ForeignKey, Boolean, Numeric, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class LLMProvider(Base, TimestampMixin):
    """LLM Provider model for API configuration."""

    __tablename__ = "llm_providers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # API configuration
    api_endpoint: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    api_key_name: Mapped[str] = mapped_column(String(100), nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Provider-specific configuration stored as JSON
    # Example: {"supports_streaming": true, "supports_function_calling": true}
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    models: Mapped[list["LLMModel"]] = relationship(
        "LLMModel",
        back_populates="provider",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<LLMProvider(id={self.id}, name='{self.name}')>"


class LLMModel(Base, TimestampMixin):
    """LLM Model model for available AI models."""

    __tablename__ = "llm_models"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    provider_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("llm_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Model identification
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # small, medium, large, reasoning

    # Model capabilities
    max_input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    max_output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    supports_system_role: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_streaming: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Default parameters
    default_temperature: Mapped[float] = mapped_column(Numeric(precision=3, scale=2), default=0.7, nullable=False)
    default_max_tokens: Mapped[int] = mapped_column(Integer, default=4096, nullable=False)

    # Pricing (per token)
    cost_per_input_token: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=12, scale=10),
        nullable=True
    )
    cost_per_output_token: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(precision=12, scale=10),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Model-specific configuration stored as JSON
    # Example: {"context_window": 128000, "training_cutoff": "2024-04"}
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    provider: Mapped["LLMProvider"] = relationship("LLMProvider", back_populates="models")

    def __repr__(self) -> str:
        return f"<LLMModel(id={self.id}, name='{self.name}', category='{self.category}')>"
