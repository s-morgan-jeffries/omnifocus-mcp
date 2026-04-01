# OmniFocus MCP Tool Descriptions

This file contains exactly what an MCP-connected agent sees: the server instructions and all tool schemas with docstrings. Used as input for blind agent eval.

## Server Instructions

OmniFocus is a GTD task manager. Hierarchy: Folders > Projects > Tasks > Subtasks.

TASK STATES: Available, Blocked, Deferred (future defer date), Flagged, Overdue, Completed, Dropped. Planned Date is a scheduling signal only — no availability/overdue constraints.

PROJECT TYPES: "sequential" (tasks in order; first incomplete = available, rest blocked; position = dependencies), "parallel" (all available), "single_actions" (no completion goal, cannot auto-complete). The `next` field is true for the first available action in a sequential project/action group; in parallel projects, all incomplete tasks have `next: true`.

ACTION GROUPS: Task with subtasks. Parent shows `blocked: true` while subtasks are active — this is normal, not an error. Do not try to unblock it.

INHERITED STATUS: `completed`/`dropped` reflect the task's own state, not its container's. Task in completed project: `completed: false`, `available: false`. Use `available_only=True` for actionable tasks.

EFFECTIVE DATES: Dates returned by get_tasks are always effective (inherited). A task with no direct due date WILL show its project's due date in the dueDate field — this is correct behavior, not a bug. You cannot clear an inherited date at the task level. Write operations set the task's own date.

RECURRING TASKS: `completed=True` uses `mark complete`, which creates the next occurrence. This is guaranteed. WARNING: Dropping a recurring task (status='dropped') without clearing recurrence first (recurrence='') spawns the next occurrence. To stop a series: update_tasks([{"id": "...", "recurrence": "", "status": "dropped"}]).

TAGS: Represent work contexts. Tag statuses: Active (normal), On Hold (tasks excluded from Available perspective), Dropped (tag hidden from picker; does NOT affect task availability).

DEFER vs DUE: Defer = hidden until that date. Due = deadline.

## Tools

### get_projects

Retrieve projects with optional filtering.

**Parameters:**
- `project_id: str` — filter to specific project
- `query: str` — search name/note/folder (case-insensitive)
- `flagged_only, on_hold_only, completed_only: bool`
- `stalled_only: bool` — active projects with no available next actions
- `include_dropped, include_completed: bool` — include hidden states
- `include_full_notes: bool`
- `include_task_health: bool` — adds remainingCount, availableCount, overdueCount, deferredCount, stalled, health
- `include_last_activity: bool` — adds lastActivityDate
- `has_overdue_tasks: bool` — implies include_task_health
- `tag_filter: list[str]` — projects with ALL specified tags
- `planned_after, planned_before, planned_on: str` — ISO date filters (planned_on is mutually exclusive)
- `modified_after, modified_before: str`
- `min_task_count: int`
- `has_no_due_dates: bool`
- `sort_by: str` — "name"; `sort_order: str` — "asc"/"desc"

**Returns:** id, name, folderPath, status, projectType, sequential (deprecated), completedByChildren, flagged, creationDate, modificationDate, completionDate, droppedDate, dueDate, deferDate, plannedDate, tags, note, lastReviewDate, nextReviewDate, reviewIntervalValue, reviewIntervalUnit. Optional health/activity fields when requested.

### create_projects

Create one or more projects.

**Parameters (per item):**
- `name: str` (required)
- `note, folder_path: str`
- `project_type: str` — "parallel" (default), "sequential", "single_actions"
- `sequential: bool` (deprecated, use project_type)
- `review_interval_value: int` + `review_interval_unit: str` ("day"/"week"/"month"/"year"); `review_interval_weeks: int` (deprecated)
- `completed_by_children: bool`
- `due_date, defer_date, planned_date: str` — ISO 8601

### update_projects

Update one or more projects. Each item has `id` (required) plus fields to change.

**Parameters (per item):**
- `id: str` (required)
- `project_name, note, folder_path: str` — note: replaces rich text
- `project_type: str`; `sequential: bool` (deprecated)
- `status: str` — "active", "on_hold", "done", "dropped"
- `review_interval_value: int` + `review_interval_unit: str` ("day"/"week"/"month"/"year"); `review_interval_weeks: int` (deprecated)
- `last_reviewed: str` — ISO or "now" (recalculates next_review_date from review interval)
- `next_review_date: str` — set AFTER last_reviewed to override the calculated date
- `completed_by_children: bool`
- `due_date, defer_date, planned_date: str` — ISO or "" to clear
- `flagged: bool`
- `estimated_minutes: int`
- `tags: list[str]` — full replacement (conflicts with add_tags/remove_tags)
- `add_tags, remove_tags: list[str]`
- `recurrence: str` — RRULE or "" to clear; `repetition_method: str` — "fixed", "start_after_completion", "due_after_completion"

### delete_projects

Permanently delete projects and all their tasks. Cannot be undone.

- `project_ids: str | list[str]` (required)

### get_tasks

Get tasks with optional filtering.

**Parameters:**
- `task_id, parent_task_id, project_id: str`
- `query: str` — search name/note
- `flagged_only, available_only, overdue, dropped_only, blocked_only, next_only, inbox_only: bool`
- `include_completed: bool`
- `include_full_notes: bool`
- `tag_filter: list[str]`; `tag_filter_mode: str` — "and" (default), "or", "not"
- `planned_after, planned_before, planned_on: str`
- `modified_after, modified_before, created_after, created_before: str`
- `max_estimated_minutes: int` — quick wins filter
- `has_estimate: bool`
- `recurring_only: bool`
- `sort_by: str` — "name", "due_date", "defer_date"; `sort_order: str`

**Returns:** id, name, projectName, completed, dropped, blocked, available, next, flagged, dueDate, deferDate, plannedDate, estimatedMinutes, tags, note, parentTaskId, subtaskCount, sequential, isRecurring, recurrence, repetitionMethod, repeatSummary, nextDueDate, nextDeferDate, nextPlannedDate, catchUpAutomatically, creationDate, modificationDate, completionDate, droppedDate.

Key fields:
- `available` — true when actionable (accounts for inherited status from containers)
- `repeatSummary` — human-readable recurrence; always use this for display, don't parse RRULE
- `repetitionMethod` — "fixed" (original schedule), "start_after_completion" (defer shifts), "due_after_completion" (due shifts)
- `catchUpAutomatically` — recurring only; true = one catch-up occurrence, false = each missed interval spawns its own
- Date fields are effective (include inherited from project). Next-occurrence fields populated only for recurring tasks.
- Tasks inherit tags from their parent project. A task showing a tag it wasn't explicitly assigned has inherited it — this is expected, not a bug.

### create_tasks

Create one or more tasks.

**Parameters (per item):**
- `task_name: str` (required)
- `project_id: str` — mutually exclusive with parent_task_id
- `parent_task_id: str` — creates subtask
- `note: str` (plain text only)
- `due_date, defer_date, planned_date: str` — ISO 8601
- `flagged: bool`
- `tags: list[str]` — must already exist
- `estimated_minutes: int`
- `sequential: bool` — subtasks completed in order
- `completed_by_children: bool`

### update_tasks

Update one or more tasks. Each item has `id` (required) plus fields to change.

**Parameters (per item):**
- `id: str` (required)
- `task_name, project_id, parent_task_id, note: str`
- `due_date, defer_date, planned_date: str` — ISO or "" to clear
- `flagged, completed: bool` — completed=True on recurring task creates next occurrence
- `status: str` — "dropped" (prefer `completed: bool` for completion)
- `tags: list[str]` — full replacement (conflicts with add_tags/remove_tags)
- `add_tags, remove_tags: list[str]`
- `estimated_minutes: int`
- `recurrence: str` — RRULE or "" to clear; `repetition_method: str`
- `sequential: bool`; `completed_by_children: bool`

### delete_tasks

Permanently delete tasks. Cannot be undone.

- `task_ids: str | list[str]` (required)

### reorder_task

Move a task before or after another task within the same project/level.

- `task_id: str` (required)
- `before_task_id: str` — place before this task
- `after_task_id: str` — place after this task

Exactly one of before/after required. In sequential projects, order = dependencies.

### reorder_project

Move a project before or after another project within the same folder.

- `project_id: str` (required)
- `before_project_id: str`
- `after_project_id: str`

Exactly one of before/after required.

### get_folders

Get all folders with hierarchy.

**Parameters:** None

**Returns:** id, name, path (e.g. "Work > Clients"), status ("active"/"dropped").

### create_folders

Create one or more folders.

**Parameters (per item):**
- `name: str` (required)
- `parent_path: str` — e.g. "Work > Clients"

### update_folders

Update one or more folders. Each item has `id` (required) plus fields to change.

**Parameters (per item):**
- `id: str` (required)
- `name: str`
- `status: str` — "active" or "dropped"

### get_tags

Retrieve all tags.

**Parameters:** None

**Returns:** id, name, status ("active"/"on hold"/"dropped"), parentTagId (empty if top-level; create/update accept parent by NAME not ID), childrenAreMutuallyExclusive (assigning one child silently removes siblings).

### create_tags

Create one or more tags.

**Parameters (per item):**
- `name: str` (required)
- `parent_tag: str` — parent by name
- `children_are_mutually_exclusive: bool`

### update_tags

Update one or more tags. Each item has `id` (required) plus fields to change.

**Parameters (per item):**
- `id: str` (required)
- `name, status: str` — status: "active", "on_hold", "dropped"
- `children_are_mutually_exclusive: bool`
- `parent_tag: str` — move to parent by name, "" for top level

### delete_tags

Delete tags. Tasks lose tag association but are not deleted.

- `tag_ids: str | list[str]` (required)

### get_perspectives

Get all perspectives.

**Parameters:** None

**Returns:** name, type (built-in/custom), id

### switch_perspective

Switch front window to a perspective.

- `perspective_name: str` (required)

### set_focus

Focus on projects/folders, or clear focus. Does not support tasks or tags.

- `item_ids: str | list[str]` — omit or empty to clear
- `item_types: str | list[str]` — "project" or "folder"

### get_focus

Get currently focused items.

**Parameters:** None
