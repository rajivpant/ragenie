# Projects

Project documentation for RaGenie development.

## Active Projects

| Project | Description | Status |
|---------|-------------|--------|
| [RaGenie Architecture](active/ragenie-architecture/) | Strategic architecture - RaGenie as extension layer on Ragbot | In Progress |

## Structure

```
projects/
├── active/                           # Current projects
│   └── ragenie-architecture/         # Main architecture project
│       ├── README.md                 # Project overview
│       ├── architecture.md           # Technical architecture
│       ├── current-status.md         # What's built and working
│       ├── langgraph-integration.md  # Agentic workflow guide
│       ├── testing-guide.md          # Backend testing
│       └── brand-guidelines.md       # Naming conventions
├── completed/                        # Finished projects
├── work-logs/                        # Session logs
│   └── ragenie-architecture/
│       └── 2025-11-22-conversation-service-complete.md
├── lessons-learned/                  # Cross-cutting insights
└── templates/                        # Reusable templates
```

## Related Projects (Other Repos)

| Project | Location | Relationship |
|---------|----------|--------------|
| **Ragbot** | [github.com/rajivpant/ragbot](https://github.com/rajivpant/ragbot) | Core RAG engine that RaGenie extends |
| **AI Knowledge Compiler** | [ragbot/projects/active/ai-knowledge-compiler](https://github.com/rajivpant/ragbot/tree/main/projects/active/ai-knowledge-compiler) | Compiles content for both products |

## Convention

See [Project Documentation Convention](https://github.com/rajivpant/ragbot/blob/main/docs/conventions/project-documentation.md).
