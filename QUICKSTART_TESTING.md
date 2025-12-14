# Quick Start Testing Guide

## Prerequisites

1. **OpenAI API Key**: Required for embeddings
2. **ragbot-data**: Must exist at `/Users/rajivpant/ragbot-data`
3. **Docker**: Docker Desktop running

## Step 1: Environment Setup

```bash
cd /Users/rajivpant/projects/my-projects/ragenie

# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# At minimum, set: OPENAI_API_KEY=sk-...
nano .env  # or use your preferred editor
```

## Step 2: Start Services

```bash
# Start all services
docker-compose up -d

# Wait ~30 seconds for services to be healthy
docker-compose ps

# Should show all services as "healthy" or "running"
```

## Step 3: Run Database Migrations

```bash
# Run migrations to create tables
docker-compose exec auth-service alembic upgrade head

# Should see:
# INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial schema
# INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, Add ragbot-data and embedding queue tables
```

## Step 4: Monitor File Watcher

```bash
# Watch file watcher logs
docker-compose logs -f file-watcher

# You should see:
# - "file_watcher_starting"
# - "scanning_existing_files"
# - "initial_scan_complete" with files_queued count
# - If you edit a file, you'll see "file_changed"
```

## Step 5: Monitor Embedding Worker

```bash
# In a new terminal, watch embedding worker
docker-compose logs -f embedding-worker

# You should see:
# - "embedding_worker_starting"
# - "qdrant_collection_created" (first time only)
# - "jobs_fetched" with count > 0
# - "job_processing" for each file
# - "ragbot_document_indexed" with chunk count
```

## Step 6: Test File Change Detection

```bash
# Edit a file in ragbot-data
echo "\n\nTest update $(date)" >> /Users/rajivpant/ragbot-data/curated-datasets/test.md

# Within 5 seconds, check file-watcher logs:
docker-compose logs --tail=20 file-watcher

# Should see:
# - "file_modified" or "new_file_detected"
# - "reembedding_queued" or "new_file_queued"

# Then check embedding-worker logs:
docker-compose logs --tail=20 embedding-worker

# Should see:
# - "job_processing"
# - "document_chunked"
# - "ragbot_document_indexed"
```

## Step 7: Check Database

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U ragenie -d ragenie

# Check how many files are tracked
SELECT embedding_status, COUNT(*)
FROM ragbot_documents
GROUP BY embedding_status;

# Should show:
#  embedding_status | count
# ------------------+-------
#  indexed          |   78   (or however many .md files you have)
#  pending          |    0   (if all processed)

# Check a specific file
SELECT file_path, chunk_count, indexed_at
FROM ragbot_documents
WHERE file_path LIKE '%test%'
LIMIT 5;

# Exit psql
\q
```

## Step 8: Check Qdrant

```bash
# Check Qdrant collection
curl http://localhost:6333/collections/ragenie_documents

# Should return JSON with:
# - status: "green"
# - vectors_count: number of chunks embedded
# - points_count: same as vectors_count

# Or open Qdrant dashboard
open http://localhost:6333/dashboard
```

## Step 9: Check Redis Cache

```bash
# Connect to Redis
docker-compose exec redis redis-cli

# List cached documents
KEYS doc:*

# Should show cached file paths

# Get a cached document (replace path with actual file)
GET "doc:curated-datasets/client-c/overview.md"

# Exit Redis
EXIT
```

## Step 10: Test Embedding Quality

```bash
# Query Qdrant for similar documents
curl -X POST http://localhost:6333/collections/ragenie_documents/points/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ...],  # Would need actual embedding
    "limit": 5,
    "with_payload": true
  }'

# For now, just verify collection exists and has points
curl http://localhost:6333/collections/ragenie_documents | jq
```

## Troubleshooting

### Services Won't Start

```bash
# Check for port conflicts
lsof -i :5432  # PostgreSQL
lsof -i :6333  # Qdrant
lsof -i :6379  # Redis

# Rebuild services
docker-compose down
docker-compose build
docker-compose up -d
```

### File Watcher Not Detecting Changes

```bash
# Check if ragbot-data is mounted
docker-compose exec file-watcher ls -la /data/ragbot-data

# Should list your files

# Check file watcher logs for errors
docker-compose logs file-watcher | grep -i error
```

### Embedding Worker Not Processing

```bash
# Check OpenAI API key is set
docker-compose exec embedding-worker env | grep OPENAI_API_KEY

# Should show: OPENAI_API_KEY=sk-...

# Check for errors
docker-compose logs embedding-worker | grep -i error

# Check queue
docker-compose exec postgres psql -U ragenie -d ragenie \
  -c "SELECT status, COUNT(*) FROM embedding_queue GROUP BY status;"
```

### Database Errors

```bash
# Check if migrations ran
docker-compose exec postgres psql -U ragenie -d ragenie \
  -c "\dt"  # List tables

# Should show: ragbot_documents, embedding_queue, etc.

# Re-run migrations
docker-compose exec auth-service alembic upgrade head
```

### Qdrant Not Responding

```bash
# Check Qdrant health
curl http://localhost:6333/health

# Should return: {"title":"healthz","version":"..."}

# Restart Qdrant
docker-compose restart qdrant
```

## Expected Results

After successful setup:

1. **~78+ files** discovered in ragbot-data
2. **All files** embedded (check `embedding_status = 'indexed'`)
3. **~150-300 chunks** in Qdrant (depends on file sizes)
4. **File changes** detected within 5 seconds
5. **Re-embedding** completes within 30-45 seconds

## Performance Metrics

- **Initial scan**: ~1-2 minutes for 78 files
- **Initial embedding**: ~5-10 minutes (depends on API rate limits)
- **File change detection**: < 5 seconds
- **Re-embedding**: 30-45 seconds per file
- **Memory usage**: ~2GB total (all services)
- **Disk usage**: ~500MB for Qdrant vectors

## Next Steps

Once everything is working:

1. **Build Document Service**: To query ragbot-data via API
2. **Build Conversation Service**: To manage chat sessions
3. **Integrate LangGraph**: For RAG query workflow
4. **Build Frontend**: React UI for chatting

## Useful Commands

```bash
# View all logs
docker-compose logs -f

# View specific service
docker-compose logs -f file-watcher

# Restart a service
docker-compose restart file-watcher

# Stop everything
docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v

# Check service health
docker-compose ps

# Execute command in container
docker-compose exec embedding-worker python -c "import openai; print('OpenAI installed')"
```

## Success Indicators

✅ File watcher shows "initial_scan_complete"
✅ Embedding worker shows "ragbot_document_indexed" messages
✅ Database shows embedding_status = 'indexed' for files
✅ Qdrant shows vectors_count > 0
✅ Redis shows cached documents with KEYS doc:*
✅ Editing a file triggers re-embedding within 45 seconds

## If Something Goes Wrong

1. Check logs: `docker-compose logs -f [service-name]`
2. Verify environment variables: `docker-compose config`
3. Check database: `psql` commands above
4. Restart services: `docker-compose restart`
5. Rebuild if needed: `docker-compose up --build`
6. Check CURRENT_STATUS.md for known issues

---

*Testing should take ~15-20 minutes total (including initial embedding)*
*Most time is spent waiting for OpenAI API to generate embeddings*
