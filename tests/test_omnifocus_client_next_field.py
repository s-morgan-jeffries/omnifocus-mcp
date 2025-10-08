"""Tests for next field and next_only filter in get_tasks."""
import json
from unittest import mock
import pytest
from omnifocus_mcp.omnifocus_client import OmniFocusClient


@pytest.fixture
def client():
    """Create an OmniFocusClient instance."""
    return OmniFocusClient()


class TestGetTasksNextField:
    """Tests for next field in get_tasks."""

    def test_get_tasks_includes_next_field(self, client):
        """Test that get_tasks includes the next field in task results."""
        tasks_json = json.dumps([
            {
                "id": "task-001",
                "name": "Next Task",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "blocked": False,
                "next": True,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": ""
            },
            {
                "id": "task-002",
                "name": "Not Next Task",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "blocked": False,
                "next": False,
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
            assert len(tasks) == 2
            assert tasks[0]['next'] is True
            assert tasks[1]['next'] is False

    def test_get_tasks_next_only(self, client):
        """Test filtering for only next tasks."""
        next_tasks_json = json.dumps([
            {
                "id": "task-001",
                "name": "Next Task",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "blocked": False,
                "next": True,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": ""
            }
        ])
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = next_tasks_json
            tasks = client.get_tasks(next_only=True)
            assert len(tasks) == 1
            assert tasks[0]['next'] is True
            # Verify the filter is in the script
            call_args = mock_run.call_args[0][0]
            assert "next of t" in call_args
            # Should skip non-next tasks
            assert "skip" in call_args.lower() or "error" in call_args.lower()
