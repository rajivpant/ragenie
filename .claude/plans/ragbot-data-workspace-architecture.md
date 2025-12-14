# RaGenie: ragbot-data Workspace Architecture Update

This document captures lessons learned and required changes from the ragbot project's November 2024 reorganization. Use this as context when implementing corresponding changes to RaGenie.

---

## Summary

The `ragbot-data` repository has been reorganized into a **workspace-based architecture** that RaGenie needs to understand and support. This includes:

1. New folder structure with `workspaces/` as the root
2. WHO/HOW/WHAT conceptual model for content organization
3. Workspace inheritance (child workspaces inherit from parents)
4. Recursive file loading from subdirectories

---

## New ragbot-data Structure

### Before (Legacy)

```
ragbot-data/
├── custom-instructions/    # Flat folder
├── curated-datasets/       # Flat folder
└── profiles.yaml           # Profile definitions
```

### After (Current)

```
ragbot-data/
├── config.yaml             # Global config (default_workspace: rajiv)
└── workspaces/
    ├── rajiv/              # Base workspace (personal identity)
    │   ├── workspace.yaml  # Workspace config
    │   ├── instructions/   # WHO - persona, behavioral rules
    │   │   └── identity.md
    │   ├── runbooks/       # HOW - task procedures
    │   │   ├── voice-and-style/
    │   │   │   └── persona.md
    │   │   ├── content-creation/
    │   │   │   ├── social-media.md
    │   │   │   ├── thought-leadership.md
    │   │   │   └── author-bios.md
    │   │   └── automation/
    │   │       ├── linkedin-engagement.md
    │   │       └── facebook-birthday.md
    │   └── datasets/       # WHAT - reference knowledge
    │       ├── personal-private/
    │       │   └── *.md files
    │       └── professional-public/
    │           └── *.md files
    ├── employer/           # Inherits from rajiv
    │   ├── workspace.yaml
    │   ├── instructions/
    │   ├── runbooks/
    │   └── datasets/
    ├── client-b/           # Inherits from employer (chain: client-b → employer → rajiv)
    ├── client-a/          # Inherits from employer
    ├── client-c/          # Inherits from rajiv
    └── ragenie/            # Inherits from rajiv
```

---

## Conceptual Model: WHO / HOW / WHAT

| Folder | Content Type | Conceptual Role |
|--------|--------------|-----------------|
| `instructions/` | Identity, persona, behavioral rules | **WHO** is the agent? |
| `runbooks/` | Task procedures, how-to guides | **HOW** does the agent do things? |
| `datasets/` | Reference data, knowledge bases | **WHAT** does the agent know? |

This model helps organize content by purpose rather than arbitrary categorization.

---

## Workspace Configuration

Each workspace has a `workspace.yaml` file:

```yaml
# workspaces/employer/workspace.yaml
name: My Employer
inherits_from:
  - rajiv
```

### Inheritance Chain

- `rajiv` — Base workspace (no parent)
- `employer` → `rajiv`
- `client-b` → `employer` → `rajiv`
- `client-a` → `employer` → `rajiv`
- `ragenie` → `rajiv`
- `client-c` → `rajiv`

When a workspace is selected, content is loaded from:
1. All parent workspaces (in order)
2. The selected workspace itself

---

## Critical Bugs Found and Fixed in ragbot

### Bug 1: String Iteration Instead of List Iteration

**Problem:** Python code was iterating over strings character-by-character.

```python
# BUG: custom_instructions is a STRING, not a list!
for custom_instruction in custom_instructions:
    history.append({"role": "system", "content": custom_instruction,})
```

When you iterate over a string in Python, you get each character:
```python
for char in "hello":  # yields 'h', 'e', 'l', 'l', 'o'
```

A 44KB string became 44,000+ single-character messages, causing token explosion.

**Fix:** Treat strings as strings, not lists:
```python
# If it's a string, don't iterate - use it directly
history = []  # or append the whole string as one item
```

### Bug 2: String.join() on Strings

**Problem:** Calling `"\n".join()` on a string inserts the separator between every character.

```python
# BUG: This doubles the content size!
system_content = "\n".join(custom_instructions) + "\n".join(curated_datasets)
```

`"\n".join("hello")` returns `"h\ne\nl\nl\no"`.

**Fix:** Concatenate strings directly:
```python
system_content = custom_instructions + "\n" + curated_datasets
```

### Bug 3: Non-Recursive File Loading

**Problem:** Files in subdirectories weren't being loaded.

```python
# Only loads immediate children, misses subdirectories
for filepath in glob.glob(os.path.join(path, "*")):
```

**Fix:** Use recursive glob:
```python
for filepath in glob.glob(os.path.join(path, "**/*"), recursive=True):
    if os.path.isfile(filepath):
        # process file
```

---

## RaGenie: Required Updates

### 1. Update File Watcher Config

**File:** `services/file-watcher/app/config.py`

Current exclude patterns:
```python
EXCLUDE_PATTERNS: tuple = (
    '.git',
    '__pycache__',
    '.DS_Store',
    'node_modules',
    '.pytest_cache',
)
```

**Add:**
```python
EXCLUDE_PATTERNS: tuple = (
    '.git',
    '__pycache__',
    '.DS_Store',
    'node_modules',
    '.pytest_cache',
    'archived',      # Skip archived folders
    'tmp',           # Skip temp folders
)
```

### 2. Update Document Categorization

**File:** `services/conversation-service/app/services/rag_retrieval.py`

Current categorization uses old folder names:
```python
if "custom-instructions" in doc.file_path:
    results["custom_instructions"].append(doc)
elif "curated-datasets" in doc.file_path:
    results["curated_datasets"].append(doc)
```

**Update to new structure:**
```python
# New folder names
if "/instructions/" in doc.file_path:
    results["instructions"].append(doc)
elif "/runbooks/" in doc.file_path:
    results["runbooks"].append(doc)
elif "/datasets/" in doc.file_path:
    results["datasets"].append(doc)
```

### 3. Add Workspace Support

RaGenie should understand workspaces to:
1. Allow filtering by workspace
2. Respect workspace inheritance
3. Support workspace-specific retrieval

**New schema concept:**
```python
class WorkspaceConfig:
    name: str
    inherits_from: List[str]
    instructions_paths: List[str]
    runbooks_paths: List[str]
    datasets_paths: List[str]
```

### 4. Update Document Metadata

When indexing documents, capture:
- `workspace`: Which workspace the document belongs to
- `content_type`: instructions | runbooks | datasets
- `parent_workspaces`: For inheritance-aware retrieval

### 5. Add Workspace Discovery

**New functionality to implement:**

```python
def discover_workspaces(data_root: Path) -> List[Workspace]:
    """Scan workspaces/ directory and parse workspace.yaml files."""
    workspaces = []
    workspaces_dir = data_root / "workspaces"

    for workspace_dir in workspaces_dir.iterdir():
        if workspace_dir.is_dir():
            config_file = workspace_dir / "workspace.yaml"
            if config_file.exists():
                config = yaml.safe_load(config_file.read_text())
                workspaces.append(Workspace(
                    name=config.get('name', workspace_dir.name),
                    dir_name=workspace_dir.name,
                    inherits_from=config.get('inherits_from', []),
                    path=workspace_dir
                ))

    return workspaces
```

---

## Implementation Checklist

### Phase 1: File Watcher Updates
- [ ] Add `archived` and `tmp` to exclude patterns
- [ ] Test that files in `workspaces/*/instructions/`, `workspaces/*/runbooks/`, `workspaces/*/datasets/` are detected
- [ ] Verify recursive scanning works for subdirectories like `datasets/personal-private/`

### Phase 2: Document Metadata
- [ ] Add `workspace` field to ragbot_documents table (or use JSON metadata)
- [ ] Add `content_type` field (instructions | runbooks | datasets)
- [ ] Update embedding worker to extract metadata from file paths

### Phase 3: Workspace Discovery
- [ ] Create workspace discovery function
- [ ] Parse workspace.yaml files
- [ ] Build inheritance graph

### Phase 4: RAG Retrieval Updates
- [ ] Update category detection for new folder names
- [ ] Add workspace-aware filtering
- [ ] Support inheritance-aware queries (retrieve from workspace + all parents)

### Phase 5: API Updates
- [ ] Add workspace list endpoint
- [ ] Add workspace filter to document endpoints
- [ ] Add workspace filter to RAG queries

---

## Key Lessons Learned

1. **Type Assumptions Are Dangerous**: Always check if a variable is a string or list before iterating. Python happily iterates over strings character-by-character.

2. **String Operations on Strings**: `"\n".join(string)` doesn't do what you think. It inserts newlines between every character.

3. **Test with Real Data**: The bugs only manifested with large files (44KB+). Small test files wouldn't trigger the token explosion.

4. **Debug Info is Crucial**: Adding character lengths and message counts to debug output helped identify the 7x token multiplication.

5. **Recursive Loading**: When organizing content into subdirectories, ensure your file loading code uses `recursive=True` or equivalent.

---

## Reference: ragbot helpers.py Functions

These functions from ragbot may be useful as reference for RaGenie:

### discover_workspaces()
```python
def discover_workspaces(data_root):
    """Discover all workspaces by scanning for workspace.yaml files."""
    workspaces_dir = os.path.join(data_root, 'workspaces')
    discovered = []

    for workspace_name in os.listdir(workspaces_dir):
        workspace_path = os.path.join(workspaces_dir, workspace_name)
        workspace_yaml = os.path.join(workspace_path, 'workspace.yaml')

        if os.path.isdir(workspace_path) and os.path.isfile(workspace_yaml):
            with open(workspace_yaml, 'r') as f:
                config = yaml.safe_load(f)

            discovered.append({
                'name': config.get('name', workspace_name),
                'path': workspace_path,
                'dir_name': workspace_name,
                'config': config
            })

    return sorted(discovered, key=lambda x: x['name'])
```

### resolve_workspace_paths()
```python
def resolve_workspace_paths(workspace, data_root, all_workspaces=None, resolved_chain=None):
    """Resolve a workspace's content paths including inherited workspaces."""
    # Prevents circular inheritance
    if resolved_chain is None:
        resolved_chain = set()

    if workspace['dir_name'] in resolved_chain:
        return {'instructions': [], 'datasets': []}
    resolved_chain.add(workspace['dir_name'])

    instructions = []
    datasets = []

    # First, resolve inherited workspaces (parent content comes first)
    for parent_name in workspace['config'].get('inherits_from', []):
        parent = next((w for w in all_workspaces if w['dir_name'] == parent_name), None)
        if parent:
            parent_paths = resolve_workspace_paths(parent, data_root, all_workspaces, resolved_chain.copy())
            instructions.extend(parent_paths['instructions'])
            datasets.extend(parent_paths['datasets'])

    # Then add this workspace's folders
    for folder in ['instructions', 'runbooks']:
        folder_path = os.path.join(workspace['path'], folder)
        if os.path.isdir(folder_path):
            instructions.append(folder_path)

    datasets_path = os.path.join(workspace['path'], 'datasets')
    if os.path.isdir(datasets_path):
        datasets.append(datasets_path)

    return {'instructions': instructions, 'datasets': datasets}
```

---

## Files Changed in ragbot (for reference)

| File | Change |
|------|--------|
| `src/helpers.py` | Recursive file loading, string concatenation fix |
| `src/ragbot.py` | Removed broken history loops |
| `src/ragbot_streamlit.py` | Removed broken history loop, added debug info |

---

## Testing Recommendations

1. **File Discovery Test**: Create a workspace with nested subdirectories and verify all files are indexed

2. **Workspace Inheritance Test**: Select a child workspace and verify content from parents is included

3. **Category Detection Test**: Verify documents are correctly categorized by content_type

4. **Token Count Test**: With debug logging, verify the actual token count matches expected (content size / ~4)

5. **Large File Test**: Test with files >10KB to catch any string iteration bugs
