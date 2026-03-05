# OmniFocus MCP Server

An MCP server bridging Claude and OmniFocus via AppleScript on macOS.

**Stack:** Python 3.10+, FastMCP, AppleScript (via `osascript`)
**Version:** v0.7.2 | **Tests:** 416 passing, 10 skipped + 8 integration | **Coverage:** 89%

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

**AppleScript round-trips are expensive.** Each `osascript` subprocess call takes 100-300ms minimum. Design for fewer calls with more data per call.

- `get_tasks()` with 188 tasks: ~2.3s baseline
- `get_projects()` with 33 projects: ~0.9s (after N+1 fix; was 7.6s before batch optimization)
- Individual task updates: ~200-400ms each
- Default timeout: 60s, max: 300s (configurable)

**Key optimization:** `_get_tasks_batch_for_filtering()` fetches all project tasks in one AppleScript call instead of N calls. This pattern should be used for any new filtering that crosses project boundaries.

**Conditional filter-first architecture:** `get_tasks()` detects whether selective filters (flagged, overdue, query, etc.) are active. If yes, it filters BEFORE extracting full properties. If no, it extracts first. This matters — wrong order can be 19x slower.

**Project task health:** `get_projects(include_task_health=True)` returns per-project task counts (remaining, available, overdue, deferred) in a single AppleScript call. Use this for project review workflows instead of N per-project `get_tasks()` calls.

**Conditional data loading:** `get_projects()` supports `include_last_activity=True` for expensive per-project calculations. Without this flag, `lastActivityDate` returns null (saves ~260ms for 33 projects).

## Database Safety

Destructive operations require `OMNIFOCUS_TEST_MODE=true` and `OMNIFOCUS_TEST_DATABASE=OmniFocus-TEST.ofocus` environment variables. Each destructive operation verifies the database name via AppleScript before proceeding. This prevents accidental production data loss during development.

## Branch Convention

`{type}/issue-{num}-{description}` — e.g., `feature/issue-42-batch-tags`, `fix/issue-99-timeout`

CHANGELOG.md is only updated on release branches, never on feature branches.

## Skills

Load these skills when working in their domains:

- **applescript-omnifocus** — OmniFocus AppleScript patterns, quirks, and workarounds
- **api-design** — API consolidation philosophy, decision tree for new functions, anti-patterns
- **performance-patterns** — Batch fetching, round-trip minimization, filter architecture
- **integration-testing** — Real-OmniFocus testing, test database setup, why mocks miss bugs

## Key Files

- `src/omnifocus_mcp/omnifocus_connector.py` — Core AppleScript client (~3250 lines)
- `src/omnifocus_mcp/server_fastmcp.py` — FastMCP server wrapping the connector (~1030 lines)
- `docs/reference/ARCHITECTURE.md` — Full API design rationale
- `docs/reference/APPLESCRIPT_GOTCHAS.md` — Complete AppleScript limitations reference
