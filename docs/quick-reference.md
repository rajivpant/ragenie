# Current backend quick reference

> [!IMPORTANT]
> These commands apply to the earlier RAG microservices implementation, not the
> planned synthesis-native harness. See the
> [product direction](product-direction.md).

## Start

```bash
docker compose up -d \
  postgres redis minio qdrant \
  auth-service user-service document-service conversation-service \
  llm-gateway-service file-watcher embedding-worker
docker compose exec auth-service alembic upgrade head
docker compose ps
```

## Service endpoints

| Service | Port | Health | API docs |
|---------|------|--------|----------|
| Auth | 8001 | <http://localhost:8001/health> | <http://localhost:8001/docs> |
| User | 8002 | <http://localhost:8002/health> | <http://localhost:8002/docs> |
| Document | 8003 | <http://localhost:8003/health> | <http://localhost:8003/docs> |
| Conversation | 8004 | <http://localhost:8004/health> | <http://localhost:8004/docs> |
| LLM gateway | 8005 | <http://localhost:8005/health> | <http://localhost:8005/docs> |

## Supporting services

| Service | Port |
|---------|------|
| PostgreSQL | 5432 |
| Redis | 6379 |
| MinIO API / console | 9000 / 9001 |
| Qdrant HTTP / gRPC | 6333 / 6334 |
| Prometheus | 9090 |
| Grafana | 3001 |

## Logs

```bash
docker compose logs -f conversation-service
docker compose logs -f file-watcher
docker compose logs -f embedding-worker
```

## Data inspection

```bash
docker compose exec postgres psql -U ragenie -d ragenie
curl http://localhost:6333/collections
```

## Stop

```bash
docker compose down
```

See the [backend quick start](quickstart.md) for configuration and the
[backend testing guide](quickstart-testing.md) for bounded checks.
