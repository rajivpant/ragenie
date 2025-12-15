# RaGenie - Agentic AI Platform

RaGenie is an agentic AI system that extends [Ragbot](https://github.com/rajivpant/ragbot) with advanced orchestration, multi-agent workflows, and a modern web UI.

## Relationship with Ragbot

```
┌─────────────────────────────────────────────────────────────┐
│                        RaGenie                               │
│  - Agentic workflows (LangGraph)                            │
│  - Multi-agent orchestration                                │
│  - FastAPI backend + React/Next.js frontend                 │
│  - Production-ready microservices                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Ragbot                                │
│  - Core RAG engine                                          │
│  - LLM integration (OpenAI, Anthropic, Google)              │
│  - CLI + Web UI + API                                       │
│  - AI Knowledge content compilation                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI Knowledge Repos                        │
│  ai-knowledge-ragbot (public templates/runbooks)            │
│  ai-knowledge-rajiv, ai-knowledge-flatiron, etc. (private)  │
└─────────────────────────────────────────────────────────────┘
```

**Ragbot** = Core RAG-enabled assistant (CLI + Web UI + API)
**RaGenie** = Agentic extension layer (multi-agent workflows, advanced orchestration)

Both products share the same AI Knowledge content from the ai-knowledge-* repositories.

## What RaGenie Adds

| Capability | Ragbot | RaGenie |
|------------|--------|---------|
| RAG-powered chat | Yes | Yes (via Ragbot) |
| CLI interface | Yes | No |
| Web UI | Yes | Yes |
| REST API | Yes | Yes |
| Agentic workflows | No | Yes (LangGraph) |
| Multi-agent orchestration | No | Yes |

## Architecture

### Backend Services (FastAPI)

| Service | Port | Purpose |
|---------|------|---------|
| Auth Service | 8001 | JWT authentication, user management |
| User Service | 8002 | Profile management, preferences |
| Document Service | 8003 | File storage, embedding generation |
| Conversation Service | 8004 | Chat management, RAG context assembly |
| LLM Gateway | 8005 | Unified LLM interface, cost tracking |
| File Watcher | - | Monitors AI Knowledge content |
| Embedding Worker | - | Generates vector embeddings |

### Infrastructure

- **PostgreSQL** - Primary database
- **Redis** - Caching, message queue
- **Qdrant** - Vector database for RAG
- **Nginx** - API gateway
- **Prometheus/Grafana** - Monitoring

### Current Status

| Component | Status |
|-----------|--------|
| Backend services | Complete |
| RAG pipeline (Qdrant) | Complete |
| LangGraph workflows | Complete |
| Streaming SSE | Complete |
| React frontend | Not started |
| Ragbot integration | Not started |

## Getting Started

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (for embeddings)
- Optionally: Anthropic, Google API keys

### Quick Start

```bash
# Clone and setup
cd ragenie
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec auth-service alembic upgrade head

# Check status
docker-compose ps
```

### API Documentation

Each service provides interactive docs:

- Auth: http://localhost:8001/docs
- User: http://localhost:8002/docs
- Document: http://localhost:8003/docs
- Conversation: http://localhost:8004/docs
- LLM Gateway: http://localhost:8005/docs

## Project Documentation

See [projects/](projects/) for detailed architecture and development docs:

- [Architecture Overview](projects/active/ragenie-architecture/)
- [LangGraph Integration](projects/active/ragenie-architecture/langgraph-integration.md)
- [Testing Guide](projects/active/ragenie-architecture/testing-guide.md)

## Development

RaGenie is built using **Synthesis Engineering**—systematically integrating human expertise with AI capabilities. Learn more:

- [The Professional Practice](https://rajiv.com/blog/2025/11/09/synthesis-engineering-the-professional-practice-emerging-in-ai-assisted-development/)
- [Technical Implementation](https://rajiv.com/blog/2025/11/09/synthesis-engineering-with-claude-code-technical-implementation-and-workflows/)

## Related Repositories

| Repository | Purpose |
|------------|---------|
| [ragbot](https://github.com/rajivpant/ragbot) | Core RAG engine (RaGenie extends this) |
| [ai-knowledge-ragbot](https://github.com/rajivpant/ai-knowledge-ragbot) | Open-source templates, runbooks, guides |
| ai-knowledge-* (private) | Personal/workspace AI Knowledge repos |

## License

Same as Ragbot
