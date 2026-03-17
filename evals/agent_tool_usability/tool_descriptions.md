# OmniFocus MCP Tool Descriptions

This file contains exactly what an MCP-connected agent sees: the server instructions and all tool schemas with docstrings. Used as input for blind agent eval.

## Server Instructions

OmniFocus is a GTD (Getting Things Done) task manager. Key concepts:

TASK STATES: Available (can work on now), Blocked (waiting on predecessor in sequential project), Deferred (has future defer date — hidden until then), Flagged (user marked as priority/today), Overdue (past due date), Completed, Dropped. Tasks also have an optional Planned Date — a scheduling signal for when you plan to work on the task, with no availability or overdue constraints (unlike defer/due dates).

PROJECT STATES: Active (tasks are actionable), On Hold (paused — tasks hidden), Dropped (abandoned), Completed.

HIERARCHY: Folders → Projects → Tasks → Subtasks. Folders organize projects. Projects contain tasks. Tasks can have subtasks via parent_task_id.

PROJECT TYPES: Three types — "sequential" (tasks completed in order, first incomplete = available, rest = blocked), "parallel" (all tasks available simultaneously), "single_actions" (grab-bag list with no completion goal — cannot auto-complete, used for loose collections like "Someday/Maybe" or catch-all inboxes). Use `projectType` field (not `sequential`) to distinguish all three. Dependencies are positional — reorder tasks to change dependency chains. There are no explicit task-to-task dependency links. The `next` field on a task is true when it is the first available action in a sequential project or action group. In parallel projects, all incomplete tasks have `next: true`.

ACTION GROUPS: A task with subtasks is an "action group." It can be parallel or sequential, just like a project. The parent task appears as `blocked: true` while its subtasks are active — this is normal behavior, not an error. Check `subtaskCount > 0` to identify action groups. An action group parent cannot be completed until its subtasks are resolved.

TAGS: Formerly "contexts." Represent work contexts (location, tools, energy, people, workflow states like Waiting-for or Agenda). Cut across projects. Use for filtering. Tags can be Active or On Hold — tasks with On Hold tags are excluded from OmniFocus's native Available perspective.

PLANNING PATTERN: To plan a day, query: (1) overdue tasks, (2) flagged + available tasks, (3) inbox items, (4) next actions. Prioritize overdue+flagged first.

INBOX: Unprocessed capture bucket. Tasks without a project land here. Non-empty inbox = items need organizing.

REVIEW: Projects have review intervals. Use get_projects() to find projects due for review (check last_reviewed + review_interval_weeks).

---

## Tools

### get_projects

Retrieve ALL active projects with full details and hierarchy, optionally filtered by search query.

**Parameters:**
- `project_id: str` (optional) — Filter to specific project by ID
- `include_full_notes: bool` (default: False) — Return full note content
- `on_hold_only: bool` (default: False) — If True, only return projects with "on hold" status
- `query: str` (optional) — Search term to filter by name, note, or folder path (case-insensitive)
- `include_task_health: bool` (default: False) — Include per-project task health counts (remaining, available, overdue, deferred)
- `include_last_activity: bool` (default: False) — Compute lastActivityDate (most recent task creation/completion)
- `stalled_only: bool` (default: False) — Only return active projects with no available actions (implies include_task_health=True)

**Returns:** Each project includes: id, name, folderPath, status, projectType, sequential, completedByChildren, creationDate, dueDate, deferDate, plannedDate, note (truncated unless include_full_notes=True), lastReviewDate, nextReviewDate, reviewIntervalWeeks. `projectType` is "sequential", "parallel", or "single_actions" (Single Actions List — grab-bag list with no completion goal, cannot auto-complete). `sequential` (boolean) is retained for backwards compatibility. `completedByChildren` (boolean) — true if the project auto-completes when its last remaining action is completed. `dueDate`, `deferDate`, `plannedDate` — project-level dates in ISO format (empty string if not set). Tasks inherit effective dates from their containing project. With include_task_health: remainingCount, availableCount, overdueCount, deferredCount, stalled, health status. `stalled` (boolean) — true when availableCount=0 and tasks are not just deferred (project needs attention). With include_last_activity: lastActivityDate.

---

### create_project

Create a new project in OmniFocus.

**Parameters:**
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

**Returns:** Success message with project ID and configuration details

---

### update_project

Update an existing project in OmniFocus.

Consolidates: set_project_status(), drop_project(), set_review_interval(), mark_project_reviewed()

**Parameters:**
- `project_id: str` (required) — The ID of the project to update
- `project_name: str` (optional) — New project name
- `folder_path: str` (optional) — Folder path to move project to (e.g., "Work : Projects")
- `note: str` (optional) — New note content. WARNING: Removes rich text formatting.
- `project_type: str` (optional) — Change project type: "parallel", "sequential", or "single_actions"
- `sequential: str` (optional, DEPRECATED) — Use project_type instead. Sequential setting - "true" or "false"
- `status: str` (optional) — Project status - "active", "on_hold", "done", or "dropped"
- `review_interval_weeks: int` (optional) — Review interval in weeks (0 to clear)
- `last_reviewed: str` (optional) — Last reviewed date in ISO format or "now"
- `next_review_date: str` (optional) — Explicit next review date in ISO format — overrides the date OmniFocus calculates from last_reviewed + review_interval
- `completed_by_children: bool` (optional) — Auto-complete the project when its last remaining action is completed
- `due_date: str` (optional) — Due date in ISO 8601 format, or "" to clear
- `defer_date: str` (optional) — Defer date in ISO 8601 format, or "" to clear
- `planned_date: str` (optional) — Planned date in ISO 8601 format, or "" to clear

**Returns:** Success message with project ID and updated fields, or error message

---

### update_projects

Update multiple projects with the same properties (batch version of update_project).

IMPORTANT: This function does NOT accept project_name or note parameters because those require unique values for each project.

**Parameters:**
- `project_ids: str | list[str]` (required) — Single project ID or list of project IDs
- `folder_path: str` (optional) — Folder path to move projects to
- `sequential: str` (optional) — Sequential setting ("true" or "false")
- `status: str` (optional) — Project status - "active", "on_hold", "done", "dropped"
- `review_interval_weeks: int` (optional) — Review interval in weeks
- `last_reviewed: str` (optional) — Last review date ("now" or ISO format)
- `next_review_date: str` (optional) — Explicit next review date in ISO format
- `due_date: str` (optional) — Due date in ISO 8601 format, or "" to clear
- `defer_date: str` (optional) — Defer date in ISO 8601 format, or "" to clear
- `planned_date: str` (optional) — Planned date in ISO 8601 format, or "" to clear

**Returns:** Success message with updated and failed counts

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

**Returns:** Each task includes: id, name, projectName, completed, dropped, blocked, available, next, flagged, dueDate, deferDate, plannedDate, estimatedMinutes, tags, note (truncated unless include_full_notes=True), parentTaskId, subtaskCount, sequential, isRecurring, recurrence, repetitionMethod, repeatSummary, nextDueDate, nextDeferDate, nextPlannedDate, catchUpAutomatically.
`available` is true when the task is actionable — not completed, not dropped, not blocked, not deferred, and not inside a completed or dropped container (project or parent task). This accounts for inherited status: a task in a done project shows `completed: false` but `available: false` because its container is inactive. Use `available_only=True` to get only truly actionable tasks.

Note: Date fields (dueDate, deferDate, plannedDate) reflect effective dates — including dates inherited from the containing project or action group. A task with no direct due date will show its project's due date in dueDate. Example: if project "Q2 Report" has dueDate=April 15, a task in that project with no direct due date will return dueDate="2026-04-15T17:00:00" in get_tasks output (inherited from project, not empty). Write operations (update_task) still set the task's own date directly. Next occurrence fields (nextDueDate, nextDeferDate, nextPlannedDate) are populated only for recurring tasks and show the dates of the next recurrence — empty for non-recurring tasks. `catchUpAutomatically` (boolean, null for non-recurring) controls missed-recurrence behavior: when true, only one catch-up occurrence is created if a task is missed; when false, each missed interval spawns its own occurrence (can flood the inbox).

Note: `repeatSummary` is a human-readable version of the recurrence RRULE (e.g., "Every 2 weeks on Mon, Wed, Fri"). Use this for user-facing output instead of parsing the raw `recurrence` string. `repetitionMethod` indicates how the next occurrence is calculated: "fixed" (next occurrence on the original schedule regardless of when completed — e.g., if due every Monday, completing on Wednesday still makes the next occurrence due Monday), "start_after_completion" (next defer date = completion date + interval — e.g., complete Wednesday, next defer = following Wednesday), "due_after_completion" (next due date = completion date + interval — e.g., complete Wednesday, next due = following Wednesday). Use `due_after_completion` when you want the **deadline** to shift based on completion; use `start_after_completion` when you want the **availability window** (defer date) to shift instead. Recurrence rules can be set, modified, or removed via `update_task(recurrence=..., repetition_method=...)`. Use standard iCalendar RRULE format (e.g., `FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,WE,FR`). Pass `recurrence=""` to remove recurrence.

---

### create_task

Create a new task in OmniFocus.

- If project_id is provided: Create task in that project
- If parent_task_id is provided: Create task as subtask under that parent
- If neither provided: Create task in inbox

**Parameters:**
- `task_name: str` (required) — The name/title of the task
- `project_id: str` (optional) — Project ID. If None, creates in inbox (unless parent_task_id is set). Mutually exclusive with parent_task_id — a subtask inherits its parent's project.
- `parent_task_id: str` (optional) — Parent task ID to create as subtask. Mutually exclusive with project_id — a subtask inherits its parent's project.
- `note: str` (optional) — Note/description (plain text only)
- `due_date: str` (optional) — Due date in ISO 8601 format (e.g., '2025-10-15' or '2025-10-15T17:00:00')
- `defer_date: str` (optional) — Defer date in ISO 8601 format (when task becomes available — hidden until then)
- `planned_date: str` (optional) — Planned date in ISO 8601 format (when you plan to work on this task — a scheduling signal with no availability or overdue constraints, unlike defer/due dates)
- `flagged: bool` (default: False) — Flag marks a task as a priority — typically 'I want to work on this today.' Flagged tasks can be queried with get_tasks(flagged_only=True).
- `tags: str` (optional) — JSON array string of tag names (e.g., '["Computer", "Work"]'). Tags must already exist. Note: this takes a JSON string; update_task takes a native list instead.
- `estimated_minutes: int` (optional) — Estimated time in minutes
- `sequential: bool` (default: False) — If True, subtasks of this task (action group) must be completed in order — only the first available subtask is actionable.

**Note:** In sequential projects, tasks are ordered by creation time. Create tasks in the desired dependency order.

**Returns:** Success message with task ID and location (project/inbox/parent)

---

### update_task

Update an existing task in OmniFocus.

Consolidates: complete_task(), drop_task(), move_task(), set_parent_task(), set_estimated_minutes(), add_tag_to_task()

**Parameters:**
- `task_id: str` (required) — The ID of the task to update
- `task_name: str` (optional) — New task name
- `project_id: str` (optional) — Move task to this project. Mutually exclusive with parent_task_id.
- `parent_task_id: str` (optional) — Make task a subtask of this parent. Mutually exclusive with project_id.
- `note: str` (optional) — New note content. WARNING: Removes rich text formatting.
- `due_date: str` (optional) — New due date in ISO 8601 format, or empty string to clear. Omitting means no change.
- `defer_date: str` (optional) — New defer date in ISO 8601 format (when task becomes available), or empty string to clear. Omitting means no change.
- `planned_date: str` (optional) — Planned date in ISO 8601 format (when you plan to work on this task), or empty string to clear. A scheduling signal with no availability or overdue constraints.
- `flagged: bool` (optional) — Flag marks a task as a priority — typically 'I want to work on this today.' Pass True to flag, False to unflag.
- `tags: list[str]` (optional) — Full replacement — set exact tag list as a native list. Conflicts with add_tags/remove_tags. Note: unlike create_task, this takes a list not a JSON string.
- `add_tags: list[str]` (optional) — Add these tags incrementally. Conflicts with tags.
- `remove_tags: list[str]` (optional) — Remove these tags. Conflicts with tags.
- `estimated_minutes: int` (optional) — Estimated time in minutes
- `completed: bool` (optional) — Mark task complete/incomplete. Uses `mark complete` internally, which correctly handles recurring tasks by spawning the next occurrence.
- `status: str` (optional) — Task status - "active" or "dropped"
- `recurrence: str` (optional) — iCalendar RRULE string (e.g., "FREQ=WEEKLY;BYDAY=MO,WE,FR"), or empty string to remove recurrence. Omitting means no change.
- `repetition_method: str` (optional) — How the next occurrence is calculated. Values: "fixed" (next occurrence on the original schedule regardless of when completed), "start_after_completion" (next defer date = completion date + interval), "due_after_completion" (next due date = completion date + interval). Only meaningful when recurrence is set.
- `sequential: bool` (optional) — If True, subtasks of this task (action group) must be completed in order. If False, subtasks are parallel (all available). Omitting means no change.

**Returns:** Success message with updated fields, or error message

**Examples:**
- `update_task("task-123", completed=True)` — Mark complete
- `update_task("task-123", status="dropped")` — Drop task
- `update_task("task-123", project_id="proj-456")` — Move to project
- `update_task("task-123", add_tags=["urgent"])` — Add tag
- `update_task("task-123", recurrence="FREQ=WEEKLY;BYDAY=MO,WE,FR", repetition_method="fixed")` — Set weekly recurrence
- `update_task("task-123", recurrence="")` — Remove recurrence

---

### update_tasks

Update multiple tasks with the same field values (batch version of update_task).

Key differences from update_task():
- Accepts str | list[str] for task_ids (single or multiple)
- Does NOT accept task_name or note (require unique values per task)
- Returns count-based summary
- Continues processing when individual tasks fail

**Parameters:**
- `task_ids: str | list[str]` (required) — Single task ID or list of task IDs
- `flagged: bool` (optional) — Flag/unflag all tasks
- `status: str` (optional) — "active" or "dropped"
- `completed: bool` (optional) — Mark all tasks complete/incomplete
- `project_id: str` (optional) — Move all tasks to this project. Mutually exclusive with parent_task_id.
- `parent_task_id: str` (optional) — Make all tasks subtasks of this parent. Mutually exclusive with project_id.
- `tags: list[str]` (optional) — Full replacement for all tasks. Conflicts with add_tags.
- `add_tags: list[str]` (optional) — Add these tags to all tasks. Conflicts with tags.
- `remove_tags: list[str]` (optional) — Remove these tags from all tasks.
- `due_date: str` (optional) — Set due date for all, or empty string to clear.
- `defer_date: str` (optional) — Set defer date for all, or empty string to clear.
- `planned_date: str` (optional) — Set planned date for all, or empty string to clear.
- `estimated_minutes: int` (optional) — Set estimated time for all tasks.
- `sequential: bool` (optional) — If True, subtasks of these tasks (action groups) must be completed in order. If False, subtasks are parallel.

**Returns:** Summary with counts of successful/failed updates

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
- `before_task_id: str` (optional) — Move the task before this task (provide either this OR after_task_id)
- `after_task_id: str` (optional) — Move the task after this task (provide either this OR before_task_id)

**Returns:** Success message confirming the task was reordered

**Note:** Both tasks must be in the same project and at the same level. Exactly one of before_task_id or after_task_id must be provided.

---

### get_folders

Get all folders from OmniFocus with their hierarchy.

**Parameters:** None

**Returns:** Each folder includes: id, name, path (hierarchical, e.g. "Work > Clients"), status ("active" or "dropped"). Dropped folders and their contents are hidden from most OmniFocus views.

---

### create_folder

Create a new folder in OmniFocus.

**Parameters:**
- `name: str` (required) — The name of the folder to create
- `parent_path: str` (optional) — Parent folder path (e.g., "Work" or "Work > Clients")

**Returns:** Success message with folder ID and full path

---

### update_folder

Update an existing folder in OmniFocus.

**Parameters:**
- `folder_id: str` (required) — The ID of the folder to update
- `name: str` (optional) — New folder name
- `status: str` (optional) — Folder status: "active" or "dropped". Dropping a folder hides it and drops all contained projects.

**Returns:** Success message with updated fields, or error message

---

### get_tags

Retrieve all available tags from OmniFocus.

Tags (formerly 'contexts') represent contexts for doing work — location (Office, Home), tools (Computer, Phone), energy level (High, Low), people, or workflow states (Waiting-for, Agenda). They cut across projects and are used for filtering tasks via get_tasks(tag_filter=[...]).

**Parameters:** None

**Returns:** Each tag includes: id, name, status (values: "active", "on hold", "dropped"), parentTagId (empty string if top-level, parent tag's ID if nested), childrenAreMutuallyExclusive (boolean — when true, child tags are mutually exclusive: assigning one child tag to a task silently removes any other child from the same group).

---

### create_tag

Create a new tag in OmniFocus.

Tags can be nested (e.g., create "High" under parent "Energy" to get "Energy : High").

**Parameters:**
- `name: str` (required) — The name of the tag to create
- `parent_tag: str` (optional) — Parent tag name for nesting. Parent tag must already exist.
- `children_are_mutually_exclusive: bool` (default: False) — If True, child tags of this tag will be mutually exclusive — assigning one child tag to a task silently removes any other child from the same group.

**Returns:** Success message with tag ID and name

---

### update_tag

Update properties of an existing tag in OmniFocus.

Tags can be renamed or have their status changed. Tags have three states: active (tasks are actionable), on_hold (tasks excluded from available queries), and dropped (tag hidden from most views).

**Parameters:**
- `tag_id: str` (required) — The ID of the tag to update (from get_tags)
- `name: str` (optional) — New tag name
- `status: str` (optional) — Tag status. Values: "active", "on_hold", "dropped". Active = tasks with this tag are actionable. On hold = tag is paused, **tasks with this tag become unavailable** (excluded from Available perspective) — use for temporary pauses. Dropped = tag is retired/archived, **tasks remain available** but the tag is hidden from most views — use for permanent retirement.
- `children_are_mutually_exclusive: bool` (optional) — If True, child tags of this tag will be mutually exclusive. If False, children are independent (default behavior).

**Returns:** Success message with updated fields, or error message

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

OmniFocus supports focusing on projects and folders only. Call with no arguments (or empty lists) to clear focus.

**Parameters:**
- `item_ids: str | list[str]` (optional) — Single ID or list of IDs to focus on. Omit or pass empty to clear.
- `item_types: str | list[str]` (optional) — Matching type(s) - each must be "project" or "folder".

**Returns:** Success message confirming focus set or cleared

---

### get_focus

Get the currently focused items in OmniFocus.

**Parameters:** None

**Returns:** Formatted list of currently focused items, or a message if no focus is set
