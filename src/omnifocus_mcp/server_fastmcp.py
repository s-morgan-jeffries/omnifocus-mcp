#!/usr/bin/env python3
"""FastMCP Server for OmniFocus integration."""
import os
from typing import Optional

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
    if proj.get('note'):
        result += f"Note: {_truncate_note(proj['note'])}\n"

    return result


# ============================================================================
# Project Tools
# ============================================================================

@mcp.tool()
def get_projects(
    on_hold_only: bool = False,
    query: Optional[str] = None
) -> str:
    """Retrieve ALL active projects with full details and hierarchy, optionally filtered by search query.

    Args:
        on_hold_only: If True, only return projects with "on hold" status
        query: Optional search term to filter by name, note, or folder path (case-insensitive)

    Returns:
        Formatted text with project list (one per line with ID, name, folder, status, and note preview)
    """
    client = get_client()
    projects = client.get_projects(on_hold_only=on_hold_only, query=query)

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
    name: Optional[str] = None,
    note: Optional[str] = None,
    sequential: Optional[str] = None
) -> str:
    """Update an existing project in OmniFocus.

    Args:
        project_id: The ID of the project to update
        name: New project name (optional)
        note: New note content (optional). WARNING: If provided, this will remove any rich text formatting (bold, italics, links, etc.) and replace it with plain text. OmniFocus automation APIs only support plain text notes. If not provided, the existing note will be preserved unchanged.
        sequential: New sequential setting (optional) - "true" for sequential (tasks completed in order), "false" for parallel, or omit to leave unchanged

    Returns:
        Success message listing all updated fields
    """
    # Convert string sequential parameter to boolean for client
    sequential_bool: Optional[bool] = None
    if sequential is not None:
        if sequential.lower() == "true":
            sequential_bool = True
        elif sequential.lower() == "false":
            sequential_bool = False
        else:
            return f"Error: Invalid sequential value '{sequential}'. Must be 'true' or 'false'."

    client = get_client()
    success = client.update_project(
        project_id=project_id,
        name=name,
        note=note,
        sequential=sequential_bool
    )

    if success:
        return f"Successfully updated project {project_id}"
    else:
        return f"Error: Failed to update project {project_id}"


@mcp.tool()
def set_project_status(project_id: str, status: str) -> str:
    """Change a project's status to active, on hold, or done.

    Args:
        project_id: The ID of the project
        status: The status to set - one of: "active", "on_hold", "done"
               Note: "dropped" status is not supported by AppleScript

    Returns:
        Success message confirming the status change
    Raises ValueError if project not found or status is invalid.
    """
    client = get_client()
    client.set_project_status(project_id, status)

    status_display = status.replace("_", " ").title()
    return f"Successfully set project status to: {status_display}"


@mcp.tool()
def get_stalled_projects(days_inactive: int = 30) -> str:
    """Get active projects with no recent task activity.

    Args:
        days_inactive: Minimum days of inactivity to consider a project stalled (default: 30)

    Returns:
        Formatted text with stalled projects sorted by inactivity (days, last activity date)
    Projects with no activity ever are included.
    """
    client = get_client()
    projects = client.get_stalled_projects(days_inactive=days_inactive)

    if not projects:
        return f"No stalled projects found (inactive for {days_inactive}+ days)."

    result = f"Found {len(projects)} stalled projects (inactive for {days_inactive}+ days):\n\n"

    for proj in projects:
        days = proj.get('daysInactive')
        last_activity = proj.get('lastActivityDate')

        if days is not None:
            result += f"• {proj['name']} ({days} days inactive)\n"
        else:
            result += f"• {proj['name']} (no activity recorded)\n"

        result += f"  ID: {proj['id']}\n"

        if last_activity:
            result += f"  Last activity: {last_activity}\n"

        result += "\n"

    return result.strip()


# ============================================================================
# Task Tools
# ============================================================================

@mcp.tool()
def get_tasks(
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
def get_project(project_id: str) -> str:
    """Get details for a specific project by its ID.

    Args:
        project_id: The ID of the project to retrieve

    Returns:
        Formatted text with detailed project information including task counts and statistics
    """
    client = get_client()
    project = client.get_project(project_id)

    result = f"Project Details:\n\n"
    result += f"ID: {project['id']}\n"
    result += f"Name: {project['name']}\n"
    result += f"Status: {project['status']}\n"
    if project.get('folderPath'):
        result += f"Folder: {project['folderPath']}\n"

    # Add statistics
    result += f"\nStatistics:\n"
    result += f"  Total Tasks: {project.get('taskCount', 0)}\n"
    result += f"  Completed: {project.get('completedTaskCount', 0)}\n"
    result += f"  Remaining: {project.get('remainingTaskCount', 0)}\n"
    result += f"  Progress: {project.get('completionPercentage', 0.0):.1f}%\n"

    # Add review metadata
    if project.get('reviewInterval') or project.get('lastReviewDate') or project.get('nextReviewDate'):
        result += f"\nReview:\n"
        if project.get('reviewInterval'):
            result += f"  Interval: {project['reviewInterval']}\n"
        if project.get('lastReviewDate'):
            result += f"  Last Reviewed: {project['lastReviewDate']}\n"
        if project.get('nextReviewDate'):
            result += f"  Next Review: {project['nextReviewDate']}\n"

    if project.get('note'):
        result += f"\nNote: {_truncate_note(project['note'])}\n"

    return result


@mcp.tool()
def get_task(task_id: str) -> str:
    """Get details for a specific task by its ID.

    Args:
        task_id: The ID of the task to retrieve

    Returns:
        Formatted text with detailed task information including all properties
    """
    client = get_client()
    task = client.get_task(task_id)

    result = f"Task Details:\n\n"
    result += _format_task(task)
    if task.get('completionDate'):
        result += f"Completion Date: {task['completionDate']}\n"

    return result


@mcp.tool()
def get_subtasks(task_id: str) -> str:
    """Get all subtasks (child tasks) of a given task.

    Args:
        task_id: The ID of the parent task

    Returns:
        Formatted text with list of child tasks or message if task has no subtasks
    """
    client = get_client()
    subtasks = client.get_subtasks(task_id)

    if not subtasks:
        return f"Task has 0 subtasks"

    result = f"Found {len(subtasks)} subtasks:\n\n"
    for task in subtasks:
        result += _format_task(task)
        result += "\n"

    return result


@mcp.tool()
def add_task(
    project_id: str,
    task_name: str,
    note: Optional[str] = None,
    due_date: Optional[str] = None,
    defer_date: Optional[str] = None,
    flagged: bool = False,
    tags: Optional[list[str]] = None
) -> str:
    """Add a new task to a specific OmniFocus project with full properties support.

    Args:
        project_id: The ID of the project to add the task to
        task_name: The name/title of the task
        note: Optional note/description for the task (plain text only - rich text formatting is not supported via automation APIs)
        due_date: Due date in ISO 8601 format (e.g., '2025-10-15' or '2025-10-15T17:00:00')
        defer_date: Defer date in ISO 8601 format (when task becomes available)
        flagged: Whether to flag the task (default: False)
        tags: List of tag names to assign to the task (tags must already exist)

    Returns:
        Success message with task name, project, and all configured properties
    """
    client = get_client()
    success = client.add_task(
        project_id=project_id,
        task_name=task_name,
        note=note or "",
        due_date=due_date,
        defer_date=defer_date,
        flagged=flagged,
        tags=tags or []
    )

    if success:
        result = f"Successfully added task '{task_name}' to project {project_id}"
        if due_date:
            result += f"\nDue date: {due_date}"
        if defer_date:
            result += f"\nDefer date: {defer_date}"
        if flagged:
            result += "\nFlagged: Yes"
        if tags:
            result += f"\nTags: {', '.join(tags)}"
        return result
    else:
        return f"Error: Failed to add task '{task_name}'"


@mcp.tool()
def update_task(
    task_id: str,
    name: Optional[str] = None,
    note: Optional[str] = None,
    due_date: Optional[str] = None,
    defer_date: Optional[str] = None,
    flagged: Optional[str] = None
) -> str:
    """Update an existing task in OmniFocus.

    Args:
        task_id: The ID of the task to update
        name: New task name (optional)
        note: New note content (optional). WARNING: If provided, this will remove any rich text formatting (bold, italics, links, etc.) and replace it with plain text. OmniFocus automation APIs only support plain text notes. If not provided, the existing note will be preserved unchanged.
        due_date: New due date in ISO 8601 format, or empty string to clear (optional)
        defer_date: New defer date in ISO 8601 format, or empty string to clear (optional)
        flagged: New flagged status - "true" to flag, "false" to unflag, or omit to leave unchanged (optional)

    Returns:
        Success message listing all updated fields
    """
    # Convert string flagged parameter to boolean for client
    flagged_bool: Optional[bool] = None
    if flagged is not None:
        if flagged.lower() == "true":
            flagged_bool = True
        elif flagged.lower() == "false":
            flagged_bool = False
        else:
            return f"Error: Invalid flagged value '{flagged}'. Must be 'true' or 'false'."

    client = get_client()
    success = client.update_task(
        task_id=task_id,
        name=name,
        note=note,
        due_date=due_date,
        defer_date=defer_date,
        flagged=flagged_bool
    )

    if success:
        return f"Successfully updated task {task_id}"
    else:
        return f"Error: Failed to update task {task_id}"


@mcp.tool()
def complete_task(task_id: str) -> str:
    """Mark a task as completed in OmniFocus.

    Args:
        task_id: The ID of the task to complete

    Returns:
        Success message confirming task completion
    """
    client = get_client()
    success = client.complete_task(task_id)

    if success:
        return f"Successfully completed task {task_id}"
    else:
        return f"Error: Failed to complete task {task_id}"


@mcp.tool()
def complete_tasks(task_ids: list[str]) -> str:
    """Mark multiple tasks as completed in a single operation (more efficient than calling complete_task repeatedly).

    Args:
        task_ids: List of task IDs to complete

    Returns:
        Summary with count of completed tasks and any errors encountered
    """
    client = get_client()
    count = client.complete_tasks(task_ids)
    return f"Successfully completed {count} of {len(task_ids)} tasks"


# ============================================================================
# Inbox Tools
# ============================================================================

@mcp.tool()
def create_inbox_task(
    task_name: str,
    note: Optional[str] = None,
    due_date: Optional[str] = None,
    flagged: bool = False
) -> str:
    """Create a new task directly in the OmniFocus inbox (quick capture).

    Args:
        task_name: The name/title of the task
        note: Optional note/description for the task (plain text only - rich text formatting is not supported via automation APIs)
        due_date: Optional due date in ISO 8601 format
        flagged: Whether to flag the task (default: False)

    Returns:
        Success message with task ID and configured properties
    """
    client = get_client()
    success = client.create_inbox_task(
        task_name=task_name,
        note=note or "",
        due_date=due_date,
        flagged=flagged
    )

    if success:
        result = f"Successfully created inbox task '{task_name}'"
        if due_date:
            result += f"\nDue date: {due_date}"
        if flagged:
            result += "\nFlagged: Yes"
        return result
    else:
        return f"Error: Failed to create inbox task '{task_name}'"


# ============================================================================
# Tag Tools
# ============================================================================

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
def add_tag_to_task(task_id: str, tag_name: str) -> str:
    """Add a tag to an existing task in OmniFocus.

    Args:
        task_id: The ID of the task to tag
        tag_name: The name of the tag to add (tag must already exist)

    Returns:
        Success message confirming tag was added to task
    """
    client = get_client()
    success = client.add_tag_to_task(task_id, tag_name)

    if success:
        return f"Successfully added tag '{tag_name}' to task {task_id}"
    else:
        return f"Error: Failed to add tag '{tag_name}' to task {task_id}"


@mcp.tool()
def add_tag_to_tasks(task_ids: list[str], tag_name: str) -> str:
    """Add a tag to multiple tasks in a single operation (more efficient than calling add_tag_to_task repeatedly).

    Args:
        task_ids: List of task IDs to tag
        tag_name: The name of the tag to add (tag must already exist)

    Returns:
        Summary with count of tasks tagged and any errors encountered
    """
    client = get_client()
    try:
        count = client.add_tag_to_tasks(task_ids, tag_name)
        return f"Successfully added tag '{tag_name}' to {count} of {len(task_ids)} tasks"
    except Exception as e:
        return f"Error adding tag to tasks: {str(e)}"


@mcp.tool()
def remove_tag_from_tasks(task_ids: list[str], tag_name: str) -> str:
    """Remove a tag from multiple tasks in a single operation (batch operation for efficiency).

    Args:
        task_ids: List of task IDs to remove tag from
        tag_name: The name of the tag to remove

    Returns:
        Summary with count of tasks untagged and any errors encountered
    """
    client = get_client()
    try:
        count = client.remove_tag_from_tasks(task_ids, tag_name)
        return f"Successfully removed tag '{tag_name}' from {count} of {len(task_ids)} tasks"
    except Exception as e:
        return f"Error removing tag from tasks: {str(e)}"


# ============================================================================
# Note Tools
# ============================================================================

@mcp.tool()
def add_note(project_id: str, note_text: str) -> str:
    """Append a note to an OmniFocus project.

    Args:
        project_id: The ID of the project to add the note to
        note_text: The text to append to the project's notes

    Returns:
        Success message confirming note was appended
    """
    client = get_client()
    success = client.add_note(project_id, note_text)

    if success:
        return f"Successfully added note to project {project_id}"
    else:
        return f"Error: Failed to add note to project {project_id}"


@mcp.tool()
def get_note(item_id: str, item_type: str = "project") -> str:
    """Get the full note content from a project or task.

    This tool retrieves the complete note without truncation, unlike get_projects
    or get_tasks which truncate notes to {NOTE_TRUNCATION_LENGTH} characters.

    Args:
        item_id: The ID of the project or task
        item_type: Either "project" or "task" (default: "project")

    Returns:
        The full note content as plain text (may be empty if no note exists)
    """
    client = get_client()
    note_content = client.get_note(item_id, item_type)

    if note_content:
        return f"Note for {item_type} {item_id}:\n\n{note_content}"
    else:
        return f"No note found for {item_type} {item_id} (note is empty)"


# ============================================================================
# Deletion Tools
# ============================================================================

@mcp.tool()
def delete_task(task_id: str) -> str:
    """Permanently remove a task from OmniFocus (cannot be undone).

    WARNING: This permanently deletes the task and cannot be undone.

    Args:
        task_id: The ID of the task to delete

    Returns:
        Success message confirming task deletion
    """
    client = get_client()
    try:
        success = client.delete_task(task_id)
        if success:
            return f"Successfully deleted task {task_id}"
        else:
            return f"Error: Failed to delete task {task_id}"
    except Exception as e:
        return f"Error deleting task: {str(e)}"


@mcp.tool()
def delete_project(project_id: str) -> str:
    """Delete a project from OmniFocus.

    WARNING: This permanently deletes the project and all its tasks. Cannot be undone.

    Args:
        project_id: The ID of the project to delete

    Returns:
        Success message confirming project deletion
    """
    client = get_client()
    try:
        success = client.delete_project(project_id)
        if success:
            return f"Successfully deleted project {project_id}"
        else:
            return f"Error: Failed to delete project {project_id}"
    except Exception as e:
        return f"Error deleting project: {str(e)}"


@mcp.tool()
def delete_tasks(task_ids: list[str]) -> str:
    """Delete multiple tasks from OmniFocus in a single operation (batch operation for efficiency).

    WARNING: This permanently deletes the tasks and cannot be undone.

    Args:
        task_ids: List of task IDs to delete

    Returns:
        Summary of deleted tasks with count and any errors encountered
    """
    client = get_client()
    try:
        count = client.delete_tasks(task_ids)
        return f"Successfully deleted {count} of {len(task_ids)} tasks"
    except Exception as e:
        return f"Error deleting tasks: {str(e)}"


@mcp.tool()
def delete_projects(project_ids: list[str]) -> str:
    """Delete multiple projects from OmniFocus in a single operation (batch operation for efficiency).

    WARNING: This permanently deletes the projects and all their tasks. Cannot be undone.

    Args:
        project_ids: List of project IDs to delete

    Returns:
        Summary of deleted projects with count and any errors encountered
    """
    client = get_client()
    try:
        count = client.delete_projects(project_ids)
        return f"Successfully deleted {count} of {len(project_ids)} projects"
    except Exception as e:
        return f"Error deleting projects: {str(e)}"


# ============================================================================
# Task Movement Tools
# ============================================================================

@mcp.tool()
def move_task(task_id: str, project_id: Optional[str] = None) -> str:
    """Move a task to a different project or to inbox.

    Args:
        task_id: The ID of the task to move
        project_id: The ID of the destination project, or omit/null to move to inbox

    Returns:
        Success message with task name and new location (project or inbox)
    """
    client = get_client()
    try:
        success = client.move_task(task_id, project_id)
        if success:
            if project_id:
                return f"Successfully moved task {task_id} to project {project_id}"
            else:
                return f"Successfully moved task {task_id} to inbox"
        else:
            return f"Error: Failed to move task {task_id}"
    except Exception as e:
        return f"Error moving task: {str(e)}"


@mcp.tool()
def move_tasks(task_ids: list[str], project_id: Optional[str] = None) -> str:
    """Move multiple tasks to a different project or inbox in a single operation (more efficient than calling move_task repeatedly).

    Args:
        task_ids: List of task IDs to move
        project_id: The ID of the destination project, or omit/null to move to inbox

    Returns:
        Summary of moved tasks with count, destination, and any errors encountered
    """
    client = get_client()
    try:
        count = client.move_tasks(task_ids, project_id)
        if project_id:
            return f"Successfully moved {count} of {len(task_ids)} tasks to project {project_id}"
        else:
            return f"Successfully moved {count} of {len(task_ids)} tasks to inbox"
    except Exception as e:
        return f"Error moving tasks: {str(e)}"


@mcp.tool()
def drop_task(task_id: str) -> str:
    """Drop a task (mark as on hold indefinitely).

    Dropping a task is different from deleting it - the task remains in OmniFocus
    but is marked as on hold and won't appear in available task lists.

    Args:
        task_id: The ID of the task to drop

    Returns:
        Success message confirming task was dropped
    """
    client = get_client()
    try:
        success = client.drop_task(task_id)
        if success:
            return f"Successfully dropped task {task_id}"
        else:
            return f"Error: Failed to drop task {task_id}"
    except Exception as e:
        return f"Error dropping task: {str(e)}"


@mcp.tool()
def drop_tasks(task_ids: list[str]) -> str:
    """Drop multiple tasks (mark as on hold indefinitely) in a single operation (batch operation for efficiency).

    Dropping tasks is different from deleting them - the tasks remain in OmniFocus
    but are marked as on hold and won't appear in available task lists.

    Args:
        task_ids: List of task IDs to drop

    Returns:
        Summary of dropped tasks with count and any errors encountered
    """
    client = get_client()
    try:
        count = client.drop_tasks(task_ids)
        return f"Successfully dropped {count} of {len(task_ids)} tasks"
    except Exception as e:
        return f"Error dropping tasks: {str(e)}"


# ============================================================================
# Folder Tools
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
def set_parent_task(task_id: str, parent_task_id: Optional[str] = None) -> str:
    """Set the parent task of a task (make it a subtask) or make it root-level.

    Args:
        task_id: The ID of the task to modify
        parent_task_id: The ID of the parent task, or omit/null to make it root-level

    Returns:
        Success message confirming the parent-child relationship
    """
    client = get_client()
    try:
        success = client.set_parent_task(task_id, parent_task_id)
        if success:
            if parent_task_id:
                return f"Successfully made task {task_id} a subtask of {parent_task_id}"
            else:
                return f"Successfully made task {task_id} a root-level task"
        else:
            return f"Error: Failed to set parent task for {task_id}"
    except Exception as e:
        return f"Error setting parent task: {str(e)}"


# ============================================================================
# Project Review Tools
# ============================================================================

@mcp.tool()
def set_review_interval(project_id: str, interval_weeks: int) -> str:
    """Set the review interval for a project.

    Args:
        project_id: The ID of the project
        interval_weeks: Review interval in weeks (e.g., 1 for weekly, 4 for monthly)

    Returns:
        Success message with new review interval and next review date
    """
    client = get_client()
    try:
        success = client.set_review_interval(project_id, interval_weeks)
        if success:
            return f"Successfully set review interval to {interval_weeks} week(s) for project {project_id}"
        else:
            return f"Error: Failed to set review interval for project {project_id}"
    except Exception as e:
        return f"Error setting review interval: {str(e)}"


@mcp.tool()
def mark_project_reviewed(project_id: str) -> str:
    """Mark a project as reviewed (updates last review date and calculates next review date).

    Args:
        project_id: The ID of the project

    Returns:
        Success message with updated review dates
    """
    client = get_client()
    try:
        success = client.mark_project_reviewed(project_id)
        if success:
            return f"Successfully marked project {project_id} as reviewed"
        else:
            return f"Error: Failed to mark project {project_id} as reviewed"
    except Exception as e:
        return f"Error marking project as reviewed: {str(e)}"


@mcp.tool()
def get_projects_due_for_review() -> str:
    """Get all projects that are due for review.

    Returns:
        Formatted list of projects needing review with last review date and next review date
    """
    client = get_client()
    projects = client.get_projects_due_for_review()

    if not projects:
        return "Found 0 projects due for review"

    result = f"Found {len(projects)} projects due for review:\n\n"
    for project in projects:
        result += f"ID: {project['id']}\n"
        result += f"Name: {project['name']}\n"
        if project.get('nextReviewDate'):
            result += f"Next Review: {project['nextReviewDate']}\n"
        if project.get('lastReviewDate'):
            result += f"Last Reviewed: {project['lastReviewDate']}\n"
        result += "---\n"

    return result


# ============================================================================
# Time Estimation Tools
# ============================================================================

@mcp.tool()
def set_estimated_minutes(task_id: str, minutes: int) -> str:
    """Set the estimated time for a task.

    Args:
        task_id: The ID of the task
        minutes: Estimated time in minutes (0 to clear estimate)

    Returns:
        Success message with task name and new time estimate
    """
    client = get_client()
    try:
        success = client.set_estimated_minutes(task_id, minutes)
        if success:
            if minutes == 0:
                return f"Successfully cleared time estimate for task {task_id}"
            else:
                return f"Successfully set time estimate to {minutes} minute(s) for task {task_id}"
        else:
            return f"Error: Failed to set time estimate for task {task_id}"
    except Exception as e:
        return f"Error setting time estimate: {str(e)}"


# ============================================================================
# Perspective Tools
# ============================================================================

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
