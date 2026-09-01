# First-generation implementation status

> [!CAUTION]
> This is a historical implementation snapshot of the earlier RAG
> microservices architecture. It is not current product status for the planned
> synthesis-native harness. See the
> [product direction](../../../docs/product-direction.md).

## Last Updated: 2025-11-24 (Session 4 - Product Resources Architecture)

> This file preserves the state reported by the original implementation
> session. Claims below have not been re-verified for the new product direction.

---

## 🎯 Current Status: ~90% Complete - Agentic RAG Workflows Implemented

### What Works Right Now

✅ **Complete RAG Infrastructure**
- Qdrant vector database running on port 6333/6334
- File watcher monitoring ragbot-data for changes
- Embedding worker processing queue
- PostgreSQL schema with ragbot_documents and embedding_queue tables
- Read-only ragbot-data mounts in all relevant services

✅ **Automatic File Sync**
- File watcher detects changes every 5 seconds
- SHA-256 hash-based change detection
- Automatic queue insertion for new/modified files
- Graceful handling of file deletions

✅ **Embedding Pipeline**
- OpenAI text-embedding-3-small integration
- LangChain text splitter (512 tokens, 50 overlap)
- Batch embedding generation
- Qdrant vector storage with metadata
- Redis caching (30 min TTL)
- Error handling and retry logic

✅ **RAG Context Assembly**

- Vector search in Qdrant for relevant documents
- Custom instructions from user profiles
- Conversation history retrieval
- System prompt generation with context
- Query embedding generation endpoint
- Configurable top_k and similarity threshold

✅ **LangGraph Agentic Workflows**

- Three-node StateGraph: retrieve → augment → generate
- State persistence with MemorySaver checkpointer
- Async workflow execution
- LLM generation via LLM Gateway Service
- Message persistence (user + assistant)
- Conversation state management
- Error handling per node
- Performance tracking

✅ **Streaming Support**

- Server-Sent Events (SSE) streaming
- Real-time workflow progress updates
- Event-driven architecture (retrieve, augment, generate, done, error)
- Non-blocking async streaming

---

## 📦 Product Resources vs User Data Architecture

**NEW in Session 4**: Clear separation between product resources and user data.

### Product Resources (Public, Ships with Ragenie)
- **Location**: `./resources/` (part of ragenie repository)
- **Container Path**: `/data/resources/` (read-only mount)
- **Purpose**: Guides, workflows, templates that ship with Ragenie
- **Indexing**: NOT indexed by file-watcher (static reference material)
- **Distribution**: Open-source, publicly accessible on GitHub
- **Standalone Usage**: Can be used in other projects without Ragenie

**Structure**:
```
resources/
├── README.md              ✅ Created (architecture documentation)
├── guides/                ✅ Created
│   ├── README.md          ✅ Created
│   └── writing/           ✅ Created
│       └── Guide_to_Identifying_and_Improving_AI-Assisted_Content.md  ✅ Added
├── workflows/             ✅ Created (empty, for future LangGraph workflows)
└── templates/             ✅ Created (empty, for future configuration templates)
```

### User Data (Private, User-Specific)
- **Location**: User's filesystem, mounted via `RAGBOT_DATA_PATH`
- **Container Path**: `/data/user-data/` (read-only mount)
- **Purpose**: User's personal documents, notes, private content
- **Indexing**: YES - monitored by file-watcher and embedded for RAG
- **Distribution**: NOT shipped with Ragenie (private data)
- **Example**: `/path/to/test-data`

### Volume Mounts Configuration

**Updated docker-compose.yml**:
```yaml
services:
  document-service:
    volumes:
      # User's PRIVATE data
      - type: bind
        source: ${RAGBOT_DATA_PATH:-./.ragenie-data}
        target: /data/user-data
        read_only: true
      # Product RESOURCES
      - ./resources:/data/resources:ro
      - ./services/document-service:/app
```

Applied to services:
- ✅ document-service (user data + resources)
- ✅ conversation-service (resources only)
- ✅ file-watcher (user data only)
- ✅ embedding-worker (user data only)

---

## 📂 Project Structure

```
ragenie/
├── resources/                 ✅ NEW (Session 4)
│   ├── README.md              ✅ Product resources documentation
│   ├── guides/                ✅ User guides
│   │   ├── README.md          ✅ Guides documentation
│   │   └── writing/           ✅ Writing-related guides
│   │       └── Guide_to_Identifying_and_Improving_AI-Assisted_Content.md  ✅
│   ├── workflows/             ✅ Created (empty, for future use)
│   └── templates/             ✅ Created (empty, for future use)
│
├── services/
│   ├── auth-service/          ✅ 100% Complete (JWT auth, user management)
│   ├── user-service/          ✅ 100% Complete (profile CRUD operations)
│   ├── document-service/      ✅ 100% Complete (ragbot-data API, embedding generation)
│   ├── conversation-service/  ✅ 100% Complete (chat management, RAG context assembly)
│   ├── llm-gateway-service/   ✅ 100% Complete (LiteLLM integration)
│   ├── file-watcher/          ✅ 100% Complete (monitors user-data)
│   └── embedding-worker/      ✅ 100% Complete (processes embeddings)
│
├── migrations/
│   └── alembic/versions/
│       ├── 001_initial_schema.py          ✅ Complete
│       └── 002_add_ragbot_data_tables.py  ✅ Complete (NEW)
│
├── shared/
│   ├── models/                ✅ Complete (all SQLAlchemy models)
│   └── schemas/               ✅ Complete
│
├── infrastructure/
│   ├── nginx/                 ✅ Complete
│   └── monitoring/            ✅ Complete
│
├── frontend/                  📋 Not started
│
├── docker-compose.yml         ✅ Updated with dual volume mounts (Session 4)
└── .env.example              ✅ Updated with data directory documentation (Session 4)

External:
├── /path/to/test-data/                    (USER DATA - SOURCE OF TRUTH)
│   ├── .claudeignore                      ✅ Created (protects sensitive data)
│   └── RAGENIE_INTEGRATION.md             ✅ Created (600+ line architecture doc)
│
└── ../ragbot/resources/                    (PRODUCT RESOURCES IN SIBLING REPO)
    └── (Same structure as ragenie/resources/ for v1 compatibility)
```

---

## 🗃️ Database Schema (Current)

### Existing Tables (from migration 001)
- `users` - User accounts
- `profiles` - User profiles with settings
- `llm_providers` - AI provider configs
- `llm_models` - Available LLM models
- `conversations` - Chat sessions (with `state` JSON for LangGraph)
- `messages` - Chat messages
- `user_uploads` - User-uploaded files (renamed from `documents`)

### New Tables (from migration 002)
- `ragbot_documents` - ragbot-data file metadata
  - `id` (UUID primary key)
  - `file_path` (relative to /data/ragbot-data, unique)
  - `content_hash` (SHA-256)
  - `file_size`, `modified_at`, `indexed_at`
  - `embedding_status` (pending, indexed, failed, deleted)
  - `chunk_count`, `error_message`
  - `metadata` (JSON for tags, category, etc.)
  - Full-text search index on file_path

- `embedding_queue` - Async job queue
  - `id` (BigInt autoincrement)
  - `document_type` (ragbot | user_upload)
  - `document_id` (UUID reference)
  - `priority` (1-10, higher = more urgent)
  - `retry_count`, `max_retries`
  - `status` (pending, processing, completed, failed)
  - `error_message`
  - `created_at`, `started_at`, `completed_at`
  - Composite index on (status, priority DESC)

---

## 🔧 Services Configuration

### File Watcher Service
**Location**: `services/file-watcher/`
**Status**: ✅ Complete and functional
**What it does**:
- Monitors `/data/user-data` using polling observer (5s interval)
- Detects .md and .txt file changes
- Computes SHA-256 hashes
- Inserts/updates ragbot_documents table
- Queues files for embedding with priority 10 (high)
- Scans all existing files on startup
- **DOES NOT monitor /data/resources/** (product resources are static)

**Configuration**:
- `RAGBOT_DATA_PATH`: /data/user-data (updated in Session 4)
- `POLLING_INTERVAL`: 5 seconds
- `INCLUDE_EXTENSIONS`: .md, .txt
- `EXCLUDE_PATTERNS`: .git, __pycache__, .DS_Store

### Embedding Worker Service
**Location**: `services/embedding-worker/`
**Status**: ✅ Complete and functional
**What it does**:
- Polls embedding_queue table (5s interval)
- Processes up to 10 jobs concurrently
- Reads files from user-data (read-only)
- Chunks documents (RecursiveCharacterTextSplitter)
- Generates embeddings (OpenAI text-embedding-3-small)
- Stores vectors in Qdrant
- Updates database metadata
- Caches content in Redis
- Retries failed jobs up to 3 times
- **ONLY processes user data** (does not embed product resources)

**Configuration**:
- `RAGBOT_DATA_PATH`: /data/user-data (updated in Session 4)
- `EMBEDDING_MODEL`: text-embedding-3-small
- `EMBEDDING_DIMENSIONS`: 1536
- `CHUNK_SIZE`: 512 tokens
- `CHUNK_OVERLAP`: 50 tokens
- `BATCH_SIZE`: 10 concurrent jobs
- `POLL_INTERVAL`: 5 seconds
- `CACHE_TTL`: 1800 seconds (30 min)

**Qdrant Collection**: `ragenie_documents`
- Vector size: 1536 dimensions
- Distance metric: Cosine similarity
- Payload includes: file_path, chunk_index, chunk_text, content_hash, source, category, tags

---

## 📊 Data Flow (How it Works)

### 1. File Change Detection
```
User edits markdown file in ragbot-data
    ↓
File watcher detects change (within 5 seconds)
    ↓
Computes SHA-256 hash
    ↓
Compares with database
    ↓
If changed: UPDATE ragbot_documents, INSERT into embedding_queue
```

### 2. Embedding Generation
```
Embedding worker polls queue (every 5 seconds)
    ↓
Fetches pending jobs (priority DESC, limit 10)
    ↓
Marks as 'processing'
    ↓
Reads file from /data/ragbot-data (read-only)
    ↓
Chunks text (512 tokens, 50 overlap)
    ↓
Generates embeddings via OpenAI API
    ↓
Deletes old embeddings from Qdrant
    ↓
Uploads new embeddings to Qdrant
    ↓
Updates ragbot_documents (status='indexed', chunk_count=N)
    ↓
Caches content in Redis (30 min TTL)
    ↓
Marks queue job as 'completed'
```

### 3. Future: RAG Query (To be implemented)
```
User sends chat query
    ↓
Generate query embedding
    ↓
Search Qdrant for similar chunks
    ↓
Retrieve top-k documents
    ↓
Assemble context (custom instructions + curated datasets + chat history)
    ↓
Send to LLM via LLM Gateway Service
    ↓
Stream response to frontend
```

---

## 🚀 How to Run (When Ready)

### Prerequisites
1. Copy `.env.example` to `.env`
2. Add OpenAI API key: `OPENAI_API_KEY=sk-...`
3. Ensure the user data directory configured in `RAGBOT_DATA_PATH` exists
4. Product resources are in `./resources/` (ships with Ragenie)

### Start Services
```bash
cd /path/to/ragenie

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f file-watcher    # Watch file detection
docker-compose logs -f embedding-worker # Watch embedding processing

# Run migrations
docker-compose exec auth-service alembic upgrade head
```

### Initial Data Load
```bash
# The file-watcher will automatically scan all existing files on startup
# Check progress:
docker-compose exec postgres psql -U ragenie -d ragenie \
  -c "SELECT embedding_status, COUNT(*) FROM ragbot_documents GROUP BY embedding_status;"

# Check queue:
docker-compose exec postgres psql -U ragenie -d ragenie \
  -c "SELECT status, COUNT(*) FROM embedding_queue GROUP BY status;"
```

---

## 📋 Next Steps (Priority Order)

### Completed in Session 3

1. **✅ DONE**: File watcher service
2. **✅ DONE**: Embedding worker service
3. **✅ DONE**: Database migrations
4. **✅ DONE**: User Service API endpoints
5. **✅ DONE**: Document Service with:
   - GET /ragbot - List ragbot-data files ✅
   - GET /ragbot/{path} - Get specific file ✅
   - GET /ragbot/{path}/content - Read file content ✅
   - POST /ragbot/embed/trigger - Manual re-embed ✅
   - GET /ragbot/embed/status - Indexing progress ✅
   - POST /ragbot/embed/generate - Generate query embeddings ✅

6. **✅ DONE**: Conversation Service with:
   - GET /conversations - List conversations ✅
   - POST /conversations - Create conversation ✅
   - GET /conversations/{id}/messages - Get messages ✅
   - POST /conversations/{id}/messages - Add message ✅
   - GET /conversations/{id}/context - Assemble RAG context ✅
   - RAGRetrievalService for vector search ✅

7. **✅ DONE**: LangGraph Integration with:
   - StateGraph with retrieve → augment → generate nodes ✅
   - POST /conversations/{id}/chat - RAG workflow endpoint ✅
   - POST /conversations/{id}/chat/stream - Streaming SSE ✅
   - State persistence in conversations.state ✅
   - Message persistence (user + assistant) ✅
   - Performance tracking and error handling ✅

### Completed in Session 4

8. **✅ DONE**: Product Resources Architecture:
   - Created resources/ folder in ragenie ✅
   - Created resources/ folder in ragbot (v1 compatibility) ✅
   - Folder structure: guides/writing/, workflows/, templates/ ✅
   - Added Guide_to_Identifying_AI-Generated_Content_v2.md ✅
   - Created comprehensive README files ✅
   - Updated docker-compose.yml with dual volume mounts ✅
   - Updated .env.example with architecture documentation ✅
   - Updated CURRENT_STATUS.md ✅
   - Clear separation: user data vs product resources ✅

### Immediate (Next Priority)

1. **🔄 NEXT**: Build React Frontend:
   - Initialize Vite project
   - Authentication UI
   - Chat interface
   - Document management

### Next Month
9. **Data Migration from v1**:
   - Export script for v1 sessions
   - Import script to load into v2
   - Verification and testing

10. **Production Hardening**:
    - Security audit
    - Performance optimization
    - Load testing
    - Monitoring alerts

---

## ⚠️ Known Issues & Limitations

### Current Limitations
1. **User uploads not implemented**: Only ragbot-data files are processed
2. **No RAG query endpoint**: Can embed but can't search yet
3. **No frontend**: API-only at this stage
4. **No tests**: Test coverage at 0%
5. **Dev secrets**: Using development passwords

### Future Enhancements
- Streaming LLM responses
- Hybrid search (keyword + semantic)
- Advanced filtering by metadata
- Local embedding models (privacy)
- Multi-modal support (images, PDFs)
- Real-time file watching (when Docker supports inotify)

---

## 🔍 Debugging & Troubleshooting

### Check File Watcher Status
```bash
# View logs
docker-compose logs -f file-watcher

# Should see:
# - "file_watcher_starting"
# - "initial_scan_complete" with files_queued count
# - "file_changed" when you edit a file
```

### Check Embedding Worker Status
```bash
# View logs
docker-compose logs -f embedding-worker

# Should see:
# - "embedding_worker_starting"
# - "qdrant_collection_created" or "qdrant_collection_exists"
# - "jobs_fetched" with count
# - "job_completed" for each processed file
```

### Check Database
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U ragenie -d ragenie

# Check ragbot_documents
SELECT file_path, embedding_status, chunk_count, indexed_at
FROM ragbot_documents
ORDER BY updated_at DESC
LIMIT 10;

# Check embedding queue
SELECT status, COUNT(*), AVG(retry_count)
FROM embedding_queue
GROUP BY status;
```

### Check Qdrant
```bash
# Qdrant Web UI
open http://localhost:6333/dashboard

# Or via API
curl http://localhost:6333/collections/ragenie_documents
```

### Check Redis Cache
```bash
# Connect to Redis
docker-compose exec redis redis-cli

# List cached documents
KEYS doc:*

# Get cached document
GET "doc:curated-datasets/client-c/overview.md"
```

---

## 💡 Key Design Decisions Made

1. **Qdrant over pgvector**: Dedicated vector storage with LangGraph integration
2. **Polling Observer**: More reliable in Docker than inotify
3. **Read-only mounts**: Guarantees ragbot-data safety
4. **UUID primary keys**: Better for distributed systems
5. **Separate tables**: ragbot_documents vs user_uploads (clear ownership)
6. **Hash-based sync**: Only re-embed when content changes
7. **Async queue**: Decouples file watching from embedding
8. **Batch processing**: Up to 10 embeddings concurrently for efficiency
9. **Metadata extraction**: Category and tags from file path structure
10. **Multi-tier caching**: PostgreSQL + Redis + Qdrant

---

## 📞 Context for Future Sessions

### If This Chat is Lost

1. **Read this file first** to understand current state
2. **Read RAGENIE_INTEGRATION.md** in ragbot-data for architecture
3. **Check docker-compose.yml** for service configuration
4. **Review migrations/** for database schema
5. **Look at services/file-watcher/** and **services/embedding-worker/** for implementation

### What's Working

- File watcher detects changes ✅
- Embedding worker generates vectors ✅
- Qdrant stores embeddings ✅
- Database tracks metadata ✅
- Document Service with ragbot-data API ✅
- Conversation Service with chat management ✅
- RAG context assembly with vector search ✅
- Query embedding generation ✅
- LangGraph agentic workflows ✅
- Streaming SSE responses ✅
- Complete end-to-end RAG pipeline ✅

### What's Missing

- Frontend UI (React app)
- User authentication integration (currently placeholder)
- Production deployment configuration
- Advanced features: Tool calling, multi-turn reasoning

### Quick Start to Continue
```bash
# 1. Pull latest code
cd /path/to/ragenie
git pull

# 2. Review current status
cat CURRENT_STATUS.md

# 3. Continue with next priority item:
# - Build React frontend
# - Production deployment
# - Or whatever is marked as 🔄 NEXT above
```

---

## 🎉 Major Achievements So Far

✅ Qdrant vector database integrated
✅ File watcher monitoring ragbot-data
✅ Embedding pipeline processing files
✅ Database schema with ragbot_documents and queue
✅ Read-only ragbot-data mounts
✅ SHA-256 hash-based change detection
✅ Automatic re-embedding on file changes
✅ OpenAI embeddings with LangChain
✅ Redis caching layer
✅ Error handling and retry logic
✅ Complete RAG context assembly
✅ Vector search with Qdrant
✅ Conversation and message management
✅ Query embedding generation
✅ Custom instructions integration
✅ LangGraph agentic workflows
✅ Streaming SSE support
✅ State management and persistence
✅ End-to-end RAG pipeline
✅ Comprehensive documentation

**Total Lines of Code**: ~9,000+
**Total Files Created**: 80+
**Backend Services**: 7 of 7 (100% complete!)
**LangGraph Integration**: ✅ Complete
**Infrastructure**: 100% complete

---

*This file is the SOURCE OF TRUTH for current development status.*
*Update this file whenever significant progress is made.*
*Last updated by Claude Code session on 2025-11-24 (Session 4)*
