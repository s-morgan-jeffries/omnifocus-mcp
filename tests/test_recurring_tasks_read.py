"""Tests for reading recurring task information."""

import json
import pytest
from unittest.mock import patch
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


@pytest.fixture
def client():
    """Create an OmniFocusConnector instance."""
    return OmniFocusConnector(enable_safety_checks=False)


class TestRecurringTaskFields:
    """Test that recurring task fields are included in task responses."""

    def test_get_tasks_includes_recurring_fields_for_non_recurring_task(self, client):
        """Non-recurring tasks should have isRecurring=False and None values."""
        # Mock response with a non-recurring task
        mock_json = json.dumps([{
            "id": "task123",
            "name": "Regular task",
            "note": "A note",
            "completed": False,
            "flagged": False,
            "dropped": False,
            "blocked": False,
            "next": False,
            "projectId": "proj123",
            "projectName": "Project",
            "dueDate": "2026-01-15T00:00:00Z",
            "deferDate": "",
            "completionDate": "",
            "tags": "work",
            "estimatedMinutes": 30,
            "isRecurring": False,
            "recurrence": "",
            "repetitionMethod": ""
        }])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            tasks = client.get_tasks()

        assert len(tasks) == 1
        task = tasks[0]
        assert task['isRecurring'] is False
        assert task['recurrence'] is None
        assert task['repetitionMethod'] is None

    def test_get_tasks_includes_recurring_fields_for_recurring_task(self, client):
        """Recurring tasks should have isRecurring=True and populated fields."""
        # Mock response with a recurring task
        mock_json = json.dumps([{
            "id": "task123",
            "name": "Weekly meeting",
            "note": "",
            "completed": False,
            "flagged": False,
            "dropped": False,
            "blocked": False,
            "next": False,
            "projectId": "proj123",
            "projectName": "Project",
            "dueDate": "2026-01-15T00:00:00Z",
            "deferDate": "",
            "completionDate": "",
            "tags": "",
            "estimatedMinutes": None,
            "isRecurring": True,
            "recurrence": "FREQ=WEEKLY",
            "repetitionMethod": "fixed repetition"
        }])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            tasks = client.get_tasks()

        assert len(tasks) == 1
        task = tasks[0]
        assert task['isRecurring'] is True
        assert task['recurrence'] == 'FREQ=WEEKLY'
        assert task['repetitionMethod'] == 'fixed'

    def test_get_tasks_handles_start_after_completion_method(self, client):
        """Test conversion of 'start after completion' method."""
        mock_json = json.dumps([{
            "id": "task123",
            "name": "Daily task",
            "note": "",
            "completed": False,
            "flagged": False,
            "dropped": False,
            "blocked": False,
            "next": False,
            "projectId": "",
            "projectName": "",
            "dueDate": "",
            "deferDate": "",
            "completionDate": "",
            "tags": "",
            "estimatedMinutes": None,
            "isRecurring": True,
            "recurrence": "FREQ=DAILY",
            "repetitionMethod": "start after completion"
        }])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            tasks = client.get_tasks()

        assert tasks[0]['repetitionMethod'] == 'start_after_completion'

    def test_get_tasks_handles_due_after_completion_method(self, client):
        """Test conversion of 'due after completion' method."""
        mock_json = json.dumps([{
            "id": "task123",
            "name": "Monthly task",
            "note": "",
            "completed": False,
            "flagged": False,
            "dropped": False,
            "blocked": False,
            "next": False,
            "projectId": "",
            "projectName": "",
            "dueDate": "",
            "deferDate": "",
            "completionDate": "",
            "tags": "",
            "estimatedMinutes": None,
            "isRecurring": True,
            "recurrence": "FREQ=MONTHLY",
            "repetitionMethod": "due after completion"
        }])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            tasks = client.get_tasks()

        assert tasks[0]['repetitionMethod'] == 'due_after_completion'


class TestRecurringOnlyFilter:
    """Test the recurring_only filter parameter."""

    def test_get_tasks_recurring_only_true(self, client):
        """recurring_only=True should return only recurring tasks."""
        mock_json = json.dumps([
            {
                "id": "task1",
                "name": "Regular task",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "blocked": False,
                "next": False,
                "projectId": "",
                "projectName": "",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": "",
                "estimatedMinutes": None,
                "isRecurring": False,
                "recurrence": "",
                "repetitionMethod": ""
            },
            {
                "id": "task2",
                "name": "Weekly meeting",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "blocked": False,
                "next": False,
                "projectId": "",
                "projectName": "",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": "",
                "estimatedMinutes": None,
                "isRecurring": True,
                "recurrence": "FREQ=WEEKLY",
                "repetitionMethod": "fixed repetition"
            },
            {
                "id": "task3",
                "name": "Another regular task",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "blocked": False,
                "next": False,
                "projectId": "",
                "projectName": "",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": "",
                "estimatedMinutes": None,
                "isRecurring": False,
                "recurrence": "",
                "repetitionMethod": ""
            }
        ])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            tasks = client.get_tasks(recurring_only=True)

        assert len(tasks) == 1
        assert tasks[0]['name'] == 'Weekly meeting'
        assert tasks[0]['isRecurring'] is True

    def test_get_tasks_recurring_only_false(self, client):
        """recurring_only=False should return only non-recurring tasks."""
        mock_json = json.dumps([
            {
                "id": "task1",
                "name": "Regular task",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "blocked": False,
                "next": False,
                "projectId": "",
                "projectName": "",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": "",
                "estimatedMinutes": None,
                "isRecurring": False,
                "recurrence": "",
                "repetitionMethod": ""
            },
            {
                "id": "task2",
                "name": "Weekly meeting",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "blocked": False,
                "next": False,
                "projectId": "",
                "projectName": "",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": "",
                "estimatedMinutes": None,
                "isRecurring": True,
                "recurrence": "FREQ=WEEKLY",
                "repetitionMethod": "fixed repetition"
            }
        ])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            tasks = client.get_tasks(recurring_only=False)

        assert len(tasks) == 1
        assert tasks[0]['name'] == 'Regular task'
        assert tasks[0]['isRecurring'] is False

    def test_get_tasks_recurring_only_none_returns_all(self, client):
        """recurring_only=None should return all tasks."""
        mock_json = json.dumps([
            {
                "id": "task1",
                "name": "Regular task",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "blocked": False,
                "next": False,
                "projectId": "",
                "projectName": "",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": "",
                "estimatedMinutes": None,
                "isRecurring": False,
                "recurrence": "",
                "repetitionMethod": ""
            },
            {
                "id": "task2",
                "name": "Weekly meeting",
                "note": "",
                "completed": False,
                "flagged": False,
                "dropped": False,
                "blocked": False,
                "next": False,
                "projectId": "",
                "projectName": "",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": "",
                "estimatedMinutes": None,
                "isRecurring": True,
                "recurrence": "FREQ=WEEKLY",
                "repetitionMethod": "fixed repetition"
            }
        ])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            tasks = client.get_tasks(recurring_only=None)

        assert len(tasks) == 2
