# OmniFocus MCP Server

An MCP server bridging Claude and OmniFocus via AppleScript on macOS.

**Stack:** Python 3.10+, FastMCP, AppleScript (via `osascript`)
**Version:** v0.8.0 | **Tests:** 438 unit, 128 integration/E2E, 25 benchmark/profiling | **Coverage:** 89%

## Commands

```bash
make test                  # Unit tests (~2min, mocked AppleScript)
make test-integration      # Real OmniFocus tests (~30s, requires test DB)
make test-e2e              # End-to-end MCP tool tests (requires test DB)
./scripts/check_complexity.sh       # Cyclomatic complexity check
./scripts/check_client_server_parity.sh  # Verify all client functions are exposed in server
./scripts/check_version_sync.sh     # Version consistency across files
```

**Running the server:** `uv run python -m omnifocus_mcp.server_fastmcp` or via Claude Desktop config.

## API Surface (17 functions: 16 core + UI navigation)

The API was consolidated from 40+ functions to 16 in October 2025. This is intentional — resist adding new functions.

**Projects (5):** create_project, get_projects, update_project, update_projects, delete_projects
**Tasks (6):** create_task, get_tasks, update_task, update_tasks, delete_tasks, reorder_task
**Folders (2):** create_folder, get_folders
**Tags (1):** get_tags
**Perspectives (2):** get_perspectives, switch_perspective
**Navigation (1):** set_focus

## Core API Principles

1. **Comprehensive update functions over specialized operations** — no `set_due_date()`, use `update_task(task_id, due_date=X)`
2. **No field-specific setters or getters** — `update_task` handles all fields, `get_tasks` handles all filters
3. **Separate single/batch updates** — batch excludes name/note (require unique values)
4. **Union types for deletes only** — `Union[str, list[str]]` for delete operations, NOT for updates
5. **No upsert pattern** — create and update are always separate
6. **Structured returns** — always `dict` or `list[dict]`, never formatted text strings

## AppleScript Gotchas (these cause real bugs)

**Variable naming conflicts:** Never use variable names that match OmniFocus properties. Using `name`, `note`, `status`, `flagged` etc. as AppleScript variable names creates silent conflicts where OmniFocus reads the property instead. Always prefix: `taskName`, `taskNote`, `projectStatus`.

**Rich text notes:** OmniFocus stores notes as rich text internally. Reading `note of task` returns plain text, but setting `note of task` replaces rich text with plain text. There is no workaround — document this limitation.

**Recurring task completion:** Use `mark complete` (AppleScript command), NOT `set completed to true` (property). The command creates the next occurrence; the property just marks the current one done without spawning the next recurrence.

**JSON helpers duplicated 9x:** AppleScript has no imports/modules. Every AppleScript block that returns JSON must include its own helper functions. This is intentional.

**Date format:** AppleScript uses `"March 5, 2026 5:00:00 PM"` format. The connector handles ISO 8601 conversion via `_iso_to_applescript_date()`.

**String escaping:** Always use `_escape_applescript_string()` for user-provided text. Unescaped quotes break AppleScript blocks silently.

## Performance Constraints

**The bottleneck is per-property IPC cost.** Each AppleScript property read from OmniFocus costs ~17ms (inter-process communication). With 26 properties per task, iterating 381 tasks = ~168s. This single fact explains nearly all performance issues. See `docs/reference/PERFORMANCE_PROFILING.md` for full experiment data.

**`whose` clauses are 20-30x faster than manual iteration.** OmniFocus evaluates `whose` natively:
- `flattened tasks whose flagged is true`: 0.22s
- Manual loop checking `flagged of t`: 6.59s
- Current `get_tasks(flagged)` (loop + 26 props): 18.9s

**What is NOT a bottleneck:** Loop iteration itself (0.17s for 381 tasks), string concatenation (<100ms for 400 items), JSON building.

**Current baselines** (32 projects, ~381 tasks — see profiling doc for full table):
- `get_tasks(project_id)`: 0.20s | `get_tasks(flagged)`: 18.9s | `get_tasks(query)`: 80.8s
- `get_projects()`: 18.7s | `get_perspectives()`: 0.17s | Write ops: 0.63-0.67s

Default timeout: 60s, max: 300s (configurable).

**Optimization path:** Use `whose` to pre-filter, then extract properties only from the small result set. Projected: `get_tasks(flagged)` from 18.9s to ~3.5s.

**Project task health:** `get_projects(include_task_health=True)` returns per-project task counts in a single AppleScript call. +133% overhead due to nested per-project task loops.

**Conditional data loading:** `get_projects()` supports `include_last_activity=True` for expensive per-project calculations (+54% overhead).

## Database Safety

Destructive operations require `OMNIFOCUS_TEST_MODE=true` and `OMNIFOCUS_TEST_DATABASE=OmniFocus-TEST.ofocus` environment variables. Each destructive operation verifies the database name via AppleScript before proceeding. This prevents accidental production data loss during development.

## Branch Convention

`{type}/issue-{num}-{description}` — e.g., `feature/issue-42-batch-tags`, `fix/issue-99-timeout`

CHANGELOG.md is only updated on release branches, never on feature branches.

## Skills

Load these skills when working in their domains:

- **release** — Full release workflow: milestone check, version bump, changelog, validation, tagging, PR
- **applescript-omnifocus** — OmniFocus AppleScript patterns, quirks, and workarounds
- **api-design** — API consolidation philosophy, decision tree for new functions, anti-patterns
- **performance-patterns** — Batch fetching, round-trip minimization, filter architecture
- **integration-testing** — Real-OmniFocus testing, test database setup, why mocks miss bugs

## Key Files

- `src/omnifocus_mcp/omnifocus_connector.py` — Core AppleScript client (~3350 lines)
- `src/omnifocus_mcp/server_fastmcp.py` — FastMCP server wrapping the connector (~1050 lines)
- `docs/reference/ARCHITECTURE.md` — Full API design rationale
- `docs/reference/APPLESCRIPT_GOTCHAS.md` — Complete AppleScript limitations reference
