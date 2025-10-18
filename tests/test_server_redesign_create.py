"""Tests for redesigned server API create functions (server_fastmcp.py layer).

This file tests the MCP server layer for the NEW API (v1.0.0 redesign).
Tests are written FIRST (TDD) before implementing server changes.
"""
import pytest
from unittest import mock

# Import server module
import omnifocus_mcp.server_fastmcp as server

# Extract function from FunctionTool wrapper
create_task = server.create_task.fn


class TestCreateTaskServerRedesign:
    """Tests for create_task() MCP tool (NEW API).

    The server tool should:
    - Accept all parameters from client.create_task()
    - Handle string return from client (task ID)
    - Return human-readable response for Claude
    - Handle inbox vs project vs subtask creation
    """

    # ========================================================================
    # Basic Creation (Project vs Inbox)
    # ========================================================================

    def test_create_task_in_project(self):
        """NEW API: Server creates task in specified project."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_task.return_value = "task-001"
            mock_get_client.return_value = mock_client

            result = create_task(
                task_name="Test Task",
                project_id="proj-123"
            )

            # Verify client was called
            mock_client.create_task.assert_called_once_with(
                task_name="Test Task",
                project_id="proj-123",
                parent_task_id=None,
                note=None,
                due_date=None,
                defer_date=None,
                flagged=False,
                tags=None,
                estimated_minutes=None
            )

            # Verify response mentions task ID
            assert "task-001" in result

    def test_create_task_in_inbox(self):
        """NEW API: Server creates task in inbox when project_id=None."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_task.return_value = "task-002"
            mock_get_client.return_value = mock_client

            result = create_task(
                task_name="Inbox Task",
                project_id=None
            )

            mock_client.create_task.assert_called_once()
            assert "task-002" in result
            assert "inbox" in result.lower() or "created" in result.lower()

    def test_create_task_defaults_to_inbox(self):
        """NEW API: Server creates in inbox when project_id not specified."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_task.return_value = "task-003"
            mock_get_client.return_value = mock_client

            result = create_task(task_name="Default Task")

            # Should pass project_id=None (default)
            call_kwargs = mock_client.create_task.call_args[1]
            assert call_kwargs['project_id'] is None
            assert "task-003" in result

    # ========================================================================
    # Hierarchy (parent_task_id)
    # ========================================================================

    def test_create_task_with_parent_task_id(self):
        """NEW API: Server creates subtask with parent_task_id."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_task.return_value = "task-004"
            mock_get_client.return_value = mock_client

            result = create_task(
                task_name="Subtask",
                parent_task_id="task-parent"
            )

            mock_client.create_task.assert_called_once()
            call_kwargs = mock_client.create_task.call_args[1]
            assert call_kwargs['parent_task_id'] == "task-parent"
            assert "task-004" in result

    # ========================================================================
    # Optional Fields
    # ========================================================================

    def test_create_task_with_all_optional_fields(self):
        """NEW API: Server passes all optional fields to client."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_task.return_value = "task-005"
            mock_get_client.return_value = mock_client

            result = create_task(
                task_name="Full Task",
                project_id="proj-123",
                note="Task note",
                due_date="2025-12-31",
                defer_date="2025-12-01",
                flagged=True,
                tags='["urgent", "work"]',  # JSON string, not list
                estimated_minutes=60
            )

            mock_client.create_task.assert_called_once_with(
                task_name="Full Task",
                project_id="proj-123",
                parent_task_id=None,
                note="Task note",
                due_date="2025-12-31",
                defer_date="2025-12-01",
                flagged=True,
                tags=["urgent", "work"],  # Parsed to list by server
                estimated_minutes=60
            )
            assert "task-005" in result

    # ========================================================================
    # Error Handling
    # ========================================================================

    def test_create_task_handles_client_error(self):
        """NEW API: Server handles client exceptions gracefully."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_task.side_effect = ValueError(
                "Cannot specify both project_id and parent_task_id"
            )
            mock_get_client.return_value = mock_client

            with pytest.raises(ValueError) as exc_info:
                create_task(
                    task_name="Bad Task",
                    project_id="proj-123",
                    parent_task_id="task-parent"
                )

            assert "project_id" in str(exc_info.value).lower()
            assert "parent_task_id" in str(exc_info.value).lower()

    # ========================================================================
    # Return Format
    # ========================================================================

    def test_create_task_returns_human_readable_response(self):
        """NEW API: Server returns human-readable response with task ID."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_task.return_value = "task-new-id"
            mock_get_client.return_value = mock_client

            result = create_task(task_name="New Task")

            assert isinstance(result, str)
            assert "task-new-id" in result
            # Should be human-readable, not just the ID
            assert len(result) > len("task-new-id")
