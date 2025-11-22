"""Document-related database models."""
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, Integer, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .profile import Profile


class DocumentType(str, enum.Enum):
    """Document type enumeration."""
    CUSTOM_INSTRUCTIONS = "custom_instructions"
    CURATED_DATASETS = "curated_datasets"
    GENERAL = "general"


class Document(Base, TimestampMixin):
    """Document model for storing user files and context."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    profile_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # File information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)  # MinIO path
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., .md, .txt, .pdf
    document_type: Mapped[DocumentType] = mapped_column(
        SQLEnum(DocumentType),
        nullable=False,
        default=DocumentType.GENERAL
    )

    # File metadata
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA256
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Additional metadata stored as JSON
    # Example: {"tags": ["work", "project-a"], "source": "upload", "version": 1}
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Cached content for quick retrieval (optional)
    cached_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="documents")
    profile: Mapped[Optional["Profile"]] = relationship("Profile", back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename='{self.filename}', type='{self.document_type}')>"
