"""Tests for FastMCP server."""
import pytest
from unittest import mock

# Import the server module to access tool functions
import omnifocus_mcp.server_fastmcp as server

# Extract underlying functions from FunctionTool wrappers
get_client = server.get_client
get_projects = server.get_projects.fn
get_project = server.get_project.fn
create_project = server.create_project.fn
update_project = server.update_project.fn
set_project_status = server.set_project_status.fn
get_stalled_projects = server.get_stalled_projects.fn
get_tasks = server.get_tasks.fn
get_task = server.get_task.fn
get_subtasks = server.get_subtasks.fn
add_task = server.add_task.fn
update_task = server.update_task.fn
complete_task = server.complete_task.fn
delete_task = server.delete_task.fn
delete_project = server.delete_project.fn
move_task = server.move_task.fn
drop_task = server.drop_task.fn
create_inbox_task = server.create_inbox_task.fn
get_tags = server.get_tags.fn
add_tag_to_task = server.add_tag_to_task.fn
add_note = server.add_note.fn
get_note = server.get_note.fn
get_folders = server.get_folders.fn
create_folder = server.create_folder.fn
set_parent_task = server.set_parent_task.fn
set_review_interval = server.set_review_interval.fn
mark_project_reviewed = server.mark_project_reviewed.fn
get_projects_due_for_review = server.get_projects_due_for_review.fn
set_estimated_minutes = server.set_estimated_minutes.fn
get_perspectives = server.get_perspectives.fn
switch_perspective = server.switch_perspective.fn
complete_tasks = server.complete_tasks.fn
move_tasks = server.move_tasks.fn
add_tag_to_tasks = server.add_tag_to_tasks.fn
remove_tag_from_tasks = server.remove_tag_from_tasks.fn
drop_tasks = server.drop_tasks.fn
delete_tasks = server.delete_tasks.fn
delete_projects = server.delete_projects.fn


@pytest.fixture(autouse=True)
def reset_client():
    """Reset the global client before each test."""
    import omnifocus_mcp.server_fastmcp as server_module
    server_module._client = None
    yield
    server_module._client = None


class TestGetClient:
    """Tests for get_client function."""

    def test_get_client_creates_client(self):
        """Test that get_client creates a client instance."""
        client = get_client()
        assert client is not None

    def test_get_client_reuses_instance(self):
        """Test that get_client returns the same instance."""
        client1 = get_client()
        client2 = get_client()
        assert client1 is client2

    def test_get_client_disables_safety_in_pytest(self):
        """Test that safety checks are disabled when running in pytest."""
        import os
        os.environ['PYTEST_CURRENT_TEST'] = 'test'
        client = get_client()
        assert client._safety_checks_enabled is False
        del os.environ['PYTEST_CURRENT_TEST']


class TestProjectTools:
    """Tests for project-related tools."""

    def test_get_projects_success(self):
        """Test get_projects with successful result."""
        mock_projects = [
            {"id": "proj-001", "name": "Test Project", "status": "active"}
        ]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_projects.return_value = mock_projects
            mock_get_client.return_value = mock_client

            result = get_projects()

            assert "Found 1 active projects" in result
            assert "Test Project" in result
            mock_client.get_projects.assert_called_once()

    def test_get_projects_empty(self):
        """Test get_projects with no projects."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_projects.return_value = []
            mock_get_client.return_value = mock_client

            result = get_projects()

            assert "Found 0 active projects" in result

    def test_search_projects_success(self):
        """Test get_projects with query parameter."""
        mock_projects = [
            {"id": "proj-001", "name": "Budget Project", "status": "active"}
        ]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_projects.return_value = mock_projects
            mock_get_client.return_value = mock_client

            result = get_projects(query="budget")

            assert "Found 1 projects matching 'budget'" in result
            assert "Budget Project" in result
            mock_client.get_projects.assert_called_once_with(on_hold_only=False, query="budget")

    def test_get_project_success(self):
        """Test get_project with successful retrieval."""
        mock_project = {
            "id": "proj-001",
            "name": "Test Project",
            "note": "Project note",
            "status": "active",
            "folderPath": "Work > Tests"
        }

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_project.return_value = mock_project
            mock_get_client.return_value = mock_client

            result = get_project("proj-001")

            assert "Project Details:" in result
            assert "Test Project" in result
            assert "Status: active" in result
            assert "Folder: Work > Tests" in result
            mock_client.get_project.assert_called_once_with("proj-001")

    def test_create_project_success(self):
        """Test create_project with successful creation."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_project.return_value = "proj-new-001"
            mock_get_client.return_value = mock_client

            result = create_project("New Project")

            assert "Successfully created project 'New Project'" in result
            assert "proj-new-001" in result

    def test_create_project_with_folder(self):
        """Test create_project with folder path."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_project.return_value = "proj-new-002"
            mock_get_client.return_value = mock_client

            result = create_project("New Project", folder_path="Work")

            assert "Successfully created project 'New Project'" in result
            assert "Folder: Work" in result
            mock_client.create_project.assert_called_once_with(
                name="New Project", note=None, folder_path="Work", sequential=False
            )

    def test_set_project_status_to_active(self):
        """Test set_project_status setting status to active."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.set_project_status.return_value = True
            mock_get_client.return_value = mock_client

            result = set_project_status("proj-123", "active")

            assert "Successfully set project status to: Active" in result
            mock_client.set_project_status.assert_called_once_with("proj-123", "active")

    def test_set_project_status_to_on_hold(self):
        """Test set_project_status setting status to on_hold."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.set_project_status.return_value = True
            mock_get_client.return_value = mock_client

            result = set_project_status("proj-123", "on_hold")

            assert "Successfully set project status to: On Hold" in result
            mock_client.set_project_status.assert_called_once_with("proj-123", "on_hold")

    def test_set_project_status_to_done(self):
        """Test set_project_status setting status to done."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.set_project_status.return_value = True
            mock_get_client.return_value = mock_client

            result = set_project_status("proj-123", "done")

            assert "Successfully set project status to: Done" in result
            mock_client.set_project_status.assert_called_once_with("proj-123", "done")

    def test_set_project_status_project_not_found(self):
        """Test set_project_status raises ValueError when project not found."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.set_project_status.side_effect = ValueError("Project with ID nonexistent not found")
            mock_get_client.return_value = mock_client

            with pytest.raises(ValueError, match="Project.*not found"):
                set_project_status("nonexistent", "active")

    def test_get_stalled_projects_success(self):
        """Test get_stalled_projects with results."""
        mock_projects = [
            {
                "id": "proj-stale-1",
                "name": "Stale Project",
                "status": "active",
                "lastActivityDate": "2024-08-01T00:00:00Z",
                "daysInactive": 68,
                "taskCount": 3
            }
        ]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_stalled_projects.return_value = mock_projects
            mock_get_client.return_value = mock_client

            result = get_stalled_projects()

            assert "Found 1 stalled projects" in result
            assert "Stale Project" in result
            assert "68 days inactive" in result

    def test_get_stalled_projects_custom_threshold(self):
        """Test get_stalled_projects with custom threshold."""
        mock_projects = [
            {
                "id": "proj-1",
                "name": "Project 1",
                "status": "active",
                "lastActivityDate": "2025-09-20T00:00:00Z",
                "daysInactive": 18,
                "taskCount": 2
            }
        ]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_stalled_projects.return_value = mock_projects
            mock_get_client.return_value = mock_client

            result = get_stalled_projects(days_inactive=14)

            assert "Found 1 stalled projects" in result
            mock_client.get_stalled_projects.assert_called_once_with(days_inactive=14, min_task_count=None)

    def test_get_stalled_projects_empty(self):
        """Test get_stalled_projects with no results."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_stalled_projects.return_value = []
            mock_get_client.return_value = mock_client

            result = get_stalled_projects()

            assert "No stalled projects found" in result

    def test_get_stalled_projects_with_min_task_count(self):
        """Test get_stalled_projects with min_task_count parameter."""
        mock_projects = [
            {
                "id": "proj-1",
                "name": "Project with Many Tasks",
                "status": "active",
                "lastActivityDate": "2024-08-01T00:00:00Z",
                "daysInactive": 68,
                "taskCount": 5
            }
        ]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_stalled_projects.return_value = mock_projects
            mock_get_client.return_value = mock_client

            result = get_stalled_projects(days_inactive=30, min_task_count=3)

            assert "Found 1 stalled projects" in result
            assert "with 3+ tasks" in result
            assert "5 tasks" in result  # Should show actual task count
            mock_client.get_stalled_projects.assert_called_once_with(days_inactive=30, min_task_count=3)


class TestTaskTools:
    """Tests for task-related tools."""

    def test_get_tasks_success(self):
        """Test get_tasks with results."""
        mock_tasks = [
            {"id": "task-001", "name": "Test Task", "completed": False}
        ]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_tasks.return_value = mock_tasks
            mock_get_client.return_value = mock_client

            result = get_tasks()

            assert "Found 1 tasks" in result
            assert "Test Task" in result

    def test_get_tasks_includes_dropped_status(self):
        """Test that get_tasks output includes dropped status."""
        mock_tasks = [
            {
                "id": "task-001",
                "name": "Dropped Task",
                "completed": False,
                "dropped": True,
                "projectName": "Test Project"
            },
            {
                "id": "task-002",
                "name": "Active Task",
                "completed": False,
                "dropped": False,
                "projectName": "Test Project"
            }
        ]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_tasks.return_value = mock_tasks
            mock_get_client.return_value = mock_client

            result = get_tasks()

            # Dropped task should show "Dropped: Yes"
            assert "Dropped: Yes" in result
            # Should appear in the first task's output
            task1_section = result.split("ID: task-002")[0]
            assert "Dropped: Yes" in task1_section
            # Active task should not show dropped status
            task2_section = result.split("ID: task-002")[1]
            assert "Dropped: Yes" not in task2_section

    def test_get_tasks_with_filters(self):
        """Test get_tasks with all filters."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_tasks.return_value = []
            mock_get_client.return_value = mock_client

            get_tasks(
                project_id="proj-001",
                flagged_only=True,
                available_only=True,
                overdue=True,
                tag_filter=["urgent"]
            )

            mock_client.get_tasks.assert_called_once_with(
                project_id="proj-001",
                flagged_only=True,
                include_completed=False,
                available_only=True,
                overdue=True,
                dropped_only=False,
                blocked_only=False,
                next_only=False,
                tag_filter=["urgent"],
                query=None,
                inbox_only=False
            )

    def test_get_tasks_dropped_only(self):
        """Test get_tasks with dropped_only filter."""
        mock_tasks = [
            {
                "id": "task-001",
                "name": "Dropped Task",
                "completed": False,
                "dropped": True,
                "projectName": "Old Project"
            }
        ]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_tasks.return_value = mock_tasks
            mock_get_client.return_value = mock_client

            result = get_tasks(dropped_only=True)

            assert "Found 1 tasks" in result
            assert "Dropped Task" in result
            mock_client.get_tasks.assert_called_once_with(
                project_id=None,
                flagged_only=False,
                include_completed=False,
                available_only=False,
                overdue=False,
                dropped_only=True,
                blocked_only=False,
                next_only=False,
                tag_filter=None,
                query=None,
                inbox_only=False
            )

    def test_get_task_success(self):
        """Test get_task with successful retrieval."""
        mock_task = {
            "id": "task-001",
            "name": "Test Task",
            "note": "Task note",
            "completed": False,
            "flagged": True,
            "dropped": False,
            "projectId": "proj-001",
            "projectName": "Test Project",
            "dueDate": "2025-10-15T17:00:00",
            "deferDate": "",
            "completionDate": "",
            "tags": "urgent"
        }

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_task.return_value = mock_task
            mock_get_client.return_value = mock_client

            result = get_task("task-001")

            assert "Task Details:" in result
            assert "Test Task" in result
            assert "Test Project" in result
            assert "Flagged: Yes" in result
            assert "Due: 2025-10-15T17:00:00" in result
            mock_client.get_task.assert_called_once_with("task-001")

    def test_get_subtasks_success(self):
        """Test get_subtasks with subtasks found."""
        mock_subtasks = [
            {
                "id": "subtask-001",
                "name": "Subtask 1",
                "note": "First subtask",
                "completed": False,
                "flagged": True,
                "dropped": False,
                "blocked": False,
                "next": True,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "2025-10-15",
                "deferDate": "",
                "completionDate": "",
                "tags": "urgent"
            },
            {
                "id": "subtask-002",
                "name": "Subtask 2",
                "note": "",
                "completed": True,
                "flagged": False,
                "dropped": False,
                "blocked": False,
                "next": False,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "2025-10-01",
                "tags": ""
            }
        ]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_subtasks.return_value = mock_subtasks
            mock_get_client.return_value = mock_client

            result = get_subtasks("parent-task-001")

            assert "Found 2 subtasks" in result
            assert "Subtask 1" in result
            assert "Subtask 2" in result
            assert "Flagged: Yes" in result
            mock_client.get_subtasks.assert_called_once_with("parent-task-001")

    def test_get_subtasks_empty(self):
        """Test get_subtasks with no subtasks."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_subtasks.return_value = []
            mock_get_client.return_value = mock_client

            result = get_subtasks("task-no-children")

            assert "Task has 0 subtasks" in result
            mock_client.get_subtasks.assert_called_once_with("task-no-children")

    def test_add_task_success(self):
        """Test add_task with successful addition."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.add_task.return_value = True
            mock_get_client.return_value = mock_client

            result = add_task("proj-001", "New Task")

            assert "Successfully added task 'New Task'" in result

    def test_complete_task_success(self):
        """Test complete_task with success."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.complete_task.return_value = True
            mock_get_client.return_value = mock_client

            result = complete_task("task-001")

            assert "Successfully completed task task-001" in result

    def test_delete_task_success(self):
        """Test delete_task with success."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.delete_task.return_value = True
            mock_get_client.return_value = mock_client

            result = delete_task("task-001")

            assert "Successfully deleted task task-001" in result

    def test_move_task_to_project(self):
        """Test move_task to a project."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.move_task.return_value = True
            mock_get_client.return_value = mock_client

            result = move_task("task-001", "proj-002")

            assert "Successfully moved task task-001 to project proj-002" in result

    def test_move_task_to_inbox(self):
        """Test move_task to inbox."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.move_task.return_value = True
            mock_get_client.return_value = mock_client

            result = move_task("task-001")

            assert "Successfully moved task task-001 to inbox" in result


class TestInboxTools:
    """Tests for inbox-related tools."""

    def test_get_inbox_tasks_success(self):
        """Test get_tasks with inbox_only parameter."""
        mock_tasks = [
            {"id": "task-001", "name": "Inbox Task", "completed": False}
        ]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_tasks.return_value = mock_tasks
            mock_get_client.return_value = mock_client

            result = get_tasks(inbox_only=True)

            assert "Found 1 inbox tasks" in result
            assert "Inbox Task" in result

    def test_get_inbox_tasks_includes_dropped_status(self):
        """Test that get_tasks(inbox_only=True) output includes dropped status."""
        mock_tasks = [
            {
                "id": "task-001",
                "name": "Dropped Inbox Task",
                "completed": False,
                "dropped": True
            },
            {
                "id": "task-002",
                "name": "Active Inbox Task",
                "completed": False,
                "dropped": False
            }
        ]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_tasks.return_value = mock_tasks
            mock_get_client.return_value = mock_client

            result = get_tasks(inbox_only=True)

            # Dropped task should show "Dropped: Yes"
            assert "Dropped: Yes" in result
            # Should appear in the first task's output
            task1_section = result.split("ID: task-002")[0]
            assert "Dropped: Yes" in task1_section
            # Active task should not show dropped status
            task2_section = result.split("ID: task-002")[1]
            assert "Dropped: Yes" not in task2_section

    def test_create_inbox_task_success(self):
        """Test create_inbox_task with success."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_inbox_task.return_value = True
            mock_get_client.return_value = mock_client

            result = create_inbox_task("Quick Task")

            assert "Successfully created inbox task 'Quick Task'" in result


class TestFolderTools:
    """Tests for folder-related tools."""

    def test_get_folders_success(self):
        """Test get_folders with results."""
        mock_folders = [
            {"id": "folder-001", "name": "Work", "path": "Work"}
        ]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_folders.return_value = mock_folders
            mock_get_client.return_value = mock_client

            result = get_folders()

            assert "Found 1 folders" in result
            assert "Work" in result

    def test_create_folder_success(self):
        """Test create_folder with success."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_folder.return_value = "folder-new-001"
            mock_get_client.return_value = mock_client

            result = create_folder("Clients", parent_path="Work")

            assert "Successfully created folder 'Clients' in 'Work'" in result

    def test_set_parent_task_success(self):
        """Test set_parent_task with success."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.set_parent_task.return_value = True
            mock_get_client.return_value = mock_client

            result = set_parent_task("task-002", "task-001")

            assert "Successfully made task task-002 a subtask of task-001" in result


class TestReviewTools:
    """Tests for project review tools."""

    def test_set_review_interval_success(self):
        """Test set_review_interval with success."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.set_review_interval.return_value = True
            mock_get_client.return_value = mock_client

            result = set_review_interval("proj-001", 1)

            assert "Successfully set review interval to 1 week(s)" in result

    def test_mark_project_reviewed_success(self):
        """Test mark_project_reviewed with success."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.mark_project_reviewed.return_value = True
            mock_get_client.return_value = mock_client

            result = mark_project_reviewed("proj-001")

            assert "Successfully marked project proj-001 as reviewed" in result

    def test_get_projects_due_for_review_success(self):
        """Test get_projects_due_for_review with results."""
        mock_projects = [
            {
                "id": "proj-001",
                "name": "Project Needing Review",
                "nextReviewDate": "2025-10-01T00:00:00"
            }
        ]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_projects_due_for_review.return_value = mock_projects
            mock_get_client.return_value = mock_client

            result = get_projects_due_for_review()

            assert "Found 1 projects due for review" in result
            assert "Project Needing Review" in result


class TestTimeEstimation:
    """Tests for time estimation tools."""

    def test_set_estimated_minutes_success(self):
        """Test set_estimated_minutes with success."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.set_estimated_minutes.return_value = True
            mock_get_client.return_value = mock_client

            result = set_estimated_minutes("task-001", 60)

            assert "Successfully set time estimate to 60 minute(s)" in result

    def test_set_estimated_minutes_clear(self):
        """Test set_estimated_minutes clearing estimate."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.set_estimated_minutes.return_value = True
            mock_get_client.return_value = mock_client

            result = set_estimated_minutes("task-001", 0)

            assert "Successfully cleared time estimate" in result


class TestPerspectiveTools:
    """Tests for perspective tools."""

    def test_get_perspectives_success(self):
        """Test get_perspectives with results."""
        mock_perspectives = ["Inbox", "Projects", "Daily Worklist"]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_perspectives.return_value = mock_perspectives
            mock_get_client.return_value = mock_client

            result = get_perspectives()

            assert "Found 3 perspectives" in result
            assert "Inbox" in result
            assert "Daily Worklist" in result

    def test_switch_perspective_success(self):
        """Test switch_perspective with success."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.switch_perspective.return_value = "Daily Worklist"
            mock_get_client.return_value = mock_client

            result = switch_perspective("Daily Worklist")

            assert "Successfully switched to perspective: Daily Worklist" in result


class TestTagTools:
    """Tests for tag-related tools."""

    def test_get_tags_success(self):
        """Test get_tags with results."""
        mock_tags = [
            {"id": "tag-001", "name": "urgent", "status": "active"}
        ]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_tags.return_value = mock_tags
            mock_get_client.return_value = mock_client

            result = get_tags()

            assert "Found 1 tags" in result
            assert "urgent" in result

    def test_add_tag_to_task_success(self):
        """Test add_tag_to_task with success."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.add_tag_to_task.return_value = True
            mock_get_client.return_value = mock_client

            result = add_tag_to_task("task-001", "urgent")

            assert "Successfully added tag 'urgent' to task task-001" in result


class TestNoteTools:
    """Tests for note-related tools."""

    def test_add_note_success(self):
        """Test add_note with success."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.add_note.return_value = True
            mock_get_client.return_value = mock_client

            result = add_note("proj-001", "Meeting notes")

            assert "Successfully added note to project proj-001" in result

    def test_get_note_project_success(self):
        """Test get_note for a project with full note content."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            long_note = "This is a very long note with lots of content\n" * 10
            mock_client.get_note.return_value = long_note
            mock_get_client.return_value = mock_client

            result = get_note("proj-001", "project")

            assert long_note in result
            assert "Note for project proj-001" in result
            mock_client.get_note.assert_called_once_with("proj-001", "project")

    def test_get_note_task_success(self):
        """Test get_note for a task."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_note.return_value = "Task note content"
            mock_get_client.return_value = mock_client

            result = get_note("task-001", "task")

            assert "Task note content" in result
            assert "Note for task task-001" in result
            mock_client.get_note.assert_called_once_with("task-001", "task")

    def test_get_note_empty(self):
        """Test get_note when item has no note."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_note.return_value = ""
            mock_get_client.return_value = mock_client

            result = get_note("proj-001", "project")

            assert "no note" in result.lower() or "empty" in result.lower()


class TestBatchOperationTools:
    """Tests for batch operation MCP tools."""

    def test_complete_tasks_success(self):
        """Test completing multiple tasks."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.complete_tasks.return_value = 3
            mock_get_client.return_value = mock_client

            result = complete_tasks(["task-001", "task-002", "task-003"])

            mock_client.complete_tasks.assert_called_once_with(["task-001", "task-002", "task-003"])
            assert "3" in result
            assert "successfully" in result.lower()

    def test_move_tasks_to_project(self):
        """Test moving multiple tasks to a project."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.move_tasks.return_value = 2
            mock_get_client.return_value = mock_client

            result = move_tasks(["task-001", "task-002"], "proj-001")

            mock_client.move_tasks.assert_called_once_with(["task-001", "task-002"], "proj-001")
            assert "2" in result
            assert "proj-001" in result

    def test_move_tasks_to_inbox(self):
        """Test moving multiple tasks to inbox."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.move_tasks.return_value = 2
            mock_get_client.return_value = mock_client

            result = move_tasks(["task-001", "task-002"], None)

            mock_client.move_tasks.assert_called_once_with(["task-001", "task-002"], None)
            assert "2" in result
            assert "inbox" in result.lower()

    def test_add_tag_to_tasks_success(self):
        """Test adding a tag to multiple tasks."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.add_tag_to_tasks.return_value = 3
            mock_get_client.return_value = mock_client

            result = add_tag_to_tasks(["task-001", "task-002", "task-003"], "urgent")

            mock_client.add_tag_to_tasks.assert_called_once_with(["task-001", "task-002", "task-003"], "urgent")
            assert "3" in result
            assert "urgent" in result

    def test_remove_tag_from_tasks_success(self):
        """Test removing a tag from multiple tasks."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.remove_tag_from_tasks.return_value = 2
            mock_get_client.return_value = mock_client

            result = remove_tag_from_tasks(["task-001", "task-002"], "urgent")

            mock_client.remove_tag_from_tasks.assert_called_once_with(["task-001", "task-002"], "urgent")
            assert "2" in result
            assert "urgent" in result

    def test_drop_tasks_success(self):
        """Test dropping multiple tasks."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.drop_tasks.return_value = 3
            mock_get_client.return_value = mock_client

            result = drop_tasks(["task-001", "task-002", "task-003"])

            mock_client.drop_tasks.assert_called_once_with(["task-001", "task-002", "task-003"])
            assert "3" in result
            assert "dropped" in result.lower()

    def test_delete_tasks_success(self):
        """Test deleting multiple tasks."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.delete_tasks.return_value = 2
            mock_get_client.return_value = mock_client

            result = delete_tasks(["task-001", "task-002"])

            mock_client.delete_tasks.assert_called_once_with(["task-001", "task-002"])
            assert "2" in result
            assert "deleted" in result.lower()

    def test_delete_projects_success(self):
        """Test deleting multiple projects."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.delete_projects.return_value = 2
            mock_get_client.return_value = mock_client

            result = delete_projects(["proj-001", "proj-002"])

            mock_client.delete_projects.assert_called_once_with(["proj-001", "proj-002"])
            assert "2" in result
            assert "deleted" in result.lower()


class TestHierarchyFieldFormatting:
    """Tests for hierarchy field formatting in output."""

    def test_format_task_includes_hierarchy_fields(self):
        """Test that _format_task includes all hierarchy fields in output."""
        mock_task = {
            "id": "task-001",
            "name": "Test Task",
            "projectName": "Test Project",
            "completed": False,
            "parentTaskId": "parent-001",
            "subtaskCount": 2,
            "sequential": True,
            "position": 3
        }

        result = server._format_task(mock_task)

        assert "Parent Task ID: parent-001" in result
        assert "Subtask Count: 2" in result
        assert "Sequential: True" in result
        assert "Position: 3" in result

    def test_format_task_shows_root_level_for_empty_parent(self):
        """Test that _format_task shows '(none - root level)' for tasks with no parent."""
        mock_task = {
            "id": "task-001",
            "name": "Root Task",
            "projectName": "Test Project",
            "completed": False,
            "parentTaskId": "",
            "subtaskCount": 0,
            "sequential": False,
            "position": 1
        }

        result = server._format_task(mock_task)

        assert "Parent Task ID: (none - root level)" in result
        assert "Subtask Count: 0" in result

    def test_format_project_includes_sequential_field(self):
        """Test that _format_project includes sequential field in output."""
        mock_project = {
            "id": "proj-001",
            "name": "Test Project",
            "status": "active",
            "sequential": True
        }

        result = server._format_project(mock_project)

        assert "Sequential: True" in result

    def test_get_task_output_includes_hierarchy_fields(self):
        """Test that get_task tool output includes hierarchy fields."""
        mock_task = {
            "id": "task-001",
            "name": "Test Task",
            "projectName": "Test Project",
            "completed": False,
            "parentTaskId": "parent-001",
            "subtaskCount": 2,
            "sequential": True,
            "position": 3
        }

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_task.return_value = mock_task
            mock_get_client.return_value = mock_client

            result = get_task("task-001")

            # Verify hierarchy fields are in the formatted output
            assert "Parent Task ID: parent-001" in result
            assert "Subtask Count: 2" in result
            assert "Sequential: True" in result
            assert "Position: 3" in result

    def test_get_tasks_output_includes_hierarchy_fields(self):
        """Test that get_tasks tool output includes hierarchy fields."""
        mock_tasks = [{
            "id": "task-001",
            "name": "Test Task",
            "projectName": "Test Project",
            "completed": False,
            "parentTaskId": "",
            "subtaskCount": 1,
            "sequential": False,
            "position": 1
        }]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_tasks.return_value = mock_tasks
            mock_get_client.return_value = mock_client

            result = get_tasks()

            # Verify hierarchy fields are in the formatted output
            assert "Parent Task ID: (none - root level)" in result
            assert "Subtask Count: 1" in result
            assert "Sequential: False" in result
            assert "Position: 1" in result

    def test_update_task_flagged_with_string_true(self):
        """Test that update_task accepts string 'true' for flagged parameter."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = True
            mock_get_client.return_value = mock_client

            result = update_task("task-001", flagged="true")

            # Verify the client was called with boolean True
            mock_client.update_task.assert_called_once_with(
                task_id="task-001",
                name=None,
                note=None,
                due_date=None,
                defer_date=None,
                flagged=True
            )
            assert "Successfully updated task" in result

    def test_update_task_flagged_with_string_false(self):
        """Test that update_task accepts string 'false' for flagged parameter."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = True
            mock_get_client.return_value = mock_client

            result = update_task("task-001", flagged="false")

            # Verify the client was called with boolean False
            mock_client.update_task.assert_called_once_with(
                task_id="task-001",
                name=None,
                note=None,
                due_date=None,
                defer_date=None,
                flagged=False
            )
            assert "Successfully updated task" in result

    def test_update_task_flagged_with_invalid_string(self):
        """Test that update_task rejects invalid flagged values."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_get_client.return_value = mock_client

            result = update_task("task-001", flagged="maybe")

            # Should return error without calling client
            assert "Error: Invalid flagged value" in result
            mock_client.update_task.assert_not_called()

    def test_update_task_flagged_omitted(self):
        """Test that update_task works when flagged parameter is omitted."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = True
            mock_get_client.return_value = mock_client

            result = update_task("task-001", name="New Name")

            # Verify the client was called with flagged=None
            mock_client.update_task.assert_called_once_with(
                task_id="task-001",
                name="New Name",
                note=None,
                due_date=None,
                defer_date=None,
                flagged=None
            )
            assert "Successfully updated task" in result

    def test_update_project_sequential_with_string_true(self):
        """Test that update_project accepts string 'true' for sequential parameter."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = True
            mock_get_client.return_value = mock_client

            result = update_project("proj-001", sequential="true")

            # Verify the client was called with boolean True
            mock_client.update_project.assert_called_once_with(
                project_id="proj-001",
                name=None,
                note=None,
                sequential=True
            )
            assert "Successfully updated project" in result

    def test_update_project_sequential_with_string_false(self):
        """Test that update_project accepts string 'false' for sequential parameter."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = True
            mock_get_client.return_value = mock_client

            result = update_project("proj-001", sequential="false")

            # Verify the client was called with boolean False
            mock_client.update_project.assert_called_once_with(
                project_id="proj-001",
                name=None,
                note=None,
                sequential=False
            )
            assert "Successfully updated project" in result

    def test_update_project_sequential_with_invalid_string(self):
        """Test that update_project rejects invalid sequential values."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_get_client.return_value = mock_client

            result = update_project("proj-001", sequential="maybe")

            # Should return error without calling client
            assert "Error: Invalid sequential value" in result
            mock_client.update_project.assert_not_called()

    def test_update_project_sequential_omitted(self):
        """Test that update_project works when sequential parameter is omitted."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = True
            mock_get_client.return_value = mock_client

            result = update_project("proj-001", name="New Name")

            # Verify the client was called with sequential=None
            mock_client.update_project.assert_called_once_with(
                project_id="proj-001",
                name="New Name",
                note=None,
                sequential=None
            )
            assert "Successfully updated project" in result
