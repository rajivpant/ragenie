# RaGenie - AI Augmentation Platform

> **Note:** RaGenie was previously known as "Ragbot". This represents a complete architectural rewrite as a scalable, production-ready microservices application with React frontend and FastAPI backend services.

RaGenie is a powerful agentic AI system designed to assist and augment humans with sophisticated tasks using Retrieval Augmented Generation (RAG) and multiple LLM providers.

## Architecture Overview

### Technology Stack

**Frontend:**
- React 18+ with TypeScript
- Vite for blazing-fast builds
- TanStack Query for data fetching
- Zustand for state management
- Tailwind CSS for styling

**Backend Services:**
- FastAPI (async Python framework)
- PostgreSQL 16 (primary database)
- Redis (caching and message queue)
- MinIO (S3-compatible object storage)
- Nginx (API gateway and reverse proxy)

**Monitoring:**
- Prometheus (metrics collection)
- Grafana (dashboards and visualization)

## Project Structure

```
ragenie/
├── services/                      # Backend microservices
│   ├── auth-service/             # Authentication and authorization
│   ├── user-service/             # User profile management
│   ├── document-service/         # Document upload and storage
│   ├── conversation-service/     # Chat session management
│   └── llm-gateway-service/      # LLM provider integration
├── frontend/                      # React application
├── shared/                        # Shared code
│   ├── models/                   # SQLAlchemy models
│   ├── schemas/                  # Pydantic schemas
│   └── utils/                    # Common utilities
├── infrastructure/               # Deployment configuration
│   ├── nginx/                    # API gateway config
│   ├── kubernetes/               # K8s manifests
│   └── monitoring/               # Prometheus/Grafana
├── migrations/                    # Database migrations
│   └── alembic/
├── scripts/                       # Utility scripts
│   └── data-migration/           # Migration from legacy Ragbot
└── docs/                          # Documentation
```

## Microservices

### 1. Auth Service (Port 8001)
- User registration and login
- JWT token management
- Password reset functionality
- OAuth2 compatible

**Endpoints:**
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get tokens
- `POST /auth/refresh` - Refresh access token
- `GET /auth/me` - Get current user info
- `POST /auth/change-password` - Change password
- `POST /auth/logout` - Logout

### 2. User Service (Port 8002)
- User profile management
- Profile CRUD operations
- User preferences
- Profile settings (model defaults, temperature, etc.)

### 3. Document Service (Port 8003)
- Document upload to MinIO
- Document metadata management
- Custom instructions storage
- Curated datasets storage
- Document search and retrieval

### 4. Conversation Service (Port 8004)
- Conversation/session management
- Message history
- Conversation search
- Context assembly for LLM

### 5. LLM Gateway Service (Port 8005)
- Unified interface to LLM providers
- OpenAI, Anthropic, Google integrations
- Token counting
- Cost tracking
- Response streaming (planned)

### 6. Frontend (Port 3000)
- Modern React UI
- Real-time chat interface
- Document management
- Profile switching
- Model configuration

### 7. Nginx API Gateway (Port 80)
- Routes requests to services
- SSL termination
- Rate limiting
- Load balancing

## Database Schema

### Users Table
- User authentication and profile information
- Relationships to profiles, documents, conversations

### Profiles Table
- User profiles with custom settings
- Maps to documents and conversations
- JSON settings field for flexibility

### Documents Table
- File metadata
- MinIO storage paths
- Document types (custom_instructions, curated_datasets)
- Content hash for deduplication

### Conversations Table
- Chat sessions
- Conversation titles and summaries
- User and profile associations

### Messages Table
- Individual chat messages
- Token counts and costs
- Model information
- Message metadata

### LLM Providers Table
- AI provider configurations
- API endpoints and keys
- Provider-specific settings

### LLM Models Table
- Available models
- Token limits and pricing
- Model capabilities
- Default parameters

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git
- OpenAI/Anthropic/Google API keys (at least one)

### Installation

1. Clone the repository:
```bash
cd ragenie
```

2. Copy environment template:
```bash
cp .env.example .env
```

3. Edit `.env` and add your API keys:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
```

4. Start all services:
```bash
docker-compose up -d
```

5. Initialize database:
```bash
docker-compose exec auth-service alembic upgrade head
```

6. Access the application:
- Frontend: http://localhost:3000
- API Gateway: http://localhost
- Grafana: http://localhost:3001
- Prometheus: http://localhost:9090
- MinIO Console: http://localhost:9001

### Development Mode

For development with hot-reload:

```bash
docker-compose up
```

This will start all services with live code reload enabled.

### Run Individual Services

```bash
# Auth service only
docker-compose up auth-service postgres redis

# Frontend only
docker-compose up frontend

# All backend services
docker-compose up postgres redis minio auth-service user-service document-service conversation-service llm-gateway-service
```

## API Documentation

Each service provides interactive API documentation:

- Auth Service: http://localhost:8001/docs
- User Service: http://localhost:8002/docs
- Document Service: http://localhost:8003/docs
- Conversation Service: http://localhost:8004/docs
- LLM Gateway Service: http://localhost:8005/docs

## Database Migrations

Using Alembic for database migrations:

```bash
# Create a new migration
docker-compose exec auth-service alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec auth-service alembic upgrade head

# Rollback migration
docker-compose exec auth-service alembic downgrade -1
```

## Testing

```bash
# Run all tests
docker-compose exec auth-service pytest

# Run specific service tests
docker-compose exec user-service pytest

# Run with coverage
docker-compose exec auth-service pytest --cov=app --cov-report=html
```

## Monitoring

### Prometheus Metrics

Available at http://localhost:9090

Metrics exposed by each service at `/metrics` endpoint:
- Request duration
- Request count
- Error rates
- Database query performance

### Grafana Dashboards

Available at http://localhost:3001 (admin/admin)

Pre-configured dashboards:
- System Overview
- API Performance
- Database Metrics
- LLM Usage and Costs

## Data Migration from v1

To migrate data from the original Ragbot:

```bash
# Run migration script
docker-compose exec auth-service python /app/scripts/migrate_from_v1.py

# Options:
# --sessions-dir: Path to old sessions directory
# --datasets-dir: Path to curated-datasets directory
# --instructions-dir: Path to custom-instructions directory
```

## Security Features

- JWT-based authentication
- Password hashing with bcrypt
- CORS protection
- Rate limiting
- SQL injection prevention (SQLAlchemy ORM)
- XSS protection
- Secure file upload validation
- API key encryption in database

## Scalability Features

- Horizontal scaling of services
- Database connection pooling
- Redis caching
- Asynchronous request handling
- Load balancing via Nginx
- Stateless service design
- Object storage for files

## Production Deployment

### Docker Swarm

```bash
docker stack deploy -c docker-compose.prod.yml ragbot
```

### Kubernetes

```bash
kubectl apply -f infrastructure/kubernetes/
```

### Environment Variables

Required production environment variables:
```bash
# Generate secure keys
JWT_SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 32)
MINIO_ROOT_PASSWORD=$(openssl rand -hex 32)

# Set environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
```

## Configuration

### Model Configuration

Models are now stored in the database. To add new models:

```bash
# Use the admin API or database directly
docker-compose exec auth-service python -m app.utils.seed_models
```

### Profile Configuration

Profiles are user-specific and managed via the UI or API:

```bash
POST /api/users/profiles
{
  "name": "Work Profile",
  "settings": {
    "default_model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 4096
  }
}
```

## Troubleshooting

### Services not starting

```bash
# Check logs
docker-compose logs -f [service-name]

# Restart services
docker-compose restart

# Rebuild containers
docker-compose up --build
```

### Database connection issues

```bash
# Check PostgreSQL is healthy
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up postgres
```

### MinIO connection issues

```bash
# Create bucket manually
docker-compose exec minio mc alias set local http://localhost:9000 minioadmin minioadmin123
docker-compose exec minio mc mb local/ragbot-documents
```

## Development Methodology

RaGenie is built using **Synthesis Engineering** (also known as **Synthesis Coding**)—a professional practice that systematically integrates human expertise with AI capabilities to build production-grade software. This approach enabled the transformation from Ragbot's monolithic Streamlit application into RaGenie's scalable microservices architecture while maintaining code quality and architectural coherence.

The methodology emphasizes:

- **Human Architectural Authority:** Engineers define system boundaries, technology choices, and integration patterns before AI-assisted implementation
- **Systematic Quality Standards:** The same rigorous code review, testing, and security analysis applied regardless of how code is generated
- **Active System Understanding:** Every component is comprehended deeply enough to debug production issues
- **Iterative Context Building:** Knowledge compounds across development sessions for increasingly sophisticated implementations

This approach delivered 7 production-ready backend services, comprehensive database migrations, and a modern React frontend—all while ensuring the codebase remains maintainable and well-understood.

Learn more about Synthesis Engineering:

- [The Professional Practice](https://rajiv.com/blog/2025/11/09/synthesis-engineering-the-professional-practice-emerging-in-ai-assisted-development/)
- [Organizational Framework](https://rajiv.com/blog/2025/11/09/the-synthesis-engineering-framework-how-organizations-build-production-software-with-ai/)
- [Technical Implementation with Claude Code](https://rajiv.com/blog/2025/11/09/synthesis-engineering-with-claude-code-technical-implementation-and-workflows/)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write tests
5. Submit a pull request

## Future Enhancements

- [ ] Streaming LLM responses
- [ ] Vector database integration (Pinecone/Weaviate)
- [ ] Advanced RAG with embeddings
- [ ] Multi-tenancy support
- [ ] Organization management
- [ ] Mobile apps (iOS/Android)
- [ ] Real-time collaboration
- [ ] Advanced analytics
- [ ] Plugin system
- [ ] Webhook integrations

## License

Same as original Ragbot

## Support

For issues and questions:
- GitHub Issues: [link]
- Documentation: [link]
- Community: [link]

---

Built with ❤️ for sophisticated agentic AI systems
