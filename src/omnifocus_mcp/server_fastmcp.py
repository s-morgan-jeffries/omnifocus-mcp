#!/usr/bin/env python3
"""FastMCP Server for OmniFocus integration."""
import os
from typing import Optional

from fastmcp import FastMCP

from .omnifocus_client import OmniFocusClient

# Create FastMCP server
mcp = FastMCP("omnifocus-mcp")

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


# ============================================================================
# Project Tools
# ============================================================================

@mcp.tool()
def get_projects() -> str:
    """Get all active projects from OmniFocus with their folder hierarchy, names, notes, and status.

    Returns a formatted list of all active projects with their details.
    """
    client = get_client()
    projects = client.get_projects()

    if not projects:
        return "Found 0 active projects"

    # Format projects for display
    result = f"Found {len(projects)} active projects:\n\n"
    for proj in projects:
        result += f"ID: {proj['id']}\n"
        result += f"Name: {proj['name']}\n"
        if proj.get('folderPath'):
            result += f"Folder: {proj['folderPath']}\n"
        result += f"Status: {proj['status']}\n"
        if proj.get('note'):
            note = proj['note']
            if len(note) > 100:
                note = note[:100] + "..."
            result += f"Note: {note}\n"
        result += "\n"

    return result


@mcp.tool()
def search_projects(query: str) -> str:
    """Search OmniFocus projects by name, note content, or folder path.

    Args:
        query: Search query to match against project names, notes, or folder paths

    Returns a formatted list of matching projects.
    """
    client = get_client()
    projects = client.search_projects(query)

    if not projects:
        return f"No projects found matching '{query}'"

    result = f"Found {len(projects)} projects matching '{query}':\n\n"
    for proj in projects:
        result += f"ID: {proj['id']}\n"
        result += f"Name: {proj['name']}\n"
        if proj.get('folderPath'):
            result += f"Folder: {proj['folderPath']}\n"
        result += f"Status: {proj['status']}\n"
        if proj.get('note'):
            note = proj['note']
            if len(note) > 100:
                note = note[:100] + "..."
            result += f"Note: {note}\n"
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
        note: Optional note/description for the project
        folder_path: Optional folder path (e.g., "Work > Clients") - folder must exist in OmniFocus
        sequential: If True, tasks must be completed in order; if False, tasks can be done in parallel (default: False)

    Returns the project ID of the newly created project.
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
        result += f"\nNote: {note[:100]}{'...' if len(note) > 100 else ''}"

    return result


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
    tag_filter: Optional[list[str]] = None
) -> str:
    """Get tasks from OmniFocus with optional filtering.

    Args:
        project_id: Optional project ID to filter tasks
        flagged_only: If True, only return flagged tasks
        include_completed: If True, include completed tasks (default: False)
        available_only: If True, only return available tasks (not blocked or deferred)
        overdue: If True, only return overdue tasks
        tag_filter: List of tag names to filter by (task must have all tags)

    Returns a formatted list of tasks.
    """
    client = get_client()
    tasks = client.get_tasks(
        project_id=project_id,
        flagged_only=flagged_only,
        include_completed=include_completed,
        available_only=available_only,
        overdue=overdue,
        tag_filter=tag_filter
    )

    if not tasks:
        return "Found 0 tasks"

    result = f"Found {len(tasks)} tasks:\n\n"
    for task in tasks:
        result += f"ID: {task['id']}\n"
        result += f"Name: {task['name']}\n"
        result += f"Project: {task.get('projectName', 'N/A')}\n"
        result += f"Completed: {task['completed']}\n"
        if task.get('flagged'):
            result += f"Flagged: Yes\n"
        if task.get('dueDate'):
            result += f"Due: {task['dueDate']}\n"
        if task.get('deferDate'):
            result += f"Defer: {task['deferDate']}\n"
        if task.get('tags'):
            result += f"Tags: {task['tags']}\n"
        if task.get('note'):
            note = task['note']
            if len(note) > 100:
                note = note[:100] + "..."
            result += f"Note: {note}\n"
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
        note: Optional note/description for the task
        due_date: Due date in ISO 8601 format (e.g., '2025-10-15' or '2025-10-15T17:00:00')
        defer_date: Defer date in ISO 8601 format (when task becomes available)
        flagged: Whether to flag the task (default: False)
        tags: List of tag names to assign to the task (tags must already exist)

    Returns a success message with the task details.
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
    flagged: Optional[bool] = None
) -> str:
    """Update an existing task in OmniFocus.

    Args:
        task_id: The ID of the task to update
        name: New task name (optional)
        note: New note content (optional)
        due_date: New due date in ISO 8601 format, or empty string to clear (optional)
        defer_date: New defer date in ISO 8601 format, or empty string to clear (optional)
        flagged: New flagged status (optional)

    Returns a success message.
    """
    client = get_client()
    success = client.update_task(
        task_id=task_id,
        name=name,
        note=note,
        due_date=due_date,
        defer_date=defer_date,
        flagged=flagged
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

    Returns a success message.
    """
    client = get_client()
    success = client.complete_task(task_id)

    if success:
        return f"Successfully completed task {task_id}"
    else:
        return f"Error: Failed to complete task {task_id}"


# ============================================================================
# Inbox Tools
# ============================================================================

@mcp.tool()
def get_inbox_tasks() -> str:
    """Get all tasks from the OmniFocus inbox.

    Returns a formatted list of inbox tasks.
    """
    client = get_client()
    tasks = client.get_inbox_tasks()

    if not tasks:
        return "No tasks in inbox"

    result = f"Found {len(tasks)} inbox tasks:\n\n"
    for task in tasks:
        result += f"ID: {task['id']}\n"
        result += f"Name: {task['name']}\n"
        result += f"Completed: {task['completed']}\n"
        if task.get('flagged'):
            result += f"Flagged: Yes\n"
        if task.get('dueDate'):
            result += f"Due: {task['dueDate']}\n"
        if task.get('note'):
            note = task['note']
            if len(note) > 100:
                note = note[:100] + "..."
            result += f"Note: {note}\n"
        result += "\n"

    return result


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
        note: Optional note/description for the task
        due_date: Optional due date in ISO 8601 format
        flagged: Whether to flag the task (default: False)

    Returns a success message.
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
    """Get all tags from OmniFocus.

    Returns a formatted list of all available tags.
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

    Returns a success message.
    """
    client = get_client()
    success = client.add_tag_to_task(task_id, tag_name)

    if success:
        return f"Successfully added tag '{tag_name}' to task {task_id}"
    else:
        return f"Error: Failed to add tag '{tag_name}' to task {task_id}"


# ============================================================================
# Note Tools
# ============================================================================

@mcp.tool()
def add_note(project_id: str, note_text: str) -> str:
    """Append a note to an OmniFocus project.

    Args:
        project_id: The ID of the project to add the note to
        note_text: The text to append to the project's notes

    Returns a success message.
    """
    client = get_client()
    success = client.add_note(project_id, note_text)

    if success:
        return f"Successfully added note to project {project_id}"
    else:
        return f"Error: Failed to add note to project {project_id}"


# ============================================================================
# Deletion Tools
# ============================================================================

@mcp.tool()
def delete_task(task_id: str) -> str:
    """Delete a task from OmniFocus.

    WARNING: This permanently deletes the task and cannot be undone.

    Args:
        task_id: The ID of the task to delete

    Returns a success or error message.
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

    Returns a success or error message.
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


# ============================================================================
# Task Movement Tools
# ============================================================================

@mcp.tool()
def move_task(task_id: str, project_id: Optional[str] = None) -> str:
    """Move a task to a different project or to inbox.

    Args:
        task_id: The ID of the task to move
        project_id: The ID of the destination project, or omit/null to move to inbox

    Returns a success or error message.
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
def drop_task(task_id: str) -> str:
    """Drop a task (mark as on hold indefinitely).

    Dropping a task is different from deleting it - the task remains in OmniFocus
    but is marked as on hold and won't appear in available task lists.

    Args:
        task_id: The ID of the task to drop

    Returns a success or error message.
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


# ============================================================================
# Folder Tools
# ============================================================================

@mcp.tool()
def get_folders() -> str:
    """Get all folders from OmniFocus with their hierarchy.

    Returns a formatted list of all folders with their paths.
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

    Returns a success message with the folder ID.
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
def set_parent_task(task_id: str, parent_task_id: Optional[str] = None) -> str:
    """Set the parent task of a task (make it a subtask) or make it root-level.

    Args:
        task_id: The ID of the task to modify
        parent_task_id: The ID of the parent task, or omit/null to make it root-level

    Returns a success or error message.
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

    Returns a success or error message.
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

    Returns a success or error message.
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

    Returns a formatted list of projects needing review.
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

    Returns a success or error message.
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

    Returns a formatted list of perspectives (both built-in and custom).
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

    Returns a success or error message.
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
