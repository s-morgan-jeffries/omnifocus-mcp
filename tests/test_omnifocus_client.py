"""Unit tests for OmniFocusClient."""
import json
import subprocess
from unittest import mock
import pytest

from omnifocus_mcp.omnifocus_client import OmniFocusClient, run_applescript


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


class TestOmniFocusClient:
    """Tests for OmniFocusClient class."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient()

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
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            projects = client.get_projects()

            assert len(projects) == 2
            assert projects[0]['id'] == "proj-001"
            assert projects[0]['name'] == "Test Project"
            assert projects[0]['folderPath'] == "Work > Tests"
            assert projects[1]['name'] == 'Project with "quotes"'

    def test_get_projects_empty(self, client):
        """Test handling of empty projects list."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            projects = client.get_projects()
            assert projects == []

    def test_get_projects_no_output(self, client):
        """Test handling of no output from AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = ""
            with pytest.raises(Exception) as exc_info:
                client.get_projects()
            assert "No output from OmniFocus AppleScript" in str(exc_info.value)

    def test_get_projects_invalid_json(self, client):
        """Test handling of invalid JSON from AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "not valid json"
            with pytest.raises(Exception) as exc_info:
                client.get_projects()
            assert "Error parsing OmniFocus output" in str(exc_info.value)

    def test_get_projects_subprocess_error(self, client):
        """Test handling of subprocess errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="permission denied")
            with pytest.raises(Exception) as exc_info:
                client.get_projects()
            assert "Error querying OmniFocus" in str(exc_info.value)

    def test_add_task_success(self, client):
        """Test successful task addition."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_task("proj-001", "New Task", "Task note")
            assert result is True

    def test_add_task_with_special_characters(self, client):
        """Test adding task with special characters in name and note."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_task(
                "proj-001",
                'Task with "quotes" and \\backslash',
                'Note with\nnewlines'
            )
            assert result is True
            # Verify escaping was applied
            call_args = mock_run.call_args[0][0]
            assert '\\"' in call_args  # Quotes should be escaped
            assert '\\\\' in call_args  # Backslashes should be escaped

    def test_add_task_failure(self, client):
        """Test handling of task addition failure."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false: Project not found"
            with pytest.raises(Exception) as exc_info:
                client.add_task("invalid-id", "Task", "Note")
            assert "Error adding task" in str(exc_info.value)

    def test_add_task_subprocess_error(self, client):
        """Test handling of subprocess errors during task addition."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.add_task("proj-001", "Task")
            assert "Error adding task" in str(exc_info.value)

    def test_add_task_without_note(self, client):
        """Test adding task without a note."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_task("proj-001", "Task without note")
            assert result is True

    def test_add_task_with_due_date(self, client):
        """Test adding task with due date."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_task(
                "proj-001",
                "Task with due date",
                due_date="2025-10-15"
            )
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "October 15, 2025" in call_args
            assert "due date" in call_args

    def test_add_task_with_due_date_and_time(self, client):
        """Test adding task with due date and time."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_task(
                "proj-001",
                "Task with due datetime",
                due_date="2025-10-15T17:00:00"
            )
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "October 15, 2025 05:00:00 PM" in call_args

    def test_add_task_with_defer_date(self, client):
        """Test adding task with defer date."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_task(
                "proj-001",
                "Task with defer date",
                defer_date="2025-10-08"
            )
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "October 08, 2025" in call_args
            assert "defer date" in call_args

    def test_add_task_with_both_dates(self, client):
        """Test adding task with both due and defer dates."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_task(
                "proj-001",
                "Task with both dates",
                due_date="2025-10-15T17:00:00",
                defer_date="2025-10-08T09:00:00"
            )
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "due date" in call_args
            assert "defer date" in call_args
            assert "October 15, 2025 05:00:00 PM" in call_args
            assert "October 08, 2025 09:00:00 AM" in call_args

    def test_add_task_with_invalid_date_format(self, client):
        """Test adding task with invalid date format."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            with pytest.raises(ValueError) as exc_info:
                client.add_task(
                    "proj-001",
                    "Task with invalid date",
                    due_date="not-a-date"
                )
            assert "Invalid date format" in str(exc_info.value)

    def test_add_task_flagged(self, client):
        """Test adding flagged task."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_task(
                "proj-001",
                "Flagged task",
                flagged=True
            )
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "flagged:true" in call_args

    def test_add_task_not_flagged(self, client):
        """Test adding non-flagged task (explicit False)."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_task(
                "proj-001",
                "Not flagged task",
                flagged=False
            )
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "flagged:true" not in call_args

    def test_add_task_with_single_tag(self, client):
        """Test adding task with a single tag."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_task(
                "proj-001",
                "Task with tag",
                tags=["urgent"]
            )
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert 'whose name is "urgent"' in call_args
            assert "add tagObj to tags of newTask" in call_args

    def test_add_task_with_multiple_tags(self, client):
        """Test adding task with multiple tags."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_task(
                "proj-001",
                "Task with multiple tags",
                tags=["urgent", "work", "important"]
            )
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert 'whose name is "urgent"' in call_args
            assert 'whose name is "work"' in call_args
            assert 'whose name is "important"' in call_args

    def test_add_task_with_tags_containing_special_chars(self, client):
        """Test adding task with tags containing special characters."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_task(
                "proj-001",
                "Task with special tag",
                tags=['tag with "quotes"', 'tag\\with\\backslash']
            )
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert '\\"' in call_args  # Quotes escaped
            assert '\\\\' in call_args  # Backslashes escaped

    def test_add_task_with_all_properties(self, client):
        """Test adding task with all optional properties."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_task(
                "proj-001",
                "Complete task",
                note="Task description with details",
                due_date="2025-10-15T17:00:00",
                defer_date="2025-10-08T09:00:00",
                flagged=True,
                tags=["urgent", "work"]
            )
            assert result is True
            call_args = mock_run.call_args[0][0]
            # Verify all properties are present
            assert 'name:"Complete task"' in call_args
            assert 'note:"Task description with details"' in call_args
            assert "flagged:true" in call_args
            assert "due date" in call_args
            assert "defer date" in call_args
            assert "October 15, 2025 05:00:00 PM" in call_args
            assert "October 08, 2025 09:00:00 AM" in call_args
            assert 'whose name is "urgent"' in call_args
            assert 'whose name is "work"' in call_args

    def test_add_note_success(self, client):
        """Test successful note addition."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_note("proj-001", "Additional note")
            assert result is True

    def test_add_note_with_special_characters(self, client):
        """Test adding note with special characters."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_note(
                "proj-001",
                'Note with "quotes", \\backslash, and\nnewlines'
            )
            assert result is True
            # Verify escaping was applied
            call_args = mock_run.call_args[0][0]
            assert '\\"' in call_args

    def test_add_note_failure(self, client):
        """Test handling of note addition failure."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false: Project not found"
            with pytest.raises(Exception) as exc_info:
                client.add_note("invalid-id", "Note")
            assert "Error adding note" in str(exc_info.value)

    def test_add_note_subprocess_error(self, client):
        """Test handling of subprocess errors during note addition."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.add_note("proj-001", "Note")
            assert "Error adding note" in str(exc_info.value)

    def test_search_projects_by_name(self, client, sample_projects_json):
        """Test searching projects by name."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            results = client.search_projects("quotes")
            assert len(results) == 1
            assert results[0]['name'] == 'Project with "quotes"'

    def test_search_projects_by_note(self, client, sample_projects_json):
        """Test searching projects by note content."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            results = client.search_projects("newlines")
            assert len(results) == 1
            assert "newlines" in results[0]['note']

    def test_search_projects_by_folder(self, client, sample_projects_json):
        """Test searching projects by folder path."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            results = client.search_projects("Work")
            assert len(results) == 1
            assert "Work" in results[0]['folderPath']

    def test_search_projects_case_insensitive(self, client, sample_projects_json):
        """Test that search is case-insensitive."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            results = client.search_projects("TEST")
            assert len(results) == 1
            assert results[0]['name'] == "Test Project"

    def test_search_projects_no_results(self, client, sample_projects_json):
        """Test searching with no matching results."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            results = client.search_projects("nonexistent")
            assert results == []

    def test_search_projects_multiple_matches(self, client, sample_projects_json):
        """Test searching that matches multiple projects."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            results = client.search_projects("Project")
            assert len(results) == 2  # Both projects have "Project" in name


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient()

    def test_very_long_note(self, client):
        """Test handling of very long notes."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            long_note = "x" * 10000
            result = client.add_note("proj-001", long_note)
            assert result is True

    def test_unicode_characters(self, client):
        """Test handling of Unicode characters."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_task(
                "proj-001",
                "Task with emoji 🎉 and unicode 你好",
                "Note with symbols: ★ ☆ ✓"
            )
            assert result is True

    def test_empty_strings(self, client):
        """Test handling of empty strings."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_task("proj-001", "", "")
            assert result is True

    def test_projects_with_all_fields_empty(self, client):
        """Test handling of projects with minimal data."""
        minimal_json = json.dumps([{
            "id": "proj-001",
            "name": "",
            "note": "",
            "status": "active",
            "folderPath": ""
        }])
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = minimal_json
            projects = client.get_projects()
            assert len(projects) == 1
            assert projects[0]['id'] == "proj-001"


class TestGetTasks:
    """Tests for get_tasks functionality."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient()

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
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            tasks = client.get_tasks()
            assert len(tasks) == 2
            assert tasks[0]['id'] == "task-001"
            assert tasks[0]['name'] == "Test Task"
            assert tasks[0]['flagged'] is True
            assert tasks[0]['tags'] == "urgent, work"

    def test_get_tasks_by_project(self, client, sample_tasks_json):
        """Test getting tasks filtered by project."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
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
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = completed_json
            tasks = client.get_tasks(include_completed=True)
            assert len(tasks) == 1
            assert tasks[0]['completed'] is True
            # Verify completion filter is not in script
            call_args = mock_run.call_args[0][0]
            assert "skip completed task" not in call_args

    def test_get_tasks_flagged_only(self, client, sample_tasks_json):
        """Test getting only flagged tasks."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_tasks_json
            client.get_tasks(flagged_only=True)
            # Verify flagged filter is in script
            call_args = mock_run.call_args[0][0]
            assert "skip non-flagged task" in call_args

    def test_get_tasks_empty(self, client):
        """Test handling of empty tasks list."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            tasks = client.get_tasks()
            assert tasks == []

    def test_get_tasks_no_output(self, client):
        """Test handling of no output from AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = ""
            with pytest.raises(Exception) as exc_info:
                client.get_tasks()
            assert "No output from OmniFocus AppleScript" in str(exc_info.value)

    def test_get_tasks_invalid_json(self, client):
        """Test handling of invalid JSON from AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "not valid json"
            with pytest.raises(Exception) as exc_info:
                client.get_tasks()
            assert "Error parsing OmniFocus task output" in str(exc_info.value)

    def test_get_tasks_subprocess_error(self, client):
        """Test handling of subprocess errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="permission denied")
            with pytest.raises(Exception) as exc_info:
                client.get_tasks()
            assert "Error querying OmniFocus tasks" in str(exc_info.value)

    def test_get_tasks_with_all_filters(self, client, sample_tasks_json):
        """Test getting tasks with all filters combined."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
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


class TestCompleteTask:
    """Tests for complete_task functionality."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient()

    def test_complete_task_success(self, client):
        """Test successfully completing a task."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.complete_task("task-001")
            assert result is True
            # Verify the AppleScript contains task ID
            call_args = mock_run.call_args[0][0]
            assert 'whose id is "task-001"' in call_args
            assert "completed" in call_args

    def test_complete_task_failure(self, client):
        """Test handling of task completion failure."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false: Task not found"
            with pytest.raises(Exception) as exc_info:
                client.complete_task("invalid-id")
            assert "Error completing task" in str(exc_info.value)

    def test_complete_task_subprocess_error(self, client):
        """Test handling of subprocess errors during task completion."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.complete_task("task-001")
            assert "Error completing task" in str(exc_info.value)

    def test_complete_task_with_special_characters_in_id(self, client):
        """Test completing task with special characters in ID."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            # OmniFocus IDs can contain special characters
            result = client.complete_task("task-001-abc-xyz")
            assert result is True

    def test_complete_task_empty_id(self, client):
        """Test completing task with empty ID raises error."""
        with pytest.raises(ValueError) as exc_info:
            client.complete_task("")
        assert "task_id is required" in str(exc_info.value)


class TestUpdateTask:
    """Tests for update_task functionality."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient()

    def test_update_task_name(self, client):
        """Test updating task name."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task("task-001", name="Updated Task Name")
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert 'whose id is "task-001"' in call_args
            assert "Updated Task Name" in call_args

    def test_update_task_note(self, client):
        """Test updating task note."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task("task-001", note="Updated note")
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "Updated note" in call_args

    def test_update_task_due_date(self, client):
        """Test updating task due date."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task("task-001", due_date="2025-12-25")
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "December 25, 2025" in call_args

    def test_update_task_defer_date(self, client):
        """Test updating task defer date."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task("task-001", defer_date="2025-12-20")
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "December 20, 2025" in call_args

    def test_update_task_flagged(self, client):
        """Test updating task flagged status."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task("task-001", flagged=True)
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "flagged" in call_args

    def test_update_task_multiple_fields(self, client):
        """Test updating multiple task fields at once."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task(
                "task-001",
                name="New Name",
                note="New note",
                due_date="2025-12-25T17:00:00",
                flagged=True
            )
            assert result is True
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
        """Test handling of task update failure."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false: Task not found"
            with pytest.raises(Exception) as exc_info:
                client.update_task("invalid-id", name="New Name")
            assert "Error updating task" in str(exc_info.value)

    def test_update_task_subprocess_error(self, client):
        """Test handling of subprocess errors during task update."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.update_task("task-001", name="New Name")
            assert "Error updating task" in str(exc_info.value)

    def test_update_task_clear_date(self, client):
        """Test clearing a task date by setting to empty string."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_task("task-001", due_date="")
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "missing value" in call_args


class TestInboxOperations:
    """Tests for inbox operations."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient()

    @pytest.fixture
    def sample_inbox_tasks_json(self):
        """Sample JSON output for inbox tasks."""
        return json.dumps([
            {
                "id": "inbox-001",
                "name": "Quick Capture",
                "note": "Need to process this",
                "completed": False,
                "flagged": False,
                "dueDate": "",
                "deferDate": "",
                "tags": ""
            },
            {
                "id": "inbox-002",
                "name": "Another Inbox Item",
                "note": "",
                "completed": False,
                "flagged": True,
                "dueDate": "2025-10-15T17:00:00",
                "deferDate": "",
                "tags": "urgent"
            }
        ])

    def test_get_inbox_tasks_success(self, client, sample_inbox_tasks_json):
        """Test getting inbox tasks."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_inbox_tasks_json
            tasks = client.get_inbox_tasks()
            assert len(tasks) == 2
            assert tasks[0]['id'] == "inbox-001"
            assert tasks[0]['name'] == "Quick Capture"
            assert tasks[1]['flagged'] is True

    def test_get_inbox_tasks_empty(self, client):
        """Test handling of empty inbox."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            tasks = client.get_inbox_tasks()
            assert tasks == []

    def test_get_inbox_tasks_subprocess_error(self, client):
        """Test handling of subprocess errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.get_inbox_tasks()
            assert "Error querying inbox tasks" in str(exc_info.value)

    def test_create_inbox_task_basic(self, client):
        """Test creating basic inbox task."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.create_inbox_task("Quick task")
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "Quick task" in call_args
            assert "inbox" in call_args.lower()

    def test_create_inbox_task_with_note(self, client):
        """Test creating inbox task with note."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.create_inbox_task("Task name", note="Task details")
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "Task name" in call_args
            assert "Task details" in call_args

    def test_create_inbox_task_with_all_properties(self, client):
        """Test creating inbox task with all properties."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.create_inbox_task(
                "Complete task",
                note="Description",
                due_date="2025-10-15",
                flagged=True
            )
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert "Complete task" in call_args
            assert "Description" in call_args
            assert "October 15, 2025" in call_args
            assert "flagged" in call_args

    def test_create_inbox_task_empty_name(self, client):
        """Test creating inbox task with empty name raises error."""
        with pytest.raises(ValueError) as exc_info:
            client.create_inbox_task("")
        assert "task_name is required" in str(exc_info.value)

    def test_create_inbox_task_failure(self, client):
        """Test handling of inbox task creation failure."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false: Error creating task"
            with pytest.raises(Exception) as exc_info:
                client.create_inbox_task("Task")
            assert "Error creating inbox task" in str(exc_info.value)

    def test_create_inbox_task_subprocess_error(self, client):
        """Test handling of subprocess errors during inbox task creation."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.create_inbox_task("Task")
            assert "Error creating inbox task" in str(exc_info.value)


class TestTagOperations:
    """Tests for tag operations."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient()

    @pytest.fixture
    def sample_tags_json(self):
        """Sample JSON output for tags."""
        return json.dumps([
            {
                "id": "tag-001",
                "name": "urgent",
                "status": "active"
            },
            {
                "id": "tag-002",
                "name": "work",
                "status": "active"
            },
            {
                "id": "tag-003",
                "name": "personal",
                "status": "active"
            }
        ])

    def test_get_tags_success(self, client, sample_tags_json):
        """Test getting all tags."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_tags_json
            tags = client.get_tags()
            assert len(tags) == 3
            assert tags[0]['id'] == "tag-001"
            assert tags[0]['name'] == "urgent"
            assert tags[1]['name'] == "work"

    def test_get_tags_empty(self, client):
        """Test handling of empty tags list."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            tags = client.get_tags()
            assert tags == []

    def test_get_tags_subprocess_error(self, client):
        """Test handling of subprocess errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.get_tags()
            assert "Error querying tags" in str(exc_info.value)

    def test_add_tag_to_task_success(self, client):
        """Test adding tag to task."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.add_tag_to_task("task-001", "urgent")
            assert result is True
            call_args = mock_run.call_args[0][0]
            assert 'whose id is "task-001"' in call_args
            assert 'whose name is "urgent"' in call_args

    def test_add_tag_to_task_empty_task_id(self, client):
        """Test adding tag with empty task ID raises error."""
        with pytest.raises(ValueError) as exc_info:
            client.add_tag_to_task("", "urgent")
        assert "task_id is required" in str(exc_info.value)

    def test_add_tag_to_task_empty_tag_name(self, client):
        """Test adding tag with empty tag name raises error."""
        with pytest.raises(ValueError) as exc_info:
            client.add_tag_to_task("task-001", "")
        assert "tag_name is required" in str(exc_info.value)

    def test_add_tag_to_task_failure(self, client):
        """Test handling of tag addition failure."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false: Tag not found"
            with pytest.raises(Exception) as exc_info:
                client.add_tag_to_task("task-001", "nonexistent")
            assert "Error adding tag to task" in str(exc_info.value)

    def test_add_tag_to_task_subprocess_error(self, client):
        """Test handling of subprocess errors during tag addition."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.add_tag_to_task("task-001", "urgent")
            assert "Error adding tag to task" in str(exc_info.value)
