# OmniFocus MCP Server

The most tested, safest, and best-optimized MCP server for OmniFocus on macOS.

> **Note:** This is a personal project. You're welcome to fork, clone, and adapt it for your own use, but I'm not accepting pull requests or feature requests. Issues are used for internal tracking.

## Why This Server

### Full API Coverage

22 tools covering every entity type — projects, tasks, folders, tags, perspectives, focus. Full CRUD with batch operations, comprehensive filtering (14 filter types on tasks alone), and date management across all entity types. Consolidated from 40+ specialized functions into a clean, composable API.

### Fast

Sub-second reads on filtered queries, even with hundreds of tasks. Native `whose` clause pre-filtering (20-30x faster than iteration) combined with batch property extraction eliminates the per-task IPC bottleneck that plagues naive AppleScript implementations.

| Operation | Time | Dataset |
|-----------|------|---------|
| Flagged tasks | 0.88s | ~200 tasks |
| Overdue tasks | 0.72s | ~200 tasks |
| Text search | 1.61s | ~200 tasks |
| All tasks (unfiltered) | 5.65s | ~200 tasks |
| All projects | 1.78s | 32 projects |
| Write operations | 0.6-0.7s | single item |

Full profiling data: [PERFORMANCE_PROFILING.md](docs/reference/PERFORMANCE_PROFILING.md)

### Reliable

782 unit tests and 138 integration tests against real OmniFocus. Database safety system prevents accidental production data modification during development. AppleScript injection hardening with dedicated string escapers for both AppleScript and OmniAutomation contexts.

### Agent-Friendly

46-scenario blind eval suite scores 92/92 — agents that have never seen OmniFocus can correctly use every tool from descriptions alone. Server instructions teach GTD concepts (task states, project types, sequential dependencies, review cycles) so agents make informed decisions, not just API calls.

## Tools (22)

### Projects (5)
- **get_projects** — filter by ID, query, status; includes dates, review info, task health, stalled detection
- **create_project** — with folder placement, dates, review interval, project type
- **update_project** — all properties: name, note, status, dates, folder, review settings
- **update_projects** — batch update (status, dates, folder, review settings)
- **delete_projects** — single or batch

### Tasks (6)
- **get_tasks** — 14 filter types: by ID, project, parent, tags, status, dates, flags, text search, inbox
- **create_task** — with dates, tags, flags, estimated time, parent task, sequential
- **update_task** — all properties including recurrence (RRULE), tags (replace/add/remove), hierarchy
- **update_tasks** — batch update (dates, flags, tags, status, project)
- **delete_tasks** — single or batch
- **reorder_task** — position relative to siblings (before/after)

### Folders (2)
- **get_folders** — hierarchy with paths
- **create_folder** — with optional parent

### Tags (4)
- **get_tags** — with status and mutual exclusivity info
- **create_tag** — with parent nesting and exclusivity
- **update_tag** — name, status, exclusivity
- **delete_tags** — single or batch

### Perspectives (2)
- **get_perspectives** — list with type info
- **switch_perspective** — navigate to perspective

### Navigation (2)
- **set_focus** — focus on projects/folders or clear
- **get_focus** — current focus state

## Prerequisites

- macOS with OmniFocus installed
- Python 3.10+
- UV package manager (recommended) or pip

## Installation

```bash
git clone https://github.com/s-morgan-jeffries/omnifocus-mcp.git
cd omnifocus-mcp
git checkout v0.9.2  # Latest stable release

# Using UV (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install -e .

# Or using pip
python3 -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## Configuration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "omnifocus": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/omnifocus-mcp",
        "run",
        "omnifocus-mcp"
      ]
    }
  }
}
```

### Other MCP Clients

```bash
python -m omnifocus_mcp.server_fastmcp
```

Communicates via stdin/stdout using the MCP protocol.

## Permissions

macOS will prompt for:
- Accessibility access (to control OmniFocus via AppleScript)
- Automation permissions for OmniFocus

## Development

```bash
make test                  # 782 unit tests (~2 min)
make test-integration      # 138 tests against real OmniFocus
make test-prod             # OmniAutomation tests (production DB)
```

See [CONTRIBUTING.md](docs/guides/CONTRIBUTING.md) for development workflow and TDD requirements.

## License

MIT
