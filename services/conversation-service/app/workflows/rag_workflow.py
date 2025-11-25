"""LangGraph workflow for RAG-powered conversations."""
from typing import TypedDict, Annotated, List, Optional, AsyncIterator
from typing_extensions import TypedDict
import httpx
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.config import settings
from app.services.rag_retrieval import RAGRetrievalService
from app.schemas.conversations import RetrievedDocument


class RAGState(TypedDict):
    """State for RAG workflow."""
    # Input
    query: str
    conversation_id: int
    profile_id: Optional[int]
    conversation_history: List[dict]

    # Intermediate state
    custom_instructions: Optional[str]
    retrieved_documents: List[dict]
    system_prompt: str

    # LLM Configuration (from profile settings or defaults)
    model: str
    temperature: float
    max_tokens: int

    # Output
    response: str
    total_tokens: Optional[int]
    cost: Optional[float]
    model_used: Optional[str]

    # Metadata
    retrieval_time_ms: float
    generation_time_ms: float


class RAGWorkflow:
    """LangGraph workflow for RAG-powered question answering."""

    def __init__(self):
        self.rag_service = RAGRetrievalService()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Create state graph
        workflow = StateGraph(RAGState)

        # Add nodes
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("augment", self._augment_node)
        workflow.add_node("generate", self._generate_node)

        # Add edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "augment")
        workflow.add_edge("augment", "generate")
        workflow.add_edge("generate", END)

        # Compile with checkpointer for state persistence
        checkpointer = MemorySaver()
        return workflow.compile(checkpointer=checkpointer)

    async def _retrieve_node(self, state: RAGState) -> RAGState:
        """
        Retrieve relevant documents using vector search.

        This node:
        1. Generates query embedding
        2. Searches Qdrant for similar documents
        3. Returns top-k chunks with scores
        """
        import time
        start_time = time.time()

        try:
            # Retrieve documents
            retrieved_documents = await self.rag_service.retrieve_documents(
                query=state["query"],
                top_k=settings.RAG_TOP_K,
                source_filter="ragbot-data"
            )

            # Convert to dict for state
            docs_dict = [
                {
                    "file_path": doc.file_path,
                    "chunk_index": doc.chunk_index,
                    "chunk_text": doc.chunk_text,
                    "similarity_score": doc.similarity_score,
                    "source": doc.source,
                    "category": doc.category,
                    "tags": doc.tags
                }
                for doc in retrieved_documents
            ]

            retrieval_time = (time.time() - start_time) * 1000

            return {
                **state,
                "retrieved_documents": docs_dict,
                "retrieval_time_ms": retrieval_time
            }

        except Exception as e:
            print(f"Error in retrieve node: {e}")
            return {
                **state,
                "retrieved_documents": [],
                "retrieval_time_ms": (time.time() - start_time) * 1000
            }

    async def _augment_node(self, state: RAGState) -> RAGState:
        """
        Augment the query with retrieved context.

        This node:
        1. Takes custom instructions from profile
        2. Formats retrieved documents
        3. Builds complete system prompt
        """
        system_prompt_parts = []

        # Add custom instructions
        if state.get("custom_instructions"):
            system_prompt_parts.append("# Custom Instructions")
            system_prompt_parts.append(state["custom_instructions"])
            system_prompt_parts.append("")

        # Add retrieved context
        if state.get("retrieved_documents"):
            system_prompt_parts.append("# Relevant Context from Knowledge Base")
            system_prompt_parts.append("")

            for i, doc in enumerate(state["retrieved_documents"], 1):
                system_prompt_parts.append(f"## Source {i}: {doc['file_path']}")
                system_prompt_parts.append(f"Relevance Score: {doc['similarity_score']:.2f}")
                system_prompt_parts.append("")
                system_prompt_parts.append(doc['chunk_text'])
                system_prompt_parts.append("")
                system_prompt_parts.append("---")
                system_prompt_parts.append("")

        # Add conversation context
        if state.get("conversation_history"):
            system_prompt_parts.append("# Recent Conversation History")
            system_prompt_parts.append("")

            for msg in state["conversation_history"][-5:]:  # Last 5 messages
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                system_prompt_parts.append(f"**{role.title()}**: {content}")
                system_prompt_parts.append("")

        # Build final prompt
        system_prompt = "\n".join(system_prompt_parts) if system_prompt_parts else \
                       "You are a helpful AI assistant."

        return {
            **state,
            "system_prompt": system_prompt
        }

    async def _generate_node(self, state: RAGState) -> RAGState:
        """
        Generate response using LLM.

        This node:
        1. Calls LLM Gateway Service
        2. Sends system prompt + query
        3. Returns generated response
        """
        import time
        start_time = time.time()

        try:
            # Prepare messages for LLM
            messages = [
                {
                    "role": "system",
                    "content": state["system_prompt"]
                },
                {
                    "role": "user",
                    "content": state["query"]
                }
            ]

            # Call LLM Gateway Service with configured model settings
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{settings.LLM_GATEWAY_URL}/chat/completions",
                    json={
                        "messages": messages,
                        "model": state["model"],
                        "temperature": state["temperature"],
                        "max_tokens": state["max_tokens"]
                    }
                )
                response.raise_for_status()
                data = response.json()

            # Extract response
            assistant_message = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            generation_time = (time.time() - start_time) * 1000

            return {
                **state,
                "response": assistant_message,
                "total_tokens": usage.get("total_tokens"),
                "model_used": data.get("model"),
                "generation_time_ms": generation_time
            }

        except Exception as e:
            print(f"Error in generate node: {e}")
            generation_time = (time.time() - start_time) * 1000

            return {
                **state,
                "response": f"Error generating response: {str(e)}",
                "generation_time_ms": generation_time
            }

    async def run(
        self,
        query: str,
        conversation_id: int,
        profile_id: Optional[int] = None,
        custom_instructions: Optional[str] = None,
        conversation_history: Optional[List[dict]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> RAGState:
        """
        Run the RAG workflow.

        Args:
            query: User's question
            conversation_id: ID of the conversation
            profile_id: Optional profile ID
            custom_instructions: Optional custom instructions from profile
            conversation_history: Optional conversation history
            model: LLM model to use (defaults to settings.DEFAULT_MODEL)
            temperature: Temperature setting (defaults to settings.DEFAULT_TEMPERATURE)
            max_tokens: Max tokens for response (defaults to settings.DEFAULT_MAX_TOKENS)

        Returns:
            Final state with response
        """
        # Initialize state with LLM configuration
        initial_state: RAGState = {
            "query": query,
            "conversation_id": conversation_id,
            "profile_id": profile_id,
            "custom_instructions": custom_instructions,
            "conversation_history": conversation_history or [],
            "retrieved_documents": [],
            "system_prompt": "",
            "model": model or settings.DEFAULT_MODEL,
            "temperature": temperature if temperature is not None else settings.DEFAULT_TEMPERATURE,
            "max_tokens": max_tokens or settings.DEFAULT_MAX_TOKENS,
            "response": "",
            "total_tokens": None,
            "cost": None,
            "model_used": None,
            "retrieval_time_ms": 0.0,
            "generation_time_ms": 0.0
        }

        # Run workflow
        config = {"configurable": {"thread_id": str(conversation_id)}}
        final_state = await self.graph.ainvoke(initial_state, config)

        return final_state

    async def stream(
        self,
        query: str,
        conversation_id: int,
        profile_id: Optional[int] = None,
        custom_instructions: Optional[str] = None,
        conversation_history: Optional[List[dict]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[dict]:
        """
        Stream the RAG workflow execution.

        Yields intermediate states as the workflow progresses.
        """
        # Initialize state with LLM configuration
        initial_state: RAGState = {
            "query": query,
            "conversation_id": conversation_id,
            "profile_id": profile_id,
            "custom_instructions": custom_instructions,
            "conversation_history": conversation_history or [],
            "retrieved_documents": [],
            "system_prompt": "",
            "model": model or settings.DEFAULT_MODEL,
            "temperature": temperature if temperature is not None else settings.DEFAULT_TEMPERATURE,
            "max_tokens": max_tokens or settings.DEFAULT_MAX_TOKENS,
            "response": "",
            "total_tokens": None,
            "cost": None,
            "model_used": None,
            "retrieval_time_ms": 0.0,
            "generation_time_ms": 0.0
        }

        # Stream workflow
        config = {"configurable": {"thread_id": str(conversation_id)}}

        async for event in self.graph.astream(initial_state, config):
            # Yield each node's output
            for node_name, node_output in event.items():
                yield {
                    "node": node_name,
                    "state": node_output
                }
