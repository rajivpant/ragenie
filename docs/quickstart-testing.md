# Current backend testing guide

> [!IMPORTANT]
> This guide exercises the earlier RAG microservices implementation. It is not
> an acceptance suite for the planned synthesis-native harness. See the
> [product direction](product-direction.md).

## Prepare a test environment

```bash
cp .env.example .env
mkdir -p .ragenie-data
```

Set `OPENAI_API_KEY` in `.env`; the current embedding path requires it. Use only
test documents in `.ragenie-data`.

## Start the tracked services

```bash
docker compose up -d \
  postgres redis minio qdrant \
  auth-service user-service document-service conversation-service \
  llm-gateway-service file-watcher embedding-worker

docker compose exec auth-service alembic upgrade head
docker compose ps
```

## Check service health

```bash
curl --fail http://localhost:8001/health
curl --fail http://localhost:8002/health
curl --fail http://localhost:8003/health
curl --fail http://localhost:8004/health
curl --fail http://localhost:8005/health
```

## Exercise file detection

Create a harmless test document:

```bash
printf '# Test document\n\nRagenie indexing fixture.\n' > .ragenie-data/test-document.md
docker compose logs --tail=50 file-watcher
docker compose logs --tail=50 embedding-worker
```

The logs should show the file watcher observing the document and the embedding
worker processing the queued work. Treat a different result as a failed check;
do not infer success from containers merely being present.

## Inspect backing services

```bash
docker compose exec postgres psql -U ragenie -d ragenie -c '\dt'
curl --fail http://localhost:6333/collections
```

## Stop and clean up

```bash
docker compose down
```

The `.ragenie-data` directory and Docker volumes remain. Remove either only
when you intend to erase the test data.

## Scope of this guide

This repository does not currently track an automated end-to-end test suite or
the frontend source named by Docker Compose. These commands are bounded checks
of the backend services and infrastructure that are present in the repository.
