# OmniFocus MCP Tool Descriptions

This file contains exactly what an MCP-connected agent sees: the server instructions and all tool schemas with docstrings. Used as input for blind agent eval.

## Server Instructions

OmniFocus is a GTD (Getting Things Done) task manager. Key concepts:

TASK STATES: Available (can work on now), Blocked (waiting on predecessor in sequential project), Deferred (has future defer date — hidden until then), Flagged (user marked as priority/today), Overdue (past due date), Completed, Dropped.

PROJECT STATES: Active (tasks are actionable), On Hold (paused — tasks hidden), Dropped (abandoned), Completed.

HIERARCHY: Folders → Projects → Tasks → Subtasks. Folders organize projects. Projects contain tasks. Tasks can have subtasks via parent_task_id.

SEQUENTIAL VS PARALLEL: Sequential projects release one task at a time (first incomplete = available, rest = blocked). Parallel projects make all tasks available. Dependencies are positional — reorder tasks to change dependency chains. There are no explicit task-to-task dependency links. The `next` field on a task is true when it is the first available action in a sequential project or action group. In parallel projects, all incomplete tasks have `next: true`.

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

**Returns:** Each project includes: id, name, folderPath, status, sequential, creationDate, note (truncated unless include_full_notes=True). Note: `sequential` is true for sequential projects, false for both parallel projects and Single Actions Lists. With include_task_health: remainingCount, availableCount, overdueCount, deferredCount, health status. With include_last_activity: lastActivityDate.

---

### create_project

Create a new project in OmniFocus.

**Parameters:**
- `name: str` (required) — The name of the project
- `note: str` (optional) — Note/description (plain text only - rich text not supported via automation APIs)
- `folder_path: str` (optional) — Folder path (e.g., "Work > Clients") - folder must exist
- `sequential: bool` (default: False) — If True, tasks must be completed in order — the first incomplete task is 'available' and the rest are 'blocked.' If False, creates a parallel project where all tasks are available simultaneously. Note: Single Actions Lists (a third project type) cannot currently be created via this API. OmniFocus represents dependencies via task ordering in sequential projects; there are no explicit task-to-task dependency links.
- `review_interval_weeks: int` (optional) — Review interval in weeks for GTD review cycle

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
- `sequential: str` (optional) — Sequential setting - "true" or "false"
- `status: str` (optional) — Project status - "active", "on_hold", "done", or "dropped"
- `review_interval_weeks: int` (optional) — Review interval in weeks (0 to clear)
- `last_reviewed: str` (optional) — Last reviewed date in ISO format or "now"

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

**Returns:** Each task includes: id, name, projectName, completed, dropped, blocked, available, next, flagged, dueDate, deferDate, estimatedMinutes, tags, note (truncated unless include_full_notes=True), parentTaskId, subtaskCount, sequential.

Note: Date fields (dueDate, deferDate) show directly-assigned dates only. Tasks that inherit dates from their project or action group will show empty date fields even though they are functionally subject to those dates in OmniFocus.

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
- `flagged: bool` (default: False) — Flag marks a task as a priority — typically 'I want to work on this today.' Flagged tasks can be queried with get_tasks(flagged_only=True).
- `tags: str` (optional) — JSON array string of tag names (e.g., '["Computer", "Work"]'). Tags must already exist. Note: this takes a JSON string; update_task takes a native list instead.
- `estimated_minutes: int` (optional) — Estimated time in minutes

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
- `flagged: bool` (optional) — Flag marks a task as a priority — typically 'I want to work on this today.' Pass True to flag, False to unflag.
- `tags: list[str]` (optional) — Full replacement — set exact tag list as a native list. Conflicts with add_tags/remove_tags. Note: unlike create_task, this takes a list not a JSON string.
- `add_tags: list[str]` (optional) — Add these tags incrementally. Conflicts with tags.
- `remove_tags: list[str]` (optional) — Remove these tags. Conflicts with tags.
- `estimated_minutes: int` (optional) — Estimated time in minutes
- `completed: bool` (optional) — Mark task complete/incomplete. Uses `mark complete` internally, which correctly handles recurring tasks by spawning the next occurrence.
- `status: str` (optional) — Task status - "active" or "dropped"

**Returns:** Success message with updated fields, or error message

**Examples:**
- `update_task("task-123", completed=True)` — Mark complete
- `update_task("task-123", status="dropped")` — Drop task
- `update_task("task-123", project_id="proj-456")` — Move to project
- `update_task("task-123", add_tags=["urgent"])` — Add tag

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
- `estimated_minutes: int` (optional) — Set estimated time for all tasks.

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

**Returns:** Formatted hierarchical list of all folders with indentation showing nesting

---

### create_folder

Create a new folder in OmniFocus.

**Parameters:**
- `name: str` (required) — The name of the folder to create
- `parent_path: str` (optional) — Parent folder path (e.g., "Work" or "Work > Clients")

**Returns:** Success message with folder ID and full path

---

### get_tags

Retrieve all available tags from OmniFocus.

Tags (formerly 'contexts') represent contexts for doing work — location (Office, Home), tools (Computer, Phone), energy level (High, Low), people, or workflow states (Waiting-for, Agenda). They cut across projects and are used for filtering tasks via get_tasks(tag_filter=[...]).

**Parameters:** None

**Returns:** Each tag includes: id, name, status.

---

### create_tag

Create a new tag in OmniFocus.

Tags can be nested (e.g., create "High" under parent "Energy" to get "Energy : High").

**Parameters:**
- `name: str` (required) — The name of the tag to create
- `parent_tag: str` (optional) — Parent tag name for nesting. Parent tag must already exist.

**Returns:** Success message with tag ID and name

---

### update_tag

Update properties of an existing tag in OmniFocus.

Tags can be renamed or put on hold. Setting active=False puts a tag on hold — tasks with on-hold tags are excluded from available task queries.

**Parameters:**
- `tag_id: str` (required) — The ID of the tag to update (from get_tags)
- `name: str` (optional) — New tag name
- `active: bool` (optional) — Whether the tag is active. False = on hold (tasks become unavailable). True = active.

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
