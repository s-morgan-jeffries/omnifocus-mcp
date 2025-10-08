"""Tests for get_subtasks method."""
import json
from unittest import mock
import pytest
from omnifocus_mcp.omnifocus_client import OmniFocusClient


@pytest.fixture
def client():
    """Create an OmniFocusClient instance."""
    return OmniFocusClient()


class TestGetSubtasks:
    """Tests for get_subtasks method."""

    def test_get_subtasks_success(self, client):
        """Test retrieving subtasks for a parent task."""
        subtasks_json = json.dumps([
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
                "note": "Second subtask",
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
        ])

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = subtasks_json
            subtasks = client.get_subtasks("parent-task-001")

            assert len(subtasks) == 2
            assert subtasks[0]['id'] == "subtask-001"
            assert subtasks[0]['name'] == "Subtask 1"
            assert subtasks[1]['id'] == "subtask-002"
            assert subtasks[1]['completed'] is True

            # Verify the AppleScript was called with parent task ID
            call_args = mock_run.call_args[0][0]
            assert "parent-task-001" in call_args
            assert "tasks" in call_args.lower()

    def test_get_subtasks_empty(self, client):
        """Test retrieving subtasks when parent has no children."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            subtasks = client.get_subtasks("task-no-children")

            assert len(subtasks) == 0
            assert isinstance(subtasks, list)

    def test_get_subtasks_not_found(self, client):
        """Test get_subtasks with non-existent parent task ID."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "[]"
            subtasks = client.get_subtasks("nonexistent-task")

            assert len(subtasks) == 0

    def test_get_subtasks_empty_id(self, client):
        """Test get_subtasks with empty task ID."""
        with pytest.raises(ValueError, match="task_id cannot be empty"):
            client.get_subtasks("")
