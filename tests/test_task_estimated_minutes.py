"""Tests for estimatedMinutes field in task responses."""
import json
from unittest import mock
import pytest
from omnifocus_mcp.omnifocus_client import OmniFocusClient


@pytest.fixture
def client():
    """Create an OmniFocusClient instance."""
    return OmniFocusClient()


class TestTaskEstimatedMinutes:
    """Tests for estimatedMinutes field in tasks."""

    def test_get_task_includes_estimated_minutes(self, client):
        """Test that get_task includes estimatedMinutes field."""
        task_json = json.dumps({
            "id": "task-001",
            "name": "Task with estimate",
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
            "estimatedMinutes": 30
        })

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = task_json
            task = client.get_task("task-001")

            assert task['estimatedMinutes'] == 30

    def test_get_task_no_estimate(self, client):
        """Test task with no time estimate."""
        task_json = json.dumps({
            "id": "task-002",
            "name": "Task without estimate",
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
            "estimatedMinutes": None
        })

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = task_json
            task = client.get_task("task-002")

            assert task['estimatedMinutes'] is None

    def test_get_tasks_includes_estimated_minutes(self, client):
        """Test that get_tasks includes estimatedMinutes for all tasks."""
        tasks_json = json.dumps([
            {
                "id": "task-001",
                "name": "Quick task",
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
            },
            {
                "id": "task-002",
                "name": "Long task",
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
                "estimatedMinutes": 120
            },
            {
                "id": "task-003",
                "name": "No estimate",
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
                "estimatedMinutes": None
            }
        ])

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = tasks_json
            tasks = client.get_tasks()

            assert len(tasks) == 3
            assert tasks[0]['estimatedMinutes'] == 15
            assert tasks[1]['estimatedMinutes'] == 120
            assert tasks[2]['estimatedMinutes'] is None
