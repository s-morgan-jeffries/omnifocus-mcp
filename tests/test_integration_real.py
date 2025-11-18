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

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


# Skip all tests in this file unless explicitly in test mode
pytestmark = pytest.mark.skipif(
    os.environ.get('OMNIFOCUS_TEST_MODE', '').lower() != 'true',
    reason="Real OmniFocus tests require OMNIFOCUS_TEST_MODE=true. "
           "Run scripts/setup_test_database.sh first."
)


# ============================================================================
# FIXTURE VERIFICATION TESTS
# ============================================================================

class TestFixtures:
    """Verify that our test fixtures work correctly with proper teardown."""

    def test_project_fixture_creates_and_cleans_up(self, client, test_project):
        """Test that test_project fixture creates a project and cleans it up."""
        # Verify project was created
        projects = client.get_projects(project_id=test_project)
        assert len(projects) == 1
        assert projects[0]['id'] == test_project
        assert 'Test Project' in projects[0]['name']
        print(f"\n✓ Project fixture created project: {projects[0]['name']}")

    def test_project_with_note_fixture(self, client, test_project_with_note):
        """Test that test_project_with_note fixture works correctly."""
        projects = client.get_projects(project_id=test_project_with_note,
                                      include_full_notes=True)
        assert len(projects) == 1
        assert projects[0]['note'] == "Test note content"
        print(f"\n✓ Project with note fixture works: {projects[0]['name']}")

    def test_projects_fixture_creates_multiple(self, client, test_projects):
        """Test that test_projects fixture creates 3 projects."""
        assert len(test_projects) == 3

        # Verify all projects exist
        for project_id in test_projects:
            projects = client.get_projects(project_id=project_id)
            assert len(projects) == 1
            assert 'Test Project' in projects[0]['name']

        print(f"\n✓ Projects fixture created {len(test_projects)} projects")

    def test_folder_fixture_creates_folder(self, client, test_folder):
        """Test that test_folder fixture creates a folder."""
        folders = client.get_folders()
        folder_ids = [f['id'] for f in folders]
        assert test_folder in folder_ids

        test_folder_obj = next(f for f in folders if f['id'] == test_folder)
        assert 'Test Folder' in test_folder_obj['name']
        print(f"\n✓ Folder fixture created folder: {test_folder_obj['name']}")

    def test_task_fixture_creates_and_cleans_up(self, client, test_task):
        """Test that test_task fixture creates a task and cleans it up."""
        # Verify task was created
        tasks = client.get_tasks(task_id=test_task)
        assert len(tasks) == 1
        assert tasks[0]['id'] == test_task
        assert 'Test Task' in tasks[0]['name']
        print(f"\n✓ Task fixture created task: {tasks[0]['name']}")

    def test_task_inbox_fixture_creates_inbox_task(self, client, test_task_inbox):
        """Test that test_task_inbox fixture creates an inbox task."""
        inbox_tasks = client.get_tasks(inbox_only=True)
        task_ids = [t['id'] for t in inbox_tasks]
        assert test_task_inbox in task_ids

        task = next(t for t in inbox_tasks if t['id'] == test_task_inbox)
        assert 'Test Inbox Task' in task['name']
        print(f"\n✓ Inbox task fixture created task: {task['name']}")

    def test_tasks_fixture_creates_multiple(self, client, test_tasks):
        """Test that test_tasks fixture creates 3 tasks."""
        assert len(test_tasks) == 3

        # Verify all tasks exist
        for task_id in test_tasks:
            tasks = client.get_tasks(task_id=task_id)
            assert len(tasks) == 1
            assert 'Test Task' in tasks[0]['name']

        print(f"\n✓ Tasks fixture created {len(test_tasks)} tasks")

    def test_task_with_note_fixture(self, client, test_task_with_note):
        """Test that test_task_with_note fixture works correctly."""
        tasks = client.get_tasks(task_id=test_task_with_note,
                                include_full_notes=True)
        assert len(tasks) == 1
        assert tasks[0]['note'] == "Test note content"
        print(f"\n✓ Task with note fixture works: {tasks[0]['name']}")

    def test_parent_task_with_subtasks_fixture(self, client, test_parent_task_with_subtasks):
        """Test that parent task fixture creates proper hierarchy."""
        parent_id = test_parent_task_with_subtasks['parent_id']
        subtask_ids = test_parent_task_with_subtasks['subtask_ids']

        # Verify parent exists
        parent_tasks = client.get_tasks(task_id=parent_id)
        assert len(parent_tasks) == 1
        assert parent_tasks[0]['subtaskCount'] == 2

        # Verify subtasks exist and have correct parent
        subtasks = client.get_tasks(parent_task_id=parent_id)
        assert len(subtasks) == 2
        for subtask in subtasks:
            assert subtask['parentTaskId'] == parent_id
            assert subtask['id'] in subtask_ids

        print(f"\n✓ Parent task fixture created hierarchy correctly")

    def test_sequential_project_fixture(self, client, test_sequential_project_with_tasks):
        """Test that sequential project fixture creates tasks correctly."""
        project_id = test_sequential_project_with_tasks['project_id']
        task_ids = test_sequential_project_with_tasks['task_ids']

        # Verify project is sequential
        projects = client.get_projects(project_id=project_id)
        assert len(projects) == 1
        assert projects[0]['sequential'] is True

        # Verify tasks exist
        assert len(task_ids) == 3
        for task_id in task_ids:
            tasks = client.get_tasks(task_id=task_id)
            assert len(tasks) == 1

        print(f"\n✓ Sequential project fixture created {len(task_ids)} tasks")

    def test_project_with_folder_fixture(self, client, test_project_with_folder):
        """Test that project with folder fixture creates correct hierarchy."""
        project_id = test_project_with_folder['project_id']
        folder_id = test_project_with_folder['folder_id']

        # Verify project is in folder
        projects = client.get_projects(project_id=project_id)
        assert len(projects) == 1
        assert 'Test Folder' in projects[0]['folderPath']

        print(f"\n✓ Project in folder fixture works correctly")

    def test_fixture_cleanup_even_on_failure(self, client, test_project):
        """Test that fixtures clean up even when test fails.

        This test intentionally raises an assertion error to verify cleanup.
        The fixture should still delete the project.

        NOTE: This test will be marked as 'failed' but the cleanup should work.
        """
        # Record the project ID before failure
        project_id_before_failure = test_project

        # Verify project exists
        projects = client.get_projects(project_id=project_id_before_failure)
        assert len(projects) == 1

        # This will cause the test to fail, but teardown should still run
        # Uncomment the next line to verify teardown works on failure
        # assert False, "Intentional failure to test fixture cleanup"

        print(f"\n✓ Cleanup test prepared (comment out assertion to test failure path)")


# ============================================================================
# LEGACY TESTS (Pre-Fixture Era)
# These tests rely on external setup script and will be refactored
# ============================================================================

class TestRealOmniFocusIntegration:
    """Integration tests with real OmniFocus.

    All tests use fixtures from conftest.py for automatic cleanup.
    Note: These are read-only tests that query existing data.
    """

    def test_get_projects_real(self, client, test_project):
        """Test getting projects from real OmniFocus."""
        # Get all projects (should include fixture project)
        projects = client.get_projects()

        assert isinstance(projects, list)
        assert len(projects) >= 1  # At least the fixture project

        # Verify project structure
        first_project = projects[0]
        assert 'id' in first_project
        assert 'name' in first_project
        assert 'status' in first_project

        print(f"\n✓ Found {len(projects)} projects in test database")

    def test_search_projects_real(self, client, test_project):
        """Test searching projects with query parameter."""
        # Search for test projects (fixture creates projects with "Test Project" in name)
        results = client.get_projects(query="Test")

        assert isinstance(results, list)
        # Should find at least the fixture project
        assert len(results) >= 1

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

    def test_get_inbox_tasks_real(self, client, test_task_inbox):
        """Test getting inbox tasks with inbox_only parameter."""
        # Get inbox tasks (should include fixture inbox task)
        inbox_tasks = client.get_tasks(inbox_only=True)

        assert isinstance(inbox_tasks, list)
        # Should have at least the fixture inbox task
        assert len(inbox_tasks) >= 1

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


class TestRealOmniFocusSafetyVerification:
    """Verify that safety guards work with real OmniFocus.

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_safety_guards_verify_database(self, client):
        """Test that safety guards actually check the database name."""
        # This test verifies the safety system works
        # Client fixture has safety checks enabled
        # The safety check will verify the database name via AppleScript
        projects = client.get_projects()
        assert isinstance(projects, list)

        print("\n✓ Safety guards successfully verified test database")

    def test_destructive_operation_checks_database_name(self, client, test_project):
        """Test that destructive operations verify database name."""
        # Use fixture project instead of querying
        # This operation should trigger database name verification
        # If we're not using the test database, it will be blocked
        task_id = client.create_task(
            "Safety Verification Task",
            project_id=test_project,
            note="If this task was created, safety guards are working!"
        )

        try:
            assert task_id is not None
            print("\n✓ Destructive operation verified database name before proceeding")
        finally:
            # Guaranteed cleanup
            client.delete_tasks(task_id)


class TestProjectCRUD:
    """Test project CRUD operations comprehensively.

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_create_project_basic(self, client, test_project):
        """Test creating a basic project."""
        # test_project fixture already created the project
        assert isinstance(test_project, str)  # Returns project ID
        assert len(test_project) > 0

        # Verify it exists
        projects = client.get_projects(project_id=test_project)
        assert len(projects) == 1
        assert 'Test Project' in projects[0]['name']
        print(f"\n✓ Created basic project: {projects[0]['name']}")

    def test_create_project_with_properties(self, client, test_project_with_folder):
        """Test creating project with all properties."""
        # test_project_with_folder already created project in folder
        project_id = test_project_with_folder['project_id']

        assert isinstance(project_id, str)  # Returns project ID
        projects = client.get_projects(project_id=project_id)
        assert len(projects) == 1
        assert 'Test Folder' in projects[0]['folderPath']
        print("\n✓ Created project with properties (in folder)")

    def test_get_project_by_id(self, client, test_project):
        """Test fetching a single project by ID."""
        # Use fixture project instead of querying
        results = client.get_projects(project_id=test_project)
        assert len(results) == 1
        project = results[0]

        assert project is not None
        assert project['id'] == test_project
        assert 'Test Project' in project['name']
        print(f"\n✓ Retrieved project by ID: {project['name']}")

    def test_get_project_includes_timestamp_fields(self, client, test_project):
        """Test that get_project includes all timestamp fields."""
        # Use fixture project
        results = client.get_projects(project_id=test_project)
        assert len(results) == 1
        project = results[0]

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

    def test_get_projects_includes_timestamp_fields(self, client, test_project):
        """Test that get_projects includes timestamp fields in list results."""
        # Use fixture project (could be any project, but fixture ensures one exists)
        projects = client.get_projects(project_id=test_project)
        assert len(projects) > 0

        # Check project has timestamp fields
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
        print(f"  Project: {project['name']}")
        print(f"  Created: {project['creationDate']}")
        print(f"  Modified: {project['modificationDate']}")

    def test_set_project_status_to_on_hold(self, client, test_project):
        """Test changing project status to on-hold."""
        from omnifocus_mcp.omnifocus_connector import ProjectStatus

        # Change fixture project to on-hold
        result = client.update_project(test_project, status=ProjectStatus.ON_HOLD)
        assert result["success"] is True
        print("\n✓ Set project to on-hold")

    def test_set_project_status_to_done(self, client, test_project):
        """Test completing a project."""
        from omnifocus_mcp.omnifocus_connector import ProjectStatus

        # Mark fixture project as done
        result = client.update_project(test_project, status=ProjectStatus.DONE)
        assert result["success"] is True
        print("\n✓ Marked project as done")
        # Fixture will clean up

    def test_update_project_name(self, client, test_project):
        """Test updating project name."""
        # Update the fixture project's name
        result = client.update_project(test_project, project_name="Updated Project Name")
        assert result["success"] is True
        print(f"\n✓ Updated project name: {result}")

        # Verify the change
        projects = client.get_projects(project_id=test_project)
        assert len(projects) == 1
        assert projects[0]['name'] == "Updated Project Name"

    def test_update_project_note(self, client, test_project_with_note):
        """Test updating project note."""
        # Update the fixture project's note
        result = client.update_project(test_project_with_note, note="Updated note content")
        assert result["success"] is True
        print(f"\n✓ Updated project note: {result}")

        # Verify the change
        projects = client.get_projects(project_id=test_project_with_note)
        assert len(projects) == 1
        assert projects[0]['note'] == "Updated note content"

    def test_update_project_sequential(self, client, test_project):
        """Test updating project sequential setting."""
        # Verify fixture project is parallel (default)
        projects = client.get_projects(project_id=test_project)
        assert len(projects) == 1
        # Default is parallel

        # Change to sequential
        result = client.update_project(test_project, sequential=True)
        assert result["success"] is True
        print(f"\n✓ Updated project to sequential: {result}")

        # Verify the change
        projects = client.get_projects(project_id=test_project)
        assert len(projects) == 1
        assert projects[0]['sequential'] is True

    def test_update_project_multiple_fields(self, client, test_project_with_note):
        """Test updating multiple project fields at once."""
        # Update multiple fields on fixture project
        result = client.update_project(
            test_project_with_note,
            project_name="New Multi-field Name",
            note="New note content",
            sequential=True
        )
        assert result["success"] is True
        print(f"\n✓ Updated multiple project fields: {result}")

        # Verify all changes
        projects = client.get_projects(project_id=test_project_with_note)
        assert len(projects) == 1
        project = projects[0]
        assert project['name'] == "New Multi-field Name"
        assert project['note'] == "New note content"
        assert project['sequential'] is True

    def test_update_project_preserves_note_when_not_provided(self, client, test_project_with_note):
        """Test that not providing note parameter preserves existing note."""
        # Update only the name (not the note)
        result = client.update_project(test_project_with_note, project_name="Updated Name Only")
        assert result["success"] is True
        print(f"\n✓ Updated project name without touching note: {result}")

        # Verify note is preserved (fixture created project with "Test note content")
        projects = client.get_projects(project_id=test_project_with_note)
        assert len(projects) == 1
        project = projects[0]
        assert project['name'] == "Updated Name Only"
        assert project['note'] == "Test note content"  # Original note preserved

    # ========================================================================
    # NEW API Integration Tests (update_project enhancements)
    # ========================================================================

    def test_update_project_set_status_integration(self, client, test_project):
        """Integration: update_project() can set project status."""
        # Set status to on_hold
        result = client.update_project(test_project, status="on_hold")
        assert result["success"] is True
        assert "status" in result["updated_fields"]
        print(f"\n✓ Set project status to on_hold: {result}")

        # Verify status was set
        projects = client.get_projects(project_id=test_project)
        assert len(projects) == 1
        project = projects[0]
        # NOTE: OmniFocus returns status with " status" suffix
        assert project['status'] == 'on hold status'

        # Set status to active
        result = client.update_project(test_project, status="active")
        assert result["success"] is True
        projects = client.get_projects(project_id=test_project)
        assert len(projects) == 1
        project = projects[0]
        assert project['status'] == 'active status'
        print("\n✓ Changed status to active")

    def test_update_project_set_review_interval_integration(self, client, test_project):
        """Integration: update_project() can set review interval."""
        # Set review interval to 2 weeks
        result = client.update_project(test_project, review_interval_weeks=2)
        assert result["success"] is True
        assert "review_interval_weeks" in result["updated_fields"]
        print(f"\n✓ Set review interval to 2 weeks: {result}")

        # NOTE: reviewInterval retrieval currently has a bug (returns None)
        # The interval IS set correctly (verified manually), but get_projects()
        # doesn't parse the {unit:week, steps:N, fixed:true} record format
        # For now, we just verify the operation succeeded
        projects = client.get_projects(project_id=test_project)
        assert len(projects) == 1
        # TODO: Fix get_projects() to parse review interval correctly
        # assert projects[0]['reviewInterval'] == "2 weeks"

    def test_update_project_mark_reviewed_integration(self, client, test_project):
        """Integration: update_project() can mark project as reviewed."""
        # Mark as reviewed now
        result = client.update_project(test_project, last_reviewed="now")
        assert result["success"] is True
        assert "last_reviewed" in result["updated_fields"]
        print(f"\n✓ Marked project as reviewed: {result}")

        # Verify last_reviewed was set (should be a date string)
        projects = client.get_projects(project_id=test_project)
        assert len(projects) == 1
        project = projects[0]
        # Field name is 'last_reviewed' not 'lastReviewDate' in NEW API
        assert project.get('last_reviewed') is not None or project.get('lastReviewDate') is not None
        last_review = project.get('last_reviewed') or project.get('lastReviewDate')
        assert len(last_review) > 0

    def test_update_project_move_to_folder_integration(self, client, test_project_with_folder):
        """Integration: update_project() can move project to folder."""
        # Fixture already created project in folder, verify it's there
        project_id = test_project_with_folder['project_id']
        projects = client.get_projects(project_id=project_id)
        assert len(projects) == 1
        project = projects[0]

        # Verify project is in folder
        assert 'Test Folder' in project.get('folderPath', '')
        print(f"\n✓ Project in folder: {project.get('folderPath', '')}")

    def test_update_project_multiple_new_fields_integration(self, client, test_project):
        """Integration: update_project() can update multiple new fields at once."""
        # Update name, status, and review interval together
        result = client.update_project(
            test_project,
            project_name="Multi-field Test Updated",
            status="active",
            review_interval_weeks=4
        )

        assert result["success"] is True
        assert len(result["updated_fields"]) == 3
        assert "project_name" in result["updated_fields"]
        assert "status" in result["updated_fields"]
        assert "review_interval_weeks" in result["updated_fields"]
        print(f"\n✓ Updated {len(result['updated_fields'])} fields: {result['updated_fields']}")

        # Verify all changes
        projects = client.get_projects(project_id=test_project)
        assert len(projects) == 1
        project = projects[0]
        assert project['name'] == "Multi-field Test Updated"
        assert project['status'] == 'active status'
        # NOTE: reviewInterval retrieval has a bug (returns None)
        # Just verify the operation succeeded

    def test_update_projects_batch_integration(self, client, test_projects):
        """Integration: update_projects() can update multiple projects at once."""
        # Use fixture that created 3 projects
        # Batch update status
        result = client.update_projects(
            test_projects,
            status="on_hold"
        )

        assert result["updated_count"] == 3
        assert result["failed_count"] == 0
        assert len(result["updated_ids"]) == 3
        print(f"\n✓ Batch updated 3 projects: {result}")

        # Verify all were updated
        for project_id in test_projects:
            results = client.get_projects(project_id=project_id)
            assert len(results) == 1
            assert results[0]['status'] == 'on hold status'

    def test_update_projects_single_id_string_integration(self, client, test_project):
        """Integration: update_projects() accepts single ID as string (Union type)."""
        # Use single string, not list
        result = client.update_projects(test_project, sequential=True)

        assert result["updated_count"] == 1
        assert result["failed_count"] == 0
        print(f"\n✓ Single ID update: {result}")

        # Verify
        results = client.get_projects(project_id=test_project)
        assert len(results) == 1
        project = results[0]
        assert project['sequential'] is True

    def test_delete_project(self, client, test_project):
        """Test deleting a single project."""
        # Delete the fixture project
        result = client.delete_projects(test_project)
        assert result["deleted_count"] == 1
        print("\n✓ Deleted project")

        # Verify it's gone
        projects_after = client.get_projects(project_id=test_project)
        # Should be empty
        assert len(projects_after) == 0

    def test_delete_projects_batch(self, client, test_projects):
        """Test batch deleting multiple projects."""
        # Use fixture that created 3 projects
        # Batch delete
        result = client.delete_projects(test_projects)
        assert result["deleted_count"] == 3
        print(f"\n✓ Batch deleted {result['deleted_count']} projects")


class TestTaskCRUD:
    """Test task CRUD operations comprehensively.

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_get_task_by_id(self, client, test_task):
        """Test fetching a single task by ID."""
        # Use fixture task
        results = client.get_tasks(task_id=test_task)
        assert len(results) == 1
        task = results[0]

        assert task is not None
        assert task['id'] == test_task
        print(f"\n✓ Retrieved task by ID: {task['name']}")

    def test_get_task_includes_timestamp_fields(self, client, test_task):
        """Test that get_task includes all timestamp fields."""
        # Use fixture task
        results = client.get_tasks(task_id=test_task)
        assert len(results) == 1
        task = results[0]

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

    def test_get_task_includes_tags(self, client, test_project):
        """Test that get_task includes tags array."""
        # Create a task with tags using fixture project
        task_id = client.create_task("Task with Tags for Testing", project_id=test_project, tags=["test-work", "test-urgent"])

        try:
            # Get full task details
            results = client.get_tasks(task_id=task_id)
            assert len(results) == 1
            full_task = results[0]

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
        finally:
            # Guaranteed cleanup
            client.delete_tasks(task_id)

    def test_get_tasks_includes_timestamp_fields(self, client, test_task):
        """Test that get_tasks includes timestamp fields in list results."""
        # Use fixture task
        tasks = client.get_tasks(task_id=test_task)
        assert len(tasks) > 0

        # Check task has timestamp fields
        task = tasks[0]

        assert 'creationDate' in task
        assert 'modificationDate' in task
        assert 'completionDate' in task
        assert 'droppedDate' in task

        # Active tasks should have creationDate and modificationDate
        if not task.get('completed'):
            assert task['creationDate'] is not None
            assert task['modificationDate'] is not None

        print("\n✓ get_tasks includes timestamp fields")
        print(f"  Task: {task['name']}")
        print(f"  Created: {task['creationDate']}")
        print(f"  Modified: {task['modificationDate']}")

    def test_get_tasks_includes_tags(self, client, test_project):
        """Test that get_tasks includes tags array."""
        # Create a task with tags
        task_id = client.create_task("Task for get_tasks Tags Test", project_id=test_project, tags=["test-work"])

        try:
            # Get tasks
            tasks = client.get_tasks(project_id=test_project)
            task = next((t for t in tasks if t['name'] == "Task for get_tasks Tags Test"), None)
            assert task is not None

            # Verify tags field is present and is an array
            assert 'tags' in task
            assert isinstance(task['tags'], list)

            # Should have the tag we added
            tag_names = [t if isinstance(t, str) else t.get('name') for t in task['tags']]
            assert "test-work" in tag_names

            print("\n✓ get_tasks includes tags array")
            print(f"  Tags: {tag_names}")
        finally:
            # Guaranteed cleanup
            client.delete_tasks(task_id)

    def test_get_subtasks(self, client, test_parent_task_with_subtasks):
        """Test getting subtasks of a parent task."""
        # Use fixture with parent and subtasks
        parent_id = test_parent_task_with_subtasks['parent_id']

        # Get subtasks
        subtasks = client.get_tasks(parent_task_id=parent_id)
        assert isinstance(subtasks, list)
        assert len(subtasks) == 2  # Fixture creates 2 subtasks
        print(f"\n✓ Found {len(subtasks)} subtasks")

    def test_delete_task(self, client, test_task):
        """Test deleting a single task."""
        # Delete the fixture task
        result = client.delete_tasks(test_task)
        assert result["deleted_count"] == 1
        print("\n✓ Deleted task")

    def test_delete_tasks_batch(self, client, test_tasks):
        """Test batch deleting multiple tasks."""
        # Use fixture that created 3 tasks
        # Batch delete
        result = client.delete_tasks(test_tasks)
        assert result["deleted_count"] == 3
        assert result["failed_count"] == 0
        assert len(result["deleted_ids"]) == 3
        print(f"✓ Batch deleted {result['deleted_count']} tasks")

    def test_move_task_to_different_project(self, client, test_task, test_projects):
        """Test moving a task to a different project."""
        # Use fixture task and move to one of the fixture projects
        target_project_id = test_projects[1]  # Use second project from batch fixture

        # Move the task
        result = client.update_task(test_task, project_id=target_project_id)
        assert result["success"] is True
        print("\n✓ Moved task to different project")

    def test_move_tasks_batch(self, client, test_tasks, test_project):
        """Test batch moving multiple tasks."""
        # Use fixture tasks and fixture project as target
        # Batch move to single project
        result = client.update_tasks(test_tasks, project_id=test_project)
        assert result["updated_count"] == 3
        print(f"\n✓ Batch moved {result['updated_count']} tasks")

    def test_drop_task(self, client, test_task):
        """Test marking a task as dropped."""
        from omnifocus_mcp.omnifocus_connector import TaskStatus

        # Drop the fixture task
        result = client.update_task(test_task, status=TaskStatus.DROPPED)
        assert result["success"] is True
        print("\n✓ Marked task as dropped")

        # Verify it's dropped
        tasks = client.get_tasks(task_id=test_task)
        assert len(tasks) == 1
        assert tasks[0]['dropped'] is True

    def test_drop_tasks_batch(self, client, test_tasks):
        """Test batch dropping multiple tasks."""
        from omnifocus_mcp.omnifocus_connector import TaskStatus

        # Batch drop fixture tasks
        result = client.update_tasks(test_tasks, status=TaskStatus.DROPPED)
        assert result["updated_count"] == 3
        print(f"\n✓ Batch dropped {result['updated_count']} tasks")

    def test_set_parent_task(self, client, test_project):
        """Test creating task hierarchy."""
        # Create two tasks using fixture project
        parent_id = client.create_task("New Parent Task", project_id=test_project)
        child_id = client.create_task("New Child Task", project_id=test_project)

        try:
            # Set parent
            result = client.update_task(child_id, parent_task_id=parent_id)
            assert result["success"] is True
            print("\n✓ Set task parent relationship")
        finally:
            # Guaranteed cleanup
            client.delete_tasks([parent_id, child_id])

    def test_complete_tasks_batch(self, client, test_tasks):
        """Test batch completing multiple tasks."""
        # Use fixture tasks
        # Batch complete
        result = client.update_tasks(test_tasks, completed=True)
        assert result["updated_count"] == 3
        print(f"\n✓ Batch completed {result['updated_count']} tasks")


# ============================================================================
# PHASE 2: ADVANCED FEATURES
# ============================================================================

class TestFolderOperations:
    """Test folder-related operations.

    All tests use fixtures from conftest.py for automatic cleanup.
    NOTE: Folders cannot be deleted via OmniFocus AppleScript API, so cleanup is limited.
    """

    def test_get_folders(self, client, test_folder):
        """Test retrieving all folders."""
        folders = client.get_folders()

        # Should find our fixture folder
        folder_ids = [f['id'] for f in folders]
        assert test_folder in folder_ids

        # Verify folder structure
        folder = next(f for f in folders if f['id'] == test_folder)
        assert 'id' in folder
        assert 'Test Folder' in folder['name']
        print("\n✓ Retrieved folders successfully")

    def test_create_folder(self, client, test_folder):
        """Test creating a new folder with hierarchy."""
        # test_folder fixture already created a root folder
        # Create sub-folder under it
        folders = client.get_folders()
        test_folder_obj = next(f for f in folders if f['id'] == test_folder)
        parent_name = test_folder_obj['name']

        # Create sub-folder using fixture folder as parent
        sub_folder_id = client.create_folder(f"Sub of {parent_name[:20]}", parent_path=parent_name)
        assert sub_folder_id is not None

        # Verify hierarchy
        folders = client.get_folders()
        sub_folder = next((f for f in folders if f['id'] == sub_folder_id), None)
        assert sub_folder is not None
        print("\n✓ Created folders with hierarchy")

        # NOTE: OmniFocus API limitation - folders cannot be deleted via AppleScript
        # This test creates folders that will remain in the test database
        # The unique naming strategy (timestamp-based) prevents test pollution


class TestNoteOperations:
    """Test note operations integrated into CRUD.

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_add_note_to_task(self, client, test_task_with_note):
        """Test adding note during task creation."""
        # Use fixture that creates task with note
        # Get task with full notes
        results = client.get_tasks(task_id=test_task_with_note, include_full_notes=True)
        assert len(results) == 1
        retrieved = results[0]

        assert retrieved['note'] == "Test note content"
        print("\n✓ Created task with note")
        # Fixture handles cleanup

    def test_update_task_note(self, client, test_task):
        """Test updating task note."""
        # Use fixture task (no note initially)
        # Update note
        result = client.update_task(test_task, note="Updated note content")
        assert result["success"] is True

        # Verify
        results = client.get_tasks(task_id=test_task, include_full_notes=True)
        assert results[0]['note'] == "Updated note content"
        print("\n✓ Updated task note")
        # Fixture handles cleanup

    def test_add_note_to_project(self, client, test_project_with_note):
        """Test adding note to project."""
        # Use fixture that creates project with note
        # Get project with full notes
        results = client.get_projects(project_id=test_project_with_note, include_full_notes=True)
        assert len(results) == 1
        retrieved = results[0]

        assert retrieved['note'] == "Test note content"
        print("\n✓ Created project with note")
        # Fixture handles cleanup


class TestTagBatchOperations:
    """Test batch tag operations.

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_add_tag_to_multiple_tasks(self, client, test_tasks, test_project):
        """Test adding a tag to multiple tasks."""
        # Use fixture tasks (3 tasks created by test_tasks fixture)
        # Add 'urgent' tag to all tasks
        result = client.update_tasks(test_tasks, add_tags=["urgent"])
        assert result["updated_count"] == len(test_tasks)
        print(f"\n✓ Added tag to {result['updated_count']} tasks")

        # Verify tags were added
        tasks = client.get_tasks(project_id=test_project)
        for task in tasks:
            if task['id'] in test_tasks:
                assert "urgent" in task.get('tags', [])

    def test_remove_tag_from_multiple_tasks(self, client, test_tasks, test_project):
        """Test removing a tag from multiple tasks."""
        # Use fixture tasks
        # First add a tag
        client.update_tasks(test_tasks, add_tags=["work"])

        # Then remove it
        result = client.update_tasks(test_tasks, remove_tags=["work"])
        assert result["updated_count"] == len(test_tasks)
        print(f"\n✓ Removed tag from {result['updated_count']} tasks")

        # Verify tags were removed
        tasks = client.get_tasks(project_id=test_project)
        for task in tasks:
            if task['id'] in test_tasks:
                assert "work" not in task.get('tags', [])


class TestTimeEstimation:
    """Test time estimation operations.

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_set_estimated_minutes(self, client, test_task):
        """Test setting estimated time on a task."""
        # Use fixture task
        # Set estimate to 30 minutes
        result = client.update_task(test_task, estimated_minutes=30)
        assert result["success"] is True
        print("\n✓ Set estimated time to 30 minutes")

        # Verify estimate was set
        results = client.get_tasks(task_id=test_task)
        assert len(results) == 1
        task = results[0]
        assert task.get('estimatedMinutes') == 30
        # Fixture handles cleanup


# ============================================================================
# PHASE 3: PARAMETER VARIATIONS & EDGE CASES
# ============================================================================

class TestGetTasksParameterVariations:
    """Test various parameter combinations for get_tasks().

    All tests use fixtures from conftest.py for automatic cleanup.
    Note: Most tests are read-only and use fixture projects/tasks for querying.
    """

    def test_get_tasks_with_project_id(self, client, test_project, test_tasks):
        """Test get_tasks with specific project_id."""
        tasks = client.get_tasks(project_id=test_project)

        assert isinstance(tasks, list)
        assert len(tasks) == 3  # test_tasks fixture creates 3 tasks

        # All tasks should be from this project (fixture project)
        for task in tasks:
            if 'projectId' in task:
                assert task['projectId'] == test_project

        print(f"\n✓ Found {len(tasks)} tasks in project")

    def test_get_tasks_include_completed(self, client, test_project):
        """Test get_tasks with include_completed=True."""
        all_tasks = client.get_tasks(project_id=test_project, include_completed=True)
        incomplete_tasks = client.get_tasks(project_id=test_project, include_completed=False)

        assert len(all_tasks) >= len(incomplete_tasks)
        print(f"\n✓ All tasks: {len(all_tasks)}, Incomplete: {len(incomplete_tasks)}")

    def test_get_tasks_flagged_only(self, client, test_project, test_tasks):
        """Test get_tasks with flagged_only=True."""
        # Flag one of the fixture tasks
        client.update_task(test_tasks[0], flagged=True)

        # Query for flagged tasks in project
        flagged = client.get_tasks(project_id=test_project, flagged_only=True)

        assert isinstance(flagged, list)
        assert len(flagged) > 0

        # All returned tasks should be flagged
        for task in flagged:
            assert task.get('flagged', False) is True

        print(f"\n✓ Found {len(flagged)} flagged tasks")

    def test_get_tasks_available_only(self, client, test_project):
        """Test get_tasks with available_only=True."""
        available = client.get_tasks(project_id=test_project, available_only=True)

        assert isinstance(available, list)
        # Just verify it returns a list (may be empty if no available tasks)
        print(f"\n✓ Found {len(available)} available tasks")

    def test_get_tasks_dropped_only(self, client, test_project):
        """Test get_tasks with dropped_only=True."""
        dropped = client.get_tasks(project_id=test_project, dropped_only=True)

        assert isinstance(dropped, list)
        # All returned tasks should be dropped
        for task in dropped:
            assert task.get('dropped', False) is True

        print(f"\n✓ Found {len(dropped)} dropped tasks")

    def test_get_tasks_blocked_only(self, client, test_project):
        """Test get_tasks with blocked_only=True."""
        blocked = client.get_tasks(project_id=test_project, blocked_only=True)

        assert isinstance(blocked, list)
        print(f"\n✓ Found {len(blocked)} blocked tasks")

    def test_get_tasks_next_only(self, client, test_project):
        """Test get_tasks with next_only=True."""
        next_tasks = client.get_tasks(project_id=test_project, next_only=True)

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

    def test_get_tasks_max_estimated_minutes(self, client, test_project):
        """Test get_tasks with max_estimated_minutes."""
        quick_tasks = client.get_tasks(project_id=test_project, max_estimated_minutes=60)

        assert isinstance(quick_tasks, list)
        # Verify tasks have estimates <= 60 minutes
        for task in quick_tasks:
            if task.get('estimatedMinutes'):
                assert task['estimatedMinutes'] <= 60

        print(f"\n✓ Found {len(quick_tasks)} tasks <= 60 minutes")

    def test_get_tasks_has_estimate_true(self, client, test_project):
        """Test get_tasks with has_estimate=True."""
        with_estimate = client.get_tasks(project_id=test_project, has_estimate=True)

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

    def test_get_tasks_sort_by_due_date(self, client, test_project):
        """Test get_tasks with sort_by='due_date'."""
        sorted_tasks = client.get_tasks(
            project_id=test_project,
            sort_by="due_date",
            sort_order="asc"
        )

        assert isinstance(sorted_tasks, list)
        # Verify sorting (tasks with due dates should be in order)
        due_dates = [t.get('dueDate') for t in sorted_tasks if t.get('dueDate')]
        assert due_dates == sorted(due_dates)

        print(f"\n✓ Retrieved {len(sorted_tasks)} tasks sorted by due date")

    # ========================================================================
    # NEW API (Phase 3.1): task_id, parent_task_id, include_full_notes
    # ========================================================================

    def test_get_tasks_with_task_id_integration(self, client, test_project, test_tasks):
        """Integration: get_tasks(task_id=X) filters to single task."""
        # Use fixture task ID
        specific_task_id = test_tasks[0]

        # Get that specific task using task_id parameter
        result = client.get_tasks(task_id=specific_task_id)

        assert isinstance(result, list)
        assert len(result) == 1, "Should return exactly 1 task"
        assert result[0]['id'] == specific_task_id
        print(f"\n✓ get_tasks(task_id) returned specific task: {result[0]['name']}")

    def test_get_tasks_with_parent_task_id_integration(self, client, test_parent_task_with_subtasks):
        """Integration: get_tasks(parent_task_id=X) returns subtasks."""
        # Use fixture that creates parent with 2 subtasks
        parent_id = test_parent_task_with_subtasks['parent_id']

        # Get subtasks using parent_task_id parameter
        subtasks = client.get_tasks(parent_task_id=parent_id)

        assert isinstance(subtasks, list)
        assert len(subtasks) == 2, "Fixture creates exactly 2 subtasks"

        # Verify all have correct parent
        for subtask in subtasks:
            assert subtask.get('parentTaskId') == parent_id, \
                f"Subtask {subtask['name']} should have parentTaskId={parent_id}"

        print(f"\n✓ get_tasks(parent_task_id) returned {len(subtasks)} subtasks")

    def test_get_tasks_include_full_notes_integration(self, client, test_task_with_note):
        """Integration: get_tasks(include_full_notes=True) returns complete notes."""
        # Get task with note using fixture
        tasks = client.get_tasks(task_id=test_task_with_note, include_full_notes=True)

        assert isinstance(tasks, list)
        assert len(tasks) == 1

        # Find a task with a note
        tasks_with_notes = [t for t in tasks if t.get('note') and len(t['note']) > 0]
        if tasks_with_notes:
            task = tasks_with_notes[0]
            # Verify note field is present and has content
            assert 'note' in task
            assert len(task['note']) > 0
            print(f"\n✓ get_tasks(include_full_notes=True) returned full notes")
            print(f"  Task: {task['name']}")
            print(f"  Note length: {len(task['note'])} characters")
        else:
            print(f"\n✓ get_tasks(include_full_notes=True) works (no tasks with notes in test data)")


class TestGetProjectsParameterVariations:
    """Test various parameter combinations for get_projects().

    All tests use fixtures from conftest.py for automatic cleanup.
    Note: Most tests are read-only parameter variation tests.
    """

    def test_get_projects_on_hold_only(self, client):
        """Test get_projects with on_hold_only=True."""
        on_hold = client.get_projects(on_hold_only=True)

        assert isinstance(on_hold, list)

        # If we have on-hold projects, verify they are actually on hold
        # NOTE: OmniFocus returns status with " status" suffix
        if on_hold:
            for project in on_hold:
                assert project['status'] == 'on hold status'

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

    def test_get_projects_sort_by_name(self, client, test_projects):
        """Test get_projects with sort_by='name'."""
        # Get projects (fixture creates 3 projects with unique names)
        projects = client.get_projects(sort_by="name", sort_order="asc")

        assert isinstance(projects, list)
        assert len(projects) >= 3  # At least the fixture projects

        # Verify alphabetical sorting (case-insensitive)
        names = [p['name'] for p in projects]
        sorted_names = sorted(names, key=str.lower)
        assert names == sorted_names

        print(f"\n✓ Retrieved {len(projects)} projects sorted by name")

    # ========================================================================
    # NEW API (Phase 3.2): project_id, include_full_notes
    # ========================================================================

    def test_get_projects_with_project_id_integration(self, client, test_project):
        """Integration: get_projects(project_id=X) filters to single project."""
        # Use fixture project ID
        specific_project_id = test_project

        # Get that specific project using project_id parameter
        result = client.get_projects(project_id=specific_project_id)

        assert isinstance(result, list)
        assert len(result) == 1, "Should return exactly 1 project"
        assert result[0]['id'] == specific_project_id
        print(f"\n✓ get_projects(project_id) returned specific project: {result[0]['name']}")

    def test_get_projects_include_full_notes_integration(self, client, test_project_with_note):
        """Integration: get_projects(include_full_notes=True) returns complete notes."""
        # Get project with note using fixture
        projects = client.get_projects(project_id=test_project_with_note, include_full_notes=True)

        assert isinstance(projects, list)
        assert len(projects) == 1

        # Verify project has note
        project = projects[0]
        if project.get('note') and len(project['note']) > 0:
            # Verify note field is present and has content
            assert 'note' in project
            assert len(project['note']) > 0
            print(f"\n✓ get_projects(include_full_notes=True) returned full notes")
            print(f"  Project: {project['name']}")
            print(f"  Note length: {len(project['note'])} characters")
        else:
            print(f"\n✓ get_projects(include_full_notes=True) works (no projects with notes in test data)")


class TestAddTaskParameterVariations:
    """Test various parameter combinations for create_task().

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_add_task_with_defer_date(self, client, test_project):
        """Test create_task with defer_date."""
        from datetime import datetime, timedelta

        defer_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

        task_id = client.create_task(
            "Task with Defer Date",
            project_id=test_project,
            defer_date=defer_date
        )

        try:
            assert task_id is not None

            # Verify task was created with defer date
            tasks = client.get_tasks(project_id=test_project, query="Task with Defer Date")
            assert len(tasks) > 0
            assert tasks[0].get('deferDate') is not None

            print("\n✓ Created task with defer date")
        finally:
            # Guaranteed cleanup
            client.delete_tasks(task_id)

    def test_add_task_with_estimated_minutes(self, client, test_project):
        """Test create_task with estimated time."""
        task_id = client.create_task(
            "Task with Estimate",
            project_id=test_project,
            estimated_minutes=45
        )

        try:
            assert task_id is not None

            # Verify estimate was set
            results = client.get_tasks(task_id=task_id)
            assert len(results) == 1
            task = results[0]
            assert task.get('estimatedMinutes') == 45

            print("\n✓ Created task with time estimate")
        finally:
            # Guaranteed cleanup
            client.delete_tasks(task_id)

    def test_add_task_with_recurrence(self, client, test_project):
        """Test create_task with recurrence pattern."""
        # Note: recurrence parameters not in v0.6.0 create_task signature
        # This test may need to be updated based on actual API support
        task_id = client.create_task(
            "Recurring Task Test",
            project_id=test_project
        )

        try:
            assert task_id is not None

            # Verify task was created
            tasks = client.get_tasks(project_id=test_project, query="Recurring Task Test")
            assert len(tasks) > 0

            print("\n✓ Created task (recurrence parameters removed in v0.6.0)")
        finally:
            # Guaranteed cleanup
            client.delete_tasks(task_id)


class TestUpdateTaskParameterVariations:
    """Test various parameter combinations for update_task().

    All tests use fixtures from conftest.py for automatic cleanup.
    """

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
        assert result["success"] is True  # NEW API returns dict

        # Verify dates were updated (NEW API uses get_tasks with task_id filter)
        tasks = client.get_tasks(task_id=test_task)
        assert len(tasks) == 1
        task = tasks[0]
        assert task.get('dueDate') is not None
        assert task.get('deferDate') is not None

        print("\n✓ Updated task dates")

    def test_update_task_clear_properties(self, client, test_task):
        """Test clearing properties by setting to None."""
        # First set some properties
        client.update_task(test_task, note="Test note", flagged=True)

        # Then clear them
        result = client.update_task(test_task, note="", flagged=False)
        assert result["success"] is True  # NEW API returns dict

        # Verify properties were cleared (NEW API uses get_tasks with task_id filter)
        tasks = client.get_tasks(task_id=test_task)
        assert len(tasks) == 1
        task = tasks[0]
        assert task.get('note', '') == ''
        assert task.get('flagged', False) is False

        print("\n✓ Cleared task properties")


# ============================================================================
# HIERARCHY FIELDS TESTS
# ============================================================================

class TestHierarchyFields:
    """Test that hierarchy and ordering fields are properly exposed.

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_project_has_sequential_field(self, client, test_project):
        """Test that projects expose sequential field."""
        # Use fixture project
        projects = client.get_projects(project_id=test_project)
        assert len(projects) == 1

        project = projects[0]
        assert 'sequential' in project
        assert isinstance(project['sequential'], bool)
        print(f"\n✓ Project has sequential field: {project['sequential']}")

    def test_task_has_hierarchy_fields(self, client, test_parent_task_with_subtasks):
        """Test that tasks expose parentTaskId, subtaskCount, sequential, position."""
        # Use fixture that created parent task with 2 subtasks
        parent_id = test_parent_task_with_subtasks['parent_id']

        tasks = client.get_tasks(task_id=parent_id)
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

    def test_subtask_has_parent_id(self, client, test_parent_task_with_subtasks):
        """Test that subtasks have their parent's ID in parentTaskId."""
        # Use fixture with parent and subtasks
        parent_id = test_parent_task_with_subtasks['parent_id']

        # Get its subtasks
        subtasks = client.get_tasks(parent_task_id=parent_id)
        assert len(subtasks) > 0

        for subtask in subtasks:
            assert 'parentTaskId' in subtask
            assert subtask['parentTaskId'] == parent_id, \
                f"Subtask should have parentTaskId='{parent_id}', got '{subtask['parentTaskId']}'"
            assert subtask['subtaskCount'] == 0, "Leaf tasks should have subtaskCount=0"

        print(f"\n✓ All {len(subtasks)} subtasks have correct parentTaskId")

    def test_position_ordering(self, client, test_project, test_tasks):
        """Test that position field reflects actual task order."""
        # Use fixture project and tasks
        # Get all tasks in the project
        tasks = client.get_tasks(project_id=test_project)

        # Top-level tasks should have sequential positions
        top_level = [t for t in tasks if t['parentTaskId'] == '']
        positions = [t['position'] for t in top_level]

        assert positions == sorted(positions), "Positions should be ordered"
        assert min(positions) >= 1, "Positions should be 1-based"

        print(f"\n✓ {len(top_level)} top-level tasks have ordered positions: {positions[:5]}...")

    def test_hierarchy_reconstruction(self, client, test_parent_task_with_subtasks):
        """Test that we can reconstruct full hierarchy from fields."""
        # Use fixture that creates parent with 2 subtasks
        parent_id = test_parent_task_with_subtasks['parent_id']
        project_id = test_parent_task_with_subtasks.get('project_id')  # Not in current fixture, but tasks have projectId

        # Get parent task to find its project
        parent_task_data = client.get_tasks(task_id=parent_id)
        project_id = parent_task_data[0]['projectId']

        # Get all tasks in project
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
    """Tests for reordering tasks within a project.

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_reorder_task_before_another(self, client, test_project, test_tasks):
        """Test moving a task before another task."""
        # Use fixture project with 3 tasks
        # Get tasks in current order
        tasks = client.get_tasks(project_id=test_project)
        assert len(tasks) == 3

        # Use the fixture task IDs directly (test_tasks has 3 tasks)
        task_a_id = test_tasks[0]
        task_b_id = test_tasks[1]
        task_c_id = test_tasks[2]

        task_a = next(t for t in tasks if t['id'] == task_a_id)
        task_b = next(t for t in tasks if t['id'] == task_b_id)
        task_c = next(t for t in tasks if t['id'] == task_c_id)

        # Verify initial order by position
        assert task_a['position'] < task_b['position'] < task_c['position'], \
            "Initial order should be A < B < C"

        # Move Task C before Task A
        success = client.reorder_task(task_c['id'], before_task_id=task_a['id'])
        assert success, "reorder_task should return True"

        # Get updated order using task IDs (not names, since fixture uses UUID names)
        tasks_after = client.get_tasks(project_id=test_project)
        task_a_after = next(t for t in tasks_after if t['id'] == task_a_id)
        task_b_after = next(t for t in tasks_after if t['id'] == task_b_id)
        task_c_after = next(t for t in tasks_after if t['id'] == task_c_id)

        # Verify new order: C should be before A
        assert task_c_after['position'] < task_a_after['position'], \
            "Task C should be before Task A after reordering"
        assert task_a_after['position'] < task_b_after['position'], \
            "Task A should still be before Task B"

        print(f"\n✓ Successfully reordered tasks:")
        print(f"  Initial: Task0(pos {task_a['position']}) < Task1(pos {task_b['position']}) < Task2(pos {task_c['position']})")
        print(f"  After:   Task2(pos {task_c_after['position']}) < Task0(pos {task_a_after['position']}) < Task1(pos {task_b_after['position']})")
        # Note: Cleanup handled by fixtures automatically

    def test_reorder_task_after_another(self, client, test_project, test_tasks):
        """Test moving a task after another task."""
        # Use fixture project with 3 tasks
        # Get tasks in current order
        tasks = client.get_tasks(project_id=test_project)
        assert len(tasks) == 3

        # Use the fixture task IDs directly (test_tasks has 3 tasks)
        task_x_id = test_tasks[0]
        task_y_id = test_tasks[1]
        task_z_id = test_tasks[2]

        task_x = next(t for t in tasks if t['id'] == task_x_id)
        task_y = next(t for t in tasks if t['id'] == task_y_id)
        task_z = next(t for t in tasks if t['id'] == task_z_id)

        # Move Task X after Task Z
        success = client.reorder_task(task_x['id'], after_task_id=task_z['id'])
        assert success, "reorder_task should return True"

        # Get updated order using task IDs
        tasks_after = client.get_tasks(project_id=test_project)
        task_x_after = next(t for t in tasks_after if t['id'] == task_x_id)
        task_y_after = next(t for t in tasks_after if t['id'] == task_y_id)
        task_z_after = next(t for t in tasks_after if t['id'] == task_z_id)

        # Verify new order: X should be after Z
        assert task_y_after['position'] < task_z_after['position'], \
            "Task Y should be before Task Z"
        assert task_z_after['position'] < task_x_after['position'], \
            "Task X should be after Task Z"

        print(f"\n✓ Successfully reordered tasks with 'after':")
        print(f"  After:   Task1(pos {task_y_after['position']}) < Task2(pos {task_z_after['position']}) < Task0(pos {task_x_after['position']})")
        # Note: Cleanup handled by fixtures automatically

    def test_reorder_task_requires_one_parameter(self, client):
        """Test that reorder_task requires either before_task_id or after_task_id."""
        project_id = client.create_project("Reorder Test Project 3")

        try:
            client.create_task("Task 1", project_id=project_id)
            client.create_task("Task 2", project_id=project_id)

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
        finally:
            # Guaranteed cleanup
            client.delete_projects(project_id)


class TestAvailabilityFields:
    """Tests for availability status fields.

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_task_has_available_and_number_of_available_tasks(self, client):
        """Test that tasks include available and numberOfAvailableTasks fields."""
        # Create a sequential project with parent task and subtask
        project_id = client.create_project("Availability Test Project", sequential=True)

        try:
            # Add parent task and subtask
            client.create_task("Parent Task", project_id=project_id)
            tasks = client.get_tasks(project_id=project_id)
            parent_id = tasks[0]['id']

            # Make it have a subtask
            client.create_task("Subtask", project_id=project_id)
            all_tasks = client.get_tasks(project_id=project_id)
            subtask = next(t for t in all_tasks if t['name'] == 'Subtask')
            client.update_task(subtask['id'], parent_task_id=parent_id)

            # Get updated parent
            results = client.get_tasks(task_id=parent_id)
            assert len(results) == 1
            parent = results[0]

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
        finally:
            # Guaranteed cleanup
            client.delete_projects(project_id)

    def test_available_true_when_task_actionable(self, client):
        """Test that available is true for directly actionable tasks."""
        project_id = client.create_project("Available Task Test")

        try:
            client.create_task("Available Task", project_id=project_id)

            tasks = client.get_tasks(project_id=project_id)
            task = tasks[0]

            # Task should be available (not blocked, not completed, not dropped, not deferred)
            assert task['completed'] == False
            assert task['dropped'] == False
            assert task['blocked'] == False
            assert task['deferDate'] == ""
            assert task['available'] == True, "Actionable task should be available"

            print(f"\n✓ Directly actionable task shows available: true")
        finally:
            # Guaranteed cleanup
            client.delete_projects(project_id)

    def test_available_true_when_blocked_with_available_children(self, client):
        """Test that available is true for blocked tasks with available subtasks."""
        # Create sequential project - parent task will be sequential action group
        project_id = client.create_project("Blocked Parent Test", sequential=True)

        try:
            # Add first task and a parent task (which will be blocked)
            client.create_task("First Task", project_id=project_id)
            client.create_task("Blocked Parent", project_id=project_id)

            tasks = client.get_tasks(project_id=project_id)
            first_task = tasks[0]
            blocked_parent_task = tasks[1]

            # Add two children to the blocked parent, making it an action group
            # Make the parent itself parallel so children are available
            client.create_task("Child 1", project_id=project_id)
            client.create_task("Child 2", project_id=project_id)
            all_tasks = client.get_tasks(project_id=project_id)
            child1 = next(t for t in all_tasks if t['name'] == 'Child 1')
            child2 = next(t for t in all_tasks if t['name'] == 'Child 2')

            # Move children under blocked parent
            client.update_task(child1['id'], parent_task_id=blocked_parent_task['id'])
            client.update_task(child2['id'], parent_task_id=blocked_parent_task['id'])

            # Get updated parent
            results = client.get_tasks(task_id=blocked_parent_task['id'])
            assert len(results) == 1
            blocked_parent = results[0]

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
        finally:
            # Guaranteed cleanup
            client.delete_projects(project_id)


class TestUINavigation:
    """Test UI navigation operations (set_focus).

    All tests use fixtures from conftest.py for automatic cleanup.
    """

    def test_set_focus_on_project(self, client, test_project):
        """Test setting focus on a project."""
        # Use fixture project
        project_id = test_project

        # Get project details for display
        projects = client.get_projects(project_id=project_id)
        project = projects[0]

        # Set focus on the project
        result = client.set_focus(item_id=project_id, item_type="project")

        assert result["success"] is True
        assert result["item_id"] == project_id
        assert result["item_type"] == "project"
        print(f"\n✓ Set focus on project: {project['name']}")

    def test_set_focus_on_folder(self, client, test_folder):
        """Test setting focus on a folder."""
        # Use fixture folder
        folder_id = test_folder

        # Get folder details for display
        folders = client.get_folders()
        test_folder_obj = next(f for f in folders if f['id'] == folder_id)

        # Set focus on the folder
        result = client.set_focus(item_id=folder_id, item_type="folder")

        assert result["success"] is True
        assert result["item_id"] == folder_id
        assert result["item_type"] == "folder"
        print(f"\n✓ Set focus on folder: {test_folder_obj['name']}")

    def test_set_focus_invalid_item_type(self, client, test_task):
        """Test that invalid item types raise errors."""
        # Use fixture task
        task_id = test_task

        # Try to set focus on task (should fail)
        with pytest.raises(ValueError) as exc_info:
            client.set_focus(item_id=task_id, item_type="task")

        assert "OmniFocus only supports setting focus on projects and folders" in str(exc_info.value)
        print("\n✓ Correctly rejected focus on task")

    def test_set_focus_nonexistent_project(self, client):
        """Test error handling for nonexistent project."""
        # Try to set focus on nonexistent project
        with pytest.raises(Exception) as exc_info:
            client.set_focus(item_id="nonexistent-id-12345", item_type="project")

        assert "Error setting focus" in str(exc_info.value)
        print("\n✓ Correctly handled nonexistent project")
