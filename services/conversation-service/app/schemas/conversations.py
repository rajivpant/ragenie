"""Conversation and message schemas."""
from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    """Schema for creating a conversation."""
    title: str = Field(default="New Conversation", max_length=255)
    profile_id: Optional[int] = None


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: Optional[str] = Field(None, max_length=255)
    summary: Optional[str] = None
    state: Optional[dict] = None


class ConversationResponse(BaseModel):
    """Schema for conversation response."""
    id: int
    user_id: int
    profile_id: Optional[int]
    title: str
    summary: Optional[str]
    state: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationList(BaseModel):
    """Schema for list of conversations."""
    total: int
    conversations: List[ConversationResponse]


class MessageCreate(BaseModel):
    """Schema for creating a message."""
    role: str = Field(..., pattern="^(system|user|assistant)$")
    content: str


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: int
    conversation_id: int
    role: str
    content: str
    token_count: Optional[int]
    cost: Optional[Decimal]
    model_used: Optional[str]
    provider: Optional[str]
    metadata: Optional[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MessageList(BaseModel):
    """Schema for list of messages."""
    total: int
    messages: List[MessageResponse]


class RetrievedDocument(BaseModel):
    """Schema for a retrieved document chunk."""
    file_path: str
    chunk_index: int
    chunk_text: str
    similarity_score: float
    source: str
    category: Optional[str]
    tags: Optional[List[str]]


class RAGContextResponse(BaseModel):
    """Schema for RAG context assembly."""
    conversation_id: int
    profile_id: Optional[int]

    # Custom instructions from profile
    custom_instructions: Optional[str]

    # Retrieved documents from ragbot-data
    retrieved_documents: List[RetrievedDocument]

    # Recent conversation history
    conversation_history: List[MessageResponse]

    # Assembled context ready for LLM
    system_prompt: str
    user_query: str

    # Metadata
    total_retrieved: int
    retrieval_time_ms: float
