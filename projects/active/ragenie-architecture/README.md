# RaGenie Architecture

**Status:** In Progress
**Created:** 2025-12-14
**Last Updated:** 2025-12-14

## Overview

RaGenie is an agentic AI system that builds ON TOP of Ragbot, extending it with advanced orchestration, multi-agent workflows, and modern UI capabilities. This project documents the strategic architecture and the relationship between the two products.

## Problem Statement

Ragbot provides excellent RAG-enabled assistant capabilities via CLI and Streamlit UI, but modern AI applications require:

- **Agentic capabilities** — Autonomous task execution and tool use
- **Multi-agent orchestration** — Coordinating multiple AI agents for complex workflows
- **Modern web UI** — React/Next.js frontend enabling richer interactions
- **Mobile-ready architecture** — FastAPI backend supporting mobile apps and voice UI
- **Scalable infrastructure** — Microservices architecture for production deployment

## Solution

Build RaGenie as an **extension layer** on top of Ragbot, not a replacement:

```
┌─────────────────────────────────────────────────────────────┐
│                        RaGenie                               │
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
│  │  - Streamlit UI                                         │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI Knowledge Repos                        │
│  ai-knowledge-rajiv, ai-knowledge-flatiron, etc.            │
└─────────────────────────────────────────────────────────────┘
```

## Documents

| Document | Purpose |
|----------|---------|
| [architecture.md](architecture.md) | Technical architecture and component design |
| [current-status.md](current-status.md) | Development progress and what's working |
| [langgraph-integration.md](langgraph-integration.md) | LangGraph agentic workflow implementation |
| [testing-guide.md](testing-guide.md) | How to test the backend services |
| [brand-guidelines.md](brand-guidelines.md) | RaGenie naming and branding |

## Quick Links

- **RaGenie Source Code:** `/Users/rajivpant/projects/my-projects/ragenie/`
- **Ragbot (core):** [github.com/rajivpant/ragbot](https://github.com/rajivpant/ragbot)
- **AI Knowledge Repos:** `/Users/rajivpant/projects/my-projects/ai-knowledge/`

## Current Status

| Phase/Feature | Status | Description |
|---------------|--------|-------------|
| Microservices scaffolding | Complete | Auth, User, Document, Conversation, LLM Gateway services |
| Database migrations | Complete | Alembic with all tables including ragbot_documents |
| RAG pipeline | Complete | Qdrant vector DB, file watcher, embedding worker |
| LangGraph workflows | Complete | Three-node StateGraph with streaming SSE |
| Project documentation | In Progress | Consolidating into projects/ structure |
| **Strategic pivot** | In Progress | Redefining as extension layer on Ragbot |
| Ragbot integration | Not Started | Connect RaGenie to Ragbot core |
| Frontend | Not Started | React/Next.js UI |

## Strategic Pivot Note

> **Important:** The existing codebase was built as a "Ragbot v2 replacement". The new strategic direction is for RaGenie to be an **extension layer** that builds ON TOP of Ragbot. This means:
>
> - The existing microservices infrastructure is valuable and can be reused
> - The LangGraph agentic workflows are exactly what RaGenie needs
> - The RAG pipeline can be adapted to work with Ragbot's core
> - Future work should focus on integration, not duplication

## Key Decisions

### Why Build ON TOP of Ragbot (Not Replace)?

1. **Ragbot works well** — The CLI and Streamlit UI serve their purpose effectively
2. **Avoid duplication** — Ragbot's RAG engine, LLM clients, and persona handling are mature
3. **Incremental value** — Users can adopt RaGenie features without abandoning Ragbot
4. **Separation of concerns** — Ragbot = RAG engine, RaGenie = agentic orchestration

### Why FastAPI Backend?

1. **API-first** — Enables mobile apps, voice UI, third-party integrations
2. **Async by default** — Better performance for concurrent requests
3. **Production-ready** — Easy deployment, monitoring, scaling
4. **Type safety** — Pydantic schemas for request/response validation

### Why React/Next.js Frontend?

1. **Rich interactions** — Beyond what Streamlit offers
2. **Mobile-ready** — PWA or React Native sharing code
3. **Voice UI ready** — Web Speech API integration
4. **Modern UX** — Real-time updates, complex state management

## Related Projects

| Project | Location | Description |
|---------|----------|-------------|
| Ragbot | [github.com/rajivpant/ragbot](https://github.com/rajivpant/ragbot) | Core RAG-enabled assistant |
| AI Knowledge Compiler | [ragbot/projects/active/ai-knowledge-compiler](https://github.com/rajivpant/ragbot/tree/main/projects/active/ai-knowledge-compiler) | Compiles AI knowledge content |
