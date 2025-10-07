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
