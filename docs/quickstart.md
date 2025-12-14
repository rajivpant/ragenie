## RaGenie - Quick Start Guide

This guide will help you get RaGenie up and running in minutes.

### Prerequisites

- Docker Desktop installed and running
- At least one LLM API key (OpenAI, Anthropic, or Google)

### Step 1: Setup Environment

```bash
cd ragenie
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
GEMINI_API_KEY=your-key-here
```

### Step 2: Start the Services

```bash
# Start all services
docker-compose up -d

# Wait for services to be healthy (about 30 seconds)
docker-compose ps
```

### Step 3: Initialize Database

```bash
# Run database migrations
docker-compose exec auth-service alembic upgrade head

# Seed initial data (LLM providers and models)
docker-compose exec llm-gateway-service python -m app.utils.seed_data
```

### Step 4: Access the Application

Open your browser and navigate to:

**Frontend Application:** http://localhost:3000

**API Documentation:**
- Auth Service: http://localhost:8001/docs
- User Service: http://localhost:8002/docs
- Document Service: http://localhost:8003/docs
- Conversation Service: http://localhost:8004/docs
- LLM Gateway: http://localhost:8005/docs

**Monitoring:**
- Grafana: http://localhost:3001 (admin/admin)
- Prometheus: http://localhost:9090
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin123)

### Step 5: Create Your First User

**Option A: Via Frontend**
1. Go to http://localhost:3000
2. Click "Register"
3. Fill in your details
4. Login with your credentials

**Option B: Via API**

```bash
# Register a new user
curl -X POST http://localhost/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "username": "yourusername",
    "password": "yourpassword123"
  }'

# Login
curl -X POST http://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "yourusername",
    "password": "yourpassword123"
  }'
```

### Step 6: Create a Profile

```bash
# Get your access token from login response, then:
curl -X POST http://localhost/api/users/profiles \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My First Profile",
    "description": "Personal assistant profile",
    "settings": {
      "default_model": "gpt-4",
      "temperature": 0.7,
      "max_tokens": 4096
    }
  }'
```

### Step 7: Upload Documents

```bash
# Upload a custom instruction file
curl -X POST http://localhost/api/documents/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/your/instructions.md" \
  -F "document_type=custom_instructions" \
  -F "profile_id=1"

# Upload a curated dataset
curl -X POST http://localhost/api/documents/upload \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@/path/to/your/dataset.md" \
  -F "document_type=curated_datasets" \
  -F "profile_id=1"
```

### Step 8: Start a Conversation

```bash
# Create a conversation
curl -X POST http://localhost/api/conversations \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "profile_id": 1,
    "title": "My First Chat"
  }'

# Send a message
curl -X POST http://localhost/api/llm/chat \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": 1,
    "message": "Hello! Tell me about yourself.",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

### Troubleshooting

**Services won't start:**
```bash
# Check logs
docker-compose logs -f

# Rebuild containers
docker-compose down
docker-compose up --build
```

**Database connection errors:**
```bash
# Wait for PostgreSQL to be healthy
docker-compose ps postgres

# Check if migrations ran
docker-compose exec auth-service alembic current
```

**MinIO bucket not created:**
```bash
# Create bucket manually
docker-compose exec minio mc alias set local http://localhost:9000 minioadmin minioadmin123
docker-compose exec minio mc mb local/ragbot-documents
```

**Port conflicts:**
```bash
# Check what's using the ports
lsof -i :8001
lsof -i :3000

# Stop conflicting services or change ports in docker-compose.yml
```

### Next Steps

1. **Explore the UI**: Navigate through the frontend at http://localhost:3000

2. **Set Up Monitoring**: Configure Grafana dashboards at http://localhost:3001

3. **Read the Docs**: Check out the full README.md for advanced features

### Common Tasks

**View service logs:**
```bash
docker-compose logs -f [service-name]
```

**Restart a service:**
```bash
docker-compose restart [service-name]
```

**Stop all services:**
```bash
docker-compose down
```

**Stop and remove all data:**
```bash
docker-compose down -v
```

**Update dependencies:**
```bash
docker-compose build --no-cache
```

### Development Mode

For live code reloading:

```bash
# Start in foreground (see all logs)
docker-compose up

# Services will auto-reload when you edit code
```

### Getting Help

- Check logs: `docker-compose logs -f`
- View health: `docker-compose ps`
- API docs: Visit `/docs` endpoint on each service
- Issue tracker: [GitHub Issues]

---

**You're all set!** Start chatting with your AI assistant with full RAG capabilities.
