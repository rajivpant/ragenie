"""ragbot-data documents API endpoints."""
from typing import Optional
from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from datetime import datetime
from langchain_openai import OpenAIEmbeddings
import os

from app.db.database import get_db
from app.core.config import settings
from app.schemas.documents import (
    RagbotDocumentResponse,
    RagbotDocumentList,
    EmbeddingStatusResponse,
    EmbedTriggerRequest,
    EmbedTriggerResponse,
    EmbeddingGenerateRequest,
    EmbeddingGenerateResponse
)

router = APIRouter()


@router.get("", response_model=RagbotDocumentList)
async def list_ragbot_documents(
    status_filter: Optional[str] = Query(None, description="Filter by embedding_status"),
    category: Optional[str] = Query(None, description="Filter by category in metadata"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List all ragbot-data documents with optional filtering."""
    # Build query
    query = select(text("*")).select_from(text("ragbot_documents"))
    count_query = select(func.count()).select_from(text("ragbot_documents"))

    conditions = []
    if status_filter:
        conditions.append(f"embedding_status = '{status_filter}'")
    if category:
        conditions.append(f"metadata->>'category' = '{category}'")

    if conditions:
        where_clause = " AND ".join(conditions)
        query = text(f"SELECT * FROM ragbot_documents WHERE {where_clause} ORDER BY updated_at DESC LIMIT {limit} OFFSET {skip}")
        count_query = text(f"SELECT COUNT(*) FROM ragbot_documents WHERE {where_clause}")
    else:
        query = text(f"SELECT * FROM ragbot_documents ORDER BY updated_at DESC LIMIT {limit} OFFSET {skip}")

    # Execute queries
    result = await db.execute(query)
    documents = result.fetchall()

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Convert to dict format
    docs_list = []
    for row in documents:
        doc_dict = dict(row._mapping)
        docs_list.append(RagbotDocumentResponse(**doc_dict))

    return RagbotDocumentList(total=total or 0, documents=docs_list)


@router.get("/status", response_model=EmbeddingStatusResponse)
async def get_embedding_status(
    db: AsyncSession = Depends(get_db)
):
    """Get embedding status summary."""
    # Get counts by status
    status_query = text("""
        SELECT
            embedding_status,
            COUNT(*) as count,
            MAX(updated_at) as last_update
        FROM ragbot_documents
        GROUP BY embedding_status
    """)

    result = await db.execute(status_query)
    status_counts = result.fetchall()

    # Get queue size
    queue_query = text("""
        SELECT COUNT(*)
        FROM embedding_queue
        WHERE status IN ('pending', 'processing')
    """)
    queue_result = await db.execute(queue_query)
    queue_size = queue_result.scalar() or 0

    # Build response
    status_dict = {row.embedding_status: row.count for row in status_counts}
    last_updates = [row.last_update for row in status_counts if row.last_update]

    return EmbeddingStatusResponse(
        total_files=sum(status_dict.values()),
        indexed=status_dict.get('indexed', 0),
        pending=status_dict.get('pending', 0),
        failed=status_dict.get('failed', 0),
        deleted=status_dict.get('deleted', 0),
        last_update=max(last_updates) if last_updates else None,
        queue_size=queue_size
    )


@router.get("/{path:path}", response_model=RagbotDocumentResponse)
async def get_ragbot_document(
    path: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific ragbot-data document by file path."""
    query = text("SELECT * FROM ragbot_documents WHERE file_path = :path")
    result = await db.execute(query, {"path": path})
    doc = result.fetchone()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {path}"
        )

    return RagbotDocumentResponse(**dict(doc._mapping))


@router.get("/{path:path}/content")
async def get_ragbot_document_content(
    path: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the actual file content of a ragbot-data document."""
    # First verify document exists in database
    query = text("SELECT file_path FROM ragbot_documents WHERE file_path = :path")
    result = await db.execute(query, {"path": path})
    doc = result.fetchone()

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {path}"
        )

    # Read file from ragbot-data
    full_path = settings.RAGBOT_DATA_PATH / path
    if not full_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found on filesystem: {path}"
        )

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return {
            "file_path": path,
            "content": content,
            "size_bytes": full_path.stat().st_size
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading file: {str(e)}"
        )


@router.post("/embed/trigger", response_model=EmbedTriggerResponse)
async def trigger_reembedding(
    request: EmbedTriggerRequest,
    db: AsyncSession = Depends(get_db)
):
    """Manually trigger re-embedding of documents."""
    if request.file_path:
        # Re-embed specific file
        query = text("""
            UPDATE ragbot_documents
            SET embedding_status = 'pending',
                chunk_count = 0,
                indexed_at = NULL,
                error_message = NULL,
                updated_at = NOW()
            WHERE file_path = :path
            RETURNING id
        """)
        result = await db.execute(query, {"path": request.file_path})
        doc = result.fetchone()

        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document not found: {request.file_path}"
            )

        # Queue for embedding
        insert_query = text("""
            INSERT INTO embedding_queue (document_type, document_id, priority, status)
            VALUES ('ragbot', :doc_id, 10, 'pending')
        """)
        await db.execute(insert_query, {"doc_id": doc.id})
        await db.commit()

        return EmbedTriggerResponse(
            message=f"Re-embedding queued for {request.file_path}",
            files_queued=1
        )
    else:
        # Re-embed all files
        update_query = text("""
            UPDATE ragbot_documents
            SET embedding_status = 'pending',
                chunk_count = 0,
                indexed_at = NULL,
                error_message = NULL,
                updated_at = NOW()
            WHERE embedding_status != 'deleted'
            RETURNING id
        """)
        result = await db.execute(update_query)
        doc_ids = [row.id for row in result.fetchall()]

        # Queue all for embedding
        for doc_id in doc_ids:
            insert_query = text("""
                INSERT INTO embedding_queue (document_type, document_id, priority, status)
                VALUES ('ragbot', :doc_id, 5, 'pending')
            """)
            await db.execute(insert_query, {"doc_id": doc_id})

        await db.commit()

        return EmbedTriggerResponse(
            message="All documents queued for re-embedding",
            files_queued=len(doc_ids)
        )


@router.post("/embed/generate", response_model=EmbeddingGenerateResponse)
async def generate_embedding(
    request: EmbeddingGenerateRequest
):
    """
    Generate embedding for a text query.

    This endpoint is used by other services (like conversation-service)
    to generate embeddings for search queries.
    """
    try:
        # Initialize OpenAI embeddings
        embeddings = OpenAIEmbeddings(
            model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )

        # Generate embedding
        embedding_vector = await embeddings.aembed_query(request.text)

        return EmbeddingGenerateResponse(
            embedding=embedding_vector,
            model=embeddings.model,
            dimensions=len(embedding_vector)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating embedding: {str(e)}"
        )
