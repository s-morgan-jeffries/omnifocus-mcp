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

Run with: make test-e2e
"""
import os
import pytest

# Import the MCP server tools
import omnifocus_mcp.server_fastmcp as server

# Extract tool functions from FunctionTool wrappers
create_task = server.create_task.fn
update_task = server.update_task.fn
update_tasks = server.update_tasks.fn
delete_tasks = server.delete_tasks.fn
get_tasks = server.get_tasks.fn

# Skip all tests unless in test mode
pytestmark = pytest.mark.skipif(
    os.environ.get('OMNIFOCUS_TEST_MODE', '').lower() != 'true',
    reason="E2E tests require OMNIFOCUS_TEST_MODE=true. Run with: make test-e2e"
)


class TestCreateTaskE2E:
    """E2E tests for create_task() MCP tool with real OmniFocus.

    Tests the full stack:
    MCP tool → client.create_task() → AppleScript → OmniFocus
    """

    @pytest.fixture(scope="class")
    def test_project_id(self):
        """Get a test project ID for E2E tests."""
        # Get projects to find a test project
        result = server.get_projects.fn()
        # Parse the response (it's a formatted string from MCP tool)
        # For now, we'll use the client directly to get a project ID
        from omnifocus_mcp.omnifocus_connector import OmniFocusConnector
        client = OmniFocusConnector(enable_safety_checks=True)
        projects = client.get_projects()
        if not projects:
            pytest.skip("No projects found in test database")
        return projects[0]['id']

    def test_create_task_in_project_e2e(self, test_project_id):
        """E2E: Create task in project via MCP tool."""
        # Call the MCP tool (not the client directly)
        result = create_task(
            task_name="E2E Test Task - Project",
            project_id=test_project_id,
            note="Created by E2E test",
            flagged=True
        )

        # Verify MCP tool returns human-readable response
        assert isinstance(result, str)
        assert "E2E Test Task - Project" in result
        assert test_project_id in result
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

    def test_create_task_with_tags_e2e(self, test_project_id):
        """E2E: Create task with tags via MCP tool (tests JSON string conversion)."""
        # MCP tools receive tags as JSON string
        result = create_task(
            task_name="E2E Test Task - Tags",
            project_id=test_project_id,
            tags='["Test"]'  # JSON string, not Python list!
        )

        assert isinstance(result, str)
        assert "E2E Test Task - Tags" in result
        assert "Successfully created" in result
        # Tags might be in response
        if "Tags:" in result:
            assert "Test" in result

        print(f"\n✓ E2E create_task with tags: {result}")

    def test_create_task_with_dates_e2e(self, test_project_id):
        """E2E: Create task with dates via MCP tool."""
        result = create_task(
            task_name="E2E Test Task - Dates",
            project_id=test_project_id,
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
        """E2E: Verify MCP tool raises ValueError for invalid parameters."""
        # Try to create with both project_id and parent_task_id (invalid)
        # This should raise ValueError (proper MCP behavior for validation errors)
        with pytest.raises(ValueError) as exc_info:
            create_task(
                task_name="Bad Task",
                project_id="proj-123",
                parent_task_id="task-456"
            )

        # Verify error message is informative
        assert "project_id" in str(exc_info.value).lower() or "parent" in str(exc_info.value).lower()

        print(f"\n✓ E2E create_task error handling: Correctly raised ValueError")


class TestUpdateTaskE2E:
    """E2E tests for update_task() MCP tool with real OmniFocus."""

    @pytest.fixture
    def test_task_id(self, test_project_id):
        """Create a test task and return its ID."""
        result = create_task(
            task_name="E2E Test Task for Updates",
            project_id=test_project_id
        )
        # Extract task ID from response
        # Response format: "Successfully created task '...' in project ...\nTask ID: <id>"
        import re
        match = re.search(r'Task ID: ([^\s]+)', result)
        if match:
            return match.group(1)
        pytest.fail(f"Could not extract task ID from: {result}")

    @pytest.fixture(scope="class")
    def test_project_id(self):
        """Get a test project ID."""
        from omnifocus_mcp.omnifocus_connector import OmniFocusConnector
        client = OmniFocusConnector(enable_safety_checks=True)
        projects = client.get_projects()
        if not projects:
            pytest.skip("No projects found")
        return projects[0]['id']

    def test_update_task_single_field_e2e(self, test_task_id):
        """E2E: Update single field via MCP tool."""
        result = update_task(
            task_id=test_task_id,
            flagged=True
        )

        assert isinstance(result, str)
        assert "Successfully updated" in result or "success" in result.lower()

        print(f"\n✓ E2E update_task single field: {result}")

    def test_update_task_multiple_fields_e2e(self, test_task_id):
        """E2E: Update multiple fields via MCP tool."""
        result = update_task(
            task_id=test_task_id,
            task_name="E2E Updated Task Name",
            flagged=False,
            note="Updated by E2E test"
        )

        assert isinstance(result, str)
        assert "Successfully updated" in result or "success" in result.lower()

        print(f"\n✓ E2E update_task multiple fields: {result}")


class TestUpdateTasksE2E:
    """E2E tests for update_tasks() batch MCP tool."""

    @pytest.fixture
    def test_task_ids(self, test_project_id):
        """Create multiple test tasks."""
        ids = []
        for i in range(3):
            result = create_task(
                task_name=f"E2E Batch Test Task {i+1}",
                project_id=test_project_id
            )
            import re
            match = re.search(r'Task ID: ([^\s]+)', result)
            if match:
                ids.append(match.group(1))
        return ids

    @pytest.fixture(scope="class")
    def test_project_id(self):
        """Get a test project ID."""
        from omnifocus_mcp.omnifocus_connector import OmniFocusConnector
        client = OmniFocusConnector(enable_safety_checks=True)
        projects = client.get_projects()
        if not projects:
            pytest.skip("No projects found")
        return projects[0]['id']

    def test_update_tasks_batch_e2e(self, test_task_ids):
        """E2E: Update multiple tasks via MCP tool."""
        result = update_tasks(
            task_ids=test_task_ids,
            flagged=True
        )

        assert isinstance(result, str)
        assert "3" in result  # Should mention 3 tasks
        assert "updated" in result.lower()

        print(f"\n✓ E2E update_tasks batch: {result}")

    def test_update_tasks_single_id_string_e2e(self, test_task_ids):
        """E2E: Update single task via batch tool (Union type)."""
        result = update_tasks(
            task_ids=test_task_ids[0],  # Single ID as string
            flagged=False
        )

        assert isinstance(result, str)
        assert "1" in result  # Should mention 1 task
        assert "updated" in result.lower()

        print(f"\n✓ E2E update_tasks single ID: {result}")


class TestDeleteTasksE2E:
    """E2E tests for delete_tasks() MCP tool."""

    @pytest.fixture
    def test_task_ids(self, test_project_id):
        """Create disposable test tasks."""
        ids = []
        for i in range(2):
            result = create_task(
                task_name=f"E2E Delete Test Task {i+1}",
                project_id=test_project_id
            )
            import re
            match = re.search(r'Task ID: ([^\s]+)', result)
            if match:
                ids.append(match.group(1))
        return ids

    @pytest.fixture(scope="class")
    def test_project_id(self):
        """Get a test project ID."""
        from omnifocus_mcp.omnifocus_connector import OmniFocusConnector
        client = OmniFocusConnector(enable_safety_checks=True)
        projects = client.get_projects()
        if not projects:
            pytest.skip("No projects found")
        return projects[0]['id']

    def test_delete_tasks_e2e(self, test_task_ids):
        """E2E: Delete multiple tasks via MCP tool."""
        result = delete_tasks(task_ids=test_task_ids)

        assert isinstance(result, str)
        assert "2" in result  # Should mention 2 tasks
        assert "deleted" in result.lower()

        print(f"\n✓ E2E delete_tasks: {result}")

    def test_delete_single_task_e2e(self, test_project_id):
        """E2E: Delete single task via MCP tool (Union type)."""
        # Create a task to delete
        create_result = create_task(
            task_name="E2E Single Delete Task",
            project_id=test_project_id
        )
        import re
        match = re.search(r'Task ID: ([^\s]+)', create_result)
        task_id = match.group(1)

        # Delete it
        result = delete_tasks(task_ids=task_id)  # Single ID as string

        assert isinstance(result, str)
        assert "1" in result  # Should mention 1 task
        assert "deleted" in result.lower()

        print(f"\n✓ E2E delete single task: {result}")


# ============================================================================
# E2E Tests for update_project() (NEW API - Phase 2)
# ============================================================================

class TestUpdateProjectE2E:
    """E2E tests for update_project() MCP tool with real OmniFocus.

    Tests the full stack:
    MCP tool → client.update_project() → AppleScript → OmniFocus
    """

    @pytest.fixture
    def test_project_id(self):
        """Create a test project for E2E tests."""
        from omnifocus_mcp.omnifocus_connector import OmniFocusConnector
        client = OmniFocusConnector(enable_safety_checks=True)
        project_id = client.create_project("E2E Test Project - update_project")
        yield project_id
        # Cleanup not needed - test database is reset regularly

    def test_update_project_set_status_e2e(self, test_project_id):
        """E2E: Set project status via MCP tool."""
        # Import the MCP tool function
        import omnifocus_mcp.server_fastmcp as server
        update_project = server.update_project.fn

        # Call the MCP tool to set status
        result = update_project(project_id=test_project_id, status="on_hold")

        # Verify MCP tool returns human-readable response
        assert isinstance(result, str)
        assert "success" in result.lower() or "updated" in result.lower()
        assert test_project_id in result or "project" in result.lower()

        print(f"\n✓ E2E update_project status: {result}")

    def test_update_project_review_interval_e2e(self, test_project_id):
        """E2E: Set review interval via MCP tool."""
        import omnifocus_mcp.server_fastmcp as server
        update_project = server.update_project.fn

        # Call the MCP tool to set review interval
        result = update_project(project_id=test_project_id, review_interval_weeks=3)

        assert isinstance(result, str)
        assert "success" in result.lower() or "updated" in result.lower()

        print(f"\n✓ E2E update_project review interval: {result}")

    def test_update_project_multiple_fields_e2e(self, test_project_id):
        """E2E: Update multiple fields at once via MCP tool."""
        import omnifocus_mcp.server_fastmcp as server
        update_project = server.update_project.fn

        # Call the MCP tool to update multiple fields
        result = update_project(
            project_id=test_project_id,
            project_name="E2E Updated Project Name",
            status="active",
            review_interval_weeks=2,
            sequential="true"
        )

        assert isinstance(result, str)
        assert "success" in result.lower() or "updated" in result.lower()
        # Should mention multiple fields
        assert "4" in result or "fields" in result.lower()

        print(f"\n✓ E2E update_project multiple fields: {result}")

    def test_update_project_error_handling_e2e(self, test_project_id):
        """E2E: Error handling when update fails."""
        import omnifocus_mcp.server_fastmcp as server
        update_project = server.update_project.fn

        # Try to update with invalid status
        result = update_project(project_id="invalid-id-999", status="active")

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
    """

    def test_update_projects_batch_e2e(self):
        """E2E: Update multiple projects via MCP tool."""
        from omnifocus_mcp.omnifocus_connector import OmniFocusConnector
        import omnifocus_mcp.server_fastmcp as server

        # Create test projects
        client = OmniFocusConnector(enable_safety_checks=True)
        proj_id_1 = client.create_project("E2E Batch 1")
        proj_id_2 = client.create_project("E2E Batch 2")

        # Call the MCP tool
        update_projects = server.update_projects.fn
        result = update_projects(
            project_ids=[proj_id_1, proj_id_2],
            status="on_hold"
        )

        # Verify MCP tool returns human-readable response
        assert isinstance(result, str)
        assert "2" in result  # Should mention 2 projects
        assert "success" in result.lower() or "updated" in result.lower()

        print(f"\n✓ E2E update_projects batch: {result}")

    def test_update_projects_single_id_e2e(self):
        """E2E: Update single project ID as string via MCP tool (Union type)."""
        from omnifocus_mcp.omnifocus_connector import OmniFocusConnector
        import omnifocus_mcp.server_fastmcp as server

        client = OmniFocusConnector(enable_safety_checks=True)
        proj_id = client.create_project("E2E Single ID")

        update_projects = server.update_projects.fn
        result = update_projects(project_ids=proj_id, sequential="true")

        assert isinstance(result, str)
        assert "1" in result  # Should mention 1 project
        assert "success" in result.lower() or "updated" in result.lower()

        print(f"\n✓ E2E update_projects single ID: {result}")
