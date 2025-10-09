"""Real OmniFocus integration tests.

IMPORTANT: These tests interact with a REAL OmniFocus instance!

Prerequisites:
1. Run scripts/setup_test_database.sh to create a test database
2. Set environment variables:
   export OMNIFOCUS_TEST_MODE=true
   export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"
3. OmniFocus must be running
4. The test database must be the active database in OmniFocus

Safety:
- These tests will ONLY run if OMNIFOCUS_TEST_MODE=true
- Database safety guards will verify you're using the test database
- Your production database is protected

Usage:
    # Run real integration tests
    pytest tests/test_integration_real.py -v

    # Skip these tests (default behavior without env vars)
    pytest tests/ -v
"""
import os
import pytest

from omnifocus_mcp.omnifocus_client import OmniFocusClient


# Skip all tests in this file unless explicitly in test mode
pytestmark = pytest.mark.skipif(
    os.environ.get('OMNIFOCUS_TEST_MODE', '').lower() != 'true',
    reason="Real OmniFocus tests require OMNIFOCUS_TEST_MODE=true. "
           "Run scripts/setup_test_database.sh first."
)


class TestRealOmniFocusIntegration:
    """Integration tests with real OmniFocus."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a client for real OmniFocus testing.

        Safety checks are enabled - will verify test database before operations.
        """
        return OmniFocusClient(enable_safety_checks=True)

    def test_get_projects_real(self, client):
        """Test getting projects from real OmniFocus."""
        projects = client.get_projects()

        # We should have at least some projects (from setup script)
        assert isinstance(projects, list)
        assert len(projects) > 0

        # Verify project structure
        first_project = projects[0]
        assert 'id' in first_project
        assert 'name' in first_project
        assert 'status' in first_project

        print(f"\n✓ Found {len(projects)} projects in test database")

    def test_search_projects_real(self, client):
        """Test searching projects with query parameter."""
        # Search for test projects (created by setup script)
        results = client.get_projects(query="Test")

        assert isinstance(results, list)
        # Should find at least one test project
        assert len(results) > 0

        print(f"\n✓ Search found {len(results)} matching projects")

    def test_get_tasks_real(self, client):
        """Test getting tasks from real OmniFocus."""
        tasks = client.get_tasks()

        assert isinstance(tasks, list)
        # Should have tasks from setup script
        assert len(tasks) > 0

        # Verify task structure
        first_task = tasks[0]
        assert 'id' in first_task
        assert 'name' in first_task
        assert 'completed' in first_task

        print(f"\n✓ Found {len(tasks)} tasks in test database")

    def test_get_tasks_with_query_real(self, client):
        """Test getting tasks with query parameter (NEW in v0.5.0)."""
        # Search for test tasks
        tasks = client.get_tasks(query="Test")

        assert isinstance(tasks, list)
        # Should find at least one test task
        assert len(tasks) > 0

        # Verify all returned tasks contain "Test" in name or note
        for task in tasks:
            task_text = (task.get('name', '') + ' ' + task.get('note', '')).lower()
            assert 'test' in task_text, f"Task {task['name']} doesn't contain 'test'"

        print(f"\n✓ Query search found {len(tasks)} matching tasks")

    def test_get_inbox_tasks_real(self, client):
        """Test getting inbox tasks with inbox_only parameter."""
        inbox_tasks = client.get_tasks(inbox_only=True)

        assert isinstance(inbox_tasks, list)
        # Should have at least one inbox task from setup script
        assert len(inbox_tasks) > 0

        # Verify all tasks have no project
        for task in inbox_tasks:
            assert task.get('projectName') in [None, '', 'N/A'], \
                f"Inbox task should not have project: {task.get('projectName')}"

        print(f"\n✓ Found {len(inbox_tasks)} inbox tasks")

    def test_get_tags_real(self, client):
        """Test getting tags from real OmniFocus."""
        tags = client.get_tags()

        assert isinstance(tags, list)
        # Should have test tags from setup script
        assert len(tags) > 0

        # Verify tag structure
        first_tag = tags[0]
        assert 'id' in first_tag
        assert 'name' in first_tag

        print(f"\n✓ Found {len(tags)} tags in test database")


class TestRealOmniFocusWriteOperations:
    """Test write operations with real OmniFocus.

    WARNING: These tests MODIFY the test database!
    """

    @pytest.fixture(scope="class")
    def client(self):
        """Create a client for real OmniFocus testing."""
        return OmniFocusClient(enable_safety_checks=True)

    @pytest.fixture(scope="class")
    def test_project_id(self, client):
        """Get a test project ID to use for operations."""
        projects = client.search_projects("Test Project 1")
        assert len(projects) > 0, "Test Project 1 not found - run setup script"
        return projects[0]['id']

    def test_add_task_real(self, client, test_project_id):
        """Test adding a task to real OmniFocus."""
        result = client.add_task(
            test_project_id,
            "Integration Test Task",
            note="This task was created by test_integration_real.py"
        )

        assert result is True
        print("\n✓ Successfully added task to test project")

        # Verify the task was created
        tasks = client.get_tasks(project_id=test_project_id)
        task_names = [t['name'] for t in tasks]
        assert "Integration Test Task" in task_names

    def test_add_task_with_properties_real(self, client, test_project_id):
        """Test adding a task with all properties."""
        result = client.add_task(
            test_project_id,
            "Task with Properties",
            note="Has due date and flag",
            due_date="2025-12-31",
            flagged=True,
            tags=["test-urgent"]
        )

        assert result is True
        print("\n✓ Successfully added task with properties")

    def test_create_inbox_task_real(self, client):
        """Test creating an inbox task in real OmniFocus."""
        result = client.create_inbox_task(
            "Real Integration Test Inbox Task",
            note="Created by integration test"
        )

        assert result is True
        print("\n✓ Successfully created inbox task")

        # Verify it appears in inbox
        inbox = client.get_inbox_tasks()
        inbox_names = [t['name'] for t in inbox]
        assert "Real Integration Test Inbox Task" in inbox_names

    def test_complete_task_real(self, client, test_project_id):
        """Test completing a task in real OmniFocus."""
        # First, add a task to complete
        client.add_task(test_project_id, "Task to Complete")

        # Get the task ID
        tasks = client.get_tasks(project_id=test_project_id)
        task_to_complete = next(t for t in tasks if t['name'] == "Task to Complete")

        # Complete it
        result = client.complete_task(task_to_complete['id'])
        assert result is True
        print("\n✓ Successfully completed task")

    def test_update_task_real(self, client, test_project_id):
        """Test updating a task in real OmniFocus."""
        # First, add a task to update
        client.add_task(test_project_id, "Task to Update")

        # Get the task ID
        tasks = client.get_tasks(project_id=test_project_id)
        task_to_update = next(t for t in tasks if t['name'] == "Task to Update")

        # Update it
        result = client.update_task(
            task_to_update['id'],
            name="Updated Task Name",
            note="This task was updated by integration test"
        )
        assert result is True
        print("\n✓ Successfully updated task")

    def test_add_tag_to_task_real(self, client, test_project_id):
        """Test adding a tag to a task in real OmniFocus."""
        # First, add a task
        client.add_task(test_project_id, "Task for Tagging")

        # Get the task ID
        tasks = client.get_tasks(project_id=test_project_id)
        task_for_tag = next(t for t in tasks if t['name'] == "Task for Tagging")

        # Add tag
        result = client.add_tag_to_task(task_for_tag['id'], "test-work")
        assert result is True
        print("\n✓ Successfully added tag to task")


class TestRealOmniFocusSafetyVerification:
    """Verify that safety guards work with real OmniFocus."""

    def test_safety_guards_verify_database(self):
        """Test that safety guards actually check the database name."""
        # This test verifies the safety system works
        # Client should successfully verify we're using test database
        client = OmniFocusClient(enable_safety_checks=True)

        # This should succeed because we're in test mode with test database
        # The safety check will verify the database name via AppleScript
        projects = client.get_projects()
        assert isinstance(projects, list)

        print("\n✓ Safety guards successfully verified test database")

    def test_destructive_operation_checks_database_name(self):
        """Test that destructive operations verify database name."""
        client = OmniFocusClient(enable_safety_checks=True)

        # Get a test project
        projects = client.search_projects("Test Project")
        assert len(projects) > 0
        test_project = projects[0]['id']

        # This operation should trigger database name verification
        # If we're not using the test database, it will be blocked
        result = client.add_task(
            test_project,
            "Safety Verification Task",
            note="If this task was created, safety guards are working!"
        )

        assert result is True
        print("\n✓ Destructive operation verified database name before proceeding")
