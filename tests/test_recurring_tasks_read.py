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
        assert task['repeatSummary'] == 'Every week'

    def test_get_tasks_repeat_summary_for_non_recurring(self, client):
        """Non-recurring tasks should have repeatSummary=None."""
        mock_json = json.dumps([{
            "id": "task123",
            "name": "One-off task",
            "note": "",
            "completed": False,
            "flagged": False,
            "dropped": False,
            "blocked": False,
            "next": False,
            "projectId": "proj123",
            "projectName": "Project",
            "dueDate": "",
            "deferDate": "",
            "completionDate": "",
            "tags": "",
            "estimatedMinutes": None,
            "isRecurring": False,
            "recurrence": "",
            "repetitionMethod": ""
        }])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            tasks = client.get_tasks()

        assert len(tasks) == 1
        assert tasks[0]['repeatSummary'] is None

    def test_get_tasks_repeat_summary_complex_rrule(self, client):
        """Recurring tasks with BYDAY should get a detailed summary."""
        mock_json = json.dumps([{
            "id": "task123",
            "name": "MWF workout",
            "note": "",
            "completed": False,
            "flagged": False,
            "dropped": False,
            "blocked": False,
            "next": False,
            "projectId": "proj123",
            "projectName": "Project",
            "dueDate": "",
            "deferDate": "",
            "completionDate": "",
            "tags": "",
            "estimatedMinutes": None,
            "isRecurring": True,
            "recurrence": "FREQ=WEEKLY;INTERVAL=1;BYDAY=MO,WE,FR",
            "repetitionMethod": "fixed repetition"
        }])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            tasks = client.get_tasks()

        assert len(tasks) == 1
        assert tasks[0]['repeatSummary'] == 'Every week on Mon, Wed, Fri'

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


class TestNextOccurrenceDates:
    """Test that next occurrence date fields are included in task responses."""

    def test_recurring_task_has_next_dates(self, client):
        """Recurring tasks should include populated next occurrence dates."""
        mock_json = json.dumps([{
            "id": "task-recurring",
            "name": "Weekly standup",
            "note": "",
            "completed": False,
            "flagged": False,
            "dropped": False,
            "blocked": False,
            "next": False,
            "projectId": "proj123",
            "projectName": "Work",
            "dueDate": "2026-03-15T09:00:00",
            "deferDate": "",
            "completionDate": "",
            "tags": "",
            "estimatedMinutes": None,
            "isRecurring": True,
            "recurrence": "FREQ=WEEKLY",
            "repetitionMethod": "fixed repetition",
            "nextDueDate": "2026-03-22T09:00:00",
            "nextDeferDate": "",
            "nextPlannedDate": ""
        }])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            tasks = client.get_tasks()

        assert len(tasks) == 1
        task = tasks[0]
        assert task['nextDueDate'] == "2026-03-22T09:00:00"
        assert task['nextDeferDate'] == ""
        assert task['nextPlannedDate'] == ""

    def test_non_recurring_task_has_empty_next_dates(self, client):
        """Non-recurring tasks should have empty next occurrence dates."""
        mock_json = json.dumps([{
            "id": "task-regular",
            "name": "One-off task",
            "note": "",
            "completed": False,
            "flagged": False,
            "dropped": False,
            "blocked": False,
            "next": False,
            "projectId": "proj123",
            "projectName": "Work",
            "dueDate": "2026-03-15T17:00:00",
            "deferDate": "",
            "completionDate": "",
            "tags": "",
            "estimatedMinutes": None,
            "isRecurring": False,
            "recurrence": "",
            "repetitionMethod": "",
            "nextDueDate": "",
            "nextDeferDate": "",
            "nextPlannedDate": ""
        }])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            tasks = client.get_tasks()

        assert len(tasks) == 1
        task = tasks[0]
        assert task['nextDueDate'] == ""
        assert task['nextDeferDate'] == ""
        assert task['nextPlannedDate'] == ""

    def test_recurring_task_with_all_next_dates(self, client):
        """Recurring task with defer and planned dates should populate all next dates."""
        mock_json = json.dumps([{
            "id": "task-full-recurring",
            "name": "Monthly review",
            "note": "",
            "completed": False,
            "flagged": True,
            "dropped": False,
            "blocked": False,
            "next": False,
            "projectId": "proj456",
            "projectName": "Reviews",
            "dueDate": "2026-03-31T17:00:00",
            "deferDate": "2026-03-25T09:00:00",
            "plannedDate": "2026-03-28T09:00:00",
            "completionDate": "",
            "tags": "",
            "estimatedMinutes": 60,
            "isRecurring": True,
            "recurrence": "FREQ=MONTHLY",
            "repetitionMethod": "fixed repetition",
            "nextDueDate": "2026-04-30T17:00:00",
            "nextDeferDate": "2026-04-25T09:00:00",
            "nextPlannedDate": "2026-04-28T09:00:00"
        }])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            tasks = client.get_tasks()

        assert len(tasks) == 1
        task = tasks[0]
        assert task['nextDueDate'] == "2026-04-30T17:00:00"
        assert task['nextDeferDate'] == "2026-04-25T09:00:00"
        assert task['nextPlannedDate'] == "2026-04-28T09:00:00"

    def test_next_dates_in_applescript_batch_mode(self, client):
        """Verify batch mode AppleScript includes next date property reads."""
        mock_json = json.dumps([{
            "id": "task1",
            "name": "Flagged recurring",
            "note": "",
            "completed": False,
            "flagged": True,
            "dropped": False,
            "blocked": False,
            "next": False,
            "projectId": "",
            "projectName": "",
            "dueDate": "2026-03-15T09:00:00",
            "deferDate": "",
            "completionDate": "",
            "tags": "",
            "estimatedMinutes": None,
            "isRecurring": True,
            "recurrence": "FREQ=WEEKLY",
            "repetitionMethod": "fixed repetition",
            "nextDueDate": "2026-03-22T09:00:00",
            "nextDeferDate": "",
            "nextPlannedDate": ""
        }])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            # flagged_only triggers batch mode (whose clause)
            client.get_tasks(flagged_only=True)

        script = mock_run.call_args[0][0]
        assert "next due date" in script
        assert "next defer date" in script
        assert "next planned date" in script

    def test_next_dates_in_applescript_per_task_mode(self, client):
        """Verify per-task mode AppleScript includes next date property reads."""
        mock_json = json.dumps([{
            "id": "task1",
            "name": "Some task",
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
            "repetitionMethod": "",
            "nextDueDate": "",
            "nextDeferDate": "",
            "nextPlannedDate": ""
        }])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            # No filters = per-task mode (no whose clause)
            client.get_tasks()

        script = mock_run.call_args[0][0]
        assert "next due date" in script
        assert "next defer date" in script
        assert "next planned date" in script


class TestCatchUpAutomatically:
    """Test that catchUpAutomatically field is included in task responses."""

    def test_recurring_task_catch_up_true(self, client):
        """Recurring task with catch-up enabled should return True."""
        mock_json = json.dumps([{
            "id": "task-catchup",
            "name": "Weekly review",
            "note": "",
            "completed": False,
            "flagged": False,
            "dropped": False,
            "blocked": False,
            "next": False,
            "projectId": "proj123",
            "projectName": "Work",
            "dueDate": "2026-03-15T09:00:00",
            "deferDate": "",
            "completionDate": "",
            "tags": "",
            "estimatedMinutes": None,
            "isRecurring": True,
            "recurrence": "FREQ=WEEKLY",
            "repetitionMethod": "fixed repetition",
            "catchUpAutomatically": True,
            "nextDueDate": "2026-03-22T09:00:00",
            "nextDeferDate": "",
            "nextPlannedDate": ""
        }])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            tasks = client.get_tasks()

        assert len(tasks) == 1
        assert tasks[0]['catchUpAutomatically'] is True

    def test_recurring_task_catch_up_false(self, client):
        """Recurring task with catch-up disabled should return False."""
        mock_json = json.dumps([{
            "id": "task-nocatchup",
            "name": "Daily standup",
            "note": "",
            "completed": False,
            "flagged": False,
            "dropped": False,
            "blocked": False,
            "next": False,
            "projectId": "proj123",
            "projectName": "Work",
            "dueDate": "2026-03-15T09:00:00",
            "deferDate": "",
            "completionDate": "",
            "tags": "",
            "estimatedMinutes": None,
            "isRecurring": True,
            "recurrence": "FREQ=DAILY",
            "repetitionMethod": "fixed repetition",
            "catchUpAutomatically": False,
            "nextDueDate": "2026-03-16T09:00:00",
            "nextDeferDate": "",
            "nextPlannedDate": ""
        }])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            tasks = client.get_tasks()

        assert len(tasks) == 1
        assert tasks[0]['catchUpAutomatically'] is False

    def test_non_recurring_task_catch_up_null(self, client):
        """Non-recurring task should have catchUpAutomatically as None."""
        mock_json = json.dumps([{
            "id": "task-regular",
            "name": "One-off task",
            "note": "",
            "completed": False,
            "flagged": False,
            "dropped": False,
            "blocked": False,
            "next": False,
            "projectId": "proj123",
            "projectName": "Work",
            "dueDate": "",
            "deferDate": "",
            "completionDate": "",
            "tags": "",
            "estimatedMinutes": None,
            "isRecurring": False,
            "recurrence": "",
            "repetitionMethod": "",
            "catchUpAutomatically": None,
            "nextDueDate": "",
            "nextDeferDate": "",
            "nextPlannedDate": ""
        }])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            tasks = client.get_tasks()

        assert len(tasks) == 1
        assert tasks[0]['catchUpAutomatically'] is None

    def test_catch_up_in_applescript_batch_mode(self, client):
        """Verify batch mode AppleScript extracts catch up automatically."""
        mock_json = json.dumps([{
            "id": "task1",
            "name": "Flagged recurring",
            "note": "",
            "completed": False,
            "flagged": True,
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
            "repetitionMethod": "fixed repetition",
            "catchUpAutomatically": True,
            "nextDueDate": "",
            "nextDeferDate": "",
            "nextPlannedDate": ""
        }])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            client.get_tasks(flagged_only=True)

        script = mock_run.call_args[0][0]
        assert "catch up automatically" in script

    def test_catch_up_in_applescript_per_task_mode(self, client):
        """Verify per-task mode AppleScript extracts catch up automatically."""
        mock_json = json.dumps([{
            "id": "task1",
            "name": "Some task",
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
            "repetitionMethod": "",
            "catchUpAutomatically": None,
            "nextDueDate": "",
            "nextDeferDate": "",
            "nextPlannedDate": ""
        }])

        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            client.get_tasks()

        script = mock_run.call_args[0][0]
        assert "catch up automatically" in script
