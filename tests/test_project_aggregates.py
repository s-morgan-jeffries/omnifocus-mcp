"""Tests for project aggregation queries."""
import pytest
from unittest import mock

from omnifocus_mcp.omnifocus_client import OmniFocusClient


@pytest.fixture
def client():
    """Create a client with safety checks disabled."""
    return OmniFocusClient(enable_safety_checks=False)


class TestProjectAggregates:
    """Tests for get_project_aggregates method."""

    def test_basic_aggregates(self, client):
        """Test basic project aggregates calculation."""
        # Mock get_tasks to return tasks for this project
        with mock.patch.object(client, 'get_tasks') as mock_get_tasks:
            mock_get_tasks.return_value = [
                {"id": "t1", "name": "Task 1", "completed": False, "dueDate": "2026-01-15T00:00:00Z", "estimatedMinutes": 30},
                {"id": "t2", "name": "Task 2", "completed": False, "dueDate": "2026-01-20T00:00:00Z", "estimatedMinutes": 60},
                {"id": "t3", "name": "Task 3", "completed": False, "dueDate": "", "estimatedMinutes": 0}
            ]

            result = client.get_project_aggregates("proj-001")

            assert result['projectId'] == "proj-001"
            assert result['totalEstimatedMinutes'] == 90
            assert result['earliestDueDate'] == "2026-01-15T00:00:00Z"
            assert result['latestDueDate'] == "2026-01-20T00:00:00Z"
            assert result['overdueTaskCount'] == 0
            assert result['taskCount'] == 3

    def test_overdue_tasks(self, client):
        """Test counting overdue tasks."""
        with mock.patch.object(client, 'get_tasks') as mock_get_tasks:
            # Mock tasks with past due dates
            mock_get_tasks.return_value = [
                {"id": "t1", "name": "Task 1", "completed": False, "dueDate": "2024-12-01T00:00:00Z", "estimatedMinutes": 30},
                {"id": "t2", "name": "Task 2", "completed": False, "dueDate": "2025-12-01T00:00:00Z", "estimatedMinutes": 0}
            ]

            result = client.get_project_aggregates("proj-001")

            # Should count task with past due date as overdue
            assert result['overdueTaskCount'] == 1

    def test_no_due_dates(self, client):
        """Test aggregates when no tasks have due dates."""
        with mock.patch.object(client, 'get_tasks') as mock_get_tasks:
            mock_get_tasks.return_value = [
                {"id": "t1", "name": "Task 1", "completed": False, "dueDate": "", "estimatedMinutes": 30},
                {"id": "t2", "name": "Task 2", "completed": False, "dueDate": "", "estimatedMinutes": 45}
            ]

            result = client.get_project_aggregates("proj-001")

            assert result['earliestDueDate'] is None
            assert result['latestDueDate'] is None
            assert result['totalEstimatedMinutes'] == 75

    def test_no_estimates(self, client):
        """Test aggregates when no tasks have time estimates."""
        with mock.patch.object(client, 'get_tasks') as mock_get_tasks:
            mock_get_tasks.return_value = [
                {"id": "t1", "name": "Task 1", "completed": False, "dueDate": "2026-01-15T00:00:00Z", "estimatedMinutes": 0},
                {"id": "t2", "name": "Task 2", "completed": False, "dueDate": "", "estimatedMinutes": 0}
            ]

            result = client.get_project_aggregates("proj-001")

            assert result['totalEstimatedMinutes'] == 0

    def test_empty_project(self, client):
        """Test aggregates for project with no tasks."""
        with mock.patch.object(client, 'get_tasks') as mock_get_tasks:
            mock_get_tasks.return_value = []

            result = client.get_project_aggregates("proj-001")

            assert result['projectId'] == "proj-001"
            assert result['taskCount'] == 0
            assert result['totalEstimatedMinutes'] == 0
            assert result['earliestDueDate'] is None
            assert result['latestDueDate'] is None
            assert result['overdueTaskCount'] == 0

    def test_include_completed_tasks(self, client):
        """Test that completed tasks are excluded by default."""
        with mock.patch.object(client, 'get_tasks') as mock_get_tasks:
            # get_tasks should be called without include_completed
            mock_get_tasks.return_value = [
                {"id": "t1", "name": "Task 1", "completed": False, "dueDate": "", "estimatedMinutes": 30}
            ]

            result = client.get_project_aggregates("proj-001")

            # Verify get_tasks was called with correct parameters
            mock_get_tasks.assert_called_once_with(project_id="proj-001", include_completed=False)
            assert result['taskCount'] == 1

    def test_missing_fields(self, client):
        """Test handling of tasks with missing fields."""
        with mock.patch.object(client, 'get_tasks') as mock_get_tasks:
            mock_get_tasks.return_value = [
                {"id": "t1", "name": "Task 1", "completed": False},
                {"id": "t2", "name": "Task 2", "completed": False, "estimatedMinutes": 30}
            ]

            result = client.get_project_aggregates("proj-001")

            # Should handle missing fields gracefully
            assert result['taskCount'] == 2
            assert result['totalEstimatedMinutes'] == 30
