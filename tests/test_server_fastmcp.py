"""Tests for FastMCP server."""
import pytest
from unittest import mock

# Import the server module to access tool functions
import omnifocus_mcp.server_fastmcp as server

# Extract underlying functions from FunctionTool wrappers
get_client = server.get_client
get_projects = server.get_projects.fn
create_project = server.create_project.fn
update_project = server.update_project.fn
get_tasks = server.get_tasks.fn
update_task = server.update_task.fn
get_tags = server.get_tags.fn
get_folders = server.get_folders.fn
create_folder = server.create_folder.fn
get_perspectives = server.get_perspectives.fn
switch_perspective = server.switch_perspective.fn
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
                name="New Project", note=None, folder_path="Work", sequential=False, review_interval_weeks=None
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
                task_id=None,  # NEW (Phase 3.1)
                parent_task_id=None,  # NEW (Phase 3.1)
                include_full_notes=False,  # NEW (Phase 3.1)
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
                task_id=None,  # NEW (Phase 3.1)
                parent_task_id=None,  # NEW (Phase 3.1)
                include_full_notes=False,  # NEW (Phase 3.1)
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


class TestBatchOperationTools:
    """Tests for batch operation MCP tools."""







    def test_delete_tasks_success(self):
        """Test deleting multiple tasks."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            # Updated for NEW API - client returns dict instead of int
            mock_client.delete_tasks.return_value = {
                "deleted_count": 2,
                "failed_count": 0,
                "deleted_ids": ["task-001", "task-002"],
                "failures": []
            }
            mock_get_client.return_value = mock_client

            result = delete_tasks(["task-001", "task-002"])

            mock_client.delete_tasks.assert_called_once_with(["task-001", "task-002"])
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
        """LEGACY TEST (updated for NEW API): Test that update_task with boolean True works."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            # NEW API: Client returns dict
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["flagged"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            result = update_task("task-001", flagged=True)

            # Verify the client was called with boolean True
            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["flagged"] is True
            assert "Successfully updated task" in result

    def test_update_task_flagged_with_string_false(self):
        """LEGACY TEST (updated for NEW API): Test that update_task with boolean False works."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            # NEW API: Client returns dict
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["flagged"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            result = update_task("task-001", flagged=False)

            # Verify the client was called with boolean False
            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["flagged"] is False
            assert "Successfully updated task" in result

    def test_update_task_flagged_with_invalid_string(self):
        """LEGACY TEST (removed): NEW API accepts bool directly, not strings."""
        # This test is no longer relevant since NEW API uses bool type, not string
        # MCP framework handles type conversion/validation
        pass

    def test_update_task_flagged_omitted(self):
        """LEGACY TEST (updated for NEW API): Test that update_task works when flagged parameter is omitted."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            # NEW API: Client returns dict
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["task_name"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            result = update_task("task-001", name="New Name")

            # Verify the client was called with flagged=None
            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["flagged"] is None
            assert "Successfully updated task" in result

    def test_update_project_sequential_with_string_true(self):
        """Test that update_project accepts string 'true' for sequential parameter."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            # NEW API returns dict, not boolean
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "proj-001",
                "updated_fields": ["sequential"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            result = update_project("proj-001", sequential="true")

            # Verify the client was called with boolean True
            call_kwargs = mock_client.update_project.call_args[1]
            assert call_kwargs['project_id'] == "proj-001"
            assert call_kwargs['sequential'] is True
            assert "Successfully updated project" in result

    def test_update_project_sequential_with_string_false(self):
        """Test that update_project accepts string 'false' for sequential parameter."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            # NEW API returns dict, not boolean
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "proj-001",
                "updated_fields": ["sequential"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            result = update_project("proj-001", sequential="false")

            # Verify the client was called with boolean False
            call_kwargs = mock_client.update_project.call_args[1]
            assert call_kwargs['project_id'] == "proj-001"
            assert call_kwargs['sequential'] is False
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
            # NEW API returns dict, not boolean
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "proj-001",
                "updated_fields": ["project_name"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            # NEW API uses project_name not name
            result = update_project("proj-001", project_name="New Name")

            # Verify the client was called with sequential=None
            call_kwargs = mock_client.update_project.call_args[1]
            assert call_kwargs['project_id'] == "proj-001"
            assert call_kwargs['project_name'] == "New Name"  # Fixed: project_name not name
            assert call_kwargs.get('sequential') is None
            assert "Successfully updated project" in result
