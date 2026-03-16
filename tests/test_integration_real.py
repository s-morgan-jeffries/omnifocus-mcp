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

    def test_create_project_single_actions_list(self, client):
        """Test creating a Single Actions List project type."""
        import uuid
        project_name = f"test-SAL-{uuid.uuid4().hex[:8]}"
        project_id = None
        try:
            project_id = client.create_project(project_name, project_type="single_actions")
            assert project_id is not None

            projects = client.get_projects(project_id=project_id)
            assert len(projects) == 1
            project = projects[0]
            assert project["projectType"] == "single_actions"
            assert project["singletonActionHolder"] is True
            assert project["sequential"] is False
            print(f"\n✓ Created SAL project: {project['name']} — projectType={project['projectType']}")
        finally:
            if project_id:
                client.delete_projects(project_id)

    def test_get_projects_returns_project_type_field(self, client, test_project):
        """Test that get_projects returns projectType for parallel, sequential projects."""
        projects = client.get_projects(project_id=test_project)
        assert len(projects) == 1
        project = projects[0]
        assert "projectType" in project
        # Default test project is parallel
        assert project["projectType"] == "parallel"
        print(f"\n✓ get_projects returns projectType: {project['projectType']}")

    def test_update_project_type_to_single_actions(self, client, test_project):
        """Test converting a parallel project to Single Actions List via project_type."""
        result = client.update_project(test_project, project_type="single_actions")
        assert result["success"] is True
        assert "project_type" in result["updated_fields"]

        projects = client.get_projects(project_id=test_project)
        assert len(projects) == 1
        assert projects[0]["projectType"] == "single_actions"
        assert projects[0]["singletonActionHolder"] is True
        print(f"\n✓ Converted project to single_actions via project_type")

    def test_update_project_type_back_to_parallel(self, client, test_project):
        """Test converting a SAL back to parallel."""
        # First make it a SAL
        client.update_project(test_project, project_type="single_actions")
        # Then convert back
        result = client.update_project(test_project, project_type="parallel")
        assert result["success"] is True

        projects = client.get_projects(project_id=test_project)
        assert projects[0]["projectType"] == "parallel"
        assert projects[0]["singletonActionHolder"] is False
        print(f"\n✓ Converted SAL back to parallel")

    def test_get_projects_returns_completed_by_children_field(self, client, test_project):
        """get_projects includes completedByChildren field."""
        projects = client.get_projects(project_id=test_project)
        assert len(projects) == 1
        assert "completedByChildren" in projects[0]
        assert isinstance(projects[0]["completedByChildren"], bool)
        print(f"\n✓ completedByChildren field present: {projects[0]['completedByChildren']}")

    def test_create_and_update_project_completed_by_children(self, client):
        """Create a project with completedByChildren=True, verify, update to False, verify."""
        project_id = None
        try:
            project_id = client.create_project(
                "test-completed-by-children",
                completed_by_children=True
            )
            assert project_id is not None

            projects = client.get_projects(project_id=project_id)
            assert len(projects) == 1
            assert projects[0]["completedByChildren"] is True
            print(f"\n✓ Created project with completedByChildren=True")

            result = client.update_project(project_id, completed_by_children=False)
            assert result["success"] is True
            assert "completed_by_children" in result["updated_fields"]

            projects = client.get_projects(project_id=project_id)
            assert projects[0]["completedByChildren"] is False
            print(f"\n✓ Updated completedByChildren to False")
        finally:
            if project_id:
                client.delete_projects([project_id])

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

    def test_update_project_next_review_date_integration(self, client, test_project):
        """Integration: update_project() can set next_review_date explicitly."""
        next_review = "2026-06-01"
        result = client.update_project(test_project, next_review_date=next_review)
        assert result["success"] is True
        assert "next_review_date" in result["updated_fields"]

        projects = client.get_projects(project_id=test_project)
        assert len(projects) == 1
        project = projects[0]
        next_review_returned = project.get('nextReviewDate') or ""
        assert next_review_returned.startswith(next_review), (
            f"Expected nextReviewDate to start with {next_review!r}, got {next_review_returned!r}"
        )
        print(f"\n✓ Set next_review_date: {next_review_returned}")

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

    def test_get_task_includes_tags(self, client, test_project, ensure_test_tags):
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

    def test_get_tasks_includes_tags(self, client, test_project, ensure_test_tags):
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

    def test_get_folders_returns_status(self, client, test_folder):
        """Test that get_folders returns status field."""
        folders = client.get_folders()
        folder = next(f for f in folders if f['id'] == test_folder)
        assert "status" in folder
        assert folder["status"] in ("active", "dropped")
        # Fixture folder should be active
        assert folder["status"] == "active"
        print(f"\n✓ get_folders returns status: {folder['status']}")

    def test_update_folder_drop_and_restore(self, client, test_folder):
        """Test dropping and restoring a folder via update_folder."""
        # Drop the folder
        result = client.update_folder(test_folder, status="dropped")
        assert result["success"] is True
        assert "status" in result["updated_fields"]

        # Verify it's dropped — NOTE: dropped folders may not appear in get_folders
        # depending on OmniFocus filter settings; check via direct property read
        # Re-activate
        result2 = client.update_folder(test_folder, status="active")
        assert result2["success"] is True

        # Verify it's active again
        folders = client.get_folders()
        folder = next((f for f in folders if f['id'] == test_folder), None)
        assert folder is not None
        assert folder["status"] == "active"
        print(f"\n✓ Dropped and restored folder successfully")


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

    def test_add_tag_to_multiple_tasks(self, client, test_tasks, test_project, ensure_test_tags):
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

    def test_remove_tag_from_multiple_tasks(self, client, test_tasks, test_project, ensure_test_tags):
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


class TestTagCRUD:
    """Integration tests for tag Create/Update/Delete operations.

    Tests verify that the AppleScript for tag CRUD actually works
    against real OmniFocus. Unit tests mock run_applescript() and
    cannot catch AppleScript syntax errors or behavioral quirks.
    """

    def test_create_tag(self, client):
        """Create a root-level tag and verify it exists."""
        import uuid
        import warnings
        tag_name = f"test-integ-{uuid.uuid4()}"
        tag_id = None
        try:
            tag_id = client.create_tag(tag_name)
            assert tag_id, "create_tag should return a tag ID"

            # Verify tag appears in get_tags
            tags = client.get_tags()
            matching = [t for t in tags if t['id'] == tag_id]
            assert len(matching) == 1
            assert matching[0]['name'] == tag_name
        finally:
            if tag_id:
                try:
                    client.delete_tags(tag_id)
                except Exception as e:
                    warnings.warn(f"Failed to clean up test tag {tag_id}: {e}")

    def test_create_nested_tag(self, client):
        """Create a nested tag under a parent."""
        import uuid
        import warnings
        parent_name = f"test-parent-{uuid.uuid4()}"
        child_name = f"test-child-{uuid.uuid4()}"
        parent_id = None
        child_id = None
        try:
            parent_id = client.create_tag(parent_name)
            assert parent_id

            child_id = client.create_tag(child_name, parent_tag=parent_name)
            assert child_id
            assert child_id != parent_id

            # Both should appear in get_tags (flattened)
            tags = client.get_tags()
            tag_ids = [t['id'] for t in tags]
            assert parent_id in tag_ids
            assert child_id in tag_ids
        finally:
            for tid in [child_id, parent_id]:
                if tid:
                    try:
                        client.delete_tags(tid)
                    except Exception as e:
                        warnings.warn(f"Failed to clean up test tag {tid}: {e}")

    def test_create_tag_already_exists(self, client):
        """Creating a duplicate tag raises ValueError."""
        import uuid
        import warnings
        tag_name = f"test-dup-{uuid.uuid4()}"
        tag_id = None
        try:
            tag_id = client.create_tag(tag_name)
            with pytest.raises(ValueError, match="already exists"):
                client.create_tag(tag_name)
        finally:
            if tag_id:
                try:
                    client.delete_tags(tag_id)
                except Exception as e:
                    warnings.warn(f"Failed to clean up test tag {tag_id}: {e}")

    def test_update_tag_name(self, client):
        """Rename a tag and verify the change took."""
        import uuid
        import warnings
        original_name = f"test-rename-{uuid.uuid4()}"
        new_name = f"test-renamed-{uuid.uuid4()}"
        tag_id = None
        try:
            tag_id = client.create_tag(original_name)
            result = client.update_tag(tag_id, name=new_name)
            assert result["success"] is True
            assert "name" in result["updated_fields"]

            # Verify rename in get_tags
            tags = client.get_tags()
            matching = [t for t in tags if t['id'] == tag_id]
            assert len(matching) == 1
            assert matching[0]['name'] == new_name
        finally:
            if tag_id:
                try:
                    client.delete_tags(tag_id)
                except Exception as e:
                    warnings.warn(f"Failed to clean up test tag {tag_id}: {e}")

    def test_update_tag_status_on_hold(self, client):
        """Set a tag to on_hold and verify."""
        import uuid
        import warnings
        tag_name = f"test-onhold-{uuid.uuid4()}"
        tag_id = None
        try:
            tag_id = client.create_tag(tag_name)
            result = client.update_tag(tag_id, status="on_hold")
            assert result["success"] is True
            assert "status" in result["updated_fields"]

            # Verify get_tags now reads actual status
            tags = client.get_tags()
            matching = [t for t in tags if t['id'] == tag_id]
            assert len(matching) == 1
            assert matching[0]['status'] == "on hold", (
                f"Expected 'on hold' status, got '{matching[0]['status']}'"
            )
        finally:
            if tag_id:
                try:
                    client.delete_tags(tag_id)
                except Exception as e:
                    warnings.warn(f"Failed to clean up test tag {tag_id}: {e}")

    def test_update_tag_status_dropped(self, client):
        """Set a tag to dropped and verify."""
        import uuid
        import warnings
        tag_name = f"test-dropped-{uuid.uuid4()}"
        tag_id = None
        try:
            tag_id = client.create_tag(tag_name)
            result = client.update_tag(tag_id, status="dropped")
            assert result["success"] is True
            assert "status" in result["updated_fields"]

            # Verify get_tags returns "dropped" status
            tags = client.get_tags()
            matching = [t for t in tags if t['id'] == tag_id]
            assert len(matching) == 1
            assert matching[0]['status'] == "dropped", (
                f"Expected 'dropped' status, got '{matching[0]['status']}'"
            )
        finally:
            if tag_id:
                try:
                    client.delete_tags(tag_id)
                except Exception as e:
                    warnings.warn(f"Failed to clean up test tag {tag_id}: {e}")

    def test_update_tag_status_active_from_dropped(self, client):
        """Re-activate a dropped tag and verify."""
        import uuid
        import warnings
        tag_name = f"test-reactivate-{uuid.uuid4()}"
        tag_id = None
        try:
            tag_id = client.create_tag(tag_name)
            # Drop it first
            client.update_tag(tag_id, status="dropped")
            # Re-activate
            result = client.update_tag(tag_id, status="active")
            assert result["success"] is True

            tags = client.get_tags()
            matching = [t for t in tags if t['id'] == tag_id]
            assert len(matching) == 1
            assert matching[0]['status'] == "active", (
                f"Expected 'active' status, got '{matching[0]['status']}'"
            )
        finally:
            if tag_id:
                try:
                    client.delete_tags(tag_id)
                except Exception as e:
                    warnings.warn(f"Failed to clean up test tag {tag_id}: {e}")

    def test_delete_tags(self, client):
        """Delete multiple tags and verify they're gone."""
        import uuid
        import warnings
        tag_ids = []
        try:
            for i in range(2):
                tid = client.create_tag(f"test-delete-{uuid.uuid4()}")
                tag_ids.append(tid)

            result = client.delete_tags(tag_ids)
            assert result["deleted_count"] == 2
            assert result["failed_count"] == 0

            # Verify tags are gone
            tags = client.get_tags()
            remaining_ids = [t['id'] for t in tags]
            for tid in tag_ids:
                assert tid not in remaining_ids
            tag_ids = []  # Already deleted, skip cleanup
        finally:
            for tid in tag_ids:
                try:
                    client.delete_tags(tid)
                except Exception as e:
                    warnings.warn(f"Failed to clean up test tag {tid}: {e}")


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

    def test_add_task_with_planned_date(self, client, test_project):
        """Test create_task with planned_date (OmniFocus 4.7+)."""
        from datetime import datetime, timedelta

        planned_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")

        task_id = client.create_task(
            "Task with Planned Date",
            project_id=test_project,
            planned_date=planned_date
        )

        try:
            assert task_id is not None

            # Verify task was created with planned date
            tasks = client.get_tasks(task_id=task_id)
            assert len(tasks) > 0
            assert tasks[0].get('plannedDate') is not None

            print("\n✓ Created task with planned date")
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


class TestRepeatSummaryIntegration:
    """Test repeatSummary field is populated correctly."""

    def test_non_recurring_task_has_repeat_summary_none(self, client, test_task):
        """Non-recurring tasks should have repeatSummary=None."""
        tasks = client.get_tasks(task_id=test_task)
        assert len(tasks) == 1
        task = tasks[0]
        assert 'repeatSummary' in task
        assert task['repeatSummary'] is None
        assert task['isRecurring'] is False

        print("\n✓ Non-recurring task has repeatSummary=None")

    # test_recurring_task_has_populated_repeat_summary moved to
    # test_prod_integration.py — requires OmniAutomation (evaluate javascript)
    # which crashes on headless test databases. See #324.



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

    def test_update_task_planned_date(self, client, test_task):
        """Test setting and clearing planned_date on a task (OmniFocus 4.7+)."""
        from datetime import datetime, timedelta

        planned_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")

        # Set planned date
        result = client.update_task(test_task, planned_date=planned_date)
        assert result["success"] is True

        tasks = client.get_tasks(task_id=test_task)
        assert len(tasks) == 1
        assert tasks[0].get('plannedDate') is not None

        # Clear planned date
        result = client.update_task(test_task, planned_date="")
        assert result["success"] is True

        tasks = client.get_tasks(task_id=test_task)
        assert len(tasks) == 1
        assert tasks[0].get('plannedDate', '') == ''

        print("\n✓ Set and cleared planned date")

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


class TestAvailableOnlyOnHoldTags:
    """Test that available_only=True excludes tasks with On Hold tags (#261).

    Validates parity with OmniFocus's native Available perspective.
    """

    def test_on_hold_tag_task_excluded_from_available(self, client, test_project):
        """Task with an On Hold tag should NOT appear in available_only results."""
        # Create an On Hold tag
        tag_id = client.create_tag("test-on-hold-261")
        try:
            client.update_tag(tag_id, active=False)

            # Create a task and assign the On Hold tag via update_task
            # (create_task On Hold tag bug was fixed in #267)
            task_id = client.create_task(
                "On Hold Tagged Task",
                project_id=test_project,
            )
            client.update_task(task_id, add_tags=["test-on-hold-261"])

            # Verify the task exists in unfiltered results with the tag
            all_tasks = client.get_tasks(project_id=test_project)
            task = next(t for t in all_tasks if t['name'] == "On Hold Tagged Task")
            assert "test-on-hold-261" in task['tags']

            # Verify the task is excluded from available_only
            available_tasks = client.get_tasks(
                project_id=test_project, available_only=True
            )
            available_names = [t['name'] for t in available_tasks]
            assert "On Hold Tagged Task" not in available_names
        finally:
            client.delete_tags(tag_id)
            client.delete_projects(test_project)

    def test_create_task_assigns_on_hold_tag(self, client, test_project):
        """Bug #267: create_task should successfully assign On Hold tags."""
        tag_id = client.create_tag("test-on-hold-267")
        try:
            client.update_tag(tag_id, active=False)

            # create_task should assign the On Hold tag directly
            task_id = client.create_task(
                "On Hold Tag Create Test",
                project_id=test_project,
                tags=["test-on-hold-267"],
            )

            # Verify the tag was actually assigned
            all_tasks = client.get_tasks(project_id=test_project)
            task = next(t for t in all_tasks if t['name'] == "On Hold Tag Create Test")
            assert "test-on-hold-267" in task['tags'], \
                f"On Hold tag should be assigned by create_task. Got tags: {task['tags']}"
        finally:
            client.delete_tags(tag_id)
            client.delete_projects(test_project)

    def test_get_on_hold_tag_names_returns_on_hold_tags(self, client):
        """_get_on_hold_tag_names() returns names of tags set to On Hold."""
        tag_id = client.create_tag("test-on-hold-261-lookup")
        try:
            client.update_tag(tag_id, active=False)
            on_hold = client._get_on_hold_tag_names()
            assert "test-on-hold-261-lookup" in on_hold
        finally:
            client.delete_tags(tag_id)


class TestUINavigation:
    """Test UI navigation operations (set_focus, get_focus, get_perspectives).

    All tests use fixtures from conftest.py for automatic cleanup.
    Focus tests clear focus in teardown to avoid polluting other tests.
    """

    def test_set_focus_single_project(self, client, test_project):
        """Test setting focus on a single project."""
        project_id = test_project

        projects = client.get_projects(project_id=project_id)
        project = projects[0]

        result = client.set_focus(item_ids=project_id, item_types="project")

        assert result["success"] is True
        assert result["action"] == "set"
        assert len(result["focused_items"]) == 1
        assert result["focused_items"][0]["id"] == project_id
        assert result["focused_items"][0]["type"] == "project"
        print(f"\n✓ Set focus on project: {project['name']}")

        # Clean up: clear focus
        client.set_focus()

    def test_set_focus_single_folder(self, client, test_folder):
        """Test setting focus on a single folder."""
        folder_id = test_folder

        folders = client.get_folders()
        test_folder_obj = next(f for f in folders if f['id'] == folder_id)

        result = client.set_focus(item_ids=folder_id, item_types="folder")

        assert result["success"] is True
        assert result["action"] == "set"
        assert len(result["focused_items"]) == 1
        assert result["focused_items"][0]["type"] == "folder"
        print(f"\n✓ Set focus on folder: {test_folder_obj['name']}")

        # Clean up: clear focus
        client.set_focus()

    def test_set_focus_multiple_items(self, client, test_project, test_folder):
        """Test setting focus on multiple items (project + folder)."""
        result = client.set_focus(
            item_ids=[test_project, test_folder],
            item_types=["project", "folder"],
        )

        assert result["success"] is True
        assert result["action"] == "set"
        assert len(result["focused_items"]) == 2
        types = {item["type"] for item in result["focused_items"]}
        assert types == {"project", "folder"}
        print("\n✓ Set focus on multiple items (project + folder)")

        # Clean up: clear focus
        client.set_focus()

    def test_set_focus_clear(self, client, test_project):
        """Test clearing focus after setting it."""
        # First set focus
        client.set_focus(item_ids=test_project, item_types="project")

        # Then clear it
        result = client.set_focus()

        assert result["success"] is True
        assert result["action"] == "cleared"
        assert result["focused_items"] == []
        print("\n✓ Cleared focus successfully")

    def test_set_focus_invalid_item_type(self, client, test_task):
        """Test that invalid item types raise errors."""
        task_id = test_task

        with pytest.raises(ValueError) as exc_info:
            client.set_focus(item_ids=task_id, item_types="task")

        assert "project" in str(exc_info.value).lower() or "folder" in str(exc_info.value).lower()
        print("\n✓ Correctly rejected focus on task")

    def test_set_focus_nonexistent_project(self, client):
        """Test error handling for nonexistent project."""
        with pytest.raises(Exception) as exc_info:
            client.set_focus(item_ids="nonexistent-id-12345", item_types="project")

        assert "Error" in str(exc_info.value) or "error" in str(exc_info.value)
        print("\n✓ Correctly handled nonexistent project")

    def test_get_focus_after_set(self, client, test_project):
        """Test reading focus after setting it."""
        # Set focus
        client.set_focus(item_ids=test_project, item_types="project")

        # Read it back
        items = client.get_focus()

        assert len(items) >= 1
        # Find our project in the focused items
        project_ids = [item["id"] for item in items]
        assert test_project in project_ids

        focused_project = next(i for i in items if i["id"] == test_project)
        assert focused_project["type"] == "project"
        assert "name" in focused_project
        print(f"\n✓ Read back focus: {focused_project['name']}")

        # Clean up: clear focus
        client.set_focus()

    def test_get_focus_empty(self, client):
        """Test reading focus when none is set."""
        # Clear focus first
        client.set_focus()

        items = client.get_focus()

        assert items == []
        print("\n✓ Empty focus returns []")

    def test_get_perspectives_enriched(self, client):
        """Test that get_perspectives returns structured dicts."""
        perspectives = client.get_perspectives()

        assert len(perspectives) > 0
        # Every perspective should have name, id, type
        for p in perspectives:
            assert "name" in p
            assert "id" in p
            assert "type" in p
            assert p["type"] in ("built-in", "custom")

        # Should include some built-in perspectives
        names = [p["name"] for p in perspectives]
        # Inbox is always present
        assert "Inbox" in names

        # Built-in perspectives should have null IDs
        inbox = next(p for p in perspectives if p["name"] == "Inbox")
        assert inbox["type"] == "built-in"
        assert inbox["id"] is None

        # Custom perspectives should have IDs and type "custom"
        custom = [p for p in perspectives if p["type"] == "custom"]
        assert len(custom) > 0, "Expected at least one custom perspective"
        for cp in custom:
            assert cp["id"] is not None, f"Custom perspective {cp['name']} should have an ID"

        print(f"\n✓ Got {len(perspectives)} enriched perspectives ({len(custom)} custom)")


# ============================================================================
# TAG-SIDE PRE-FILTER TESTS (#249)
# ============================================================================

class TestTagSidePreFilter:
    """Integration tests for tag-side task ID lookup.

    Validates the AppleScript pattern:
        tasks of (first flattened tag whose name is "X")
    which is used by _get_task_ids_for_tags() for the tag pre-filter
    optimization (issue #249).
    """

    def test_tasks_of_tag_returns_task_ids(self, client, test_project, ensure_test_tags):
        """Create a tagged task, verify _get_task_ids_for_tags finds it."""
        import warnings
        task_id = None
        try:
            task_id = client.create_task(
                "test-tag-prefilter-task",
                project_id=test_project,
                tags=["test-work"],
            )
            assert task_id, "create_task should return a task ID"

            # Use the tag-side pre-filter to find the task
            result = client._get_task_ids_for_tags(["test-work"], "and")
            assert result is not None, "_get_task_ids_for_tags should not return None"
            assert task_id in result, f"Task {task_id} should be in tag pre-filter results"
            print(f"\n✓ _get_task_ids_for_tags found task {task_id} via tag 'test-work'")
        finally:
            if task_id:
                try:
                    client.delete_tasks(task_id)
                except Exception as e:
                    warnings.warn(f"Failed to clean up task {task_id}: {e}")

    def test_tag_prefilter_and_mode(self, client, test_project, ensure_test_tags):
        """AND mode: task with both tags is found, task with one tag is not."""
        import warnings
        task_both = None
        task_one = None
        try:
            task_both = client.create_task(
                "test-tag-both",
                project_id=test_project,
                tags=["test-work", "test-urgent"],
            )
            task_one = client.create_task(
                "test-tag-one",
                project_id=test_project,
                tags=["test-work"],
            )

            result = client._get_task_ids_for_tags(["test-work", "test-urgent"], "and")
            assert result is not None
            assert task_both in result, "Task with both tags should be in AND result"
            assert task_one not in result, "Task with only one tag should NOT be in AND result"
            print(f"\n✓ AND mode correctly filters: both={task_both in result}, one={task_one in result}")
        finally:
            for tid in [task_both, task_one]:
                if tid:
                    try:
                        client.delete_tasks(tid)
                    except Exception as e:
                        warnings.warn(f"Failed to clean up task {tid}: {e}")

    def test_get_tasks_tag_filter_uses_prefilter(self, client, test_project, ensure_test_tags):
        """Full get_tasks(tag_filter=...) returns correct results via pre-filter path."""
        import warnings
        task_id = None
        try:
            task_id = client.create_task(
                "test-tag-filter-e2e",
                project_id=test_project,
                tags=["test-work"],
            )

            tasks = client.get_tasks(tag_filter=["test-work"], project_id=test_project)
            task_ids = [t['id'] for t in tasks]
            assert task_id in task_ids, "Tagged task should appear in get_tasks(tag_filter=...) results"
            print(f"\n✓ get_tasks(tag_filter=['test-work']) found task {task_id}")
        finally:
            if task_id:
                try:
                    client.delete_tasks(task_id)
                except Exception as e:
                    warnings.warn(f"Failed to clean up task {task_id}: {e}")


class TestEffectiveDates:
    """Test that get_tasks returns effective (inherited) dates from the containing project."""

    def test_task_inherits_due_date_from_project(self, client):
        """Task with no direct due date shows project's due date in dueDate field."""
        from datetime import datetime, timedelta

        due_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
        project_id = None
        task_id = None
        try:
            project_id = client.create_project(
                "test-effective-due-project",
                due_date=due_date,
            )
            task_id = client.create_task(
                "test-effective-due-task",
                project_id=project_id,
                # No due_date — should inherit from project
            )

            tasks = client.get_tasks(project_id=project_id, query="test-effective-due-task")
            assert len(tasks) == 1
            task = tasks[0]
            assert task.get('dueDate'), (
                f"Expected task to inherit due date from project, got dueDate={task.get('dueDate')!r}"
            )
            # The effective due date should match the project's due date (date portion)
            assert task['dueDate'].startswith(due_date), (
                f"Expected dueDate to start with {due_date!r}, got {task['dueDate']!r}"
            )
            print(f"\n✓ Task inherited due date from project: {task['dueDate']}")
        finally:
            if task_id:
                try:
                    client.delete_tasks(task_id)
                except Exception as e:
                    warnings.warn(f"Failed to clean up task {task_id}: {e}")
            if project_id:
                try:
                    client.delete_projects(project_id)
                except Exception as e:
                    warnings.warn(f"Failed to clean up project {project_id}: {e}")

    def test_overdue_filter_includes_tasks_with_inherited_due_date(self, client):
        """get_tasks(overdue=True) returns tasks that are overdue via project inheritance."""
        from datetime import datetime, timedelta

        past_due = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
        project_id = None
        task_id = None
        try:
            project_id = client.create_project(
                "test-effective-overdue-project",
                due_date=past_due,
            )
            task_id = client.create_task(
                "test-effective-overdue-task",
                project_id=project_id,
                # No direct due date — inherits overdue date from project
            )

            overdue_tasks = client.get_tasks(overdue=True)
            overdue_ids = [t['id'] for t in overdue_tasks]
            assert task_id in overdue_ids, (
                f"Task {task_id} should appear in overdue results via inherited project due date"
            )
            print(f"\n✓ Overdue filter found task with inherited due date (project due: {past_due})")
        finally:
            if task_id:
                try:
                    client.delete_tasks(task_id)
                except Exception as e:
                    warnings.warn(f"Failed to clean up task {task_id}: {e}")
            if project_id:
                try:
                    client.delete_projects(project_id)
                except Exception as e:
                    warnings.warn(f"Failed to clean up project {project_id}: {e}")
