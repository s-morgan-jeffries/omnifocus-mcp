"""End-to-End (E2E) integration tests for OmniFocus MCP Server.

These tests verify the COMPLETE flow:
- MCP Tool (server_fastmcp.py) → Client (omnifocus_connector.py) → AppleScript → Real OmniFocus

Unlike other test files:
- test_omnifocus_connector.py: Tests client with mocked AppleScript
- test_server_fastmcp.py: Tests MCP tools with mocked client
- test_integration_real.py: Tests client with real OmniFocus (bypasses MCP layer)
- test_e2e_real.py (THIS FILE): Tests MCP tools with real OmniFocus (full stack)

Why E2E tests matter:
- Catch parameter conversion bugs (JSON strings, type mismatches)
- Verify response formatting for Claude
- Test the exact code path that production users hit
- Found issues like tags='["tag"]' vs tags=["tag"]

Safety:
- Requires OMNIFOCUS_TEST_MODE=true
- Requires test database active
- Safety guards verify database before writes
- Tests are skipped if environment not configured

All tests use fixtures from conftest.py for automatic cleanup.

Run with: make test-e2e
"""
import os
import re
import pytest

# Import the MCP server tools
import omnifocus_mcp.server_fastmcp as server

# Extract tool functions (FastMCP @mcp.tool() returns the function directly)
create_task = server.create_task
update_task = server.update_task
update_tasks = server.update_tasks
delete_tasks = server.delete_tasks
get_tasks = server.get_tasks
get_projects = server.get_projects
create_project = server.create_project
delete_projects = server.delete_projects
get_tags = server.get_tags
create_tag = server.create_tag
update_tag = server.update_tag
delete_tags = server.delete_tags
get_folders = server.get_folders
create_folder = server.create_folder
update_folder = server.update_folder
get_perspectives = server.get_perspectives
get_focus = server.get_focus

# Skip all tests unless in test mode
pytestmark = pytest.mark.skipif(
    os.environ.get('OMNIFOCUS_TEST_MODE', '').lower() != 'true',
    reason="E2E tests require OMNIFOCUS_TEST_MODE=true. Run with: make test-e2e"
)


class TestCreateTaskE2E:
    """E2E tests for create_task() MCP tool with real OmniFocus.

    Tests the full stack:
    MCP tool → client.create_task() → AppleScript → OmniFocus

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_create_task_in_project_e2e(self, test_project):
        """E2E: Create task in project via MCP tool."""
        # Call the MCP tool (not the client directly)
        result = create_task(
            task_name="E2E Test Task - Project",
            project_id=test_project,
            note="Created by E2E test",
            flagged=True
        )

        # Verify MCP tool returns human-readable response
        assert isinstance(result, str)
        assert "E2E Test Task - Project" in result
        assert test_project in result
        assert "Successfully created" in result

        # Verify task ID is in response
        assert "Task ID:" in result

        print(f"\n✓ E2E create_task in project: {result}")

    def test_create_task_in_inbox_e2e(self):
        """E2E: Create task in inbox via MCP tool."""
        result = create_task(
            task_name="E2E Test Task - Inbox",
            project_id=None,  # Explicit inbox
            flagged=False
        )

        assert isinstance(result, str)
        assert "E2E Test Task - Inbox" in result
        assert "inbox" in result.lower()
        assert "Successfully created" in result

        print(f"\n✓ E2E create_task in inbox: {result}")

    def test_create_task_with_tags_e2e(self, test_project, ensure_test_tags):
        """E2E: Create task with tags via MCP tool."""
        result = create_task(
            task_name="E2E Test Task - Tags",
            project_id=test_project,
            tags=["work"]
        )

        assert isinstance(result, str)
        assert "E2E Test Task - Tags" in result
        assert "Successfully created" in result
        # Tags might be in response
        if "Tags:" in result:
            assert "work" in result

        print(f"\n✓ E2E create_task with tags: {result}")

    def test_create_task_with_dates_e2e(self, test_project):
        """E2E: Create task with dates via MCP tool."""
        result = create_task(
            task_name="E2E Test Task - Dates",
            project_id=test_project,
            due_date="2025-12-31",
            defer_date="2025-12-01",
            estimated_minutes=60
        )

        assert isinstance(result, str)
        assert "E2E Test Task - Dates" in result
        assert "2025-12-31" in result
        assert "60 minutes" in result or "60" in result

        print(f"\n✓ E2E create_task with dates: {result}")

    def test_create_task_error_handling_e2e(self):
        """E2E: Verify MCP tool returns error for invalid parameters."""
        # Try to create with both project_id and parent_task_id (invalid)
        # The server catches ValueError and returns an error string
        result = create_task(
            task_name="Bad Task",
            project_id="proj-123",
            parent_task_id="task-456"
        )

        # Verify error message is returned (not raised)
        assert isinstance(result, str)
        assert "error" in result.lower()

        print(f"\n✓ E2E create_task error handling: {result}")


class TestUpdateTaskE2E:
    """E2E tests for update_task() MCP tool with real OmniFocus.

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_update_task_single_field_e2e(self, client, test_project):
        """E2E: Update single field via MCP tool."""
        # Create a task to update using client (setup)
        task_id = client.create_task("E2E Test Task for Update", project_id=test_project)

        # Call MCP tool to update
        result = update_task(
            task_id=task_id,
            flagged=True
        )

        assert isinstance(result, str)
        assert "Successfully updated" in result or "success" in result.lower()

        print(f"\n✓ E2E update_task single field: {result}")

        # Cleanup
        client.delete_tasks(task_id)

    def test_update_task_multiple_fields_e2e(self, client, test_project):
        """E2E: Update multiple fields via MCP tool."""
        # Create a task to update
        task_id = client.create_task("E2E Test Task for Multi-Update", project_id=test_project)

        # Call MCP tool
        result = update_task(
            task_id=task_id,
            task_name="E2E Updated Task Name",
            flagged=False,
            note="Updated by E2E test"
        )

        assert isinstance(result, str)
        assert "Successfully updated" in result or "success" in result.lower()

        print(f"\n✓ E2E update_task multiple fields: {result}")

        # Cleanup
        client.delete_tasks(task_id)


class TestUpdateTasksE2E:
    """E2E tests for update_tasks() batch MCP tool.

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_update_tasks_batch_e2e(self, client, test_project):
        """E2E: Update multiple tasks via MCP tool."""
        # Create multiple test tasks
        task_ids = []
        for i in range(3):
            task_id = client.create_task(f"E2E Batch Test Task {i+1}", project_id=test_project)
            task_ids.append(task_id)

        # Call MCP tool
        result = update_tasks(
            tasks=[{"id": tid, "flagged": True} for tid in task_ids]
        )

        assert isinstance(result, str)
        assert "3" in result  # Should mention 3 tasks
        assert "updated" in result.lower()

        print(f"\n✓ E2E update_tasks batch: {result}")

        # Cleanup
        client.delete_tasks(task_ids)

    def test_update_tasks_single_id_string_e2e(self, client, test_project):
        """E2E: Update single task via batch tool (Union type)."""
        # Create a single task
        task_id = client.create_task("E2E Single Update Task", project_id=test_project)

        # Call MCP tool with single ID wrapped in list
        result = update_tasks(
            tasks=[{"id": task_id, "flagged": False}]
        )

        assert isinstance(result, str)
        assert "updated" in result.lower()

        print(f"\n✓ E2E update_tasks single ID: {result}")

        # Cleanup
        client.delete_tasks(task_id)


class TestDeleteTasksE2E:
    """E2E tests for delete_tasks() MCP tool.

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_delete_tasks_e2e(self, client, test_project):
        """E2E: Delete multiple tasks via MCP tool."""
        # Create disposable test tasks
        task_ids = []
        for i in range(2):
            task_id = client.create_task(f"E2E Delete Test Task {i+1}", project_id=test_project)
            task_ids.append(task_id)

        # Call MCP tool to delete
        result = delete_tasks(task_ids=task_ids)

        assert isinstance(result, str)
        assert "2" in result  # Should mention 2 tasks
        assert "deleted" in result.lower()

        print(f"\n✓ E2E delete_tasks: {result}")

        # No cleanup needed - tasks were deleted by the test

    def test_delete_single_task_e2e(self, client, test_project):
        """E2E: Delete single task via MCP tool (Union type)."""
        # Create a task to delete
        task_id = client.create_task("E2E Single Delete Task", project_id=test_project)

        # Call MCP tool to delete
        result = delete_tasks(task_ids=task_id)  # Single ID as string

        assert isinstance(result, str)
        assert "1" in result  # Should mention 1 task
        assert "deleted" in result.lower()

        print(f"\n✓ E2E delete single task: {result}")

        # No cleanup needed - task was deleted by the test


# ============================================================================
# E2E Tests for update_project() (NEW API - Phase 2)
# ============================================================================

class TestUpdateProjectE2E:
    """E2E tests for update_project() MCP tool with real OmniFocus.

    Tests the full stack:
    MCP tool → client.update_project() → AppleScript → OmniFocus

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_update_project_set_status_e2e(self, test_project):
        """E2E: Set project status via MCP tool."""
        # Import the MCP tool function
        # Call the MCP tool to set status
        result = server.update_project(project_id=test_project, status="on_hold")

        # Verify MCP tool returns human-readable response
        assert isinstance(result, str)
        assert "success" in result.lower() or "updated" in result.lower()
        assert test_project in result or "project" in result.lower()

        print(f"\n✓ E2E update_project status: {result}")

    def test_update_project_review_interval_e2e(self, test_project):
        """E2E: Set review interval via MCP tool."""
        # Call the MCP tool to set review interval
        result = server.update_project(project_id=test_project, review_interval_weeks=3)

        assert isinstance(result, str)
        assert "success" in result.lower() or "updated" in result.lower()

        print(f"\n✓ E2E update_project review interval: {result}")

    def test_update_project_multiple_fields_e2e(self, test_project):
        """E2E: Update multiple fields at once via MCP tool."""
        # Call the MCP tool to update multiple fields
        result = server.update_project(
            project_id=test_project,
            project_name="E2E Updated Project Name",
            status="active",
            review_interval_weeks=2,
            sequential=True
        )

        assert isinstance(result, str)
        assert "success" in result.lower() or "updated" in result.lower()
        # Should mention multiple fields
        assert "4" in result or "fields" in result.lower()

        print(f"\n✓ E2E update_project multiple fields: {result}")

    def test_update_project_error_handling_e2e(self):
        """E2E: Error handling when update fails."""
        # Try to update with invalid project ID
        result = server.update_project(project_id="invalid-id-999", status="active")

        # Should return error message (not raise exception for runtime errors)
        assert isinstance(result, str)
        assert "error" in result.lower() or "failed" in result.lower()

        print(f"\n✓ E2E update_project error handling: {result}")


# ============================================================================
# E2E Tests for update_projects() (NEW API - Phase 2, Function 2.2)
# ============================================================================

class TestUpdateProjectsE2E:
    """E2E tests for update_projects() MCP tool with real OmniFocus.

    Tests the full stack:
    MCP tool → client.update_projects() → AppleScript → OmniFocus

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_update_projects_batch_e2e(self, client):
        """E2E: Update multiple projects via MCP tool."""
        # Create test projects
        proj_id_1 = client.create_project("E2E Batch 1")
        proj_id_2 = client.create_project("E2E Batch 2")

        # Call the MCP tool
        result = server.update_projects(
            projects=[
                {"id": proj_id_1, "status": "on_hold"},
                {"id": proj_id_2, "status": "on_hold"},
            ]
        )

        # Verify MCP tool returns human-readable response
        assert isinstance(result, str)
        assert "2" in result  # Should mention 2 projects
        assert "success" in result.lower() or "updated" in result.lower()

        print(f"\n✓ E2E update_projects batch: {result}")

        # Cleanup
        client.delete_projects([proj_id_1, proj_id_2])

    def test_update_projects_single_id_e2e(self, client):
        """E2E: Update single project ID as string via MCP tool (Union type)."""
        # Create a project
        proj_id = client.create_project("E2E Single ID")

        # Call MCP tool
        result = server.update_projects(projects=[{"id": proj_id, "sequential": True}])

        assert isinstance(result, str)
        assert "1" in result  # Should mention 1 project
        assert "success" in result.lower() or "updated" in result.lower()

        print(f"\n✓ E2E update_projects single ID: {result}")

        # Cleanup
        client.delete_projects(proj_id)


# ============================================================================
# E2E Tests for set_focus() (NEW API - v0.7.0)
# ============================================================================

class TestSetFocusE2E:
    """E2E tests for set_focus() MCP tool with real OmniFocus.

    Tests the full stack:
    MCP tool → client.set_focus() → AppleScript → OmniFocus

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_set_focus_on_project_e2e(self, test_project):
        """E2E: Set focus on a project via MCP tool."""
        # Call the MCP tool
        result = server.set_focus(item_ids=test_project, item_types="project")

        # Verify MCP tool returns human-readable response
        assert isinstance(result, str)
        assert "Focus set on" in result
        assert "project" in result.lower()
        assert test_project in result

        print(f"\n✓ E2E set_focus on project: {result}")

    def test_set_focus_on_folder_e2e(self, test_folder):
        """E2E: Set focus on a folder via MCP tool."""
        # Call the MCP tool
        result = server.set_focus(item_ids=test_folder, item_types="folder")

        # Verify MCP tool returns human-readable response
        assert isinstance(result, str)
        assert "Focus set on" in result
        assert "folder" in result.lower()
        assert test_folder in result

        print(f"\n✓ E2E set_focus on folder: {result}")

    def test_set_focus_invalid_type_e2e(self):
        """E2E: Test error handling for invalid item type via MCP tool."""
        # Call the MCP tool with invalid type
        result = server.set_focus(item_ids="any-id", item_types="task")

        # Verify MCP tool returns error message
        assert isinstance(result, str)
        assert "invalid" in result.lower() or "error" in result.lower()
        assert "task" in result.lower()

        print(f"\n✓ E2E set_focus invalid type: {result}")


# ============================================================================
# E2E Tests for get_tasks() with filters
# ============================================================================

class TestGetTasksE2E:
    """E2E tests for get_tasks() MCP tool with various filters.

    Tests the full stack:
    MCP tool → client.get_tasks() → AppleScript → OmniFocus
    """

    def test_get_tasks_all_e2e(self, client, test_project):
        """E2E: Get all tasks via MCP tool."""
        # Create a task first so we have at least one
        client.create_task("E2E Get Tasks Test", project_id=test_project)
        result = get_tasks()
        assert isinstance(result, str)
        assert "Found" in result
        assert "tasks" in result.lower()

        print(f"\n✓ E2E get_tasks (all): {result[:200]}")

    def test_get_tasks_with_query_e2e(self, client, test_project):
        """E2E: Get tasks with query filter via MCP tool."""
        client.create_task("E2E Unique Query Target XYZ", project_id=test_project)
        result = get_tasks(query="Unique Query Target XYZ")
        assert isinstance(result, str)
        assert "Unique Query Target XYZ" in result

        print(f"\n✓ E2E get_tasks (query): {result[:200]}")

    def test_get_tasks_flagged_e2e(self, client, test_project):
        """E2E: Get flagged tasks via MCP tool."""
        task_id = client.create_task("E2E Flagged Task", project_id=test_project, flagged=True)
        result = get_tasks(flagged_only=True)
        assert isinstance(result, str)
        # Should find at least one flagged task
        assert "Found" in result

        print(f"\n✓ E2E get_tasks (flagged): {result[:200]}")

        client.delete_tasks(task_id)

    def test_get_tasks_inbox_e2e(self):
        """E2E: Get inbox tasks via MCP tool."""
        result = get_tasks(inbox_only=True)
        assert isinstance(result, str)
        # Either finds tasks or says none
        assert "Found" in result or "No tasks in inbox" in result

        print(f"\n✓ E2E get_tasks (inbox): {result[:200]}")


# ============================================================================
# E2E Tests for get_projects()
# ============================================================================

class TestGetProjectsE2E:
    """E2E tests for get_projects() MCP tool.

    Tests the full stack:
    MCP tool → client.get_projects() → AppleScript → OmniFocus
    """

    def test_get_projects_all_e2e(self):
        """E2E: Get all projects via MCP tool."""
        result = get_projects()
        assert isinstance(result, str)
        assert "Found" in result

        print(f"\n✓ E2E get_projects (all): {result[:200]}")

    def test_get_projects_with_query_e2e(self, test_project):
        """E2E: Get projects with query filter via MCP tool."""
        # test_project creates a project with a unique name containing "test-"
        result = get_projects(query="test-")
        assert isinstance(result, str)
        assert "Found" in result

        print(f"\n✓ E2E get_projects (query): {result[:200]}")


# ============================================================================
# E2E Tests for create_project()
# ============================================================================

class TestCreateProjectE2E:
    """E2E tests for create_project() MCP tool.

    Tests the full stack:
    MCP tool → client.create_project() → AppleScript → OmniFocus
    """

    def test_create_project_e2e(self, client):
        """E2E: Create project via MCP tool."""
        result = create_project(name="E2E Test Project Creation")
        assert isinstance(result, str)
        assert "Successfully created" in result
        assert "Project ID:" in result

        # Extract ID and cleanup
        match = re.search(r'Project ID: (\S+)', result)
        if match:
            client.delete_projects(match.group(1))

        print(f"\n✓ E2E create_project: {result}")


# ============================================================================
# E2E Tests for delete_projects()
# ============================================================================

class TestDeleteProjectsE2E:
    """E2E tests for delete_projects() MCP tool.

    Tests the full stack:
    MCP tool → client.delete_projects() → AppleScript → OmniFocus
    """

    def test_delete_projects_e2e(self, client):
        """E2E: Delete project via MCP tool."""
        proj_id = client.create_project("E2E Delete Project Test")
        result = delete_projects(project_ids=proj_id)
        assert isinstance(result, str)
        assert "deleted" in result.lower()

        print(f"\n✓ E2E delete_projects: {result}")


# ============================================================================
# E2E Tests for get_tags()
# ============================================================================

class TestGetTagsE2E:
    """E2E tests for get_tags() MCP tool.

    Tests the full stack:
    MCP tool → client.get_tags() → AppleScript → OmniFocus
    """

    def test_get_tags_e2e(self):
        """E2E: Get all tags via MCP tool."""
        result = get_tags()
        assert isinstance(result, str)
        assert "Found" in result
        assert "tags" in result.lower()

        print(f"\n✓ E2E get_tags: {result[:200]}")


# ============================================================================
# E2E Tests for tag lifecycle (create, update, delete)
# ============================================================================

class TestTagCRUDE2E:
    """E2E tests for tag create/update/delete MCP tools.

    Tests the full stack:
    MCP tool → client methods → AppleScript → OmniFocus
    """

    def test_tag_lifecycle_e2e(self, client):
        """E2E: Full tag lifecycle via MCP tools."""
        # Create
        result = create_tag(name="E2E-Test-Tag-Lifecycle")
        assert isinstance(result, str)
        assert "Successfully" in result

        # Extract tag ID
        match = re.search(r'Tag ID: (\S+)', result)
        assert match, f"Could not find tag ID in: {result}"
        tag_id = match.group(1)

        print(f"\n✓ E2E create_tag: {result}")

        # Update (rename)
        result = update_tag(tag_id=tag_id, name="E2E-Test-Tag-Renamed")
        assert isinstance(result, str)
        assert "Successfully" in result

        print(f"\n✓ E2E update_tag: {result}")

        # Delete
        result = delete_tags(tag_ids=tag_id)
        assert isinstance(result, str)
        assert "deleted" in result.lower()

        print(f"\n✓ E2E delete_tags: {result}")


# ============================================================================
# E2E Tests for folder operations
# ============================================================================

class TestFolderE2E:
    """E2E tests for folder MCP tools.

    Tests the full stack:
    MCP tool → client methods → AppleScript → OmniFocus
    """

    def test_get_folders_e2e(self):
        """E2E: Get all folders via MCP tool."""
        result = get_folders()
        assert isinstance(result, str)
        assert "Found" in result or "folder" in result.lower()

        print(f"\n✓ E2E get_folders: {result[:200]}")

    def test_folder_lifecycle_e2e(self, client):
        """E2E: Create and update folder via MCP tools."""
        # Create
        result = create_folder(name="E2E-Test-Folder")
        assert isinstance(result, str)
        assert "Successfully" in result

        # Extract folder ID
        match = re.search(r'ID: (\S+)', result)
        assert match, f"Could not find folder ID in: {result}"
        folder_id = match.group(1).rstrip(')')

        print(f"\n✓ E2E create_folder: {result}")

        # Update (rename)
        result = update_folder(folder_id=folder_id, name="E2E-Test-Folder-Renamed")
        assert isinstance(result, str)
        assert "Successfully" in result

        print(f"\n✓ E2E update_folder: {result}")

        # Cleanup - drop the folder
        server.update_folder(folder_id=folder_id, status="dropped")


# ============================================================================
# E2E Tests for get_perspectives()
# ============================================================================

class TestPerspectivesE2E:
    """E2E tests for get_perspectives() MCP tool.

    Tests the full stack:
    MCP tool → client.get_perspectives() → AppleScript → OmniFocus
    """

    def test_get_perspectives_e2e(self):
        """E2E: Get perspectives via MCP tool."""
        result = get_perspectives()
        assert isinstance(result, str)
        assert "Found" in result or "perspective" in result.lower()

        print(f"\n✓ E2E get_perspectives: {result[:200]}")


# ============================================================================
# E2E Tests for get_focus()
# ============================================================================

class TestGetFocusE2E:
    """E2E tests for get_focus() MCP tool.

    Tests the full stack:
    MCP tool → client.get_focus() → AppleScript → OmniFocus
    """

    def test_get_focus_e2e(self):
        """E2E: Get current focus via MCP tool."""
        result = get_focus()
        assert isinstance(result, str)
        # Either has focus or doesn't
        assert "focus" in result.lower() or "No focus" in result

        print(f"\n✓ E2E get_focus: {result}")
