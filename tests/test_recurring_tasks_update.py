"""Tests for updating recurring tasks."""

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
        """Test adding recurrence to a non-recurring task (LEGACY TEST - updated for new API return format)."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                recurrence="FREQ=WEEKLY",
                repetition_method="fixed"
            )

            # NEW API: Returns dict instead of bool
            assert result["success"] is True

            call_args = mock_run.call_args[0][0]
            assert "repetition rule" in call_args.lower()
            assert "FREQ=WEEKLY" in call_args
            assert "fixed repetition" in call_args

    def test_update_task_modify_recurrence(self, client):
        """Test modifying the recurrence of an existing recurring task (LEGACY TEST - updated for new API return format)."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                recurrence="FREQ=DAILY",
                repetition_method="start_after_completion"
            )

            # NEW API: Returns dict instead of bool
            assert result["success"] is True

            call_args = mock_run.call_args[0][0]
            assert "FREQ=DAILY" in call_args
            assert "start after completion" in call_args

    def test_update_task_remove_recurrence(self, client):
        """Test removing recurrence from a recurring task (LEGACY TEST - updated for new API return format)."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                recurrence=""  # Empty string to remove
            )

            # NEW API: Returns dict instead of bool
            assert result["success"] is True

            call_args = mock_run.call_args[0][0]
            # Should set repetition rule to missing value
            assert "missing value" in call_args.lower()

    def test_update_task_change_method_only(self, client):
        """Test changing only the repetition method (LEGACY TEST - updated for new API return format)."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                repetition_method="due_after_completion"
            )

            # NEW API: Returns dict instead of bool
            assert result["success"] is True

            call_args = mock_run.call_args[0][0]
            assert "due after completion" in call_args

    def test_update_task_with_recurrence_and_other_params(self, client):
        """Test updating recurrence along with other task properties (LEGACY TEST - updated for new API return format)."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                task_name="Updated task",
                note="Updated note",
                recurrence="FREQ=MONTHLY",
                repetition_method="fixed"
            )

            # NEW API: Returns dict instead of bool
            assert result["success"] is True

            call_args = mock_run.call_args[0][0]
            assert "Updated task" in call_args
            assert "Updated note" in call_args
            assert "FREQ=MONTHLY" in call_args
            assert "fixed repetition" in call_args

    def test_update_task_invalid_repetition_method(self, client):
        """Test that invalid repetition method raises ValueError."""
        with pytest.raises(ValueError, match="Invalid repetition_method"):
            client.update_task(
                task_id="task-123",
                recurrence="FREQ=DAILY",
                repetition_method="invalid_method"
            )

    def test_update_task_no_changes(self, client):
        """Test updating a task with no recurring changes works normally (LEGACY TEST - updated for new API return format)."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                task_name="New name"
            )

            # NEW API: Returns dict instead of bool
            assert result["success"] is True

            call_args = mock_run.call_args[0][0]
            # Should not include repetition logic
            assert "repetition rule" not in call_args.lower() or "missing value" not in call_args.lower()
