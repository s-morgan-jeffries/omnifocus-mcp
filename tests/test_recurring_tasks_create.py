"""Tests for creating recurring tasks."""

import pytest
from unittest.mock import patch
from omnifocus_mcp.omnifocus_client import OmniFocusClient


@pytest.fixture
def client():
    """Create an OmniFocusClient instance."""
    return OmniFocusClient(enable_safety_checks=False)


class TestCreateRecurringTasksInProject:
    """Test creating recurring tasks in projects."""

    def test_add_task_with_recurrence_fixed(self, client):
        """Test creating a recurring task with fixed repetition."""
        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            success = client.create_task(
                project_id="proj-123",
                task_name="Weekly meeting",
                recurrence="FREQ=WEEKLY",
                repetition_method="fixed"
            )

            assert success is True

            # Verify the AppleScript includes repetition logic
            call_args = mock_run.call_args[0][0]
            assert "repetition rule" in call_args.lower()
            assert "FREQ=WEEKLY" in call_args
            assert "fixed repetition" in call_args

    def test_add_task_with_recurrence_start_after_completion(self, client):
        """Test creating a recurring task with start after completion method."""
        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            success = client.create_task(
                project_id="proj-123",
                task_name="Daily task",
                recurrence="FREQ=DAILY",
                repetition_method="start_after_completion"
            )

            assert success is True

            call_args = mock_run.call_args[0][0]
            assert "repetition rule" in call_args.lower()
            assert "FREQ=DAILY" in call_args
            assert "start after completion" in call_args

    def test_add_task_with_recurrence_due_after_completion(self, client):
        """Test creating a recurring task with due after completion method."""
        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            success = client.create_task(
                project_id="proj-123",
                task_name="Monthly review",
                recurrence="FREQ=MONTHLY",
                repetition_method="due_after_completion"
            )

            assert success is True

            call_args = mock_run.call_args[0][0]
            assert "repetition rule" in call_args.lower()
            assert "FREQ=MONTHLY" in call_args
            assert "due after completion" in call_args

    def test_add_task_with_recurrence_defaults_to_fixed(self, client):
        """Test that repetition_method defaults to 'fixed' if not specified."""
        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            success = client.create_task(
                project_id="proj-123",
                task_name="Weekly task",
                recurrence="FREQ=WEEKLY"
            )

            assert success is True

            call_args = mock_run.call_args[0][0]
            assert "fixed repetition" in call_args

    def test_add_task_without_recurrence(self, client):
        """Test creating a non-recurring task (no repetition logic in script)."""
        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            success = client.create_task(
                project_id="proj-123",
                task_name="Regular task"
            )

            assert success is True

            call_args = mock_run.call_args[0][0]
            # Should not include repetition logic
            assert "repetition rule" not in call_args.lower()

    def test_add_task_invalid_repetition_method(self, client):
        """Test that invalid repetition method raises ValueError."""
        with pytest.raises(ValueError, match="Invalid repetition_method"):
            client.create_task(
                project_id="proj-123",
                task_name="Test task",
                recurrence="FREQ=DAILY",
                repetition_method="invalid_method"
            )

    def test_add_task_method_without_recurrence_raises_error(self, client):
        """Test that providing repetition_method without recurrence raises ValueError."""
        with pytest.raises(ValueError, match="repetition_method requires recurrence"):
            client.create_task(
                project_id="proj-123",
                task_name="Test task",
                repetition_method="fixed"
            )

    def test_add_task_with_recurrence_and_other_params(self, client):
        """Test creating a recurring task with other parameters."""
        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            success = client.create_task(
                project_id="proj-123",
                task_name="Weekly report",
                note="Submit by Friday",
                due_date="2026-01-31T17:00:00Z",
                recurrence="FREQ=WEEKLY",
                repetition_method="fixed"
            )

            assert success is True

            call_args = mock_run.call_args[0][0]
            assert "Weekly report" in call_args
            assert "Submit by Friday" in call_args
            assert "proj-123" in call_args
            assert "FREQ=WEEKLY" in call_args
            assert "fixed repetition" in call_args

    def test_add_task_complex_recurrence_rule(self, client):
        """Test creating a task with a complex recurrence rule."""
        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            success = client.create_task(
                project_id="proj-123",
                task_name="Bi-weekly standup",
                recurrence="FREQ=WEEKLY;INTERVAL=2;BYDAY=MO",
                repetition_method="fixed"
            )

            assert success is True

            call_args = mock_run.call_args[0][0]
            assert "FREQ=WEEKLY;INTERVAL=2;BYDAY=MO" in call_args


class TestCreateRecurringInboxTasks:
    """Test creating recurring tasks in inbox."""

    def test_create_inbox_task_with_recurrence(self, client):
        """Test creating a recurring inbox task."""
        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            success = client.create_task(
                task_name="Daily check-in",
                recurrence="FREQ=DAILY",
                repetition_method="fixed"
            )

            assert success is True

            call_args = mock_run.call_args[0][0]
            assert "repetition rule" in call_args.lower()
            assert "FREQ=DAILY" in call_args

    def test_create_inbox_task_without_recurrence(self, client):
        """Test creating a non-recurring inbox task."""
        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            success = client.create_task(
                task_name="One-time task"
            )

            assert success is True

            call_args = mock_run.call_args[0][0]
            # Should not include repetition logic
            assert "repetition rule" not in call_args.lower()
