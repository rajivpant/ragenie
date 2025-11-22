"""Chat API endpoints with LangGraph RAG workflow."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel
import json

from app.db.database import get_db
from app.workflows.rag_workflow import RAGWorkflow
from app.schemas.conversations import MessageResponse
from shared.models import Conversation, Message, MessageRole, Profile

router = APIRouter()


# TODO: Replace with actual auth dependency
async def get_current_user_id() -> int:
    """Get current user ID from JWT token."""
    return 1


class ChatRequest(BaseModel):
    """Request for chat endpoint."""
    query: str
    stream: bool = False


class ChatResponse(BaseModel):
    """Response from chat endpoint."""
    conversation_id: int
    response: str
    retrieved_documents: list[dict]
    total_tokens: Optional[int]
    cost: Optional[float]
    model_used: Optional[str]
    retrieval_time_ms: float
    generation_time_ms: float


@router.post("/conversations/{conversation_id}/chat", response_model=ChatResponse)
async def chat(
    conversation_id: int,
    request: ChatRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate a response using LangGraph RAG workflow.

    This endpoint:
    1. Verifies conversation ownership
    2. Gets profile and custom instructions
    3. Retrieves conversation history
    4. Runs LangGraph workflow:
       - Retrieves relevant documents
       - Augments prompt with context
       - Generates LLM response
    5. Saves user message and assistant response
    6. Returns complete response with metadata
    """
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

    # Get conversation history (last 10 messages)
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(10)
    )
    messages = messages_result.scalars().all()

    # Convert to dict format
    conversation_history = [
        {
            "role": msg.role.value,
            "content": msg.content
        }
        for msg in messages
    ]

    # Run LangGraph workflow
    workflow = RAGWorkflow()
    final_state = await workflow.run(
        query=request.query,
        conversation_id=conversation_id,
        profile_id=conversation.profile_id,
        custom_instructions=custom_instructions,
        conversation_history=conversation_history
    )

    # Save user message
    user_message = Message(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=request.query
    )
    db.add(user_message)

    # Save assistant message
    assistant_message = Message(
        conversation_id=conversation_id,
        role=MessageRole.ASSISTANT,
        content=final_state["response"],
        token_count=final_state.get("total_tokens"),
        model_used=final_state.get("model_used")
    )
    db.add(assistant_message)

    # Update conversation timestamp and state
    conversation.updated_at = func.now()
    if final_state.get("system_prompt"):
        # Store last state for debugging
        conversation.state = {
            "last_retrieval_time_ms": final_state["retrieval_time_ms"],
            "last_generation_time_ms": final_state["generation_time_ms"],
            "last_documents_count": len(final_state.get("retrieved_documents", []))
        }

    await db.commit()
    await db.refresh(user_message)
    await db.refresh(assistant_message)

    return ChatResponse(
        conversation_id=conversation_id,
        response=final_state["response"],
        retrieved_documents=final_state.get("retrieved_documents", []),
        total_tokens=final_state.get("total_tokens"),
        cost=final_state.get("cost"),
        model_used=final_state.get("model_used"),
        retrieval_time_ms=final_state["retrieval_time_ms"],
        generation_time_ms=final_state["generation_time_ms"]
    )


@router.post("/conversations/{conversation_id}/chat/stream")
async def chat_stream(
    conversation_id: int,
    request: ChatRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Stream chat response using LangGraph RAG workflow.

    This endpoint streams the workflow execution as Server-Sent Events (SSE):
    - event: retrieve - Document retrieval complete
    - event: augment - Prompt augmentation complete
    - event: generate - LLM generation complete
    - event: done - Workflow complete
    """
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

    # Get conversation history
    messages_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .limit(10)
    )
    messages = messages_result.scalars().all()

    conversation_history = [
        {
            "role": msg.role.value,
            "content": msg.content
        }
        for msg in messages
    ]

    async def event_generator():
        """Generate Server-Sent Events."""
        workflow = RAGWorkflow()
        final_response = None

        try:
            # Stream workflow execution
            async for event in workflow.stream(
                query=request.query,
                conversation_id=conversation_id,
                profile_id=conversation.profile_id,
                custom_instructions=custom_instructions,
                conversation_history=conversation_history
            ):
                node_name = event["node"]
                state = event["state"]

                # Send event based on node
                event_data = {
                    "node": node_name,
                    "data": {}
                }

                if node_name == "retrieve":
                    event_data["data"] = {
                        "documents_count": len(state.get("retrieved_documents", [])),
                        "retrieval_time_ms": state.get("retrieval_time_ms", 0)
                    }
                elif node_name == "augment":
                    event_data["data"] = {
                        "prompt_length": len(state.get("system_prompt", ""))
                    }
                elif node_name == "generate":
                    event_data["data"] = {
                        "response": state.get("response", ""),
                        "total_tokens": state.get("total_tokens"),
                        "generation_time_ms": state.get("generation_time_ms", 0)
                    }
                    final_response = state

                yield f"event: {node_name}\n"
                yield f"data: {json.dumps(event_data)}\n\n"

            # Save messages after workflow completes
            if final_response:
                user_message = Message(
                    conversation_id=conversation_id,
                    role=MessageRole.USER,
                    content=request.query
                )
                db.add(user_message)

                assistant_message = Message(
                    conversation_id=conversation_id,
                    role=MessageRole.ASSISTANT,
                    content=final_response["response"],
                    token_count=final_response.get("total_tokens"),
                    model_used=final_response.get("model_used")
                )
                db.add(assistant_message)

                conversation.updated_at = func.now()
                await db.commit()

            # Send done event
            yield f"event: done\n"
            yield f"data: {json.dumps({'status': 'completed'})}\n\n"

        except Exception as e:
            # Send error event
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
