# OmniFocus MCP Server

A comprehensive, fast, reliable, and agent-friendly MCP server for OmniFocus on macOS.

## Why This Server

### Comprehensive

22 tools covering projects, tasks, folders, tags, perspectives, and focus. Full CRUD on projects and tasks with batch operations, 14 filter types on task queries, and date management including recurrence (RRULE read/write).

### Fast

Sub-second reads on filtered queries, even with hundreds of tasks in the database.

| Operation | Time | Database |
|-----------|------|----------|
| Get flagged tasks | 0.88s | ~200 tasks |
| Get overdue tasks | 0.72s | ~200 tasks |
| Search tasks by keyword | 1.61s | ~200 tasks |
| Get all tasks (unfiltered) | 5.65s | ~200 tasks |
| Get all projects | 1.78s | 32 projects |
| Create or update a task | 0.6-0.7s | — |

Full profiling data: [PERFORMANCE_PROFILING.md](docs/reference/PERFORMANCE_PROFILING.md)

### Reliable

91% code coverage from 782 unit tests. 138 integration tests run against real OmniFocus covering task, project, and tag lifecycles, filtering, hierarchy, dates, recurrence, and review workflows.

### Agent-Friendly

47-scenario blind eval suite scores 94/94 — agents that have never seen OmniFocus can correctly use every tool from descriptions alone. Server instructions teach GTD concepts (task states, project types, sequential dependencies, review cycles) so agents make informed decisions, not just API calls.

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

## Contributing

Bug reports and feature requests are welcome via [GitHub Issues](https://github.com/s-morgan-jeffries/omnifocus-mcp/issues). See [CONTRIBUTING.md](docs/guides/CONTRIBUTING.md) for development workflow and pull request guidelines.

## License

MIT
