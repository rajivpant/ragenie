# Ragenie resources

This directory belongs to the first-generation RAG microservices
implementation. It contains public reference material that the current Docker
services mount read-only at `/data/resources/`.

The new [product direction](../docs/product-direction.md) does not yet decide
whether these resources belong in the harness runtime. Their presence in this
repository is not a commitment to that architecture.

## Contents

- `guides/`: public reference guides used by the current implementation

No workflow or template files are currently tracked in this directory.

## Current container behavior

- Product resources: repository files mounted read-only at `/data/resources/`
- User data: a separate path mounted read-only at `/data/user-data/`
- Indexing: the current file watcher indexes user data, not product resources

## Contributing

Resources must be suitable for unrestricted public distribution. Use generic
examples and exclude identifying names, local machine paths, credentials, and
material that has not passed the repository's publication checks.
