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


class TestBatchMove:
    """Tests for batch task movement."""

    def test_move_tasks_to_project(self, client):
        """Test moving multiple tasks to a project."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "3"  # 3 tasks moved

            task_ids = ["task-001", "task-002", "task-003"]
            result = client.move_tasks(task_ids, "proj-001")

            assert result == 3
            # Verify AppleScript contains all task IDs and target project
            call_args = mock_run.call_args[0][0]
            assert "task-001" in call_args
            assert "task-002" in call_args
            assert "task-003" in call_args
            assert "proj-001" in call_args

    def test_move_tasks_to_inbox(self, client):
        """Test moving multiple tasks to inbox."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "2"

            task_ids = ["task-001", "task-002"]
            result = client.move_tasks(task_ids, None)  # None = inbox

            assert result == 2
            # Verify it moves to document tasks (inbox)
            call_args = mock_run.call_args[0][0]
            assert "tasks of front document" in call_args.lower()

    def test_move_tasks_empty_list(self, client):
        """Test that empty task list raises ValueError."""
        with pytest.raises(ValueError, match="task_ids cannot be empty"):
            client.move_tasks([], "proj-001")

    def test_move_tasks_partial_success(self, client):
        """Test when some tasks move but others don't exist."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "2"  # Only 2 of 3

            task_ids = ["task-001", "task-002", "nonexistent"]
            result = client.move_tasks(task_ids, "proj-001")

            assert result == 2

    def test_move_tasks_error(self, client):
        """Test error handling in batch movement."""
        import subprocess
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            error = subprocess.CalledProcessError(1, 'osascript')
            error.stderr = "Project not found"
            mock_run.side_effect = error

            with pytest.raises(Exception, match="Error moving tasks"):
                client.move_tasks(["task-001"], "nonexistent-project")


class TestBatchTag:
    """Tests for batch tagging operations."""

    def test_add_tag_to_tasks(self, client):
        """Test adding a tag to multiple tasks."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "3"

            task_ids = ["task-001", "task-002", "task-003"]
            result = client.add_tag_to_tasks(task_ids, "urgent")

            assert result == 3
            call_args = mock_run.call_args[0][0]
            assert "task-001" in call_args
            assert "urgent" in call_args

    def test_add_tag_to_tasks_empty_list(self, client):
        """Test that empty task list raises ValueError."""
        with pytest.raises(ValueError, match="task_ids cannot be empty"):
            client.add_tag_to_tasks([], "urgent")

    def test_add_tag_to_tasks_empty_tag(self, client):
        """Test that empty tag name raises ValueError."""
        with pytest.raises(ValueError, match="tag_name cannot be empty"):
            client.add_tag_to_tasks(["task-001"], "")

    def test_remove_tag_from_tasks(self, client):
        """Test removing a tag from multiple tasks."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "2"

            task_ids = ["task-001", "task-002"]
            result = client.remove_tag_from_tasks(task_ids, "urgent")

            assert result == 2
            call_args = mock_run.call_args[0][0]
            assert "task-001" in call_args
            assert "urgent" in call_args

    def test_remove_tag_from_tasks_empty_list(self, client):
        """Test that empty task list raises ValueError."""
        with pytest.raises(ValueError, match="task_ids cannot be empty"):
            client.remove_tag_from_tasks([], "urgent")

    def test_remove_tag_from_tasks_empty_tag(self, client):
        """Test that empty tag name raises ValueError."""
        with pytest.raises(ValueError, match="tag_name cannot be empty"):
            client.remove_tag_from_tasks(["task-001"], "")

    def test_add_tag_to_tasks_partial_success(self, client):
        """Test when some tasks get tagged but others don't exist."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "2"  # Only 2 of 3

            task_ids = ["task-001", "task-002", "nonexistent"]
            result = client.add_tag_to_tasks(task_ids, "urgent")

            assert result == 2

    def test_add_tag_error(self, client):
        """Test error handling in batch tagging."""
        import subprocess
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            error = subprocess.CalledProcessError(1, 'osascript')
            error.stderr = "Tag error"
            mock_run.side_effect = error

            with pytest.raises(Exception, match="Error adding tag"):
                client.add_tag_to_tasks(["task-001"], "urgent")
