#!/usr/bin/env python3
"""FastMCP Server for OmniFocus integration."""
import os
from typing import Optional, Union

from fastmcp import FastMCP
from pydantic import BaseModel

from .omnifocus_connector import OmniFocusConnector

# Create FastMCP server
mcp = FastMCP("omnifocus-mcp", instructions="""OmniFocus is a GTD task manager. Hierarchy: Folders > Projects > Tasks > Subtasks.

TASK STATES: Available, Blocked, Deferred (future defer date), Flagged, Overdue, Completed, Dropped. Planned Date is a scheduling signal only — no availability/overdue constraints.

PROJECT TYPES: "sequential" (tasks in order; first incomplete = available, rest blocked; position = dependencies), "parallel" (all available), "single_actions" (no completion goal, cannot auto-complete). The `next` field is true for the first available action in a sequential project/action group; in parallel projects, all incomplete tasks have `next: true`.

ACTION GROUPS: Task with subtasks. Parent shows `blocked: true` while subtasks are active — this is normal, not an error. Do not try to unblock it.

INHERITED STATUS: `completed`/`dropped` reflect the task's own state, not its container's. `effectivelyCompleted`/`effectivelyDropped` reflect the container's state — if true, the task's parent project or action group was completed/dropped. Task in completed project: `completed: false`, `effectivelyCompleted: true`, `available: false`. Use `available_only=True` for actionable tasks.

EFFECTIVE DATES: Dates returned by get_tasks are always effective (inherited). A task with no direct due date WILL show its project's due date in the dueDate field — this is correct behavior, not a bug. You cannot clear an inherited date at the task level. Write operations set the task's own date.

RECURRING TASKS: `completed=True` uses `mark complete`, which creates the next occurrence. This is guaranteed. WARNING: Dropping a recurring task (status='dropped') without clearing recurrence first (recurrence='') spawns the next occurrence. To stop a series: update_tasks([{"id": "...", "recurrence": "", "status": "dropped"}]).

TAGS: Represent work contexts. Tag statuses: Active (normal), On Hold (tasks excluded from Available perspective), Dropped (tag hidden from picker; does NOT affect task availability).

DEFER vs DUE: Defer = hidden until that date. Due = deadline.
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
    if proj.get('flagged'):
        result += "Flagged: True\n"
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
    if proj.get('reviewIntervalValue') and proj.get('reviewIntervalUnit'):
        result += f"Review Interval: Every {proj['reviewIntervalValue']} {proj['reviewIntervalUnit']}(s)\n"
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
    flagged_only: bool = False,
    include_dropped: bool = False,
    include_completed: bool = False,
    completed_only: bool = False,
    tag_filter: Optional[list[str]] = None,
    planned_after: Optional[str] = None,
    planned_before: Optional[str] = None,
    planned_on: Optional[str] = None,
    due_after: Optional[str] = None,
    due_before: Optional[str] = None,
    due_on: Optional[str] = None,
    defer_after: Optional[str] = None,
    defer_before: Optional[str] = None,
    defer_on: Optional[str] = None,
    completion_after: Optional[str] = None,
    completion_before: Optional[str] = None,
    completion_on: Optional[str] = None,
    dropped_after: Optional[str] = None,
    dropped_before: Optional[str] = None,
    dropped_on: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    created_on: Optional[str] = None,
    modified_on: Optional[str] = None,
    has_overdue_tasks: Optional[bool] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    modified_after: Optional[str] = None,
    modified_before: Optional[str] = None,
    min_task_count: Optional[int] = None,
    has_no_due_dates: Optional[bool] = None,
) -> str:
    """Retrieve projects with optional filtering.

    Parameters:
    - project_id: str -- filter to specific project
    - query: str -- search name/note/folder (case-insensitive)
    - flagged_only, on_hold_only, completed_only: bool
    - stalled_only: bool -- active projects with no available next actions
    - include_dropped, include_completed: bool -- include hidden states
    - include_full_notes: bool
    - include_task_health: bool -- adds remainingCount, availableCount, overdueCount, deferredCount, stalled, health
    - include_last_activity: bool -- adds lastActivityDate
    - has_overdue_tasks: bool -- implies include_task_health
    - tag_filter: list[str] -- projects with ALL specified tags
    - due_after, due_before, due_on: str -- ISO date filters for due date
    - defer_after, defer_before, defer_on: str -- ISO date filters for defer date
    - planned_after, planned_before, planned_on: str
    - completion_after, completion_before, completion_on: str
    - dropped_after, dropped_before, dropped_on: str
    - created_after, created_before, created_on: str
    - modified_after, modified_before, modified_on: str
    - min_task_count: int
    - has_no_due_dates: bool
    - sort_by: str -- "name", "due_date", "defer_date", "planned_date", "creation_date", "modification_date", "completion_date", "dropped_date"; sort_order: str -- "asc"/"desc"

    Returns: id, name, folderPath, status, projectType, sequential (deprecated), completedByChildren, flagged, creationDate, modificationDate, completionDate, droppedDate, dueDate, deferDate, plannedDate, tags, note, lastReviewDate, nextReviewDate, reviewIntervalValue, reviewIntervalUnit. Optional health/activity fields when requested.
    """
    # Expand _on params to _after + _before (single-day range)
    from datetime import date, timedelta

    def _expand_on(on_name, on_val, after_val, before_val):
        if on_val is None:
            return after_val, before_val, None
        if after_val is not None or before_val is not None:
            after_name = on_name.replace("_on", "_after")
            before_name = on_name.replace("_on", "_before")
            return None, None, f"Error: {on_name} is mutually exclusive with {after_name}/{before_name}."
        try:
            d = date.fromisoformat(on_val)
            return on_val, (d + timedelta(days=1)).isoformat(), None
        except ValueError:
            return None, None, f"Error: Invalid date format for {on_name}: '{on_val}'. Use ISO 8601 (e.g., '2026-03-23')."

    planned_after, planned_before, err = _expand_on("planned_on", planned_on, planned_after, planned_before)
    if err: return err
    due_after, due_before, err = _expand_on("due_on", due_on, due_after, due_before)
    if err: return err
    defer_after, defer_before, err = _expand_on("defer_on", defer_on, defer_after, defer_before)
    if err: return err
    completion_after, completion_before, err = _expand_on("completion_on", completion_on, completion_after, completion_before)
    if err: return err
    dropped_after, dropped_before, err = _expand_on("dropped_on", dropped_on, dropped_after, dropped_before)
    if err: return err
    created_after, created_before, err = _expand_on("created_on", created_on, created_after, created_before)
    if err: return err
    modified_after, modified_before, err = _expand_on("modified_on", modified_on, modified_after, modified_before)
    if err: return err

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
            flagged_only=flagged_only,
            include_dropped=include_dropped,
            include_completed=include_completed,
            completed_only=completed_only,
            tag_filter=tag_filter,
            planned_after=planned_after,
            planned_before=planned_before,
            has_overdue_tasks=has_overdue_tasks,
            sort_by=sort_by,
            sort_order=sort_order,
            modified_after=modified_after,
            modified_before=modified_before,
            created_after=created_after,
            created_before=created_before,
            due_after=due_after,
            due_before=due_before,
            defer_after=defer_after,
            defer_before=defer_before,
            completion_after=completion_after,
            completion_before=completion_before,
            dropped_after=dropped_after,
            dropped_before=dropped_before,
            min_task_count=min_task_count,
            has_no_due_dates=has_no_due_dates,
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
    elif completed_only:
        descriptor = "completed projects"
    elif has_overdue_tasks:
        descriptor = "projects with overdue tasks"
    elif flagged_only:
        descriptor = "flagged projects"
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


class ProjectUpdate(BaseModel):
    """Input model for updating a project."""
    id: str
    project_name: Optional[str] = None
    folder_path: Optional[str] = None
    note: Optional[str] = None
    sequential: Optional[bool] = None
    project_type: Optional[str] = None
    status: Optional[str] = None
    review_interval_weeks: Optional[int] = None
    review_interval_value: Optional[int] = None
    review_interval_unit: Optional[str] = None
    last_reviewed: Optional[str] = None
    next_review_date: Optional[str] = None
    completed_by_children: Optional[bool] = None
    due_date: Optional[str] = None
    defer_date: Optional[str] = None
    planned_date: Optional[str] = None
    flagged: Optional[bool] = None
    estimated_minutes: Optional[int] = None
    tags: Optional[list[str]] = None
    add_tags: Optional[list[str]] = None
    remove_tags: Optional[list[str]] = None
    recurrence: Optional[str] = None
    repetition_method: Optional[str] = None


def update_project(
    project_id: str,
    project_name: Optional[str] = None,
    folder_path: Optional[str] = None,
    note: Optional[str] = None,
    sequential: Optional[bool] = None,
    project_type: Optional[str] = None,
    status: Optional[str] = None,
    review_interval_weeks: Optional[int] = None,
    review_interval_value: Optional[int] = None,
    review_interval_unit: Optional[str] = None,
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
    """DEPRECATED: Use update_projects instead. Update a single project in OmniFocus.

    Delegates to update_projects with a single-item list.

    Args:
        project_id: The ID of the project to update
        project_name: New project name (optional)
        folder_path: Folder path to move project to (e.g., "Work : Projects")
        note: New note content (optional). WARNING: Removes rich text formatting.
        project_type: Change project type — "parallel", "sequential", or "single_actions" (optional)
        sequential: DEPRECATED — use project_type instead. (optional)
        status: Project status - "active", "on_hold", "done", or "dropped"
        review_interval_weeks: DEPRECATED — use review_interval_value + review_interval_unit instead. Review interval in weeks (0 to clear)
        review_interval_value: Review interval amount (e.g., 3 for "every 3 months"). Used with review_interval_unit.
        review_interval_unit: Review interval unit — "day", "week", "month", or "year" (default: "week")
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
    # Build project dict from non-None params
    params = locals()
    project_dict = {"id": params.pop("project_id")}
    for k, v in params.items():
        if v is not None:
            project_dict[k] = v
    return update_projects(projects=[project_dict])


@mcp.tool()
def update_projects(projects: list[ProjectUpdate]) -> str:
    """Update one or more projects. Each item has id (required) plus fields to change.

    Parameters (per item):
    - id: str (required)
    - project_name, note, folder_path: str -- note: replaces rich text
    - project_type: str; sequential: bool (deprecated)
    - status: str -- "active", "on_hold", "done", "dropped"
    - review_interval_value: int + review_interval_unit: str ("day"/"week"/"month"/"year"); review_interval_weeks: int (deprecated)
    - last_reviewed: str -- ISO or "now" (recalculates next_review_date from review interval)
    - next_review_date: str -- set AFTER last_reviewed to override the calculated date
    - completed_by_children: bool
    - due_date, defer_date, planned_date: str -- ISO or "" to clear
    - flagged: bool
    - estimated_minutes: int
    - tags: list[str] -- full replacement (conflicts with add_tags/remove_tags)
    - add_tags, remove_tags: list[str]
    - recurrence: str -- RRULE or "" to clear; repetition_method: str -- "fixed", "start_after_completion", "due_after_completion"
    """
    client = get_client()

    # Coerce dicts to ProjectUpdate
    try:
        projects = [ProjectUpdate(**p) if isinstance(p, dict) else p for p in projects]
    except Exception as e:
        return f"Error: Invalid project input: {e}"

    results = []
    for project in projects:
        try:
            # Build kwargs, excluding None values and the id field
            kwargs = project.model_dump(exclude_none=True, exclude={"id"})
            result = client.update_project(project_id=project.id, **kwargs)
            results.append({
                "id": project.id,
                "success": result["success"],
                "updated_fields": result.get("updated_fields", []),
                "error": result.get("error"),
            })
        except (ValueError, Exception) as e:
            results.append({
                "id": project.id,
                "success": False,
                "updated_fields": [],
                "error": str(e),
            })

    succeeded = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    # Single project: match old update_project format
    if len(projects) == 1:
        r = results[0]
        if r["success"]:
            fields = r["updated_fields"]
            if len(fields) == 0:
                return f"Successfully updated project {r['id']} (no changes detected)"
            elif len(fields) == 1:
                return f"Successfully updated project {r['id']}: {fields[0]}"
            else:
                return f"Successfully updated project {r['id']}: {len(fields)} fields ({', '.join(fields)})"
        else:
            return f"Error updating project {r['id']}: {r['error']}"

    # Multiple projects: summary
    lines = [f"Updated {len(succeeded)} of {len(projects)} projects:"]
    for r in succeeded:
        lines.append(f"  - {r['id']}: {', '.join(r['updated_fields'])}")
    for r in failed:
        lines.append(f"  - {r['id']}: FAILED — {r['error']}")
    return "\n".join(lines)




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
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    modified_after: Optional[str] = None,
    modified_before: Optional[str] = None,
    created_after: Optional[str] = None,
    created_before: Optional[str] = None,
    max_estimated_minutes: Optional[int] = None,
    has_estimate: Optional[bool] = None,
    recurring_only: Optional[bool] = None,
    tag_filter_mode: str = "and",
    planned_after: Optional[str] = None,
    planned_before: Optional[str] = None,
    planned_on: Optional[str] = None,
    due_after: Optional[str] = None,
    due_before: Optional[str] = None,
    due_on: Optional[str] = None,
    defer_after: Optional[str] = None,
    defer_before: Optional[str] = None,
    defer_on: Optional[str] = None,
    completion_after: Optional[str] = None,
    completion_before: Optional[str] = None,
    completion_on: Optional[str] = None,
    dropped_after: Optional[str] = None,
    dropped_before: Optional[str] = None,
    dropped_on: Optional[str] = None,
    created_on: Optional[str] = None,
    modified_on: Optional[str] = None,
) -> str:
    """Get tasks with optional filtering.

    Parameters:
    - task_id, parent_task_id, project_id: str
    - query: str -- search name/note
    - flagged_only, available_only, overdue, dropped_only, blocked_only, next_only, inbox_only: bool
    - include_completed: bool
    - include_full_notes: bool
    - tag_filter: list[str]; tag_filter_mode: str -- "and" (default), "or", "not"
    - due_after, due_before, due_on: str -- ISO date filters for due date
    - defer_after, defer_before, defer_on: str -- ISO date filters for defer date
    - planned_after, planned_before, planned_on: str
    - completion_after, completion_before, completion_on: str -- requires include_completed
    - dropped_after, dropped_before, dropped_on: str -- requires dropped_only or include_completed
    - modified_after, modified_before, modified_on, created_after, created_before, created_on: str
    - max_estimated_minutes: int -- quick wins filter
    - has_estimate: bool
    - recurring_only: bool
    - sort_by: str -- "name", "due_date", "defer_date", "planned_date", "creation_date", "modification_date", "completion_date", "dropped_date"; sort_order: str

    Returns: id, name, projectName, completed, dropped, blocked, available, next, flagged, dueDate, deferDate, plannedDate, estimatedMinutes, tags, note, parentTaskId, subtaskCount, sequential, isRecurring, recurrence, repetitionMethod, repeatSummary, nextDueDate, nextDeferDate, nextPlannedDate, catchUpAutomatically, creationDate, modificationDate, completionDate, droppedDate.

    Key fields:
    - available -- true when actionable (accounts for inherited status from containers)
    - repeatSummary -- human-readable recurrence; always use this for display, don't parse RRULE
    - repetitionMethod -- "fixed" (original schedule), "start_after_completion" (defer shifts), "due_after_completion" (due shifts)
    - catchUpAutomatically -- recurring only; true = one catch-up occurrence, false = each missed interval spawns its own
    - Date fields are effective (include inherited from project). Next-occurrence fields populated only for recurring tasks.
    - Tasks inherit tags from their parent project. A task showing a tag it wasn't explicitly assigned has inherited it -- this is expected, not a bug.
    """
    # Expand _on params to _after + _before (single-day range)
    from datetime import date, timedelta

    def _expand_on(on_name, on_val, after_val, before_val):
        """Expand a date _on param to _after + _before range. Returns (after, before, error)."""
        if on_val is None:
            return after_val, before_val, None
        if after_val is not None or before_val is not None:
            after_name = on_name.replace("_on", "_after")
            before_name = on_name.replace("_on", "_before")
            return None, None, f"Error: {on_name} is mutually exclusive with {after_name}/{before_name}."
        try:
            d = date.fromisoformat(on_val)
            return on_val, (d + timedelta(days=1)).isoformat(), None
        except ValueError:
            return None, None, f"Error: Invalid date format for {on_name}: '{on_val}'. Use ISO 8601 (e.g., '2026-03-23')."

    planned_after, planned_before, err = _expand_on("planned_on", planned_on, planned_after, planned_before)
    if err: return err
    due_after, due_before, err = _expand_on("due_on", due_on, due_after, due_before)
    if err: return err
    defer_after, defer_before, err = _expand_on("defer_on", defer_on, defer_after, defer_before)
    if err: return err
    completion_after, completion_before, err = _expand_on("completion_on", completion_on, completion_after, completion_before)
    if err: return err
    dropped_after, dropped_before, err = _expand_on("dropped_on", dropped_on, dropped_after, dropped_before)
    if err: return err
    created_after, created_before, err = _expand_on("created_on", created_on, created_after, created_before)
    if err: return err
    modified_after, modified_before, err = _expand_on("modified_on", modified_on, modified_after, modified_before)
    if err: return err

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
            tag_filter_mode=tag_filter_mode,
            query=query,
            inbox_only=inbox_only,
            sort_by=sort_by,
            sort_order=sort_order,
            modified_after=modified_after,
            modified_before=modified_before,
            created_after=created_after,
            created_before=created_before,
            max_estimated_minutes=max_estimated_minutes,
            has_estimate=has_estimate,
            recurring_only=recurring_only,
            planned_after=planned_after,
            planned_before=planned_before,
            due_after=due_after,
            due_before=due_before,
            defer_after=defer_after,
            defer_before=defer_before,
            completion_after=completion_after,
            completion_before=completion_before,
            dropped_after=dropped_after,
            dropped_before=dropped_before,
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
    review_interval_value: Optional[int] = None
    review_interval_unit: Optional[str] = None
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
    """Create one or more tasks.

    Parameters (per item):
    - task_name: str (required)
    - project_id: str -- mutually exclusive with parent_task_id
    - parent_task_id: str -- creates subtask
    - note: str (plain text only)
    - due_date, defer_date, planned_date: str -- ISO 8601
    - flagged: bool
    - tags: list[str] -- must already exist
    - estimated_minutes: int
    - sequential: bool -- subtasks completed in order
    - completed_by_children: bool
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
            if task.estimated_minutes:
                result += f"\nEstimated time: {task.estimated_minutes} minutes"
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
# Unified Batch Create Projects (v0.12.0)
# ============================================================================


@mcp.tool()
def create_projects(projects: list[ProjectCreate]) -> str:
    """Create one or more projects.

    Parameters (per item):
    - name: str (required)
    - note, folder_path: str
    - project_type: str -- "parallel" (default), "sequential", "single_actions"
    - sequential: bool (deprecated, use project_type)
    - review_interval_value: int + review_interval_unit: str ("day"/"week"/"month"/"year"); review_interval_weeks: int (deprecated)
    - completed_by_children: bool
    - due_date, defer_date, planned_date: str -- ISO 8601
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
    """Update one or more tasks. Each item has id (required) plus fields to change.

    Parameters (per item):
    - id: str (required)
    - task_name, project_id, parent_task_id, note: str
    - due_date, defer_date, planned_date: str -- ISO or "" to clear
    - flagged, completed: bool -- completed=True on recurring task creates next occurrence
    - status: str -- "dropped" (prefer completed: bool for completion)
    - tags: list[str] -- full replacement (conflicts with add_tags/remove_tags)
    - add_tags, remove_tags: list[str]
    - estimated_minutes: int
    - recurrence: str -- RRULE or "" to clear; repetition_method: str
    - sequential: bool; completed_by_children: bool
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
    """Retrieve all tags.

    Returns: id, name, status ("active"/"on hold"/"dropped"), parentTagId (empty if top-level; create/update accept parent by NAME not ID), childrenAreMutuallyExclusive (assigning one child silently removes siblings).
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


# ============================================================================
# Pydantic Models for Tag CRUD (v0.12.1)
# ============================================================================

class TagCreate(BaseModel):
    """Input model for creating a tag."""
    name: str
    parent_tag: Optional[str] = None
    children_are_mutually_exclusive: bool = False


class TagUpdate(BaseModel):
    """Input model for updating a tag."""
    id: str
    name: Optional[str] = None
    status: Optional[str] = None
    children_are_mutually_exclusive: Optional[bool] = None
    parent_tag: Optional[str] = None


# ============================================================================
# Unified Batch Create/Update Tags (v0.12.1)
# ============================================================================

def create_tag(
    name: str,
    parent_tag: Optional[str] = None,
    children_are_mutually_exclusive: bool = False
) -> str:
    """DEPRECATED: Use create_tags instead. Creates a single tag (delegates to create_tags)."""
    return create_tags(tags=[{
        "name": name,
        "parent_tag": parent_tag,
        "children_are_mutually_exclusive": children_are_mutually_exclusive,
    }])


@mcp.tool()
def create_tags(tags: list[TagCreate]) -> str:
    """Create one or more tags.

    Parameters (per item):
    - name: str (required)
    - parent_tag: str -- parent by name
    - children_are_mutually_exclusive: bool
    """
    client = get_client()
    results = []

    try:
        tags = [TagCreate(**t) if isinstance(t, dict) else t for t in tags]
    except Exception as e:
        return f"Error: Invalid tag input: {e}"

    for tag in tags:
        try:
            tag_id = client.create_tag(**tag.model_dump())
            results.append({"name": tag.name, "tag_id": tag_id, "success": True})
        except (ValueError, Exception) as e:
            results.append({"name": tag.name, "success": False, "error": str(e)})

    succeeded = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    # Single tag: detailed format
    if len(tags) == 1:
        r = results[0]
        if r["success"]:
            tag = tags[0]
            result = f"Successfully created tag '{tag.name}'\nTag ID: {r['tag_id']}"
            if tag.parent_tag:
                result += f"\nParent: {tag.parent_tag}"
            return result
        else:
            return f"Error: {r['error']}"

    # Multiple tags: summary
    lines = [f"Created {len(succeeded)} of {len(tags)} tags:"]
    for r in succeeded:
        lines.append(f"  - {r['name']}: {r['tag_id']}")
    for r in failed:
        lines.append(f"  - {r['name']}: FAILED — {r['error']}")
    return "\n".join(lines)


def update_tag(
    tag_id: str,
    name: Optional[str] = None,
    status: Optional[str] = None,
    children_are_mutually_exclusive: Optional[bool] = None,
    parent_tag: Optional[str] = None
) -> str:
    """DEPRECATED: Use update_tags instead. Updates a single tag (delegates to update_tags)."""
    params = locals()
    tag_dict = {"id": params.pop("tag_id")}
    for k, v in params.items():
        if v is not None:
            tag_dict[k] = v
    return update_tags(tags=[tag_dict])


@mcp.tool()
def update_tags(tags: list[TagUpdate]) -> str:
    """Update one or more tags. Each item has id (required) plus fields to change.

    Parameters (per item):
    - id: str (required)
    - name, status: str -- status: "active", "on_hold", "dropped"
    - children_are_mutually_exclusive: bool
    - parent_tag: str -- move to parent by name, "" for top level
    """
    client = get_client()
    results = []

    try:
        tags = [TagUpdate(**t) if isinstance(t, dict) else t for t in tags]
    except Exception as e:
        return f"Error: Invalid tag update input: {e}"

    for tag in tags:
        try:
            params = tag.model_dump(exclude_none=True, exclude={"id"})
            result = client.update_tag(tag_id=tag.id, **params)
            results.append({
                "id": tag.id,
                "success": result.get("success", True),
                "updated_fields": result.get("updated_fields", []),
                "error": result.get("error"),
            })
        except (ValueError, Exception) as e:
            results.append({"id": tag.id, "success": False, "updated_fields": [], "error": str(e)})

    succeeded = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    # Single tag: detailed format
    if len(tags) == 1:
        r = results[0]
        if r["success"]:
            fields = ", ".join(r["updated_fields"])
            return f"Successfully updated tag {r['id']}\nUpdated fields: {fields}"
        else:
            return f"Error updating tag {r['id']}: {r['error']}"

    # Multiple tags: summary
    lines = [f"Updated {len(succeeded)} of {len(tags)} tags:"]
    for r in succeeded:
        fields = ", ".join(r["updated_fields"])
        lines.append(f"  - {r['id']}: {fields}")
    for r in failed:
        lines.append(f"  - {r['id']}: FAILED — {r['error']}")
    return "\n".join(lines)


@mcp.tool()
def delete_tags(tag_ids: Union[str, list[str]]) -> str:
    """Delete tags. Tasks lose tag association but are not deleted.

    - tag_ids: str | list[str] (required)
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
    """Permanently delete tasks. Cannot be undone.

    - task_ids: str | list[str] (required)
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
    """Permanently delete projects and all their tasks. Cannot be undone.

    - project_ids: str | list[str] (required)
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
    """Get all folders with hierarchy.

    Returns: id, name, path (e.g. "Work > Clients"), status ("active"/"dropped").
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


# ============================================================================
# Pydantic Models for Folder CRUD (v0.13.0)
# ============================================================================

class FolderCreate(BaseModel):
    """Input model for creating a folder."""
    name: str
    parent_path: Optional[str] = None


class FolderUpdate(BaseModel):
    """Input model for updating a folder."""
    id: str
    name: Optional[str] = None
    status: Optional[str] = None  # "active" or "dropped"


# ============================================================================
# Unified Batch Create/Update Folders (v0.13.0)
# ============================================================================

def create_folder(name: str, parent_path: Optional[str] = None) -> str:
    """DEPRECATED: Use create_folders instead. Creates a single folder (delegates to create_folders)."""
    return create_folders(folders=[{"name": name, "parent_path": parent_path}])


@mcp.tool()
def create_folders(folders: list[FolderCreate]) -> str:
    """Create one or more folders.

    Parameters (per item):
    - name: str (required)
    - parent_path: str -- e.g. "Work > Clients"
    """
    client = get_client()
    results = []

    try:
        folders = [FolderCreate(**f) if isinstance(f, dict) else f for f in folders]
    except Exception as e:
        return f"Error: Invalid folder input: {e}"

    for folder in folders:
        try:
            folder_id = client.create_folder(**folder.model_dump())
            results.append({"name": folder.name, "folder_id": folder_id, "success": True})
        except (ValueError, Exception) as e:
            results.append({"name": folder.name, "success": False, "error": str(e)})

    succeeded = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    # Single folder: detailed format
    if len(folders) == 1:
        r = results[0]
        if r["success"]:
            folder = folders[0]
            if folder.parent_path:
                return f"Successfully created folder '{folder.name}' in '{folder.parent_path}'\nFolder ID: {r['folder_id']}"
            else:
                return f"Successfully created folder '{folder.name}' at root level\nFolder ID: {r['folder_id']}"
        else:
            return f"Error: {r['error']}"

    # Multiple folders: summary
    lines = [f"Created {len(succeeded)} of {len(folders)} folders:"]
    for r in succeeded:
        lines.append(f"  - {r['name']}: {r['folder_id']}")
    for r in failed:
        lines.append(f"  - {r['name']}: FAILED — {r['error']}")
    return "\n".join(lines)


def update_folder(
    folder_id: str,
    name: Optional[str] = None,
    status: Optional[str] = None,
) -> str:
    """DEPRECATED: Use update_folders instead. Updates a single folder (delegates to update_folders)."""
    params = locals()
    folder_dict = {"id": params.pop("folder_id")}
    for k, v in params.items():
        if v is not None:
            folder_dict[k] = v
    return update_folders(folders=[folder_dict])


@mcp.tool()
def update_folders(folders: list[FolderUpdate]) -> str:
    """Update one or more folders. Each item has id (required) plus fields to change.

    Parameters (per item):
    - id: str (required)
    - name: str
    - status: str -- "active" or "dropped"
    """
    client = get_client()
    results = []

    try:
        folders = [FolderUpdate(**f) if isinstance(f, dict) else f for f in folders]
    except Exception as e:
        return f"Error: Invalid folder update input: {e}"

    for folder in folders:
        try:
            params = folder.model_dump(exclude_none=True, exclude={"id"})
            result = client.update_folder(folder_id=folder.id, **params)
            results.append({
                "id": folder.id,
                "success": result.get("success", True),
                "updated_fields": result.get("updated_fields", []),
                "error": result.get("error"),
            })
        except (ValueError, Exception) as e:
            results.append({"id": folder.id, "success": False, "updated_fields": [], "error": str(e)})

    succeeded = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    # Single folder: detailed format
    if len(folders) == 1:
        r = results[0]
        if r["success"]:
            fields = ", ".join(r["updated_fields"])
            return f"Successfully updated folder {r['id']}\nUpdated fields: {fields}"
        else:
            return f"Error updating folder {r['id']}: {r['error']}"

    # Multiple folders: summary
    lines = [f"Updated {len(succeeded)} of {len(folders)} folders:"]
    for r in succeeded:
        fields = ", ".join(r["updated_fields"])
        lines.append(f"  - {r['id']}: {fields}")
    for r in failed:
        lines.append(f"  - {r['id']}: FAILED — {r['error']}")
    return "\n".join(lines)


# ============================================================================
# Task Hierarchy Tools
# ============================================================================

@mcp.tool()
def reorder_task(task_id: str, before_task_id: Optional[str] = None, after_task_id: Optional[str] = None) -> str:
    """Move a task before or after another task within the same project/level.

    - task_id: str (required)
    - before_task_id: str -- place before this task
    - after_task_id: str -- place after this task

    Exactly one of before/after required. In sequential projects, order = dependencies.
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
    """Move a project before or after another project within the same folder.

    - project_id: str (required)
    - before_project_id: str
    - after_project_id: str

    Exactly one of before/after required.
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
    """Get all perspectives.

    Returns: name, type (built-in/custom), id
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
    """Switch front window to a perspective.

    - perspective_name: str (required)
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
    """Focus on projects/folders, or clear focus. Does not support tasks or tags.

    - item_ids: str | list[str] -- omit or empty to clear
    - item_types: str | list[str] -- "project" or "folder"
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
    """Get currently focused items.
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
