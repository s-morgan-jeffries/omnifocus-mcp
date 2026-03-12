"""Tests for updating recurring tasks.

Tests verify that update_task generates correct AppleScript/OmniAutomation calls
for recurrence operations:
- Remove: AppleScript `set repetition rule to missing value` (single call)
- Set/Modify: OmniAutomation `evaluate javascript` with Task.RepetitionRule (two calls)
- Change method only: OmniAutomation reads current RRULE, creates new rule (two calls)
"""

import pytest
from unittest.mock import patch
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


@pytest.fixture
def client():
    """Create an OmniFocusConnector instance."""
    return OmniFocusConnector(enable_safety_checks=False)


class TestUpdateRecurringTasks:
    """Test updating tasks with recurrence rules."""

    def test_update_task_add_recurrence_to_non_recurring(self, client):
        """Test adding recurrence to a non-recurring task via OmniAutomation."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                recurrence="FREQ=WEEKLY",
                repetition_method="fixed"
            )

            assert result["success"] is True

            # Two calls: main AppleScript update + OmniAutomation JS for recurrence
            assert mock_run.call_count == 2

            # Second call should be the OmniAutomation JS
            js_call = mock_run.call_args_list[1][0][0]
            assert "evaluate javascript" in js_call
            assert "Task.RepetitionRule" in js_call
            assert "FREQ=WEEKLY" in js_call
            assert "Task.RepetitionMethod.Fixed" in js_call

    def test_update_task_modify_recurrence(self, client):
        """Test modifying the recurrence of an existing recurring task."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                recurrence="FREQ=DAILY",
                repetition_method="start_after_completion"
            )

            assert result["success"] is True
            assert mock_run.call_count == 2

            js_call = mock_run.call_args_list[1][0][0]
            assert "FREQ=DAILY" in js_call
            assert "Task.RepetitionMethod.DeferUntilDate" in js_call

    def test_update_task_remove_recurrence(self, client):
        """Test removing recurrence from a recurring task via AppleScript."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                recurrence=""  # Empty string to remove
            )

            assert result["success"] is True

            # Remove uses AppleScript only — single call
            assert mock_run.call_count == 1

            call_args = mock_run.call_args[0][0]
            assert "missing value" in call_args.lower()

    def test_update_task_change_method_only(self, client):
        """Test changing only the repetition method via OmniAutomation."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                repetition_method="due_after_completion"
            )

            assert result["success"] is True
            assert mock_run.call_count == 2

            js_call = mock_run.call_args_list[1][0][0]
            assert "Task.RepetitionMethod.DueDate" in js_call
            # Should read existing ruleString and reuse it
            assert "t.repetitionRule.ruleString" in js_call

    def test_update_task_with_recurrence_and_other_params(self, client):
        """Test updating recurrence along with other task properties."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                task_name="Updated task",
                note="Updated note",
                recurrence="FREQ=MONTHLY",
                repetition_method="fixed"
            )

            assert result["success"] is True
            assert mock_run.call_count == 2

            # First call: main AppleScript with name + note
            main_call = mock_run.call_args_list[0][0][0]
            assert "Updated task" in main_call
            assert "Updated note" in main_call

            # Second call: OmniAutomation JS for recurrence
            js_call = mock_run.call_args_list[1][0][0]
            assert "FREQ=MONTHLY" in js_call
            assert "Task.RepetitionMethod.Fixed" in js_call

    def test_update_task_invalid_repetition_method(self, client):
        """Test that invalid repetition method raises ValueError."""
        with pytest.raises(ValueError, match="Invalid repetition_method"):
            client.update_task(
                task_id="task-123",
                recurrence="FREQ=DAILY",
                repetition_method="invalid_method"
            )

    def test_update_task_no_changes(self, client):
        """Test updating a task with no recurring changes works normally."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                task_name="New name"
            )

            assert result["success"] is True

            # No recurrence change — single AppleScript call only
            assert mock_run.call_count == 1

            call_args = mock_run.call_args[0][0]
            assert "evaluate javascript" not in call_args
