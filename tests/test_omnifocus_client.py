"""Unit tests for OmniFocusConnector."""
import json
import subprocess
from unittest import mock
import pytest

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector, TaskStatus, run_applescript


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
            # Verify flagged filter uses whose clause
            call_args = mock_run.call_args[0][0]
            assert "flagged is true" in call_args

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
            # Accept either batch mode or per-task mode
            assert ("set taskDrops to dropped of ft" in call_args or
                    "set taskDropped to dropped of t" in call_args)
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
            # Verify dropped filter uses whose clause
            call_args = mock_run.call_args[0][0]
            assert "dropped is true" in call_args

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
            # Accept either batch mode or per-task mode
            assert ("set taskBlocks to blocked of ft" in call_args or
                    "set taskBlocked to blocked of t" in call_args)
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
            # Verify blocked filter uses whose clause
            call_args = mock_run.call_args[0][0]
            assert "blocked is true" in call_args

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


class TestTagExtractionAndFiltering:
    """Tests for tag extraction from AppleScript and tag filtering in Python (issue #199)."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    def test_filter_tasks_by_tags_handles_list_tags(self, client):
        """_filter_tasks_by_tags must handle tags as a list (JSON array from AppleScript)."""
        tasks = [
            {"id": "t1", "tags": ["urgent", "work"]},
            {"id": "t2", "tags": ["personal"]},
            {"id": "t3", "tags": []},
        ]
        result = client._filter_tasks_by_tags(tasks, ["urgent"], "or")
        assert len(result) == 1
        assert result[0]["id"] == "t1"

    def test_filter_tasks_by_tags_and_mode_with_list_tags(self, client):
        """AND mode must work with list-type tags."""
        tasks = [
            {"id": "t1", "tags": ["urgent", "work"]},
            {"id": "t2", "tags": ["urgent"]},
        ]
        result = client._filter_tasks_by_tags(tasks, ["urgent", "work"], "and")
        assert len(result) == 1
        assert result[0]["id"] == "t1"

    def test_filter_tasks_by_tags_not_mode_with_list_tags(self, client):
        """NOT mode must work with list-type tags."""
        tasks = [
            {"id": "t1", "tags": ["urgent", "work"]},
            {"id": "t2", "tags": ["personal"]},
        ]
        result = client._filter_tasks_by_tags(tasks, ["urgent"], "not")
        assert len(result) == 1
        assert result[0]["id"] == "t2"

    def test_get_tasks_tag_filter_with_list_tags(self, client):
        """get_tasks with tag_filter must work when AppleScript returns tags as JSON arrays."""
        tasks_json = json.dumps([
            {
                "id": "task-001", "name": "Tagged Task", "note": "",
                "completed": False, "flagged": False, "dropped": False,
                "blocked": False, "next": True,
                "projectId": "proj-001", "projectName": "Test Project",
                "dueDate": "", "deferDate": "", "creationDate": None,
                "modificationDate": None, "completionDate": None, "droppedDate": None,
                "tags": ["urgent", "work"], "estimatedMinutes": None,
                "isRecurring": False, "recurrence": "", "repetitionMethod": "",
                "parentTaskId": "", "subtaskCount": 0, "sequential": False,
                "position": 1, "numberOfAvailableTasks": 0, "available": True
            }
        ])
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = tasks_json
            tasks = client.get_tasks(tag_filter=["urgent"])
            assert len(tasks) == 1
            assert tasks[0]["id"] == "task-001"


class TestWhoseClauseOptimization:
    """Tests that get_tasks uses 'whose' clauses for pre-filtering instead of manual iteration."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    @pytest.fixture
    def sample_tasks_json(self):
        return json.dumps([{
            "id": "task-001", "name": "Test Task", "note": "", "completed": False,
            "flagged": True, "dropped": False, "blocked": False, "next": True,
            "projectId": "proj-001", "projectName": "Test Project",
            "dueDate": "", "deferDate": "", "creationDate": None,
            "modificationDate": None, "completionDate": None, "droppedDate": None,
            "tags": [], "estimatedMinutes": None, "isRecurring": False,
            "recurrence": "", "repetitionMethod": "", "parentTaskId": "",
            "subtaskCount": 0, "sequential": False, "position": 1,
            "numberOfAvailableTasks": 0, "available": True
        }])

    def test_flagged_uses_whose_clause(self, client, sample_tasks_json):
        """flagged_only should use 'whose' with 'flagged is true' in task source."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(flagged_only=True)
            script = mock_run.call_args[0][0]
            assert "whose" in script
            assert "flagged is true" in script

    def test_next_uses_whose_clause(self, client, sample_tasks_json):
        """next_only should use 'whose' with 'next is true' in task source."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(next_only=True)
            script = mock_run.call_args[0][0]
            assert "whose" in script
            assert "next is true" in script

    def test_query_uses_whose_clause(self, client, sample_tasks_json):
        """query should use 'whose ... name contains' in task source."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(query="bench")
            script = mock_run.call_args[0][0]
            assert 'name contains "bench"' in script
            assert 'note contains "bench"' in script
            assert "whose" in script

    def test_no_filter_uses_whose_completed_false(self, client, sample_tasks_json):
        """No explicit filter should still use whose to exclude completed tasks."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks()
            script = mock_run.call_args[0][0]
            assert "whose completed is false" in script

    def test_project_id_not_affected(self, client, sample_tasks_json):
        """project_id filter should still use its existing fast path."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(project_id="proj-001")
            script = mock_run.call_args[0][0]
            assert 'whose id is "proj-001"' in script

    def test_flagged_whose_excludes_completed(self, client, sample_tasks_json):
        """flagged_only should combine whose with completed filter."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(flagged_only=True)
            script = mock_run.call_args[0][0]
            # Should combine both conditions in whose clause
            assert "completed is false" in script
            assert "flagged is true" in script

    def test_overdue_uses_whose_clause(self, client, sample_tasks_json):
        """overdue should use 'whose' with effective due date comparison."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(overdue=True)
            script = mock_run.call_args[0][0]
            # Should use whose for effective due date filtering (includes inherited)
            assert "whose" in script.lower()
            assert "effective due date" in script


    def test_tag_filter_uses_tag_side_prefilter(self, client, sample_tasks_json):
        """tag_filter should query from tag side first, then use whose id clause."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # First call: _get_task_ids_for_tags returns IDs
            # Second call: get_tasks main query uses those IDs in whose clause
            mock_run.side_effect = [
                "task-001|",  # tag pre-filter returns one task ID
                sample_tasks_json,  # main batch query
            ]
            result = client.get_tasks(tag_filter=["urgent"])
            assert len(result) == 1

            # Should have made 2 calls: tag pre-filter + main query
            assert mock_run.call_count == 2

            # First call should query from the tag side
            tag_script = mock_run.call_args_list[0][0][0]
            assert "first flattened tag whose name is" in tag_script

            # Second call should use whose with the pre-filtered ID
            main_script = mock_run.call_args_list[1][0][0]
            assert 'id is "task-001"' in main_script
            assert "a reference to" in main_script  # Should enter batch mode

    def test_tag_filter_empty_result_returns_early(self, client):
        """tag_filter with no matching tasks should return empty list without main query."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "|"  # Tag exists but no tasks
            result = client.get_tasks(tag_filter=["empty-tag"])
            assert result == []
            # Should only make 1 call (the tag pre-filter), not the main query
            assert mock_run.call_count == 1

    def test_tag_filter_not_found_falls_back(self, client, sample_tasks_json):
        """tag_filter with unknown tag should fall back to standard path."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json  # All calls return same JSON
            # When tag not found, _get_task_ids_for_tags returns None
            with mock.patch.object(client, '_get_task_ids_for_tags', return_value=None):
                result = client.get_tasks(tag_filter=["nonexistent"])
            # Should still return results (fallback path)
            assert isinstance(result, list)

    def test_tag_filter_not_mode_uses_batch_mode(self, client, sample_tasks_json):
        """NOT mode tag_filter uses batch mode like all other source types.

        After #368, all get_tasks calls use batch mode with 'a reference to'.
        """
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(
                tag_filter=["waiting"], tag_filter_mode="not",
                include_completed=True
            )
            script = mock_run.call_args[0][0]
            # Batch mode uses 'a reference to' for property reads
            assert "a reference to" in script


class TestBatchPropertyExtraction:
    """Tests that get_tasks uses batch property extraction via 'a reference to' when whose is active."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    @pytest.fixture
    def sample_tasks_json(self):
        return json.dumps([{
            "id": "task-001", "name": "Test Task", "note": "", "completed": False,
            "flagged": True, "dropped": False, "blocked": False, "next": True,
            "projectId": "proj-001", "projectName": "Test Project",
            "dueDate": "", "deferDate": "", "creationDate": None,
            "modificationDate": None, "completionDate": None, "droppedDate": None,
            "tags": [], "estimatedMinutes": None, "isRecurring": False,
            "recurrence": "", "repetitionMethod": "", "parentTaskId": "",
            "subtaskCount": 0, "sequential": False, "position": 1,
            "numberOfAvailableTasks": 0, "available": True
        }])

    def test_flagged_uses_batch_extraction(self, client, sample_tasks_json):
        """flagged_only should use 'a reference to' for batch property reads."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(flagged_only=True)
            script = mock_run.call_args[0][0]
            assert "a reference to" in script
            assert "id of ft" in script
            assert "name of ft" in script

    def test_batch_uses_nested_project_reads(self, client, sample_tasks_json):
        """Batch mode should use nested batch reads for project info."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(flagged_only=True)
            script = mock_run.call_args[0][0]
            assert "id of (containing project of ft)" in script
            assert "name of (containing project of ft)" in script

    def test_batch_uses_nested_tag_reads(self, client, sample_tasks_json):
        """Batch mode should use nested batch reads for tag names."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(flagged_only=True)
            script = mock_run.call_args[0][0]
            assert "name of (tags of ft)" in script

    def test_batch_uses_nested_parent_reads(self, client, sample_tasks_json):
        """Batch mode should use nested batch reads for parent task IDs."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(flagged_only=True)
            script = mock_run.call_args[0][0]
            assert "id of (parent task of ft)" in script

    def test_batch_zips_parallel_lists(self, client, sample_tasks_json):
        """Batch mode should iterate by index (zip pattern) not per-task reference."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(flagged_only=True)
            script = mock_run.call_args[0][0]
            # Should use indexed access pattern
            assert "item i of ids" in script
            # Should NOT use per-task loop with property reads
            assert "set taskId to id of t" not in script

    def test_project_id_uses_batch(self, client, sample_tasks_json):
        """project_id path uses batch extraction after #368."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(project_id="proj-001")
            script = mock_run.call_args[0][0]
            assert "a reference to" in script

    def test_inbox_uses_batch(self, client, sample_tasks_json):
        """inbox path uses batch extraction after #368."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(inbox_only=True)
            script = mock_run.call_args[0][0]
            assert "a reference to" in script

    def test_no_filter_uses_batch(self, client, sample_tasks_json):
        """Unfiltered get_tasks should also use batch extraction (whose completed is false)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks()
            script = mock_run.call_args[0][0]
            assert "a reference to" in script
            assert "id of ft" in script

    def test_batch_uses_batch_subtask_count(self, client, sample_tasks_json):
        """Batch mode should batch-read subtask counts, not per-task IPC."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(flagged_only=True)
            script = mock_run.call_args[0][0]
            # Should batch-read subtask counts before the loop
            assert "number of tasks of ft" in script
            # Should NOT use per-task count of tasks
            assert "count of (tasks of" not in script


class TestGetProjectsBatchOptimization:
    """Tests that get_projects task_health/last_activity use batch property reads."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    @pytest.fixture
    def sample_projects_json(self):
        return json.dumps([{
            "id": "proj-001", "name": "Test Project", "note": "",
            "status": "active", "sequential": False, "folderPath": "",
            "creationDate": None, "modificationDate": None,
            "completionDate": None, "droppedDate": None,
            "lastActivityDate": None, "lastReviewDate": None,
            "nextReviewDate": None, "remainingCount": 3,
            "availableCount": 2, "overdueCount": 1, "deferredCount": 0,
            "hasDeferredOnly": False
        }])

    def test_baseline_uses_batch_project_reads(self, client, sample_projects_json):
        """Baseline get_projects should batch-read project properties, not per-project IPC."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            client.get_projects()
            script = mock_run.call_args[0][0]
            # Should batch-read project properties
            assert "id of fp" in script
            assert "name of fp" in script
            assert "note of fp" in script
            assert "status of fp" in script
            # Should NOT use per-project property reads in a repeat loop
            assert "set projId to id of proj" not in script

    def test_task_health_uses_global_batch(self, client, sample_projects_json):
        """include_task_health should use global task batch, not per-project reads."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            client.get_projects(include_task_health=True)
            script = mock_run.call_args[0][0]
            # Should batch-read ALL tasks globally
            assert "a reference to flattened tasks" in script
            assert "id of (containing project of ft)" in script
            # Should NOT do per-project task reads
            assert "flattened tasks of (item i of projRefs)" not in script

    def test_last_activity_uses_global_batch(self, client, sample_projects_json):
        """include_last_activity should use global task batch, not per-project reads."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            client.get_projects(include_last_activity=True)
            script = mock_run.call_args[0][0]
            # Should batch-read ALL tasks globally
            assert "a reference to flattened tasks" in script
            assert "id of (containing project of ft)" in script
            # Should NOT do per-project task reads
            assert "flattened tasks of (item i of projRefs)" not in script

    def test_task_health_global_batch_reads_required_properties(self, client, sample_projects_json):
        """Task health global batch should read completed, dropped, blocked, defer date, due date."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            client.get_projects(include_task_health=True)
            script = mock_run.call_args[0][0]
            assert "completed of ft" in script
            assert "dropped of ft" in script
            assert "blocked of ft" in script
            assert "defer date of ft" in script
            assert "due date of ft" in script

    def test_last_activity_global_batch_reads_required_properties(self, client, sample_projects_json):
        """Last activity global batch should read creation date and completion date."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            client.get_projects(include_last_activity=True)
            script = mock_run.call_args[0][0]
            assert "creation date of ft" in script
            assert "completion date of ft" in script

    def test_task_health_uses_parallel_counter_lists(self, client, sample_projects_json):
        """Task health should use parallel counter lists indexed by project position."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            client.get_projects(include_task_health=True)
            script = mock_run.call_args[0][0]
            assert "remainingCounts" in script
            assert "availableCounts" in script
            assert "overdueCounts" in script
            assert "deferredCounts" in script


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

    def test_update_task_sequential_true(self, client):
        """#307: update_task() sets sequential flag on action groups."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task("task-001", sequential=True)
            assert result["success"] is True
            call_args = mock_run.call_args[0][0]
            assert "sequential:true" in call_args

    def test_update_task_sequential_false(self, client):
        """#307: update_task() can set sequential to false."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task("task-001", sequential=False)
            assert result["success"] is True
            call_args = mock_run.call_args[0][0]
            assert "sequential:false" in call_args

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

    def test_update_task_planned_date(self, client):
        """#252: update_task supports planned_date parameter."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task("task-001", planned_date="2026-03-15")
            assert result["success"] is True
            call_args = mock_run.call_args[0][0]
            assert "planned date" in call_args
            assert "March 15, 2026" in call_args

    def test_update_task_clear_planned_date(self, client):
        """#252: update_task clears planned_date with empty string."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task("task-001", planned_date="")
            assert result["success"] is True
            call_args = mock_run.call_args[0][0]
            assert "planned date" in call_args
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


class TestFolderStatus:
    """Tests for folder status (active/dropped) in get_folders and update_folder."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    def _make_folders_json(self, hidden: bool = False):
        return json.dumps([{
            "id": "folder-001", "name": "Work", "path": "Work",
            "hidden": hidden,
        }])

    # --- get_folders ---

    def test_get_folders_returns_status_active(self, client):
        """get_folders returns status='active' for non-hidden folders."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = self._make_folders_json(hidden=False)
            folders = client.get_folders()
            assert folders[0]["status"] == "active"

    def test_get_folders_returns_status_dropped(self, client):
        """get_folders returns status='dropped' for hidden folders."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = self._make_folders_json(hidden=True)
            folders = client.get_folders()
            assert folders[0]["status"] == "dropped"

    def test_get_folders_applescript_reads_hidden(self, client):
        """get_folders AppleScript must read the hidden property per folder."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = self._make_folders_json()
            client.get_folders()
            script = mock_run.call_args[0][0]
            assert "hidden of f" in script

    # --- update_folder ---

    def test_update_folder_drop_sets_hidden_true(self, client):
        """update_folder(status='dropped') sets hidden to true in AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_folder("folder-001", status="dropped")
            assert result["success"] is True
            script = mock_run.call_args[0][0]
            assert "hidden" in script
            assert "true" in script

    def test_update_folder_activate_sets_hidden_false(self, client):
        """update_folder(status='active') sets hidden to false in AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_folder("folder-001", status="active")
            assert result["success"] is True
            script = mock_run.call_args[0][0]
            assert "hidden" in script
            assert "false" in script

    def test_update_folder_status_in_updated_fields(self, client):
        """status change is reflected in updated_fields."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_folder("folder-001", status="dropped")
            assert "status" in result["updated_fields"]

    def test_update_folder_invalid_status_raises(self, client):
        """Invalid status raises ValueError."""
        with pytest.raises(ValueError, match="Invalid status"):
            client.update_folder("folder-001", status="invalid")

    def test_update_folder_no_fields_raises(self, client):
        """No fields provided raises ValueError."""
        with pytest.raises(ValueError):
            client.update_folder("folder-001")


class TestGetPerspectives:
    """Tests for get_perspectives method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusConnector(enable_safety_checks=False)

    def test_get_perspectives_returns_dicts(self, client):
        """Test that perspectives return list of dicts with name, id, type."""
        json_result = '[{"name":"Inbox","id":null,"type":"built-in"},{"name":"Daily Worklist","id":"m3NLQ","type":"custom"}]'
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = json_result
            perspectives = client.get_perspectives()
            assert len(perspectives) == 2
            assert perspectives[0]["name"] == "Inbox"
            assert perspectives[0]["id"] is None
            assert perspectives[0]["type"] == "built-in"
            assert perspectives[1]["name"] == "Daily Worklist"
            assert perspectives[1]["id"] == "m3NLQ"
            assert perspectives[1]["type"] == "custom"

    def test_get_perspectives_empty(self, client):
        """Test when no perspectives exist."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            perspectives = client.get_perspectives()
            assert perspectives == []

    def test_get_perspectives_error(self, client):
        """Test handling of errors."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.get_perspectives()
            assert "Error retrieving perspectives" in str(exc_info.value)

    def test_get_perspectives_uses_every_perspective_for_type_detection(self, client):
        """Type detection should use 'every perspective' lookup, not 'first custom perspective'."""
        json_result = '[{"name":"Inbox","id":null,"type":"built-in"}]'
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = json_result
            client.get_perspectives()
            script = mock_run.call_args[0][0]
            assert "every perspective" in script
            assert "first custom perspective" not in script


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


class TestSetFocus:
    """Tests for set_focus method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusConnector(enable_safety_checks=False)

    def test_set_focus_single_project(self, client):
        """Test focusing on a single project (string normalizes to list)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "SUCCESS"
            result = client.set_focus(item_ids="proj-123", item_types="project")
            assert result["success"] is True
            assert result["action"] == "set"
            assert result["focused_items"] == [{"id": "proj-123", "type": "project"}]
            call_args = mock_run.call_args[0][0]
            assert 'proj-123' in call_args
            assert 'flattened project' in call_args
            assert 'set focus to' in call_args

    def test_set_focus_single_folder(self, client):
        """Test focusing on a single folder uses flattened folders for nested support."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "SUCCESS"
            result = client.set_focus(item_ids="folder-456", item_types="folder")
            assert result["success"] is True
            assert result["action"] == "set"
            assert result["focused_items"] == [{"id": "folder-456", "type": "folder"}]
            call_args = mock_run.call_args[0][0]
            assert 'flattened folders whose id' in call_args

    def test_set_focus_multiple_items(self, client):
        """Test focusing on multiple items."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "SUCCESS"
            result = client.set_focus(
                item_ids=["proj-1", "folder-2"],
                item_types=["project", "folder"],
            )
            assert result["success"] is True
            assert result["action"] == "set"
            assert len(result["focused_items"]) == 2
            assert result["focused_items"][0] == {"id": "proj-1", "type": "project"}
            assert result["focused_items"][1] == {"id": "folder-2", "type": "folder"}
            call_args = mock_run.call_args[0][0]
            assert 'proj-1' in call_args
            assert 'folder-2' in call_args
            assert 'focusList' in call_args

    def test_set_focus_clear_no_args(self, client):
        """Test clearing focus with no arguments."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "CLEARED"
            result = client.set_focus()
            assert result["success"] is True
            assert result["action"] == "cleared"
            assert result["focused_items"] == []
            call_args = mock_run.call_args[0][0]
            assert 'set focus to {}' in call_args

    def test_set_focus_clear_empty_lists(self, client):
        """Test clearing focus with empty lists."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "CLEARED"
            result = client.set_focus(item_ids=[], item_types=[])
            assert result["action"] == "cleared"

    def test_set_focus_mismatched_lengths(self, client):
        """Test that mismatched ID/type lengths raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            client.set_focus(item_ids=["a", "b"], item_types=["project"])
        assert "same length" in str(exc_info.value)

    def test_set_focus_invalid_type_task(self, client):
        """Test that task type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            client.set_focus(item_ids="task-1", item_types="task")
        assert "OmniFocus only supports setting focus on projects and folders" in str(exc_info.value)

    def test_set_focus_invalid_type_unknown(self, client):
        """Test that unknown types raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            client.set_focus(item_ids="x", item_types="invalid")
        assert "item_type must be" in str(exc_info.value)

    def test_set_focus_applescript_error(self, client):
        """Test handling of AppleScript errors."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="not found")
            with pytest.raises(Exception) as exc_info:
                client.set_focus(item_ids="proj-bad", item_types="project")
            assert "Error setting focus" in str(exc_info.value)

    def test_set_focus_escapes_special_characters(self, client):
        """Test that IDs with special characters are properly escaped."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "SUCCESS"
            result = client.set_focus(item_ids='proj-"test', item_types="project")
            assert result["success"] is True
            call_args = mock_run.call_args[0][0]
            assert '\\"' in call_args


class TestGetFocus:
    """Tests for get_focus method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusConnector(enable_safety_checks=False)

    def test_get_focus_with_items(self, client):
        """Test reading focus with items focused."""
        json_result = '[{"id":"proj-1","name":"My Project","type":"project"}]'
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = json_result
            result = client.get_focus()
            assert len(result) == 1
            assert result[0]["id"] == "proj-1"
            assert result[0]["name"] == "My Project"
            assert result[0]["type"] == "project"

    def test_get_focus_multiple_items(self, client):
        """Test reading focus with multiple items."""
        json_result = '[{"id":"proj-1","name":"Proj","type":"project"},{"id":"fold-2","name":"Fold","type":"folder"}]'
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = json_result
            result = client.get_focus()
            assert len(result) == 2

    def test_get_focus_empty(self, client):
        """Test reading focus when no focus is set."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            result = client.get_focus()
            assert result == []

    def test_get_focus_error(self, client):
        """Test handling of AppleScript errors."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.get_focus()
            assert "Error getting focus" in str(exc_info.value)



class TestBatchUpdateTasks:
    """Tests for batched update_tasks() — or-chain optimization (#215).

    Bulk-settable fields (flagged, estimated_minutes, due_date, defer_date,
    completed=True) use whose or-chain for near-constant time.
    Per-task fields (tags, moves, completed=False, status) use repeat loop.
    Mixed fields produce hybrid scripts with both.
    """

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    # ========================================================================
    # Basic contract: single call, return values, validation
    # ========================================================================

    def test_batch_update_single_applescript_call(self, client):
        """update_tasks() should make exactly one AppleScript call."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "3"
            result = client.update_tasks(
                ["task-001", "task-002", "task-003"],
                flagged=True
            )
            assert mock_run.call_count == 1
            assert result["updated_count"] == 3

    def test_batch_update_returns_correct_counts(self, client):
        """Return value should reflect success count from AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            result = client.update_tasks(
                ["task-001", "task-002", "task-003"],
                flagged=True
            )
            assert result["updated_count"] == 2
            assert result["failed_count"] == 1

    def test_batch_update_single_id_string(self, client):
        """Single string task_id should work (normalized to list)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "1"
            result = client.update_tasks("task-001", flagged=True)
            assert result["updated_count"] == 1

    def test_batch_update_validation_no_fields(self, client):
        """Should raise ValueError if no fields provided."""
        with pytest.raises(ValueError, match="Must provide at least one field"):
            client.update_tasks(["task-001"])

    def test_batch_update_validation_task_name_rejected(self, client):
        """Should raise ValueError if task_name is passed."""
        with pytest.raises(ValueError, match="task_name is not allowed"):
            client.update_tasks(["task-001"], task_name="New Name")

    def test_batch_update_validation_note_rejected(self, client):
        """Should raise ValueError if note is passed."""
        with pytest.raises(ValueError, match="note is not allowed"):
            client.update_tasks(["task-001"], note="New note")

    # ========================================================================
    # Bulk-settable fields: use or-chain (no repeat loop)
    # ========================================================================

    def test_bulk_flagged_uses_or_chain(self, client):
        """Bulk-settable flagged uses or-chain, no repeat loop."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "3"
            client.update_tasks(["t1", "t2", "t3"], flagged=True)
            script = mock_run.call_args[0][0]
            assert 'whose id is "t1" or id is "t2" or id is "t3"' in script
            assert "flagged" in script
            assert "repeat with" not in script

    def test_bulk_estimated_minutes_uses_or_chain(self, client):
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_tasks(["t1", "t2"], estimated_minutes=30)
            script = mock_run.call_args[0][0]
            assert "estimated minutes" in script
            assert "30" in script
            assert "repeat with" not in script

    def test_bulk_due_date_uses_or_chain(self, client):
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_tasks(["t1", "t2"], due_date="2026-12-25")
            script = mock_run.call_args[0][0]
            assert "due date" in script
            assert "December 25, 2026" in script
            assert "repeat with" not in script

    def test_bulk_clear_due_date_uses_or_chain(self, client):
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_tasks(["t1", "t2"], due_date="")
            script = mock_run.call_args[0][0]
            assert "missing value" in script
            assert "repeat with" not in script

    def test_bulk_defer_date_uses_or_chain(self, client):
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_tasks(["t1", "t2"], defer_date="2026-06-01")
            script = mock_run.call_args[0][0]
            assert "defer date" in script
            assert "repeat with" not in script

    def test_bulk_planned_date_uses_or_chain(self, client):
        """#252: Batch planned_date uses or-chain (bulk-settable)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_tasks(["t1", "t2"], planned_date="2026-03-15")
            script = mock_run.call_args[0][0]
            assert "planned date" in script
            assert "March 15, 2026" in script
            assert "repeat with" not in script

    def test_bulk_mark_complete_uses_or_chain(self, client):
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "3"
            client.update_tasks(["t1", "t2", "t3"], completed=True)
            script = mock_run.call_args[0][0]
            assert "mark complete" in script
            assert "whose" in script
            assert "repeat with" not in script

    # ========================================================================
    # Per-task fields: must use repeat loop
    # ========================================================================

    def test_per_task_completed_false_uses_repeat_loop(self, client):
        """completed=False cannot be bulk-set (error -10006)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_tasks(["t1", "t2"], completed=False)
            script = mock_run.call_args[0][0]
            assert "repeat with" in script
            assert "set completed" in script

    def test_per_task_tags_uses_repeat_loop(self, client):
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_tasks(["t1", "t2"], add_tags=["urgent"])
            script = mock_run.call_args[0][0]
            assert "repeat with" in script

    def test_per_task_project_move_uses_repeat_loop(self, client):
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_tasks(["t1", "t2"], project_id="proj-1")
            script = mock_run.call_args[0][0]
            assert "repeat with" in script
            assert "move" in script

    def test_per_task_status_dropped_uses_repeat_loop(self, client):
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_tasks(["t1", "t2"], status="dropped")
            script = mock_run.call_args[0][0]
            assert "repeat with" in script
            assert "mark dropped" in script.lower() or "dropped" in script

    # ========================================================================
    # Mixed fields: hybrid script (bulk + repeat loop)
    # ========================================================================

    def test_mixed_fields_uses_hybrid(self, client):
        """Mixed bulk + per-task fields produce hybrid script."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_tasks(["t1", "t2"], flagged=True, add_tags=["urgent"])
            script = mock_run.call_args[0][0]
            # Bulk part: or-chain for flagged
            assert "set flagged" in script
            assert "whose" in script
            # Per-task part: repeat loop for tags
            assert "repeat with" in script

    def test_per_task_script_has_try_on_error(self, client):
        """Per-task repeat loop should have error handling."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_tasks(["t1", "t2"], add_tags=["urgent"])
            script = mock_run.call_args[0][0]
            assert "try" in script
            assert "on error" in script


class TestBatchUpdateProjects:
    """Tests for batched update_projects() — or-chain optimization (#215).

    Bulk-settable fields (sequential, status, review_interval_weeks,
    last_reviewed, next_review_date) use whose or-chain.
    Per-project fields (folder_path) use repeat loop.
    """

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    # ========================================================================
    # Basic contract: single call, return values, validation
    # ========================================================================

    def test_batch_update_single_applescript_call(self, client):
        """update_projects() should make exactly one AppleScript call."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            result = client.update_projects(
                ["proj-001", "proj-002"],
                sequential=True
            )
            assert mock_run.call_count == 1
            assert result["updated_count"] == 2

    def test_batch_update_returns_correct_counts(self, client):
        """Return value should reflect success count."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "1"
            result = client.update_projects(
                ["proj-001", "proj-002"],
                status="on_hold"
            )
            assert result["updated_count"] == 1
            assert result["failed_count"] == 1

    def test_batch_update_validation_name_rejected(self, client):
        """Should raise ValueError if project_name is passed."""
        with pytest.raises(ValueError, match="project_name"):
            client.update_projects(["proj-001"], project_name="New Name")

    def test_batch_update_validation_note_rejected(self, client):
        """Should raise ValueError if note is passed."""
        with pytest.raises(ValueError, match="note"):
            client.update_projects(["proj-001"], note="New note")

    # ========================================================================
    # Bulk-settable fields: use or-chain (no repeat loop)
    # ========================================================================

    def test_bulk_sequential_uses_or_chain(self, client):
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_projects(["p1", "p2"], sequential=True)
            script = mock_run.call_args[0][0]
            assert 'whose id is "p1" or id is "p2"' in script
            assert "sequential" in script
            assert "repeat with" not in script

    def test_bulk_status_on_hold_uses_or_chain(self, client):
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_projects(["p1", "p2"], status="on_hold")
            script = mock_run.call_args[0][0]
            assert "whose" in script
            assert "on hold" in script
            assert "repeat with" not in script

    def test_bulk_status_active_uses_or_chain(self, client):
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_projects(["p1", "p2"], status="active")
            script = mock_run.call_args[0][0]
            assert "whose" in script
            assert "repeat with" not in script

    def test_bulk_status_done_uses_or_chain(self, client):
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "1"
            client.update_projects(["p1"], status="done")
            script = mock_run.call_args[0][0]
            assert "mark complete" in script
            assert "whose" in script
            assert "repeat with" not in script

    def test_bulk_review_interval_uses_or_chain(self, client):
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_projects(["p1", "p2"], review_interval_weeks=2)
            script = mock_run.call_args[0][0]
            assert "review interval" in script
            assert "whose" in script
            assert "repeat with" not in script

    # ========================================================================
    # Per-project fields: must use repeat loop
    # ========================================================================

    def test_per_project_folder_uses_repeat_loop(self, client):
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_projects(["p1", "p2"], folder_path="Work")
            script = mock_run.call_args[0][0]
            assert "repeat with" in script
            assert "move" in script

    # ========================================================================
    # Mixed fields: hybrid script (bulk + repeat loop)
    # ========================================================================

    def test_mixed_fields_uses_hybrid(self, client):
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            client.update_projects(["p1", "p2"], status="active", folder_path="Work")
            script = mock_run.call_args[0][0]
            assert "whose" in script  # Bulk part
            assert "repeat with" in script  # Per-project part


class TestBuildWhoseOrChain:
    """Tests for _build_whose_or_chain() helper."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    def test_single_id(self, client):
        result = client._build_whose_or_chain(["abc"], "flattened task")
        assert result == 'every flattened task whose id is "abc"'

    def test_multiple_ids(self, client):
        result = client._build_whose_or_chain(["abc", "def", "ghi"], "flattened task")
        assert result == 'every flattened task whose id is "abc" or id is "def" or id is "ghi"'

    def test_project_entity(self, client):
        result = client._build_whose_or_chain(["p1", "p2"], "flattened project")
        assert result == 'every flattened project whose id is "p1" or id is "p2"'

    def test_escapes_ids(self, client):
        result = client._build_whose_or_chain(['a"b'], "flattened task")
        assert 'a\\"b' in result


class TestGetTaskIdsForTags:
    """Tests for _get_task_ids_for_tags() — tag-side pre-filter for performance."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    def test_and_mode_single_tag(self, client):
        """AND mode with one tag returns task IDs from that tag's tasks."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # AppleScript returns pipe-delimited groups, one per tag
            mock_run.return_value = "task-1,task-2,task-3|"
            result = client._get_task_ids_for_tags(["urgent"], "and", include_completed=False)
            assert result == {"task-1", "task-2", "task-3"}
            # Verify AppleScript queries from the tag side
            script = mock_run.call_args[0][0]
            assert "first flattened tag whose name is" in script
            assert "urgent" in script

    def test_and_mode_multiple_tags_intersects(self, client):
        """AND mode with multiple tags returns intersection of task ID sets."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # Tag "urgent" has tasks 1,2,3; tag "work" has tasks 2,3,4
            mock_run.return_value = "task-1,task-2,task-3|task-2,task-3,task-4|"
            result = client._get_task_ids_for_tags(["urgent", "work"], "and", include_completed=False)
            assert result == {"task-2", "task-3"}

    def test_or_mode_unions(self, client):
        """OR mode returns union of task ID sets."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "task-1,task-2|task-3,task-4|"
            result = client._get_task_ids_for_tags(["urgent", "work"], "or", include_completed=False)
            assert result == {"task-1", "task-2", "task-3", "task-4"}

    def test_tag_not_found_returns_none(self, client):
        """If a tag is not found, return None to signal fallback."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "TAG_NOT_FOUND|"
            result = client._get_task_ids_for_tags(["nonexistent"], "and", include_completed=False)
            assert result is None

    def test_empty_result_returns_empty_set(self, client):
        """If tag exists but has no tasks, return empty set."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "|"
            result = client._get_task_ids_for_tags(["empty-tag"], "and", include_completed=False)
            assert result == set()

    def test_include_completed_affects_script(self, client):
        """include_completed=True should not filter by completed status."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "task-1|"
            client._get_task_ids_for_tags(["urgent"], "and", include_completed=True)
            script = mock_run.call_args[0][0]
            assert "completed is false" not in script

    def test_include_completed_false_filters(self, client):
        """include_completed=False should filter tasks by completed status."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "task-1|"
            client._get_task_ids_for_tags(["urgent"], "and", include_completed=False)
            script = mock_run.call_args[0][0]
            assert "completed is false" in script

    def test_escapes_tag_names(self, client):
        """Tag names with special characters should be escaped."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "task-1|"
            client._get_task_ids_for_tags(['tag"with"quotes'], "and", include_completed=False)
            script = mock_run.call_args[0][0]
            assert 'tag\\"with\\"quotes' in script


class TestIdEscapingInMethods:
    """Verify _escape_applescript_string is applied to IDs in all methods."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    def test_get_tasks_escapes_task_id(self, client):
        """get_tasks() should escape task_id in whose clause."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            client.get_tasks(task_id='id"inject')
            script = mock_run.call_args[0][0]
            assert 'id\\"inject' in script
            assert 'id"inject' not in script

    def test_get_tasks_escapes_project_id(self, client):
        """get_tasks() should escape project_id in whose clause."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            client.get_tasks(project_id='proj"bad')
            script = mock_run.call_args[0][0]
            assert 'proj\\"bad' in script

    def test_get_projects_escapes_project_id(self, client):
        """get_projects() should escape project_id in whose clause."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            client.get_projects(project_id='p"inject')
            script = mock_run.call_args[0][0]
            assert 'p\\"inject' in script

    def test_delete_tasks_escapes_ids(self, client):
        """delete_tasks() should escape IDs in the AppleScript list."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "1"
            client.delete_tasks(['t"bad'])
            script = mock_run.call_args[0][0]
            assert 't\\"bad' in script
            assert 't"bad' not in script

    def test_delete_projects_escapes_ids(self, client):
        """delete_projects() should escape IDs in the AppleScript list."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "1"
            client.delete_projects(['p"bad'])
            script = mock_run.call_args[0][0]
            assert 'p\\"bad' in script

    def test_reorder_task_escapes_ids(self, client):
        """reorder_task() should escape task_id and reference_task_id."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            client.reorder_task(task_id='t"1', before_task_id='t"2')
            script = mock_run.call_args[0][0]
            assert 't\\"1' in script
            assert 't\\"2' in script

    def test_reorder_project_escapes_ids(self, client):
        """reorder_project() should escape project_id and reference_project_id."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            client.reorder_project(project_id='p"1', before_project_id='p"2')
            script = mock_run.call_args[0][0]
            assert 'p\\"1' in script
            assert 'p\\"2' in script


class TestUndropTaskLimitation:
    """Tests that undropping tasks raises a clear error (#372)."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    def test_update_task_status_active_raises_valueerror(self, client):
        """update_task(status=ACTIVE) should raise ValueError — OmniFocus cannot undrop tasks."""
        with pytest.raises(ValueError, match="Cannot undrop"):
            client.update_task("task-001", status=TaskStatus.ACTIVE)

    def test_update_tasks_status_active_raises_valueerror(self, client):
        """update_tasks(status=ACTIVE) should raise ValueError — OmniFocus cannot undrop tasks."""
        with pytest.raises(ValueError, match="Cannot undrop"):
            client.update_tasks(["task-001"], status=TaskStatus.ACTIVE)


class TestReorderProject:
    """Tests for reorder_project method."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    def test_reorder_project_before(self, client):
        """reorder_project() with before_project_id uses 'before' in AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.reorder_project("proj-A", before_project_id="proj-B")
            assert result is True
            script = mock_run.call_args[0][0]
            assert "before" in script
            assert "proj-A" in script
            assert "proj-B" in script

    def test_reorder_project_after(self, client):
        """reorder_project() with after_project_id uses 'after' in AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.reorder_project("proj-A", after_project_id="proj-C")
            assert result is True
            script = mock_run.call_args[0][0]
            assert "after" in script
            assert "proj-A" in script
            assert "proj-C" in script

    def test_reorder_project_requires_one_param(self, client):
        """reorder_project() raises ValueError when both or neither params provided."""
        with pytest.raises(ValueError, match="Must provide either"):
            client.reorder_project("proj-A")
        with pytest.raises(ValueError, match="Cannot provide both"):
            client.reorder_project("proj-A", before_project_id="proj-B", after_project_id="proj-C")

    def test_reorder_project_requires_project_id(self, client):
        """reorder_project() raises ValueError on empty project_id."""
        with pytest.raises(ValueError, match="project_id"):
            client.reorder_project("", before_project_id="proj-B")

    def test_reorder_project_uses_flattened_project(self, client):
        """reorder_project() uses 'flattened project' in AppleScript (not 'flattened task')."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            client.reorder_project("proj-A", before_project_id="proj-B")
            script = mock_run.call_args[0][0]
            assert "flattened project" in script
            assert "flattened task" not in script

    def test_reorder_project_raises_on_failure(self, client):
        """reorder_project() raises Exception on AppleScript failure."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "false: Projects not in same folder"
            with pytest.raises(Exception, match="reordering project"):
                client.reorder_project("proj-A", before_project_id="proj-B")


class TestGetTags:
    """Tests for get_tags method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusConnector(enable_safety_checks=False)

    def test_get_tags_reads_actual_status(self, client):
        """AppleScript should read 'allows next action' to determine tag status."""
        json_result = '[{"id":"abc","name":"Work","status":"active"}]'
        exclusivity_json = '{"abc": false}'
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = [json_result, exclusivity_json]
            client.get_tags()
            script = mock_run.call_args_list[0][0][0]
            assert "allows next action" in script


class TestAvailableOnlyOnHoldTags:
    """Tests for available_only excluding tasks with On Hold tags (#261)."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    def test_available_only_script_contains_on_hold_tag_check(self, client):
        """When On Hold tags exist, the get_tasks script should check for them."""
        tasks_json = json.dumps([])
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # First call: _get_on_hold_tag_names returns On Hold tags
            # Second call: get_tasks main script returns empty task list
            mock_run.side_effect = ["Waiting, On Hold", tasks_json]
            client.get_tasks(available_only=True)
            # The main get_tasks script (second call) should reference onHoldTags
            main_script = mock_run.call_args_list[1][0][0]
            assert "onHoldTags" in main_script
            assert "Waiting" in main_script
            assert "On Hold" in main_script

    def test_available_only_without_on_hold_tags_skips_check(self, client):
        """When no On Hold tags exist, the script should not include the check."""
        tasks_json = json.dumps([])
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # First call: no On Hold tags
            # Second call: get_tasks main script
            mock_run.side_effect = ["", tasks_json]
            client.get_tasks(available_only=True)
            main_script = mock_run.call_args_list[1][0][0]
            assert "onHoldTags" not in main_script


class TestGetOnHoldTagNames:
    """Tests for _get_on_hold_tag_names() — pre-fetches On Hold tag names."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    def test_returns_on_hold_and_dropped_tag_names(self, client):
        """Returns tag names where allows next action is false or hidden is true."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "Waiting, On Hold, Archived"
            result = client._get_on_hold_tag_names()
            assert result == ["Waiting", "On Hold", "Archived"]
            script = mock_run.call_args[0][0]
            assert "allows next action is false or hidden is true" in script

    def test_returns_empty_list_when_no_on_hold_tags(self, client):
        """Returns empty list when no tags are On Hold."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = ""
            result = client._get_on_hold_tag_names()
            assert result == []

    def test_handles_applescript_error_gracefully(self, client):
        """Returns empty list if AppleScript errors."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = Exception("AppleScript error")
            result = client._get_on_hold_tag_names()
            assert result == []


class TestRruleToSummary:
    """Tests for _rrule_to_summary() RRULE parser."""

    def test_daily(self):
        assert OmniFocusConnector._rrule_to_summary("FREQ=DAILY") == "Every day"

    def test_daily_interval(self):
        assert OmniFocusConnector._rrule_to_summary("FREQ=DAILY;INTERVAL=3") == "Every 3 days"

    def test_weekly(self):
        assert OmniFocusConnector._rrule_to_summary("FREQ=WEEKLY") == "Every week"

    def test_weekly_with_day(self):
        assert OmniFocusConnector._rrule_to_summary("FREQ=WEEKLY;INTERVAL=1;BYDAY=MO") == "Every week on Mon"

    def test_weekly_interval_with_days(self):
        assert OmniFocusConnector._rrule_to_summary("FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,WE,FR") == "Every 2 weeks on Mon, Wed, Fri"

    def test_monthly(self):
        assert OmniFocusConnector._rrule_to_summary("FREQ=MONTHLY") == "Every month"

    def test_monthly_interval(self):
        assert OmniFocusConnector._rrule_to_summary("FREQ=MONTHLY;INTERVAL=3") == "Every 3 months"

    def test_yearly(self):
        assert OmniFocusConnector._rrule_to_summary("FREQ=YEARLY") == "Every year"

    def test_yearly_interval(self):
        assert OmniFocusConnector._rrule_to_summary("FREQ=YEARLY;INTERVAL=2") == "Every 2 years"

    def test_fallback_unparseable(self):
        """Unparseable strings return the raw input."""
        assert OmniFocusConnector._rrule_to_summary("SOMETHING_WEIRD") == "SOMETHING_WEIRD"

    def test_fallback_empty(self):
        """Empty string returns empty string."""
        assert OmniFocusConnector._rrule_to_summary("") == ""

    def test_interval_1_omitted(self):
        """INTERVAL=1 should not produce 'Every 1 weeks', just 'Every week'."""
        assert OmniFocusConnector._rrule_to_summary("FREQ=WEEKLY;INTERVAL=1") == "Every week"

    def test_daily_interval_1(self):
        """INTERVAL=1 for daily should say 'Every day' not 'Every 1 days'."""
        assert OmniFocusConnector._rrule_to_summary("FREQ=DAILY;INTERVAL=1") == "Every day"


class TestProjectType:
    """Tests for projectType field (parallel / sequential / single_actions)."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    def _make_projects_json(self, singleton: bool = False, sequential: bool = False):
        return json.dumps([{
            "id": "proj-001", "name": "Test Project", "note": "",
            "status": "active", "sequential": sequential,
            "singletonActionHolder": singleton,
            "folderPath": "", "creationDate": None, "modificationDate": None,
            "completionDate": None, "droppedDate": None,
            "lastActivityDate": None, "lastReviewDate": None,
            "nextReviewDate": None,
        }])

    # --- get_projects ---

    def test_get_projects_batch_reads_singleton_action_holder(self, client):
        """get_projects AppleScript must batch-read singleton action holder."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = self._make_projects_json()
            client.get_projects()
            script = mock_run.call_args[0][0]
            assert "singleton action holder of fp" in script

    def test_get_projects_returns_project_type_parallel(self, client):
        """Parallel project (singleton=false, sequential=false) → projectType 'parallel'."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = self._make_projects_json(singleton=False, sequential=False)
            projects = client.get_projects()
            assert projects[0]["projectType"] == "parallel"

    def test_get_projects_returns_project_type_sequential(self, client):
        """Sequential project (singleton=false, sequential=true) → projectType 'sequential'."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = self._make_projects_json(singleton=False, sequential=True)
            projects = client.get_projects()
            assert projects[0]["projectType"] == "sequential"

    def test_get_projects_returns_project_type_single_actions(self, client):
        """Single Actions List (singleton=true) → projectType 'single_actions'."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = self._make_projects_json(singleton=True, sequential=False)
            projects = client.get_projects()
            assert projects[0]["projectType"] == "single_actions"

    # --- create_project ---

    def test_create_project_single_actions_sets_singleton(self, client):
        """project_type='single_actions' must set singleton action holder:true in AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            client.create_project("My SAL", project_type="single_actions")
            script = mock_run.call_args[0][0]
            assert "singleton action holder:true" in script

    def test_create_project_parallel_does_not_set_singleton(self, client):
        """project_type='parallel' must not set singleton action holder:true."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            client.create_project("My Parallel", project_type="parallel")
            script = mock_run.call_args[0][0]
            assert "singleton action holder:true" not in script

    def test_create_project_sequential_via_project_type(self, client):
        """project_type='sequential' sets sequential:true."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            client.create_project("My Sequential", project_type="sequential")
            script = mock_run.call_args[0][0]
            assert "sequential:true" in script

    def test_create_project_default_is_parallel(self, client):
        """Default (no project_type, no sequential) creates a parallel project."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            client.create_project("Default")
            script = mock_run.call_args[0][0]
            assert "singleton action holder:true" not in script
            assert "sequential:false" in script

    # --- update_project ---

    def test_update_project_type_single_actions(self, client):
        """update_project(project_type='single_actions') sets singleton action holder."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_project("proj-001", project_type="single_actions")
            assert result["success"] is True
            script = mock_run.call_args[0][0]
            assert "singleton action holder" in script
            assert "true" in script

    def test_update_project_type_parallel(self, client):
        """update_project(project_type='parallel') clears singleton action holder."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_project("proj-001", project_type="parallel")
            assert result["success"] is True
            script = mock_run.call_args[0][0]
            assert "singleton action holder" in script

    def test_update_project_type_in_updated_fields(self, client):
        """project_type change is reflected in updated_fields."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_project("proj-001", project_type="single_actions")
            assert "project_type" in result["updated_fields"]


class TestCompletedByChildren:
    """Tests for completed_by_children (completed by children) property."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    def _make_projects_json(self, completed_by_children: bool = False):
        return json.dumps([{
            "id": "proj-001", "name": "Test Project", "note": "",
            "status": "active", "sequential": False,
            "singletonActionHolder": False,
            "completedByChildren": completed_by_children,
            "folderPath": "", "creationDate": None, "modificationDate": None,
            "completionDate": None, "droppedDate": None,
            "lastActivityDate": None, "lastReviewDate": None,
            "nextReviewDate": None,
        }])

    # --- get_projects ---

    def test_get_projects_batch_reads_completed_by_children(self, client):
        """get_projects AppleScript must batch-read 'completed by children'."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = self._make_projects_json()
            client.get_projects()
            script = mock_run.call_args[0][0]
            assert "completed by children of fp" in script

    def test_get_projects_returns_completed_by_children_true(self, client):
        """completedByChildren=true in JSON → True in returned project dict."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = self._make_projects_json(completed_by_children=True)
            projects = client.get_projects()
            assert projects[0]["completedByChildren"] is True

    def test_get_projects_returns_completed_by_children_false(self, client):
        """completedByChildren=false in JSON → False in returned project dict."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = self._make_projects_json(completed_by_children=False)
            projects = client.get_projects()
            assert projects[0]["completedByChildren"] is False

    # --- create_project ---

    def test_create_project_completed_by_children_true(self, client):
        """create_project(completed_by_children=True) sets the property in AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            client.create_project("My Project", completed_by_children=True)
            script = mock_run.call_args[0][0]
            assert "completed by children:true" in script

    def test_create_project_completed_by_children_false(self, client):
        """create_project(completed_by_children=False) sets the property to false."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            client.create_project("My Project", completed_by_children=False)
            script = mock_run.call_args[0][0]
            assert "completed by children:false" in script

    def test_create_project_completed_by_children_none_not_set(self, client):
        """Default None does not set completed by children in AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            client.create_project("My Project")
            script = mock_run.call_args[0][0]
            assert "completed by children" not in script

    # --- update_project ---

    def test_update_project_completed_by_children_true(self, client):
        """update_project(completed_by_children=True) → updated_fields contains the key."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_project("proj-001", completed_by_children=True)
            assert result["success"] is True
            assert "completed_by_children" in result["updated_fields"]
            script = mock_run.call_args[0][0]
            assert "completed by children" in script

    def test_update_project_completed_by_children_false(self, client):
        """update_project(completed_by_children=False) sets property to false."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_project("proj-001", completed_by_children=False)
            assert result["success"] is True
            assert "completed_by_children" in result["updated_fields"]
            script = mock_run.call_args[0][0]
            assert "completed by children" in script


class TestStalledProjects:
    """Tests for stalled project detection (availableCount==0 and not hasDeferredOnly)."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    def _make_health_json(self, status="active status", available=0, remaining=0, deferred_only=False):
        return json.dumps([{
            "id": "proj-001", "name": "Test Project", "note": "",
            "status": status, "sequential": False,
            "singletonActionHolder": False, "completedByChildren": False,
            "folderPath": "", "creationDate": None, "modificationDate": None,
            "completionDate": None, "droppedDate": None,
            "lastActivityDate": None, "lastReviewDate": None,
            "nextReviewDate": None,
            "remainingCount": remaining, "availableCount": available,
            "overdueCount": 0, "deferredCount": 0 if not deferred_only else remaining,
            "hasDeferredOnly": deferred_only,
        }])

    # --- stalled field ---

    def test_get_projects_stalled_true_when_no_available_tasks(self, client):
        """Active project with availableCount=0 and hasDeferredOnly=False → stalled=True."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = self._make_health_json(available=0, remaining=2, deferred_only=False)
            projects = client.get_projects(include_task_health=True)
            assert projects[0]["stalled"] is True

    def test_get_projects_stalled_false_when_available_tasks(self, client):
        """Project with availableCount>0 → stalled=False."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = self._make_health_json(available=2, remaining=2)
            projects = client.get_projects(include_task_health=True)
            assert projects[0]["stalled"] is False

    def test_get_projects_stalled_false_when_deferred_only(self, client):
        """Project with hasDeferredOnly=True → stalled=False (appropriately scheduled)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = self._make_health_json(available=0, remaining=2, deferred_only=True)
            projects = client.get_projects(include_task_health=True)
            assert projects[0]["stalled"] is False

    def test_get_projects_stalled_true_when_no_remaining_tasks(self, client):
        """Active project with remainingCount=0 → stalled=True."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = self._make_health_json(available=0, remaining=0, deferred_only=False)
            projects = client.get_projects(include_task_health=True)
            assert projects[0]["stalled"] is True

    def test_get_projects_stalled_absent_without_task_health(self, client):
        """Without include_task_health, stalled field is not present."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = json.dumps([{
                "id": "proj-001", "name": "Test Project", "note": "",
                "status": "active status", "sequential": False,
                "singletonActionHolder": False, "completedByChildren": False,
                "folderPath": "", "creationDate": None, "modificationDate": None,
                "completionDate": None, "droppedDate": None,
                "lastActivityDate": None, "lastReviewDate": None, "nextReviewDate": None,
            }])
            projects = client.get_projects()
            assert "stalled" not in projects[0]

    # --- stalled_only filter ---

    def test_get_projects_stalled_only_returns_stalled_projects(self, client):
        """stalled_only=True returns only stalled projects."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = json.dumps([
                {
                    "id": "proj-001", "name": "Stalled", "note": "",
                    "status": "active status", "sequential": False,
                    "singletonActionHolder": False, "completedByChildren": False,
                    "folderPath": "", "creationDate": None, "modificationDate": None,
                    "completionDate": None, "droppedDate": None,
                    "lastActivityDate": None, "lastReviewDate": None, "nextReviewDate": None,
                    "remainingCount": 0, "availableCount": 0, "overdueCount": 0,
                    "deferredCount": 0, "hasDeferredOnly": False,
                },
                {
                    "id": "proj-002", "name": "Active", "note": "",
                    "status": "active status", "sequential": False,
                    "singletonActionHolder": False, "completedByChildren": False,
                    "folderPath": "", "creationDate": None, "modificationDate": None,
                    "completionDate": None, "droppedDate": None,
                    "lastActivityDate": None, "lastReviewDate": None, "nextReviewDate": None,
                    "remainingCount": 2, "availableCount": 2, "overdueCount": 0,
                    "deferredCount": 0, "hasDeferredOnly": False,
                },
            ])
            projects = client.get_projects(stalled_only=True)
            assert len(projects) == 1
            assert projects[0]["id"] == "proj-001"
            assert projects[0]["stalled"] is True

    def test_get_projects_stalled_only_implies_task_health(self, client):
        """stalled_only=True forces include_task_health=True in the AppleScript call."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = json.dumps([])
            client.get_projects(stalled_only=True)
            script = mock_run.call_args[0][0]
            # Task health AppleScript contains these counter lists
            assert "availableCounts" in script


class TestEffectiveDates:
    """Tests that get_tasks reads effective (inherited) dates, not just direct dates."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    @pytest.fixture
    def sample_tasks_json(self):
        return json.dumps([{
            "id": "task-001", "name": "Test Task", "note": "",
            "completed": False, "flagged": False, "dropped": False,
            "projectId": "proj-001", "projectName": "Test Project",
            "dueDate": "2025-10-15T17:00:00", "deferDate": "",
            "completionDate": "", "tags": "",
        }])

    def test_get_tasks_reads_effective_due_date(self, client, sample_tasks_json):
        """get_tasks should read effective due date (includes inherited) not direct due date."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks()
            script = mock_run.call_args[0][0]
            assert "effective due date" in script

    def test_get_tasks_reads_effective_defer_date(self, client, sample_tasks_json):
        """get_tasks should read effective defer date (includes inherited) not direct defer date."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks()
            script = mock_run.call_args[0][0]
            assert "effective defer date" in script

    def test_get_tasks_overdue_whose_uses_effective_due_date(self, client, sample_tasks_json):
        """overdue=True should filter on effective due date, not direct due date."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(overdue=True)
            script = mock_run.call_args[0][0]
            assert "effective due date" in script
            # Must NOT use bare "due date <" without "effective" prefix
            import re
            assert not re.search(r'(?<!effective )due date <', script)
