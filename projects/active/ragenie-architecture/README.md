# First-generation Ragenie architecture

> [!CAUTION]
> This record describes the earlier RAG microservices product architecture. It
> is not the independent synthesis-native harness design. See the current
> [product direction](../../../docs/product-direction.md).

**Status:** Historical product architecture; current implementation reference
**Created:** 2025-12-14
**Direction notice added:** 2026-09-01

## Overview

This project records the architecture used for the RAG microservices code that
is currently present in the repository. It treated Ragenie as an extension
layer on top of Ragbot. That relationship is historical, not the current
product direction.

## Problem Statement

Ragbot provides RAG-enabled assistant capabilities via CLI, Web UI, and API. This design proposed extending Ragbot with:

- **Agentic capabilities** — Autonomous task execution and tool use
- **Multi-agent orchestration** — Coordinating multiple AI agents for complex workflows
- **Advanced workflow automation** — LangGraph-based state machines for complex tasks

## Solution

Build Ragenie as an **extension layer** on top of Ragbot, not a replacement:

```
┌─────────────────────────────────────────────────────────────┐
│                        Ragenie                               │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Agentic Layer                                          │ │
│  │  - Multi-agent orchestration                            │ │
│  │  - Workflow automation                                  │ │
│  │  - Tool integration                                     │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  API Layer (FastAPI)                                    │ │
│  │  - REST/WebSocket endpoints                             │ │
│  │  - Authentication & authorization                       │ │
│  │  - LLM gateway with usage tracking                      │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Frontend Layer                                         │ │
│  │  - React/Next.js web UI                                 │ │
│  │  - Mobile apps (future)                                 │ │
│  │  - Voice UI (future)                                    │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        Ragbot                                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Core RAG Engine                                        │ │
│  │  - Knowledge retrieval (AI Knowledge repos)             │ │
│  │  - LLM integration (OpenAI, Anthropic, Google)          │ │
│  │  - Persona-aware responses                              │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Existing UIs                                           │ │
│  │  - CLI (ragbot.py)                                      │ │
│  │  - Web UI                                               │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI Knowledge Repos                        │
│  ai-knowledge-example-user, ai-knowledge-example-company    │
└─────────────────────────────────────────────────────────────┘
```

## Documents

| Document | Purpose |
|----------|---------|
| [architecture.md](architecture.md) | Technical architecture and component design |
| [current-status.md](current-status.md) | Development progress and what's working |
| [langgraph-integration.md](langgraph-integration.md) | LangGraph agentic workflow implementation |
| [testing-guide.md](testing-guide.md) | How to test the backend services |
| [brand-guidelines.md](brand-guidelines.md) | Ragenie naming and branding |

## Quick Links

- **Ragenie source code:** this repository
- **Ragbot:** [github.com/synthesisengineering/ragbot](https://github.com/synthesisengineering/ragbot)
- **Example knowledge repositories:** sibling `ai-knowledge-*` repositories supplied by the user

## Current Status

| Phase/Feature | Status | Description |
|---------------|--------|-------------|
| Microservices scaffolding | Complete | Auth, User, Document, Conversation, LLM Gateway services |
| Database migrations | Complete | Alembic with all tables including ragbot_documents |
| RAG pipeline | Complete | Qdrant vector DB, file watcher, embedding worker |
| LangGraph workflows | Complete | Three-node StateGraph with streaming SSE |
| Project documentation | In Progress | Consolidating into projects/ structure |
| **Strategic pivot** | In Progress | Redefining as extension layer on Ragbot |
| Ragbot integration | Not Started | Connect Ragenie to Ragbot core |
| Frontend | Not Started | React/Next.js UI |

## Key Decisions

### Why Build ON TOP of Ragbot (Not Replace)?

1. **Ragbot works well** — The CLI and Web UI serve their purpose effectively
2. **Avoid duplication** — Ragbot's RAG engine, LLM clients, and persona handling are mature
3. **Incremental value** — Users can adopt Ragenie features without abandoning Ragbot
4. **Separation of concerns** — Ragbot = RAG engine, Ragenie = agentic orchestration

### Why FastAPI Backend?

1. **API-first** — Enables mobile apps, voice UI, third-party integrations
2. **Async by default** — Supports concurrent requests without blocking the service loop
3. **Operationally explicit** — Deployment, monitoring, and scaling remain visible design concerns
4. **Type safety** — Pydantic schemas for request/response validation

### Why React/Next.js Frontend for Ragenie?

1. **Advanced agentic UX** — Multi-agent workflow visualization, real-time updates
2. **Voice UI ready** — Web Speech API integration

## Related Projects

| Project | Location | Description |
|---------|----------|-------------|
| Ragbot | [github.com/synthesisengineering/ragbot](https://github.com/synthesisengineering/ragbot) | Core RAG-enabled assistant |
| AI Knowledge Compiler | [ragbot/projects/active/ai-knowledge-compiler](https://github.com/synthesisengineering/ragbot/tree/main/projects/active/ai-knowledge-compiler) | Compiles AI knowledge content |
