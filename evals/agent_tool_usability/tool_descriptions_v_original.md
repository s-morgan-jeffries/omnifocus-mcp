# OmniFocus MCP Tool Descriptions

This file contains exactly what an MCP-connected agent sees: the server instructions and all tool schemas with docstrings. Used as input for blind agent eval.

## Server Instructions

OmniFocus is a GTD (Getting Things Done) task manager. Key concepts:

TASK STATES: Available (can work on now), Blocked (waiting on predecessor in sequential project), Deferred (has future defer date — hidden until then), Flagged (user marked as priority/today), Overdue (past due date), Completed, Dropped. Tasks also have an optional Planned Date — a scheduling signal for when you plan to work on the task, with no availability or overdue constraints (unlike defer/due dates).

PROJECT STATES: Active (tasks are actionable), On Hold (paused — tasks hidden), Dropped (abandoned), Completed.

HIERARCHY: Folders → Projects → Tasks → Subtasks. Folders organize projects. Projects contain tasks. Tasks can have subtasks via parent_task_id.

PROJECT TYPES: Three types — "sequential" (tasks completed in order, first incomplete = available, rest = blocked), "parallel" (all tasks available simultaneously), "single_actions" (grab-bag list with no completion goal — cannot auto-complete, used for loose collections like "Someday/Maybe" or catch-all inboxes). Use `projectType` field (not `sequential`) to distinguish all three. Dependencies are positional — reorder tasks to change dependency chains. There are no explicit task-to-task dependency links. The `next` field on a task is true when it is the first available action in a sequential project or action group. In parallel projects, all incomplete tasks have `next: true`.

ACTION GROUPS: A task with subtasks is an "action group." It can be parallel or sequential, just like a project. The parent task appears as `blocked: true` while its subtasks are active — **this is normal behavior, not an error or a problem to fix.** Check `subtaskCount > 0` to identify action groups. An action group parent cannot be completed until its subtasks are resolved. If you see a task with `blocked: true` and `subtaskCount > 0`, it means "work on the subtasks first" — do not try to unblock it.

INHERITED STATUS: Task-level fields like `completed` and `dropped` reflect the task's own state, NOT its container's state. A task inside a completed project will show `completed: false` (because the task itself wasn't individually completed) but `available: false` (because its container is inactive). This is expected behavior. To find truly actionable tasks, always use `available` or `available_only=True` — do not rely on `completed` alone.

EFFECTIVE DATES: Date fields (dueDate, deferDate, plannedDate) returned by get_tasks are EFFECTIVE dates — they include dates inherited from the containing project. A task with no direct due date in a project with dueDate=April 15 will return dueDate="2026-04-15T17:00:00" (not empty). Do not assume an empty due date on a task means the project has no due date either. Write operations (update_task) set the task's own date directly.

BATCH OPERATIONS: When updating multiple items, prefer the unified tools (update_tasks, update_projects) which accept a list of update objects — each item can have different fields. More efficient than multiple individual calls.

RECURRING TASKS: Setting completed=True on a recurring task uses OmniFocus's 'mark complete' command, which automatically creates the next occurrence. This is guaranteed behavior — do not hedge or warn that recurrence might stop. WARNING: Dropping a recurring task (status='dropped') WITHOUT first clearing recurrence (recurrence='') will spawn the next occurrence. To permanently stop a recurring series, clear recurrence and drop in a single update_tasks call: update_tasks([{"id": "...", "recurrence": "", "status": "dropped"}]).

TAGS: Formerly "contexts." Represent work contexts (location, tools, energy, people, workflow states like Waiting-for or Agenda). Cut across projects. Use for filtering. Tags can be Active or On Hold — tasks with On Hold tags are excluded from OmniFocus's native Available perspective.

PLANNING PATTERN: To plan a day, query: (1) overdue tasks, (2) flagged + available tasks, (3) inbox items, (4) next actions. Prioritize overdue+flagged first.

INBOX: Unprocessed capture bucket. Tasks without a project land here. Non-empty inbox = items need organizing.

REVIEW: Projects have review intervals. Use get_projects() to find projects due for review (check last_reviewed + review_interval_weeks).

---

## Tools

### get_projects

Retrieve projects from OmniFocus with optional filtering.

**Parameters:**
- `project_id: str` (optional) — Filter to specific project by ID
- `include_full_notes: bool` (default: False) — Return full note content
- `on_hold_only: bool` (default: False) — If True, only return projects with "on hold" status
- `query: str` (optional) — Search term to filter by name, note, or folder path (case-insensitive)
- `include_task_health: bool` (default: False) — Include per-project task health counts (remaining, available, overdue, deferred)
- `include_last_activity: bool` (default: False) — Compute lastActivityDate (most recent task creation/completion)
- `stalled_only: bool` (default: False) — Only return active projects with no available actions (implies include_task_health=True)
- `flagged_only: bool` (default: False) — Only return flagged projects
- `include_dropped: bool` (default: False) — Include dropped projects in results (hidden by default)
- `include_completed: bool` (default: False) — Include completed projects in results (hidden by default)
- `completed_only: bool` (default: False) — Only return completed projects (implies include_completed)
- `tag_filter: list[str]` (optional) — Filter projects by tags. Only returns projects with ALL specified tags.
- `planned_after: str` (optional) — Only return projects with planned date on or after this ISO date
- `planned_before: str` (optional) — Only return projects with planned date before this ISO date
- `planned_on: str` (optional) — Only return projects planned for this specific date (e.g., "2026-03-23"). Convenience for planned_after=date + planned_before=next_day. Mutually exclusive with planned_after/planned_before.
- `has_overdue_tasks: bool` (optional) — Only return projects with overdue tasks (implies include_task_health)
- `sort_by: str` (optional) — Sort results by field — "name"
- `sort_order: str` (default: "asc") — Sort direction — "asc" or "desc"
- `modified_after: str` (optional) — Only return projects modified after this ISO date
- `modified_before: str` (optional) — Only return projects modified before this ISO date
- `min_task_count: int` (optional) — Only return projects with at least this many tasks
- `has_no_due_dates: bool` (optional) — If True, only return projects where no tasks have due dates

**Returns:** Each project includes: id, name, folderPath, status, projectType, sequential, completedByChildren, flagged, creationDate, modificationDate, completionDate (null if not completed), droppedDate (null if not dropped), dueDate, deferDate, plannedDate, tags, note (truncated unless include_full_notes=True), lastReviewDate, nextReviewDate, reviewIntervalValue, reviewIntervalUnit. `projectType` is "sequential", "parallel", or "single_actions" (Single Actions List — grab-bag list with no completion goal, cannot auto-complete). `sequential` (boolean) is retained for backwards compatibility. `completedByChildren` (boolean) — true if the project auto-completes when its last remaining action is completed. `dueDate`, `deferDate`, `plannedDate` — project-level dates in ISO format (empty string if not set). Tasks inherit effective dates from their containing project. With include_task_health: remainingCount, availableCount, overdueCount, deferredCount, stalled, health status. `stalled` (boolean) — true when availableCount=0 and tasks are not just deferred (project needs attention). With include_last_activity: lastActivityDate.

---

### create_projects

Create one or more projects in OmniFocus.

Pass a list of project objects. Each must have a name; all other fields optional.

**Parameters:**
- `projects: list[ProjectCreate]` (required) — List of project objects. Each supports:
  - `name: str` (required) — The name of the project
  - `note: str` (optional) — Note/description (plain text only - rich text not supported via automation APIs)
  - `folder_path: str` (optional) — Folder path (e.g., "Work > Clients") - folder must exist
  - `project_type: str` (optional) — Project type: "parallel" (default, all tasks available simultaneously), "sequential" (tasks completed in order, only first available), or "single_actions" (grab-bag list with no completion goal, cannot auto-complete). Overrides `sequential` when provided.
  - `sequential: bool` (default: False, DEPRECATED) — Use project_type instead. If True, creates a sequential project.
  - `review_interval_weeks: int` (optional) — Review interval in weeks for GTD review cycle
  - `completed_by_children: bool` (optional) — Auto-complete the project when its last remaining action is completed
  - `due_date: str` (optional) — Due date in ISO 8601 format (e.g., "2025-10-15" or "2025-10-15T17:00:00"). Tasks inherit this as their effective due date.
  - `defer_date: str` (optional) — Defer date in ISO 8601 format (when project becomes available)
  - `planned_date: str` (optional) — Planned date in ISO 8601 format (when you plan to work on the project)

**Returns:** For single project: success message with project ID and configuration details. For multiple: summary with per-item results.

**Examples:**
```
create_projects([{"name": "Website Redesign"}])
create_projects([
    {"name": "Project A", "folder_path": "Work", "project_type": "sequential"},
    {"name": "Project B", "due_date": "2026-04-01"}
])
```

---

### update_projects

Update one or more projects in OmniFocus. Pass a list of project update objects — each must have an `id` field, plus any fields to change. Each project can have different fields updated.

**Parameters:**
- `projects: list[object]` (required) — List of project update objects. Each object has:
  - `id: str` (required) — The project ID to update
  - `project_name: str` (optional) — New project name
  - `folder_path: str` (optional) — Folder path to move project to (e.g., "Work : Projects")
  - `note: str` (optional) — New note content. WARNING: Removes rich text formatting.
  - `project_type: str` (optional) — Change project type: "parallel", "sequential", or "single_actions"
  - `sequential: bool` (optional, DEPRECATED) — Use project_type instead.
  - `status: str` (optional) — Project status - "active", "on_hold", "done", or "dropped"
  - `review_interval_weeks: int` (optional, DEPRECATED) — Use review_interval_value + review_interval_unit instead. Review interval in weeks (0 to clear)
  - `review_interval_value: int` (optional) — Review interval amount (e.g., 3 for "every 3 months"). Used with review_interval_unit.
  - `review_interval_unit: str` (optional) — Review interval unit: "day", "week", "month", or "year" (default: "week")
  - `last_reviewed: str` (optional) — Last reviewed date in ISO format or "now"
  - `next_review_date: str` (optional) — Explicit next review date in ISO format — overrides the date OmniFocus calculates from last_reviewed + review_interval
  - `completed_by_children: bool` (optional) — Auto-complete the project when its last remaining action is completed
  - `due_date: str` (optional) — Due date in ISO 8601 format, or "" to clear
  - `defer_date: str` (optional) — Defer date in ISO 8601 format, or "" to clear
  - `planned_date: str` (optional) — Planned date in ISO 8601 format, or "" to clear
  - `flagged: bool` (optional) — Flag marks a project as a priority. Pass True to flag, False to unflag.
  - `estimated_minutes: int` (optional) — Estimated time in minutes for the project
  - `tags: list[str]` (optional) — Full replacement — set exact tag list. Conflicts with add_tags/remove_tags.
  - `add_tags: list[str]` (optional) — Add these tags incrementally. Conflicts with tags.
  - `remove_tags: list[str]` (optional) — Remove these tags. Conflicts with tags.
  - `recurrence: str` (optional) — iCalendar RRULE string, or empty string to remove recurrence.
  - `repetition_method: str` (optional) — "fixed", "start_after_completion", or "due_after_completion". Only meaningful when recurrence is set.

**Returns:** For single project: success message with updated fields. For multiple: summary with per-item results.

**Examples:**
```
update_projects([{"id": "proj-123", "flagged": true}])
update_projects([
    {"id": "proj-1", "status": "on_hold"},
    {"id": "proj-2", "project_name": "Renamed", "flagged": true}
])
```

---

### delete_projects

Delete one or more projects from OmniFocus.

WARNING: This permanently deletes the projects and all their tasks. Cannot be undone.

**Parameters:**
- `project_ids: str | list[str]` (required) — Single project ID or list of project IDs to delete

**Returns:** Summary of deleted projects with count and any errors encountered

---

### get_tasks

Get tasks from OmniFocus with optional filtering.

**Parameters:**
- `task_id: str` (optional) — Filter to specific task by ID
- `parent_task_id: str` (optional) — Filter to subtasks of parent
- `include_full_notes: bool` (default: False) — Return full note content
- `project_id: str` (optional) — Project ID to filter tasks (ignored if inbox_only=True)
- `flagged_only: bool` (default: False) — Only return flagged tasks
- `include_completed: bool` (default: False) — Include completed tasks
- `available_only: bool` (default: False) — Only return available tasks (not completed, not dropped, not blocked, not deferred)
- `overdue: bool` (default: False) — Only return overdue tasks
- `dropped_only: bool` (default: False) — Only return dropped tasks
- `blocked_only: bool` (default: False) — Only return blocked tasks
- `next_only: bool` (default: False) — Only return next tasks
- `tag_filter: list[str]` (optional) — List of tag names to filter by, e.g., `["Errands", "Weekend"]` (task must have ALL listed tags)
- `query: str` (optional) — Search term to filter by name or note (case-insensitive)
- `inbox_only: bool` (default: False) — Only return inbox tasks
- `planned_after: str` (optional) — Only return tasks with planned date on or after this ISO date
- `planned_before: str` (optional) — Only return tasks with planned date before this ISO date
- `sort_by: str` (optional) — Sort results by field — "name", "due_date", or "defer_date"
- `sort_order: str` (default: "asc") — Sort direction — "asc" or "desc"
- `modified_after: str` (optional) — Only return tasks modified after this ISO date
- `modified_before: str` (optional) — Only return tasks modified before this ISO date
- `created_after: str` (optional) — Only return tasks created after this ISO date
- `created_before: str` (optional) — Only return tasks created before this ISO date
- `max_estimated_minutes: int` (optional) — Only return tasks with estimated time <= this value — "quick wins" filter
- `has_estimate: bool` (optional) — If True, only return tasks with an estimate set; if False, only tasks without
- `recurring_only: bool` (optional) — If True, only return recurring tasks; if False, only non-recurring
- `tag_filter_mode: str` (default: "and") — How tag_filter matches — "and" (all tags), "or" (any tag), "not" (none of the tags)
- `planned_on: str` (optional) — Only return tasks planned for this specific date (e.g., "2026-03-23"). Mutually exclusive with planned_after/planned_before.

**Returns:** Each task includes: id, name, projectName, completed, dropped, blocked, available, next, flagged, dueDate, deferDate, plannedDate, estimatedMinutes, tags, note (truncated unless include_full_notes=True), parentTaskId, subtaskCount, sequential, isRecurring, recurrence, repetitionMethod, repeatSummary, nextDueDate, nextDeferDate, nextPlannedDate, catchUpAutomatically, creationDate, modificationDate, completionDate (null if not completed), droppedDate (null if not dropped).
`available` is true when the task is actionable — not completed, not dropped, not blocked, not deferred, and not inside a completed or dropped container (project or parent task). This accounts for inherited status: a task in a done project shows `completed: false` but `available: false` because its container is inactive. Use `available_only=True` to get only truly actionable tasks.

Note: Date fields (dueDate, deferDate, plannedDate) reflect effective dates — including dates inherited from the containing project or action group. A task with no direct due date will show its project's due date in dueDate. Example: if project "Q2 Report" has dueDate=April 15, a task in that project with no direct due date will return dueDate="2026-04-15T17:00:00" in get_tasks output (inherited from project, not empty). Write operations (update_task) still set the task's own date directly. Next occurrence fields (nextDueDate, nextDeferDate, nextPlannedDate) are populated only for recurring tasks and show the dates of the next recurrence — empty for non-recurring tasks. `catchUpAutomatically` (boolean, null for non-recurring) controls missed-recurrence behavior: when true, only one catch-up occurrence is created if a task is missed; when false, each missed interval spawns its own occurrence (can flood the inbox).

**Important:** `repeatSummary` is a human-readable version of the recurrence RRULE (e.g., "Every 2 weeks on Mon, Wed, Fri"). **Always use `repeatSummary` for user-facing output — do not manually parse the raw `recurrence` RRULE string.** `repetitionMethod` indicates how the next occurrence is calculated: "fixed" (next occurrence on the original schedule regardless of when completed — e.g., if due every Monday, completing on Wednesday still makes the next occurrence due Monday), "start_after_completion" (next defer date = completion date + interval — e.g., complete Wednesday, next defer = following Wednesday), "due_after_completion" (next due date = completion date + interval — e.g., complete Wednesday, next due = following Wednesday). Use `due_after_completion` when you want the **deadline** to shift based on completion; use `start_after_completion` when you want the **availability window** (defer date) to shift instead. Recurrence rules can be set, modified, or removed via `update_task(recurrence=..., repetition_method=...)`. Use standard iCalendar RRULE format (e.g., `FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,WE,FR`). Pass `recurrence=""` to remove recurrence.

---

### create_tasks

Create one or more tasks in OmniFocus (unified batch operation).

Pass a list of TaskCreate objects. Each task must have a `task_name`; all other fields are optional. For a single task, pass a list with one item. Prefer this over calling `create_task` multiple times.

**Parameters:**
- `tasks: list[TaskCreate]` (required) — List of task objects to create. Each supports:
  - `task_name: str` (required) — The name/title of the task
  - `project_id: str` (optional) — Project ID. Mutually exclusive with parent_task_id.
  - `parent_task_id: str` (optional) — Parent task ID to create as subtask. Mutually exclusive with project_id.
  - `note: str` (optional) — Note/description (plain text only)
  - `due_date: str` (optional) — Due date in ISO 8601 format
  - `defer_date: str` (optional) — Defer date in ISO 8601 format
  - `planned_date: str` (optional) — Planned date in ISO 8601 format
  - `flagged: bool` (default: False) — Flag as priority
  - `tags: list[str]` (optional) — List of tag names. Tags must already exist.
  - `estimated_minutes: int` (optional) — Estimated time in minutes
  - `sequential: bool` (default: False) — If True, subtasks must be completed in order
  - `completed_by_children: bool` (default: False) — Auto-complete when last subtask completes

**Returns:** For single task: success message with task ID. For multiple: summary with per-item results.

**Examples:**
- `create_tasks([{"task_name": "Buy groceries"}])` — Single inbox task
- `create_tasks([{"task_name": "A", "project_id": "p1"}, {"task_name": "B", "project_id": "p1"}])` — Two tasks in a project

---

### update_tasks

Update multiple tasks with per-item values via a list of update objects (unified batch operation).

Each item in the list is a TaskUpdate object with an `id` field (required) and any fields to change. Different items can have different fields — this is NOT limited to uniform updates.

**Parameters:**
- `tasks: list[TaskUpdate]` (required) — List of task update objects. Each must have:
  - `id: str` (required) — The task ID to update
  - All other fields from update_task are available per item: `task_name`, `project_id`, `parent_task_id`, `note`, `due_date`, `defer_date`, `planned_date`, `flagged`, `tags`, `add_tags`, `remove_tags`, `estimated_minutes`, `completed`, `status`, `recurrence`, `repetition_method`, `sequential`, `completed_by_children`

**Returns:** Summary with counts of successful/failed updates. Continues processing when individual tasks fail.

**Examples:**
- `update_tasks([{"id": "t1", "flagged": true}, {"id": "t2", "flagged": true}])` — Flag two tasks
- `update_tasks([{"id": "t1", "task_name": "Renamed"}, {"id": "t2", "completed": true}])` — Different fields per task

---

### delete_tasks

Delete multiple tasks from OmniFocus.

WARNING: This permanently deletes the tasks and cannot be undone.

**Parameters:**
- `task_ids: str | list[str]` (required) — Single task ID or list of task IDs to delete

**Returns:** Summary of deleted tasks with count and any errors encountered

---

### reorder_task

Move a task before or after another task to change its position.

Use this to reorder tasks within a project or within a parent task's subtasks. In sequential projects, task order determines dependencies — reordering changes which task is available next (first incomplete = available, rest = blocked).

**Parameters:**
- `task_id: str` (required) — The ID of the task to move
- `before_task_id: str` (optional) — Place task immediately BEFORE this reference task. Example: reorder_task("C", before_task_id="A") → [..., C, A, ...]
- `after_task_id: str` (optional) — Place task immediately AFTER this reference task. Example: reorder_task("C", after_task_id="A") → [..., A, C, ...]

**Returns:** Success message confirming the task was reordered

**Note:** Both tasks must be in the same project and at the same level. Exactly one of before_task_id or after_task_id must be provided.

---

### reorder_project

Move a project before or after another project to change its position within a folder.

**Parameters:**
- `project_id: str` (required) — The ID of the project to move
- `before_project_id: str` (optional) — Place project immediately BEFORE this reference project. Example: reorder_project("C", before_project_id="A") → [..., C, A, ...]
- `after_project_id: str` (optional) — Place project immediately AFTER this reference project. Example: reorder_project("C", after_project_id="A") → [..., A, C, ...]

**Returns:** Success message confirming the project was reordered

**Note:** Both projects must be in the same folder. Exactly one of before_project_id or after_project_id must be provided.

---

### get_folders

Get all folders from OmniFocus with their hierarchy.

**Parameters:** None

**Returns:** Each folder includes: id, name, path (hierarchical, e.g. "Work > Clients"), status ("active" or "dropped"). Dropped folders and their contents are hidden from most OmniFocus views.

---

### create_folders

Create one or more folders in OmniFocus (unified batch operation).

**Parameters:**
- `folders: list[FolderCreate]` (required) — List of folder objects. Each supports:
  - `name: str` (required) — The name of the folder
  - `parent_path: str` (optional) — Parent folder path (e.g., "Work" or "Work > Clients")

**Returns:** For single folder: success message with folder ID. For multiple: summary with per-item results.

**Examples:**
- `create_folders([{"name": "Clients"}])`
- `create_folders([{"name": "Work"}, {"name": "Personal", "parent_path": "Home"}])`

---

### update_folders

Update one or more folders in OmniFocus (unified batch operation).

**Parameters:**
- `folders: list[FolderUpdate]` (required) — List of folder update objects. Each must have:
  - `id: str` (required) — The folder ID to update
  - `name: str` (optional) — New folder name
  - `status: str` (optional) — "active" or "dropped"

**Returns:** For single folder: success message with updated fields. For multiple: summary with per-item results.

**Examples:**
- `update_folders([{"id": "f1", "name": "Renamed"}])`
- `update_folders([{"id": "f1", "status": "dropped"}, {"id": "f2", "name": "New Name"}])`

---

### get_tags

Retrieve all available tags from OmniFocus.

Tags (formerly 'contexts') represent contexts for doing work — location (Office, Home), tools (Computer, Phone), energy level (High, Low), people, or workflow states (Waiting-for, Agenda). They cut across projects and are used for filtering tasks via get_tasks(tag_filter=[...]).

**Parameters:** None

**Returns:** Each tag includes: id, name, status (values: "active", "on hold", "dropped"), parentTagId (empty string if top-level, parent tag's ID if nested — note: create_tag and update_tag accept parent_tag by NAME, not this ID), childrenAreMutuallyExclusive (boolean — when true, child tags are mutually exclusive: assigning one child tag to a task silently removes any other child from the same group).

---

### create_tags

Create one or more tags in OmniFocus (unified batch operation).

Pass a list of TagCreate objects. Each tag must have a `name`; other fields are optional. Prefer this over calling `create_tag` multiple times.

**Parameters:**
- `tags: list[TagCreate]` (required) — List of tag objects to create. Each supports:
  - `name: str` (required) — The name of the tag to create
  - `parent_tag: str` (optional) — Parent tag by NAME for nesting
  - `children_are_mutually_exclusive: bool` (default: False) — Mutually exclusive children

**Returns:** For single tag: success message with tag ID. For multiple: summary with per-item results.

**Examples:**
- `create_tags([{"name": "Automation"}])` — Single tag
- `create_tags([{"name": "High", "parent_tag": "Energy"}, {"name": "Low", "parent_tag": "Energy"}])` — Batch nested tags

---

### update_tags

Update one or more tags in OmniFocus (unified batch operation).

Each item in the list can update different fields. Prefer this over calling `update_tag` multiple times.

**Parameters:**
- `tags: list[TagUpdate]` (required) — List of tag update objects. Each must have:
  - `id: str` (required) — The tag ID to update
  - `name: str` (optional) — New tag name
  - `status: str` (optional) — "active", "on_hold", or "dropped"
  - `children_are_mutually_exclusive: bool` (optional) — Mutually exclusive children
  - `parent_tag: str` (optional) — Move to parent by NAME, or empty string for top level

**Returns:** For single tag: success message with updated fields. For multiple: summary with per-item results.

**Examples:**
- `update_tags([{"id": "tag-1", "name": "Renamed"}])` — Single update
- `update_tags([{"id": "tag-1", "status": "on_hold"}, {"id": "tag-2", "parent_tag": "People"}])` — Batch with different fields

---

### delete_tags

Delete one or more tags from OmniFocus.

WARNING: This permanently deletes the tags. Tasks that had these tags will lose the tag association but are not themselves deleted.

**Parameters:**
- `tag_ids: str | list[str]` (required) — Single tag ID or list of tag IDs to delete

**Returns:** Summary of deleted tags with count and any errors encountered

---

### get_perspectives

Get all perspectives from OmniFocus with type and ID information.

**Parameters:** None

**Returns:** Formatted list of perspectives with name, type (built-in/custom), and ID

---

### switch_perspective

Switch the front window to a different perspective.

**Parameters:**
- `perspective_name: str` (required) — Name of the perspective to switch to

**Returns:** Success message confirming perspective switch

---

### set_focus

Set focus on one or more items, or clear focus.

OmniFocus supports focusing on projects and folders only (NOT tasks or tags). To highlight specific tasks, use `update_task(flagged=True)` instead. Call with no arguments (or empty lists) to clear focus.

**Parameters:**
- `item_ids: str | list[str]` (optional) — Single ID or list of IDs to focus on. Omit or pass empty to clear.
- `item_types: str | list[str]` (optional) — Matching type(s) - each must be "project" or "folder".

**Returns:** Success message confirming focus set or cleared

---

### get_focus

Get the currently focused items in OmniFocus.

**Parameters:** None

**Returns:** Formatted list of currently focused items, or a message if no focus is set
