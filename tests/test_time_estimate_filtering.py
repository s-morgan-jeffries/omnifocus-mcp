"""Tests for time estimate filtering in get_tasks."""
import json
from unittest import mock
import pytest
from omnifocus_mcp.omnifocus_client import OmniFocusClient


@pytest.fixture
def client():
    """Create an OmniFocusClient instance."""
    return OmniFocusClient()


class TestTimeEstimateFiltering:
    """Tests for filtering by time estimates."""

    def test_get_tasks_max_estimated_minutes(self, client):
        """Test filtering for tasks under a time limit."""
        tasks_json = json.dumps([
            {
                "id": "task-001",
                "name": "Quick 15min task",
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
                "tags": "",
                "estimatedMinutes": 15
            }
        ])

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = tasks_json
            tasks = client.get_tasks(max_estimated_minutes=30)

            assert len(tasks) == 1
            assert tasks[0]['estimatedMinutes'] == 15
            # Verify filter in script
            call_args = mock_run.call_args[0][0]
            assert "estimated minutes" in call_args.lower()

    def test_get_tasks_has_estimate_true(self, client):
        """Test filtering for tasks that have an estimate."""
        tasks_json = json.dumps([
            {
                "id": "task-002",
                "name": "Task with estimate",
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
                "tags": "",
                "estimatedMinutes": 60
            }
        ])

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = tasks_json
            tasks = client.get_tasks(has_estimate=True)

            assert len(tasks) == 1
            assert tasks[0]['estimatedMinutes'] == 60

    def test_get_tasks_has_estimate_false(self, client):
        """Test filtering for tasks without an estimate."""
        tasks_json = json.dumps([
            {
                "id": "task-003",
                "name": "No estimate",
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
                "tags": "",
                "estimatedMinutes": None
            }
        ])

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = tasks_json
            tasks = client.get_tasks(has_estimate=False)

            assert len(tasks) == 1
            assert tasks[0]['estimatedMinutes'] is None

    def test_get_tasks_combined_estimate_filters(self, client):
        """Test combining max_estimated_minutes with other filters."""
        tasks_json = json.dumps([
            {
                "id": "task-004",
                "name": "Quick flagged task",
                "note": "",
                "completed": False,
                "flagged": True,
                "dropped": False,
                "blocked": False,
                "next": True,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": "",
                "estimatedMinutes": 10
            }
        ])

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = tasks_json
            tasks = client.get_tasks(max_estimated_minutes=15, flagged_only=True)

            assert len(tasks) == 1
            assert tasks[0]['flagged'] is True
            assert tasks[0]['estimatedMinutes'] == 10
