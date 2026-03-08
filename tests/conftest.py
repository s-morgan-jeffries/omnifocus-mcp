"""Pytest fixtures for integration tests.

This module provides reusable fixtures for integration testing with real OmniFocus.
All fixtures properly clean up after themselves to prevent test pollution.

Key features:
- Automatic teardown even if tests fail
- Unique naming with UUID to prevent conflicts
- Batch cleanup for better performance
- Error handling to prevent cascade failures
"""

import os
import uuid
import warnings
from typing import Optional

import pytest

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector, run_applescript


# ============================================================================
# Session and Class-Scoped Fixtures (Shared Across Tests)
# ============================================================================

@pytest.fixture(scope="class")
def client():
    """Create a client for real OmniFocus testing.

    Scope: class - shared across all tests in a class
    Safety: Enabled - will verify test database before operations

    Returns:
        OmniFocusConnector: Client with safety checks enabled
    """
    return OmniFocusConnector(enable_safety_checks=True)


# ============================================================================
# Function-Scoped Fixtures (Create/Cleanup Per Test)
# ============================================================================

@pytest.fixture(scope="function")
def test_project(client):
    """Create a test project and clean it up after the test.

    Creates a unique project with name "Test Project {uuid}" to avoid conflicts.
    Automatically deletes the project after the test completes (even if test fails).

    Args:
        client: OmniFocusConnector fixture

    Yields:
        str: Project ID

    Example:
        def test_update_project(client, test_project):
            result = client.update_project(test_project, project_name="Updated")
            assert result["success"] is True
    """
    # Setup: Create unique project
    unique_name = f"Test Project {uuid.uuid4()}"
    project_id = client.create_project(unique_name)

    yield project_id

    # Teardown: Always clean up, even if test fails
    try:
        client.delete_projects(project_id)
    except Exception as e:
        warnings.warn(f"Failed to clean up test project {project_id}: {e}")


@pytest.fixture(scope="function")
def test_project_with_note(client):
    """Create a test project with a note and clean it up after the test.

    Args:
        client: OmniFocusConnector fixture

    Yields:
        str: Project ID

    Example:
        def test_project_notes(client, test_project_with_note):
            projects = client.get_projects(project_id=test_project_with_note,
                                          include_full_notes=True)
            assert len(projects[0]['note']) > 0
    """
    unique_name = f"Test Project {uuid.uuid4()}"
    project_id = client.create_project(unique_name, note="Test note content")

    yield project_id

    try:
        client.delete_projects(project_id)
    except Exception as e:
        warnings.warn(f"Failed to clean up test project {project_id}: {e}")


@pytest.fixture(scope="function")
def test_projects(client):
    """Create multiple test projects for batch operations.

    Creates 3 projects with unique names.

    Args:
        client: OmniFocusConnector fixture

    Yields:
        list[str]: List of project IDs

    Example:
        def test_batch_update(client, test_projects):
            result = client.update_projects(test_projects, status="on_hold")
            assert result["updated_count"] == 3
    """
    # Setup: Create 3 unique projects
    base_uuid = uuid.uuid4()
    project_ids = []
    for i in range(3):
        unique_name = f"Test Project {base_uuid}-{i}"
        project_id = client.create_project(unique_name)
        project_ids.append(project_id)

    yield project_ids

    # Teardown: Batch delete for efficiency
    try:
        client.delete_projects(project_ids)
    except Exception as e:
        warnings.warn(f"Failed to clean up test projects {project_ids}: {e}")


@pytest.fixture(scope="function")
def test_folder(client):
    """Create a test folder and clean it up after the test.

    Creates a unique folder with name "Test Folder {uuid}" to avoid conflicts.
    Note: Cannot delete folders in OmniFocus, so cleanup is limited.

    Args:
        client: OmniFocusConnector fixture

    Yields:
        str: Folder ID

    Example:
        def test_create_project_in_folder(client, test_folder):
            folders = client.get_folders()
            folder_names = [f['name'] for f in folders]
            assert any('Test Folder' in name for name in folder_names)
    """
    # Setup: Create unique folder
    unique_name = f"Test Folder {uuid.uuid4()}"
    folder_id = client.create_folder(unique_name)

    yield folder_id

    # Teardown: OmniFocus doesn't support folder deletion via AppleScript
    # The folder will remain but with a unique name it won't interfere
    # NOTE: This is a known limitation - see issue #143
    warnings.warn(
        f"Test folder {folder_id} cannot be deleted (OmniFocus limitation). "
        "This may contribute to test database pollution over time."
    )


@pytest.fixture(scope="function")
def test_task(client, test_project):
    """Create a test task and clean it up after the test.

    Creates a unique task in the test_project.
    Automatically deletes the task after the test completes.

    Args:
        client: OmniFocusConnector fixture
        test_project: Project ID from test_project fixture

    Yields:
        str: Task ID

    Example:
        def test_update_task(client, test_task):
            result = client.update_task(test_task, flagged=True)
            assert result["success"] is True
    """
    # Setup: Create unique task in project
    unique_name = f"Test Task {uuid.uuid4()}"
    task_id = client.create_task(unique_name, project_id=test_project)

    yield task_id

    # Teardown: Always clean up
    try:
        client.delete_tasks(task_id)
    except Exception as e:
        warnings.warn(f"Failed to clean up test task {task_id}: {e}")


@pytest.fixture(scope="function")
def test_task_inbox(client):
    """Create a test task in inbox and clean it up after the test.

    Creates a unique task with no project (goes to inbox).
    Automatically deletes the task after the test completes.

    Args:
        client: OmniFocusConnector fixture

    Yields:
        str: Task ID

    Example:
        def test_inbox_tasks(client, test_task_inbox):
            inbox_tasks = client.get_tasks(inbox_only=True)
            task_ids = [t['id'] for t in inbox_tasks]
            assert test_task_inbox in task_ids
    """
    # Setup: Create unique inbox task (no project)
    unique_name = f"Test Inbox Task {uuid.uuid4()}"
    task_id = client.create_task(unique_name)  # No project_id = inbox

    yield task_id

    # Teardown: Always clean up
    try:
        client.delete_tasks(task_id)
    except Exception as e:
        warnings.warn(f"Failed to clean up test inbox task {task_id}: {e}")


@pytest.fixture(scope="function")
def test_tasks(client, test_project):
    """Create multiple test tasks for batch operations.

    Creates 3 tasks with unique names in the test_project.

    Args:
        client: OmniFocusConnector fixture
        test_project: Project ID from test_project fixture

    Yields:
        list[str]: List of task IDs

    Example:
        def test_batch_complete(client, test_tasks):
            result = client.update_tasks(test_tasks, completed=True)
            assert result["updated_count"] == 3
    """
    # Setup: Create 3 unique tasks
    base_uuid = uuid.uuid4()
    task_ids = []
    for i in range(3):
        unique_name = f"Test Task {base_uuid}-{i}"
        task_id = client.create_task(unique_name, project_id=test_project)
        task_ids.append(task_id)

    yield task_ids

    # Teardown: Batch delete for efficiency
    try:
        client.delete_tasks(task_ids)
    except Exception as e:
        warnings.warn(f"Failed to clean up test tasks {task_ids}: {e}")


@pytest.fixture(scope="function")
def test_task_with_note(client, test_project):
    """Create a test task with a note and clean it up after the test.

    Args:
        client: OmniFocusConnector fixture
        test_project: Project ID from test_project fixture

    Yields:
        str: Task ID

    Example:
        def test_task_notes(client, test_task_with_note):
            tasks = client.get_tasks(task_id=test_task_with_note,
                                    include_full_notes=True)
            assert len(tasks[0]['note']) > 0
    """
    unique_name = f"Test Task {uuid.uuid4()}"
    task_id = client.create_task(
        unique_name,
        project_id=test_project,
        note="Test note content"
    )

    yield task_id

    try:
        client.delete_tasks(task_id)
    except Exception as e:
        warnings.warn(f"Failed to clean up test task {task_id}: {e}")


@pytest.fixture(scope="function")
def test_parent_task_with_subtasks(client, test_project):
    """Create a parent task with 2 subtasks and clean up after the test.

    Creates:
    - 1 parent task
    - 2 subtasks under the parent

    Args:
        client: OmniFocusConnector fixture
        test_project: Project ID from test_project fixture

    Yields:
        dict: {'parent_id': str, 'subtask_ids': list[str]}

    Example:
        def test_hierarchy(client, test_parent_task_with_subtasks):
            parent_id = test_parent_task_with_subtasks['parent_id']
            subtasks = client.get_tasks(parent_task_id=parent_id)
            assert len(subtasks) == 2
    """
    # Setup: Create parent and subtasks
    base_uuid = uuid.uuid4()
    parent_name = f"Test Parent Task {base_uuid}"
    parent_id = client.create_task(parent_name, project_id=test_project)

    subtask_ids = []
    for i in range(2):
        subtask_name = f"Test Subtask {base_uuid}-{i}"
        subtask_id = client.create_task(subtask_name, project_id=test_project)
        # Set parent relationship
        client.update_task(subtask_id, parent_task_id=parent_id)
        subtask_ids.append(subtask_id)

    yield {
        'parent_id': parent_id,
        'subtask_ids': subtask_ids
    }

    # Teardown: Delete all tasks (subtasks first, then parent)
    try:
        all_task_ids = subtask_ids + [parent_id]
        client.delete_tasks(all_task_ids)
    except Exception as e:
        warnings.warn(f"Failed to clean up parent task and subtasks: {e}")


# ============================================================================
# Specialized Fixtures for Complex Scenarios
# ============================================================================

@pytest.fixture(scope="function")
def test_sequential_project_with_tasks(client):
    """Create a sequential project with 3 tasks for testing availability.

    Creates:
    - 1 sequential project
    - 3 tasks in order (only first should be available)

    Args:
        client: OmniFocusConnector fixture

    Yields:
        dict: {'project_id': str, 'task_ids': list[str]}

    Example:
        def test_sequential_availability(client, test_sequential_project_with_tasks):
            task_ids = test_sequential_project_with_tasks['task_ids']
            tasks = client.get_tasks(task_id=task_ids[0])
            assert tasks[0]['available'] is True  # First task available
    """
    # Setup: Create sequential project
    base_uuid = uuid.uuid4()
    project_name = f"Test Sequential Project {base_uuid}"
    project_id = client.create_project(project_name, sequential=True)

    # Create 3 tasks
    task_ids = []
    for i in range(3):
        task_name = f"Test Task {base_uuid}-{i}"
        task_id = client.create_task(task_name, project_id=project_id)
        task_ids.append(task_id)

    yield {
        'project_id': project_id,
        'task_ids': task_ids
    }

    # Teardown: Delete project (cascade deletes tasks)
    try:
        client.delete_projects(project_id)
    except Exception as e:
        warnings.warn(f"Failed to clean up sequential project test: {e}")


@pytest.fixture(scope="function")
def test_project_with_folder(client, test_folder):
    """Create a project in a test folder.

    Args:
        client: OmniFocusConnector fixture
        test_folder: Folder ID from test_folder fixture

    Yields:
        dict: {'project_id': str, 'folder_id': str}

    Example:
        def test_folder_hierarchy(client, test_project_with_folder):
            project_id = test_project_with_folder['project_id']
            projects = client.get_projects(project_id=project_id)
            assert 'Test Folder' in projects[0]['folderPath']
    """
    # Get folder name for folder_path parameter
    folders = client.get_folders()
    test_folder_obj = next(f for f in folders if f['id'] == test_folder)
    folder_path = test_folder_obj['name']

    # Setup: Create project in folder
    base_uuid = uuid.uuid4()
    project_name = f"Test Project {base_uuid}"
    project_id = client.create_project(project_name, folder_path=folder_path)

    yield {
        'project_id': project_id,
        'folder_id': test_folder
    }

    # Teardown: Delete project (folder remains due to OmniFocus limitation)
    try:
        client.delete_projects(project_id)
    except Exception as e:
        warnings.warn(f"Failed to clean up project in folder: {e}")


@pytest.fixture(scope="class")
def ensure_test_tags():
    """Ensure required test tags exist in OmniFocus.

    Creates tags needed by integration tests if they don't already exist.
    Tags persist across tests in the class (not cleaned up, as OmniFocus
    doesn't support tag deletion via AppleScript).

    Tags created: test-work, test-urgent, urgent, work
    """
    tag_names = ["test-work", "test-urgent", "urgent", "work"]
    for tag_name in tag_names:
        try:
            run_applescript(f'''
                tell application "OmniFocus"
                    tell front document
                        try
                            first flattened tag whose name is "{tag_name}"
                        on error
                            make new tag with properties {{name:"{tag_name}"}}
                        end try
                    end tell
                end tell
            ''')
        except Exception as e:
            warnings.warn(f"Failed to create test tag '{tag_name}': {e}")
