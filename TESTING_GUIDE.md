# RaGenie Testing Guide

## Overview

This guide provides step-by-step instructions for testing RaGenie's backend services.

---

## Prerequisites

1. **Environment Setup**
   ```bash
   cd /Users/rajivpant/projects/my-projects/ragenie
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

2. **ragbot-data Location**
   - Ensure ragbot-data exists at `/Users/rajivpant/ragbot-data`
   - Contains markdown files in `custom-instructions/` and `curated-datasets/`

---

## Starting the Services

```bash
# Start all services
docker-compose up -d

# Check service health
docker-compose ps

# View logs for specific services
docker-compose logs -f file-watcher
docker-compose logs -f embedding-worker
docker-compose logs -f conversation-service
```

---

## Running Migrations

```bash
# Run database migrations
docker-compose exec auth-service alembic upgrade head

# Verify tables were created
docker-compose exec postgres psql -U ragenie -d ragenie -c "\dt"
```

---

## Testing Each Service

### 1. Health Checks

```bash
# Auth Service (port 8001)
curl http://localhost:8001/health

# User Service (port 8002)
curl http://localhost:8002/health

# Document Service (port 8003)
curl http://localhost:8003/health

# Conversation Service (port 8004)
curl http://localhost:8004/health

# LLM Gateway Service (port 8005)
curl http://localhost:8005/health
```

**Expected**: All should return `{"status": "healthy", ...}`

---

### 2. File Watcher & Embedding Worker

#### Check File Detection

```bash
# View file watcher logs
docker-compose logs -f file-watcher

# Expected output:
# - "file_watcher_starting"
# - "initial_scan_complete" with files_queued count
# - "file_changed" when you edit a file
```

#### Check Embedding Status

```bash
# Check ragbot_documents table
docker-compose exec postgres psql -U ragenie -d ragenie -c "
  SELECT file_path, embedding_status, chunk_count, indexed_at
  FROM ragbot_documents
  ORDER BY updated_at DESC
  LIMIT 10;
"

# Check embedding queue
docker-compose exec postgres psql -U ragenie -d ragenie -c "
  SELECT status, COUNT(*), AVG(retry_count)
  FROM embedding_queue
  GROUP BY status;
"
```

**Expected**:
- Files should have `embedding_status = 'indexed'`
- Queue should have completed jobs

#### Check Qdrant

```bash
# Open Qdrant dashboard
open http://localhost:6333/dashboard

# Or check via API
curl http://localhost:6333/collections/ragenie_documents
```

**Expected**: Collection exists with vectors stored

---

### 3. Document Service API

#### List ragbot-data Documents

```bash
curl "http://localhost:8003/ragbot?limit=5" | jq
```

**Expected**: JSON list of documents with metadata

#### Get Specific Document

```bash
curl "http://localhost:8003/ragbot/custom-instructions/overview.md" | jq
```

**Expected**: Document metadata

#### Get Document Content

```bash
curl "http://localhost:8003/ragbot/custom-instructions/overview.md/content" | jq
```

**Expected**: File content returned

#### Get Embedding Status

```bash
curl "http://localhost:8003/ragbot/status" | jq
```

**Expected**:
```json
{
  "total_files": 78,
  "indexed": 78,
  "pending": 0,
  "failed": 0,
  "queue_size": 0
}
```

#### Generate Query Embedding

```bash
curl -X POST "http://localhost:8003/ragbot/embed/generate" \
  -H "Content-Type: application/json" \
  -d '{"text": "What is RaGenie?"}' | jq '.dimensions'
```

**Expected**: `1536` (embedding dimensions)

---

### 4. User Service API

#### Create User Profile

```bash
curl -X POST "http://localhost:8002/profiles" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Profile",
    "settings": {
      "custom_instructions": "You are a helpful AI assistant specialized in technical documentation."
    }
  }' | jq
```

**Expected**: Profile created with ID

#### List Profiles

```bash
curl "http://localhost:8002/profiles" | jq
```

**Expected**: Array of profiles

---

### 5. Conversation Service API

#### Create Conversation

```bash
curl -X POST "http://localhost:8004/conversations" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test RAG Conversation",
    "profile_id": 1
  }' | jq

# Save the conversation ID from response
CONV_ID=1
```

**Expected**: Conversation created with ID

#### Add Message

```bash
curl -X POST "http://localhost:8004/conversations/$CONV_ID/messages" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "user",
    "content": "What is RaGenie and how does it work?"
  }' | jq
```

**Expected**: Message created

#### Get RAG Context (THE KEY TEST!)

```bash
curl "http://localhost:8004/conversations/$CONV_ID/context?query=What%20is%20RaGenie" | jq
```

**Expected Response Structure**:
```json
{
  "conversation_id": 1,
  "profile_id": 1,
  "custom_instructions": "You are a helpful AI assistant...",
  "retrieved_documents": [
    {
      "file_path": "custom-instructions/overview.md",
      "chunk_index": 0,
      "chunk_text": "RaGenie is a RAG-powered...",
      "similarity_score": 0.85,
      "source": "ragbot-data",
      "category": "custom-instructions"
    }
  ],
  "conversation_history": [...],
  "system_prompt": "# Custom Instructions\n...\n# Relevant Context from Knowledge Base\n...",
  "user_query": "What is RaGenie",
  "total_retrieved": 5,
  "retrieval_time_ms": 234.5
}
```

**What to Verify**:
- ✅ `retrieved_documents` array is populated (if embeddings are ready)
- ✅ `similarity_score` is above threshold (default 0.7)
- ✅ `system_prompt` contains custom instructions and retrieved context
- ✅ `conversation_history` shows previous messages
- ✅ `retrieval_time_ms` is reasonable (< 1000ms)

#### Get Conversation History

```bash
curl "http://localhost:8004/conversations/$CONV_ID/messages" | jq
```

**Expected**: All messages in the conversation

---

## Common Issues & Troubleshooting

### Issue: No documents retrieved in RAG context

**Cause**: Embeddings not yet generated

**Solution**:
```bash
# Check embedding status
curl "http://localhost:8003/ragbot/status" | jq

# If pending, wait for embedding worker
docker-compose logs -f embedding-worker

# Manually trigger re-embedding
curl -X POST "http://localhost:8003/ragbot/embed/trigger" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Issue: "Collection not found" error

**Cause**: Qdrant collection not created

**Solution**:
```bash
# Restart embedding worker (it creates the collection on startup)
docker-compose restart embedding-worker

# Check Qdrant logs
docker-compose logs qdrant
```

### Issue: OpenAI API errors

**Cause**: Missing or invalid API key

**Solution**:
```bash
# Check .env file has OPENAI_API_KEY
grep OPENAI_API_KEY .env

# Restart services
docker-compose restart
```

### Issue: File changes not detected

**Cause**: Polling interval or volume mount issue

**Solution**:
```bash
# Check file-watcher logs
docker-compose logs -f file-watcher

# Manually edit a file in ragbot-data
echo "test change" >> /Users/rajivpant/ragbot-data/custom-instructions/overview.md

# Should see "file_changed" in logs within 5 seconds
```

---

## End-to-End RAG Workflow Test

This tests the complete flow from file to RAG response:

```bash
# 1. Add a new file to ragbot-data
echo "# Test Document\n\nThis is a test for RaGenie's RAG capabilities." > \
  /Users/rajivpant/ragbot-data/curated-datasets/test-document.md

# 2. Wait for file detection (5 seconds)
sleep 6

# 3. Check if detected
curl "http://localhost:8003/ragbot/curated-datasets/test-document.md" | jq '.embedding_status'

# 4. Wait for embedding (may take 10-30 seconds)
sleep 30

# 5. Query with RAG
curl "http://localhost:8004/conversations/1/context?query=test%20RaGenie%20capabilities" | jq '.retrieved_documents[] | .file_path'

# Expected: Should include "curated-datasets/test-document.md"
```

---

## Performance Benchmarks

### Expected Performance

| Operation | Expected Time |
|-----------|--------------|
| File detection | < 5 seconds |
| Single file embedding | 2-10 seconds |
| Batch embedding (10 files) | 10-30 seconds |
| Vector search | < 200ms |
| RAG context assembly | < 500ms |
| Full query (embed + search + context) | < 1000ms |

### Check Performance

```bash
# Test embedding generation speed
time curl -X POST "http://localhost:8003/ragbot/embed/generate" \
  -H "Content-Type: application/json" \
  -d '{"text": "test query"}'

# Test RAG context assembly speed (check retrieval_time_ms in response)
curl "http://localhost:8004/conversations/1/context?query=test" | jq '.retrieval_time_ms'
```

---

## Database Inspection

### Useful SQL Queries

```bash
# Connect to database
docker-compose exec postgres psql -U ragenie -d ragenie

# Check all tables
\dt

# Count documents by status
SELECT embedding_status, COUNT(*)
FROM ragbot_documents
GROUP BY embedding_status;

# Check recent embeddings
SELECT file_path, embedding_status, chunk_count, indexed_at
FROM ragbot_documents
WHERE indexed_at IS NOT NULL
ORDER BY indexed_at DESC
LIMIT 10;

# Check conversation messages
SELECT c.title, m.role, LEFT(m.content, 50) as content_preview
FROM conversations c
JOIN messages m ON m.conversation_id = c.id
ORDER BY m.created_at DESC
LIMIT 10;

# Exit
\q
```

---

## Interactive API Testing (Recommended)

Use FastAPI's built-in Swagger UI for interactive testing:

- **Document Service**: http://localhost:8003/docs
- **Conversation Service**: http://localhost:8004/docs
- **User Service**: http://localhost:8002/docs
- **Auth Service**: http://localhost:8001/docs

---

## Success Criteria

Your RaGenie backend is working correctly if:

- ✅ All health checks return 200 OK
- ✅ File watcher detects changes within 5 seconds
- ✅ Embeddings are generated and stored in Qdrant
- ✅ Document Service returns ragbot-data files
- ✅ Conversation Service creates conversations and messages
- ✅ RAG context endpoint returns relevant documents with high similarity scores
- ✅ System prompt is assembled with custom instructions and context
- ✅ All operations complete within expected time ranges

---

## Next Steps After Testing

Once all tests pass:

1. **LangGraph Integration** - Add agentic RAG workflows
2. **Frontend Development** - Build React UI
3. **Production Deployment** - Deploy to production environment

---

*Last updated: 2025-11-22*
