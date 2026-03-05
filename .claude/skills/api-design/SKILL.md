---
name: api-design
description: Use BEFORE adding any new function, parameter, or endpoint to the OmniFocus MCP server. Also use when considering API changes, evaluating feature requests, or when tempted to create a specialized operation. Contains the decision tree that prevents API sprawl, the anti-pattern catalog, and the consolidation philosophy.
---

# OmniFocus MCP API Design

The API was consolidated from 40+ functions to 16 in October 2025. This consolidation is the project's most important architectural decision. Every new function request must pass through this decision tree.

## Decision Tree: Use BEFORE Adding Any Function

```
Can existing update_X() handle this?  (90% of cases: YES)
  |-- Setting a field? -> update_task() or update_project()
  |-- Example: Flag a task -> update_task(task_id, flagged=True)
  |-- Example: Complete a task -> update_task(task_id, completed=True)
  |-- Example: Move to project -> update_task(task_id, project_id=X)
  |
Can existing get_X() handle this with a parameter?  (9% of cases: YES)
  |-- Filtering data? -> Add parameter to get_tasks() or get_projects()
  |-- Example: Overdue tasks -> get_tasks(overdue=True)
  |-- Example: Flagged tasks -> get_tasks(flagged_only=True)
  |
Is this truly specialized logic?  (1% of cases: MAYBE)
  |-- Positioning? Recursive? UI state?
  |-- Example: reorder_task() has before/after logic that doesn't fit update_task()
  |
If NO to all three: You might need a new function. This is rare.
```

## Anti-Patterns (Never Do These)

### Field-Specific Setters
```python
# WRONG - creates API sprawl
set_due_date(task_id, date)
set_flag(task_id, True)
set_estimated_minutes(task_id, 30)
complete_task(task_id)
drop_task(task_id)
move_task(task_id, project_id)

# RIGHT - one comprehensive function
update_task(task_id, due_date=date, flagged=True, estimated_minutes=30)
update_task(task_id, completed=True)
update_task(task_id, status=TaskStatus.DROPPED)
update_task(task_id, project_id=project_id)
```

### Specialized Filter Functions
```python
# WRONG - each filter becomes a function
get_overdue_tasks()
get_stalled_projects()
get_flagged_tasks()
get_tasks_in_project(project_id)

# RIGHT - parameters on the existing function
get_tasks(overdue=True)
get_projects(stalled=True)
get_tasks(flagged_only=True)
get_tasks(project_id=project_id)
```

### String Booleans
```python
# WRONG
update_task(task_id, flagged="true")

# RIGHT
update_task(task_id, flagged=True)
```

### Formatted Text Returns
```python
# WRONG - returns human-readable string
def get_tasks():
    return "Task 1: Buy groceries\nTask 2: Write report"

# RIGHT - returns structured data
def get_tasks():
    return [{"id": "abc", "name": "Buy groceries"}, {"id": "def", "name": "Write report"}]
```

## Single vs Batch Update Rules

The API separates single-item and batch updates for safety:

- **`update_task()`** — single task, ALL fields available (including name, note)
- **`update_tasks()`** — multiple tasks, LIMITED fields (excludes name, note)

**Why?** Name and note require unique values per task. Batch-setting all tasks to the same name is almost always a mistake. The API prevents this by design.

Same pattern applies to projects: `update_project()` vs `update_projects()`.

## Union Types

`Union[str, list[str]]` is used ONLY for delete operations:
```python
def delete_tasks(task_ids: Union[str, list[str]]) -> dict
def delete_projects(project_ids: Union[str, list[str]]) -> dict
```

This allows convenient single-item deletes without wrapping in a list. Do NOT use this pattern for update operations — the single/batch distinction is intentional.

## No Upsert

Create and update are always separate operations. Never combine them into a "create or update if exists" pattern. This is an MCP design principle — the caller should know whether they're creating or updating.

## Adding a New Function Checklist

If you've passed the decision tree and genuinely need a new function:

1. Verify it doesn't fit in existing update_X() or get_X()
2. Write unit tests (mock AppleScript)
3. Write integration tests (real OmniFocus)
4. Write E2E tests (test MCP tool invocation in `test_e2e_mcp_tools.py`)
5. Implement in `omnifocus_connector.py`
6. Expose in `server_fastmcp.py`
7. Run `./scripts/check_client_server_parity.sh` to verify exposure
8. Update API documentation

## Full Design Rationale

For detailed worked examples, the complete anti-pattern catalog with explanations, and type signature templates, see `docs/reference/ARCHITECTURE.md`.
