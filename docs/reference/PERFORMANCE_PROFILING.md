# Performance Profiling Results

Profiled 2026-03-07 on a clean test database (32 projects, ~200 tasks, 10 tags, 4 folders).
Actual task count at profiling time: 381 total, 376 active (accumulated from prior test runs).

## Benchmark Results

### get_tasks() by filter (3 iterations each, CV <1.5%)

| Operation | Mean | Items Returned |
|-----------|------|----------------|
| `get_tasks(project_id=X)` | 0.20s | varies |
| `get_tasks(inbox_only)` | 5.4s | 13 |
| `get_tasks(overdue)` | 16.6s | 8 |
| `get_tasks(flagged_only)` | 18.9s | 14 |
| `get_tasks(next_only)` | 41.9s | 67 |
| `get_tasks(query='bench')` | 80.8s | 39 |
| `get_tasks(available_only)` | >120s | TIMEOUT |

### get_projects() by options

| Operation | Mean | Overhead vs baseline |
|-----------|------|---------------------|
| `get_projects()` | 18.7s | baseline |
| `get_projects(+task_health)` | 43.6s | +133% |
| `get_projects(+last_activity)` | 28.8s | +54% |
| `get_projects(+full_notes)` | 18.7s | +0% (no-op) |
| `get_projects(all options)` | 53.6s | +187% |

### Other reads

| Operation | Mean | Items |
|-----------|------|-------|
| `get_folders()` | 0.68s | 5 |
| `get_tags()` | 1.01s | 25 |
| `get_perspectives()` | 0.17s | 24 |

### Write operations

| Operation | Mean |
|-----------|------|
| `create_task` | 0.66s |
| `update_task` | 0.65s |
| `delete_tasks` | 0.64s |
| `create_project` | 0.65s |
| `update_project` | 0.67s |
| `delete_projects` | 0.65s |

## Root Cause Experiments

### Experiment 1: `whose` clause vs manual iteration

OmniFocus evaluates `whose` clauses natively, avoiding per-task AppleScript overhead.

| Approach | Time | Speedup |
|----------|------|---------|
| `repeat with t in flattened tasks` + `if flagged of t` | 6.59s | 1x |
| `flattened tasks whose flagged is true` | 0.22s | **30x** |
| Manual loop + `name contains "bench"` | 6.54s | 1x |
| `whose name contains "bench"` | 0.32s | **20x** |
| `whose completed is false` (376/381 match) | 1.14s | — |
| `whose flagged is true and completed is false` | 0.22s | **30x** |

### Experiment 2: Per-task property read cost

Each AppleScript property read from OmniFocus costs ~17ms due to inter-process communication.

| Loop body (381 tasks) | Time | Per-task |
|-----------------------|------|----------|
| Empty loop | 0.17s | 0.4ms |
| 1 property (`id`) | 6.53s | 17ms |
| 4 properties | 25.69s | 67ms |
| 8 properties | 51.81s | 136ms |
| 8 properties + 2 dates | 63.85s | 168ms |
| `id` + `number of available tasks` | 12.90s | 34ms |
| `id` + `containing project` (3 reads) | 25.22s | 66ms |

The cost is linear in properties: ~17ms per property read per task.

### Experiment 3: String concatenation scaling

String concatenation is NOT a bottleneck at this scale.

| Items | Concat (`&`) | List + join |
|-------|-------------|-------------|
| 50 | 0.035s | 0.030s |
| 100 | 0.033s | 0.030s |
| 200 | 0.041s | 0.043s |
| 400 | 0.066s | 0.036s |

Both approaches are <100ms even at 400 items with ~300-char JSON per item.

### Experiment 4: `whose` + property extraction

| Approach | Time |
|----------|------|
| `whose flagged` + loop 8 props (14 tasks) | 2.06s |
| `whose flagged` + loop 14 props (14 tasks) | 3.20s |
| Manual loop 381 tasks + filter + 3 props | 7.53s |
| Bulk `id of (whose flagged)` | ERROR (mixed inbox/project types) |
| Current `get_tasks(flagged)` benchmark | 18.88s |

Bulk property reads (`id of flaggedTasks`) fail when the result set mixes inbox tasks and project tasks — different AppleScript classes. Looping over a pre-filtered set works and is fast.

## Conclusions

### The bottleneck is per-property IPC cost

Each property read from OmniFocus via AppleScript costs ~17ms. This is inter-process communication overhead between `osascript` and OmniFocus. The cost is:

```
total_time ≈ (num_tasks_iterated × num_properties_per_task × 17ms) + overhead
```

Current `get_tasks()` extracts 26 properties per task. For 381 tasks:
`381 × 26 × 17ms = 168s` — which explains the >120s timeout.

### What was NOT the bottleneck

- **Loop iteration itself**: 0.17s for 381 tasks (negligible)
- **String concatenation**: <100ms for 400 items (negligible)
- **JSON building**: Trivial compared to property reads

### `whose` clauses are the key optimization

OmniFocus evaluates `whose` natively — 20-30x faster than manual iteration with property checks. Combined with extracting properties only from the filtered set:

| Current | Optimized (projected) |
|---------|----------------------|
| 381 tasks × 26 props × 17ms = 168s | `whose` (0.2s) + 14 tasks × 14 props × 17ms = 3.5s |

### Optimization strategy

1. **Use `whose` clauses** to pre-filter tasks before the property extraction loop ✅ (implemented)
2. **Reduce properties extracted** — not all 27 are needed for every use case (future work)
3. **Pre-filter to small sets** — the per-task cost is fixed, so fewer tasks = proportionally faster
4. `get_projects()` nested loops (task_health, last_activity) should use similar pre-filtering

### Filters that map to `whose` clauses

| Filter | `whose` equivalent | Implemented? |
|--------|-------------------|--------|
| `flagged_only` | `whose flagged is true` | ✅ Yes |
| `overdue` | `whose due date < (current date)` | ✅ Yes |
| `next_only` | `whose next is true` | ✅ Yes |
| `completed` | `whose completed is false` | ✅ Yes (default) |
| `dropped_only` | `whose dropped is true` | ✅ Yes |
| `blocked_only` | `whose blocked is true` | ✅ Yes |
| `query` | `whose name contains "X" or note contains "X"` | ✅ Yes |
| `available_only` | Complex (dropped, blocked, deferred) | No (still times out) |
| `inbox_only` | Already uses `inbox tasks` (fast path) | N/A |
| `project_id` | Already uses scoped task source (fast path) | N/A |

## Post-Optimization Benchmark (whose-clause implementation)

Measured after implementing `whose` clause pre-filtering for get_tasks().
Same test database: 32 projects, ~200 tasks, 10 tags, 4 folders.

### get_tasks() before vs after

| Operation | Before | After | Speedup |
|-----------|--------|-------|---------|
| `get_tasks(flagged_only)` | 18.9s | **6.3s** | **3.0x** |
| `get_tasks(overdue)` | 16.6s | **3.6s** | **4.6x** |
| `get_tasks(query='bench')` | 80.8s | **16.3s** | **5.0x** |
| `get_tasks(next_only)` | 41.9s | **29.3s** | **1.4x** |
| `get_tasks(inbox_only)` | 5.4s | 5.4s | — (already fast path) |
| `get_tasks(project_id=X)` | 0.20s | 0.18s | — (already fast path) |
| `get_tasks(available_only)` | >120s | >120s | — (still times out) |
| `get_tasks()` (no filter) | >120s | >120s | — (still times out) |

### Why speedups are less than the 20-30x from whose experiments

The `whose` clause itself is fast (0.2s), but the remaining bottleneck is per-task property extraction.
With 27 properties × ~17ms per property × N matching tasks:

| Filter | Matching tasks | Expected time | Actual time |
|--------|---------------|--------------|-------------|
| overdue | 8 | 8 × 27 × 17ms = 3.7s | 3.6s ✓ |
| flagged | 14 | 14 × 27 × 17ms = 6.4s | 6.3s ✓ |
| query | 39 | 39 × 27 × 17ms = 17.9s | 16.3s ✓ |
| next | 67 | 67 × 27 × 17ms = 30.7s | 29.3s ✓ |

The optimization eliminates iteration over non-matching tasks. Further gains require reducing properties per task.
