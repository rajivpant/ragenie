"""Conversation management API endpoints."""
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.db.database import get_db
from app.core.config import settings
from app.services.rag_retrieval import RAGRetrievalService
from app.schemas.conversations import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationList,
    MessageCreate,
    MessageResponse,
    MessageList,
    RAGContextResponse,
    RetrievedDocument,
)
from shared.models import Conversation, Message, MessageRole, Profile

router = APIRouter()


# TODO: Replace with actual auth dependency
async def get_current_user_id() -> int:
    """Get current user ID from JWT token."""
    # Placeholder - will be replaced with actual auth integration
    return 1


@router.get("", response_model=ConversationList)
async def list_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """List all conversations for the current user."""
    # Get total count
    count_result = await db.execute(
        select(func.count(Conversation.id))
        .where(Conversation.user_id == current_user_id)
    )
    total = count_result.scalar_one()

    # Get conversations
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == current_user_id)
        .order_by(desc(Conversation.updated_at))
        .offset(skip)
        .limit(limit)
    )
    conversations = result.scalars().all()

    return ConversationList(
        total=total,
        conversations=[ConversationResponse.model_validate(conv) for conv in conversations]
    )


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new conversation."""
    # Validate profile_id if provided
    if conversation_data.profile_id:
        profile_result = await db.execute(
            select(Profile)
            .where(Profile.id == conversation_data.profile_id)
            .where(Profile.user_id == current_user_id)
        )
        if not profile_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

    # Create conversation
    conversation = Conversation(
        user_id=current_user_id,
        title=conversation_data.title,
        profile_id=conversation_data.profile_id
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return ConversationResponse.model_validate(conversation)


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific conversation."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == current_user_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    return ConversationResponse.model_validate(conversation)


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    update_data: ConversationUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update a conversation."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == current_user_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(conversation, field, value)

    await db.commit()
    await db.refresh(conversation)

    return ConversationResponse.model_validate(conversation)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation."""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == current_user_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    await db.delete(conversation)
    await db.commit()


@router.get("/{conversation_id}/messages", response_model=MessageList)
async def get_conversation_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get all messages in a conversation."""
    # Verify conversation ownership
    conv_result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == current_user_id)
    )
    if not conv_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Get total count
    count_result = await db.execute(
        select(func.count(Message.id))
        .where(Message.conversation_id == conversation_id)
    )
    total = count_result.scalar_one()

    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .offset(skip)
        .limit(limit)
    )
    messages = result.scalars().all()

    return MessageList(
        total=total,
        messages=[MessageResponse.model_validate(msg) for msg in messages]
    )


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def add_message(
    conversation_id: int,
    message_data: MessageCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Add a message to a conversation."""
    # Verify conversation ownership
    conv_result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == current_user_id)
    )
    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Create message
    message = Message(
        conversation_id=conversation_id,
        role=MessageRole(message_data.role),
        content=message_data.content
    )
    db.add(message)

    # Update conversation timestamp
    conversation.updated_at = func.now()

    await db.commit()
    await db.refresh(message)

    return MessageResponse.model_validate(message)


@router.get("/{conversation_id}/context", response_model=RAGContextResponse)
async def get_rag_context(
    conversation_id: int,
    query: str,
    top_k: Optional[int] = None,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Assemble RAG context for a conversation.

    This endpoint:
    1. Retrieves custom instructions from the user's profile
    2. Performs vector search in Qdrant for relevant documents
    3. Gets recent conversation history
    4. Assembles everything into a context ready for the LLM
    """
    start_time = time.time()

    # Verify conversation ownership
    conv_result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == current_user_id)
    )
    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    # Get profile and custom instructions
    custom_instructions = None
    if conversation.profile_id:
        profile_result = await db.execute(
            select(Profile)
            .where(Profile.id == conversation.profile_id)
        )
        profile = profile_result.scalar_one_or_none()
        if profile and profile.settings:
            custom_instructions = profile.settings.get("custom_instructions")

    # Get recent conversation history (last 10 messages)
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(desc(Message.created_at))
        .limit(10)
    )
    messages = list(reversed(messages_result.scalars().all()))

    # Perform vector search in Qdrant using RAGRetrievalService
    retrieved_documents = []
    try:
        rag_service = RAGRetrievalService()
        retrieved_documents = await rag_service.retrieve_documents(
            query=query,
            top_k=top_k or settings.RAG_TOP_K,
            source_filter="ragbot-data"
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error retrieving documents: {e}")

    # Assemble system prompt
    system_prompt_parts = []

    if custom_instructions:
        system_prompt_parts.append("# Custom Instructions")
        system_prompt_parts.append(custom_instructions)
        system_prompt_parts.append("")

    if retrieved_documents:
        system_prompt_parts.append("# Relevant Context from Knowledge Base")
        for i, doc in enumerate(retrieved_documents, 1):
            system_prompt_parts.append(f"## Document {i}: {doc.file_path}")
            system_prompt_parts.append(doc.chunk_text)
            system_prompt_parts.append("")

    system_prompt = "\n".join(system_prompt_parts) if system_prompt_parts else "You are a helpful AI assistant."

    retrieval_time_ms = (time.time() - start_time) * 1000

    return RAGContextResponse(
        conversation_id=conversation_id,
        profile_id=conversation.profile_id,
        custom_instructions=custom_instructions,
        retrieved_documents=retrieved_documents,
        conversation_history=[MessageResponse.model_validate(msg) for msg in messages],
        system_prompt=system_prompt,
        user_query=query,
        total_retrieved=len(retrieved_documents),
        retrieval_time_ms=retrieval_time_ms
    )
