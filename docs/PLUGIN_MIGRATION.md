# Plugin Migration Guide: Performance Optimizations

This document describes API changes in the OmniFocus MCP server that the
personal-productivity plugin should adopt.

## Summary

Three additive parameter changes. No functions were removed or renamed.
All changes are backward-compatible — existing calls continue to work.

---

## 1. `get_projects(include_task_health=True)` — High Priority

### What changed

`get_projects()` now accepts `include_task_health=True`, which adds per-project
task health data to each project in the response:

- `remainingCount` — non-completed, non-dropped tasks
- `availableCount` — tasks that are not blocked, not deferred, not completed
- `overdueCount` — tasks with due dates in the past
- `deferredCount` — tasks with defer dates in the future
- `hasDeferredOnly` — True if remaining > 0 but available = 0

### Why it matters

The `/project-review` sweep currently calls `get_tasks(project_id=X)` for each
project to assess health. With 33 projects, that's 33+ AppleScript round-trips
at ~2.3s each = 76+ seconds. With `include_task_health=True`, one call returns
everything needed for the sweep in ~2-4 seconds.

### Plugin changes needed

**`/project-review` sweep mode** — Replace the per-project task fetching loop:

```
# Before (slow — N+1 calls):
projects = get_projects()
for project in projects:
    tasks = get_tasks(project_id=project.id, available_only=True, next_only=True)
    # assess health from tasks...

# After (fast — 1 call):
projects = get_projects(include_task_health=True)
for project in projects:
    if project.availableCount > 0:
        health = "On Track"
    elif project.hasDeferredOnly:
        health = "Appropriately Scheduled"
    elif project.remainingCount == 0:
        health = "No Remaining Tasks"
    else:
        health = "Stuck"
```

The deep-dive mode (single project with argument) can still use
`get_tasks(project_id=X)` to get full task details.

---

## 2. `get_projects(include_last_activity=True)` — Low Priority

### What changed

`lastActivityDate` (the most recent task creation or completion date per project)
is no longer computed by default. It now requires `include_last_activity=True`.

Without the flag, `lastActivityDate` returns `null` in the response.

### Why it matters

Computing `lastActivityDate` iterates all tasks (including completed) of every
project. This adds ~260ms to every `get_projects()` call even when nobody reads
the field.

### Plugin changes needed

If the plugin reads `lastActivityDate` from project data, add the flag:

```
get_projects(include_last_activity=True)
```

If the plugin doesn't use `lastActivityDate`, no changes needed.

---

## 3. `query` filter optimization — No Plugin Changes

### What changed

`get_tasks(query="...")` now filters by name/note in AppleScript instead of
Python. Tasks that don't match are skipped before extracting their 27 properties.

### Why it matters

Targeted lookups (like `/daily-wrapup` searching for tasks by name) are faster,
especially with large task databases.

### Plugin changes needed

None. Same API, same behavior, just faster.

---

## Health field reference

When `include_task_health=True`, each project dict includes:

| Field | Type | Description |
|-------|------|-------------|
| `remainingCount` | int | Tasks not completed and not dropped |
| `availableCount` | int | Tasks that are actionable right now |
| `overdueCount` | int | Tasks past their due date |
| `deferredCount` | int | Tasks with future defer dates |
| `hasDeferredOnly` | bool | All remaining tasks are blocked/deferred |

These map directly to the project review health categories:
- `availableCount > 0` → On Track
- `hasDeferredOnly` → Appropriately Scheduled
- `remainingCount == 0` → No Remaining Tasks (consider completing project)
- else → Stuck (needs next action or status change)
