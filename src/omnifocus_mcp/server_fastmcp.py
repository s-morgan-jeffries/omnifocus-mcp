#!/usr/bin/env python3
"""FastMCP Server for OmniFocus integration."""
import os
from typing import Optional, Union

from fastmcp import FastMCP

from .omnifocus_connector import OmniFocusConnector

# Create FastMCP server
mcp = FastMCP("omnifocus-mcp", instructions="""OmniFocus is a GTD (Getting Things Done) task manager. Key concepts:

TASK STATES: Available (can work on now), Blocked (waiting on predecessor in sequential project), Deferred (has future defer date — hidden until then), Flagged (user marked as priority/today), Overdue (past due date), Completed, Dropped.

PROJECT STATES: Active (tasks are actionable), On Hold (paused — tasks hidden), Dropped (abandoned), Completed.

HIERARCHY: Folders → Projects → Tasks → Subtasks. Folders organize projects. Projects contain tasks. Tasks can have subtasks via parent_task_id.

SEQUENTIAL VS PARALLEL: Sequential projects release one task at a time (first incomplete = available, rest = blocked). Parallel projects make all tasks available. Dependencies are positional — reorder tasks to change dependency chains. There are no explicit task-to-task dependency links. The `next` field on a task is true when it is the first available action in a sequential project or action group. In parallel projects, all incomplete tasks have `next: true`.

ACTION GROUPS: A task with subtasks is an "action group." It can be parallel or sequential, just like a project. The parent task appears as `blocked: true` while its subtasks are active — this is normal behavior, not an error or a problem to fix. Check `subtaskCount > 0` to identify action groups. An action group parent cannot be completed until its subtasks are resolved. If you see a task with `blocked: true` and `subtaskCount > 0`, it means "work on the subtasks first" — do not try to unblock it.

INHERITED STATUS: Task-level fields like `completed` and `dropped` reflect the task's own state, NOT its container's state. A task inside a completed project will show `completed: false` (because the task itself wasn't individually completed) but `available: false` (because its container is inactive). This is expected behavior. To find truly actionable tasks, always use `available` or `available_only=True` — do not rely on `completed` alone.

EFFECTIVE DATES: Date fields (dueDate, deferDate, plannedDate) returned by get_tasks are EFFECTIVE dates — they include dates inherited from the containing project. A task with no direct due date in a project with dueDate=April 15 will return dueDate="2026-04-15T17:00:00" (not empty). Do not assume an empty due date on a task means the project has no due date either. Write operations (update_task) set the task's own date directly.

BATCH OPERATIONS: When applying the same change to multiple items, prefer the batch tools (update_tasks, update_projects) over multiple individual calls. Batch tools accept a list of IDs and are more efficient.

RECURRING TASKS: Setting completed=True on a recurring task uses OmniFocus's 'mark complete' command, which automatically creates the next occurrence. This is guaranteed behavior — do not hedge or warn that recurrence might stop.

TAGS: Formerly "contexts." Represent work contexts (location, tools, energy, people, workflow states like Waiting-for or Agenda). Cut across projects. Use for filtering. Tags can be Active or On Hold — tasks with On Hold tags are excluded from OmniFocus's native Available perspective.

PLANNING PATTERN: To plan a day, query: (1) overdue tasks, (2) flagged + available tasks, (3) inbox items, (4) next actions. Prioritize overdue+flagged first.

INBOX: Unprocessed capture bucket. Tasks without a project land here. Non-empty inbox = items need organizing.

REVIEW: Projects have review intervals. Use get_projects() to find projects due for review (check last_reviewed + review_interval_weeks).
""")

# Configuration
NOTE_TRUNCATION_LENGTH = 100  # Maximum note length in get_projects/get_tasks responses

# Initialize OmniFocus client (lazy)
_client: Optional[OmniFocusConnector] = None


def get_client() -> OmniFocusConnector:
    """Get or create the OmniFocus client."""
    global _client
    if _client is None:
        # Disable safety checks if in pytest environment (for integration tests with mocked AppleScript)
        _in_pytest = os.environ.get('PYTEST_CURRENT_TEST') is not None
        _client = OmniFocusConnector(enable_safety_checks=not _in_pytest)
    return _client


def _truncate_note(note: str, max_length: int = NOTE_TRUNCATION_LENGTH) -> str:
    """Truncate note with ellipsis if too long.

    Args:
        note: The note text to truncate
        max_length: Maximum length before truncation (default: NOTE_TRUNCATION_LENGTH)

    Returns:
        Truncated note with "..." appended if it exceeds max_length
    """
    if len(note) > max_length:
        return note[:max_length] + "..."
    return note


def _format_task(task: dict, truncate_notes: bool = True) -> str:
    """Format a task dictionary as human-readable text.

    Args:
        task: Task dictionary from omnifocus_connector
        truncate_notes: If True, truncate notes to preview length. If False, show full notes.

    Returns:
        Formatted task text with all properties
    """
    result = f"ID: {task['id']}\n"
    result += f"Name: {task['name']}\n"
    result += f"Project: {task.get('projectName', 'N/A')}\n"
    result += f"Completed: {task['completed']}\n"

    if task.get('dropped'):
        result += f"Dropped: Yes\n"
    if task.get('blocked'):
        # Show blocked status with explanation if it has available subtasks
        if task.get('numberOfAvailableTasks', 0) > 0:
            result += f"Blocked: Yes (but has {task['numberOfAvailableTasks']} available subtask(s))\n"
        else:
            result += f"Blocked: Yes\n"
    if task.get('available') is not None:
        result += f"Available: {task['available']}\n"
    if task.get('next'):
        result += f"Next: Yes\n"
    if task.get('flagged'):
        result += f"Flagged: Yes\n"
    if task.get('inInbox'):
        result += f"In Inbox: Yes\n"
    if task.get('dueDate'):
        result += f"Due: {task['dueDate']}\n"
    if task.get('deferDate'):
        result += f"Defer: {task['deferDate']}\n"
    if task.get('plannedDate'):
        result += f"Planned: {task['plannedDate']}\n"
    if task.get('nextDueDate'):
        result += f"Next Due: {task['nextDueDate']}\n"
    if task.get('nextDeferDate'):
        result += f"Next Defer: {task['nextDeferDate']}\n"
    if task.get('nextPlannedDate'):
        result += f"Next Planned: {task['nextPlannedDate']}\n"
    if task.get('creationDate'):
        result += f"Created: {task['creationDate']}\n"
    if task.get('modificationDate'):
        result += f"Modified: {task['modificationDate']}\n"
    if task.get('completionDate'):
        result += f"Completed Date: {task['completionDate']}\n"
    if task.get('droppedDate'):
        result += f"Dropped Date: {task['droppedDate']}\n"
    if task.get('estimatedMinutes'):
        result += f"Estimated: {task['estimatedMinutes']} minutes\n"
    if task.get('repeatSummary'):
        result += f"Repeats: {task['repeatSummary']}\n"
    elif task.get('isRecurring'):
        result += f"Repeats: {task.get('recurrence', 'Yes')}\n"
    if task.get('catchUpAutomatically') is not None:
        result += f"Catch Up Automatically: {task['catchUpAutomatically']}\n"
    if task.get('tags'):
        result += f"Tags: {task['tags']}\n"
    if task.get('note'):
        note_text = task['note'] if not truncate_notes else _truncate_note(task['note'])
        result += f"Note: {note_text}\n"

    # Hierarchy fields
    if 'parentTaskId' in task:
        if task['parentTaskId']:
            result += f"Parent Task ID: {task['parentTaskId']}\n"
        else:
            result += f"Parent Task ID: (none - root level)\n"
    if 'subtaskCount' in task:
        result += f"Subtask Count: {task['subtaskCount']}\n"
    if 'sequential' in task:
        result += f"Sequential: {task['sequential']}\n"
    if 'completedByChildren' in task:
        result += f"Completed By Children: {task['completedByChildren']}\n"
    if 'position' in task:
        result += f"Position: {task['position']}\n"

    return result


def _format_project(proj: dict, truncate_notes: bool = True) -> str:
    """Format a project dictionary as human-readable text.

    Args:
        proj: Project dictionary from omnifocus_connector
        truncate_notes: If True, truncate notes to preview length. If False, show full notes.

    Returns:
        Formatted project text with all properties
    """
    result = f"ID: {proj['id']}\n"
    result += f"Name: {proj['name']}\n"
    if proj.get('folderPath'):
        result += f"Folder: {proj['folderPath']}\n"
    result += f"Status: {proj['status']}\n"
    if 'sequential' in proj:
        result += f"Sequential: {proj['sequential']}\n"
    if proj.get('creationDate'):
        result += f"Created: {proj['creationDate']}\n"
    if proj.get('modificationDate'):
        result += f"Modified: {proj['modificationDate']}\n"
    if proj.get('completionDate'):
        result += f"Completed Date: {proj['completionDate']}\n"
    if proj.get('droppedDate'):
        result += f"Dropped Date: {proj['droppedDate']}\n"
    if proj.get('lastReviewDate'):
        result += f"Last Review: {proj['lastReviewDate']}\n"
    if proj.get('nextReviewDate'):
        result += f"Next Review: {proj['nextReviewDate']}\n"
    if proj.get('note'):
        note_text = proj['note'] if not truncate_notes else _truncate_note(proj['note'])
        result += f"Note: {note_text}\n"

    # Task health fields (when include_task_health=True)
    if 'remainingCount' in proj:
        result += f"Remaining Tasks: {proj['remainingCount']}\n"
        result += f"Available Tasks: {proj['availableCount']}\n"
        result += f"Overdue Tasks: {proj['overdueCount']}\n"
        result += f"Deferred Tasks: {proj['deferredCount']}\n"
        # Health status
        if proj.get('availableCount', 0) > 0:
            result += "Health: On Track\n"
        elif proj.get('hasDeferredOnly'):
            result += "Health: Appropriately Scheduled\n"
        elif proj.get('remainingCount', 0) == 0:
            result += "Health: No Remaining Tasks\n"
        else:
            result += "Health: Stuck\n"
        if proj.get('stalled'):
            result += "Stalled: Yes\n"

    # Last activity (when include_last_activity=True)
    if proj.get('lastActivityDate'):
        result += f"Last Activity: {proj['lastActivityDate']}\n"

    return result


# ============================================================================
# Project Tools
# ============================================================================

@mcp.tool()
def get_projects(
    project_id: Optional[str] = None,
    include_full_notes: bool = False,
    on_hold_only: bool = False,
    query: Optional[str] = None,
    include_task_health: bool = False,
    include_last_activity: bool = False,
    stalled_only: bool = False
) -> str:
    """Retrieve ALL active projects with full details and hierarchy, optionally filtered by search query.

    Args:
        project_id: Filter to specific project by ID (optional)
        include_full_notes: Return full note content (default: False)
        on_hold_only: If True, only return projects with "on hold" status
        query: Optional search term to filter by name, note, or folder path (case-insensitive)
        include_task_health: If True, include per-project task health counts (remaining, available, overdue, deferred)
        include_last_activity: If True, compute lastActivityDate (most recent task creation/completion)
        stalled_only: If True, only return active projects with no available actions — projects that need attention (implies include_task_health=True)

    Returns:
        Each project includes: id, name, folderPath, status, projectType, sequential,
        completedByChildren, creationDate, note (truncated unless include_full_notes=True).
        `projectType` is "sequential", "parallel", or "single_actions" (Single Actions List —
        a grab-bag list with no completion goal). `sequential` (boolean) is retained for
        backwards compatibility. `completedByChildren` (boolean) indicates whether the project
        auto-completes when its last remaining action is completed.
        With include_task_health: remainingCount, availableCount, overdueCount, deferredCount, stalled, health status.
        `stalled` (boolean) — true when availableCount=0 and not all tasks are deferred (project needs attention).
        With include_last_activity: lastActivityDate.
    """
    client = get_client()
    try:
        projects = client.get_projects(
            project_id=project_id,
            include_full_notes=include_full_notes,
            on_hold_only=on_hold_only,
            query=query,
            include_task_health=include_task_health,
            include_last_activity=include_last_activity,
            stalled_only=stalled_only,
        )
    except ValueError as e:
        return f"Error: {str(e)}"

    # Build descriptor based on filter
    if project_id:
        descriptor = "project"
    elif on_hold_only:
        descriptor = "on-hold projects"
    elif stalled_only:
        descriptor = "stalled projects"
    else:
        descriptor = "active projects"

    if not projects:
        if query:
            return f"No {descriptor} found matching '{query}'"
        return f"Found 0 {descriptor}"

    # Format projects for display
    if query:
        result = f"Found {len(projects)} {descriptor} matching '{query}':\n\n"
    else:
        result = f"Found {len(projects)} {descriptor}:\n\n"
    for proj in projects:
        result += _format_project(proj, truncate_notes=(not include_full_notes))
        result += "\n"

    return result


@mcp.tool()
def create_project(
    name: str,
    note: Optional[str] = None,
    folder_path: Optional[str] = None,
    sequential: bool = False,
    project_type: Optional[str] = None,
    review_interval_weeks: Optional[int] = None,
    completed_by_children: Optional[bool] = None,
    due_date: Optional[str] = None,
    defer_date: Optional[str] = None,
    planned_date: Optional[str] = None,
) -> str:
    """Create a new project in OmniFocus.

    Args:
        name: The name of the project
        note: Optional note/description for the project (plain text only - rich text formatting is not supported via automation APIs)
        folder_path: Optional folder path (e.g., "Work > Clients") - folder must exist in OmniFocus
        project_type: Project type — "parallel" (default, all tasks available simultaneously),
            "sequential" (tasks completed in order, only first available), or "single_actions"
            (grab-bag list with no completion goal, cannot auto-complete). Overrides sequential
            when provided.
        sequential: DEPRECATED — use project_type instead. If True, creates a sequential project.
            Ignored when project_type is provided. (default: False)
        review_interval_weeks: Optional review interval in weeks for GTD review cycle
        completed_by_children: Auto-complete the project when its last remaining action is completed. (optional)
        due_date: Due date in ISO 8601 format (e.g., "2025-10-15" or "2025-10-15T17:00:00")
        defer_date: Defer date in ISO 8601 format (when project becomes available)
        planned_date: Planned date in ISO 8601 format (when you plan to work on the project)

    Returns:
        Success message with project ID and configuration details
    """
    client = get_client()
    try:
        project_id = client.create_project(
            name=name,
            note=note,
            folder_path=folder_path,
            sequential=sequential,
            project_type=project_type,
            review_interval_weeks=review_interval_weeks,
            completed_by_children=completed_by_children,
            due_date=due_date,
            defer_date=defer_date,
            planned_date=planned_date,
        )
    except ValueError as e:
        return f"Error: {str(e)}"

    effective_type = project_type or ("sequential" if sequential else "parallel")
    type_labels = {
        "sequential": "Sequential (tasks completed in order)",
        "parallel": "Parallel (tasks can be done in any order)",
        "single_actions": "Single Actions List (grab-bag, no completion goal)",
    }
    result = f"Successfully created project '{name}'"
    result += f"\nProject ID: {project_id}"
    if folder_path:
        result += f"\nFolder: {folder_path}"
    result += f"\nType: {type_labels.get(effective_type, effective_type)}"
    if review_interval_weeks:
        result += f"\nReview Interval: Every {review_interval_weeks} week(s)"
    if note:
        result += f"\nNote: {_truncate_note(note)}"

    return result


@mcp.tool()
def update_project(
    project_id: str,
    project_name: Optional[str] = None,
    folder_path: Optional[str] = None,
    note: Optional[str] = None,
    sequential: Optional[bool] = None,
    project_type: Optional[str] = None,
    status: Optional[str] = None,
    review_interval_weeks: Optional[int] = None,
    last_reviewed: Optional[str] = None,
    next_review_date: Optional[str] = None,
    completed_by_children: Optional[bool] = None,
    due_date: Optional[str] = None,
    defer_date: Optional[str] = None,
    planned_date: Optional[str] = None,
    flagged: Optional[bool] = None,
    estimated_minutes: Optional[int] = None,
    tags: Optional[list[str]] = None,
    add_tags: Optional[list[str]] = None,
    remove_tags: Optional[list[str]] = None,
    recurrence: Optional[str] = None,
    repetition_method: Optional[str] = None,
) -> str:
    """Update an existing project in OmniFocus.

    Args:
        project_id: The ID of the project to update
        project_name: New project name (optional)
        folder_path: Folder path to move project to (e.g., "Work : Projects")
        note: New note content (optional). WARNING: Removes rich text formatting.
        project_type: Change project type — "parallel", "sequential", or "single_actions" (optional)
        sequential: DEPRECATED — use project_type instead. (optional)
        status: Project status - "active", "on_hold", "done", or "dropped"
        review_interval_weeks: Review interval in weeks (0 to clear)
        last_reviewed: Last reviewed date in ISO format or "now"
        next_review_date: Explicit next review date in ISO format — overrides the date OmniFocus calculates from last_reviewed + review_interval. (optional)
        completed_by_children: Auto-complete the project when its last remaining action is completed. (optional)
        due_date: Due date in ISO 8601 format, or "" to clear (optional)
        defer_date: Defer date in ISO 8601 format, or "" to clear (optional)
        planned_date: Planned date in ISO 8601 format, or "" to clear (optional)
        flagged: Flag marks a project as a priority — pass True to flag, False to unflag. (optional)
        estimated_minutes: Estimated time in minutes (optional)
        tags: Full replacement — set exact tag list as a native list (optional, conflicts
            with add_tags/remove_tags).
        add_tags: Add these tags incrementally (optional, conflicts with tags)
        remove_tags: Remove these tags (optional, conflicts with tags)
        recurrence: iCalendar RRULE string (e.g., "FREQ=WEEKLY;INTERVAL=2;BYDAY=MO"),
            or empty string to remove recurrence. Omitting means no change. (optional)
        repetition_method: How the next occurrence is calculated (optional). Only meaningful
            when recurrence is set. Values: "fixed", "start_after_completion",
            "due_after_completion".

    Returns:
        Success message with project ID and updated fields, or error message
    """
    client = get_client()
    try:
        result = client.update_project(
            project_id=project_id,
            project_name=project_name,
            folder_path=folder_path,
            note=note,
            sequential=sequential,
            project_type=project_type,
            status=status,
            review_interval_weeks=review_interval_weeks,
            last_reviewed=last_reviewed,
            next_review_date=next_review_date,
            completed_by_children=completed_by_children,
            due_date=due_date,
            defer_date=defer_date,
            planned_date=planned_date,
            flagged=flagged,
            estimated_minutes=estimated_minutes,
            tags=tags,
            add_tags=add_tags,
            remove_tags=remove_tags,
            recurrence=recurrence,
            repetition_method=repetition_method,
        )
    except ValueError as e:
        return f"Error: {str(e)}"

    # Handle dict return from client
    if result["success"]:
        updated_fields = result["updated_fields"]
        field_count = len(updated_fields)

        if field_count == 1:
            response = f"Successfully updated project {project_id}: {updated_fields[0]}"
        else:
            response = f"Successfully updated project {project_id}: {field_count} fields ({', '.join(updated_fields)})"

        return response
    else:
        error_msg = result.get("error", "Unknown error")
        return f"Error updating project {project_id}: {error_msg}"


@mcp.tool()
def update_projects(
    project_ids: Union[str, list[str]],
    folder_path: Optional[str] = None,
    sequential: Optional[bool] = None,
    status: Optional[str] = None,
    review_interval_weeks: Optional[int] = None,
    last_reviewed: Optional[str] = None,
    next_review_date: Optional[str] = None,
    due_date: Optional[str] = None,
    defer_date: Optional[str] = None,
    planned_date: Optional[str] = None,
    flagged: Optional[bool] = None,
    estimated_minutes: Optional[int] = None,
    add_tags: Optional[list[str]] = None,
    remove_tags: Optional[list[str]] = None,
) -> str:
    """Update multiple projects with the same properties.

    This is the BATCH version of update_project(). It updates multiple projects
    with the same values. This is more efficient than calling update_project()
    multiple times.

    IMPORTANT: This function does NOT accept project_name or note parameters
    because those require unique values for each project.

    Args:
        project_ids: Single project ID (str) or list of project IDs to update
        folder_path: Folder path to move projects to (e.g., "Work > Projects")
        sequential: Sequential setting (optional)
        status: Project status - one of: "active", "on_hold", "done", "dropped"
        review_interval_weeks: Review interval in weeks
        last_reviewed: Last review date ("now" or ISO format like "2025-01-15")
        next_review_date: Explicit next review date in ISO format — overrides OmniFocus-calculated date (optional)
        due_date: Due date in ISO 8601 format, or "" to clear (optional)
        defer_date: Defer date in ISO 8601 format, or "" to clear (optional)
        planned_date: Planned date in ISO 8601 format, or "" to clear (optional)
        flagged: Flag marks projects as a priority — pass True to flag, False to unflag. (optional)
        estimated_minutes: Estimated time in minutes (optional)
        add_tags: Add these tags incrementally (optional)
        remove_tags: Remove these tags (optional)

    Returns:
        Success message with updated and failed counts, or error message

    Example:
        # Drop multiple projects at once
        update_projects(
            project_ids=["proj-001", "proj-002", "proj-003"],
            status="dropped"
        )
    """
    try:
        client = get_client()
        result = client.update_projects(
            project_ids=project_ids,
            folder_path=folder_path,
            sequential=sequential,
            status=status,
            review_interval_weeks=review_interval_weeks,
            last_reviewed=last_reviewed,
            next_review_date=next_review_date,
            due_date=due_date,
            defer_date=defer_date,
            planned_date=planned_date,
            flagged=flagged,
            estimated_minutes=estimated_minutes,
            add_tags=add_tags,
            remove_tags=remove_tags,
        )

        # Handle dict return from client
        updated_count = result["updated_count"]
        failed_count = result["failed_count"]
        failures = result["failures"]

        if failed_count == 0:
            # All succeeded
            if updated_count == 1:
                return f"Successfully updated 1 project"
            else:
                return f"Successfully updated {updated_count} projects"
        elif updated_count == 0:
            # All failed
            error_details = "; ".join([f"{f['project_id']}: {f['error']}" for f in failures])
            return f"Error: Failed to update {failed_count} projects. {error_details}"
        else:
            # Partial success
            error_details = "; ".join([f"{f['project_id']}: {f['error']}" for f in failures])
            return (f"Partially updated: {updated_count} succeeded, {failed_count} failed. "
                   f"Failures: {error_details}")

    except ValueError as e:
        # Parameter validation errors
        return f"Error: {str(e)}"
    except Exception as e:
        # Other errors
        return f"Error updating projects: {str(e)}"




@mcp.tool()
def get_tasks(
    task_id: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    include_full_notes: bool = False,
    project_id: Optional[str] = None,
    flagged_only: bool = False,
    include_completed: bool = False,
    available_only: bool = False,
    overdue: bool = False,
    dropped_only: bool = False,
    blocked_only: bool = False,
    next_only: bool = False,
    tag_filter: Optional[list[str]] = None,
    query: Optional[str] = None,
    inbox_only: bool = False
) -> str:
    """Get tasks from OmniFocus with optional filtering.

    Args:
        task_id: Filter to specific task by ID (optional)
        parent_task_id: Filter to subtasks of this parent task (optional)
        include_full_notes: Return full note content (default: False)
        project_id: Optional project ID to filter tasks (ignored if inbox_only=True)
        flagged_only: If True, only return flagged tasks
        include_completed: If True, include completed tasks (default: False)
        available_only: If True, only return available tasks (not completed, not dropped, not blocked, not deferred)
        overdue: If True, only return overdue tasks
        dropped_only: If True, only return dropped tasks
        blocked_only: If True, only return blocked tasks
        next_only: If True, only return next tasks
        tag_filter: List of tag names to filter by, e.g., ["Errands", "Weekend"] (task must have ALL listed tags)
        query: Optional search term to filter by name or note (case-insensitive)
        inbox_only: If True, only return inbox tasks

    Returns:
        Each task includes: id, name, projectName, completed, dropped, blocked, available, next,
        flagged, inInbox, dueDate, deferDate, plannedDate, estimatedMinutes, tags, note (truncated
        unless include_full_notes=True), parentTaskId, subtaskCount, sequential, nextDueDate,
        nextDeferDate, nextPlannedDate, catchUpAutomatically.
        `available` is true when the task is not completed, not dropped, not blocked, and not
        deferred (defer date is in the past or unset). Equivalent to OmniFocus's native Available
        filter.

    Note: Date fields (dueDate, deferDate, plannedDate) reflect effective dates — including
    dates inherited from the containing project or action group. A task with no direct due
    date will show its project's due date in dueDate. Example: if project "Q2 Report" has
    dueDate=April 15, a task with no direct due date returns dueDate="2026-04-15T17:00:00"
    (inherited, not empty). Write operations (update_task) still set the task's own date
    directly. Next occurrence fields (nextDueDate, nextDeferDate,
    nextPlannedDate) are populated only for recurring tasks and show the dates of the next
    recurrence — empty for non-recurring tasks. `catchUpAutomatically` (boolean, null for
    non-recurring) controls missed-recurrence behavior: when true, only one catch-up
    occurrence is created; when false, each missed interval spawns its own occurrence.
    """
    client = get_client()
    try:
        tasks = client.get_tasks(
            task_id=task_id,
            parent_task_id=parent_task_id,
            include_full_notes=include_full_notes,
            project_id=project_id,
            flagged_only=flagged_only,
            include_completed=include_completed,
            available_only=available_only,
            overdue=overdue,
            dropped_only=dropped_only,
            blocked_only=blocked_only,
            next_only=next_only,
            tag_filter=tag_filter,
            query=query,
            inbox_only=inbox_only
        )
    except ValueError as e:
        return f"Error: {str(e)}"

    if not tasks:
        if query:
            return f"No tasks found matching '{query}'"
        elif inbox_only:
            return "No tasks in inbox"
        return "Found 0 tasks"

    # Build descriptive result message
    if query and inbox_only:
        result = f"Found {len(tasks)} inbox tasks matching '{query}':\n\n"
    elif query:
        result = f"Found {len(tasks)} tasks matching '{query}':\n\n"
    elif inbox_only:
        result = f"Found {len(tasks)} inbox tasks:\n\n"
    else:
        result = f"Found {len(tasks)} tasks:\n\n"

    for task in tasks:
        result += _format_task(task, truncate_notes=(not include_full_notes))
        result += "\n"

    return result




@mcp.tool()
def create_task(
    task_name: str,
    project_id: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    note: Optional[str] = None,
    due_date: Optional[str] = None,
    defer_date: Optional[str] = None,
    planned_date: Optional[str] = None,
    flagged: bool = False,
    tags: Optional[list[str]] = None,
    estimated_minutes: Optional[int] = None,
    sequential: bool = False,
    completed_by_children: bool = False
) -> str:
    """Create a new task in OmniFocus.

    This is the redesigned create function that unifies task creation across all contexts:
    - If project_id is provided: Create task in that project
    - If parent_task_id is provided: Create task as subtask under that parent
    - If neither provided (or project_id=None): Create task in inbox

    Args:
        task_name: The name/title of the task (required)
        project_id: Optional project ID. If None, creates in inbox (unless parent_task_id is set).
            Mutually exclusive with parent_task_id — a subtask inherits its parent's project.
        parent_task_id: Optional parent task ID to create as subtask.
            Mutually exclusive with project_id — a subtask inherits its parent's project.
        note: Optional note/description for the task (plain text only)
        due_date: Due date in ISO 8601 format (e.g., '2025-10-15' or '2025-10-15T17:00:00')
        defer_date: Defer date in ISO 8601 format (when task becomes available — hidden until then)
        planned_date: Planned date in ISO 8601 format — when you plan to work on the task.
            Unlike defer (controls availability) or due (controls overdue), planned date is
            purely a scheduling signal with no behavioral constraints.
        flagged: Flag marks a task as a priority — typically 'I want to work on this today.'
            Flagged tasks can be queried with get_tasks(flagged_only=True). (default: False)
        tags: Optional list of tag names (e.g., ["Computer", "Work"]). Tags must already exist.
        estimated_minutes: Estimated time in minutes to complete the task
        sequential: If True, subtasks of this task (action group) must be completed in order —
            only the first available subtask is actionable. (default: False = parallel)
        completed_by_children: If True, this task (action group) is automatically marked complete
            when all its subtasks are completed. (default: False)

    Returns:
        Success message with task ID and location (project/inbox/parent)

    Note:
        In sequential projects, tasks are ordered by creation time. Create tasks
        in the desired dependency order.

    Raises:
        ValueError: If both project_id and parent_task_id are specified
    """
    client = get_client()

    # Validate tags parameter
    if tags is not None and not isinstance(tags, list):
        return f"Error: tags must be a list of tag names, e.g., [\"Computer\", \"Work\"]. Got {type(tags).__name__}."

    try:
        task_id = client.create_task(
            task_name=task_name,
            project_id=project_id,
            parent_task_id=parent_task_id,
            note=note,
            due_date=due_date,
            defer_date=defer_date,
            planned_date=planned_date,
            flagged=flagged,
            tags=tags,
            estimated_minutes=estimated_minutes,
            sequential=sequential,
            completed_by_children=completed_by_children
        )
    except ValueError as e:
        return f"Error: {str(e)}"

    # Build human-readable response
    if parent_task_id:
        location = f"as subtask under {parent_task_id}"
    elif project_id:
        location = f"in project {project_id}"
    else:
        location = "in inbox"

    result = f"Successfully created task '{task_name}' {location}\nTask ID: {task_id}"

    if due_date:
        result += f"\nDue date: {due_date}"
    if defer_date:
        result += f"\nDefer date: {defer_date}"
    if flagged:
        result += "\nFlagged: Yes"
    if tags:
        result += f"\nTags: {', '.join(tags)}"
    if estimated_minutes:
        result += f"\nEstimated time: {estimated_minutes} minutes"

    return result



@mcp.tool()
def update_task(
    task_id: str,
    task_name: Optional[str] = None,
    project_id: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    note: Optional[str] = None,
    due_date: Optional[str] = None,
    defer_date: Optional[str] = None,
    planned_date: Optional[str] = None,
    flagged: Optional[bool] = None,
    tags: Optional[list[str]] = None,
    add_tags: Optional[list[str]] = None,
    remove_tags: Optional[list[str]] = None,
    estimated_minutes: Optional[int] = None,
    completed: Optional[bool] = None,
    status: Optional[str] = None,
    recurrence: Optional[str] = None,
    repetition_method: Optional[str] = None,
    sequential: Optional[bool] = None,
    completed_by_children: Optional[bool] = None,
    # Legacy parameters (backward compatibility)
    name: Optional[str] = None
) -> str:
    """Update an existing task in OmniFocus.

    Args:
        task_id: The ID of the task to update
        task_name: New task name (optional)
        project_id: Move task to this project (optional). Mutually exclusive with
            parent_task_id — a subtask inherits its parent's project.
        parent_task_id: Make task a subtask of this parent (optional). Mutually exclusive
            with project_id — a subtask inherits its parent's project.
        note: New note content (optional). WARNING: Removes rich text formatting
        due_date: New due date in ISO 8601 format, or empty string to clear.
            Omitting means no change. (optional)
        defer_date: New defer date in ISO 8601 format (when task becomes available), or
            empty string to clear. Omitting means no change. (optional)
        planned_date: Planned date in ISO 8601 format, or empty string to clear.
            When you plan to work on the task — purely a scheduling signal, no behavioral
            constraints (unlike defer/due). Omitting means no change. (optional)
        flagged: Flag marks a task as a priority — typically 'I want to work on this today.'
            Pass True to flag, False to unflag. (optional)
        tags: Full replacement — set exact tag list as a native list (optional, conflicts
            with add_tags/remove_tags).
        add_tags: Add these tags incrementally (optional, conflicts with tags)
        remove_tags: Remove these tags (optional, conflicts with tags)
        estimated_minutes: Estimated time in minutes (optional)
        completed: Mark task complete/incomplete (optional). Uses `mark complete` internally,
            which correctly handles recurring tasks by spawning the next occurrence.
        status: Task status - "active" or "dropped" (optional). To drop an entire
            recurring series (not just the current occurrence), pass both
            recurrence="" and status="dropped" in the same call.
        recurrence: iCalendar RRULE string (e.g., "FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,WE,FR"),
            or empty string to remove recurrence. Omitting means no change. (optional)
        repetition_method: How the next occurrence is calculated (optional). Only meaningful
            when recurrence is set. Values: "fixed" (next occurrence on the original schedule
            regardless of when completed), "start_after_completion" (next defer date =
            completion date + interval), "due_after_completion" (next due date = completion
            date + interval). Use due_after_completion when you want the deadline to shift
            based on completion; use start_after_completion when you want the availability
            window (defer date) to shift instead.
        sequential: If True, subtasks of this task (action group) must be completed in order.
            If False, subtasks are parallel (all available). Omitting means no change. (optional)
        completed_by_children: If True, this task (action group) is automatically marked complete
            when all its subtasks are completed. If False, requires manual completion. Omitting
            means no change. (optional)
        name: DEPRECATED - Use task_name instead (optional, for backward compatibility)

    Returns:
        Success message with updated fields, or error message

    Examples:
        update_task("task-123", completed=True)  # Mark complete
        update_task("task-123", status="dropped")  # Drop task
        update_task("task-123", project_id="proj-456")  # Move to project
        update_task("task-123", add_tags=["urgent"])  # Add tag
        update_task("task-123", task_name="New Name", flagged=True, due_date="2025-12-31")
        update_task("task-123", recurrence="FREQ=WEEKLY;BYDAY=MO,WE,FR", repetition_method="fixed")
        update_task("task-123", recurrence="")  # Remove recurrence
        update_task("task-123", recurrence="", status="dropped")  # Drop entire recurring series
    """
    # Support legacy 'name' parameter for backward compatibility
    if name is not None and task_name is None:
        task_name = name

    client = get_client()
    try:
        result = client.update_task(
            task_id=task_id,
            task_name=task_name,
            project_id=project_id,
            parent_task_id=parent_task_id,
            note=note,
            due_date=due_date,
            defer_date=defer_date,
            planned_date=planned_date,
            flagged=flagged,
            tags=tags,
            add_tags=add_tags,
            remove_tags=remove_tags,
            estimated_minutes=estimated_minutes,
            completed=completed,
            status=status,
            recurrence=recurrence,
            repetition_method=repetition_method,
            sequential=sequential,
            completed_by_children=completed_by_children,
            name=name  # Pass to client for its own backward compat handling
        )
    except ValueError as e:
        return f"Error: {str(e)}"

    # Handle dict return from client (NEW API)
    if result["success"]:
        fields = result["updated_fields"]
        if len(fields) == 0:
            return f"Successfully updated task {task_id} (no changes detected)"
        elif len(fields) == 1:
            return f"Successfully updated task {task_id}: {fields[0]}"
        else:
            fields_str = ", ".join(fields)
            return f"Successfully updated task {task_id}: {fields_str}"
    else:
        error_msg = result.get("error", "Unknown error")
        return f"Error updating task {task_id}: {error_msg}"


@mcp.tool()
def update_tasks(
    task_ids: Union[str, list[str]],
    flagged: Optional[bool] = None,
    status: Optional[str] = None,
    completed: Optional[bool] = None,
    project_id: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    tags: Optional[list[str]] = None,
    add_tags: Optional[list[str]] = None,
    remove_tags: Optional[list[str]] = None,
    due_date: Optional[str] = None,
    defer_date: Optional[str] = None,
    planned_date: Optional[str] = None,
    estimated_minutes: Optional[int] = None
) -> str:
    """Update multiple tasks with the same field values.

    This is the batch version of update_task(). It applies uniform changes to
    multiple tasks simultaneously.

    Key differences from update_task():
    - Accepts Union[str, list[str]] for task_ids (single or multiple)
    - Does NOT accept task_name or note (require unique values per task)
    - Returns count-based summary instead of single success/failure
    - Continues processing when individual tasks fail

    Args:
        task_ids: Single task ID (str) or list of task IDs to update
        flagged: Flag/unflag all tasks (optional)
        status: Set status for all tasks - "active" or "dropped" (optional)
        completed: Mark all tasks complete/incomplete (optional)
        project_id: Move all tasks to this project (optional). Mutually exclusive with
            parent_task_id — a subtask inherits its parent's project.
        parent_task_id: Make all tasks subtasks of this parent (optional). Mutually exclusive
            with project_id — a subtask inherits its parent's project.
        tags: Full replacement - set exact tag list for all tasks (optional, conflicts with add_tags)
        add_tags: Add these tags to all tasks (optional, conflicts with tags)
        remove_tags: Remove these tags from all tasks (optional)
        due_date: Set due date for all tasks in ISO 8601 format, or empty string to clear.
            Omitting means no change. (optional)
        defer_date: Set defer date for all tasks in ISO 8601 format, or empty string to clear.
            Omitting means no change. (optional)
        planned_date: Set planned date for all tasks in ISO 8601 format, or empty string to clear.
            When you plan to work on the tasks — purely a scheduling signal. (optional)
        estimated_minutes: Set estimated time in minutes for all tasks (optional)

    Returns:
        Summary message with counts of successful/failed updates

    Examples:
        update_tasks(["task-001", "task-002"], flagged=True)  # Flag multiple tasks
        update_tasks("task-123", completed=True)  # Complete single task (Union type)
        update_tasks(["task-001", "task-002", "task-003"], status="dropped")  # Drop multiple
    """
    client = get_client()
    try:
        result = client.update_tasks(
            task_ids=task_ids,
            flagged=flagged,
            status=status,
            completed=completed,
            project_id=project_id,
            parent_task_id=parent_task_id,
            tags=tags,
            add_tags=add_tags,
            remove_tags=remove_tags,
            due_date=due_date,
            defer_date=defer_date,
            planned_date=planned_date,
            estimated_minutes=estimated_minutes
        )
    except ValueError as e:
        return f"Error: {str(e)}"

    # Handle dict return with counts
    updated_count = result["updated_count"]
    failed_count = result["failed_count"]

    # Build response message
    if failed_count == 0:
        # All succeeded
        if updated_count == 1:
            return f"Successfully updated 1 task"
        else:
            return f"Successfully updated {updated_count} tasks"
    elif updated_count == 0:
        # All failed
        failures = result.get("failures", [])
        if len(failures) == 1:
            error = failures[0].get("error", "Unknown error")
            return f"Failed to update task: {error}"
        else:
            return f"Failed to update all {failed_count} tasks"
    else:
        # Partial success
        return f"Updated {updated_count} tasks successfully, {failed_count} failed"





@mcp.tool()
def get_tags() -> str:
    """Retrieve all available tags from OmniFocus.

    Tags (formerly 'contexts') represent contexts for doing work — location (Office, Home),
    tools (Computer, Phone), energy level (High, Low), people, or workflow states
    (Waiting-for, Agenda). They cut across projects and are used for filtering tasks
    via get_tasks(tag_filter=[...]).

    Returns:
        Each tag includes: id, name, status, childrenAreMutuallyExclusive.
        `childrenAreMutuallyExclusive` (boolean) — when true, child tags are mutually
        exclusive: assigning one child tag to a task silently removes any other child
        from the same group. Read via OmniAutomation (defaults to false if unavailable).
    """
    client = get_client()
    tags = client.get_tags()

    if not tags:
        return "Found 0 tags"

    result = f"Found {len(tags)} tags:\n\n"
    for tag in tags:
        result += f"ID: {tag['id']}\n"
        result += f"Name: {tag['name']}\n"
        result += f"Status: {tag['status']}\n"
        if tag.get('childrenAreMutuallyExclusive'):
            result += "Children Are Mutually Exclusive: Yes\n"
        result += "\n"

    return result


@mcp.tool()
def create_tag(
    name: str,
    parent_tag: Optional[str] = None,
    children_are_mutually_exclusive: bool = False
) -> str:
    """Create a new tag in OmniFocus.

    Tags (formerly 'contexts') represent contexts for doing work — location, tools,
    energy level, people, or workflow states. Tags can be nested (e.g., create "High"
    under parent "Energy" to get "Energy : High").

    Args:
        name: The name of the tag to create
        parent_tag: Optional parent tag name for nesting (e.g., "Energy" to create
            "Energy : High"). Parent tag must already exist.
        children_are_mutually_exclusive: If True, child tags of this tag will be
            mutually exclusive — assigning one child tag to a task silently removes
            any other child from the same group. Set via OmniAutomation.

    Returns:
        Success message with tag ID and name

    Raises:
        ValueError: If a tag with the same name already exists
    """
    client = get_client()
    try:
        tag_id = client.create_tag(
            name=name,
            parent_tag=parent_tag,
            children_are_mutually_exclusive=children_are_mutually_exclusive
        )
    except ValueError as e:
        return f"Error: {str(e)}"

    result = f"Successfully created tag '{name}'\nTag ID: {tag_id}"
    if parent_tag:
        result += f"\nParent: {parent_tag}"

    return result


@mcp.tool()
def update_tag(
    tag_id: str,
    name: Optional[str] = None,
    status: Optional[str] = None,
    children_are_mutually_exclusive: Optional[bool] = None,
    parent_tag: Optional[str] = None
) -> str:
    """Update properties of an existing tag in OmniFocus.

    Tags can be renamed, reparented, or have their status changed. Tags have three
    states: active (tasks are actionable), on_hold (tasks excluded from available
    queries), and dropped (tag hidden from most views).

    Args:
        tag_id: The ID of the tag to update (from get_tags)
        name: New tag name (optional)
        status: Tag status (optional). Values: "active", "on_hold", "dropped".
            Active = tasks with this tag are actionable. On hold = tag is paused,
            tasks with this tag become unavailable (excluded from Available perspective)
            — use for temporary pauses. Dropped = tag is retired/archived, tasks remain
            available but the tag is hidden from most views — use for permanent retirement.
        children_are_mutually_exclusive: If True, child tags of this tag will be
            mutually exclusive — assigning one child tag to a task silently removes
            any other child from the same group. Set via OmniAutomation. (optional)
        parent_tag: Move this tag under a different parent tag (by name), or empty
            string to move to top level. Preserves all task associations. (optional)

    Returns:
        Success message with updated fields, or error message

    Examples:
        update_tag("tag-123", parent_tag="People")  # Move under "People"
        update_tag("tag-123", parent_tag="")  # Move to top level
    """
    client = get_client()
    try:
        result = client.update_tag(
            tag_id=tag_id,
            name=name,
            status=status,
            children_are_mutually_exclusive=children_are_mutually_exclusive,
            parent_tag=parent_tag
        )

        fields = ", ".join(result["updated_fields"])
        return f"Successfully updated tag {tag_id}\nUpdated fields: {fields}"
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error updating tag: {str(e)}"


@mcp.tool()
def delete_tags(tag_ids: Union[str, list[str]]) -> str:
    """Delete one or more tags from OmniFocus.

    WARNING: This permanently deletes the tags. Tasks that had these tags will
    lose the tag association but are not themselves deleted.

    Args:
        tag_ids: Single tag ID (str) or list of tag IDs to delete

    Returns:
        Summary of deleted tags with count and any errors encountered

    Examples:
        delete_tags("tag-123")  # Delete single tag
        delete_tags(["tag-001", "tag-002"])  # Delete multiple
    """
    client = get_client()
    try:
        result = client.delete_tags(tag_ids)

        deleted_count = result["deleted_count"]
        failed_count = result["failed_count"]

        if failed_count == 0:
            if deleted_count == 1:
                return "Successfully deleted 1 tag"
            else:
                return f"Successfully deleted {deleted_count} tags"
        elif deleted_count == 0:
            if failed_count == 1:
                return "Failed to delete tag (not found or error)"
            else:
                return f"Failed to delete all {failed_count} tags"
        else:
            return f"Deleted {deleted_count} tags successfully, {failed_count} failed"
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error deleting tags: {str(e)}"


@mcp.tool()
def delete_tasks(task_ids: Union[str, list[str]]) -> str:
    """Delete one or more tasks from OmniFocus.

    WARNING: This permanently deletes the tasks and cannot be undone.

    Args:
        task_ids: Single task ID (str) or list of task IDs to delete

    Returns:
        Summary of deleted tasks with count and any errors encountered

    Examples:
        delete_tasks("task-123")  # Delete single task
        delete_tasks(["task-001", "task-002", "task-003"])  # Delete multiple
    """
    client = get_client()
    try:
        result = client.delete_tasks(task_ids)


        deleted_count = result["deleted_count"]
        failed_count = result["failed_count"]

        # Build response message
        if failed_count == 0:
            # All succeeded
            if deleted_count == 1:
                return f"Successfully deleted 1 task"
            else:
                return f"Successfully deleted {deleted_count} tasks"
        elif deleted_count == 0:
            # All failed
            if failed_count == 1:
                return f"Failed to delete task (not found or error)"
            else:
                return f"Failed to delete all {failed_count} tasks"
        else:
            # Partial success
            return f"Deleted {deleted_count} tasks successfully, {failed_count} failed"
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error deleting tasks: {str(e)}"


@mcp.tool()
def delete_projects(project_ids: Union[str, list[str]]) -> str:
    """Delete one or more projects from OmniFocus.

    WARNING: This permanently deletes the projects and all their tasks. Cannot be undone.

    Args:
        project_ids: Single project ID (str) or list of project IDs to delete

    Returns:
        Summary of deleted projects with count and any errors encountered
    """
    client = get_client()
    try:
        result = client.delete_projects(project_ids)
        deleted_count = result["deleted_count"]
        failed_count = result["failed_count"]

        # Determine total count
        if isinstance(project_ids, str):
            total_count = 1
        else:
            total_count = len(project_ids)

        if failed_count == 0:
            if deleted_count == 1:
                return f"Successfully deleted 1 project"
            else:
                return f"Successfully deleted {deleted_count} projects"
        else:
            return f"Deleted {deleted_count} of {total_count} projects ({failed_count} failed)"
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error deleting projects: {str(e)}"


# ============================================================================
# Task Movement Tools
# ============================================================================





@mcp.tool()
def get_folders() -> str:
    """Get all folders from OmniFocus with their hierarchy.

    Returns:
        Each folder includes: id, name, path (hierarchical, e.g. "Work > Clients"),
        status ("active" or "dropped"). Dropped folders and their contents are hidden
        from most OmniFocus views.
    """
    client = get_client()
    folders = client.get_folders()

    if not folders:
        return "Found 0 folders"

    # Format folders for display
    result = f"Found {len(folders)} folders:\n\n"
    for folder in folders:
        result += f"ID: {folder['id']}\n"
        result += f"Name: {folder['name']}\n"
        result += f"Path: {folder['path']}\n"
        result += f"Status: {folder.get('status', 'active')}\n"
        result += "---\n"

    return result


@mcp.tool()
def create_folder(name: str, parent_path: Optional[str] = None) -> str:
    """Create a new folder in OmniFocus.

    Args:
        name: The name of the folder to create
        parent_path: Optional parent folder path (e.g., "Work" or "Work > Clients")

    Returns:
        Success message with folder ID and full path
    """
    client = get_client()
    try:
        folder_id = client.create_folder(name, parent_path)
        if parent_path:
            return f"Successfully created folder '{name}' in '{parent_path}' (ID: {folder_id})"
        else:
            return f"Successfully created folder '{name}' at root level (ID: {folder_id})"
    except Exception as e:
        return f"Error creating folder: {str(e)}"


@mcp.tool()
def update_folder(
    folder_id: str,
    name: Optional[str] = None,
    status: Optional[str] = None,
) -> str:
    """Update an existing folder in OmniFocus.

    Args:
        folder_id: The ID of the folder to update
        name: New folder name (optional)
        status: Folder status — "active" or "dropped". Dropping a folder hides it
            and drops all contained projects. (optional)

    Returns:
        Success message with updated fields, or error message
    """
    client = get_client()
    try:
        result = client.update_folder(folder_id=folder_id, name=name, status=status)
    except ValueError as e:
        return f"Error: {str(e)}"

    if result["success"]:
        updated_fields = result["updated_fields"]
        if len(updated_fields) == 1:
            return f"Successfully updated folder {folder_id}: {updated_fields[0]}"
        return f"Successfully updated folder {folder_id}: {len(updated_fields)} fields ({', '.join(updated_fields)})"
    else:
        error_msg = result.get("error", "Unknown error")
        return f"Error updating folder {folder_id}: {error_msg}"


# ============================================================================
# Task Hierarchy Tools
# ============================================================================

@mcp.tool()
def reorder_task(task_id: str, before_task_id: Optional[str] = None, after_task_id: Optional[str] = None) -> str:
    """Move a task before or after another task to change its position.

    Use this to reorder tasks within a project or within a parent task's subtasks.
    In sequential projects, task order determines dependencies — reordering changes
    which task is available next (first incomplete = available, rest = blocked).

    Args:
        task_id: The ID of the task to move
        before_task_id: Move the task before this task (provide either this OR after_task_id)
        after_task_id: Move the task after this task (provide either this OR before_task_id)

    Returns:
        Success message confirming the task was reordered

    Note:
        Both tasks must be in the same project and at the same level (both root-level or both subtasks of the same parent).
        Exactly one of before_task_id or after_task_id must be provided.
    """
    client = get_client()
    try:
        success = client.reorder_task(task_id, before_task_id, after_task_id)
        if success:
            if before_task_id:
                return f"Successfully moved task {task_id} before task {before_task_id}"
            else:
                return f"Successfully moved task {task_id} after task {after_task_id}"
        else:
            return f"Error: Failed to reorder task {task_id}"
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error reordering task: {str(e)}"


@mcp.tool()
def reorder_project(project_id: str, before_project_id: Optional[str] = None, after_project_id: Optional[str] = None) -> str:
    """Move a project before or after another project to change its position within a folder.

    Use this to reorder projects within a folder. Both projects must be in the same folder.

    Args:
        project_id: The ID of the project to move
        before_project_id: Move the project before this project (provide either this OR after_project_id)
        after_project_id: Move the project after this project (provide either this OR before_project_id)

    Returns:
        Success message confirming the project was reordered

    Note:
        Both projects must be in the same folder.
        Exactly one of before_project_id or after_project_id must be provided.
    """
    client = get_client()
    try:
        success = client.reorder_project(project_id, before_project_id, after_project_id)
        if success:
            if before_project_id:
                return f"Successfully moved project {project_id} before project {before_project_id}"
            else:
                return f"Successfully moved project {project_id} after project {after_project_id}"
        else:
            return f"Error: Failed to reorder project {project_id}"
    except ValueError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error reordering project: {str(e)}"




@mcp.tool()
def get_perspectives() -> str:
    """Get all perspectives from OmniFocus with type and ID information.

    Returns:
        Formatted list of perspectives with name, type (built-in/custom), and ID
    """
    client = get_client()
    perspectives = client.get_perspectives()

    if not perspectives:
        return "Found 0 perspectives"

    result = f"Found {len(perspectives)} perspectives:\n\n"
    for p in perspectives:
        parts = [p["name"]]
        parts.append(p.get("type", "unknown"))
        pid = p.get("id")
        if pid:
            parts.append(f"ID: {pid}")
        result += f"- {parts[0]} ({', '.join(parts[1:])})\n"

    return result


@mcp.tool()
def switch_perspective(perspective_name: str) -> str:
    """Switch the front window to a different perspective.

    Args:
        perspective_name: Name of the perspective to switch to

    Returns:
        Success message confirming perspective switch
    """
    client = get_client()
    try:
        result = client.switch_perspective(perspective_name)
        return f"Successfully switched to perspective: {result}"
    except Exception as e:
        return f"Error switching perspective: {str(e)}"


@mcp.tool()
def set_focus(
    item_ids: str | list[str] = None,
    item_types: str | list[str] = None,
) -> str:
    """Set focus on one or more items, or clear focus.

    OmniFocus supports focusing on projects and folders only (NOT tasks or tags). To highlight specific tasks, use update_task(flagged=True) instead.
    Call with no arguments (or empty lists) to clear focus.

    Args:
        item_ids: Single ID or list of IDs to focus on. Omit or pass empty to clear.
        item_types: Matching type(s) - each must be "project" or "folder".

    Returns:
        Success message confirming focus set or cleared
    """
    client = get_client()
    try:
        result = client.set_focus(item_ids=item_ids, item_types=item_types)
        action = result.get("action", "unknown")
        if action == "cleared":
            return "Focus cleared."
        focused = result.get("focused_items", [])
        items_desc = ", ".join(
            f"{item['type']} {item['id']}" for item in focused
        )
        return f"Focus set on {len(focused)} item(s): {items_desc}"
    except ValueError as e:
        return f"Invalid input: {str(e)}"
    except Exception as e:
        return f"Error setting focus: {str(e)}"


@mcp.tool()
def get_focus() -> str:
    """Get the currently focused items in OmniFocus.

    Returns:
        Formatted list of currently focused items, or a message if no focus is set
    """
    client = get_client()
    try:
        items = client.get_focus()
        if not items:
            return "No focus set."
        result = f"Currently focused on {len(items)} item(s):\n\n"
        for item in items:
            result += f"- {item['name']} ({item['type']}, ID: {item['id']})\n"
        return result
    except Exception as e:
        return f"Error getting focus: {str(e)}"


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    mcp.run()
