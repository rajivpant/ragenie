"""RAG retrieval service for semantic search."""
import httpx
from typing import List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.core.config import settings
from app.schemas.conversations import RetrievedDocument


class RAGRetrievalService:
    """Service for retrieving relevant documents using RAG."""

    def __init__(self):
        self.qdrant = QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        self.collection_name = settings.QDRANT_COLLECTION

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a text query.

        This uses the document service's embedding endpoint (which has OpenAI integration).
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.DOCUMENT_SERVICE_URL}/ragbot/embed/generate",
                json={"text": text},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]

    async def retrieve_documents(
        self,
        query: str,
        top_k: Optional[int] = None,
        similarity_threshold: Optional[float] = None,
        category_filter: Optional[str] = None,
        source_filter: Optional[str] = "ragbot-data"
    ) -> List[RetrievedDocument]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: The search query
            top_k: Number of documents to retrieve (default from settings)
            similarity_threshold: Minimum similarity score (default from settings)
            category_filter: Filter by document category
            source_filter: Filter by source (default: ragbot-data)

        Returns:
            List of retrieved documents with similarity scores
        """
        if top_k is None:
            top_k = settings.RAG_TOP_K
        if similarity_threshold is None:
            similarity_threshold = settings.RAG_SIMILARITY_THRESHOLD

        try:
            # Generate query embedding
            query_vector = await self.generate_embedding(query)

            # Build search filter
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="source",
                        match=MatchValue(value=source_filter)
                    )
                ]
            )
            if category_filter:
                search_filter.must.append(
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=category_filter)
                    )
                )

            # Search Qdrant
            results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=top_k,
                score_threshold=similarity_threshold
            )

            return [
                RetrievedDocument(
                    file_path=hit.payload["file_path"],
                    chunk_index=hit.payload["chunk_index"],
                    chunk_text=hit.payload["chunk_text"],
                    similarity_score=hit.score,
                    source=hit.payload["source"],
                    category=hit.payload.get("category"),
                    tags=hit.payload.get("tags")
                )
                for hit in results
            ]

        except Exception as e:
            # Log error and return empty list
            print(f"Error retrieving documents: {e}")
            return []

    async def retrieve_with_metadata(
        self,
        query: str,
        top_k: Optional[int] = None,
        include_custom_instructions: bool = True,
        include_curated_datasets: bool = True
    ) -> dict:
        """
        Retrieve documents with additional metadata filtering.

        This is a higher-level method that can filter by document type
        (custom instructions, curated datasets, etc.).

        Args:
            query: The search query
            top_k: Number of documents to retrieve
            include_custom_instructions: Whether to include custom-instructions docs
            include_curated_datasets: Whether to include curated-datasets docs

        Returns:
            Dictionary with categorized results
        """
        results = {
            "custom_instructions": [],
            "curated_datasets": [],
            "other": []
        }

        # Retrieve all relevant documents
        all_docs = await self.retrieve_documents(query, top_k)

        # Categorize by file path
        for doc in all_docs:
            if "custom-instructions" in doc.file_path and include_custom_instructions:
                results["custom_instructions"].append(doc)
            elif "curated-datasets" in doc.file_path and include_curated_datasets:
                results["curated_datasets"].append(doc)
            else:
                results["other"].append(doc)

        return results
