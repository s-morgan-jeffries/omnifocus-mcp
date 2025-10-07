"""Tests for FastMCP server."""
import pytest
from unittest import mock

# Import the server module to access tool functions
import omnifocus_mcp.server_fastmcp as server

# Extract underlying functions from FunctionTool wrappers
get_client = server.get_client
get_projects = server.get_projects.fn
search_projects = server.search_projects.fn
create_project = server.create_project.fn
get_tasks = server.get_tasks.fn
add_task = server.add_task.fn
update_task = server.update_task.fn
complete_task = server.complete_task.fn
delete_task = server.delete_task.fn
delete_project = server.delete_project.fn
move_task = server.move_task.fn
drop_task = server.drop_task.fn
get_inbox_tasks = server.get_inbox_tasks.fn
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
        """Test search_projects with results."""
        mock_projects = [
            {"id": "proj-001", "name": "Budget Project", "status": "active"}
        ]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.search_projects.return_value = mock_projects
            mock_get_client.return_value = mock_client

            result = search_projects("budget")

            assert "Found 1 projects matching 'budget'" in result
            assert "Budget Project" in result
            mock_client.search_projects.assert_called_once_with("budget")

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
                tag_filter=["urgent"]
            )

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
        """Test get_inbox_tasks with results."""
        mock_tasks = [
            {"id": "task-001", "name": "Inbox Task", "completed": False}
        ]

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_inbox_tasks.return_value = mock_tasks
            mock_get_client.return_value = mock_client

            result = get_inbox_tasks()

            assert "Found 1 inbox tasks" in result
            assert "Inbox Task" in result

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
