# OmniFocus MCP Server - Architecture Decision Record

**Last Updated:** 2025-10-17

## Overview

This document captures the architectural principles and design decisions for the OmniFocus MCP Server API. When adding new functionality, follow these principles to maintain consistency and quality.

## Core Design Principles

### 1. Minimize Tool Call Overhead

**Principle:** Each MCP tool call has overhead (user approval, network round-trip). Minimize the number of calls needed to accomplish common tasks.

**Application:**
- Comprehensive update functions (`update_task()`, `update_project()`) allow updating multiple fields in a single call
- Instead of `set_due_date()`, `set_flag()`, `add_tag()` as separate calls, one `update_task()` call can do all three

**Example:**
```python
# ❌ Bad: 3 separate calls
update_task(task_id, due_date="2025-10-20")
update_task(task_id, flagged=True)
add_tag_to_task(task_id, "urgent")

# ✅ Good: 1 call
update_task(task_id, due_date="2025-10-20", flagged=True, add_tags=["urgent"])
```

### 2. Prevent User Errors

**Principle:** API design should make incorrect usage difficult or impossible.

**Application:**
- Separate `update_task()` (single, all fields) from `update_tasks()` (batch, limited fields)
- Batch update only includes fields that make sense to apply uniformly
- Excluded from batch: `task_name`, `note` (require unique values per task)

**Why:** Prevents accidentally renaming 10 tasks to the same name or overwriting unique notes.

**Example:**
```python
# ❌ Would be dangerous if allowed
update_tasks([id1, id2, id3], task_name="New Name")  # All get same name!

# ✅ Safe batch operations
update_tasks([id1, id2, id3], flagged=True)  # Flag multiple tasks
update_tasks([id1, id2, id3], add_tags=["urgent"])  # Tag multiple tasks
```

### 3. Consistency Over Convenience

**Principle:** Maintain consistent patterns across the API even if it requires slightly more typing.

**Application:**
- Use `project_name` and `task_name` (not just `name`) for consistency
- All batch delete operations use plural names: `delete_tasks()`, `delete_projects()`
- All get operations return structured data (`list[dict]`) not formatted text

**Why:** Predictable patterns reduce cognitive load and make the API easier to learn.

### 4. Union Types for Variable Quantities

**Principle:** Operations that work on "one or many" items should use `Union[str, list[str]]` rather than having separate singular/batch functions.

**Application:**
- `delete_tasks(task_ids: Union[str, list[str]])` handles both single and batch deletion
- No separate `delete_task()` function needed

**When NOT to use Union types:**
- Update operations - we DO separate `update_task()` and `update_tasks()` because they have different field sets

**Example:**
```python
# ✅ Both work with same function
delete_tasks("task-123")                    # Delete one
delete_tasks(["task-123", "task-456"])     # Delete many
```

### 5. MCP-First Design

**Principle:** Design for Model Context Protocol tool calling, not general API design.

**Application:**
- Keep create/update separate (don't merge into "upsert" pattern) - clearer tool descriptions
- Each tool should have a single, clear purpose
- Tool descriptions should make intent obvious to foundation models

**Why:** While "upsert" patterns are common in APIs, they add complexity for AI tool selection. "Create a task" vs "Update a task" is clearer than "Create or update a task depending on whether you provide an ID."

### 6. Structured Returns

**Principle:** Return structured data (dicts, lists) rather than formatted text strings.

**Application:**
- Get operations return `list[dict]` not formatted strings
- Batch operations return dicts with counts and failures
- Single operations return dicts with success status and updated fields

**Why:** Easier for MCP clients to parse and use programmatically.

## Decision Patterns

### When to Add a New Function vs Parameter

**Add a parameter when:**
- It's a filter or option on existing operation
- It modifies behavior of existing operation
- Examples: `include_full_notes`, `project_id` filter on `get_tasks()`

**Add a new function when:**
- It's a fundamentally different operation
- It has specialized logic that can't be generalized
- Example: `reorder_task()` - specialized positioning logic

**Decision tree:**
```
New functionality needed?
├─ Is it a filter/option on existing operation?
│  └─ → Add parameter to existing function
├─ Is it setting a single field?
│  └─ → Add to update() function
├─ Can it be done client-side?
│  └─ → Don't add (example: get_stalled_projects)
└─ Is it truly specialized logic?
   └─ → Consider new function (rare)
```

### When to Have Batch Version

**Create batch version when:**
- Applying the same value to multiple items makes sense
- Examples: flag multiple tasks, move tasks to same project, tag multiple items

**Don't create batch version when:**
- Items need unique values (names, notes)
- Operation is already singular (get, create)

**Pattern:**
- Single update: `update_task(task_id: str, ...)` - ALL fields
- Batch update: `update_tasks(task_ids: Union[str, list[str]], ...)` - LIMITED fields

### When to Use Enum vs String

**Use Enum when:**
- Value set is constrained and known
- Examples: `ProjectStatus`, `TaskStatus`
- Benefits: Type safety, IDE autocomplete, validation

**Use String when:**
- Value set is open-ended
- Examples: `task_name`, `note`, `project_id`

**Implementation:**
```python
class ProjectStatus(Enum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    DONE = "done"
    DROPPED = "dropped"
```

Consider accepting both enum values and strings for MCP client flexibility.

## Worked Examples

### Example 1: Why `update_task()` and `update_tasks()` are separate

**Question:** Why not just have `update_tasks()` that accepts both single and multiple IDs?

**Answer:** Because they have different field sets.

- `update_task()`: Can update `task_name`, `note`, and all other fields
- `update_tasks()`: Cannot update `task_name` or `note` (require unique values)

**Scenario:**
```python
# User wants to update name - must be unique
update_task("task-123", task_name="New unique name")

# User wants to flag multiple tasks - same value is fine
update_tasks(["task-123", "task-456"], flagged=True)
```

### Example 2: Why we deleted `complete_task()`

**Question:** Why delete a dedicated completion function?

**Answer:** Completing a task is just setting `completed=True`. No special logic needed.

**Before:**
```python
complete_task(task_id)  # Dedicated function
```

**After:**
```python
update_task(task_id, completed=True)  # General field update
```

**Benefit:** Fewer functions to maintain, and you can combine completion with other updates:
```python
update_task(task_id, completed=True, add_tags=["done"], note="Finished!")
```

### Example 3: Why `reorder_task()` is its own function

**Question:** Why not consolidate reordering into `update_task()`?

**Answer:** Reordering has specialized logic (before/after relationships) that doesn't fit the general update pattern.

**Why specialized:**
- Requires two task IDs (the task being moved and the reference task)
- Has constraints (both tasks must be at same level)
- Uses exclusive parameters (`before_task_id` OR `after_task_id`, not both)

This is complex enough to warrant its own function with clear semantics.

## Anti-Patterns

### ❌ Field-Specific Setters

**Don't do this:**
```python
set_due_date(task_id, date)
set_estimated_minutes(task_id, minutes)
set_flag(task_id, flagged)
```

**Do this instead:**
```python
update_task(task_id, due_date=date, estimated_minutes=minutes, flagged=True)
```

**Why:** Reduces API surface area and tool call overhead.

### ❌ Client-Side Filters as Functions

**Don't do this:**
```python
get_stalled_projects(days_inactive=30)  # Specialized filter
get_overdue_tasks()  # Can be done with date comparison
```

**Do this instead:**
```python
# Client fetches all projects and filters by last_activity_date
projects = get_projects()
stalled = [p for p in projects if days_since(p.last_activity) > 30]
```

**Why:** Reduces API complexity. Only include filters that require server-side logic.

### ❌ Upsert Pattern

**Don't do this:**
```python
create_or_update_task(task_id=None, ...)  # If ID provided, update; else create
```

**Do this instead:**
```python
create_task(...)  # Clear: creating new task
update_task(task_id, ...)  # Clear: updating existing task
```

**Why:** More explicit for MCP tool calling. FM knows exactly what operation it's performing.

### ❌ String Types for Booleans or Enums

**Don't do this:**
```python
update_task(task_id, flagged="true")  # String
update_project(project_id, status="active")  # String without constraints
```

**Do this instead:**
```python
update_task(task_id, flagged=True)  # Boolean
update_project(project_id, status=ProjectStatus.ACTIVE)  # Enum
```

**Why:** Type safety, validation, IDE support.

### ❌ Formatted Text Returns

**Don't do this:**
```python
def get_tasks():
    return "Task 1: Buy milk\nTask 2: Walk dog\n..."  # Formatted string
```

**Do this instead:**
```python
def get_tasks():
    return [
        {"id": "1", "name": "Buy milk", ...},
        {"id": "2", "name": "Walk dog", ...}
    ]  # Structured data
```

**Why:** Easier for MCP clients to parse and use.

## Checklist for New Functions

When adding new functionality, ask:

### 1. Is this a new entity type?
- [ ] Follow the CRUD pattern: `create_X()`, `get_X()`, `update_X()`, `update_Xs()`, `delete_Xs()`
- [ ] Use consistent naming: `{entity}_name` for name fields
- [ ] Return structured data from get operations

### 2. Is this an operation on existing entity?
- [ ] Can it be a parameter on existing function? → Add parameter
- [ ] Is it setting a single field? → Add to `update()` function
- [ ] Is it a filter? → Add to `get()` function
- [ ] Is it truly specialized? → Consider new function (rare)

### 3. Is it batch-safe?
- [ ] Would same value make sense for all items? → Include in `update_Xs()`
- [ ] Needs unique values per item? → Keep in `update_X()` only

### 4. Error handling
- [ ] Single operations: Return dict with success/error
- [ ] Batch operations: Return dict with counts and failures list
- [ ] Parameter conflicts: Raise `ValueError` with clear message

### 5. Type safety
- [ ] Use `Enum` for constrained value sets
- [ ] Use `Union[str, list[str]]` for variable quantity operations
- [ ] Use proper types: `bool` not `"true"/"false"`, `int` not string

### 6. Documentation
- [ ] Clear function description
- [ ] All parameters documented
- [ ] Return format specified
- [ ] Examples for complex operations

## Common Scenarios

### Adding a New Field to Tasks

**Scenario:** OmniFocus adds a new "energy_level" field.

**Decision:** Add it to both `update_task()` and `update_tasks()` since setting the same energy level for multiple tasks makes sense.

```python
# Single update
update_task(task_id, energy_level="high")

# Batch update  
update_tasks([id1, id2], energy_level="low")
```

### Adding a New Filter to Get Operations

**Scenario:** Need to filter tasks by energy level.

**Decision:** Add parameter to `get_tasks()`.

```python
get_tasks(energy_level="high")
```

### Adding Complex Business Logic

**Scenario:** Need to "archive" a project (move to archive folder, mark as done, update note).

**Decision:** This can be done with existing `update_project()` call. No new function needed.

```python
update_project(
    project_id,
    folder_path="Archive",
    status=ProjectStatus.DONE,
    note=f"{existing_note}\n\nArchived on {today}"
)
```

### Adding Specialized Operation

**Scenario:** Need to duplicate a task with all its subtasks.

**Decision:** This requires complex logic (reading task, creating new task, recursively duplicating subtasks). Warrant a new `duplicate_task()` function.

## Version History

- **2025-10-17:** Initial architecture document based on API redesign from 40 to 16 functions

## References

- See `API-REFERENCE.md` for complete API specification
- See `.clinerules` for Claude Code enforcement rules