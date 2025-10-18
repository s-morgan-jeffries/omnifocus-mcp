#!/usr/bin/env python3
"""FastMCP Server for OmniFocus integration."""
import json
import os
from typing import Optional, Union

from fastmcp import FastMCP

from .omnifocus_client import OmniFocusClient

# Create FastMCP server
mcp = FastMCP("omnifocus-mcp")

# Configuration
NOTE_TRUNCATION_LENGTH = 100  # Maximum note length in get_projects/get_tasks responses

# Initialize OmniFocus client (lazy)
_client: Optional[OmniFocusClient] = None


def get_client() -> OmniFocusClient:
    """Get or create the OmniFocus client."""
    global _client
    if _client is None:
        # Disable safety checks if in pytest environment (for integration tests with mocked AppleScript)
        _in_pytest = os.environ.get('PYTEST_CURRENT_TEST') is not None
        _client = OmniFocusClient(enable_safety_checks=not _in_pytest)
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


def _format_task(task: dict) -> str:
    """Format a task dictionary as human-readable text.

    Args:
        task: Task dictionary from omnifocus_client

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
    if task.get('dueDate'):
        result += f"Due: {task['dueDate']}\n"
    if task.get('deferDate'):
        result += f"Defer: {task['deferDate']}\n"
    if task.get('estimatedMinutes'):
        result += f"Estimated: {task['estimatedMinutes']} minutes\n"
    if task.get('tags'):
        result += f"Tags: {task['tags']}\n"
    if task.get('note'):
        result += f"Note: {_truncate_note(task['note'])}\n"

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
    if 'position' in task:
        result += f"Position: {task['position']}\n"

    return result


def _format_project(proj: dict) -> str:
    """Format a project dictionary as human-readable text.

    Args:
        proj: Project dictionary from omnifocus_client

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
    if proj.get('note'):
        result += f"Note: {_truncate_note(proj['note'])}\n"

    return result


# ============================================================================
# Project Tools
# ============================================================================

@mcp.tool()
def get_projects(
    project_id: Optional[str] = None,  # NEW (Phase 3.2)
    include_full_notes: bool = False,  # NEW (Phase 3.2)
    on_hold_only: bool = False,
    query: Optional[str] = None
) -> str:
    """Retrieve ALL active projects with full details and hierarchy, optionally filtered by search query.

    NEW (Phase 3.2): Added project_id and include_full_notes parameters to consolidate
    get_project() and get_note() functionality.

    Args:
        project_id: NEW - Filter to specific project by ID (consolidates get_project())
        include_full_notes: NEW - Return full note content (consolidates get_note())
        on_hold_only: If True, only return projects with "on hold" status
        query: Optional search term to filter by name, note, or folder path (case-insensitive)

    Returns:
        Formatted text with project list (one per line with ID, name, folder, status, and note preview)
    """
    client = get_client()
    projects = client.get_projects(
        project_id=project_id,
        include_full_notes=include_full_notes,
        on_hold_only=on_hold_only,
        query=query
    )

    if not projects:
        if query:
            return f"No projects found matching '{query}'"
        return "Found 0 active projects"

    # Format projects for display
    if query:
        result = f"Found {len(projects)} projects matching '{query}':\n\n"
    else:
        result = f"Found {len(projects)} active projects:\n\n"
    for proj in projects:
        result += _format_project(proj)
        result += "\n"

    return result


@mcp.tool()
def create_project(
    name: str,
    note: Optional[str] = None,
    folder_path: Optional[str] = None,
    sequential: bool = False
) -> str:
    """Create a new project in OmniFocus.

    Args:
        name: The name of the project
        note: Optional note/description for the project (plain text only - rich text formatting is not supported via automation APIs)
        folder_path: Optional folder path (e.g., "Work > Clients") - folder must exist in OmniFocus
        sequential: If True, tasks must be completed in order; if False, tasks can be done in parallel (default: False)

    Returns:
        Success message with project ID and configuration details
    """
    client = get_client()
    project_id = client.create_project(
        name=name,
        note=note,
        folder_path=folder_path,
        sequential=sequential
    )

    result = f"Successfully created project '{name}'"
    result += f"\nProject ID: {project_id}"
    if folder_path:
        result += f"\nFolder: {folder_path}"
    if sequential:
        result += "\nType: Sequential (tasks completed in order)"
    else:
        result += "\nType: Parallel (tasks can be done in any order)"
    if note:
        result += f"\nNote: {_truncate_note(note)}"

    return result


@mcp.tool()
def update_project(
    project_id: str,
    project_name: Optional[str] = None,
    folder_path: Optional[str] = None,
    note: Optional[str] = None,
    sequential: Optional[str] = None,
    status: Optional[str] = None,
    review_interval_weeks: Optional[int] = None,
    last_reviewed: Optional[str] = None
) -> str:
    """Update an existing project in OmniFocus (NEW API - Phase 2).

    NEW API changes:
    - Renamed 'name' to 'project_name' for consistency
    - Added status parameter (active, on_hold, done, dropped)
    - Added review_interval_weeks parameter
    - Added last_reviewed parameter
    - Added folder_path parameter
    - Returns structured response with updated fields
    - Consolidates: set_project_status(), drop_project(), set_review_interval(), mark_project_reviewed()

    Args:
        project_id: The ID of the project to update
        project_name: New project name (optional)
        folder_path: Folder path to move project to (e.g., "Work : Projects")
        note: New note content (optional). WARNING: Removes rich text formatting.
        sequential: Sequential setting (optional) - "true" or "false"
        status: Project status - "active", "on_hold", "done", or "dropped"
        review_interval_weeks: Review interval in weeks (0 to clear)
        last_reviewed: Last reviewed date in ISO format or "now"

    Returns:
        Success message with project ID and updated fields, or error message
    """
    # Convert sequential parameter to boolean for client (handle both string and bool)
    sequential_bool: Optional[bool] = None
    if sequential is not None:
        if isinstance(sequential, bool):
            # Direct boolean (from tests or Python calls)
            sequential_bool = sequential
        elif isinstance(sequential, str):
            # String from MCP (Claude passes strings)
            if sequential.lower() == "true":
                sequential_bool = True
            elif sequential.lower() == "false":
                sequential_bool = False
            else:
                return f"Error: Invalid sequential value '{sequential}'. Must be 'true' or 'false'."

    client = get_client()
    result = client.update_project(
        project_id=project_id,
        project_name=project_name,
        folder_path=folder_path,
        note=note,
        sequential=sequential_bool,
        status=status,
        review_interval_weeks=review_interval_weeks,
        last_reviewed=last_reviewed
    )

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
    sequential: Optional[str] = None,
    status: Optional[str] = None,
    review_interval_weeks: Optional[int] = None,
    last_reviewed: Optional[str] = None
) -> str:
    """Update multiple projects with the same properties (NEW API - Phase 2, Batch Function).

    This is the BATCH version of update_project(). It updates multiple projects
    with the same values. This is more efficient than calling update_project()
    multiple times.

    IMPORTANT: This function does NOT accept project_name or note parameters
    because those require unique values for each project.

    Args:
        project_ids: Single project ID (str) or list of project IDs to update
        folder_path: Folder path to move projects to (e.g., "Work > Projects")
        sequential: Sequential setting as string ("true" or "false")
        status: Project status - one of: "active", "on_hold", "done", "dropped"
        review_interval_weeks: Review interval in weeks
        last_reviewed: Last review date ("now" or ISO format like "2025-01-15")

    Returns:
        Success message with updated and failed counts, or error message

    Example:
        # Drop multiple projects at once
        update_projects(
            project_ids=["proj-001", "proj-002", "proj-003"],
            status="dropped"
        )
    """
    # Convert sequential parameter to boolean for client (handle both string and bool)
    sequential_bool: Optional[bool] = None
    if sequential is not None:
        if isinstance(sequential, bool):
            # Direct boolean (from tests or Python calls)
            sequential_bool = sequential
        elif isinstance(sequential, str):
            # String from MCP (Claude passes strings)
            if sequential.lower() == "true":
                sequential_bool = True
            elif sequential.lower() == "false":
                sequential_bool = False
            else:
                return f"Error: Invalid sequential value '{sequential}'. Must be 'true' or 'false'."

    try:
        client = get_client()
        result = client.update_projects(
            project_ids=project_ids,
            folder_path=folder_path,
            sequential=sequential_bool,
            status=status,
            review_interval_weeks=review_interval_weeks,
            last_reviewed=last_reviewed
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
    task_id: Optional[str] = None,  # NEW (Phase 3.1)
    parent_task_id: Optional[str] = None,  # NEW (Phase 3.1)
    include_full_notes: bool = False,  # NEW (Phase 3.1)
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
    """Get tasks from OmniFocus with optional filtering (Enhanced - Phase 3.1).

    NEW (Phase 3.1): Added task_id, parent_task_id, include_full_notes parameters
    to consolidate get_task(), get_subtasks(), and get_note() functionality.

    Args:
        task_id: NEW - Filter to specific task by ID (consolidates get_task())
        parent_task_id: NEW - Filter to subtasks of parent (consolidates get_subtasks())
        include_full_notes: NEW - Return full note content (consolidates get_note())
        project_id: Optional project ID to filter tasks (ignored if inbox_only=True)
        flagged_only: If True, only return flagged tasks
        include_completed: If True, include completed tasks (default: False)
        available_only: If True, only return available tasks (not blocked or deferred)
        overdue: If True, only return overdue tasks
        dropped_only: If True, only return dropped tasks
        blocked_only: If True, only return blocked tasks
        next_only: If True, only return next tasks
        tag_filter: List of tag names to filter by (task must have all tags)
        query: Optional search term to filter by name or note (case-insensitive)
        inbox_only: If True, only return inbox tasks

    Returns:
        Formatted text with task list including ID, name, project, due date, tags, and completion status
    """
    client = get_client()
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
        result += _format_task(task)
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
    flagged: bool = False,
    tags: Optional[str] = None,
    estimated_minutes: Optional[int] = None
) -> str:
    """Create a new task in OmniFocus (NEW API - consolidates add_task and create_inbox_task).

    This is the redesigned create function that unifies task creation across all contexts:
    - If project_id is provided: Create task in that project
    - If parent_task_id is provided: Create task as subtask under that parent
    - If neither provided (or project_id=None): Create task in inbox

    Args:
        task_name: The name/title of the task (required)
        project_id: Optional project ID. If None, creates in inbox (unless parent_task_id is set)
        parent_task_id: Optional parent task ID to create as subtask. Cannot be used with project_id.
        note: Optional note/description for the task (plain text only)
        due_date: Due date in ISO 8601 format (e.g., '2025-10-15' or '2025-10-15T17:00:00')
        defer_date: Defer date in ISO 8601 format (when task becomes available)
        flagged: Whether to flag the task (default: False)
        tags: Optional JSON array string of tag names (e.g., '["Computer", "Work"]'). Tags must already exist.
        estimated_minutes: Estimated time in minutes to complete the task

    Returns:
        Success message with task ID and location (project/inbox/parent)

    Raises:
        ValueError: If both project_id and parent_task_id are specified
    """
    client = get_client()

    # Parse tags parameter - convert JSON string to list
    tags_list = None
    if tags:
        try:
            tags_list = json.loads(tags)
            if not isinstance(tags_list, list):
                return f"Error: tags must be a JSON array string, e.g., '[\"Computer\"]'"
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON for tags parameter: {e}"

    # Validation errors should raise immediately (before calling client)
    # This allows MCP to report them properly
    task_id = client.create_task(
        task_name=task_name,
        project_id=project_id,
        parent_task_id=parent_task_id,
        note=note,
        due_date=due_date,
        defer_date=defer_date,
        flagged=flagged,
        tags=tags_list,
        estimated_minutes=estimated_minutes
    )

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
    if tags_list:
        result += f"\nTags: {', '.join(tags_list)}"
    if estimated_minutes:
        result += f"\nEstimated time: {estimated_minutes} minutes"

    return result


@mcp.tool()
def add_task(
    project_id: str,
    task_name: str,
    note: Optional[str] = None,
    due_date: Optional[str] = None,
    defer_date: Optional[str] = None,
    flagged: bool = False,
    tags: Optional[str] = None
) -> str:
    """Add a new task to a specific OmniFocus project with full properties support.

    Args:
        project_id: The ID of the project to add the task to
        task_name: The name/title of the task
        note: Optional note/description for the task (plain text only - rich text formatting is not supported via automation APIs)
        due_date: Due date in ISO 8601 format (e.g., '2025-10-15' or '2025-10-15T17:00:00')
        defer_date: Defer date in ISO 8601 format (when task becomes available)
        flagged: Whether to flag the task (default: False)
        tags: Optional JSON array string of tag names (e.g., '["Computer", "Work"]'). Tags must already exist.

    Returns:
        Success message with task name, project, and all configured properties
    """
    client = get_client()

    # Parse tags parameter - convert JSON string to list
    tags_list = []
    if tags:
        try:
            tags_list = json.loads(tags)
            if not isinstance(tags_list, list):
                return f"Error: tags must be a JSON array string, e.g., '[\"Computer\"]'"
        except json.JSONDecodeError as e:
            return f"Error: Invalid JSON for tags parameter: {e}"

    success = client.add_task(
        project_id=project_id,
        task_name=task_name,
        note=note or "",
        due_date=due_date,
        defer_date=defer_date,
        flagged=flagged,
        tags=tags_list
    )

    if success:
        result = f"Successfully added task '{task_name}' to project {project_id}"
        if due_date:
            result += f"\nDue date: {due_date}"
        if defer_date:
            result += f"\nDefer date: {defer_date}"
        if flagged:
            result += "\nFlagged: Yes"
        if tags_list:
            result += f"\nTags: {', '.join(tags_list)}"
        return result
    else:
        return f"Error: Failed to add task '{task_name}'"


@mcp.tool()
def update_task(
    task_id: str,
    task_name: Optional[str] = None,
    project_id: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    note: Optional[str] = None,
    due_date: Optional[str] = None,
    defer_date: Optional[str] = None,
    flagged: Optional[bool] = None,
    tags: Optional[list[str]] = None,
    add_tags: Optional[list[str]] = None,
    remove_tags: Optional[list[str]] = None,
    estimated_minutes: Optional[int] = None,
    completed: Optional[bool] = None,
    status: Optional[str] = None,
    # Legacy parameters (backward compatibility)
    name: Optional[str] = None
) -> str:
    """Update an existing task in OmniFocus (NEW API - Redesign).

    This comprehensive update function consolidates multiple specialized functions:
    - complete_task() -> update_task(task_id, completed=True)
    - drop_task() -> update_task(task_id, status="dropped")
    - move_task() -> update_task(task_id, project_id=X)
    - set_parent_task() -> update_task(task_id, parent_task_id=X)
    - set_estimated_minutes() -> update_task(task_id, estimated_minutes=X)
    - add_tag_to_task() -> update_task(task_id, add_tags=[...])

    Args:
        task_id: The ID of the task to update
        task_name: New task name (optional)
        project_id: Move task to this project (optional, conflicts with parent_task_id)
        parent_task_id: Make task a subtask of this parent (optional, conflicts with project_id)
        note: New note content (optional). WARNING: Removes rich text formatting
        due_date: New due date in ISO 8601 format, or empty string to clear (optional)
        defer_date: New defer date in ISO 8601 format, or empty string to clear (optional)
        flagged: Flag/unflag the task (optional)
        tags: Full replacement - set exact tag list (optional, conflicts with add_tags/remove_tags)
        add_tags: Add these tags incrementally (optional, conflicts with tags)
        remove_tags: Remove these tags (optional, conflicts with tags)
        estimated_minutes: Estimated time in minutes (optional)
        completed: Mark task complete/incomplete (optional)
        status: Task status - "active" or "dropped" (optional)
        name: DEPRECATED - Use task_name instead (optional, for backward compatibility)

    Returns:
        Success message with updated fields, or error message

    Examples:
        update_task("task-123", completed=True)  # Mark complete
        update_task("task-123", status="dropped")  # Drop task
        update_task("task-123", project_id="proj-456")  # Move to project
        update_task("task-123", add_tags=["urgent"])  # Add tag
        update_task("task-123", task_name="New Name", flagged=True, due_date="2025-12-31")
    """
    # Support legacy 'name' parameter for backward compatibility
    if name is not None and task_name is None:
        task_name = name

    client = get_client()
    result = client.update_task(
        task_id=task_id,
        task_name=task_name,
        project_id=project_id,
        parent_task_id=parent_task_id,
        note=note,
        due_date=due_date,
        defer_date=defer_date,
        flagged=flagged,
        tags=tags,
        add_tags=add_tags,
        remove_tags=remove_tags,
        estimated_minutes=estimated_minutes,
        completed=completed,
        status=status,
        name=name  # Pass to client for its own backward compat handling
    )

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
    estimated_minutes: Optional[int] = None
) -> str:
    """Update multiple tasks with the same field values (batch operation - NEW API).

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
        project_id: Move all tasks to this project (optional, conflicts with parent_task_id)
        parent_task_id: Make all tasks subtasks of this parent (optional, conflicts with project_id)
        tags: Full replacement - set exact tag list for all tasks (optional, conflicts with add_tags)
        add_tags: Add these tags to all tasks (optional, conflicts with tags)
        remove_tags: Remove these tags from all tasks (optional)
        due_date: Set due date for all tasks in ISO 8601 format, or empty string to clear (optional)
        defer_date: Set defer date for all tasks in ISO 8601 format, or empty string to clear (optional)
        estimated_minutes: Set estimated time in minutes for all tasks (optional)

    Returns:
        Summary message with counts of successful/failed updates

    Examples:
        update_tasks(["task-001", "task-002"], flagged=True)  # Flag multiple tasks
        update_tasks("task-123", completed=True)  # Complete single task (Union type)
        update_tasks(["task-001", "task-002", "task-003"], status="dropped")  # Drop multiple
    """
    client = get_client()
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
        estimated_minutes=estimated_minutes
    )

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
    """Retrieve all available tags from OmniFocus with their names.

    Returns:
        Formatted list of all tag names (one per line)
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
        result += "\n"

    return result




@mcp.tool()
def delete_tasks(task_ids: Union[str, list[str]]) -> str:
    """Delete multiple tasks from OmniFocus in a single operation (NEW API - Enhanced).

    WARNING: This permanently deletes the tasks and cannot be undone.

    NEW API (Redesign): Now accepts Union[str, list[str]] and handles dict return from client.

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

        # Handle dict return from client (NEW API)
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
    except Exception as e:
        return f"Error deleting tasks: {str(e)}"


@mcp.tool()
def delete_projects(project_ids: Union[str, list[str]]) -> str:
    """Delete one or more projects from OmniFocus (NEW API - Enhanced with Union type).

    WARNING: This permanently deletes the projects and all their tasks. Cannot be undone.

    NEW API changes:
    - Accepts Union[str, list[str]] for project_ids (single or multiple)
    - Returns detailed summary with success/failure counts

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
    except Exception as e:
        return f"Error deleting projects: {str(e)}"


# ============================================================================
# Task Movement Tools
# ============================================================================





@mcp.tool()
def get_folders() -> str:
    """Get all folders from OmniFocus with their hierarchy.

    Returns:
        Formatted hierarchical list of all folders with indentation showing nesting
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


# ============================================================================
# Task Hierarchy Tools
# ============================================================================

@mcp.tool()
def reorder_task(task_id: str, before_task_id: Optional[str] = None, after_task_id: Optional[str] = None) -> str:
    """Move a task before or after another task to change its position.

    Use this to reorder tasks within a project or within a parent task's subtasks.
    This is essential for sequential projects where task order matters.

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
def get_perspectives() -> str:
    """Get all perspective names from OmniFocus.

    Returns:
        Formatted list of all perspective names (one per line)
    """
    client = get_client()
    perspectives = client.get_perspectives()

    if not perspectives:
        return "Found 0 perspectives"

    result = f"Found {len(perspectives)} perspectives:\n\n"
    for perspective in perspectives:
        result += f"- {perspective}\n"

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


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    mcp.run()
