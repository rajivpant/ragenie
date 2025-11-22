# LangGraph Integration Guide

## Overview

This guide explains how RaGenie uses LangGraph for agentic RAG workflows, including architecture, usage, and customization.

---

## Architecture

### StateGraph Workflow

RaGenie implements a three-node StateGraph for RAG-powered conversations:

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph StateGraph                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐          │
│  │ RETRIEVE │ ───> │ AUGMENT  │ ───> │ GENERATE │ ───> END │
│  └──────────┘      └──────────┘      └──────────┘          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Node Descriptions

#### 1. RETRIEVE Node
**Purpose**: Fetch relevant documents using vector search

**Process**:
1. Generate query embedding via Document Service
2. Search Qdrant with query vector
3. Filter by source (ragbot-data)
4. Apply similarity threshold (default: 0.7)
5. Return top-k documents (default: 5)

**Inputs**:
- `query`: User's question
- `top_k`: Number of documents to retrieve
- `similarity_threshold`: Minimum score

**Outputs**:
- `retrieved_documents`: List of relevant chunks
- `retrieval_time_ms`: Time taken

**Error Handling**:
- Returns empty list on failure
- Logs error but doesn't fail workflow

#### 2. AUGMENT Node
**Purpose**: Build comprehensive system prompt with context

**Process**:
1. Get custom instructions from profile
2. Format retrieved documents with metadata
3. Include conversation history (last 5 messages)
4. Assemble complete system prompt

**Inputs**:
- `custom_instructions`: From user profile
- `retrieved_documents`: From RETRIEVE node
- `conversation_history`: Recent messages

**Outputs**:
- `system_prompt`: Complete prompt for LLM

**Prompt Structure**:
```markdown
# Custom Instructions
[User's custom instructions]

# Relevant Context from Knowledge Base

## Source 1: curated-datasets/ragenie/overview.md
Relevance Score: 0.89

[Chunk text...]

---

## Source 2: custom-instructions/technical-writing.md
Relevance Score: 0.85

[Chunk text...]

---

# Recent Conversation History

**User**: What is RaGenie?
**Assistant**: RaGenie is a RAG-powered...
```

#### 3. GENERATE Node
**Purpose**: Generate AI response using LLM

**Process**:
1. Prepare messages (system + user query)
2. Call LLM Gateway Service
3. Extract response and metadata
4. Track tokens and cost

**Inputs**:
- `system_prompt`: From AUGMENT node
- `query`: User's question

**Outputs**:
- `response`: AI-generated answer
- `total_tokens`: Token usage
- `model_used`: LLM model name
- `generation_time_ms`: Time taken

**LLM Gateway Call**:
```json
{
  "messages": [
    {"role": "system", "content": "[system_prompt]"},
    {"role": "user", "content": "[query]"}
  ],
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

---

## State Management

### RAGState Type

```python
class RAGState(TypedDict):
    # Input
    query: str
    conversation_id: int
    profile_id: Optional[int]
    conversation_history: List[dict]

    # Intermediate
    custom_instructions: Optional[str]
    retrieved_documents: List[dict]
    system_prompt: str

    # Output
    response: str
    total_tokens: Optional[int]
    cost: Optional[float]
    model_used: Optional[str]

    # Metadata
    retrieval_time_ms: float
    generation_time_ms: float
```

### State Persistence

**Checkpointer**: MemorySaver
- Stores state in memory per conversation thread
- Thread ID: `str(conversation_id)`
- Enables workflow resumption
- Future: Migrate to PostgreSQL checkpointer

**Database State**:
```python
# conversations.state field stores:
{
  "last_retrieval_time_ms": 234.5,
  "last_generation_time_ms": 1234.5,
  "last_documents_count": 5
}
```

---

## API Endpoints

### POST /conversations/{id}/chat

**Non-streaming endpoint** - Returns complete response

**Request**:
```json
{
  "query": "What is RaGenie and how does it work?"
}
```

**Response**:
```json
{
  "conversation_id": 1,
  "response": "RaGenie is a RAG-powered chat system...",
  "retrieved_documents": [
    {
      "file_path": "curated-datasets/ragenie/overview.md",
      "chunk_index": 0,
      "chunk_text": "RaGenie is...",
      "similarity_score": 0.89,
      "source": "ragbot-data",
      "category": "curated-datasets",
      "tags": ["ragenie", "architecture"]
    }
  ],
  "total_tokens": 1234,
  "cost": null,
  "model_used": "gpt-4",
  "retrieval_time_ms": 234.5,
  "generation_time_ms": 1234.5
}
```

**What Happens**:
1. Verifies conversation ownership
2. Gets profile and custom instructions
3. Retrieves conversation history
4. Runs LangGraph workflow
5. Saves user message
6. Saves assistant message
7. Updates conversation state
8. Returns complete response

### POST /conversations/{id}/chat/stream

**Streaming endpoint** - Returns Server-Sent Events

**Request**:
```json
{
  "query": "Explain RAG workflows in detail"
}
```

**Response** (SSE Stream):
```
event: retrieve
data: {"node":"retrieve","data":{"documents_count":5,"retrieval_time_ms":234.5}}

event: augment
data: {"node":"augment","data":{"prompt_length":2500}}

event: generate
data: {"node":"generate","data":{"response":"RAG workflows consist of...","total_tokens":1234,"generation_time_ms":1234.5}}

event: done
data: {"status":"completed"}
```

**What Happens**:
1. Same setup as non-streaming
2. Streams each node's completion as SSE
3. Frontend can show progress
4. Saves messages after workflow completes

---

## Usage Examples

### Python Client

```python
import httpx
import json

async def chat_with_ragenie(conversation_id: int, query: str):
    """Non-streaming chat."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://localhost:8004/conversations/{conversation_id}/chat",
            json={"query": query}
        )
        return response.json()

async def chat_streaming(conversation_id: int, query: str):
    """Streaming chat with SSE."""
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            f"http://localhost:8004/conversations/{conversation_id}/chat/stream",
            json={"query": query}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    print(f"Event: {data}")

# Usage
response = await chat_with_ragenie(1, "What is RaGenie?")
print(response["response"])
```

### cURL Examples

```bash
# Non-streaming
curl -X POST "http://localhost:8004/conversations/1/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RaGenie?"}'

# Streaming (watch events)
curl -X POST "http://localhost:8004/conversations/1/chat/stream" \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain RAG workflows"}' \
  --no-buffer
```

### JavaScript/TypeScript

```typescript
// Non-streaming
async function chat(conversationId: number, query: string) {
  const response = await fetch(
    `http://localhost:8004/conversations/${conversationId}/chat`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    }
  );
  return await response.json();
}

// Streaming with EventSource
function chatStream(conversationId: number, query: string) {
  const eventSource = new EventSource(
    `http://localhost:8004/conversations/${conversationId}/chat/stream?query=${encodeURIComponent(query)}`
  );

  eventSource.addEventListener('retrieve', (e) => {
    const data = JSON.parse(e.data);
    console.log('Retrieved', data.data.documents_count, 'documents');
  });

  eventSource.addEventListener('generate', (e) => {
    const data = JSON.parse(e.data);
    console.log('Response:', data.data.response);
  });

  eventSource.addEventListener('done', () => {
    console.log('Workflow complete');
    eventSource.close();
  });

  eventSource.addEventListener('error', (e) => {
    console.error('Error:', e);
    eventSource.close();
  });
}
```

---

## Customization

### Modify Workflow Nodes

Edit `services/conversation-service/app/workflows/rag_workflow.py`:

```python
class RAGWorkflow:
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(RAGState)

        # Add custom nodes
        workflow.add_node("retrieve", self._retrieve_node)
        workflow.add_node("filter", self._custom_filter_node)  # NEW
        workflow.add_node("augment", self._augment_node)
        workflow.add_node("generate", self._generate_node)

        # Add custom edges
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "filter")  # NEW
        workflow.add_edge("filter", "augment")
        workflow.add_edge("augment", "generate")
        workflow.add_edge("generate", END)

        return workflow.compile(checkpointer=MemorySaver())

    async def _custom_filter_node(self, state: RAGState) -> RAGState:
        """Filter documents by relevance."""
        filtered_docs = [
            doc for doc in state["retrieved_documents"]
            if doc["similarity_score"] > 0.8
        ]
        return {**state, "retrieved_documents": filtered_docs}
```

### Add Conditional Routing

```python
def should_retrieve_more(state: RAGState) -> str:
    """Decide if more documents needed."""
    if len(state["retrieved_documents"]) < 3:
        return "retrieve"  # Go back to retrieve
    return "augment"  # Continue to augment

workflow.add_conditional_edges(
    "retrieve",
    should_retrieve_more,
    {
        "retrieve": "retrieve",
        "augment": "augment"
    }
)
```

### Configure LLM Parameters

Edit `_generate_node` in `rag_workflow.py`:

```python
response = await client.post(
    f"{settings.LLM_GATEWAY_URL}/chat/completions",
    json={
        "messages": messages,
        "model": "gpt-4-turbo",  # Different model
        "temperature": 0.5,      # More focused
        "max_tokens": 4000,      # Longer responses
        "top_p": 0.9,
        "frequency_penalty": 0.5
    }
)
```

### Adjust Retrieval Settings

Edit `app/core/config.py`:

```python
class Settings(BaseSettings):
    RAG_TOP_K: int = 10  # Retrieve more documents
    RAG_SIMILARITY_THRESHOLD: float = 0.75  # Higher threshold
```

---

## Performance Optimization

### Caching Embeddings

The Document Service already caches embeddings in Redis. For query caching:

```python
# In rag_retrieval.py
from redis import Redis

class RAGRetrievalService:
    def __init__(self):
        self.redis = Redis(host=settings.REDIS_HOST)
        # ...

    async def generate_embedding(self, text: str) -> List[float]:
        # Check cache
        cache_key = f"embedding:{text[:100]}"
        cached = self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # Generate and cache
        embedding = await self._fetch_embedding(text)
        self.redis.setex(cache_key, 1800, json.dumps(embedding))
        return embedding
```

### Parallel Node Execution

For independent nodes, use `StateGraph.add_parallel_edges`:

```python
# Execute multiple retrievals in parallel
workflow.add_node("retrieve_docs", self._retrieve_documents)
workflow.add_node("retrieve_history", self._retrieve_history)

workflow.add_parallel_edges(
    "start",
    ["retrieve_docs", "retrieve_history"]
)
```

### Batch Processing

Process multiple queries concurrently:

```python
from asyncio import gather

async def batch_chat(conversation_ids: List[int], queries: List[str]):
    """Process multiple chats concurrently."""
    workflow = RAGWorkflow()

    tasks = [
        workflow.run(query, conv_id)
        for conv_id, query in zip(conversation_ids, queries)
    ]

    return await gather(*tasks)
```

---

## Monitoring and Debugging

### Enable Detailed Logging

```python
import structlog

logger = structlog.get_logger()

class RAGWorkflow:
    async def _retrieve_node(self, state: RAGState) -> RAGState:
        logger.info("retrieve_node_start", query=state["query"])
        # ...
        logger.info(
            "retrieve_node_complete",
            documents_count=len(retrieved_documents),
            retrieval_time_ms=retrieval_time
        )
        return state
```

### Track Performance Metrics

```python
from prometheus_client import Histogram

retrieval_duration = Histogram(
    'ragenie_retrieval_duration_seconds',
    'Time spent retrieving documents'
)

@retrieval_duration.time()
async def _retrieve_node(self, state: RAGState) -> RAGState:
    # ...
```

### Inspect Workflow State

```python
# Get workflow state at any point
config = {"configurable": {"thread_id": "1"}}
current_state = await workflow.aget_state(config)

print(current_state.values)  # Current state
print(current_state.next)    # Next nodes to execute
```

---

## Troubleshooting

### No Documents Retrieved

**Symptom**: `retrieved_documents` is always empty

**Causes**:
1. Embeddings not generated yet
2. Query embedding generation failing
3. Qdrant collection empty

**Solutions**:
```bash
# Check embedding status
curl "http://localhost:8003/ragbot/status"

# Trigger re-embedding
curl -X POST "http://localhost:8003/ragbot/embed/trigger" \
  -H "Content-Type: application/json" -d '{}'

# Check Qdrant collection
curl "http://localhost:6333/collections/ragenie_documents"
```

### LLM Generation Fails

**Symptom**: Error in GENERATE node

**Causes**:
1. LLM Gateway Service down
2. Invalid API key
3. Timeout

**Solutions**:
```bash
# Check LLM Gateway health
curl "http://localhost:8005/health"

# Check environment variable
docker-compose exec conversation-service env | grep LLM_GATEWAY_URL

# Increase timeout in _generate_node
httpx.AsyncClient(timeout=120.0)  # 2 minutes
```

### Streaming Disconnects

**Symptom**: SSE stream cuts off early

**Causes**:
1. Reverse proxy timeout
2. Client timeout
3. Network issues

**Solutions**:
- Configure nginx timeout: `proxy_read_timeout 300s;`
- Set client keep-alive: `httpx.AsyncClient(timeout=None)`
- Add heartbeat events

---

## Future Enhancements

### Tool Calling

Add tools that the LLM can call:

```python
workflow.add_node("tool_selection", self._select_tool)
workflow.add_node("tool_execution", self._execute_tool)

workflow.add_conditional_edges(
    "generate",
    lambda state: "tool" if needs_tool(state) else END,
    {"tool": "tool_selection", END: END}
)
```

### Multi-Turn Reasoning

Enable back-and-forth reasoning:

```python
workflow.add_conditional_edges(
    "generate",
    lambda state: "retrieve" if needs_more_context(state) else END,
    {"retrieve": "retrieve", END: END}
)
```

### Human-in-the-Loop

Add approval step:

```python
workflow.add_node("human_review", self._wait_for_approval)
workflow.add_edge("generate", "human_review")
workflow.add_edge("human_review", END)
```

---

*For more information, see [SESSION_3_SUMMARY.md](SESSION_3_SUMMARY.md)*
