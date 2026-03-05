---
name: performance-patterns
description: Use when optimizing OmniFocus MCP operations, diagnosing slow queries, adding new filtering logic, or modifying how data is fetched from OmniFocus. Covers the N+1 elimination pattern, batch fetching, conditional filter-first architecture, and known operation timings. Also use when adding any new get_* or filter parameter.
---

# OmniFocus MCP Performance Patterns

AppleScript round-trips via `osascript` are the dominant performance cost. Every optimization in this project reduces the number of subprocess calls.

## Known Operation Timings

| Operation | Time | Notes |
|-----------|------|-------|
| Single `osascript` call overhead | 100-300ms | Minimum cost per subprocess |
| `get_tasks()` — 188 tasks, no filters | ~2.3s | Baseline with full property extraction |
| `get_projects()` — 33 projects | ~0.9s | After N+1 fix |
| `get_projects()` — 33 projects (BEFORE fix) | ~7.6s | N+1 pattern: 1 call per project |
| Individual task update | 200-400ms | Single property change |
| `get_tasks()` with overdue filter | ~0.3s | Filter-first eliminates non-matching tasks early |
| Database safety check | ~100ms | Runs before every destructive operation |

**Timeout defaults:** 60s standard, 300s maximum. Configurable per operation.

## Pattern 1: Eliminate N+1 Queries

The most impactful optimization in this project. Before the fix, filtering projects by their tasks required one AppleScript call per project:

```python
# BAD: N+1 pattern (33 projects = 33 calls = 7.6s)
for project in projects:
    tasks = get_tasks(project_id=project.id)  # 230ms each!
    if meets_filter(tasks):
        results.append(project)

# GOOD: Batch pattern (33 projects = 1 call = 0.9s)
all_tasks_by_project = _get_tasks_batch_for_filtering()  # Single call
for project in projects:
    tasks = all_tasks_by_project.get(project.id, [])
    if meets_filter(tasks):
        results.append(project)
```

**Implementation:** `_get_tasks_batch_for_filtering()` fetches minimal data (id, projectId, dueDate) for ALL tasks in one AppleScript call, returning a `{projectId: [tasks]}` dictionary.

**Result:** 8.5x faster (7.6s -> 0.9s for 33 projects). Scales linearly — 500 projects would go from 115s to 13.5s.

**Apply this pattern** whenever you need to cross project boundaries for filtering or aggregation.

## Pattern 2: Conditional Filter-First Architecture

`get_tasks()` has a critical optimization: it detects whether "selective filters" are active and changes its execution order accordingly.

**Selective filters:** flagged_only, overdue, dropped_only, blocked_only, next_only, relative date ranges

```
IF selective filters active:
    1. Apply filters in AppleScript (cheap — just checking properties)
    2. Extract full properties only for matching tasks (expensive)
    Result: 82-88% faster for selective queries

IF no selective filters:
    1. Extract full properties for all tasks
    2. Apply post-processing filters in Python
    Result: Avoids overhead of empty filter checks
```

**Why this matters:** Extracting 27 properties per task is expensive. If you're only looking for 5 overdue tasks out of 188, filtering first means you only extract properties for 5 tasks instead of 188. This is a 19x speedup for selective queries.

**When adding new filter parameters:** Determine whether the filter is "selective" (likely to match a small subset) or "broad" (likely to match most tasks). Selective filters should go into the filter-first path.

## Pattern 3: Minimize Data Per Call

When you don't need all properties, fetch only what you need:

```applescript
-- GOOD: Fetch only what's needed for filtering
set taskData to {id of t, project of t, due date of t}

-- BAD: Fetch everything when you only need to filter
set taskData to {id, name, note, status, flagged, due date, defer date, ...}
```

`_get_tasks_batch_for_filtering()` demonstrates this — it fetches only id, projectId, and dueDate because that's all the project filtering logic needs.

## Pattern 4: Python Post-Processing vs AppleScript Filtering

Some filters are better applied in Python after fetching data:

- **Tag filtering (OR/NOT modes):** Done in Python via `_filter_tasks_by_tags()` because AppleScript tag matching is limited
- **Tag filtering (AND mode):** Done in AppleScript for efficiency, then verified in Python for consistency
- **Date range filtering:** Simpler to compare ISO dates in Python than to build date comparison logic in AppleScript

**Rule of thumb:** Use AppleScript filtering when it eliminates data transfer (fewer tasks to serialize). Use Python filtering when the logic is complex or when the data is already fetched.

## Anti-Patterns

### Repeated Safety Checks
Each destructive operation calls `_verify_database_safety()` which runs an AppleScript to fetch the database name (~100ms). For batch operations that call multiple destructive methods, this check runs multiple times unnecessarily. Consider caching the result for the session.

### Large AppleScript Blocks
Very large AppleScript strings (1000+ lines) can be slow to parse. If a script grows unwieldy, consider splitting into two calls: one for data retrieval, one for data processing, with Python bridging them.

### Unnecessary Property Extraction
Don't add properties to the "always extract" list unless they're commonly needed. Each additional property adds serialization overhead for every task in every query.

## Profiling Infrastructure

The project has performance profiling tests in `tests/test_profile_performance.py` and test data generation scripts in `scripts/local/setup_profiling_data.sh`.

To profile a change:
1. Switch to test database: `./scripts/local/switch_to_test_db.sh`
2. Generate test data: `./scripts/local/setup_profiling_data.sh`
3. Run profiling: `pytest tests/test_profile_performance.py -v`
4. Switch back: `./scripts/local/switch_to_prod_db.sh`

## Detailed Analysis

For the complete performance analysis including Phase 1/Phase 2 optimization results and empirical data, see:
- `docs/performance/GET_TASKS_PERFORMANCE_ANALYSIS.md`
- `docs/performance/PERFORMANCE_OPTIMIZATION_SUMMARY.md`
