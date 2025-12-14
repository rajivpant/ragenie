# Claude Code Context: ragenie

## Repository: ragenie (PUBLIC)

This is a **PUBLIC** open source repository. Be careful not to include confidential information.

## Repository Ecosystem

| Repository | Type | Purpose | Location |
|------------|------|---------|----------|
| **ragbot** | Public | AI assistant CLI + Web UI | `~/projects/my-projects/ragbot/` |
| **ragenie** | Public | Agentic extension layer for Ragbot | `~/projects/my-projects/ragenie/` |
| **ai-knowledge-*** | Private | AI Knowledge content repos | `~/projects/my-projects/ai-knowledge/` |

Note: Home directory varies by machine (`/Users/rajiv` vs `/Users/rajivpant`), so use `~` for paths.

## VS Code Workspace

All repositories are in the same VS Code workspace for unified development.

## Product Relationship

- **Ragbot**: Core RAG-enabled assistant (CLI + Web UI). Actively maintained.
- **RaGenie**: Agentic extension layer that builds ON TOP of Ragbot. Adds multi-agent workflows, advanced orchestration.
- Both products share AI Knowledge content (ai-knowledge-* repos).
- Both products will continue to be actively developed.

## Architecture

RaGenie is a microservices-based platform:

- **FastAPI backend** - REST API services
- **React frontend** - Modern web UI
- **Qdrant** - Vector database for RAG
- **PostgreSQL** - Metadata and user management
- **Redis** - Caching layer

## Data Location

RaGenie reads AI Knowledge content from ai-knowledge-* repos (via AI Knowledge Compiler):

- **source/instructions/** - Identity/persona files
- **source/datasets/** - Reference knowledge
- **compiled/** - LLM-optimized output

## Privacy Guidelines for This Public Repo

### NEVER include in docs or code

- Client/employer company names (use "example-company" instead)
- Workspace names that reveal client relationships
- Any content from ragbot-data that could identify clients

### Safe to use

- "rajiv" workspace name (owner's personal workspace)
- Open source project workspace names (e.g., "ragenie")
- Generic example names: "example-company", "acme-corp", "test-workspace"

### Example transformations

When writing documentation or examples:

- Use "example-company" or "client-workspace" instead of actual client names
- Use generic business scenarios instead of actual client project details

## Key Concepts

### Workspace System

- `user_workspace` config points to the user's identity workspace (e.g., "rajiv")
- Workspace folder names are usernames - do NOT rename to generic names
- Workspaces inherit from the user workspace

### Multi-User Design

- System supports multiple users with separate identity workspaces
- Different workspaces may come from different git repos
- User workspaces are private; some workspaces may be shared team repos

### RAG Architecture

- Uses Qdrant for vector storage
- Separate collections per workspace with query-time merging
- Supports workspace inheritance in retrieval

## Git Operations

**IMPORTANT**: Before any git commands for this repo, ensure you are in the correct directory:

```bash
cd ~/projects/my-projects/ragenie
```

Each repo in the ecosystem has its own git history. Don't run git commands from the wrong directory.

## Versioning

- Version is tracked in `VERSION` file (semantic versioning: MAJOR.MINOR.PATCH)
- **Maintain version numbers**: When making releases, increment the version appropriately:
  - PATCH (0.0.X): Bug fixes, minor changes
  - MINOR (0.X.0): New features, backwards compatible
  - MAJOR (X.0.0): Breaking changes
- Create git tags for releases: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
- Push tags: `git push origin vX.Y.Z`

## Development Notes

- Docker-based development environment
- FastAPI for backend services
- React/TypeScript for frontend
- Qdrant for vector search (shared technology choice with Ragbot's planned RAG)
