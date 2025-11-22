"""Profile-related database models."""
from typing import Optional, TYPE_CHECKING

from sqlalchemy import String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .user import User
    from .document import Document
    from .conversation import Conversation


class Profile(Base, TimestampMixin):
    """Profile model for user preferences and configurations."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Settings stored as JSON
    # Example: {"default_model": "gpt-4", "temperature": 0.7, "max_tokens": 4096}
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="profiles")
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="profile",
        cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="profile"
    )

    def __repr__(self) -> str:
        return f"<Profile(id={self.id}, name='{self.name}', user_id={self.user_id})>"
