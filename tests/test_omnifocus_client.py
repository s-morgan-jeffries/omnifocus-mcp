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
        return OmniFocusClient(enable_safety_checks=False)

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

    def test_get_note_project_success(self, client):
        """Test successfully getting a note from a project."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "This is a long project note with multiple lines\nand lots of content"
            result = client.get_note("proj-001", "project")
            assert result == "This is a long project note with multiple lines\nand lots of content"
            # Verify AppleScript was called for project
            call_args = mock_run.call_args[0][0]
            assert "flattened project" in call_args
            assert "proj-001" in call_args

    def test_get_note_task_success(self, client):
        """Test successfully getting a note from a task."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "Task note with details"
            result = client.get_note("task-001", "task")
            assert result == "Task note with details"
            # Verify AppleScript was called for task
            call_args = mock_run.call_args[0][0]
            assert "flattened task" in call_args
            assert "task-001" in call_args

    def test_get_note_empty_note(self, client):
        """Test getting a note when item has no note."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = ""
            result = client.get_note("proj-001", "project")
            assert result == ""

    def test_get_note_default_item_type(self, client):
        """Test that item_type defaults to 'project'."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "Default project note"
            result = client.get_note("proj-001")  # No item_type specified
            assert result == "Default project note"
            # Verify it used project script
            call_args = mock_run.call_args[0][0]
            assert "flattened project" in call_args

    def test_get_note_invalid_item_type(self, client):
        """Test that invalid item_type raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            client.get_note("proj-001", "folder")
        assert "must be 'project' or 'task'" in str(exc_info.value)

    def test_get_note_item_not_found(self, client):
        """Test error handling when item is not found."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="Project not found")
            with pytest.raises(Exception) as exc_info:
                client.get_note("invalid-id", "project")
            assert "Error getting note" in str(exc_info.value)

    def test_search_projects_by_name(self, client, sample_projects_json):
        """Test searching projects by name."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            results = client.get_projects(query="quotes")
            assert len(results) == 1
            assert results[0]['name'] == 'Project with "quotes"'

    def test_search_projects_by_note(self, client, sample_projects_json):
        """Test searching projects by note content."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            results = client.get_projects(query="newlines")
            assert len(results) == 1
            assert "newlines" in results[0]['note']

    def test_search_projects_by_folder(self, client, sample_projects_json):
        """Test searching projects by folder path."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            results = client.get_projects(query="Work")
            assert len(results) == 1
            assert "Work" in results[0]['folderPath']

    def test_search_projects_case_insensitive(self, client, sample_projects_json):
        """Test that search is case-insensitive."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            results = client.get_projects(query="TEST")
            assert len(results) == 1
            assert results[0]['name'] == "Test Project"

    def test_search_projects_no_results(self, client, sample_projects_json):
        """Test searching with no matching results."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            results = client.get_projects(query="nonexistent")
            assert results == []

    def test_search_projects_multiple_matches(self, client, sample_projects_json):
        """Test searching that matches multiple projects."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_projects_json
            results = client.get_projects(query="Project")
            assert len(results) == 2  # Both projects have "Project" in name


class TestGetProject:
    """Tests for get_project functionality."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_get_project_success(self, client):
        """Test getting a single project by ID."""
        project_json = json.dumps({
            "id": "proj-001",
            "name": "Test Project",
            "note": "Project note",
            "status": "active",
            "folderPath": "Work > Tests"
        })

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = project_json
            project = client.get_project("proj-001")

            # Verify the project details
            assert project['id'] == "proj-001"
            assert project['name'] == "Test Project"
            assert project['status'] == "active"
            assert project['folderPath'] == "Work > Tests"

            # Verify the AppleScript was called with the project ID
            call_args = mock_run.call_args[0][0]
            assert 'proj-001' in call_args

    def test_get_project_not_found(self, client):
        """Test handling of project not found."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = ""
            with pytest.raises(Exception) as exc_info:
                client.get_project("nonexistent-project")
            assert "not found" in str(exc_info.value).lower()

    def test_get_project_empty_id(self, client):
        """Test handling of empty project ID."""
        with pytest.raises(ValueError) as exc_info:
            client.get_project("")
        assert "project_id is required" in str(exc_info.value)


class TestCreateProject:
    """Tests for create_project functionality."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_create_project_basic(self, client):
        """Test creating a basic project."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            project_id = client.create_project("New Project")
            assert project_id == "proj-new-001"
            # Verify AppleScript contains project name
            call_args = mock_run.call_args[0][0]
            assert "New Project" in call_args
            assert "make new project" in call_args

    def test_create_project_with_note(self, client):
        """Test creating project with note."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
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
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            project_id = client.create_project("Sequential Project", sequential=True)
            assert project_id == "proj-new-001"
            call_args = mock_run.call_args[0][0]
            assert "sequential:true" in call_args

    def test_create_project_parallel(self, client):
        """Test creating parallel project (default)."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            project_id = client.create_project("Parallel Project", sequential=False)
            assert project_id == "proj-new-001"
            call_args = mock_run.call_args[0][0]
            assert "sequential:false" in call_args

    def test_create_project_in_folder(self, client):
        """Test creating project in a folder."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            project_id = client.create_project("New Project", folder_path="Work")
            assert project_id == "proj-new-001"
            call_args = mock_run.call_args[0][0]
            assert 'whose name is "Work"' in call_args

    def test_create_project_in_nested_folder(self, client):
        """Test creating project in nested folder."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            project_id = client.create_project("New Project", folder_path="Work > Clients")
            assert project_id == "proj-new-001"
            call_args = mock_run.call_args[0][0]
            assert '"Work"' in call_args
            assert '"Clients"' in call_args

    def test_create_project_with_special_characters(self, client):
        """Test creating project with special characters in name."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            project_id = client.create_project('Project with "quotes" and \\backslashes')
            assert project_id == "proj-new-001"
            # Verify characters are escaped
            call_args = mock_run.call_args[0][0]
            assert '\\"quotes\\"' in call_args or 'quotes' in call_args
            assert '\\\\backslashes' in call_args or 'backslashes' in call_args

    def test_create_project_with_all_properties(self, client):
        """Test creating project with all properties."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
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
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = ""
            with pytest.raises(Exception) as exc_info:
                client.create_project("New Project")
            assert "No project ID returned" in str(exc_info.value)

    def test_create_project_subprocess_error(self, client):
        """Test handling of subprocess errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="permission denied")
            with pytest.raises(Exception) as exc_info:
                client.create_project("New Project")
            assert "Error creating project" in str(exc_info.value)

    def test_create_project_empty_name(self, client):
        """Test creating project with empty name."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "proj-new-001"
            # OmniFocus allows empty names, so this should work
            project_id = client.create_project("")
            assert project_id == "proj-new-001"


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

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
        return OmniFocusClient(enable_safety_checks=False)

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
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
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

    def test_get_tasks_includes_dropped_field(self, client, sample_tasks_json):
        """Test that get_tasks includes the dropped field in the AppleScript and response."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
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
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
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
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
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
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
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
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
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
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
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
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
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
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = tasks_json
            tasks = client.get_tasks(tag_filter=["urgent", "work"])
            assert len(tasks) == 1


class TestGetTask:
    """Tests for get_task functionality."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_get_task_success(self, client):
        """Test getting a single task by ID."""
        task_json = json.dumps({
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
        })

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = task_json
            task = client.get_task("task-001")

            # Verify the task details
            assert task['id'] == "task-001"
            assert task['name'] == "Test Task"
            assert task['flagged'] is True
            assert task['dropped'] is False
            assert task['projectId'] == "proj-001"

            # Verify the AppleScript was called with the task ID
            call_args = mock_run.call_args[0][0]
            assert 'task-001' in call_args

    def test_get_task_not_found(self, client):
        """Test handling of task not found."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = ""
            with pytest.raises(Exception) as exc_info:
                client.get_task("nonexistent-task")
            assert "not found" in str(exc_info.value).lower()

    def test_get_task_empty_id(self, client):
        """Test handling of empty task ID."""
        with pytest.raises(ValueError) as exc_info:
            client.get_task("")
        assert "task_id is required" in str(exc_info.value)


class TestCompleteTask:
    """Tests for complete_task functionality."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_complete_task_success(self, client):
        """Test successfully completing a task."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.complete_task("task-001")
            assert result is True
            # Verify the AppleScript contains task ID and mark complete command
            call_args = mock_run.call_args[0][0]
            assert 'whose id is "task-001"' in call_args
            assert "mark complete" in call_args

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
        return OmniFocusClient(enable_safety_checks=False)

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
        return OmniFocusClient(enable_safety_checks=False)

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
                "dropped": False,
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
                "dropped": False,
                "dueDate": "2025-10-15T17:00:00",
                "deferDate": "",
                "tags": "urgent"
            }
        ])

    def test_get_inbox_tasks_success(self, client, sample_inbox_tasks_json):
        """Test getting inbox tasks."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_inbox_tasks_json
            tasks = client.get_tasks(inbox_only=True)
            assert len(tasks) == 2
            assert tasks[0]['id'] == "inbox-001"
            assert tasks[0]['name'] == "Quick Capture"
            assert tasks[0]['dropped'] is False
            assert tasks[1]['flagged'] is True

    def test_get_inbox_tasks_includes_dropped_field(self, client, sample_inbox_tasks_json):
        """Test that get_tasks(inbox_only=True) includes the dropped field in the AppleScript and response."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_inbox_tasks_json
            tasks = client.get_tasks(inbox_only=True)
            # Verify dropped field is in returned data
            assert 'dropped' in tasks[0]
            assert tasks[0]['dropped'] is False
            # Verify the AppleScript retrieves the dropped field
            call_args = mock_run.call_args[0][0]
            assert "set taskDropped to dropped of t" in call_args
            # Verify the AppleScript includes dropped in JSON output
            assert '\\"dropped\\"' in call_args

    def test_get_inbox_tasks_empty(self, client):
        """Test handling of empty inbox."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            tasks = client.get_tasks(inbox_only=True)
            assert tasks == []

    def test_get_inbox_tasks_subprocess_error(self, client):
        """Test handling of subprocess errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.get_tasks(inbox_only=True)
            assert "Error querying" in str(exc_info.value)

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
        return OmniFocusClient(enable_safety_checks=False)

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


class TestDeleteTask:
    """Tests for delete_task method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_delete_task_success(self, client):
        """Test successful task deletion."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.delete_task("task-001")
            assert result is True
            mock_run.assert_called_once()

    def test_delete_task_not_found(self, client):
        """Test deleting non-existent task."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false"
            with pytest.raises(Exception) as exc_info:
                client.delete_task("nonexistent")
            assert "Task not found" in str(exc_info.value)

    def test_delete_task_error(self, client):
        """Test handling of deletion errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.delete_task("task-001")
            assert "Error deleting task" in str(exc_info.value)


class TestDeleteProject:
    """Tests for delete_project method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_delete_project_success(self, client):
        """Test successful project deletion."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.delete_project("proj-001")
            assert result is True
            mock_run.assert_called_once()

    def test_delete_project_not_found(self, client):
        """Test deleting non-existent project."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false"
            with pytest.raises(Exception) as exc_info:
                client.delete_project("nonexistent")
            assert "Project not found" in str(exc_info.value)

    def test_delete_project_error(self, client):
        """Test handling of deletion errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.delete_project("proj-001")
            assert "Error deleting project" in str(exc_info.value)


class TestDropProject:
    """Tests for drop_project method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_drop_project_success(self, client):
        """Test successfully dropping a project."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.drop_project("proj-001")
            assert result is True
            mock_run.assert_called_once()

    def test_drop_project_not_found(self, client):
        """Test dropping non-existent project."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false"
            with pytest.raises(Exception) as exc_info:
                client.drop_project("nonexistent")
            assert "Project not found" in str(exc_info.value)

    def test_drop_project_error(self, client):
        """Test handling of drop errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.drop_project("proj-001")
            assert "Error dropping project" in str(exc_info.value)


class TestMoveTask:
    """Tests for move_task method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_move_task_to_project_success(self, client):
        """Test successfully moving task to a project."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.move_task("task-001", "proj-002")
            assert result is True
            mock_run.assert_called_once()

    def test_move_task_to_inbox_success(self, client):
        """Test successfully moving task to inbox."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.move_task("task-001", None)  # None means inbox
            assert result is True
            mock_run.assert_called_once()

    def test_move_task_not_found(self, client):
        """Test moving non-existent task."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false: Task not found"
            with pytest.raises(Exception) as exc_info:
                client.move_task("nonexistent", "proj-001")
            assert "not found" in str(exc_info.value).lower()

    def test_move_task_project_not_found(self, client):
        """Test moving task to non-existent project."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false: Project not found"
            with pytest.raises(Exception) as exc_info:
                client.move_task("task-001", "nonexistent")
            assert "not found" in str(exc_info.value).lower()

    def test_move_task_error(self, client):
        """Test handling of move errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.move_task("task-001", "proj-001")
            assert "Error moving task" in str(exc_info.value)


class TestGetFolders:
    """Tests for get_folders method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

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
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_folders_json
            folders = client.get_folders()
            assert len(folders) == 3
            assert folders[0]["name"] == "Work"
            assert folders[2]["path"] == "Work > Clients"

    def test_get_folders_empty(self, client):
        """Test retrieving folders when none exist."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            folders = client.get_folders()
            assert folders == []

    def test_get_folders_error(self, client):
        """Test handling of AppleScript errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.get_folders()
            assert "Error retrieving folders" in str(exc_info.value)


class TestDropTask:
    """Tests for drop_task method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_drop_task_success(self, client):
        """Test successfully dropping a task."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.drop_task("task-001")
            assert result is True
            mock_run.assert_called_once()

    def test_drop_task_not_found(self, client):
        """Test dropping non-existent task."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false"
            with pytest.raises(Exception) as exc_info:
                client.drop_task("nonexistent")
            assert "Task not found" in str(exc_info.value)

    def test_drop_task_error(self, client):
        """Test handling of drop errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.drop_task("task-001")
            assert "Error dropping task" in str(exc_info.value)


class TestCreateFolder:
    """Tests for create_folder method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_create_folder_root_level(self, client):
        """Test creating a folder at root level."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "folder-new-001"
            folder_id = client.create_folder("New Folder")
            assert folder_id == "folder-new-001"
            mock_run.assert_called_once()

    def test_create_folder_with_parent_path(self, client):
        """Test creating a folder with parent path."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "folder-new-002"
            folder_id = client.create_folder("Clients", parent_path="Work")
            assert folder_id == "folder-new-002"
            mock_run.assert_called_once()

    def test_create_folder_nested_parent_path(self, client):
        """Test creating a folder with nested parent path."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "folder-new-003"
            folder_id = client.create_folder("Active", parent_path="Work > Clients")
            assert folder_id == "folder-new-003"
            mock_run.assert_called_once()

    def test_create_folder_with_special_characters(self, client):
        """Test creating a folder with special characters in name."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "folder-new-004"
            folder_id = client.create_folder("Work & Life")
            assert folder_id == "folder-new-004"

    def test_create_folder_parent_not_found(self, client):
        """Test creating folder with non-existent parent."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false: Parent folder not found"
            with pytest.raises(Exception) as exc_info:
                client.create_folder("New Folder", parent_path="Nonexistent")
            assert "not found" in str(exc_info.value).lower()

    def test_create_folder_error(self, client):
        """Test handling of folder creation errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.create_folder("New Folder")
            assert "Error creating folder" in str(exc_info.value)


class TestSetParentTask:
    """Tests for set_parent_task method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_set_parent_task_success(self, client):
        """Test successfully making a task a subtask."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.set_parent_task("task-002", "task-001")
            assert result is True
            mock_run.assert_called_once()

    def test_set_parent_task_to_none(self, client):
        """Test making a subtask into a root-level task."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.set_parent_task("task-002", None)
            assert result is True
            mock_run.assert_called_once()

    def test_set_parent_task_task_not_found(self, client):
        """Test with non-existent task."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false: Task not found"
            with pytest.raises(Exception) as exc_info:
                client.set_parent_task("nonexistent", "task-001")
            assert "not found" in str(exc_info.value).lower()

    def test_set_parent_task_parent_not_found(self, client):
        """Test with non-existent parent task."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false: Parent task not found"
            with pytest.raises(Exception) as exc_info:
                client.set_parent_task("task-002", "nonexistent")
            assert "not found" in str(exc_info.value).lower()

    def test_set_parent_task_circular_reference(self, client):
        """Test preventing circular references (task being its own parent)."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false: Cannot set task as its own parent"
            with pytest.raises(Exception) as exc_info:
                client.set_parent_task("task-001", "task-001")
            assert "cannot" in str(exc_info.value).lower()

    def test_set_parent_task_error(self, client):
        """Test handling of set parent errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.set_parent_task("task-002", "task-001")
            assert "Error setting parent task" in str(exc_info.value)


class TestSetReviewInterval:
    """Tests for set_review_interval method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_set_review_interval_weekly(self, client):
        """Test setting weekly review interval."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.set_review_interval("proj-001", interval_weeks=1)
            assert result is True
            mock_run.assert_called_once()

    def test_set_review_interval_monthly(self, client):
        """Test setting monthly review interval."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.set_review_interval("proj-001", interval_weeks=4)
            assert result is True

    def test_set_review_interval_project_not_found(self, client):
        """Test with non-existent project."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false"
            with pytest.raises(Exception) as exc_info:
                client.set_review_interval("nonexistent", interval_weeks=1)
            assert "Project not found" in str(exc_info.value)

    def test_set_review_interval_error(self, client):
        """Test handling of errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.set_review_interval("proj-001", interval_weeks=1)
            assert "Error setting review interval" in str(exc_info.value)


class TestMarkProjectReviewed:
    """Tests for mark_project_reviewed method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_mark_project_reviewed_success(self, client):
        """Test successfully marking project as reviewed."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.mark_project_reviewed("proj-001")
            assert result is True
            mock_run.assert_called_once()

    def test_mark_project_reviewed_not_found(self, client):
        """Test with non-existent project."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false"
            with pytest.raises(Exception) as exc_info:
                client.mark_project_reviewed("nonexistent")
            assert "Project not found" in str(exc_info.value)

    def test_mark_project_reviewed_error(self, client):
        """Test handling of errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.mark_project_reviewed("proj-001")
            assert "Error marking project as reviewed" in str(exc_info.value)


class TestGetProjectsDueForReview:
    """Tests for get_projects_due_for_review method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    @pytest.fixture
    def sample_review_projects_json(self):
        """Sample projects due for review."""
        return json.dumps([
            {
                "id": "proj-001",
                "name": "Project Needing Review",
                "nextReviewDate": "2025-10-01T00:00:00",
                "lastReviewDate": "2025-09-24T00:00:00"
            },
            {
                "id": "proj-002",
                "name": "Another Project",
                "nextReviewDate": "2025-10-05T00:00:00",
                "lastReviewDate": "2025-09-28T00:00:00"
            }
        ])

    def test_get_projects_due_for_review_success(self, client, sample_review_projects_json):
        """Test getting projects due for review."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = sample_review_projects_json
            projects = client.get_projects_due_for_review()
            assert len(projects) == 2
            assert projects[0]["id"] == "proj-001"
            assert "nextReviewDate" in projects[0]

    def test_get_projects_due_for_review_empty(self, client):
        """Test when no projects are due for review."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            projects = client.get_projects_due_for_review()
            assert projects == []

    def test_get_projects_due_for_review_error(self, client):
        """Test handling of errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.get_projects_due_for_review()
            assert "Error retrieving projects due for review" in str(exc_info.value)


class TestSetEstimatedMinutes:
    """Tests for set_estimated_minutes method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_set_estimated_minutes_success(self, client):
        """Test successfully setting estimated time."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.set_estimated_minutes("task-001", 60)
            assert result is True
            mock_run.assert_called_once()

    def test_set_estimated_minutes_zero(self, client):
        """Test setting estimated time to zero (clear estimate)."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.set_estimated_minutes("task-001", 0)
            assert result is True

    def test_set_estimated_minutes_task_not_found(self, client):
        """Test with non-existent task."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false"
            with pytest.raises(Exception) as exc_info:
                client.set_estimated_minutes("nonexistent", 30)
            assert "Task not found" in str(exc_info.value)

    def test_set_estimated_minutes_error(self, client):
        """Test handling of errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.set_estimated_minutes("task-001", 45)
            assert "Error setting estimated minutes" in str(exc_info.value)


class TestGetPerspectives:
    """Tests for get_perspectives method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_get_perspectives_success(self, client):
        """Test getting perspective names."""
        perspectives_str = "Inbox, Projects, Tags, Forecast, Daily Worklist"
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = perspectives_str
            perspectives = client.get_perspectives()
            assert len(perspectives) == 5
            assert "Inbox" in perspectives
            assert "Daily Worklist" in perspectives

    def test_get_perspectives_empty(self, client):
        """Test when no custom perspectives exist."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "Inbox, Projects"
            perspectives = client.get_perspectives()
            assert len(perspectives) == 2

    def test_get_perspectives_error(self, client):
        """Test handling of errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.get_perspectives()
            assert "Error retrieving perspectives" in str(exc_info.value)


class TestSwitchPerspective:
    """Tests for switch_perspective method."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_switch_perspective_success(self, client):
        """Test successfully switching perspective."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "Daily Worklist"
            result = client.switch_perspective("Daily Worklist")
            assert result == "Daily Worklist"
            mock_run.assert_called_once()

    def test_switch_perspective_builtin(self, client):
        """Test switching to built-in perspective."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "Inbox"
            result = client.switch_perspective("Inbox")
            assert result == "Inbox"

    def test_switch_perspective_error(self, client):
        """Test handling of errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, 'osascript', stderr="error")
            with pytest.raises(Exception) as exc_info:
                client.switch_perspective("Invalid")
            assert "Error switching perspective" in str(exc_info.value)
