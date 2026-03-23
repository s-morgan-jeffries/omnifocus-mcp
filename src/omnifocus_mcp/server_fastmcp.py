#!/usr/bin/env python3
"""FastMCP Server for OmniFocus integration."""
import os
from typing import Optional, Union

from fastmcp import FastMCP
from pydantic import BaseModel

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
    stalled_only: bool = False,
    include_dropped: bool = False,
    tag_filter: Optional[list[str]] = None
) -> str:
    """Retrieve projects from OmniFocus with optional filtering.

    Args:
        project_id: Filter to specific project by ID (optional)
        include_full_notes: Return full note content (default: False)
        on_hold_only: If True, only return projects with "on hold" status
        query: Optional search term to filter by name, note, or folder path (case-insensitive)
        include_task_health: If True, include per-project task health counts (remaining, available, overdue, deferred)
        include_last_activity: If True, compute lastActivityDate (most recent task creation/completion)
        stalled_only: If True, only return active projects with no available actions — projects that need attention (implies include_task_health=True)
        include_dropped: If True, include dropped projects in results (default: False — dropped projects are hidden)
        tag_filter: Only return projects with ALL specified tags (case-insensitive)

    Returns:
        Each project includes: id, name, folderPath, status, projectType, sequential,
        completedByChildren, creationDate, tags, note (truncated unless include_full_notes=True).
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
            include_dropped=include_dropped,
            tag_filter=tag_filter,
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
    elif include_dropped:
        descriptor = "projects (including dropped)"
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
    """DEPRECATED: Use create_projects instead. Creates a single project in OmniFocus.

    This function is kept for backward compatibility. It delegates to
    create_projects([{...}]) internally. Prefer create_projects for new code.
    """
    return create_projects(projects=[{
        "name": name,
        "note": note,
        "folder_path": folder_path,
        "project_type": project_type,
        "sequential": sequential,
        "review_interval_weeks": review_interval_weeks,
        "completed_by_children": completed_by_children,
        "due_date": due_date,
        "defer_date": defer_date,
        "planned_date": planned_date,
    }])


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
    inbox_only: bool = False,
    planned_after: Optional[str] = None,
    planned_before: Optional[str] = None,
    planned_on: Optional[str] = None,
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
        planned_after: Only return tasks with planned date on or after this ISO date (optional)
        planned_before: Only return tasks with planned date before this ISO date (optional)
        planned_on: Only return tasks planned for this specific date, e.g., "2026-03-23" (optional).
            Convenience for planned_after=date + planned_before=next_day. Mutually exclusive
            with planned_after/planned_before.

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
    # Expand planned_on to planned_after + planned_before
    if planned_on is not None:
        if planned_after is not None or planned_before is not None:
            return "Error: planned_on is mutually exclusive with planned_after/planned_before."
        from datetime import date, timedelta
        try:
            d = date.fromisoformat(planned_on)
            planned_after = planned_on
            planned_before = (d + timedelta(days=1)).isoformat()
        except ValueError:
            return f"Error: Invalid date format for planned_on: '{planned_on}'. Use ISO 8601 (e.g., '2026-03-23')."

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
            inbox_only=inbox_only,
            planned_after=planned_after,
            planned_before=planned_before,
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
    """DEPRECATED: Use create_tasks instead. Creates a single task in OmniFocus.

    This function is kept for backward compatibility. It delegates to
    create_tasks([{...}]) internally. Prefer create_tasks for new code.
    """
    return create_tasks(tasks=[{
        "task_name": task_name,
        "project_id": project_id,
        "parent_task_id": parent_task_id,
        "note": note,
        "due_date": due_date,
        "defer_date": defer_date,
        "planned_date": planned_date,
        "flagged": flagged,
        "tags": tags,
        "estimated_minutes": estimated_minutes,
        "sequential": sequential,
        "completed_by_children": completed_by_children,
    }])


# ============================================================================
# Unified Batch Create (v0.12.0)
# ============================================================================


class TaskCreate(BaseModel):
    """Input model for creating a task."""
    task_name: str
    project_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    note: Optional[str] = None
    due_date: Optional[str] = None
    defer_date: Optional[str] = None
    planned_date: Optional[str] = None
    flagged: bool = False
    tags: Optional[list[str]] = None
    estimated_minutes: Optional[int] = None
    sequential: bool = False
    completed_by_children: bool = False


class ProjectCreate(BaseModel):
    """Input model for creating a project."""
    name: str
    note: Optional[str] = None
    folder_path: Optional[str] = None
    project_type: Optional[str] = None
    sequential: bool = False
    review_interval_weeks: Optional[int] = None
    completed_by_children: Optional[bool] = None
    due_date: Optional[str] = None
    defer_date: Optional[str] = None
    planned_date: Optional[str] = None


class TaskUpdate(BaseModel):
    """Input model for updating a task."""
    id: str
    task_name: Optional[str] = None
    project_id: Optional[str] = None
    parent_task_id: Optional[str] = None
    note: Optional[str] = None
    due_date: Optional[str] = None
    defer_date: Optional[str] = None
    planned_date: Optional[str] = None
    flagged: Optional[bool] = None
    tags: Optional[list[str]] = None
    add_tags: Optional[list[str]] = None
    remove_tags: Optional[list[str]] = None
    estimated_minutes: Optional[int] = None
    completed: Optional[bool] = None
    status: Optional[str] = None
    recurrence: Optional[str] = None
    repetition_method: Optional[str] = None
    sequential: Optional[bool] = None
    completed_by_children: Optional[bool] = None


@mcp.tool()
def create_tasks(tasks: list[TaskCreate]) -> str:
    """Create one or more tasks in OmniFocus.

    Pass a list of task objects. Each task must have a task_name; all other
    fields are optional. For a single task, pass a list with one item.

    Args:
        tasks: List of task objects to create. Each object supports:
            task_name (required), project_id, parent_task_id, note, due_date,
            defer_date, planned_date, flagged, tags, estimated_minutes,
            sequential, completed_by_children.

    Returns:
        For single task: success message with task ID.
        For multiple tasks: summary with per-item results.

    Examples:
        create_tasks([{"task_name": "Buy groceries"}])
        create_tasks([
            {"task_name": "Task A", "project_id": "proj-1", "flagged": true},
            {"task_name": "Task B", "tags": ["work"], "due_date": "2026-04-01"}
        ])
    """
    client = get_client()
    results = []

    # Coerce dicts to TaskCreate (MCP protocol does this automatically,
    # but direct Python calls from tests pass raw dicts)
    try:
        tasks = [TaskCreate(**t) if isinstance(t, dict) else t for t in tasks]
    except Exception as e:
        return f"Error: Invalid task input: {e}"

    for task in tasks:
        try:
            task_id = client.create_task(**task.model_dump())
            results.append({
                "task_name": task.task_name,
                "task_id": task_id,
                "success": True,
            })
        except (ValueError, Exception) as e:
            results.append({
                "task_name": task.task_name,
                "success": False,
                "error": str(e),
            })

    succeeded = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    # Single task: match old create_task format
    if len(tasks) == 1:
        r = results[0]
        if r["success"]:
            task = tasks[0]
            location = f"in project {task.project_id}" if task.project_id else \
                       f"as subtask of {task.parent_task_id}" if task.parent_task_id else \
                       "in inbox"
            result = f"Successfully created task '{task.task_name}' {location}\nTask ID: {r['task_id']}"
            if task.due_date:
                result += f"\nDue date: {task.due_date}"
            if task.flagged:
                result += "\nFlagged: Yes"
            if task.tags:
                result += f"\nTags: {', '.join(task.tags)}"
            return result
        else:
            return f"Error: {r['error']}"

    # Multiple tasks: summary
    lines = [f"Created {len(succeeded)} of {len(tasks)} tasks:"]
    for r in succeeded:
        lines.append(f"  - {r['task_name']}: {r['task_id']}")
    for r in failed:
        lines.append(f"  - {r['task_name']}: FAILED — {r['error']}")
    return "\n".join(lines)


# ============================================================================
# Unified Batch Create Projects (v0.11.0)
# ============================================================================


@mcp.tool()
def create_projects(projects: list[ProjectCreate]) -> str:
    """Create one or more projects in OmniFocus.

    Pass a list of project objects. Each must have a name; all other fields optional.

    Args:
        projects: List of project objects to create. Each object supports:
            name (required), note, folder_path, project_type, sequential,
            review_interval_weeks, completed_by_children, due_date,
            defer_date, planned_date.

    Returns:
        For single project: success message with project ID.
        For multiple projects: summary with per-item results.

    Examples:
        create_projects([{"name": "Website Redesign"}])
        create_projects([
            {"name": "Project A", "folder_path": "Work", "project_type": "sequential"},
            {"name": "Project B", "due_date": "2026-04-01"}
        ])
    """
    client = get_client()

    # Coerce dicts to ProjectCreate (MCP protocol does this automatically,
    # but direct Python calls from tests pass raw dicts)
    try:
        projects = [ProjectCreate(**p) if isinstance(p, dict) else p for p in projects]
    except Exception as e:
        return f"Error: Invalid project input: {e}"

    results = []
    for project in projects:
        try:
            project_id = client.create_project(**project.model_dump())
            results.append({
                "name": project.name,
                "project_id": project_id,
                "success": True,
            })
        except (ValueError, Exception) as e:
            results.append({
                "name": project.name,
                "success": False,
                "error": str(e),
            })

    succeeded = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    # Single project: match old create_project format
    if len(projects) == 1:
        r = results[0]
        if r["success"]:
            proj = projects[0]
            effective_type = proj.project_type or ("sequential" if proj.sequential else "parallel")
            type_labels = {
                "sequential": "Sequential (tasks completed in order)",
                "parallel": "Parallel (tasks can be done in any order)",
                "single_actions": "Single Actions List (grab-bag, no completion goal)",
            }
            result = f"Successfully created project '{proj.name}'"
            result += f"\nProject ID: {r['project_id']}"
            if proj.folder_path:
                result += f"\nFolder: {proj.folder_path}"
            result += f"\nType: {type_labels.get(effective_type, effective_type)}"
            if proj.review_interval_weeks:
                result += f"\nReview Interval: Every {proj.review_interval_weeks} week(s)"
            if proj.note:
                result += f"\nNote: {_truncate_note(proj.note)}"
            return result
        else:
            return f"Error: {r['error']}"

    # Multiple projects: summary
    lines = [f"Created {len(succeeded)} of {len(projects)} projects:"]
    for r in succeeded:
        lines.append(f"  - {r['name']}: {r['project_id']}")
    for r in failed:
        lines.append(f"  - {r['name']}: FAILED — {r['error']}")
    return "\n".join(lines)


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
) -> str:
    """DEPRECATED: Use update_tasks instead. Update a single task in OmniFocus.

    Delegates to update_tasks with a single-item list.

    Args:
        task_id: The ID of the task to update
        task_name: New task name (optional)
        project_id: Move task to this project (optional)
        parent_task_id: Make task a subtask of this parent (optional)
        note: New note content (optional)
        due_date: New due date in ISO 8601 format, or empty string to clear (optional)
        defer_date: New defer date in ISO 8601 format, or empty string to clear (optional)
        planned_date: Planned date in ISO 8601 format, or empty string to clear (optional)
        flagged: Flag/unflag the task (optional)
        tags: Full replacement tag list (optional)
        add_tags: Add these tags incrementally (optional)
        remove_tags: Remove these tags (optional)
        estimated_minutes: Estimated time in minutes (optional)
        completed: Mark task complete/incomplete (optional)
        status: Task status — "active" or "dropped" (optional)
        recurrence: iCalendar RRULE string, or empty string to remove (optional)
        repetition_method: "fixed", "start_after_completion", or "due_after_completion" (optional)
        sequential: If True, subtasks must be completed in order (optional)
        completed_by_children: If True, auto-complete when subtasks done (optional)

    Returns:
        Success message with updated fields, or error message
    """
    # Build task dict from non-None params
    params = locals()
    task_dict = {"id": params.pop("task_id")}
    for k, v in params.items():
        if v is not None:
            task_dict[k] = v
    return update_tasks(tasks=[task_dict])


@mcp.tool()
def update_tasks(tasks: list[TaskUpdate]) -> str:
    """Update one or more tasks in OmniFocus.

    Pass a list of task update objects. Each must have an id field.
    Only the specified fields will be updated — omitted fields are unchanged.

    Args:
        tasks: List of task update objects. Each must have:
            id (required), plus any fields to update: task_name, project_id,
            parent_task_id, note, due_date, defer_date, planned_date, flagged,
            tags, add_tags, remove_tags, estimated_minutes, completed, status,
            recurrence, repetition_method, sequential, completed_by_children.

    Returns:
        For single task: success message with updated fields.
        For multiple tasks: summary with per-item results.

    Examples:
        update_tasks([{"id": "t1", "flagged": true}])
        update_tasks([
            {"id": "t1", "flagged": true},
            {"id": "t2", "task_name": "Renamed", "due_date": "2026-04-01"}
        ])
    """
    client = get_client()

    # Coerce dicts to TaskUpdate
    try:
        tasks = [TaskUpdate(**t) if isinstance(t, dict) else t for t in tasks]
    except Exception as e:
        return f"Error: Invalid task input: {e}"

    results = []
    for task in tasks:
        try:
            # Build kwargs, excluding None values and the id field
            kwargs = task.model_dump(exclude_none=True, exclude={"id"})
            result = client.update_task(task_id=task.id, **kwargs)
            results.append({
                "id": task.id,
                "success": result["success"],
                "updated_fields": result.get("updated_fields", []),
                "error": result.get("error"),
            })
        except (ValueError, Exception) as e:
            results.append({
                "id": task.id,
                "success": False,
                "updated_fields": [],
                "error": str(e),
            })

    succeeded = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    # Single task: match old update_task format
    if len(tasks) == 1:
        r = results[0]
        if r["success"]:
            fields = r["updated_fields"]
            if len(fields) == 0:
                return f"Successfully updated task {r['id']} (no changes detected)"
            elif len(fields) == 1:
                return f"Successfully updated task {r['id']}: {fields[0]}"
            else:
                return f"Successfully updated task {r['id']}: {', '.join(fields)}"
        else:
            return f"Error updating task {r['id']}: {r['error']}"

    # Multiple tasks: summary
    lines = [f"Updated {len(succeeded)} of {len(tasks)} tasks:"]
    for r in succeeded:
        lines.append(f"  - {r['id']}: {', '.join(r['updated_fields'])}")
    for r in failed:
        lines.append(f"  - {r['id']}: FAILED — {r['error']}")
    return "\n".join(lines)





@mcp.tool()
def get_tags() -> str:
    """Retrieve all available tags from OmniFocus.

    Tags (formerly 'contexts') represent contexts for doing work — location (Office, Home),
    tools (Computer, Phone), energy level (High, Low), people, or workflow states
    (Waiting-for, Agenda). They cut across projects and are used for filtering tasks
    via get_tasks(tag_filter=[...]).

    Returns:
        Each tag includes: id, name, status, parentTagId, childrenAreMutuallyExclusive.
        `parentTagId` is the parent tag's ID (empty string if top-level). Note: create_tag()
        and update_tag() accept parent_tag by NAME, not by this ID.
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
        parent_tag: Optional parent tag by NAME (not ID) for nesting (e.g., "Energy" to create
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
        parent_tag: Move this tag under a different parent tag by NAME (not ID), or empty
            string to move to top level. Preserves all task associations. Note: get_tags()
            returns parentTagId by ID, but this parameter accepts the tag's name. (optional)

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
        before_task_id: Place task immediately BEFORE this reference task (provide either this OR after_task_id).
            Example: reorder_task("C", before_task_id="A") results in [..., C, A, ...]
        after_task_id: Place task immediately AFTER this reference task (provide either this OR before_task_id).
            Example: reorder_task("C", after_task_id="A") results in [..., A, C, ...]

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
        before_project_id: Place project immediately BEFORE this reference project (provide either this OR after_project_id).
            Example: reorder_project("C", before_project_id="A") results in [..., C, A, ...]
        after_project_id: Place project immediately AFTER this reference project (provide either this OR before_project_id).
            Example: reorder_project("C", after_project_id="A") results in [..., A, C, ...]

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
