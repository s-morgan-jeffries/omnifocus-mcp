"""Tests for redesigned server API (server_fastmcp.py layer).

This file tests the MCP server layer for the NEW API (v1.0.0 redesign).
Tests are written FIRST (TDD) before implementing server changes.
"""
import pytest
from unittest import mock

# Import server module
import omnifocus_mcp.server_fastmcp as server

# Extract function from FunctionTool wrapper
# Note: This will fail initially because we haven't updated the server yet
# That's the point of TDD!
update_task = server.update_task.fn


class TestUpdateTaskServerRedesign:
    """Tests for enhanced update_task() MCP tool (NEW API).

    The redesigned server tool should:
    - Accept all new parameters (project_id, parent_task_id, tags, etc.)
    - Handle dict return from client (not bool)
    - Return structured response for Claude
    - Validate conflicts (project_id vs parent_task_id, tags vs add_tags)
    """

    # ========================================================================
    # Basic Field Updates
    # ========================================================================

    def test_update_task_with_task_name(self):
        """NEW API: Server handles task_name parameter."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["task_name"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            result = update_task("task-001", task_name="New Name")

            # Verify client was called
            mock_client.update_task.assert_called_once()
            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["task_id"] == "task-001"
            assert call_kwargs["task_name"] == "New Name"

            # Verify structured response
            assert "Successfully updated task task-001" in result
            assert "task_name" in result

    def test_update_task_with_multiple_fields(self):
        """NEW API: Server handles multiple fields at once."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["task_name", "flagged", "due_date"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            result = update_task(
                "task-001",
                task_name="New Name",
                flagged=True,
                due_date="2025-12-31"
            )

            mock_client.update_task.assert_called_once()
            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["task_name"] == "New Name"
            assert call_kwargs["flagged"] is True
            assert call_kwargs["due_date"] == "2025-12-31"

            assert "Successfully updated task" in result

    # ========================================================================
    # New Parameters (Hierarchy)
    # ========================================================================

    def test_update_task_with_project_id(self):
        """NEW API: Server handles project_id parameter (move to project)."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["project_id"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            result = update_task("task-001", project_id="proj-456")

            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["project_id"] == "proj-456"
            assert "Successfully updated task" in result

    def test_update_task_with_parent_task_id(self):
        """NEW API: Server handles parent_task_id parameter (make subtask)."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["parent_task_id"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            result = update_task("task-001", parent_task_id="task-parent")

            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["parent_task_id"] == "task-parent"
            assert "Successfully updated task" in result

    # ========================================================================
    # New Parameters (Tags)
    # ========================================================================

    def test_update_task_with_tags_list(self):
        """NEW API: Server handles tags parameter (full replacement)."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["tags"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            result = update_task("task-001", tags=["urgent", "work"])

            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["tags"] == ["urgent", "work"]
            assert "Successfully updated task" in result

    def test_update_task_with_add_tags(self):
        """NEW API: Server handles add_tags parameter (incremental add)."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["add_tags"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            result = update_task("task-001", add_tags=["new-tag"])

            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["add_tags"] == ["new-tag"]
            assert "Successfully updated task" in result

    def test_update_task_with_remove_tags(self):
        """NEW API: Server handles remove_tags parameter."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["remove_tags"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            result = update_task("task-001", remove_tags=["old-tag"])

            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["remove_tags"] == ["old-tag"]
            assert "Successfully updated task" in result

    # ========================================================================
    # New Parameters (Completion & Status)
    # ========================================================================

    def test_update_task_with_completed(self):
        """NEW API: Server handles completed parameter (replaces complete_task)."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["completed"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            result = update_task("task-001", completed=True)

            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["completed"] is True
            assert "Successfully updated task" in result

    def test_update_task_with_status_string(self):
        """NEW API: Server handles status parameter (accepts string)."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["status"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            result = update_task("task-001", status="dropped")

            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["status"] == "dropped"
            assert "Successfully updated task" in result

    def test_update_task_with_estimated_minutes(self):
        """NEW API: Server handles estimated_minutes parameter."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["estimated_minutes"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            result = update_task("task-001", estimated_minutes=60)

            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["estimated_minutes"] == 60
            assert "Successfully updated task" in result

    # ========================================================================
    # Error Handling
    # ========================================================================

    def test_update_task_handles_client_error_dict(self):
        """NEW API: Server handles error dict from client."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": False,
                "task_id": "task-001",
                "updated_fields": [],
                "error": "Task not found"
            }
            mock_get_client.return_value = mock_client

            result = update_task("task-001", task_name="New Name")

            assert "Error" in result or "Failed" in result
            assert "task-001" in result

    def test_update_task_shows_updated_fields(self):
        """NEW API: Server response includes which fields were updated."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["task_name", "flagged", "due_date"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            result = update_task(
                "task-001",
                task_name="New",
                flagged=True,
                due_date="2025-12-31"
            )

            # Response should mention what was updated
            assert "task_name" in result or "3 fields" in result or "updated" in result.lower()

    # ========================================================================
    # Backward Compatibility (Legacy Parameters)
    # ========================================================================

    def test_update_task_accepts_legacy_name_parameter(self):
        """NEW API: Server still accepts legacy 'name' parameter for backward compat."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["task_name"],
                "error": None
            }
            mock_get_client.return_value = mock_client

            # Use legacy 'name' parameter
            result = update_task("task-001", name="Legacy Name")

            # Should still work
            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs.get("name") == "Legacy Name" or call_kwargs.get("task_name") == "Legacy Name"
            assert "Successfully updated task" in result
