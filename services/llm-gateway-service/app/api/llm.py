"""LLM Gateway API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import sys
import os

sys.path.append("/app/../../..")

from app.db import get_db
from app.schemas import (
    ChatRequest,
    ChatResponse,
    TokenCountRequest,
    TokenCountResponse,
    LLMProviderResponse,
    LLMModelResponse,
    ModelCostEstimateRequest,
    ModelCostEstimateResponse,
)
from app.utils import llm_client, count_tokens, count_messages_tokens
from shared.models import LLMProvider, LLMModel

router = APIRouter(prefix="/llm", tags=["llm"])


@router.post("/chat", response_model=ChatResponse)
async def chat_completion(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Send a chat completion request to an LLM provider.

    This endpoint provides direct access to LLM providers via LiteLLM.
    """
    try:
        # Convert message inputs to dict format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Call LLM
        response = await llm_client.chat_completion(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream
        )

        if request.stream:
            # TODO: Handle streaming responses
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Streaming not yet implemented"
            )

        # Calculate cost
        usage = response["usage"]
        cost = llm_client.calculate_cost(
            model=request.model,
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"]
        )

        return ChatResponse(
            content=response["content"],
            model=response["model"],
            usage=usage,
            finish_reason=response["finish_reason"],
            cost=cost
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM request failed: {str(e)}"
        )


@router.post("/count-tokens", response_model=TokenCountResponse)
async def count_tokens_endpoint(request: TokenCountRequest):
    """
    Count tokens in text or messages.

    Useful for estimating costs and checking context limits before sending requests.
    """
    try:
        if request.text:
            token_count = count_tokens(request.text)
        elif request.messages:
            messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
            token_count = count_messages_tokens(messages, request.model)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'text' or 'messages' must be provided"
            )

        return TokenCountResponse(
            token_count=token_count,
            model=request.model
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token counting failed: {str(e)}"
        )


@router.post("/estimate-cost", response_model=ModelCostEstimateResponse)
async def estimate_cost(request: ModelCostEstimateRequest):
    """
    Estimate the cost of an LLM request.

    Provides cost estimates based on token counts and model pricing.
    """
    try:
        cost = llm_client.calculate_cost(
            model=request.model,
            prompt_tokens=request.prompt_tokens,
            completion_tokens=request.completion_tokens
        )

        return ModelCostEstimateResponse(
            model=request.model,
            prompt_tokens=request.prompt_tokens,
            completion_tokens=request.completion_tokens,
            total_tokens=request.prompt_tokens + request.completion_tokens,
            estimated_cost=cost
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cost estimation failed: {str(e)}"
        )


@router.get("/providers", response_model=List[LLMProviderResponse])
async def list_providers(
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """
    List all LLM providers.

    Returns a list of configured LLM providers (OpenAI, Anthropic, Google, etc.)
    """
    query = db.query(LLMProvider)

    if not include_inactive:
        query = query.filter(LLMProvider.is_active == True)

    providers = query.order_by(LLMProvider.name).all()
    return providers


@router.get("/providers/{provider_id}", response_model=LLMProviderResponse)
async def get_provider(provider_id: int, db: Session = Depends(get_db)):
    """Get a specific LLM provider by ID."""
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()

    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider not found"
        )

    return provider


@router.get("/models", response_model=List[LLMModelResponse])
async def list_models(
    provider_id: Optional[int] = None,
    category: Optional[str] = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """
    List all available LLM models.

    Filter by provider, category, or active status.
    """
    query = db.query(LLMModel)

    if provider_id:
        query = query.filter(LLMModel.provider_id == provider_id)

    if category:
        query = query.filter(LLMModel.category == category)

    if not include_inactive:
        query = query.filter(LLMModel.is_active == True)

    models = query.order_by(LLMModel.category, LLMModel.name).all()
    return models


@router.get("/models/{model_id}", response_model=LLMModelResponse)
async def get_model(model_id: int, db: Session = Depends(get_db)):
    """Get a specific LLM model by ID."""
    model = db.query(LLMModel).filter(LLMModel.id == model_id).first()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found"
        )

    return model


@router.get("/models/by-name/{model_name}", response_model=LLMModelResponse)
async def get_model_by_name(model_name: str, db: Session = Depends(get_db)):
    """Get a specific LLM model by name."""
    model = db.query(LLMModel).filter(LLMModel.name == model_name).first()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_name}' not found"
        )

    return model
