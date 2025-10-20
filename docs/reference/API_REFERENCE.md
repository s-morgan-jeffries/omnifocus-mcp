# OmniFocus MCP Server - API Reference

**Current Version:** v0.6.1 (API Redesign - IMPLEMENTED)
**Total MCP Tools:** 16 (reduced from 40+)

This document shows the complete API surface that Claude Desktop sees when connecting to the OmniFocus MCP server. Each tool is exposed via the Model Context Protocol and can be invoked by Claude.

**Last Updated:** 2025-10-20
**Latest Change:** v0.6.1 renamed `omnifocus_client` → `omnifocus_connector` (no API changes)

## ⚠️ Version History Notice

**v0.6.0 (Current - October 2025):** Major API redesign completed
- Consolidated 40+ functions → 16 core functions
- Removed 26 deprecated functions (functionality preserved in new API)
- All proposals from this document have been **IMPLEMENTED ✅**
- See [CHANGELOG.md](../../CHANGELOG.md) for migration guide

**Historical Note:** This document originally proposed the API redesign. All "Enhanced proposed signature" sections below have now been implemented and are the current production API.

---

## Table of Contents

**Current API (v0.6.0 - 16 Core Functions):**
- [Projects](#projects) (5 functions) - `create`, `get`, `update`, `update_batch`, `delete`
- [Tasks](#tasks) (6 functions) - `create`, `get`, `update`, `update_batch`, `delete`, `reorder`
- [Folders](#folders) (2 functions) - `create`, `get`
- [Tags](#tags) (1 function) - `get`
- [Perspectives](#perspectives) (2 functions) - `get`, `switch`

**Deprecated Functions (Removed in v0.6.0):**
- [Deprecated Functions](#deprecated-functions-removed-in-v060) - 26 functions consolidated into core API

---

## Implementation Status (v0.6.0)

### ✅ Implemented Functions (16 Core Functions)

All "Enhanced proposed signature" sections in this document have been **FULLY IMPLEMENTED** as of v0.6.0.

**Projects (5):**
- ✅ `create_project()` - With `review_interval_weeks` parameter
- ✅ `get_projects()` - Enhanced with `project_id`, `include_full_notes` parameters
- ✅ `update_project()` - Comprehensive single-project update
- ✅ `update_projects()` - NEW: Batch update (safe fields only)
- ✅ `delete_projects()` - Union type: accepts single ID or list

**Tasks (6):**
- ✅ `create_task()` - Replaces `add_task()` and `create_inbox_task()`
- ✅ `get_tasks()` - Enhanced with `task_id`, `parent_task_id`, `include_full_notes` parameters
- ✅ `update_task()` - Comprehensive single-task update
- ✅ `update_tasks()` - NEW: Batch update (safe fields only)
- ✅ `delete_tasks()` - Union type: accepts single ID or list
- ✅ `reorder_task()` - Specialized positioning logic

**Folders (2):**
- ✅ `create_folder()` - With optional parent path
- ✅ `get_folders()` - Returns folder hierarchy

**Tags (1):**
- ✅ `get_tags()` - Returns all available tags

**Perspectives (2):**
- ✅ `get_perspectives()` - Returns available perspectives
- ✅ `switch_perspective()` - UI control function

### ❌ Removed Functions (26 Deprecated)

See [Deprecated Functions](#deprecated-functions-removed-in-v060) section below for full list and migration paths.

---

## Projects

### `create_project()`

**Description:** Create a new project in OmniFocus.

**Parameters:**
- `name: str` - The name of the project
- `note: Optional[str] = None` - Optional note/description (plain text only)
- `folder_path: Optional[str] = None` - Optional folder path (e.g., "Work > Clients")
- `sequential: bool = False` - If True, tasks must be completed in order

**Returns:** Success message with project ID and configuration details

**Example:**
```
name: "Q4 Marketing Campaign"
folder_path: "Work > Marketing"
sequential: false
note: "Focus on social media and email outreach"
```

**PROPOSED: KEEP as separate function** - While merging with `update_project()` would reduce API surface area, keeping them separate provides clearer intent for MCP tool calling. An AI assistant can more easily reason about "create a project" vs "update a project" as distinct operations.

**Enhanced proposed signature:**
```python
create_project(
    name: str,  # REQUIRED
    folder_path: Optional[str] = None,
    note: Optional[str] = None,
    sequential: bool = False,
    status: ProjectStatus = ProjectStatus.ACTIVE,  # Enum with default
    review_interval_weeks: Optional[int] = None
)
```

**Type safety recommendations:**
- Use `Enum` for `status` parameter to provide type safety and IDE autocomplete
- Recommended enum definition: `class ProjectStatus(Enum): ACTIVE = "active"; ON_HOLD = "on_hold"; DONE = "done"; DROPPED = "dropped"`
- Example: `class ProjectStatus(Enum): ACTIVE = "active"; ON_HOLD = "on_hold"; ...`

---

### `delete_project()`

**Description:** Delete a project from OmniFocus.

**WARNING:** This permanently deletes the project and all its tasks. Cannot be undone.

**Parameters:**
- `project_id: str` - The ID of the project to delete

**Returns:** Success message confirming project deletion

**PROPOSED: DELETE - merged into `delete_projects()`** - The batch function accepts `Union[str, list[str]]` to handle single or multiple deletions in one function.

---

### `delete_projects()`

**Description:** Delete multiple projects from OmniFocus in a single operation (batch operation for efficiency).

**WARNING:** This permanently deletes the projects and all their tasks. Cannot be undone.

**Parameters:**
- `project_ids: list[str]` - List of project IDs to delete

**Returns:** Summary of deleted projects with count and any errors encountered

**PROPOSED: KEEP and enhance to handle single or multiple IDs** - Accept `Union[str, list[str]]` for flexibility.

**Enhanced proposed signature:**
```python
delete_projects(
    project_ids: Union[str, list[str]]  # Single ID or list of IDs
) -> dict
```

**Return format:**
```python
{
    "deleted_count": int,
    "failed_count": int,
    "deleted_ids": list[str],
    "failures": [{"project_id": str, "error": str}, ...]
}
```

---

### `drop_project()`

**Description:** Drop a project (mark as on hold indefinitely).

Dropping a project is different from deleting it - the project remains in OmniFocus but is marked as on hold and won't appear in active project lists.

**Parameters:**
- `project_id: str` - The ID of the project to drop

**Returns:** Success message confirming project was dropped

**PROPOSED: DELETE - consolidated into `update_project()`** - Dropping is setting project status. Use `update_project(project_id, status="dropped")` for consistency.

---

### `drop_projects()`

**Description:** Drop multiple projects (mark as on hold indefinitely) in a single operation.

**Parameters:**
- `project_ids: list[str]` - List of project IDs to drop

**Returns:** Summary of dropped projects with count and any errors encountered

**PROPOSED: DELETE - consolidated into `update_project()`** - Status changes should go through the unified `update_project()` function. Use `update_project(project_ids, status="dropped")` for consistency.

---

### `get_project()`

**Description:** Get details for a specific project by its ID.

**Parameters:**
- `project_id: str` - The ID of the project to retrieve

**Returns:** Formatted text with detailed project information including:
- ID, Name, Status, Folder, Type (Sequential/Parallel)
- Timestamps (Created, Modified, Last Activity)
- Statistics (Total/Completed/Remaining tasks, Progress %)
- Review metadata (Interval, Last Reviewed, Next Review)
- Note preview

**PROPOSED: DELETE** - This is just `get_projects()` with an ID filter. Add an `id` or `project_id` parameter to `get_projects()` instead. Having separate "get one" vs "get many" functions unnecessarily doubles the API surface.

---

### `get_projects()`

**Description:** Retrieve ALL active projects with full details and hierarchy, optionally filtered by search query.

**Parameters:**
- `on_hold_only: bool = False` - If True, only return projects with "on hold" status
- `query: Optional[str] = None` - Optional search term to filter by name, note, or folder path (case-insensitive)

**Returns:** Formatted text with project list (one per line with ID, name, folder, status, creation date, and note preview)

**PROPOSED: KEEP and enhance** - Add filtering and note control parameters. Return structured data for easier parsing.

**Enhanced proposed signature:**
```python
get_projects(
    project_id: Optional[str] = None,  # Filter to specific project (replaces get_project)
    on_hold_only: bool = False,
    query: Optional[str] = None,
    include_full_notes: bool = False  # Return full notes instead of truncated preview
) -> list[dict]
```

**Returns:** List of project dictionaries with all project data. When `include_full_notes=False`, notes are truncated to preview length. When `include_full_notes=True`, complete note content is included.

**Performance note:** Using `include_full_notes=True` without appropriate filtering can result in large data transfers. Recommended to use with specific `project_id` or narrow `query` filters when full notes are needed.

**Enhancements:**
- `project_id` parameter filters to a specific project, replacing the need for `get_project()`
- `include_full_notes` flag returns complete note content instead of truncated previews, replacing the need for `get_note()` for projects
- Returns structured data (list of dicts) instead of formatted text for easier parsing by MCP clients

---

### `get_stalled_projects()`

**Description:** Get active projects with no recent task activity.

Helps identify projects that may need attention or cleanup during GTD reviews.

**Parameters:**
- `days_inactive: int = 30` - Minimum days of inactivity to consider a project stalled
- `min_task_count: Optional[int] = None` - Minimum number of tasks a project must have to be included

**Returns:** Projects sorted by inactivity (most stale first) with last activity date, days inactive, and task count. Projects with no activity ever are included.

**PROPOSED: DELETE** - This is specialized application logic that can be implemented client-side. Fetch all projects with `get_projects()`, then filter and sort by last activity date. Embedding business logic like "what counts as stalled" in the API reduces flexibility.

---

### `set_project_status()`

**Description:** Change a project's status to active, on hold, done, or dropped.

**Parameters:**
- `project_id: str` - The ID of the project
- `status: str` - The status to set: "active", "on_hold", "done", or "dropped"

**Returns:** Success message confirming status change

**Raises:** ValueError if project not found or status is invalid.

**PROPOSED: DELETE - consolidated into `update_project()`** - Status is just another project field. Use `update_project(project_id, status=ProjectStatus.ACTIVE)` for consistency with all other field updates.

**Type safety recommendations:**
- Use `Enum` for `status` parameter instead of string
- Define `ProjectStatus` enum: `class ProjectStatus(Enum): ACTIVE = "active"; ON_HOLD = "on_hold"; DONE = "done"; DROPPED = "dropped"`
- This provides compile-time type checking and IDE autocomplete
- Consider accepting both enum values and strings for MCP client flexibility

---

### `update_project()`

**Description:** Update an existing project in OmniFocus.

**Parameters:**
- `project_id: str` - The ID of the project to update
- `name: Optional[str] = None` - New project name (optional)
- `note: Optional[str] = None` - New note content (optional). **WARNING:** Removes rich text formatting
- `sequential: Optional[bool] = None` - True for sequential, False for parallel (changed from string to bool for consistency)

**Returns:** Success message listing all updated fields

**PROPOSED: KEEP as separate function and greatly enhance** - While merging with `create_project()` would reduce API surface area, keeping them separate makes tool calling clearer for MCP clients. Each function has a single, well-defined purpose. This becomes the comprehensive update function for ALL project field changes, consolidating operations from set_project_status, set_review_interval, and mark_project_reviewed. Rename `name` to `project_name` for consistency with `task_name`.

**Enhanced proposed signature:**
```python
update_project(
    project_id: str,  # Single project only
    project_name: Optional[str] = None,  # Renamed for consistency
    folder_path: Optional[str] = None,  # For moving between folders
    note: Optional[str] = None,
    sequential: Optional[bool] = None,
    status: Optional[ProjectStatus] = None,  # Replaces set_project_status()
    review_interval_weeks: Optional[int] = None,  # Replaces set_review_interval()
    last_reviewed: Optional[str] = None  # Replaces mark_project_reviewed() (ISO format)
) -> dict
```

**Return format:**
```python
{
    "success": bool,
    "project_id": str,
    "updated_fields": list[str],  # Names of fields that were changed
    "error": Optional[str]
}
```

**Type safety:**
- Use `Enum` for `status` parameter to provide type safety and IDE autocomplete
- Recommended enum definition: `class ProjectStatus(Enum): ACTIVE = "active"; ON_HOLD = "on_hold"; DONE = "done"; DROPPED = "dropped"`
- The `ProjectStatus` enum should be consistent with `create_project()`
- Consider accepting both enum values and strings, converting strings to enums internally for flexibility with MCP client calls

**Error handling:**
- On success: Returns dict with `success=True`, `project_id`, and `updated_fields`
- On failure: Returns dict with `success=False`, `project_id`, and `error` message
- Does not throw exceptions for project-specific errors (e.g., project not found, invalid field values)
- May throw `ValueError` for parameter conflicts

**Consistency fixes needed:**
- Change `sequential` parameter from `Optional[str]` to `Optional[bool]` to match `create_project()`
- Add `folder_path` parameter to enable moving projects between folders
- Add `status`, `review_interval_weeks`, and `last_reviewed` parameters to consolidate related functions

**Key benefit:** Allows updating multiple fields in a single tool call, dramatically reducing overhead when multiple changes are needed.

---

### `update_projects()` (NEW)

**Description:** Update multiple projects with the same field values in a single operation. Use this for operations that make sense to apply uniformly across multiple projects (like changing status, moving to folders, or setting review intervals). For unique updates to individual projects (like names or notes), use `update_project()` instead.

**Proposed signature:**
```python
update_projects(
    project_ids: Union[str, list[str]],  # Single ID or list of IDs
    status: Optional[ProjectStatus] = None,  # Set same status for all
    folder_path: Optional[str] = None,  # Move all to same folder
    sequential: Optional[bool] = None,  # Make all sequential or parallel
    review_interval_weeks: Optional[int] = None,  # Set same review interval
    last_reviewed: Optional[str] = None  # Mark all as reviewed at same time (ISO format)
) -> dict
```

**Return format:**
```python
{
    "updated_count": int,
    "failed_count": int,
    "updated_ids": list[str],
    "failures": [{"project_id": str, "error": str}, ...]
}
```

**Fields NOT included (use `update_project()` for these):**
- `project_name` - Each project should have a unique name
- `note` - Each project should have a unique note

**Key benefit:** Efficiently apply the same changes to multiple projects in one call (e.g., "move these projects to Archive folder", "set all to monthly review", "mark these projects as reviewed").

---

### `update_tasks()` (NEW)

**Description:** Update multiple tasks with the same field values in a single operation. Use this for operations that make sense to apply uniformly across multiple tasks (like flagging, tagging, or moving). For unique updates to individual tasks (like names or notes), use `update_task()` instead.

**Proposed signature:**
```python
update_tasks(
    task_ids: Union[str, list[str]],  # Single ID or list of IDs
    flagged: Optional[bool] = None,
    status: Optional[TaskStatus] = None,
    completed: Optional[bool] = None,
    project_id: Optional[str] = None,  # Move all to same project
    parent_task_id: Optional[str] = None,  # Make all subtasks of same parent
    tags: Optional[list[str]] = None,  # Full replacement - set exact tag list
    add_tags: Optional[list[str]] = None,  # Add these tags to all tasks
    remove_tags: Optional[list[str]] = None,  # Remove these tags from all tasks
    due_date: Optional[str] = None,  # Set same due date for all
    defer_date: Optional[str] = None,  # Set same defer date for all
    estimated_minutes: Optional[int] = None  # Set same estimate for all
) -> dict
```

**Return format:**
```python
{
    "updated_count": int,
    "failed_count": int,
    "updated_ids": list[str],
    "failures": [{"task_id": str, "error": str}, ...]
}
```

**Fields NOT included (use `update_task()` for these):**
- `task_name` - Each task should have a unique name
- `note` - Each task should have a unique note

**Conflict resolution:**
- **Hierarchy conflicts:** If both `parent_task_id` and `project_id` provided, raise `ValueError`
- **Tag conflicts:** If `tags` provided along with `add_tags`/`remove_tags`, raise `ValueError`

**Key benefit:** Efficiently apply the same changes to multiple tasks in one call (e.g., "flag these 5 tasks", "move these 10 tasks to Project X", "add 'urgent' tag to these tasks").

---

## Tasks

### `create_task()` (formerly `add_task()`)

**Description:** Add a new task to a specific OmniFocus project with full properties support.

**Parameters:**
- `project_id: str` - The ID of the project to add the task to
- `task_name: str` - The name/title of the task
- `note: Optional[str] = None` - Optional note/description (plain text only)
- `due_date: Optional[str] = None` - Due date in ISO 8601 format (e.g., '2025-10-15')
- `defer_date: Optional[str] = None` - Defer date in ISO 8601 format
- `flagged: bool = False` - Whether to flag the task
- `tags: Optional[str] = None` - JSON array string of tag names (e.g., '["Computer", "Work"]')

**Returns:** Success message with task name, project, and all configured properties

**Example:**
```
project_id: "proj-123"
task_name: "Review Q3 budget"
due_date: "2025-10-20"
flagged: true
tags: '["Finance", "High Priority"]'
```

**PROPOSED: KEEP, rename to `create_task()`, and merge with `create_inbox_task()`** - Make `project_id` optional. When omitted or `None`, task goes to inbox. This eliminates the need for a separate inbox creation function and provides consistent naming with `create_project()` and `create_folder()`.

**Enhanced proposed signature:**
```python
create_task(
    task_name: str,  # REQUIRED - only truly required parameter
    project_id: Optional[str] = None,  # OPTIONAL - inbox if omitted and no parent
    parent_task_id: Optional[str] = None,  # OPTIONAL - makes it a subtask
    note: Optional[str] = None,
    due_date: Optional[str] = None,
    defer_date: Optional[str] = None,
    flagged: bool = False,  # OPTIONAL with default False
    tags: Optional[list[str]] = None,
    estimated_minutes: Optional[int] = None
)
```

**Conflict resolution behavior:**
- **Hierarchy conflicts:** If both `parent_task_id` and `project_id` are provided, raise a `ValueError` with message like "Cannot specify both parent_task_id and project_id - parent task already determines the project." This makes conflicts explicit and forces correct API usage.

---

### `complete_task()`

**Description:** Mark a task as completed in OmniFocus.

**Parameters:**
- `task_id: str` - The ID of the task to complete

**Returns:** Success message confirming task completion

**PROPOSED: DELETE - consolidated into `update_task()`** - Task completion is simply setting the completed field. Use `update_task(task_id, completed=True)` instead of a dedicated function. This reduces API surface and tool call overhead.

---

### `complete_tasks()`

**Description:** Mark multiple tasks as completed in a single operation (batch operation for efficiency).

**Parameters:**
- `task_ids: list[str]` - List of task IDs to complete

**Returns:** Summary with count of completed tasks and any errors encountered

**PROPOSED: DELETE - consolidated into `update_task()`** - Completion is a field update operation. Use `update_task(task_ids, completed=True)` for better consistency and to avoid API proliferation. This also allows updating completion status along with other fields in a single call.

---

### `delete_task()`

**Description:** Permanently remove a task from OmniFocus.

**WARNING:** Cannot be undone.

**Parameters:**
- `task_id: str` - The ID of the task to delete

**Returns:** Success message confirming task deletion

**PROPOSED: DELETE - merged into `delete_tasks()`** - The batch function will accept `Union[str, list[str]]` to handle both single and multiple task deletions.

---

### `delete_tasks()`

**Description:** Delete multiple tasks from OmniFocus in a single operation.

**WARNING:** Permanently deletes tasks. Cannot be undone.

**Parameters:**
- `task_ids: list[str]` - List of task IDs to delete

**Returns:** Summary of deleted tasks with count and any errors encountered

**PROPOSED: KEEP and enhance to handle single or multiple IDs** - Accept `Union[str, list[str]]` for maximum flexibility.

**Enhanced proposed signature:**
```python
delete_tasks(
    task_ids: Union[str, list[str]]  # Single ID or list of IDs
) -> dict
```

**Return format:**
Always return structured format for consistency:
```python
{
    "deleted_count": int,
    "failed_count": int,
    "deleted_ids": list[str],
    "failures": [{"task_id": str, "error": str}, ...]
}
```

**Error handling:**
- Attempt to delete all tasks
- Continue on individual failures
- Report all successes and failures in return value

---

### `drop_task()`

**Description:** Drop a task (mark as on hold indefinitely).

Dropping is different from deleting - the task remains in OmniFocus but won't appear in available task lists.

**Parameters:**
- `task_id: str` - The ID of the task to drop

**Returns:** Success message confirming task was dropped

**PROPOSED: DELETE - consolidated into `update_task()`** - Dropping a task is setting its status. Use `update_task(task_id, status="dropped")` instead. This is consistent with how other status changes are handled.

---

### `drop_tasks()`

**Description:** Drop multiple tasks in a single operation.

**Parameters:**
- `task_ids: list[str]` - List of task IDs to drop

**Returns:** Summary of dropped tasks with count and any errors encountered

**PROPOSED: DELETE - consolidated into `update_task()`** - Dropping tasks is a status change operation. Use `update_task(task_ids, status="dropped")` for consistency. This allows combining status changes with other field updates in a single call.

---

### `get_task()`

**Description:** Get details for a specific task by its ID.

**Parameters:**
- `task_id: str` - The ID of the task to retrieve

**Returns:** Formatted text with detailed task information including:
- ID, Name, Project, Completed status
- Flags (Dropped, Blocked, Available, Next, Flagged)
- Dates (Due, Defer)
- Timestamps (Created, Modified, Completed, Dropped)
- Hierarchy (Parent Task, Subtask Count, Sequential, Position)
- Tags, Estimated Minutes, Note

**PROPOSED: DELETE** - This is just `get_tasks()` with a `task_id` filter. Add an `id` or `task_id` parameter to `get_tasks()` instead of maintaining separate "get one" vs "get many" functions.

---

### `get_tasks()`

**Description:** Get tasks from OmniFocus with optional filtering.

**Parameters:**
- `project_id: Optional[str] = None` - Optional project ID to filter tasks
- `flagged_only: bool = False` - Only return flagged tasks
- `include_completed: bool = False` - Include completed tasks (default: False)
- `available_only: bool = False` - Only return available tasks (not blocked or deferred)
- `overdue: bool = False` - Only return overdue tasks
- `dropped_only: bool = False` - Only return dropped tasks
- `blocked_only: bool = False` - Only return blocked tasks
- `next_only: bool = False` - Only return next tasks
- `tag_filter: Optional[list[str]] = None` - List of tag names (task must have all)
- `query: Optional[str] = None` - Search term to filter by name or note (case-insensitive)
- `inbox_only: bool = False` - Only return inbox tasks

**Returns:** Formatted text with task list including ID, name, project, due date, tags, and completion status

**PROPOSED: KEEP and enhance** - Add filtering and note control parameters. Return structured data for easier parsing.

**Enhanced proposed signature:**
```python
get_tasks(
    task_id: Optional[str] = None,  # Filter to specific task (replaces get_task)
    project_id: Optional[str] = None,
    parent_task_id: Optional[str] = None,  # Filter by parent (replaces get_subtasks)
    flagged_only: bool = False,
    include_completed: bool = False,
    available_only: bool = False,
    overdue: bool = False,
    dropped_only: bool = False,
    blocked_only: bool = False,
    next_only: bool = False,
    tag_filter: Optional[list[str]] = None,
    query: Optional[str] = None,
    inbox_only: bool = False,
    include_full_notes: bool = False  # Return full notes instead of truncated preview
) -> list[dict]
```

**Returns:** List of task dictionaries with all task data. When `include_full_notes=False`, notes are truncated to preview length. When `include_full_notes=True`, complete note content is included.

**Performance note:** Using `include_full_notes=True` without appropriate filtering can result in large data transfers. Recommended to use with specific `task_id`, `project_id`, or narrow `query` filters when full notes are needed.

**Enhancements:**
- `task_id` parameter filters to a specific task, replacing the need for `get_task()`
- `parent_task_id` parameter filters by parent task, replacing the need for `get_subtasks()`
- `include_full_notes` flag returns complete note content instead of truncated previews, replacing the need for `get_note()` for tasks
- Returns structured data (list of dicts) instead of formatted text for easier parsing by MCP clients

---

### `get_subtasks()`

**Description:** Get all subtasks (child tasks) of a given task.

**Parameters:**
- `task_id: str` - The ID of the parent task

**Returns:** Formatted text with list of child tasks or message if task has no subtasks

**PROPOSED: DELETE** - This is just `get_tasks(parent_task_id=task_id)`. Add a `parent_task_id` filter parameter to `get_tasks()` instead of maintaining a separate function for this common filtering pattern.

---

### `move_task()`

**Description:** Move a task to a different project or to inbox.

**Parameters:**
- `task_id: str` - The ID of the task to move
- `project_id: Optional[str] = None` - The ID of the destination project, or omit to move to inbox

**Returns:** Success message with task name and new location (project or inbox)

**PROPOSED: DELETE - consolidated into `update_task()`** - Moving a task is updating its project_id or parent_task_id. Use `update_task()` for all hierarchy changes.

---

### `move_tasks()`

**Description:** Move multiple tasks to a different project or inbox in a single operation.

**Parameters:**
- `task_ids: list[str]` - List of task IDs to move
- `project_id: Optional[str] = None` - Destination project ID, or omit for inbox

**Returns:** Summary of moved tasks with count, destination, and any errors encountered

**PROPOSED: DELETE - consolidated into `update_task()`** - Moving is updating the task's location in the hierarchy. Use `update_task(task_ids, project_id=X)` or `update_task(task_ids, parent_task_id=Y)` for moves. This consolidates all update operations into one function.

---

### `reorder_task()`

**Description:** Move a task before or after another task to change its position.

**Parameters:**
- `task_id: str` - The ID of the task to move
- `before_task_id: Optional[str] = None` - Move the task before this task
- `after_task_id: Optional[str] = None` - Move the task after this task

**Note:** Exactly one of `before_task_id` or `after_task_id` must be provided.

**Returns:** Success message confirming the task was reordered

**PROPOSED: KEEP** - This is specialized positioning logic that can't be easily replicated through general property updates. Task ordering is complex enough to warrant its own function, especially for sequential projects where order matters.

---

### `set_parent_task()`

**Description:** Set the parent task of a task (make it a subtask) or make it root-level.

**Parameters:**
- `task_id: str` - The ID of the task to modify
- `parent_task_id: Optional[str] = None` - The ID of the parent task, or omit to make root-level

**Returns:** Success message confirming the parent-child relationship

**PROPOSED: DELETE - consolidated into `update_task()`** - Setting a parent is updating the parent_task_id field. Use `update_task(task_id, parent_task_id=X)` for hierarchy changes. Setting to None makes it root-level.

---

### `update_task()`

**Description:** Update an existing task in OmniFocus.

**Parameters:**
- `task_id: str` - The ID of the task to update
- `name: Optional[str] = None` - New task name (optional)
- `note: Optional[str] = None` - New note content (optional). **WARNING:** Removes rich text formatting
- `due_date: Optional[str] = None` - New due date in ISO 8601 format, or empty string to clear
- `defer_date: Optional[str] = None` - New defer date in ISO 8601 format, or empty string to clear
- `flagged: Optional[str] = None` - "true" to flag, "false" to unflag, or omit to leave unchanged

**Returns:** Success message listing all updated fields

**PROPOSED: KEEP and enhance** - Add parameters for all updatable fields: `parent_task_id` (replacing both `set_parent_task()` and `move_task()` - when set, the task inherits the parent's project automatically), `estimated_minutes` (replacing `set_estimated_minutes()`), `completed` (replacing `complete_task()`), `status` (replacing `drop_task()`), and `tags` operations. Note: `project_id` parameter should only be used when `parent_task_id` is null/omitted, as setting a parent automatically determines the project. This prevents conflicts and reflects the actual task hierarchy.

**Enhanced proposed signature:**
```python
update_task(
    task_id: str,  # REQUIRED
    task_name: Optional[str] = None,
    project_id: Optional[str] = None,  # For moving to root-level in project
    parent_task_id: Optional[str] = None,  # For making subtask
    note: Optional[str] = None,
    due_date: Optional[str] = None,  # ISO format or empty string to clear
    defer_date: Optional[str] = None,  # ISO format or empty string to clear
    flagged: Optional[bool] = None,  # Changed from string to bool
    tags: Optional[list[str]] = None,  # Full replacement
    add_tags: Optional[list[str]] = None,  # Incremental add
    remove_tags: Optional[list[str]] = None,  # Incremental remove
    estimated_minutes: Optional[int] = None,
    completed: Optional[bool] = None,
    status: Optional[TaskStatus] = None  # Use enum for type safety
)
```

**Type safety recommendations:**
- Use `Enum` for `status` parameter (e.g., `TaskStatus` with values like ACTIVE, DROPPED, etc.)
- Consider defining enums consistently across the codebase
- Accept both enum values and strings for MCP client flexibility

**Conflict resolution behavior:**
- **Hierarchy conflicts:** If both `parent_task_id` and `project_id` are provided, raise a `ValueError` with message like "Cannot specify both parent_task_id and project_id - parent task already determines the project." This makes conflicts explicit and forces correct API usage.
- **Tag conflicts:** If `tags` (full replacement) is provided along with `add_tags` or `remove_tags`, raise a `ValueError` with message like "Cannot specify both tags and add_tags/remove_tags - use tags for full replacement or add_tags/remove_tags for incremental changes." This prevents ambiguous tag operations.

---

### `add_tag_to_task()`

**Description:** Add a tag to an existing task in OmniFocus.

**Parameters:**
- `task_id: str` - The ID of the task to tag
- `tag_name: str` - The name of the tag to add (tag must already exist)

**Returns:** Success message confirming tag was added to task

**PROPOSED: DELETE - consolidated into `update_task()`** - Adding tags is updating the task's tag list. Use `update_task(task_id, add_tags=[tag_name])` for adding tags incrementally.

---

### `add_tag_to_tasks()`

**Description:** Add a tag to multiple tasks in a single operation.

**Parameters:**
- `task_ids: list[str]` - List of task IDs to tag
- `tag_name: str` - The name of the tag to add (tag must already exist)

**Returns:** Summary with count of tasks tagged and any errors encountered

**PROPOSED: DELETE - consolidated into `update_task()`** - Tag operations are field updates. Use `update_task(task_ids, add_tags=[tag_name])` for consistency. This allows tagging along with other updates in a single call.

---

### `remove_tag_from_tasks()`

**Description:** Remove a tag from multiple tasks in a single operation.

**Parameters:**
- `task_ids: list[str]` - List of task IDs to remove tag from
- `tag_name: str` - The name of the tag to remove

**Returns:** Summary with count of tasks untagged and any errors encountered

**PROPOSED: DELETE - consolidated into `update_task()`** - Tag removal is a field update. Use `update_task(task_ids, remove_tags=[tag_name])` for consistency and to allow combining tag operations with other updates.

---

### `set_estimated_minutes()`

**Description:** Set the estimated time for a task.

**Parameters:**
- `task_id: str` - The ID of the task
- `minutes: int` - Estimated time in minutes (0 to clear estimate)

**Returns:** Success message with task name and new time estimate

**PROPOSED: DELETE - consolidated into `update_task()`** - Estimated time is just another task field. Use `update_task(task_id, estimated_minutes=X)` for consistency with all other field updates.

---

## Folders

### `create_folder()`

**Description:** Create a new folder in OmniFocus.

**Parameters:**
- `name: str` - The name of the folder to create
- `parent_path: Optional[str] = None` - Optional parent folder path (e.g., "Work" or "Work > Clients")

**Returns:** Success message with folder ID and full path

**Example:**
```
name: "Q4 Projects"
parent_path: "Work"
```

**PROPOSED: KEEP** - Core functionality for folder management. Folders are a distinct organizational structure that warrant dedicated creation.

---

### `get_folders()`

**Description:** Get all folders from OmniFocus with their hierarchy.

**Returns:** Formatted hierarchical list of all folders with indentation showing nesting

**PROPOSED: KEEP** - Core read functionality for understanding folder structure. Essential for navigation and organization.

---

## Tags

### `get_tags()`

**Description:** Retrieve all available tags from OmniFocus with their names.

**Returns:** Formatted list of all tag names (one per line)

**PROPOSED: KEEP** - Core read functionality. Users need to discover available tags before using them in filters or assignments.

---

## Review & GTD

### `get_projects_due_for_review()`

**Description:** Get all projects that are due for review (GTD weekly review workflow).

Projects are considered due if their next review date is today or in the past.

**Returns:** Formatted list of projects needing review with last review date and next review date

**PROPOSED: DELETE** - This is just `get_projects()` filtered by `next_review_date <= today`. This application logic can easily be done client-side. Embedding review workflow logic in the API reduces flexibility for users with different GTD practices.

---

### `mark_project_reviewed()`

**Description:** Mark a project as reviewed (updates last review date and calculates next review date).

**Parameters:**
- `project_id: str` - The ID of the project

**Returns:** Success message with updated review dates

**Note:** This updates the last review date to today, and OmniFocus automatically calculates the next review date based on the project's review interval.

**PROPOSED: DELETE - consolidated into `update_project()`** - Marking as reviewed is updating the last_reviewed date. Use `update_project(project_id, last_reviewed=today)` for consistency.

---

### `set_review_interval()`

**Description:** Set the review interval for a project (GTD workflow).

**Parameters:**
- `project_id: str` - The ID of the project
- `interval_weeks: int` - Review interval in weeks (e.g., 1 for weekly, 4 for monthly)

**Returns:** Success message with new review interval and next review date

**PROPOSED: DELETE - consolidated into `update_project()`** - Review interval is just another project field. Use `update_project(project_id, review_interval_weeks=X)` for consistency.

---

## Perspectives

### `get_perspectives()`

**Description:** Get all perspective names from OmniFocus.

Perspectives are custom views that filter and organize your tasks and projects.

**Returns:** Formatted list of all perspective names (one per line)

**PROPOSED: KEEP** - Core read functionality. Users need to discover available perspectives before they can switch to them.

---

### `switch_perspective()`

**Description:** Switch the front window to a different perspective.

**Parameters:**
- `perspective_name: str` - Name of the perspective to switch to

**Returns:** Success message confirming perspective switch

**PROPOSED: KEEP** - This is UI control functionality that can't be achieved through data operations. Switching perspectives is a distinct action that changes the application view state.

---

## Notes

### `add_note()`

**Description:** Append a note to an OmniFocus project.

**Parameters:**
- `project_id: str` - The ID of the project to add the note to
- `note_text: str` - The text to append to the project's notes

**Returns:** Success message confirming note was appended

**Note:** This appends to existing notes, does not replace them.

**PROPOSED: DELETE** - Appending can be done client-side: fetch existing note with `get_projects(project_id, include_full_notes=True)`, concatenate with new text, then `update_project(project_id, note=combined_text)`. No need for a dedicated append function.

---

### `get_note()`

**Description:** Get the full note content from a project or task.

**Parameters:**
- `item_id: str` - The ID of the project or task
- `item_type: str = "project"` - Either "project" or "task" (default: "project")

**Returns:** The full note content as plain text (may be empty if no note exists)

**Note:** Only plain text is returned. Rich text formatting is not accessible via AppleScript.

**PROPOSED: DELETE** - Notes are already returned by `get_project()` and `get_task()`. Instead of a separate function, add `include_full_notes: bool = False` parameter to `get_projects()` and `get_tasks()` to optionally return full notes instead of truncated previews.

---

## Inbox

### `create_inbox_task()`

**Description:** Create a new task directly in the OmniFocus inbox (quick capture).

Use this for rapid task capture without assigning to a project.

**Parameters:**
- `task_name: str` - The name/title of the task
- `note: Optional[str] = None` - Optional note/description (plain text only)
- `due_date: Optional[str] = None` - Optional due date in ISO 8601 format
- `flagged: bool = False` - Whether to flag the task (default: False)

**Returns:** Success message with task ID and configured properties

**PROPOSED: DELETE - merged into `create_task()`** - The main task creation function should accept optional `project_id`. When omitted or `None`, task goes to inbox. This eliminates the need for a separate inbox-specific function and provides consistent naming with `create_project()` and `create_folder()`.

---

## Architecture Notes

This MCP server has a two-layer architecture:

1. **MCP Server Layer** (`server_fastmcp.py`) - This file, which:
   - Exposes tools via the Model Context Protocol
   - Formats responses as human-readable text for Claude
   - Handles JSON-RPC communication with Claude Desktop

2. **OmniFocus Connector Layer** (`omnifocus_connector.py`) - Core business logic that:
   - Builds and executes AppleScript commands
   - Parses OmniFocus data
   - Returns structured Python dictionaries

Claude Desktop connects to the MCP server, which uses the OmniFocus connector to interact with the OmniFocus application via AppleScript.

---

## Summary by Category

- **Projects:** 10 tools
- **Tasks:** 18 tools
- **Folders:** 2 tools
- **Tags:** 1 tool
- **Review & GTD:** 4 tools
- **Perspectives:** 2 tools
- **Notes:** 2 tools
- **Inbox:** 1 tool

**Total:** 40 MCP tools

---

## Deprecated Functions (Removed in v0.6.0)

### Migration Guide

All 26 deprecated functions have been removed. Their functionality is preserved in the new API. Use this guide to migrate:

**Read Operations (4 removed):**
- ❌ `get_task(task_id)` → ✅ `get_tasks(task_id=X)` - Returns list with single task
- ❌ `get_project(project_id)` → ✅ `get_projects(project_id=X)` - Returns list with single project
- ❌ `get_subtasks(parent_id)` → ✅ `get_tasks(parent_task_id=X)` - Returns list of child tasks
- ❌ `get_note(entity_id)` → ✅ `get_tasks/get_projects(entity_id=X, include_full_notes=True)` - Returns full note content

**Task Update Operations (10 removed):**
- ❌ `complete_task(task_id)` → ✅ `update_task(task_id, completed=True)`
- ❌ `complete_tasks(task_ids)` → ✅ `update_tasks(task_ids, completed=True)`
- ❌ `drop_task(task_id)` → ✅ `update_task(task_id, status=TaskStatus.DROPPED)`
- ❌ `drop_tasks(task_ids)` → ✅ `update_tasks(task_ids, status=TaskStatus.DROPPED)`
- ❌ `move_task(task_id, project_id)` → ✅ `update_task(task_id, project_id=X)`
- ❌ `move_tasks(task_ids, project_id)` → ✅ `update_tasks(task_ids, project_id=X)`
- ❌ `set_parent_task(task_id, parent_id)` → ✅ `update_task(task_id, parent_task_id=X)`
- ❌ `set_estimated_minutes(task_id, minutes)` → ✅ `update_task(task_id, estimated_minutes=X)`
- ❌ `add_tag_to_task(task_id, tag)` → ✅ `update_task(task_id, add_tags=[X])`
- ❌ `remove_tag_from_tasks(task_ids, tag)` → ✅ `update_tasks(task_ids, remove_tags=[X])`

**Project Update Operations (4 removed):**
- ❌ `drop_project(project_id)` → ✅ `update_project(project_id, status=ProjectStatus.DROPPED)`
- ❌ `drop_projects(project_ids)` → ✅ `update_projects(project_ids, status=ProjectStatus.DROPPED)`
- ❌ `set_review_interval(project_id, weeks)` → ✅ `update_project(project_id, review_interval_weeks=X)`
- ❌ `mark_project_reviewed(project_id)` → ✅ `update_project(project_id, last_reviewed="today")`
- ❌ `set_project_status(project_id, status)` → ✅ `update_project(project_id, status=X)`

**Delete Operations (2 removed):**
- ❌ `delete_task(task_id)` → ✅ `delete_tasks(task_id)` - Now accepts single ID or list
- ❌ `delete_project(project_id)` → ✅ `delete_projects(project_id)` - Now accepts single ID or list

**Batch Tag Operations (1 removed):**
- ❌ `add_tag_to_tasks(task_ids, tag)` → ✅ `update_tasks(task_ids, add_tags=[X])`

**Note Operations (1 removed):**
- ❌ `add_note(entity_id, note)` → ✅ Client-side: Fetch current note, concatenate, then `update_task/update_project(entity_id, note=combined)`

**Inbox Operations (1 removed):**
- ❌ `create_inbox_task(name, ...)` → ✅ `create_task(name, project_id=None, ...)` - Omit project_id to create in inbox

**Specialized Filters (2 removed):**
- ❌ `get_stalled_projects()` → ✅ Client-side filtering with `get_projects()` - Check for projects with no next actions
- ❌ `get_projects_due_for_review()` → ✅ Client-side filtering with `get_projects()` - Compare review dates

**Total Removed:** 26 functions

---

## API Reduction Summary (COMPLETED v0.6.0)

**Previous API:** 40+ functions
**Current API:** 16 functions (60% reduction)

**Implemented changes:** ✅ ALL COMPLETE
1. ✅ **Consolidate into core CRUD operations** - Focus on create, read, update, delete for each entity type
2. ✅ **Merge singular/batch operations** - Functions accept `Union[str, list[str]]` for flexibility
3. ✅ **Remove specialized filters** - Functions like `get_stalled_projects()` removed (client-side filtering)
4. ✅ **Consolidate all updates into update functions** - Single `update_task()` and `update_project()` handle all field changes
5. ✅ **Remove redundant getters** - Functions like `get_note()` and `get_subtasks()` replaced with parameters on general get functions
6. ✅ **Merge inbox creation** - `create_inbox_task()` merged into `create_task()`

**Core API Pattern (Implemented):**
Following MCP best practices while minimizing overhead, the API follows a simple CRUD pattern:
- `create_X()` - Create new entities
- `get_Xs()` - Read entities with filtering (supports single ID via parameter)
- `update_X()` - Update any field on a single entity (handles all property changes)
- `update_Xs()` - Batch update (safe fields only, excludes name/note)
- `delete_Xs()` - Delete one or more entities (accepts single or multiple IDs)

**Functions DELETED:** 26 (See migration guide above)

**Final count:** 16 core functions

**Key architectural decisions (All Implemented):**
- ✅ **Comprehensive update functions** - `update_task()` and `update_project()` handle ALL field updates to minimize tool call overhead
- ✅ **Union types for batch operations** - `Union[str, list[str]]` allows single function to handle one or many items
- ✅ **Structured returns for batch operations** - Consistent dict format with success/failure counts
- ✅ **Enum types** - `TaskStatus` and `ProjectStatus` enums for status values
- ✅ **Explicit ValueError** on conflicting parameters (e.g., can't set both `project_id` and `parent_task_id`)
- ✅ **Keep create/update separate** - Clear distinction between creating and modifying (no upsert pattern)
- ✅ **Simple, atomic operations** - Each tool has one clear purpose
- ✅ **Separate single/batch updates** - Batch functions exclude `name` and `note` fields to prevent accidental overwrites

**Benefits (Realized):**
- ✅ Minimizes tool call overhead (update multiple fields in one call)
- ✅ Simpler API surface (16 vs 40+ functions - 60% reduction)
- ✅ Flexible batch operations (one function handles any quantity)
- ✅ Consistent patterns across all entity types
- ✅ Easier to extend (add parameters vs add functions)
- ✅ Type safety with enums and structured returns
- ✅ Database safety guards enabled for all destructive operations

**Implementation Details:**
- **Code reduction:** 2,681 lines of deprecated code removed
- **Test coverage:** 333 tests passing (100% pass rate)
- **Safety guards:** All write operations verify database in test mode
- **Backward compatibility:** Server layer handles legacy parameter names where needed
- **Error handling:** Parameter validation (ValueError) vs runtime errors (dict with error field)