"""Document schemas."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from uuid import UUID


class RagbotDocumentResponse(BaseModel):
    """Response schema for ragbot-data document."""
    id: UUID
    file_path: str
    content_hash: str
    file_size: int
    modified_at: datetime
    indexed_at: Optional[datetime]
    embedding_status: str
    chunk_count: int
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RagbotDocumentList(BaseModel):
    """List of ragbot-data documents."""
    total: int
    documents: list[RagbotDocumentResponse]


class EmbeddingStatusResponse(BaseModel):
    """Embedding status summary."""
    total_files: int
    indexed: int
    pending: int
    failed: int
    deleted: int
    last_update: Optional[datetime]
    queue_size: int


class EmbedTriggerRequest(BaseModel):
    """Request to trigger re-embedding."""
    file_path: Optional[str] = None  # None = re-embed all


class EmbedTriggerResponse(BaseModel):
    """Response from embed trigger."""
    message: str
    files_queued: int


class EmbeddingGenerateRequest(BaseModel):
    """Request to generate embedding for text."""
    text: str


class EmbeddingGenerateResponse(BaseModel):
    """Response with generated embedding."""
    embedding: list[float]
    model: str
    dimensions: int
