"""Tests for batch operations."""
import json
from unittest import mock
import pytest
from omnifocus_mcp.omnifocus_client import OmniFocusClient


@pytest.fixture
def client():
    """Create an OmniFocusClient instance."""
    return OmniFocusClient()


class TestBatchComplete:
    """Tests for batch task completion."""

    def test_complete_tasks_success(self, client):
        """Test completing multiple tasks successfully."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "3"  # 3 tasks completed

            task_ids = ["task-001", "task-002", "task-003"]
            result = client.complete_tasks(task_ids)

            assert result == 3
            # Verify AppleScript was called
            call_args = mock_run.call_args[0][0]
            assert "task-001" in call_args
            assert "task-002" in call_args
            assert "task-003" in call_args
            assert "completed" in call_args.lower()

    def test_complete_tasks_single(self, client):
        """Test completing a single task via batch operation."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "1"

            result = client.complete_tasks(["task-001"])

            assert result == 1

    def test_complete_tasks_empty_list(self, client):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError, match="task_ids cannot be empty"):
            client.complete_tasks([])

    def test_complete_tasks_partial_success(self, client):
        """Test when some tasks complete but others don't exist."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "2"  # Only 2 of 3 succeeded

            task_ids = ["task-001", "task-002", "nonexistent"]
            result = client.complete_tasks(task_ids)

            # Should return count of successfully completed
            assert result == 2

    def test_complete_tasks_already_completed(self, client):
        """Test completing tasks that are already completed."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "0"  # Already completed

            result = client.complete_tasks(["completed-task"])

            assert result == 0

    def test_complete_tasks_error(self, client):
        """Test error handling in batch completion."""
        import subprocess
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            error = subprocess.CalledProcessError(1, 'osascript')
            error.stderr = "OmniFocus error"
            mock_run.side_effect = error

            with pytest.raises(Exception, match="Error completing tasks"):
                client.complete_tasks(["task-001"])
