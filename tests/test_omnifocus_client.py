"""Unit tests for OmniFocusConnector."""
import json
import subprocess
from unittest import mock
import pytest

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector, run_applescript


class TestRunAppleScript:
    """Tests for the run_applescript function."""

    def test_successful_execution(self):
        """Test successful AppleScript execution."""
        with mock.patch('subprocess.run') as mock_run:
            mock_run.return_value = mock.Mock(stdout="test output\n")
            result = run_applescript("tell application 'Finder' to return name")
            assert result == "test output"
            mock_run.assert_called_once()

    def test_subprocess_error(self):
        """Test handling of subprocess errors."""
        with mock.patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error message")
            with pytest.raises(subprocess.CalledProcessError):
                run_applescript("invalid script")


class TestOmniFocusConnector:
    """Tests for OmniFocusConnector class."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusConnector(enable_safety_checks=False)

    @pytest.fixture
    def sample_projects_json(self):
        """Sample JSON output from AppleScript."""
        return json.dumps([
            {
                "id": "proj-001",
                "name": "Test Project",
                "note": "Test note",
                "status": "active",
                "folderPath": "Work > Tests"
            },
            {
                "id": "proj-002",
                "name": "Project with \"quotes\"",
                "note": "Note with\nnewlines\nand\ttabs",
                "status": "active",
                "folderPath": ""
            }
        ])

    def test_get_projects_success(self, client, sample_projects_json):
        """Test successful project retrieval."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            projects = client.get_projects()

            assert len(projects) == 2
            assert projects[0]['id'] == "proj-001"
            assert projects[0]['name'] == "Test Project"
            assert projects[0]['folderPath'] == "Work > Tests"
            assert projects[1]['name'] == 'Project with "quotes"'

    def test_get_projects_empty(self, client):
        """Test handling of empty projects list."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            projects = client.get_projects()
            assert projects == []

    def test_get_projects_no_output(self, client):
        """Test handling of no output from AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = ""
            with pytest.raises(Exception) as exc_info:
                client.get_projects()
            assert "No output from OmniFocus AppleScript" in str(exc_info.value)

    def test_get_projects_invalid_json(self, client):
        """Test handling of invalid JSON from AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "not valid json"
            with pytest.raises(Exception) as exc_info:
                client.get_projects()
            assert "Error parsing OmniFocus output" in str(exc_info.value)

    def test_get_projects_subprocess_error(self, client):
        """Test handling of subprocess errors."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="permission denied")
            with pytest.raises(Exception) as exc_info:
                client.get_projects()
            assert "Error querying OmniFocus" in str(exc_info.value)

    def test_create_project_basic(self, client):
        """Test creating a basic project."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            project_id = client.create_project("New Project")
            assert project_id == "proj-new-001"
            # Verify AppleScript contains project name
            call_args = mock_run.call_args[0][0]
            assert "New Project" in call_args
            assert "make new project" in call_args

    def test_create_project_with_note(self, client):
        """Test creating project with note."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            project_id = client.create_project(
                "New Project",
                note="This is the project description"
            )
            assert project_id == "proj-new-001"
            call_args = mock_run.call_args[0][0]
            assert "This is the project description" in call_args

    def test_create_project_sequential(self, client):
        """Test creating sequential project."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            project_id = client.create_project("Sequential Project", sequential=True)
            assert project_id == "proj-new-001"
            call_args = mock_run.call_args[0][0]
            assert "sequential:true" in call_args

    def test_create_project_parallel(self, client):
        """Test creating parallel project (default)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            project_id = client.create_project("Parallel Project", sequential=False)
            assert project_id == "proj-new-001"
            call_args = mock_run.call_args[0][0]
            assert "sequential:false" in call_args

    def test_create_project_in_folder(self, client):
        """Test creating project in a folder."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            project_id = client.create_project("New Project", folder_path="Work")
            assert project_id == "proj-new-001"
            call_args = mock_run.call_args[0][0]
            assert 'whose name is "Work"' in call_args

    def test_create_project_in_nested_folder(self, client):
        """Test creating project in nested folder."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            project_id = client.create_project("New Project", folder_path="Work > Clients")
            assert project_id == "proj-new-001"
            call_args = mock_run.call_args[0][0]
            assert '"Work"' in call_args
            assert '"Clients"' in call_args

    def test_create_project_with_special_characters(self, client):
        """Test creating project with special characters in name."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            project_id = client.create_project('Project with "quotes" and \\backslashes')
            assert project_id == "proj-new-001"
            # Verify characters are escaped
            call_args = mock_run.call_args[0][0]
            assert '\\"quotes\\"' in call_args or 'quotes' in call_args
            assert '\\\\backslashes' in call_args or 'backslashes' in call_args

    def test_create_project_with_all_properties(self, client):
        """Test creating project with all properties."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            project_id = client.create_project(
                name="Full Featured Project",
                note="Complete description with details",
                folder_path="Work > Active",
                sequential=True
            )
            assert project_id == "proj-new-001"
            call_args = mock_run.call_args[0][0]
            assert "Full Featured Project" in call_args
            assert "Complete description with details" in call_args
            assert "sequential:true" in call_args

    def test_create_project_no_output(self, client):
        """Test handling of no output from AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = ""
            with pytest.raises(Exception) as exc_info:
                client.create_project("New Project")
            assert "No project ID returned" in str(exc_info.value)

    def test_create_project_subprocess_error(self, client):
        """Test handling of subprocess errors."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="permission denied")
            with pytest.raises(Exception) as exc_info:
                client.create_project("New Project")
            assert "Error creating project" in str(exc_info.value)

    def test_create_project_empty_name(self, client):
        """Test creating project with empty name."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            # OmniFocus allows empty names, so this should work
            project_id = client.create_project("")
            assert project_id == "proj-new-001"


class TestGetTasks:
    """Tests for get_tasks functionality."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusConnector(enable_safety_checks=False)

    @pytest.fixture
    def sample_tasks_json(self):
        """Sample JSON output for tasks."""
        return json.dumps([
            {
                "id": "task-001",
                "name": "Test Task",
                "note": "Task note",
                "completed": False,
                "flagged": True,
                "dropped": False,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "2025-10-15T17:00:00",
                "deferDate": "2025-10-08T09:00:00",
                "completionDate": "",
                "tags": "urgent, work"
            },
            {
                "id": "task-002",
                "name": "Another Task",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": ""
            }
        ])

    def test_get_tasks_all(self, client, sample_tasks_json):
        """Test getting all tasks."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            tasks = client.get_tasks()
            assert len(tasks) == 2
            assert tasks[0]['id'] == "task-001"
            assert tasks[0]['name'] == "Test Task"
            assert tasks[0]['flagged'] is True
            assert tasks[0]['dropped'] is False
            assert tasks[0]['tags'] == "urgent, work"

    def test_get_tasks_by_project(self, client, sample_tasks_json):
        """Test getting tasks filtered by project."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            tasks = client.get_tasks(project_id="proj-001")
            assert len(tasks) == 2
            # Verify the AppleScript was called with project filter
            call_args = mock_run.call_args[0][0]
            assert 'whose id is "proj-001"' in call_args

    def test_get_tasks_include_completed(self, client):
        """Test getting tasks including completed ones."""
        completed_json = json.dumps([
            {
                "id": "task-001",
                "name": "Completed Task",
                "note": "",
                "completed": True,
                "flagged": False,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "2025-10-01T10:00:00",
                "tags": ""
            }
        ])
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = completed_json
            tasks = client.get_tasks(include_completed=True)
            assert len(tasks) == 1
            assert tasks[0]['completed'] is True
            # Verify completion filter is not in script
            call_args = mock_run.call_args[0][0]
            assert "skip completed task" not in call_args

    def test_get_tasks_flagged_only(self, client, sample_tasks_json):
        """Test getting only flagged tasks."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(flagged_only=True)
            # Verify flagged filter is in script
            call_args = mock_run.call_args[0][0]
            assert "skip non-flagged task" in call_args

    def test_get_tasks_empty(self, client):
        """Test handling of empty tasks list."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            tasks = client.get_tasks()
            assert tasks == []

    def test_get_tasks_no_output(self, client):
        """Test handling of no output from AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = ""
            with pytest.raises(Exception) as exc_info:
                client.get_tasks()
            assert "No output from OmniFocus AppleScript" in str(exc_info.value)

    def test_get_tasks_invalid_json(self, client):
        """Test handling of invalid JSON from AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "not valid json"
            with pytest.raises(Exception) as exc_info:
                client.get_tasks()
            assert "Error parsing OmniFocus task output" in str(exc_info.value)

    def test_get_tasks_subprocess_error(self, client):
        """Test handling of subprocess errors."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="permission denied")
            with pytest.raises(Exception) as exc_info:
                client.get_tasks()
            assert "Error querying OmniFocus tasks" in str(exc_info.value)

    def test_get_tasks_with_all_filters(self, client, sample_tasks_json):
        """Test getting tasks with all filters combined."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(
                project_id="proj-001",
                include_completed=True,
                flagged_only=True
            )
            # Verify all filters are in script
            call_args = mock_run.call_args[0][0]
            assert 'whose id is "proj-001"' in call_args
            assert "skip completed task" not in call_args
            assert "skip non-flagged task" in call_args

    def test_get_tasks_includes_dropped_field(self, client, sample_tasks_json):
        """Test that get_tasks includes the dropped field in the AppleScript and response."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            tasks = client.get_tasks()
            # Verify dropped field is in returned data
            assert 'dropped' in tasks[0]
            assert tasks[0]['dropped'] is False
            # Verify the AppleScript retrieves the dropped field
            call_args = mock_run.call_args[0][0]
            assert "set taskDropped to dropped of t" in call_args
            # Verify the AppleScript includes dropped in JSON output
            assert '\\"dropped\\"' in call_args

    def test_get_tasks_dropped_only(self, client):
        """Test filtering for only dropped tasks."""
        dropped_tasks_json = json.dumps([
            {
                "id": "task-001",
                "name": "Dropped Task",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": True,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": ""
            }
        ])
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = dropped_tasks_json
            tasks = client.get_tasks(dropped_only=True)
            assert len(tasks) == 1
            assert tasks[0]['dropped'] is True
            # Verify the filter is in the script
            call_args = mock_run.call_args[0][0]
            assert "dropped of t" in call_args
            # Should skip non-dropped tasks
            assert "skip" in call_args.lower() or "error" in call_args.lower()

    def test_get_tasks_includes_blocked_field(self, client):
        """Test that get_tasks includes the blocked field in the AppleScript and response."""
        tasks_json = json.dumps([
            {
                "id": "task-001",
                "name": "Blocked Task",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "blocked": True,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": ""
            }
        ])
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = tasks_json
            tasks = client.get_tasks()
            # Verify blocked field is in returned data
            assert 'blocked' in tasks[0]
            assert tasks[0]['blocked'] is True
            # Verify the AppleScript retrieves the blocked field
            call_args = mock_run.call_args[0][0]
            assert "set taskBlocked to blocked of t" in call_args
            # Verify the AppleScript includes blocked in JSON output
            assert '\\"blocked\\"' in call_args

    def test_get_tasks_blocked_only(self, client):
        """Test filtering for only blocked tasks."""
        blocked_tasks_json = json.dumps([
            {
                "id": "task-001",
                "name": "Blocked Task",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "blocked": True,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": ""
            }
        ])
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = blocked_tasks_json
            tasks = client.get_tasks(blocked_only=True)
            assert len(tasks) == 1
            assert tasks[0]['blocked'] is True
            # Verify the filter is in the script
            call_args = mock_run.call_args[0][0]
            assert "blocked of t" in call_args
            # Should skip non-blocked tasks
            assert "skip" in call_args.lower() or "error" in call_args.lower()

    def test_get_tasks_available_only(self, client):
        """Test getting only available tasks (not deferred or blocked)."""
        tasks_json = json.dumps([
            {
                "id": "task-001",
                "name": "Available Task",
                "note": "",
                "completed": False,
                "flagged": False,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": "",
                "dropped": False,
                "blocked": False
            }
        ])
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = tasks_json
            tasks = client.get_tasks(available_only=True)
            assert len(tasks) == 1
            # Verify the filter is in the script
            call_args = mock_run.call_args[0][0]
            assert "skip unavailable task" in call_args or "dropped" in call_args

    def test_get_tasks_overdue(self, client):
        """Test getting only overdue tasks."""
        overdue_json = json.dumps([
            {
                "id": "task-001",
                "name": "Overdue Task",
                "note": "",
                "completed": False,
                "flagged": False,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "2025-10-01T17:00:00",
                "deferDate": "",
                "completionDate": "",
                "tags": ""
            }
        ])
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = overdue_json
            tasks = client.get_tasks(overdue=True)
            assert len(tasks) == 1
            # Verify the filter is in the script
            call_args = mock_run.call_args[0][0]
            assert "overdue" in call_args.lower() or "current date" in call_args

    def test_get_tasks_tag_filter_single(self, client):
        """Test filtering tasks by a single tag."""
        tasks_json = json.dumps([
            {
                "id": "task-001",
                "name": "Tagged Task",
                "note": "",
                "completed": False,
                "flagged": False,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": "urgent, work"
            }
        ])
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = tasks_json
            tasks = client.get_tasks(tag_filter=["urgent"])
            assert len(tasks) == 1
            assert "urgent" in tasks[0]["tags"]

    def test_get_tasks_tag_filter_multiple(self, client):
        """Test filtering tasks by multiple tags (AND logic)."""
        tasks_json = json.dumps([
            {
                "id": "task-001",
                "name": "Multi-Tagged Task",
                "note": "",
                "completed": False,
                "flagged": False,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": "urgent, work, priority"
            }
        ])
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = tasks_json
            tasks = client.get_tasks(tag_filter=["urgent", "work"])
            assert len(tasks) == 1


class TestUpdateTask:
    """Tests for update_task functionality."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusConnector(enable_safety_checks=False)

    def test_update_task_name(self, client):
        """Test updating task name (LEGACY TEST - updated for new API return format)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task("task-001", name="Updated Task Name")
            # NEW API: Returns dict instead of bool
            assert result["success"] is True
            assert result["task_id"] == "task-001"
            call_args = mock_run.call_args[0][0]
            assert 'whose id is "task-001"' in call_args
            assert "Updated Task Name" in call_args

    def test_update_task_note(self, client):
        """Test updating task note (LEGACY TEST - updated for new API return format)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task("task-001", note="Updated note")
            # NEW API: Returns dict instead of bool
            assert result["success"] is True
            assert result["task_id"] == "task-001"
            call_args = mock_run.call_args[0][0]
            assert "Updated note" in call_args

    def test_update_task_due_date(self, client):
        """Test updating task due date (LEGACY TEST - updated for new API return format)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task("task-001", due_date="2025-12-25")
            # NEW API: Returns dict instead of bool
            assert result["success"] is True
            assert result["task_id"] == "task-001"
            call_args = mock_run.call_args[0][0]
            assert "December 25, 2025" in call_args

    def test_update_task_defer_date(self, client):
        """Test updating task defer date (LEGACY TEST - updated for new API return format)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task("task-001", defer_date="2025-12-20")
            # NEW API: Returns dict instead of bool
            assert result["success"] is True
            assert result["task_id"] == "task-001"
            call_args = mock_run.call_args[0][0]
            assert "December 20, 2025" in call_args

    def test_update_task_flagged(self, client):
        """Test updating task flagged status (LEGACY TEST - updated for new API return format)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task("task-001", flagged=True)
            # NEW API: Returns dict instead of bool
            assert result["success"] is True
            assert result["task_id"] == "task-001"
            call_args = mock_run.call_args[0][0]
            assert "flagged" in call_args

    def test_update_task_multiple_fields(self, client):
        """Test updating multiple task fields at once (LEGACY TEST - updated for new API return format)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task(
                "task-001",
                name="New Name",
                note="New note",
                due_date="2025-12-25T17:00:00",
                flagged=True
            )
            # NEW API: Returns dict instead of bool
            assert result["success"] is True
            assert result["task_id"] == "task-001"
            call_args = mock_run.call_args[0][0]
            assert "New Name" in call_args
            assert "New note" in call_args
            assert "December 25, 2025 05:00:00 PM" in call_args
            assert "flagged" in call_args

    def test_update_task_no_fields(self, client):
        """Test updating task with no fields raises error."""
        with pytest.raises(ValueError) as exc_info:
            client.update_task("task-001")
        assert "At least one field must be provided" in str(exc_info.value)

    def test_update_task_empty_id(self, client):
        """Test updating task with empty ID raises error."""
        with pytest.raises(ValueError) as exc_info:
            client.update_task("", name="New Name")
        assert "task_id is required" in str(exc_info.value)

    def test_update_task_failure(self, client):
        """Test handling of task update failure (LEGACY TEST - updated for new API error handling)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "false: Task not found"
            # NEW API: Returns error dict instead of raising exception
            result = client.update_task("invalid-id", name="New Name")
            assert result["success"] is False
            assert "error" in result

    def test_update_task_subprocess_error(self, client):
        """Test handling of subprocess errors during task update (LEGACY TEST - updated for new API error handling)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            # NEW API: Returns error dict instead of raising exception
            result = client.update_task("task-001", name="New Name")
            assert result["success"] is False
            assert "error" in result

    def test_update_task_clear_date(self, client):
        """Test clearing a task date by setting to empty string (LEGACY TEST - updated for new API return format)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task("task-001", due_date="")
            # NEW API: Returns dict instead of bool
            assert result["success"] is True
            assert result["task_id"] == "task-001"
            call_args = mock_run.call_args[0][0]
            assert "missing value" in call_args


class TestGetFolders:
    """Tests for get_folders method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusConnector(enable_safety_checks=False)

    @pytest.fixture
    def sample_folders_json(self):
        """Sample folder data."""
        return json.dumps([
            {"id": "folder-001", "name": "Work", "path": "Work"},
            {"id": "folder-002", "name": "Personal", "path": "Personal"},
            {"id": "folder-003", "name": "Clients", "path": "Work > Clients"}
        ])

    def test_get_folders_success(self, client, sample_folders_json):
        """Test successfully retrieving folders."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_folders_json
            folders = client.get_folders()
            assert len(folders) == 3
            assert folders[0]["name"] == "Work"
            assert folders[2]["path"] == "Work > Clients"

    def test_get_folders_empty(self, client):
        """Test retrieving folders when none exist."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            folders = client.get_folders()
            assert folders == []

    def test_get_folders_error(self, client):
        """Test handling of AppleScript errors."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.get_folders()
            assert "Error retrieving folders" in str(exc_info.value)


class TestCreateFolder:
    """Tests for create_folder method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusConnector(enable_safety_checks=False)

    def test_create_folder_root_level(self, client):
        """Test creating a folder at root level."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "folder-new-001"
            folder_id = client.create_folder("New Folder")
            assert folder_id == "folder-new-001"
            mock_run.assert_called_once()

    def test_create_folder_with_parent_path(self, client):
        """Test creating a folder with parent path."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "folder-new-002"
            folder_id = client.create_folder("Clients", parent_path="Work")
            assert folder_id == "folder-new-002"
            mock_run.assert_called_once()

    def test_create_folder_nested_parent_path(self, client):
        """Test creating a folder with nested parent path."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "folder-new-003"
            folder_id = client.create_folder("Active", parent_path="Work > Clients")
            assert folder_id == "folder-new-003"
            mock_run.assert_called_once()

    def test_create_folder_with_special_characters(self, client):
        """Test creating a folder with special characters in name."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "folder-new-004"
            folder_id = client.create_folder("Work & Life")
            assert folder_id == "folder-new-004"

    def test_create_folder_parent_not_found(self, client):
        """Test creating folder with non-existent parent."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "false: Parent folder not found"
            with pytest.raises(Exception) as exc_info:
                client.create_folder("New Folder", parent_path="Nonexistent")
            assert "not found" in str(exc_info.value).lower()

    def test_create_folder_error(self, client):
        """Test handling of folder creation errors."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.create_folder("New Folder")
            assert "Error creating folder" in str(exc_info.value)


class TestGetPerspectives:
    """Tests for get_perspectives method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusConnector(enable_safety_checks=False)

    def test_get_perspectives_success(self, client):
        """Test getting perspective names."""
        perspectives_str = "Inbox, Projects, Tags, Forecast, Daily Worklist"
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = perspectives_str
            perspectives = client.get_perspectives()
            assert len(perspectives) == 5
            assert "Inbox" in perspectives
            assert "Daily Worklist" in perspectives

    def test_get_perspectives_empty(self, client):
        """Test when no custom perspectives exist."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "Inbox, Projects"
            perspectives = client.get_perspectives()
            assert len(perspectives) == 2

    def test_get_perspectives_error(self, client):
        """Test handling of errors."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.get_perspectives()
            assert "Error retrieving perspectives" in str(exc_info.value)


class TestSwitchPerspective:
    """Tests for switch_perspective method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusConnector(enable_safety_checks=False)

    def test_switch_perspective_success(self, client):
        """Test successfully switching perspective."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "Daily Worklist"
            result = client.switch_perspective("Daily Worklist")
            assert result == "Daily Worklist"
            mock_run.assert_called_once()

    def test_switch_perspective_builtin(self, client):
        """Test switching to built-in perspective."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "Inbox"
            result = client.switch_perspective("Inbox")
            assert result == "Inbox"

    def test_switch_perspective_error(self, client):
        """Test handling of errors."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.switch_perspective("Invalid")
            assert "Error switching perspective" in str(exc_info.value)
