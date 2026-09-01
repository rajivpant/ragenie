# Ragenie product direction

**Status:** Direction decided; architecture charter not yet written

This document is the public source of truth for what Ragenie is becoming. The
repository also contains an earlier RAG microservices implementation. That code
is real, but it describes a previous product architecture rather than this
direction.

## Vision

Ragenie is an independent AI agent harness built around durable work. A project
should retain its memory, decisions, evidence, policies, and handoffs when a
conversation ends, a model changes, a machine is replaced, or another person
takes over.

The synthesis work system is native to Ragenie. It is not an optional layer
installed after the agent runtime. At the same time, the underlying work-system
contract remains open and vendor-neutral so other harnesses can implement it
without depending on Ragenie.

## Mission

Build a usable agent runtime in which people and agents can carry complex work
across sessions with inspectable state, evidence-backed progress, explicit
human decisions, reliable handoffs, and a lifecycle that keeps the system
healthy over time.

Ragenie should demonstrate what native synthesis support looks like while
remaining one implementation among many. It must earn adoption on its own
merits, never through a privileged place in the synthesis ecosystem.

## What an agent harness is

An assistant answers inside a conversation. A harness supplies the environment
in which agents do work: projects, model access, tool execution, permissions,
context, state, interfaces, and operational boundaries.

Ragenie's defining choice is the unit around which that environment is built.
The unit is the durable project, not the chat transcript.

## Product principles

### Work is the source of truth

Conversations, models, and interfaces attach to a project. They do not own the
project's state. Records remain readable and useful without reconstructing a
past chat.

### Progress arrives with evidence

The runtime treats builds, tests, diffs, source references, and receipts as
part of completed work. A status claim without its supporting evidence remains
a claim.

### Human judgment is explicit

Agents prepare, execute, check, and keep records. People decide what matters,
approve consequential actions, and remain accountable for what ships.

### Portability is architectural

Project state uses inspectable formats and a published contract. Ragenie may
provide the most complete implementation, but it cannot make the work system
depend on itself.

### Incomplete means visible

Every layer reports whether it is working, declined, or missing. A dormant
guard or absent capability cannot look like a successful check.

## Strategy

1. **Design from durable work outward.** Start with project state, evidence,
   policy, and handoffs. Attach chat, models, and tools to that center.
2. **Make synthesis native while keeping the contract neutral.** Ragenie will
   be the reference implementation; other runtimes remain first-class
   participants.
3. **Separate direction from shipped capability.** Public pages and docs state
   what exists, what is planned, and what remains undecided.
4. **Use the existing code as evidence, not as a constraint.** Reuse a service
   when it fits the harness architecture. Replace it when it does not.
5. **Prove the boundary.** A conformance suite and at least one independent
   implementation must demonstrate that the contract is portable in practice.

## Product plan

The plan is sequential. Dates follow the architecture charter and executable
work breakdown rather than being invented in advance.

### 1. Harness charter

Define the user and project model, runtime boundaries, tool execution,
sandboxing, model adapters, interfaces, security posture, deployment model, and
the migration boundary around the existing microservices code.

**Exit evidence:** a reviewed architecture decision record and a repository
plan that maps every first release capability to an owner, implementation
surface, test, and acceptance condition.

### 2. Independent runtime foundation

Implement the project runtime, model and tool boundaries, state model, and a
first usable interface. The foundation must work without importing private
configuration or assuming one person's machine layout.

**Exit evidence:** a fresh-machine setup reaches a working project, exercises a
real tool, persists state, and resumes from that state in a new session.

### 3. Native synthesis work system

Integrate session context, policy, gates, coordination, lifecycle, and doctors
as coherent product behavior. Personal policy is authored through supported
scaffolds rather than copied from a reference installation.

**Exit evidence:** each layer reports installed, declined, or missing; enabled
guards fail closed; a second session or person can continue the work from the
durable record.

### 4. Contract and conformance

Publish the runtime contract and executable conformance tests. Prove that the
work system remains complete when another harness implements the contract.

**Exit evidence:** the same project passes the declared conformance suite on
Ragenie and on an independent adapter without Ragenie-specific state.

### 5. First public release

Package the runtime, documentation, upgrade path, and support boundaries into a
release a stranger can evaluate from public materials.

**Exit evidence:** a person with no connection to the project installs the
released harness, completes real work, verifies the result, and resumes it in a
later session without direct support.

## The repository today

At the current public commit, this repository contains seven FastAPI service
directories and supporting infrastructure for an earlier RAG platform. The
services cover accounts, users, documents, conversations, model access, file
watching, and embeddings. The stack includes PostgreSQL, Redis, Qdrant, MinIO,
Nginx, Prometheus, Grafana, and Docker Compose.

The documents under `projects/active/ragenie-architecture/` record that
implementation. They are marked as first-generation architecture so they are
not mistaken for the new harness design. The guides under `docs/` that concern
setup and testing also describe the current backend implementation.

No synthesis-native harness release exists in this repository yet.

## Relationship to Ragbot

[Ragbot](https://github.com/synthesisengineering/ragbot) is a separate,
chat-led runtime in the synthesis ecosystem. The earlier Ragenie architecture
described Ragenie as an extension layer on top of Ragbot. That is no longer the
product direction.

The projects may share formats, libraries, or lessons when that produces a
clear result. Ragenie's architecture and release path are independent.

## Non-goals

- Making the synthesis work system depend on Ragenie
- Wrapping one model provider and calling the wrapper a harness
- Presenting the existing microservices platform as the new harness
- Preserving an earlier architecture solely because code already exists
- Publishing feature claims before the corresponding behavior and evidence exist

## Related work

- [The Synthesis Manifesto](https://synthesiswork.org/manifesto/)
- [The synthesis work system](https://synthesiswork.org/)
- [Current backend quick start](quickstart.md)
- [First-generation architecture record](../projects/active/ragenie-architecture/README.md)
