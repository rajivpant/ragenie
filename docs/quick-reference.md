# RaGenie Quick Reference

## 🚀 Quick Start

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec auth-service alembic upgrade head

# Check health
curl http://localhost:8004/health
```

## 📡 API Endpoints

### Conversations
```bash
# Create conversation
curl -X POST http://localhost:8004/conversations \
  -H "Content-Type: application/json" \
  -d '{"title": "My Chat", "profile_id": 1}'

# List conversations
curl http://localhost:8004/conversations

# Get messages
curl http://localhost:8004/conversations/1/messages
```

### Chat with RAG
```bash
# Non-streaming
curl -X POST http://localhost:8004/conversations/1/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is RaGenie?"}'

# Streaming (SSE)
curl -X POST http://localhost:8004/conversations/1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain RAG workflows"}' \
  --no-buffer
```

### RAG Context
```bash
# Get context assembly
curl "http://localhost:8004/conversations/1/context?query=test"
```

## 🔧 Services & Ports

| Service | Port | Endpoint |
|---------|------|----------|
| Auth | 8001 | http://localhost:8001 |
| User | 8002 | http://localhost:8002 |
| Document | 8003 | http://localhost:8003 |
| Conversation | 8004 | http://localhost:8004 |
| LLM Gateway | 8005 | http://localhost:8005 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |
| MinIO | 9000/9001 | localhost:9000 |
| Qdrant | 6333/6334 | http://localhost:6333 |

## 📊 Monitoring

```bash
# Check embedding status
curl http://localhost:8003/ragbot/status

# View logs
docker-compose logs -f conversation-service
docker-compose logs -f embedding-worker
docker-compose logs -f file-watcher

# Database queries
docker-compose exec postgres psql -U ragenie -d ragenie

# Qdrant dashboard
open http://localhost:6333/dashboard
```

## 🐛 Troubleshooting

```bash
# Restart a service
docker-compose restart conversation-service

# Rebuild a service
docker-compose up -d --build conversation-service

# Check container status
docker-compose ps

# View full logs
docker-compose logs --tail=100 conversation-service
```

## 📚 Documentation

- [CURRENT_STATUS.md](CURRENT_STATUS.md) - Project status
- [TESTING_GUIDE.md](TESTING_GUIDE.md) - Complete testing guide
- [LANGGRAPH_INTEGRATION_GUIDE.md](LANGGRAPH_INTEGRATION_GUIDE.md) - LangGraph details
- [SESSION_3_SUMMARY.md](SESSION_3_SUMMARY.md) - Session notes

## 🎯 Key Features

✅ Automatic file monitoring & embedding
✅ Vector search with Qdrant
✅ RAG context assembly
✅ LangGraph agentic workflows
✅ Streaming SSE responses
✅ State management & persistence

## 📝 Common Tasks

### Trigger Re-embedding
```bash
# Single file
curl -X POST http://localhost:8003/ragbot/embed/trigger \
  -H "Content-Type: application/json" \
  -d '{"file_path": "curated-datasets/test.md"}'

# All files
curl -X POST http://localhost:8003/ragbot/embed/trigger \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Check Database
```sql
-- Connect
docker-compose exec postgres psql -U ragenie -d ragenie

-- Embedding status
SELECT embedding_status, COUNT(*)
FROM ragbot_documents
GROUP BY embedding_status;

-- Recent conversations
SELECT id, title, created_at
FROM conversations
ORDER BY created_at DESC
LIMIT 10;
```

### Update Configuration
```bash
# Edit .env
nano .env

# Restart affected services
docker-compose restart conversation-service
```

## 🔐 Environment Variables

Key variables in `.env`:
- `OPENAI_API_KEY` - Required for embeddings
- `RAGBOT_DATA_PATH` - Path to ragbot-data
- `RAG_TOP_K` - Documents to retrieve (default: 5)
- `RAG_SIMILARITY_THRESHOLD` - Min score (default: 0.7)

## 💡 Tips

1. **Always check logs first** when debugging
2. **Use streaming** for better UX in frontend
3. **Monitor Qdrant** to verify embeddings
4. **Check embedding status** before testing RAG
5. **Use --no-buffer** with curl for streaming

## 🎓 Next Steps

1. Review [TESTING_GUIDE.md](TESTING_GUIDE.md)
2. Test all endpoints
3. Build React frontend
4. Deploy to production

---

**Status**: 90% Complete
**Last Updated**: 2025-11-22
**Ready For**: Frontend Development
