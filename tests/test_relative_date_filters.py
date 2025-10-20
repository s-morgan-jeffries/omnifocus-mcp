"""Tests for relative date filters in get_tasks."""
import json
from unittest import mock
import pytest
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


@pytest.fixture
def client():
    """Create an OmniFocusConnector instance."""
    return OmniFocusConnector()


class TestRelativeDateFilters:
    """Tests for relative date filtering."""

    def test_get_tasks_due_today(self, client):
        """Test filtering for tasks due today."""
        tasks_json = json.dumps([
            {
                "id": "task-001",
                "name": "Task due today",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "blocked": False,
                "next": True,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "2025-10-08T17:00:00",
                "deferDate": "",
                "completionDate": "",
                "tags": "",
                "estimatedMinutes": None
            }
        ])

        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = tasks_json
            tasks = client.get_tasks(due_relative="today")

            assert len(tasks) == 1
            assert tasks[0]['name'] == "Task due today"
            # Verify the script includes date filtering
            call_args = mock_run.call_args[0][0]
            assert "due date" in call_args.lower()

    def test_get_tasks_due_tomorrow(self, client):
        """Test filtering for tasks due tomorrow."""
        tasks_json = json.dumps([
            {
                "id": "task-002",
                "name": "Task due tomorrow",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "blocked": False,
                "next": False,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "2025-10-09T17:00:00",
                "deferDate": "",
                "completionDate": "",
                "tags": "",
                "estimatedMinutes": None
            }
        ])

        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = tasks_json
            tasks = client.get_tasks(due_relative="tomorrow")

            assert len(tasks) == 1
            assert tasks[0]['name'] == "Task due tomorrow"

    def test_get_tasks_due_this_week(self, client):
        """Test filtering for tasks due this week."""
        tasks_json = json.dumps([
            {
                "id": "task-003",
                "name": "Task due this week",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "blocked": False,
                "next": False,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "2025-10-10T17:00:00",
                "deferDate": "",
                "completionDate": "",
                "tags": "",
                "estimatedMinutes": None
            }
        ])

        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = tasks_json
            tasks = client.get_tasks(due_relative="this_week")

            assert len(tasks) == 1

    def test_get_tasks_overdue_relative(self, client):
        """Test filtering for overdue tasks using relative filter."""
        tasks_json = json.dumps([
            {
                "id": "task-004",
                "name": "Overdue task",
                "note": "",
                "completed": False,
                "flagged": True,
                "dropped": False,
                "blocked": False,
                "next": True,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "2025-10-01T17:00:00",
                "deferDate": "",
                "completionDate": "",
                "tags": "",
                "estimatedMinutes": None
            }
        ])

        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = tasks_json
            tasks = client.get_tasks(due_relative="overdue")

            assert len(tasks) == 1
            assert tasks[0]['name'] == "Overdue task"

    def test_get_tasks_defer_relative_today(self, client):
        """Test filtering for tasks deferred until today."""
        tasks_json = json.dumps([
            {
                "id": "task-005",
                "name": "Available today",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "blocked": False,
                "next": True,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "",
                "deferDate": "2025-10-08T09:00:00",
                "completionDate": "",
                "tags": "",
                "estimatedMinutes": None
            }
        ])

        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = tasks_json
            tasks = client.get_tasks(defer_relative="today")

            assert len(tasks) == 1
            assert tasks[0]['name'] == "Available today"

    def test_get_tasks_invalid_relative_value(self, client):
        """Test that invalid relative date values raise an error."""
        with pytest.raises(ValueError, match="Invalid due_relative value"):
            client.get_tasks(due_relative="invalid")
