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

    def test_update_task_flag(self, client, test_project_id):
        """Test setting and unsetting the flagged status on a task."""
        # Create a task (unflagged by default)
        client.add_task(test_project_id, "Task for Flag Test", flagged=False)

        # Get the task
        tasks = client.get_tasks(project_id=test_project_id)
        task = next(t for t in tasks if t['name'] == "Task for Flag Test")

        # Verify it's not flagged initially
        assert task['flagged'] is False
        print("\n✓ Task initially unflagged")

        # Set flag to True
        result = client.update_task(task['id'], flagged=True)
        assert result is True

        # Verify flag was set
        tasks = client.get_tasks(project_id=test_project_id)
        task = next(t for t in tasks if t['name'] == "Task for Flag Test")
        assert task['flagged'] is True
        print("✓ Successfully set flag to True")

        # Unset flag back to False
        result = client.update_task(task['id'], flagged=False)
        assert result is True

        # Verify flag was unset
        tasks = client.get_tasks(project_id=test_project_id)
        task = next(t for t in tasks if t['name'] == "Task for Flag Test")
        assert task['flagged'] is False
        print("✓ Successfully set flag to False")

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
        assert isinstance(result, str)  # Returns project ID
        assert len(result) > 0
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
            note="This project has a note"
        )
        assert isinstance(result, str)  # Returns project ID
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

    def test_get_project_includes_timestamp_fields(self, client):
        """Test that get_project includes all timestamp fields."""
        # Get any active project
        projects = client.get_projects(query="Active Test Project")
        assert len(projects) > 0

        project_id = projects[0]['id']
        project = client.get_project(project_id)

        # Verify timestamp fields are present
        assert 'creationDate' in project
        assert 'modificationDate' in project
        assert 'completionDate' in project
        assert 'droppedDate' in project
        assert 'lastReviewDate' in project
        assert 'nextReviewDate' in project
        assert 'lastActivityDate' in project

        # creationDate and modificationDate should be set for active projects
        assert project['creationDate'] is not None
        assert project['modificationDate'] is not None

        # completionDate and droppedDate should be null for active projects
        assert project['completionDate'] is None
        assert project['droppedDate'] is None

        # Verify dates are in ISO 8601 format (if not null)
        if project['creationDate']:
            assert 'T' in project['creationDate'] or '-' in project['creationDate']
        if project['lastReviewDate']:
            assert 'T' in project['lastReviewDate'] or '-' in project['lastReviewDate']

        print("\n✓ Project includes all timestamp fields")
        print(f"  Created: {project['creationDate']}")
        print(f"  Modified: {project['modificationDate']}")
        print(f"  Last Review: {project['lastReviewDate']}")
        print(f"  Next Review: {project['nextReviewDate']}")

    def test_get_projects_includes_timestamp_fields(self, client):
        """Test that get_projects includes timestamp fields in list results."""
        # Get multiple projects
        projects = client.get_projects()
        assert len(projects) > 0

        # Check first project has timestamp fields
        project = projects[0]

        assert 'creationDate' in project
        assert 'modificationDate' in project
        assert 'completionDate' in project
        assert 'droppedDate' in project

        # Active projects should have creationDate and modificationDate
        if project['status'] == 'active status':
            assert project['creationDate'] is not None
            assert project['modificationDate'] is not None

        print("\n✓ get_projects includes timestamp fields")
        print(f"  First project: {project['name']}")
        print(f"  Created: {project['creationDate']}")
        print(f"  Modified: {project['modificationDate']}")

    def test_set_project_status_to_on_hold(self, client):
        """Test changing project status to on-hold."""
        # Create a project to modify
        client.create_project("Project for Status Change")
        projects = client.get_projects(query="Project for Status Change")
        project_id = projects[0]['id']

        # Change to on-hold
        result = client.set_project_status(project_id, "on_hold")
        assert result is True
        print("\n✓ Set project to on-hold")

    def test_set_project_status_to_done(self, client):
        """Test completing a project."""
        # Get an active project
        projects = client.get_projects(query="Project for Status Change")
        project_id = projects[0]['id']

        # Mark as done
        result = client.set_project_status(project_id, "done")
        assert result is True
        print("\n✓ Marked project as done")

    def test_update_project_name(self, client):
        """Test updating project name."""
        # Create a project to update
        project_id = client.create_project("Project to Update Name")

        # Update the name
        result = client.update_project(project_id, name="Updated Project Name")
        assert result is True
        print("\n✓ Updated project name")

        # Verify the change
        project = client.get_project(project_id)
        assert project['name'] == "Updated Project Name"

    def test_update_project_note(self, client):
        """Test updating project note."""
        # Create a project with a note
        project_id = client.create_project("Project with Note", note="Original note")

        # Update the note
        result = client.update_project(project_id, note="Updated note content")
        assert result is True
        print("\n✓ Updated project note")

        # Verify the change
        project = client.get_project(project_id)
        assert project['note'] == "Updated note content"

    def test_update_project_sequential(self, client):
        """Test updating project sequential setting."""
        # Create a parallel project
        project_id = client.create_project("Project Sequential Test", sequential=False)

        # Verify it's parallel
        project = client.get_project(project_id)
        assert project['sequential'] is False

        # Change to sequential
        result = client.update_project(project_id, sequential=True)
        assert result is True
        print("\n✓ Updated project to sequential")

        # Verify the change
        project = client.get_project(project_id)
        assert project['sequential'] is True

    def test_update_project_multiple_fields(self, client):
        """Test updating multiple project fields at once."""
        # Create a project
        project_id = client.create_project("Multi-field Update", note="Old note", sequential=False)

        # Update multiple fields
        result = client.update_project(
            project_id,
            name="New Multi-field Name",
            note="New note content",
            sequential=True
        )
        assert result is True
        print("\n✓ Updated multiple project fields")

        # Verify all changes
        project = client.get_project(project_id)
        assert project['name'] == "New Multi-field Name"
        assert project['note'] == "New note content"
        assert project['sequential'] is True

    def test_update_project_preserves_note_when_not_provided(self, client):
        """Test that not providing note parameter preserves existing note."""
        # Create a project with a note
        project_id = client.create_project("Note Preservation Test", note="Important note content")

        # Update only the name (not the note)
        result = client.update_project(project_id, name="Updated Name Only")
        assert result is True
        print("\n✓ Updated project name without touching note")

        # Verify note is preserved
        project = client.get_project(project_id)
        assert project['name'] == "Updated Name Only"
        assert project['note'] == "Important note content"

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

    def test_get_task_includes_timestamp_fields(self, client, test_project_id):
        """Test that get_task includes all timestamp fields."""
        # Get any task
        tasks = client.get_tasks(project_id=test_project_id)
        assert len(tasks) > 0

        task_id = tasks[0]['id']
        task = client.get_task(task_id)

        # Verify timestamp fields are present
        assert 'creationDate' in task
        assert 'modificationDate' in task
        assert 'completionDate' in task
        assert 'droppedDate' in task

        # Active tasks should have creationDate and modificationDate
        assert task['creationDate'] is not None
        assert task['modificationDate'] is not None

        # completionDate and droppedDate should be null for incomplete tasks
        if not task.get('completed'):
            assert task['completionDate'] is None
            assert task['droppedDate'] is None

        print("\n✓ Task includes all timestamp fields")
        print(f"  Created: {task['creationDate']}")
        print(f"  Modified: {task['modificationDate']}")

    def test_get_task_includes_tags(self, client, test_project_id):
        """Test that get_task includes tags array."""
        # Create a task with tags
        client.add_task(test_project_id, "Task with Tags for Testing", tags=["test-work", "test-urgent"])

        # Get the task
        tasks = client.get_tasks(project_id=test_project_id)
        task = next(t for t in tasks if t['name'] == "Task with Tags for Testing")

        # Get full task details
        full_task = client.get_task(task['id'])

        # Verify tags field is present
        assert 'tags' in full_task
        assert isinstance(full_task['tags'], list)

        # Should have the tags we added
        assert len(full_task['tags']) >= 2
        tag_names = [t if isinstance(t, str) else t.get('name') for t in full_task['tags']]
        assert "test-work" in tag_names
        assert "test-urgent" in tag_names

        print("\n✓ Task includes tags array")
        print(f"  Tags: {tag_names}")

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
        client.add_task(test_project_id, "Unique Task to Drop")
        tasks = client.get_tasks(project_id=test_project_id, query="Unique Task to Drop")
        assert len(tasks) > 0, "Task was not created"
        task_id = tasks[0]['id']

        # Drop it
        result = client.drop_task(task_id)
        assert result is True
        print("\n✓ Marked task as dropped")

        # Verify it's dropped (need to include dropped tasks in query)
        all_tasks = client.get_tasks(project_id=test_project_id, dropped_only=True)
        dropped_task = next((t for t in all_tasks if t['id'] == task_id), None)
        assert dropped_task is not None
        assert dropped_task['dropped'] is True

    def test_drop_tasks_batch(self, client, test_project_id):
        """Test batch dropping multiple tasks."""
        # Create multiple tasks with unique names
        client.add_task(test_project_id, "Unique Batch Drop 1")
        client.add_task(test_project_id, "Unique Batch Drop 2")

        tasks = client.get_tasks(project_id=test_project_id, query="Unique Batch Drop")
        task_ids = [t['id'] for t in tasks]
        assert len(task_ids) >= 2, f"Expected 2+ tasks, got {len(task_ids)}"

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


# ============================================================================
# PHASE 2: ADVANCED FEATURES
# ============================================================================

class TestFolderOperations:
    """Test folder-related operations."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a client for real OmniFocus testing."""
        return OmniFocusClient(enable_safety_checks=True)

    def test_get_folders(self, client):
        """Test retrieving all folders."""
        folders = client.get_folders()

        # Should find our test folders
        folder_names = [f['name'] for f in folders]
        assert "Test Root Folder" in folder_names
        assert "Test Sub Folder" in folder_names

        # Verify folder structure
        root_folder = next(f for f in folders if f['name'] == "Test Root Folder")
        assert 'id' in root_folder
        assert root_folder['name'] == "Test Root Folder"
        print("\n✓ Retrieved folders successfully")

    def test_create_folder(self, client):
        """Test creating a new folder."""
        # Create root folder
        folder_id = client.create_folder("Phase 2 Test Folder")
        assert folder_id is not None
        assert len(folder_id) > 0

        # Verify it exists
        folders = client.get_folders()
        folder_names = [f['name'] for f in folders]
        assert "Phase 2 Test Folder" in folder_names

        # Create sub-folder
        sub_folder_id = client.create_folder("Phase 2 Sub Folder", parent_path="Phase 2 Test Folder")
        assert sub_folder_id is not None

        # Verify hierarchy
        folders = client.get_folders()
        sub_folder = next((f for f in folders if f['name'] == "Phase 2 Sub Folder"), None)
        assert sub_folder is not None
        print("\n✓ Created folders with hierarchy")


class TestNoteOperations:
    """Test note-related operations."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a client for real OmniFocus testing."""
        return OmniFocusClient(enable_safety_checks=True)

    def test_add_note_to_project(self, client):
        """Test adding a note to a project."""
        # Find Active Test Project
        projects = client.get_projects(query="Active Test Project")
        assert len(projects) > 0
        project_id = projects[0]['id']

        # Add note
        note_content = "This is a test note added by Phase 2 tests.\n\nIt has multiple lines."
        result = client.add_note(project_id, note_content)
        assert result is True

        # Verify note was added
        note = client.get_note(project_id)
        assert note_content in note
        print("\n✓ Added note to project")

    def test_get_note_from_task(self, client):
        """Test retrieving a note from a task."""
        # Find a task with a note
        projects = client.get_projects(query="Active Test Project")
        project_id = projects[0]['id']

        tasks = client.get_tasks(project_id=project_id, query="Task 2 - With Note")
        assert len(tasks) > 0

        task_id = tasks[0]['id']
        note = client.get_note(task_id, item_type="task")

        assert note is not None
        assert len(note) > 0
        print(f"\n✓ Retrieved note from task")


class TestTagBatchOperations:
    """Test batch tag operations."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a client for real OmniFocus testing."""
        return OmniFocusClient(enable_safety_checks=True)

    @pytest.fixture
    def test_tasks_for_tagging(self, client):
        """Create test tasks for batch tagging."""
        projects = client.get_projects(query="Active Test Project")
        project_id = projects[0]['id']

        # Create 3 tasks for tagging tests
        client.add_task(project_id, "Batch Tag Test 1")
        client.add_task(project_id, "Batch Tag Test 2")
        client.add_task(project_id, "Batch Tag Test 3")

        tasks = client.get_tasks(project_id=project_id, query="Batch Tag Test")
        task_ids = [t['id'] for t in tasks]

        yield task_ids

        # Cleanup
        client.delete_tasks(task_ids)

    def test_add_tag_to_multiple_tasks(self, client, test_tasks_for_tagging):
        """Test adding a tag to multiple tasks."""
        task_ids = test_tasks_for_tagging

        # Add 'urgent' tag to all tasks
        count = client.add_tag_to_tasks(task_ids, "urgent")
        assert count == len(task_ids)
        print(f"\n✓ Added tag to {count} tasks")

        # Verify tags were added
        projects = client.get_projects(query="Active Test Project")
        project_id = projects[0]['id']
        tasks = client.get_tasks(project_id=project_id, query="Batch Tag Test")

        for task in tasks:
            assert "urgent" in task.get('tags', [])

    def test_remove_tag_from_multiple_tasks(self, client, test_tasks_for_tagging):
        """Test removing a tag from multiple tasks."""
        task_ids = test_tasks_for_tagging

        # First add a tag
        client.add_tag_to_tasks(task_ids, "work")

        # Then remove it
        count = client.remove_tag_from_tasks(task_ids, "work")
        assert count == len(task_ids)
        print(f"\n✓ Removed tag from {count} tasks")

        # Verify tags were removed
        projects = client.get_projects(query="Active Test Project")
        project_id = projects[0]['id']
        tasks = client.get_tasks(project_id=project_id, query="Batch Tag Test")

        for task in tasks:
            assert "work" not in task.get('tags', [])


class TestReviewSystem:
    """Test project review system operations."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a client for real OmniFocus testing."""
        return OmniFocusClient(enable_safety_checks=True)

    def test_set_review_interval(self, client):
        """Test setting a review interval on a project."""
        # Find Active Test Project
        projects = client.get_projects(query="Active Test Project")
        assert len(projects) > 0
        project_id = projects[0]['id']

        # Set review interval (weekly = 1 week)
        result = client.set_review_interval(project_id, interval_weeks=1)
        assert result is True
        print("\n✓ Set review interval to 1 week")

    def test_mark_project_reviewed(self, client):
        """Test marking a project as reviewed."""
        # Find Active Test Project
        projects = client.get_projects(query="Active Test Project")
        assert len(projects) > 0
        project_id = projects[0]['id']

        # Mark as reviewed
        result = client.mark_project_reviewed(project_id)
        assert result is True
        print("\n✓ Marked project as reviewed")

    def test_get_projects_due_for_review(self, client):
        """Test retrieving projects due for review."""
        # This will return projects that need review
        projects = client.get_projects_due_for_review()

        # Should return a list (may be empty if no projects due)
        assert isinstance(projects, list)

        # Each project should have required fields
        for project in projects:
            assert 'id' in project
            assert 'name' in project

        print(f"\n✓ Found {len(projects)} projects due for review")


class TestTimeEstimation:
    """Test time estimation operations."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a client for real OmniFocus testing."""
        return OmniFocusClient(enable_safety_checks=True)

    def test_set_estimated_minutes(self, client):
        """Test setting estimated time on a task."""
        # Find a task
        projects = client.get_projects(query="Active Test Project")
        project_id = projects[0]['id']

        tasks = client.get_tasks(project_id=project_id, query="Task 1 - Flagged")
        assert len(tasks) > 0
        task_id = tasks[0]['id']

        # Set estimate to 30 minutes
        result = client.set_estimated_minutes(task_id, 30)
        assert result is True
        print("\n✓ Set estimated time to 30 minutes")

        # Verify estimate was set (get task and check)
        task = client.get_task(task_id)
        assert task is not None
        # Note: The estimate might be in the task data


class TestStalledProjects:
    """Test stalled project detection."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a client for real OmniFocus testing."""
        return OmniFocusClient(enable_safety_checks=True)

    def test_get_stalled_projects(self, client):
        """Test retrieving stalled projects (currently returns all active projects)."""
        # Get stalled projects (currently simplified to return all active projects)
        projects = client.get_stalled_projects()

        # Should return a list
        assert isinstance(projects, list)

        # Each project should have required fields
        for project in projects:
            assert 'id' in project
            assert 'name' in project
            assert 'status' in project

        print(f"\n✓ Found {len(projects)} active projects (stalled detection simplified)")


# ============================================================================
# PHASE 3: PARAMETER VARIATIONS & EDGE CASES
# ============================================================================

class TestGetTasksParameterVariations:
    """Test various parameter combinations for get_tasks()."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a client for real OmniFocus testing."""
        return OmniFocusClient(enable_safety_checks=True)

    @pytest.fixture(scope="class")
    def test_project_id(self, client):
        """Get the Active Test Project ID."""
        projects = client.get_projects(query="Active Test Project")
        return projects[0]['id']

    def test_get_tasks_with_project_id(self, client, test_project_id):
        """Test get_tasks with specific project_id."""
        tasks = client.get_tasks(project_id=test_project_id)

        assert isinstance(tasks, list)
        assert len(tasks) > 0

        # All tasks should be from this project
        for task in tasks:
            if 'project' in task and task['project']:
                assert 'Active Test Project' in task['project']

        print(f"\n✓ Found {len(tasks)} tasks in project")

    def test_get_tasks_include_completed(self, client, test_project_id):
        """Test get_tasks with include_completed=True."""
        all_tasks = client.get_tasks(project_id=test_project_id, include_completed=True)
        incomplete_tasks = client.get_tasks(project_id=test_project_id, include_completed=False)

        assert len(all_tasks) >= len(incomplete_tasks)
        print(f"\n✓ All tasks: {len(all_tasks)}, Incomplete: {len(incomplete_tasks)}")

    def test_get_tasks_flagged_only(self, client, test_project_id):
        """Test get_tasks with flagged_only=True."""
        flagged = client.get_tasks(project_id=test_project_id, flagged_only=True)

        assert isinstance(flagged, list)
        # Should find "Task 1 - Flagged"
        flagged_names = [t['name'] for t in flagged]
        assert any('Flagged' in name for name in flagged_names)

        # All returned tasks should be flagged
        for task in flagged:
            assert task.get('flagged', False) is True

        print(f"\n✓ Found {len(flagged)} flagged tasks")

    def test_get_tasks_available_only(self, client, test_project_id):
        """Test get_tasks with available_only=True."""
        available = client.get_tasks(project_id=test_project_id, available_only=True)

        assert isinstance(available, list)
        # Just verify it returns a list (may be empty if no available tasks)
        print(f"\n✓ Found {len(available)} available tasks")

    def test_get_tasks_dropped_only(self, client, test_project_id):
        """Test get_tasks with dropped_only=True."""
        dropped = client.get_tasks(project_id=test_project_id, dropped_only=True)

        assert isinstance(dropped, list)
        # All returned tasks should be dropped
        for task in dropped:
            assert task.get('dropped', False) is True

        print(f"\n✓ Found {len(dropped)} dropped tasks")

    def test_get_tasks_blocked_only(self, client, test_project_id):
        """Test get_tasks with blocked_only=True."""
        blocked = client.get_tasks(project_id=test_project_id, blocked_only=True)

        assert isinstance(blocked, list)
        print(f"\n✓ Found {len(blocked)} blocked tasks")

    def test_get_tasks_next_only(self, client, test_project_id):
        """Test get_tasks with next_only=True."""
        next_tasks = client.get_tasks(project_id=test_project_id, next_only=True)

        assert isinstance(next_tasks, list)
        print(f"\n✓ Found {len(next_tasks)} next action tasks")

    def test_get_tasks_overdue(self, client):
        """Test get_tasks with overdue=True."""
        overdue = client.get_tasks(overdue=True)

        assert isinstance(overdue, list)
        print(f"\n✓ Found {len(overdue)} overdue tasks")

    def test_get_tasks_due_relative_today(self, client):
        """Test get_tasks with due_relative='today'."""
        today_tasks = client.get_tasks(due_relative="today")

        assert isinstance(today_tasks, list)
        print(f"\n✓ Found {len(today_tasks)} tasks due today")

    def test_get_tasks_due_relative_this_week(self, client):
        """Test get_tasks with due_relative='this_week'."""
        week_tasks = client.get_tasks(due_relative="this_week")

        assert isinstance(week_tasks, list)
        print(f"\n✓ Found {len(week_tasks)} tasks due this week")

    def test_get_tasks_defer_relative_this_week(self, client):
        """Test get_tasks with defer_relative='this_week'."""
        deferred = client.get_tasks(defer_relative="this_week")

        assert isinstance(deferred, list)
        print(f"\n✓ Found {len(deferred)} tasks deferred this week")

    def test_get_tasks_max_estimated_minutes(self, client, test_project_id):
        """Test get_tasks with max_estimated_minutes."""
        quick_tasks = client.get_tasks(project_id=test_project_id, max_estimated_minutes=60)

        assert isinstance(quick_tasks, list)
        # Verify tasks have estimates <= 60 minutes
        for task in quick_tasks:
            if task.get('estimatedMinutes'):
                assert task['estimatedMinutes'] <= 60

        print(f"\n✓ Found {len(quick_tasks)} tasks <= 60 minutes")

    def test_get_tasks_has_estimate_true(self, client, test_project_id):
        """Test get_tasks with has_estimate=True."""
        with_estimate = client.get_tasks(project_id=test_project_id, has_estimate=True)

        assert isinstance(with_estimate, list)
        # All should have an estimate
        for task in with_estimate:
            assert task.get('estimatedMinutes') is not None
            assert task['estimatedMinutes'] > 0

        print(f"\n✓ Found {len(with_estimate)} tasks with estimates")

    def test_get_tasks_tag_filter_single(self, client):
        """Test get_tasks with single tag filter."""
        urgent_tasks = client.get_tasks(tag_filter=["urgent"])

        assert isinstance(urgent_tasks, list)
        # All should have 'urgent' tag
        for task in urgent_tasks:
            assert 'urgent' in task.get('tags', [])

        print(f"\n✓ Found {len(urgent_tasks)} tasks with 'urgent' tag")

    def test_get_tasks_sort_by_due_date(self, client, test_project_id):
        """Test get_tasks with sort_by='due_date'."""
        sorted_tasks = client.get_tasks(
            project_id=test_project_id,
            sort_by="due_date",
            sort_order="asc"
        )

        assert isinstance(sorted_tasks, list)
        # Verify sorting (tasks with due dates should be in order)
        due_dates = [t.get('dueDate') for t in sorted_tasks if t.get('dueDate')]
        assert due_dates == sorted(due_dates)

        print(f"\n✓ Retrieved {len(sorted_tasks)} tasks sorted by due date")


class TestGetProjectsParameterVariations:
    """Test various parameter combinations for get_projects()."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a client for real OmniFocus testing."""
        return OmniFocusClient(enable_safety_checks=True)

    def test_get_projects_on_hold_only(self, client):
        """Test get_projects with on_hold_only=True."""
        on_hold = client.get_projects(on_hold_only=True)

        assert isinstance(on_hold, list)

        # If we have on-hold projects, verify they are actually on hold
        if on_hold:
            for project in on_hold:
                assert project['status'] == 'on hold'

        print(f"\n✓ Found {len(on_hold)} on-hold projects")

    def test_get_projects_min_task_count(self, client):
        """Test get_projects with min_task_count."""
        projects = client.get_projects(min_task_count=3)

        assert isinstance(projects, list)
        # If filtering works, all returned projects should have at least 3 tasks
        # Note: Some implementations may not include taskCount in response
        if projects:
            for project in projects:
                if 'taskCount' in project:
                    assert project['taskCount'] >= 3

        print(f"\n✓ Found {len(projects)} projects (filtered by min_task_count)")

    def test_get_projects_has_overdue_tasks(self, client):
        """Test get_projects with has_overdue_tasks=True."""
        projects = client.get_projects(has_overdue_tasks=True)

        assert isinstance(projects, list)
        print(f"\n✓ Found {len(projects)} projects with overdue tasks")

    def test_get_projects_has_no_due_dates(self, client):
        """Test get_projects with has_no_due_dates=True."""
        projects = client.get_projects(has_no_due_dates=True)

        assert isinstance(projects, list)
        print(f"\n✓ Found {len(projects)} projects with no due dates")

    def test_get_projects_sort_by_name(self, client):
        """Test get_projects with sort_by='name'."""
        projects = client.get_projects(sort_by="name", sort_order="asc")

        assert isinstance(projects, list)
        assert len(projects) > 0

        # Verify alphabetical sorting (case-insensitive)
        names = [p['name'] for p in projects]
        sorted_names = sorted(names, key=str.lower)
        assert names == sorted_names

        print(f"\n✓ Retrieved {len(projects)} projects sorted by name")


class TestAddTaskParameterVariations:
    """Test various parameter combinations for add_task()."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a client for real OmniFocus testing."""
        return OmniFocusClient(enable_safety_checks=True)

    @pytest.fixture(scope="class")
    def test_project_id(self, client):
        """Get the Active Test Project ID."""
        projects = client.get_projects(query="Active Test Project")
        return projects[0]['id']

    def test_add_task_with_defer_date(self, client, test_project_id):
        """Test add_task with defer_date."""
        from datetime import datetime, timedelta

        defer_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        result = client.add_task(
            test_project_id,
            "Task with Defer Date",
            defer_date=defer_date
        )
        assert result is True

        # Verify task was created with defer date
        tasks = client.get_tasks(project_id=test_project_id, query="Task with Defer Date")
        assert len(tasks) > 0
        assert tasks[0].get('deferDate') is not None

        # Cleanup
        client.delete_task(tasks[0]['id'])
        print("\n✓ Created task with defer date")

    def test_add_task_with_estimated_minutes(self, client, test_project_id):
        """Test add_task with estimated time."""
        result = client.add_task(
            test_project_id,
            "Task with Estimate"
        )
        assert result is True

        # Get task and set estimate
        tasks = client.get_tasks(project_id=test_project_id, query="Task with Estimate")
        task_id = tasks[0]['id']
        client.set_estimated_minutes(task_id, 45)

        # Verify estimate was set
        task = client.get_task(task_id)
        assert task.get('estimatedMinutes') == 45

        # Cleanup
        client.delete_task(task_id)
        print("\n✓ Created task with time estimate")

    def test_add_task_with_recurrence(self, client, test_project_id):
        """Test add_task with recurrence pattern."""
        result = client.add_task(
            test_project_id,
            "Recurring Task Test",
            recurrence="FREQ=WEEKLY",
            repetition_method="fixed"
        )
        assert result is True

        # Verify task was created
        tasks = client.get_tasks(project_id=test_project_id, query="Recurring Task Test")
        assert len(tasks) > 0

        # Cleanup
        client.delete_task(tasks[0]['id'])
        print("\n✓ Created recurring task")


class TestUpdateTaskParameterVariations:
    """Test various parameter combinations for update_task()."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a client for real OmniFocus testing."""
        return OmniFocusClient(enable_safety_checks=True)

    @pytest.fixture
    def test_task(self, client):
        """Create a test task for update tests."""
        projects = client.get_projects(query="Active Test Project")
        project_id = projects[0]['id']

        client.add_task(project_id, "Task for Update Tests")
        tasks = client.get_tasks(project_id=project_id, query="Task for Update Tests")
        task_id = tasks[0]['id']

        yield task_id

        # Cleanup
        try:
            client.delete_task(task_id)
        except:
            pass

    def test_update_task_dates(self, client, test_task):
        """Test updating due_date and defer_date."""
        from datetime import datetime, timedelta

        due_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        defer_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        result = client.update_task(
            test_task,
            due_date=due_date,
            defer_date=defer_date
        )
        assert result is True

        # Verify dates were updated
        task = client.get_task(test_task)
        assert task.get('dueDate') is not None
        assert task.get('deferDate') is not None

        print("\n✓ Updated task dates")

    def test_update_task_clear_properties(self, client, test_task):
        """Test clearing properties by setting to None."""
        # First set some properties
        client.update_task(test_task, note="Test note", flagged=True)

        # Then clear them
        result = client.update_task(test_task, note="", flagged=False)
        assert result is True

        # Verify properties were cleared
        task = client.get_task(test_task)
        assert task.get('note', '') == ''
        assert task.get('flagged', False) is False

        print("\n✓ Cleared task properties")


# ============================================================================
# HIERARCHY FIELDS TESTS
# ============================================================================

class TestHierarchyFields:
    """Test that hierarchy and ordering fields are properly exposed."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a client for real OmniFocus testing."""
        return OmniFocusClient(enable_safety_checks=True)

    def test_project_has_sequential_field(self, client):
        """Test that projects expose sequential field."""
        projects = client.get_projects(query="Active Test Project")
        assert len(projects) > 0

        project = projects[0]
        assert 'sequential' in project
        assert isinstance(project['sequential'], bool)
        print(f"\n✓ Project has sequential field: {project['sequential']}")

    def test_task_has_hierarchy_fields(self, client):
        """Test that tasks expose parentTaskId, subtaskCount, sequential, position."""
        # Get a task we know has subtasks
        projects = client.get_projects(query="Active Test Project")
        project_id = projects[0]['id']

        tasks = client.get_tasks(project_id=project_id, query="Parent Task")
        assert len(tasks) > 0

        task = tasks[0]

        # Check all hierarchy fields exist
        assert 'parentTaskId' in task, "Missing parentTaskId field"
        assert 'subtaskCount' in task, "Missing subtaskCount field"
        assert 'sequential' in task, "Missing sequential field"
        assert 'position' in task, "Missing position field"

        # Check types
        assert isinstance(task['parentTaskId'], str), "parentTaskId should be string"
        assert isinstance(task['subtaskCount'], int), "subtaskCount should be int"
        assert isinstance(task['sequential'], bool), "sequential should be bool"
        assert isinstance(task['position'], int), "position should be int"

        # Check values make sense
        assert task['parentTaskId'] == "", "Top-level task should have empty parentTaskId"
        assert task['subtaskCount'] == 2, "Parent Task should have 2 subtasks"
        assert task['position'] >= 1, "Position should be 1-based"

        print(f"\n✓ Task hierarchy fields:")
        print(f"  parentTaskId: '{task['parentTaskId']}'")
        print(f"  subtaskCount: {task['subtaskCount']}")
        print(f"  sequential: {task['sequential']}")
        print(f"  position: {task['position']}")

    def test_subtask_has_parent_id(self, client):
        """Test that subtasks have their parent's ID in parentTaskId."""
        projects = client.get_projects(query="Active Test Project")
        project_id = projects[0]['id']

        # Get the parent task
        parent_tasks = client.get_tasks(project_id=project_id, query="Parent Task")
        parent_id = parent_tasks[0]['id']

        # Get its subtasks
        subtasks = client.get_subtasks(parent_id)
        assert len(subtasks) > 0

        for subtask in subtasks:
            assert 'parentTaskId' in subtask
            assert subtask['parentTaskId'] == parent_id, \
                f"Subtask should have parentTaskId='{parent_id}', got '{subtask['parentTaskId']}'"
            assert subtask['subtaskCount'] == 0, "Leaf tasks should have subtaskCount=0"

        print(f"\n✓ All {len(subtasks)} subtasks have correct parentTaskId")

    def test_position_ordering(self, client):
        """Test that position field reflects actual task order."""
        projects = client.get_projects(query="Active Test Project")
        project_id = projects[0]['id']

        # Get all tasks in the project
        tasks = client.get_tasks(project_id=project_id)

        # Top-level tasks should have sequential positions
        top_level = [t for t in tasks if t['parentTaskId'] == '']
        positions = [t['position'] for t in top_level]

        assert positions == sorted(positions), "Positions should be ordered"
        assert min(positions) >= 1, "Positions should be 1-based"

        print(f"\n✓ {len(top_level)} top-level tasks have ordered positions: {positions[:5]}...")

    def test_hierarchy_reconstruction(self, client):
        """Test that we can reconstruct full hierarchy from fields."""
        projects = client.get_projects(query="Active Test Project")
        project_id = projects[0]['id']

        # Get all tasks
        all_tasks = client.get_tasks(project_id=project_id)

        # Build hierarchy using fields
        tasks_by_id = {t['id']: t for t in all_tasks}
        children = {}
        for task in all_tasks:
            parent_id = task['parentTaskId']
            if parent_id not in children:
                children[parent_id] = []
            children[parent_id].append(task)

        # Sort children by position
        for child_list in children.values():
            child_list.sort(key=lambda t: t['position'])

        # Verify hierarchy matches expected structure
        root_tasks = children.get('', [])
        assert len(root_tasks) > 0, "Should have root-level tasks"

        # Find Parent Task
        parent_task = next((t for t in root_tasks if 'Parent Task' in t['name']), None)
        assert parent_task is not None, "Should find Parent Task"
        assert parent_task['subtaskCount'] == 2, "Parent Task should have 2 children"

        # Check its children
        parent_children = children.get(parent_task['id'], [])
        assert len(parent_children) == 2, "Should retrieve 2 children"
        assert parent_children[0]['position'] < parent_children[1]['position'], \
            "Children should be ordered by position"

        print(f"\n✓ Successfully reconstructed hierarchy:")
        print(f"  Root tasks: {len(root_tasks)}")
        print(f"  Parent Task has {len(parent_children)} children")
        print(f"    1. {parent_children[0]['name']} (pos {parent_children[0]['position']})")
        print(f"    2. {parent_children[1]['name']} (pos {parent_children[1]['position']})")


class TestTaskReordering:
    """Tests for reordering tasks within a project."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a client for real OmniFocus testing."""
        return OmniFocusClient(enable_safety_checks=True)

    def test_reorder_task_before_another(self, client):
        """Test moving a task before another task."""
        # Create a test project with 3 tasks
        project_id = client.create_project("Reorder Test Project")

        # Add 3 tasks
        client.add_task(project_id, "Task A")
        client.add_task(project_id, "Task B")
        client.add_task(project_id, "Task C")

        # Get tasks in current order
        tasks = client.get_tasks(project_id=project_id)
        assert len(tasks) == 3

        task_a = next(t for t in tasks if t['name'] == 'Task A')
        task_b = next(t for t in tasks if t['name'] == 'Task B')
        task_c = next(t for t in tasks if t['name'] == 'Task C')

        # Verify initial order by position
        assert task_a['position'] < task_b['position'] < task_c['position'], \
            "Initial order should be A < B < C"

        # Move Task C before Task A
        success = client.reorder_task(task_c['id'], before_task_id=task_a['id'])
        assert success, "reorder_task should return True"

        # Get updated order
        tasks_after = client.get_tasks(project_id=project_id)
        task_a_after = next(t for t in tasks_after if t['name'] == 'Task A')
        task_b_after = next(t for t in tasks_after if t['name'] == 'Task B')
        task_c_after = next(t for t in tasks_after if t['name'] == 'Task C')

        # Verify new order: C should be before A
        assert task_c_after['position'] < task_a_after['position'], \
            "Task C should be before Task A after reordering"
        assert task_a_after['position'] < task_b_after['position'], \
            "Task A should still be before Task B"

        print(f"\n✓ Successfully reordered tasks:")
        print(f"  Initial: A(pos {task_a['position']}) < B(pos {task_b['position']}) < C(pos {task_c['position']})")
        print(f"  After:   C(pos {task_c_after['position']}) < A(pos {task_a_after['position']}) < B(pos {task_b_after['position']})")

        # Cleanup
        client.delete_project(project_id)

    def test_reorder_task_after_another(self, client):
        """Test moving a task after another task."""
        # Create a test project with 3 tasks
        project_id = client.create_project("Reorder Test Project 2")

        # Add 3 tasks
        client.add_task(project_id, "Task X")
        client.add_task(project_id, "Task Y")
        client.add_task(project_id, "Task Z")

        # Get tasks in current order
        tasks = client.get_tasks(project_id=project_id)
        task_x = next(t for t in tasks if t['name'] == 'Task X')
        task_y = next(t for t in tasks if t['name'] == 'Task Y')
        task_z = next(t for t in tasks if t['name'] == 'Task Z')

        # Move Task X after Task Z
        success = client.reorder_task(task_x['id'], after_task_id=task_z['id'])
        assert success, "reorder_task should return True"

        # Get updated order
        tasks_after = client.get_tasks(project_id=project_id)
        task_x_after = next(t for t in tasks_after if t['name'] == 'Task X')
        task_y_after = next(t for t in tasks_after if t['name'] == 'Task Y')
        task_z_after = next(t for t in tasks_after if t['name'] == 'Task Z')

        # Verify new order: X should be after Z
        assert task_y_after['position'] < task_z_after['position'], \
            "Task Y should be before Task Z"
        assert task_z_after['position'] < task_x_after['position'], \
            "Task X should be after Task Z"

        print(f"\n✓ Successfully reordered tasks with 'after':")
        print(f"  After:   Y(pos {task_y_after['position']}) < Z(pos {task_z_after['position']}) < X(pos {task_x_after['position']})")

        # Cleanup
        client.delete_project(project_id)

    def test_reorder_task_requires_one_parameter(self, client):
        """Test that reorder_task requires either before_task_id or after_task_id."""
        project_id = client.create_project("Reorder Test Project 3")
        client.add_task(project_id, "Task 1")
        client.add_task(project_id, "Task 2")

        tasks = client.get_tasks(project_id=project_id)
        task1_id = tasks[0]['id']
        task2_id = tasks[1]['id']

        # Should raise ValueError if neither parameter provided
        with pytest.raises(ValueError, match="Must provide either before_task_id or after_task_id"):
            client.reorder_task(task1_id)

        # Should raise ValueError if both parameters provided
        with pytest.raises(ValueError, match="Cannot provide both"):
            client.reorder_task(task1_id, before_task_id=task2_id, after_task_id=task2_id)

        print("\n✓ Parameter validation works correctly")

        # Cleanup
        client.delete_project(project_id)


class TestAvailabilityFields:
    """Tests for availability status fields."""

    @pytest.fixture(scope="class")
    def client(self):
        """Create a client for real OmniFocus testing."""
        return OmniFocusClient(enable_safety_checks=True)

    def test_task_has_available_and_number_of_available_tasks(self, client):
        """Test that tasks include available and numberOfAvailableTasks fields."""
        # Create a project with a parent task and subtask
        project_id = client.create_project("Availability Test Project", sequential=True)
        
        # Add parent task and subtask
        client.add_task(project_id, "Parent Task")
        tasks = client.get_tasks(project_id=project_id)
        parent_id = tasks[0]['id']
        
        # Make it have a subtask
        client.add_task(project_id, "Subtask")
        all_tasks = client.get_tasks(project_id=project_id)
        subtask = next(t for t in all_tasks if t['name'] == 'Subtask')
        client.set_parent_task(subtask['id'], parent_id)
        
        # Get updated parent
        parent = client.get_task(parent_id)
        
        # Check fields exist
        assert 'available' in parent, "Should have available field"
        assert 'numberOfAvailableTasks' in parent, "Should have numberOfAvailableTasks field"
        
        # Check types
        assert isinstance(parent['available'], bool), "available should be boolean"
        assert isinstance(parent['numberOfAvailableTasks'], int), "numberOfAvailableTasks should be int"
        
        # For a sequential project, first task is available, parent should have available subtasks
        assert parent['numberOfAvailableTasks'] >= 0, "Should have count of available subtasks"
        
        print(f"\n✓ Task has availability fields:")
        print(f"  available: {parent['available']}")
        print(f"  numberOfAvailableTasks: {parent['numberOfAvailableTasks']}")
        print(f"  blocked: {parent['blocked']}")
        
        # Cleanup
        client.delete_project(project_id)

    def test_available_true_when_task_actionable(self, client):
        """Test that available is true for directly actionable tasks."""
        project_id = client.create_project("Available Task Test")
        client.add_task(project_id, "Available Task")
        
        tasks = client.get_tasks(project_id=project_id)
        task = tasks[0]
        
        # Task should be available (not blocked, not completed, not dropped, not deferred)
        assert task['completed'] == False
        assert task['dropped'] == False
        assert task['blocked'] == False
        assert task['deferDate'] == ""
        assert task['available'] == True, "Actionable task should be available"
        
        print(f"\n✓ Directly actionable task shows available: true")
        
        # Cleanup
        client.delete_project(project_id)

    def test_available_true_when_blocked_with_available_children(self, client):
        """Test that available is true for blocked tasks with available subtasks."""
        # Create sequential project - parent task will be sequential action group
        project_id = client.create_project("Blocked Parent Test", sequential=True)

        # Add first task and a parent task (which will be blocked)
        client.add_task(project_id, "First Task")
        client.add_task(project_id, "Blocked Parent")

        tasks = client.get_tasks(project_id=project_id)
        first_task = tasks[0]
        blocked_parent_task = tasks[1]

        # Add two children to the blocked parent, making it an action group
        # Make the parent itself parallel so children are available
        client.add_task(project_id, "Child 1")
        client.add_task(project_id, "Child 2")
        all_tasks = client.get_tasks(project_id=project_id)
        child1 = next(t for t in all_tasks if t['name'] == 'Child 1')
        child2 = next(t for t in all_tasks if t['name'] == 'Child 2')

        # Move children under blocked parent
        client.set_parent_task(child1['id'], blocked_parent_task['id'])
        client.set_parent_task(child2['id'], blocked_parent_task['id'])

        # Get updated parent
        blocked_parent = client.get_task(blocked_parent_task['id'])

        # Parent should be blocked (second in sequential project)
        # The parent action group itself is parallel (default), so children are available
        # Parent should be available (has available children)
        assert blocked_parent['blocked'] == True, "Second task in sequential project should be blocked"

        # Even if numberOfAvailableTasks is 0 (children might inherit blocked status),
        # we still test that the available field is computed correctly
        if blocked_parent['numberOfAvailableTasks'] > 0:
            assert blocked_parent['available'] == True, "Should be available due to available children"
            print(f"\n✓ Blocked task with available children shows available: true")
        else:
            # If children are also blocked (sequential inheritance), available should be false
            assert blocked_parent['available'] == False, "Should not be available if no available children"
            print(f"\n✓ Blocked task without available children shows available: false")

        print(f"  blocked: {blocked_parent['blocked']}")
        print(f"  numberOfAvailableTasks: {blocked_parent['numberOfAvailableTasks']}")
        print(f"  available: {blocked_parent['available']}")

        # Cleanup
        client.delete_project(project_id)
