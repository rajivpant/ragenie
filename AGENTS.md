# Repository context: ragenie

## Repository

Ragenie is a **PUBLIC** open-source repository. Every tracked byte must be
suitable for unrestricted public distribution. Exclude non-public workspace
identifiers, personal machine paths, real-party work details, and material
copied from access-controlled knowledge repositories.

## Product direction

Ragenie is becoming a full, independent, synthesis-native AI agent harness.
The durable project is the architectural center. Conversations, models, tools,
and interfaces attach to project state rather than owning it.

The synthesis work system is native to Ragenie, while the underlying contract
remains open and vendor-neutral. Ragenie is a reference implementation, never a
privileged dependency. The public source of truth is
`docs/product-direction.md`.

## Current implementation boundary

The code currently tracked in this repository is an earlier RAG microservices
implementation. It includes seven FastAPI service directories plus PostgreSQL,
Redis, Qdrant, MinIO, Nginx, Prometheus, Grafana, and Docker Compose support.

Documents under `projects/active/ragenie-architecture/` describe that
first-generation implementation. They are historical architecture records, not
the new harness design. Setup guides under `docs/` must label that boundary.

## Relationship to Ragbot

Ragbot is a separate chat-led runtime. Ragenie is no longer defined as an
extension layer on top of Ragbot. The repositories may share public formats or
libraries when the new architecture calls for them, but neither product is the
other's required layer.

## Public-repository rules

### Never include

- Client, employer, or colleague names
- Identifying descriptions of private organizations or work
- Personal absolute paths or usernames
- Private repository names or private configuration
- Credentials, tokens, private endpoints, or operational details

### Safe examples

- `example-user`, `example-company`, `example-workspace`
- Repository-relative paths
- Public synthesis project names and public URLs

## Architecture and implementation rules

- Treat `docs/product-direction.md` as direction, not as proof that a capability
  exists.
- Label planned, implemented, and verified behavior separately.
- Do not preserve an earlier architecture solely for compatibility. Reuse must
  earn its place in the harness design.
- Keep the work-system contract implementable without Ragenie-specific state.
- A completion claim includes its evidence.

## Current development environment

- Docker Compose
- FastAPI services
- PostgreSQL, Redis, Qdrant, and MinIO
- No tracked frontend source at the current commit

## Git operations

Run Git commands from this repository's root. Use a feature branch for
non-trivial changes. Commit messages in this public repository remain generic.
Never bypass hooks with `--no-verify`.
