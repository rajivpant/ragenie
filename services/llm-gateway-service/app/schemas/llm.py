"""LLM-related schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal


class MessageInput(BaseModel):
    """Message input schema."""
    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    """Chat completion request schema."""
    model: str = Field(..., description="Model identifier (e.g., gpt-4, claude-3-sonnet)")
    messages: List[MessageInput] = Field(..., description="List of messages")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(4096, gt=0, le=128000, description="Maximum tokens to generate")
    stream: bool = Field(False, description="Whether to stream the response")

    class Config:
        json_schema_extra = {
            "example": {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is the capital of France?"}
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
        }


class ChatResponse(BaseModel):
    """Chat completion response schema."""
    content: str = Field(..., description="Generated response content")
    model: str = Field(..., description="Model used")
    usage: Dict[str, int] = Field(..., description="Token usage statistics")
    finish_reason: str = Field(..., description="Reason for completion finish")
    cost: Optional[Decimal] = Field(None, description="Estimated cost in USD")


class SimplePromptRequest(BaseModel):
    """Simple prompt request (with context assembly)."""
    prompt: str = Field(..., description="User prompt")
    model: str = Field(..., description="Model to use")
    conversation_id: Optional[int] = Field(None, description="Conversation ID for history")
    profile_id: Optional[int] = Field(None, description="Profile ID for context documents")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(4096, gt=0, le=128000)

    class Config:
        json_schema_extra = {
            "example": {
                "prompt": "Explain quantum computing",
                "model": "gpt-4",
                "conversation_id": 1,
                "profile_id": 1,
                "temperature": 0.7,
                "max_tokens": 2000
            }
        }


class TokenCountRequest(BaseModel):
    """Token counting request schema."""
    text: Optional[str] = Field(None, description="Text to count tokens for")
    messages: Optional[List[MessageInput]] = Field(None, description="Messages to count tokens for")
    model: str = Field("gpt-4", description="Model for accurate token counting")


class TokenCountResponse(BaseModel):
    """Token counting response schema."""
    token_count: int = Field(..., description="Number of tokens")
    model: str = Field(..., description="Model used for counting")


class LLMProviderResponse(BaseModel):
    """LLM provider response schema."""
    id: int
    name: str
    display_name: str
    description: Optional[str]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class LLMModelResponse(BaseModel):
    """LLM model response schema."""
    id: int
    provider_id: int
    name: str
    display_name: str
    category: str
    max_input_tokens: int
    max_output_tokens: int
    supports_system_role: bool
    supports_streaming: bool
    default_temperature: float
    default_max_tokens: int
    cost_per_input_token: Optional[Decimal]
    cost_per_output_token: Optional[Decimal]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ModelCostEstimateRequest(BaseModel):
    """Cost estimation request schema."""
    model: str
    prompt_tokens: int = Field(..., gt=0)
    completion_tokens: int = Field(..., gt=0)


class ModelCostEstimateResponse(BaseModel):
    """Cost estimation response schema."""
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: Optional[Decimal]
    currency: str = "USD"
