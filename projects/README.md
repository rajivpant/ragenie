# Ragenie project records

The product direction changed in 2026. Ragenie is becoming an independent,
synthesis-native agent harness rather than an extension layer on top of
Ragbot.

The current public direction lives in
[docs/product-direction.md](../docs/product-direction.md).

## Existing architecture record

| Record | What it describes | Status |
|--------|-------------------|--------|
| [First-generation Ragenie architecture](active/ragenie-architecture/) | The RAG microservices implementation currently tracked in this repository | Historical product architecture; current implementation reference |

The directory retains its original path so links inside the implementation
record continue to resolve. Its documents carry a notice that the architecture
is not the planned harness design.

## Structure

```text
projects/
├── active/ragenie-architecture/  # First-generation implementation record
├── completed/
├── lessons-learned/
├── templates/
└── work-logs/
```

New harness architecture records belong in a distinct project area after the
charter defines their scope. Do not overwrite the earlier implementation
record and make it appear to have described the new system all along.
