"""Tests for redesigned server API delete functions (server_fastmcp.py layer).

This file tests the MCP server layer for the NEW API (v1.0.0 redesign).
Tests are written FIRST (TDD) before implementing server changes.
"""
import pytest
from unittest import mock

# Import server module
import omnifocus_mcp.server_fastmcp as server

# Extract function from FunctionTool wrapper
delete_tasks = server.delete_tasks.fn


class TestDeleteTasksServerRedesign:
    """Tests for enhanced delete_tasks() MCP tool (NEW API).

    The enhanced server tool should:
    - Accept Union[str, list[str]] for task_ids
    - Handle dict return from client (not int)
    - Return structured response for Claude
    """

    # ========================================================================
    # Union Type Handling
    # ========================================================================

    def test_delete_tasks_with_single_id_string(self):
        """NEW API: Server handles single task ID as string."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.delete_tasks.return_value = {
                "deleted_count": 1,
                "failed_count": 0,
                "deleted_ids": ["task-001"],
                "failures": []
            }
            mock_get_client.return_value = mock_client

            result = delete_tasks("task-001")

            # Verify client was called
            mock_client.delete_tasks.assert_called_once_with("task-001")

            # Verify response
            assert "1 task" in result.lower() or "deleted" in result.lower()

    def test_delete_tasks_with_list_of_ids(self):
        """NEW API: Server handles list of task IDs."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.delete_tasks.return_value = {
                "deleted_count": 3,
                "failed_count": 0,
                "deleted_ids": ["task-001", "task-002", "task-003"],
                "failures": []
            }
            mock_get_client.return_value = mock_client

            result = delete_tasks(["task-001", "task-002", "task-003"])

            mock_client.delete_tasks.assert_called_once()
            assert "3" in result or "3 tasks" in result.lower()

    # ========================================================================
    # Return Format and Error Handling
    # ========================================================================

    def test_delete_tasks_shows_success_count(self):
        """NEW API: Server response includes success count."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.delete_tasks.return_value = {
                "deleted_count": 5,
                "failed_count": 0,
                "deleted_ids": ["task-001", "task-002", "task-003", "task-004", "task-005"],
                "failures": []
            }
            mock_get_client.return_value = mock_client

            result = delete_tasks(
                ["task-001", "task-002", "task-003", "task-004", "task-005"]
            )

            assert "5" in result

    def test_delete_tasks_handles_partial_failures(self):
        """NEW API: Server shows both successes and failures."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.delete_tasks.return_value = {
                "deleted_count": 2,
                "failed_count": 1,
                "deleted_ids": ["task-001", "task-002"],
                "failures": []
            }
            mock_get_client.return_value = mock_client

            result = delete_tasks(
                ["task-001", "task-002", "task-invalid"]
            )

            # Should mention both successes and failures
            assert "2" in result
            assert "1" in result or "failed" in result.lower()

    def test_delete_tasks_handles_all_failures(self):
        """NEW API: Server handles case where all tasks fail."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.delete_tasks.return_value = {
                "deleted_count": 0,
                "failed_count": 2,
                "deleted_ids": [],
                "failures": []
            }
            mock_get_client.return_value = mock_client

            result = delete_tasks(["task-001", "task-002"])

            assert "0" in result or "no tasks" in result.lower() or "failed" in result.lower()
