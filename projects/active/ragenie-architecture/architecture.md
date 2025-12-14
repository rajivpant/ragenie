# RaGenie Technical Architecture

## Strategic Positioning

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Product Ecosystem                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐ │
│   │    Ragbot       │    │    RaGenie      │    │    Future       │ │
│   │    (Core)       │───▶│    (Agentic)    │───▶│    Products     │ │
│   └─────────────────┘    └─────────────────┘    └─────────────────┘ │
│          │                       │                                   │
│          │                       │                                   │
│          ▼                       ▼                                   │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │              Shared AI Knowledge Content                     │   │
│   │          (ai-knowledge-* repos via AI Knowledge Compiler)    │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Ragbot vs RaGenie: Complementary Products

| Aspect | Ragbot | RaGenie |
|--------|--------|---------|
| **Primary Use Case** | RAG-enabled personal assistant | Agentic AI workflows |
| **Interface** | CLI, Streamlit | Web UI, API, Mobile (future) |
| **Architecture** | Monolithic Python | Microservices (FastAPI) |
| **Deployment** | Local-first | Cloud-ready, self-hosted |
| **Users** | Individual power users | Teams, organizations |
| **Complexity** | Simple setup | Production infrastructure |

## RaGenie System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Client Layer                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Web UI     │  │  Mobile App  │  │   Voice UI   │  │  API Client  │     │
│  │  (Next.js)   │  │ (React Native)│  │ (Web Speech) │  │   (SDK)      │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │                  │             │
│         └─────────────────┴─────────────────┴──────────────────┘             │
│                                    │                                         │
│                                    ▼                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                              API Gateway                                     │
│                           (nginx / traefik)                                  │
├──────────────────────────────┬──────────────────────────────────────────────┤
│                              │                                               │
│                              ▼                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                           Service Layer                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │  Auth Service   │  │  LLM Gateway    │  │  Agent Service  │              │
│  │  (FastAPI)      │  │  Service        │  │  (orchestration)│              │
│  │                 │  │  (FastAPI)      │  │                 │              │
│  │  - JWT auth     │  │  - Multi-LLM    │  │  - Workflows    │              │
│  │  - User mgmt    │  │  - Usage track  │  │  - Tool use     │              │
│  │  - Permissions  │  │  - Cost mgmt    │  │  - Memory       │              │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘              │
│           │                    │                    │                        │
│           └────────────────────┴────────────────────┘                        │
│                               │                                              │
│                               ▼                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                          Data Layer                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │   PostgreSQL    │  │     Redis       │  │  Vector Store   │              │
│  │   (primary)     │  │   (cache/queue) │  │  (embeddings)   │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
│                                                                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                        Ragbot Integration                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                               │                                              │
│                               ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Ragbot Core                                  │    │
│  │  - RAG engine (knowledge retrieval)                                  │    │
│  │  - LLM client abstraction (OpenAI, Anthropic, Google)                │    │
│  │  - Persona/workspace handling                                        │    │
│  │  - Instruction compilation                                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                               │                                              │
│                               ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    AI Knowledge Content                              │    │
│  │  - ai-knowledge-rajiv, ai-knowledge-flatiron, etc.                   │    │
│  │  - Compiled via AI Knowledge Compiler                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Service Descriptions

### Auth Service (Existing)

**Location:** `services/auth-service/`

Handles authentication and authorization:
- JWT token issuance and validation
- User registration and management
- Role-based permissions
- API key management for programmatic access

### LLM Gateway Service (Existing)

**Location:** `services/llm-gateway-service/`

Unified interface to multiple LLM providers:
- Multi-provider support (OpenAI, Anthropic, Google)
- Usage tracking and cost management
- Rate limiting and quota enforcement
- Token counting and budget alerts

### Agent Service (Planned)

**Location:** `services/agent-service/` (to be created)

Orchestrates agentic AI workflows:
- Multi-agent coordination
- Tool integration (web search, code execution, file operations)
- Conversation memory and context management
- Workflow definition and execution

### RAG Service (Planned - via Ragbot Integration)

Rather than duplicating Ragbot's RAG capabilities, RaGenie will integrate with Ragbot:

**Option A: Library Import**
```python
# RaGenie service imports Ragbot as a library
from ragbot.core import RAGEngine
engine = RAGEngine(workspace="rajiv")
response = engine.query("What are my preferences?")
```

**Option B: Subprocess/CLI**
```python
# RaGenie calls Ragbot CLI
import subprocess
result = subprocess.run(["python", "ragbot.py", "-w", "rajiv", "-q", query])
```

**Option C: Internal API** (recommended for production)
```python
# Ragbot exposes an internal API that RaGenie consumes
# This requires adding an API layer to Ragbot
response = requests.post("http://ragbot:8000/query", json={"workspace": "rajiv", "query": query})
```

## Agentic Capabilities

### What Makes RaGenie "Agentic"?

1. **Autonomous Task Execution**
   - Given a goal, agent breaks it into steps and executes
   - Uses tools (search, code execution, file I/O) as needed
   - Handles errors and retries automatically

2. **Multi-Agent Workflows**
   - Coordinator agent delegates to specialist agents
   - Agents can communicate and hand off tasks
   - Parallel execution where possible

3. **Tool Integration**
   - Web search (Brave, Google, etc.)
   - Code execution (sandboxed Python/JavaScript)
   - File operations (read, write, analyze)
   - External API calls

4. **Memory and Context**
   - Long-term memory across sessions
   - Working memory for current task
   - Episodic memory for learning from past interactions

### Example Agentic Workflow

```
User: "Research the latest AI agent frameworks and create a comparison table"

Coordinator Agent:
├── Delegates to: Research Agent
│   ├── Uses: Web Search Tool
│   ├── Uses: Web Scraper Tool
│   └── Returns: Raw research findings
├── Delegates to: Analysis Agent
│   ├── Receives: Research findings
│   └── Returns: Structured comparison
├── Delegates to: Formatting Agent
│   ├── Receives: Structured comparison
│   └── Returns: Markdown table
└── Returns: Final comparison table to user
```

## Integration Points with Ragbot

### Shared Content

Both products consume the same AI Knowledge content:

```
ai-knowledge-rajiv/
├── source/
│   ├── instructions/
│   └── datasets/
└── compiled/           # Used by both Ragbot and RaGenie
    └── claude-projects/
```

### Ragbot as RAG Engine

RaGenie uses Ragbot's RAG capabilities for:
- Knowledge retrieval from compiled instructions
- Persona-aware response generation
- Context injection for agentic tasks

### Shared LLM Client Configuration

Both products can share LLM provider configurations:
- API keys (via environment variables or .env)
- Default models
- Token limits

## Deployment Architecture

### Development

```
docker-compose up
# Starts: PostgreSQL, Redis, auth-service, llm-gateway-service
# Ragbot runs locally (not containerized)
```

### Production

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer / CDN                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Frontend  │  │  API Gateway│  │  Services   │          │
│  │   (Next.js) │  │  (ingress)  │  │  (pods)     │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Managed Services                                        ││
│  │  - PostgreSQL (RDS/Cloud SQL)                            ││
│  │  - Redis (ElastiCache/Memorystore)                       ││
│  │  - Vector DB (Pinecone/Weaviate)                         ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Frontend | Next.js 14+ | SSR, App Router, React Server Components |
| API | FastAPI | Async, type-safe, auto-docs |
| Database | PostgreSQL | Reliable, feature-rich RDBMS |
| Cache | Redis | Fast caching, pub/sub for real-time |
| Vector DB | TBD | Embeddings for semantic search |
| Auth | JWT + OAuth2 | Standard, stateless authentication |
| Containerization | Docker | Consistent environments |
| Orchestration | Kubernetes (prod) | Scalable deployment |

## Next Steps

1. **Define Ragbot Integration Strategy** — Choose Option A, B, or C above
2. **Design Agent Service API** — Define endpoints for agentic workflows
3. **Prototype Multi-Agent Workflow** — Simple coordinator + specialist pattern
4. **Frontend Design** — Wireframes for web UI
5. **Connect to Ragbot** — Implement chosen integration approach
