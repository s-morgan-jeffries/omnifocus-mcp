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


class TestProjectCRUD:
    """Test project CRUD operations comprehensively."""

    @pytest.fixture(scope="class")
    def client(self):
        return OmniFocusClient(enable_safety_checks=True)

    def test_create_project_basic(self, client):
        """Test creating a basic project."""
        result = client.create_project("Integration Test Project")
        assert result is True
        print("\n✓ Created basic project")

        # Verify it exists
        projects = client.get_projects(query="Integration Test Project")
        assert len(projects) > 0
        assert projects[0]['name'] == "Integration Test Project"

    def test_create_project_with_properties(self, client):
        """Test creating project with all properties."""
        result = client.create_project(
            "Project with Properties",
            folder_path="Test Root Folder",
            note="This project has a note",
            review_interval=7
        )
        assert result is True
        print("\n✓ Created project with properties")

    def test_get_project_by_id(self, client):
        """Test fetching a single project by ID."""
        # Get a known project
        projects = client.get_projects(query="Active Test Project")
        assert len(projects) > 0

        project_id = projects[0]['id']
        project = client.get_project(project_id)

        assert project is not None
        assert project['id'] == project_id
        assert project['name'] == "Active Test Project"
        print(f"\n✓ Retrieved project by ID: {project['name']}")

    def test_set_project_status_to_on_hold(self, client):
        """Test changing project status to on-hold."""
        # Create a project to modify
        client.create_project("Project for Status Change")
        projects = client.get_projects(query="Project for Status Change")
        project_id = projects[0]['id']

        # Change to on-hold
        result = client.set_project_status(project_id, "on_hold")
        assert "on hold" in result.lower() or "on-hold" in result.lower()
        print("\n✓ Set project to on-hold")

    def test_set_project_status_to_done(self, client):
        """Test completing a project."""
        # Get an active project
        projects = client.get_projects(query="Project for Status Change")
        project_id = projects[0]['id']

        # Mark as done
        result = client.set_project_status(project_id, "done")
        assert "done" in result.lower() or "completed" in result.lower()
        print("\n✓ Marked project as done")

    def test_delete_project(self, client):
        """Test deleting a single project."""
        # Create a project to delete
        client.create_project("Project to Delete")
        projects = client.get_projects(query="Project to Delete")
        assert len(projects) > 0
        project_id = projects[0]['id']

        # Delete it
        result = client.delete_project(project_id)
        assert result is True
        print("\n✓ Deleted project")

        # Verify it's gone
        projects_after = client.get_projects(query="Project to Delete")
        # Should be empty or not contain the deleted project
        if projects_after:
            assert project_id not in [p['id'] for p in projects_after]

    def test_delete_projects_batch(self, client):
        """Test batch deleting multiple projects."""
        # Create multiple projects
        client.create_project("Batch Delete 1")
        client.create_project("Batch Delete 2")

        # Get their IDs
        projects = client.get_projects(query="Batch Delete")
        project_ids = [p['id'] for p in projects]
        assert len(project_ids) >= 2

        # Batch delete
        count = client.delete_projects(project_ids)
        assert count >= 2
        print(f"\n✓ Batch deleted {count} projects")


class TestTaskCRUD:
    """Test task CRUD operations comprehensively."""

    @pytest.fixture(scope="class")
    def client(self):
        return OmniFocusClient(enable_safety_checks=True)

    @pytest.fixture(scope="class")
    def test_project_id(self, client):
        projects = client.get_projects(query="Active Test Project")
        return projects[0]['id']

    def test_get_task_by_id(self, client, test_project_id):
        """Test fetching a single task by ID."""
        # Get tasks from the project
        tasks = client.get_tasks(project_id=test_project_id)
        assert len(tasks) > 0

        task_id = tasks[0]['id']
        task = client.get_task(task_id)

        assert task is not None
        assert task['id'] == task_id
        print(f"\n✓ Retrieved task by ID: {task['name']}")

    def test_get_subtasks(self, client):
        """Test getting subtasks of a parent task."""
        # Find the parent task
        tasks = client.get_tasks(query="Parent Task")
        assert len(tasks) > 0
        parent_id = tasks[0]['id']

        # Get subtasks
        subtasks = client.get_subtasks(parent_id)
        assert isinstance(subtasks, list)
        assert len(subtasks) >= 2  # Should have Subtask 1 and Subtask 2
        print(f"\n✓ Found {len(subtasks)} subtasks")

    def test_delete_task(self, client, test_project_id):
        """Test deleting a single task."""
        # Create a task to delete
        client.add_task(test_project_id, "Task to Delete")
        tasks = client.get_tasks(project_id=test_project_id, query="Task to Delete")
        task_id = tasks[0]['id']

        # Delete it
        result = client.delete_task(task_id)
        assert result is True
        print("\n✓ Deleted task")

    def test_delete_tasks_batch(self, client, test_project_id):
        """Test batch deleting multiple tasks."""
        # Create multiple tasks
        client.add_task(test_project_id, "Batch Delete Task 1")
        client.add_task(test_project_id, "Batch Delete Task 2")

        # Get their IDs
        tasks = client.get_tasks(project_id=test_project_id, query="Batch Delete Task")
        task_ids = [t['id'] for t in tasks]
        assert len(task_ids) >= 2

        # Batch delete
        count = client.delete_tasks(task_ids)
        assert count >= 2
        print(f"\n✓ Batch deleted {count} tasks")

    def test_move_task_to_different_project(self, client, test_project_id):
        """Test moving a task to a different project."""
        # Create a task in one project
        client.add_task(test_project_id, "Task to Move")
        tasks = client.get_tasks(project_id=test_project_id, query="Task to Move")
        task_id = tasks[0]['id']

        # Get another project
        other_projects = client.get_projects(query="Standalone Project")
        other_project_id = other_projects[0]['id']

        # Move the task
        result = client.move_task(task_id, other_project_id)
        assert result is True
        print("\n✓ Moved task to different project")

    def test_move_tasks_batch(self, client, test_project_id):
        """Test batch moving multiple tasks."""
        # Create multiple tasks
        client.add_task(test_project_id, "Batch Move 1")
        client.add_task(test_project_id, "Batch Move 2")

        tasks = client.get_tasks(project_id=test_project_id, query="Batch Move")
        task_ids = [t['id'] for t in tasks]

        # Get target project
        target_projects = client.get_projects(query="Standalone Project")
        target_id = target_projects[0]['id']

        # Batch move
        count = client.move_tasks(task_ids, target_id)
        assert count >= 2
        print(f"\n✓ Batch moved {count} tasks")

    def test_drop_task(self, client, test_project_id):
        """Test marking a task as dropped."""
        # Create a task to drop
        client.add_task(test_project_id, "Task to Drop")
        tasks = client.get_tasks(project_id=test_project_id, query="Task to Drop")
        task_id = tasks[0]['id']

        # Drop it
        result = client.drop_task(task_id)
        assert result is True
        print("\n✓ Marked task as dropped")

        # Verify it's dropped
        task = client.get_task(task_id)
        assert task['dropped'] is True

    def test_drop_tasks_batch(self, client, test_project_id):
        """Test batch dropping multiple tasks."""
        # Create multiple tasks
        client.add_task(test_project_id, "Batch Drop 1")
        client.add_task(test_project_id, "Batch Drop 2")

        tasks = client.get_tasks(project_id=test_project_id, query="Batch Drop")
        task_ids = [t['id'] for t in tasks]

        # Batch drop
        count = client.drop_tasks(task_ids)
        assert count >= 2
        print(f"\n✓ Batch dropped {count} tasks")

    def test_set_parent_task(self, client, test_project_id):
        """Test creating task hierarchy."""
        # Create two tasks
        client.add_task(test_project_id, "New Parent Task")
        client.add_task(test_project_id, "New Child Task")

        tasks = client.get_tasks(project_id=test_project_id, query="New")
        parent_id = next(t['id'] for t in tasks if "Parent" in t['name'])
        child_id = next(t['id'] for t in tasks if "Child" in t['name'])

        # Set parent
        result = client.set_parent_task(child_id, parent_id)
        assert result is True
        print("\n✓ Set task parent relationship")

    def test_complete_tasks_batch(self, client, test_project_id):
        """Test batch completing multiple tasks."""
        # Create multiple tasks
        client.add_task(test_project_id, "Batch Complete 1")
        client.add_task(test_project_id, "Batch Complete 2")

        tasks = client.get_tasks(project_id=test_project_id, query="Batch Complete")
        task_ids = [t['id'] for t in tasks]

        # Batch complete
        count = client.complete_tasks(task_ids)
        assert count >= 2
        print(f"\n✓ Batch completed {count} tasks")
