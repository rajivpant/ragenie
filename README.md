# Ragenie

Ragenie is becoming an independent AI agent harness built around durable work.
Its architectural center is the project: memory, decisions, evidence, policy,
coordination, and handoffs survive individual conversations and model changes.

The synthesis work system will be native to Ragenie, but never dependent on it.
The underlying contract remains open and vendor-neutral so other harnesses can
implement the same work system without privileged access to this codebase.

Read the [product direction](docs/product-direction.md) for the vision, mission,
strategy, staged plan, and boundaries.

## Current repository state

> [!IMPORTANT]
> This repository does not contain a released synthesis-native harness yet. It
> contains an earlier RAG microservices implementation. The code and its guides
> remain available while the independent harness architecture is defined and
> built.

The current implementation includes seven FastAPI service directories:

| Service | Responsibility |
|---------|----------------|
| Auth | Authentication and tokens |
| User | Profiles and preferences |
| Document | Files, metadata, and retrieval support |
| Conversation | Conversations and RAG context assembly |
| LLM gateway | Model-provider access |
| File watcher | Knowledge-file change detection |
| Embedding worker | Embedding generation and vector indexing |

Supporting infrastructure includes PostgreSQL, Redis, Qdrant, MinIO, Nginx,
Prometheus, Grafana, and Docker Compose.

The current docs distinguish between two things:

- [Product direction](docs/product-direction.md): what Ragenie is becoming
- [Backend quick start](docs/quickstart.md): how to inspect the earlier
  microservices implementation

## Why the direction changed

The earlier architecture treated Ragenie as an agentic extension to
[Ragbot](https://github.com/synthesisengineering/ragbot). The new direction is
larger and independent: Ragenie is a harness in its own right, with the
[synthesis work system](https://synthesiswork.org/) built into its runtime.

Ragbot remains a separate, chat-led runtime in the same ecosystem. The projects
can share formats, libraries, and lessons when doing so produces a clear result,
but neither product is the other's architectural layer.

## Current backend quick start

The commands below start only the tracked backend services. The Docker Compose
file contains a frontend definition, but no frontend source is tracked at the
current commit.

### Prerequisites

- Docker with the Compose plugin
- An API key for the embedding provider used by the current implementation

### Start

```bash
cp .env.example .env
mkdir -p .ragenie-data
# Add the required API key to .env.

docker compose up -d \
  postgres redis minio qdrant \
  auth-service user-service document-service conversation-service \
  llm-gateway-service file-watcher embedding-worker \
  prometheus grafana

docker compose exec auth-service alembic upgrade head
docker compose ps
```

The service APIs are available on ports 8001 through 8005. See the
[backend quick start](docs/quickstart.md) and
[quick reference](docs/quick-reference.md) for the current implementation.

## Documentation

- [Product direction](docs/product-direction.md)
- [Current backend quick start](docs/quickstart.md)
- [Current backend quick reference](docs/quick-reference.md)
- [Current backend testing guide](docs/quickstart-testing.md)
- [First-generation architecture record](projects/active/ragenie-architecture/README.md)

## Related work

- [Ragenie website](https://ragenie.ai/)
- [The Synthesis Manifesto](https://synthesiswork.org/manifesto/)
- [The synthesis work system](https://synthesiswork.org/)
- [Ragbot](https://github.com/synthesisengineering/ragbot)
- [Synthesis Coding](https://synthesiscoding.org/)

## License

[MIT](LICENSE.md)
