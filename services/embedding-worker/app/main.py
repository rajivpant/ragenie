"""Main embedding worker service."""
import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import UUID

import asyncpg
import redis.asyncio as redis
import structlog
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue

from app.config import settings

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer()
    ]
)
logger = structlog.get_logger()


class EmbeddingWorker:
    """Worker for processing embedding queue."""

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        redis_client: redis.Redis,
        qdrant_client: AsyncQdrantClient,
        embeddings: OpenAIEmbeddings,
        text_splitter: RecursiveCharacterTextSplitter
    ):
        """Initialize the embedding worker."""
        self.db_pool = db_pool
        self.redis_client = redis_client
        self.qdrant_client = qdrant_client
        self.embeddings = embeddings
        self.text_splitter = text_splitter
        logger.info("EmbeddingWorker initialized")

    async def process_queue(self) -> None:
        """Main queue processing loop."""
        logger.info("queue_processing_started", batch_size=settings.BATCH_SIZE)

        while True:
            try:
                # Fetch pending jobs from queue (ordered by priority DESC)
                async with self.db_pool.acquire() as conn:
                    jobs = await conn.fetch("""
                        SELECT id, document_type, document_id, retry_count, max_retries
                        FROM embedding_queue
                        WHERE status = 'pending'
                        AND retry_count < max_retries
                        ORDER BY priority DESC, created_at ASC
                        LIMIT $1
                    """, settings.BATCH_SIZE)

                if not jobs:
                    logger.debug("queue_empty", waiting=f"{settings.POLL_INTERVAL}s")
                    await asyncio.sleep(settings.POLL_INTERVAL)
                    continue

                logger.info("jobs_fetched", count=len(jobs))

                # Process jobs concurrently
                tasks = [self._process_job(job) for job in jobs]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Log results
                success_count = sum(1 for r in results if r is True)
                error_count = sum(1 for r in results if isinstance(r, Exception))
                logger.info(
                    "batch_processed",
                    total=len(jobs),
                    success=success_count,
                    errors=error_count
                )

            except Exception as e:
                logger.error("queue_processing_error", error=str(e), exc_info=True)
                await asyncio.sleep(settings.POLL_INTERVAL)

    async def _process_job(self, job: asyncpg.Record) -> bool:
        """Process a single embedding job."""
        job_id = job['id']
        document_type = job['document_type']
        document_id = job['document_id']

        logger.info(
            "job_processing",
            job_id=job_id,
            document_type=document_type,
            document_id=str(document_id),
            retry_count=job['retry_count']
        )

        try:
            # Mark as processing
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE embedding_queue
                    SET status = 'processing', started_at = NOW()
                    WHERE id = $1
                """, job_id)

            # Route to appropriate handler
            if document_type == 'ragbot':
                await self._process_ragbot_document(document_id)
            elif document_type == 'user_upload':
                await self._process_user_upload(document_id)
            else:
                raise ValueError(f"Unknown document type: {document_type}")

            # Mark as completed
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE embedding_queue
                    SET status = 'completed', completed_at = NOW()
                    WHERE id = $1
                """, job_id)

            logger.info("job_completed", job_id=job_id, document_id=str(document_id))
            return True

        except Exception as e:
            logger.error(
                "job_failed",
                job_id=job_id,
                document_id=str(document_id),
                error=str(e),
                exc_info=True
            )

            # Update job with error
            async with self.db_pool.acquire() as conn:
                retry_count = job['retry_count'] + 1
                max_retries = job['max_retries']

                if retry_count >= max_retries:
                    # Max retries reached - mark as failed
                    await conn.execute("""
                        UPDATE embedding_queue
                        SET status = 'failed',
                            retry_count = $1,
                            error_message = $2,
                            completed_at = NOW()
                        WHERE id = $3
                    """, retry_count, str(e)[:500], job_id)
                    logger.error("job_failed_permanently", job_id=job_id, retries=retry_count)
                else:
                    # Retry - mark as pending
                    await conn.execute("""
                        UPDATE embedding_queue
                        SET status = 'pending',
                            retry_count = $1,
                            error_message = $2
                        WHERE id = $3
                    """, retry_count, str(e)[:500], job_id)
                    logger.warning("job_retry_scheduled", job_id=job_id, retry=retry_count)

            raise

    async def _process_ragbot_document(self, document_id: UUID) -> None:
        """Process a ragbot-data document."""
        logger.info("processing_ragbot_document", document_id=str(document_id))

        # Fetch document metadata
        async with self.db_pool.acquire() as conn:
            doc = await conn.fetchrow("""
                SELECT id, file_path, content_hash
                FROM ragbot_documents
                WHERE id = $1
            """, document_id)

        if not doc:
            raise ValueError(f"Document not found: {document_id}")

        file_path = doc['file_path']
        content_hash = doc['content_hash']

        # Read file content
        full_path = settings.RAGBOT_DATA_PATH / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")

        logger.debug("reading_file", path=file_path, size=full_path.stat().st_size)

        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract metadata from file path
        metadata = self._extract_metadata_from_path(file_path)

        # Delete old embeddings for this document
        await self._delete_old_embeddings(file_path, 'ragbot')

        # Chunk the document
        chunks = self.text_splitter.split_text(content)
        logger.info("document_chunked", path=file_path, chunk_count=len(chunks))

        if not chunks:
            logger.warning("no_chunks_generated", path=file_path)
            # Mark as indexed with 0 chunks
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE ragbot_documents
                    SET embedding_status = 'indexed',
                        chunk_count = 0,
                        indexed_at = NOW(),
                        error_message = 'Empty document',
                        updated_at = NOW()
                    WHERE id = $1
                """, document_id)
            return

        # Generate embeddings (batch for efficiency)
        logger.debug("generating_embeddings", chunk_count=len(chunks))
        vectors = await self.embeddings.aembed_documents(chunks)

        # Prepare Qdrant points
        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
            point = PointStruct(
                id=f"{document_id}:{i}",
                vector=vector,
                payload={
                    "file_path": file_path,
                    "chunk_index": i,
                    "chunk_text": chunk,
                    "content_hash": content_hash,
                    "source": "ragbot-data",
                    "document_id": str(document_id),
                    "category": metadata.get("category", "unknown"),
                    "tags": metadata.get("tags", []),
                    "indexed_at": datetime.now().isoformat()
                }
            )
            points.append(point)

        # Upload to Qdrant
        logger.debug("uploading_to_qdrant", point_count=len(points))
        await self.qdrant_client.upsert(
            collection_name=settings.QDRANT_COLLECTION,
            points=points
        )

        # Update database metadata
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE ragbot_documents
                SET embedding_status = 'indexed',
                    chunk_count = $1,
                    indexed_at = NOW(),
                    error_message = NULL,
                    metadata = $2,
                    updated_at = NOW()
                WHERE id = $3
            """, len(chunks), metadata, document_id)

        # Cache document content in Redis
        cache_key = f"doc:{file_path}"
        await self.redis_client.setex(cache_key, settings.CACHE_TTL, content)

        logger.info(
            "ragbot_document_indexed",
            path=file_path,
            chunks=len(chunks),
            vectors=len(vectors)
        )

    async def _process_user_upload(self, document_id: UUID) -> None:
        """Process a user-uploaded document."""
        logger.info("processing_user_upload", document_id=str(document_id))

        # Fetch document metadata
        async with self.db_pool.acquire() as conn:
            doc = await conn.fetchrow("""
                SELECT id, filename, file_path, content_hash, user_id
                FROM user_uploads
                WHERE id = $1
            """, document_id)

        if not doc:
            raise ValueError(f"User upload not found: {document_id}")

        # TODO: Implement MinIO file retrieval
        # For now, user uploads will be handled in a future iteration
        logger.warning("user_upload_not_implemented_yet", document_id=str(document_id))

        # Mark as indexed (placeholder)
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE user_uploads
                SET embedding_status = 'pending',
                    error_message = 'User uploads not yet implemented',
                    updated_at = NOW()
                WHERE id = $1
            """, document_id)

    async def _delete_old_embeddings(self, file_path: str, source: str) -> None:
        """Delete old embeddings for a document from Qdrant."""
        try:
            # Use scroll to find all points for this file
            scroll_result = await self.qdrant_client.scroll(
                collection_name=settings.QDRANT_COLLECTION,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="file_path",
                            match=MatchValue(value=file_path)
                        ),
                        FieldCondition(
                            key="source",
                            match=MatchValue(value=source)
                        )
                    ]
                ),
                limit=1000
            )

            points_to_delete = [point.id for point in scroll_result[0]]

            if points_to_delete:
                await self.qdrant_client.delete(
                    collection_name=settings.QDRANT_COLLECTION,
                    points_selector=points_to_delete
                )
                logger.debug(
                    "old_embeddings_deleted",
                    file_path=file_path,
                    count=len(points_to_delete)
                )
        except Exception as e:
            logger.warning("delete_old_embeddings_failed", file_path=file_path, error=str(e))

    def _extract_metadata_from_path(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from file path structure."""
        parts = Path(file_path).parts
        metadata = {
            "file_path": file_path,
            "category": "unknown",
            "tags": []
        }

        # Extract category from path structure
        if len(parts) > 1:
            if parts[0] == "curated-datasets":
                metadata["category"] = parts[1] if len(parts) > 1 else "general"
                metadata["tags"].append("curated-dataset")
            elif parts[0] == "custom-instructions":
                metadata["category"] = "custom-instructions"
                metadata["tags"].append("custom-instruction")
            elif parts[0] == "prompt-library":
                metadata["category"] = parts[1] if len(parts) > 1 else "prompts"
                metadata["tags"].append("prompt-library")

        return metadata


async def initialize_qdrant(client: AsyncQdrantClient) -> None:
    """Initialize Qdrant collection if it doesn't exist."""
    logger.info("initializing_qdrant", collection=settings.QDRANT_COLLECTION)

    try:
        # Check if collection exists
        collections = await client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if settings.QDRANT_COLLECTION not in collection_names:
            # Create collection
            await client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(
                    size=settings.EMBEDDING_DIMENSIONS,
                    distance=Distance.COSINE,
                )
            )
            logger.info("qdrant_collection_created", collection=settings.QDRANT_COLLECTION)
        else:
            logger.info("qdrant_collection_exists", collection=settings.QDRANT_COLLECTION)

    except Exception as e:
        logger.error("qdrant_initialization_failed", error=str(e), exc_info=True)
        raise


async def main() -> None:
    """Main entry point for embedding worker service."""
    logger.info(
        "embedding_worker_starting",
        model=settings.EMBEDDING_MODEL,
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )

    # Verify OpenAI API key
    if not settings.OPENAI_API_KEY:
        logger.error("openai_api_key_not_set")
        sys.exit(1)

    # Create database connection pool
    try:
        db_pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=2,
            max_size=10
        )
        logger.info("database_connected")
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        sys.exit(1)

    # Create Redis client
    try:
        redis_client = await redis.from_url(settings.REDIS_URL)
        await redis_client.ping()
        logger.info("redis_connected")
    except Exception as e:
        logger.error("redis_connection_failed", error=str(e))
        sys.exit(1)

    # Create Qdrant client
    try:
        qdrant_client = AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        # Initialize collection
        await initialize_qdrant(qdrant_client)
        logger.info("qdrant_connected")
    except Exception as e:
        logger.error("qdrant_connection_failed", error=str(e))
        sys.exit(1)

    # Create embeddings instance
    embeddings = OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        openai_api_key=settings.OPENAI_API_KEY
    )

    # Create text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len
    )

    # Create worker
    worker = EmbeddingWorker(
        db_pool=db_pool,
        redis_client=redis_client,
        qdrant_client=qdrant_client,
        embeddings=embeddings,
        text_splitter=text_splitter
    )

    logger.info("embedding_worker_ready", batch_size=settings.BATCH_SIZE)

    try:
        # Start processing queue
        await worker.process_queue()
    except KeyboardInterrupt:
        logger.info("embedding_worker_stopping")
    finally:
        await db_pool.close()
        await redis_client.close()
        await qdrant_client.close()
        logger.info("embedding_worker_stopped")


if __name__ == "__main__":
    asyncio.run(main())
