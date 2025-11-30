# Claude Code Context: ragenie

## Repository: ragenie (PUBLIC)

This is a **PUBLIC** open source repository. Be careful not to include confidential information.

## Repository Ecosystem

| Repository | Type | Purpose | Location |
|------------|------|---------|----------|
| **ragbot** | Public | AI assistant CLI and Streamlit UI | `~/projects/my-projects/ragbot/` |
| **ragenie** | Public | Next-gen RAG platform | `~/projects/my-projects/ragenie/` |
| **ragbot-data** | Private | Shared data for both products | `~/ragbot-data/` |

Note: Home directory varies by machine (`/Users/rajiv` vs `/Users/rajivpant`), so use `~` for paths.

## VS Code Workspace

All three repositories are in the same VS Code workspace for unified development.

## Product Relationship

- **RaGenie**: Next-generation RAG platform, successor to Ragbot. Under active development.
- **Ragbot**: Original product, continues to be actively maintained and upgraded.
- Both products share `ragbot-data` as their data layer.
- Both products will continue to be actively developed.

## Architecture

RaGenie is a microservices-based platform:

- **FastAPI backend** - REST API services
- **React frontend** - Modern web UI
- **Qdrant** - Vector database for RAG
- **PostgreSQL** - Metadata and user management
- **Redis** - Caching layer

## Data Location

RaGenie reads data from `~/ragbot-data/workspaces/` (mounted read-only via Docker):

- **instructions/** - WHO: Identity/persona files
- **runbooks/** - HOW: Procedure guides
- **datasets/** - WHAT: Reference knowledge

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

## Development Notes

- Docker-based development environment
- FastAPI for backend services
- React/TypeScript for frontend
- Qdrant for vector search (shared technology choice with Ragbot's planned RAG)
