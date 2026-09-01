# Current backend quick start

> [!IMPORTANT]
> This guide starts the earlier RAG microservices implementation in the
> repository. It does not install the synthesis-native harness described in
> the [product direction](product-direction.md). No harness release exists in
> this repository yet.

The current repository tracks backend services and supporting infrastructure.
It does not track the frontend source referenced by the Docker Compose file, so
the command below names the backend services explicitly.

## Prerequisites

- Docker with the Compose plugin
- An API key for the embedding provider used by this implementation

## 1. Configure the environment

```bash
cp .env.example .env
mkdir -p .ragenie-data
```

Open `.env` and set `OPENAI_API_KEY`. The current embedding worker requires it.
The other provider keys are optional for model-gateway testing.

The example file points `RAGBOT_DATA_PATH` at `.ragenie-data`, which is ignored
by Git. Put only test documents there unless you have reviewed the current
implementation's storage and provider behavior for your use case.

## 2. Start the tracked backend

```bash
docker compose up -d \
  postgres redis minio qdrant \
  auth-service user-service document-service conversation-service \
  llm-gateway-service file-watcher embedding-worker \
  prometheus grafana
```

## 3. Run database migrations

```bash
docker compose exec auth-service alembic upgrade head
```

## 4. Inspect the services

```bash
docker compose ps
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
```

Interactive API docs:

- Auth: <http://localhost:8001/docs>
- User: <http://localhost:8002/docs>
- Document: <http://localhost:8003/docs>
- Conversation: <http://localhost:8004/docs>
- LLM gateway: <http://localhost:8005/docs>

Supporting services:

- Qdrant: <http://localhost:6333/dashboard>
- Grafana: <http://localhost:3001>
- Prometheus: <http://localhost:9090>
- MinIO: <http://localhost:9001>

The values in `.env.example` are development defaults. Do not expose this stack
to a network or use it with sensitive material without changing the passwords,
reviewing authentication, and verifying the data path.

## 5. Stop the services

```bash
docker compose down
```

Add `--volumes` only when you intend to erase the local service data.

## More detail

- [Quick reference](quick-reference.md)
- [Backend testing guide](quickstart-testing.md)
- [First-generation architecture record](../projects/active/ragenie-architecture/README.md)
