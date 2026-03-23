"""Tests for redesigned server API (server_fastmcp.py layer).

This file tests the MCP server layer for the NEW API (v1.0.0 redesign).
Tests are written FIRST (TDD) before implementing server changes.
"""
import pytest
from unittest import mock

# Import server module
import omnifocus_mcp.server_fastmcp as server

# Extract tool functions (FastMCP @mcp.tool() returns the function directly)
update_task = server.update_task
update_tasks = server.update_tasks
TaskUpdate = server.TaskUpdate


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

class TestUpdateTasksServerRedesign:
    """Tests for update_tasks() MCP tool (batch operations via unified API).

    The unified update_tasks accepts list[TaskUpdate] and iterates over them,
    calling client.update_task for each item individually.
    """

    # ========================================================================
    # Batch with Uniform Values (replaces old update_tasks API)
    # ========================================================================

    def test_update_tasks_single_id_via_list(self):
        """Unified API: Single task update via list with one item."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["flagged"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tasks([{"id": "task-001", "flagged": True}])

            mock_client.update_task.assert_called_once()
            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["task_id"] == "task-001"
            assert call_kwargs["flagged"] is True
            assert "Successfully" in result

    def test_update_tasks_multiple_ids_same_value(self):
        """Unified API: Multiple tasks with same flagged value."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "any",
                "updated_fields": ["flagged"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tasks([
                {"id": "task-001", "flagged": True},
                {"id": "task-002", "flagged": True},
                {"id": "task-003", "flagged": True},
            ])

            assert mock_client.update_task.call_count == 3
            assert "3 of 3 tasks" in result

    def test_update_tasks_batch_with_flagged(self):
        """Unified API: Flagged parameter passed through for each task."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "any",
                "updated_fields": ["flagged"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tasks([
                {"id": "task-001", "flagged": True},
                {"id": "task-002", "flagged": True},
            ])

            for call in mock_client.update_task.call_args_list:
                assert call.kwargs["flagged"] is True
            assert "2 of 2 tasks" in result

    def test_update_tasks_batch_with_completed(self):
        """Unified API: Completed parameter for batch update."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "any",
                "updated_fields": ["completed"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tasks([
                {"id": "task-001", "completed": True},
                {"id": "task-002", "completed": True},
                {"id": "task-003", "completed": True},
            ])

            for call in mock_client.update_task.call_args_list:
                assert call.kwargs["completed"] is True
            assert "3 of 3 tasks" in result

    # ========================================================================
    # Return Format and Error Handling
    # ========================================================================

    def test_update_tasks_shows_success_count(self):
        """Unified API: Response includes success count for multiple tasks."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "any",
                "updated_fields": ["flagged"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tasks([
                {"id": f"task-{i:03d}", "flagged": True} for i in range(5)
            ])

            assert "5 of 5 tasks" in result

    def test_update_tasks_handles_partial_failures(self):
        """Unified API: Shows both successes and failures."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.side_effect = [
                {"success": True, "task_id": "task-001", "updated_fields": ["flagged"], "error": None},
                {"success": True, "task_id": "task-002", "updated_fields": ["flagged"], "error": None},
                {"success": False, "task_id": "task-invalid", "updated_fields": [], "error": "Task not found"},
            ]
            mock_get_client.return_value = mock_client

            result = update_tasks([
                {"id": "task-001", "flagged": True},
                {"id": "task-002", "flagged": True},
                {"id": "task-invalid", "flagged": True},
            ])

            assert "2 of 3 tasks" in result
            assert "FAILED" in result

    def test_update_tasks_handles_all_failures(self):
        """Unified API: Handles case where all tasks fail."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": False,
                "task_id": "any",
                "updated_fields": [],
                "error": "Task not found",
            }
            mock_get_client.return_value = mock_client

            result = update_tasks([
                {"id": "task-001", "flagged": True},
                {"id": "task-002", "flagged": True},
            ])

            assert "FAILED" in result
            assert "0 of 2 tasks" in result

    def test_update_task_handles_value_error(self):
        """Server: update_task() catches ValueError via update_tasks delegation."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.side_effect = ValueError("Empty task_id")
            mock_get_client.return_value = mock_client

            result = update_task(task_id="", flagged=True)
            assert isinstance(result, str)
            assert "error" in result.lower()

    def test_update_tasks_handles_value_error(self):
        """Server: update_tasks() catches ValueError and returns error string."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.side_effect = ValueError("Invalid task")
            mock_get_client.return_value = mock_client

            result = update_tasks([{"id": "task-001", "flagged": True}])
            assert isinstance(result, str)
            assert "error" in result.lower()


class TestUpdateTasksUnified:
    """Tests for unified update_tasks() with Pydantic TaskUpdate model (#492).

    The new update_tasks accepts list[TaskUpdate], where each item can have
    different fields. This replaces both update_task (single) and the old
    update_tasks (batch with uniform values).
    """

    # ========================================================================
    # TaskUpdate Model
    # ========================================================================

    def test_task_update_model_requires_id(self):
        """TaskUpdate model requires id field."""
        with pytest.raises(Exception):
            TaskUpdate(flagged=True)  # Missing id

    def test_task_update_model_defaults_to_none(self):
        """TaskUpdate model defaults all optional fields to None."""
        task = TaskUpdate(id="t1")
        assert task.id == "t1"
        assert task.task_name is None
        assert task.flagged is None
        assert task.due_date is None
        assert task.tags is None

    def test_task_update_model_dump_exclude_none(self):
        """model_dump(exclude_none=True) excludes unset fields but keeps False/0."""
        task = TaskUpdate(id="t1", flagged=False, estimated_minutes=0)
        dumped = task.model_dump(exclude_none=True, exclude={"id"})
        assert dumped == {"flagged": False, "estimated_minutes": 0}

    # ========================================================================
    # Single Task Update (via list with one item)
    # ========================================================================

    def test_update_tasks_single_item(self):
        """Unified update_tasks with single item delegates to client.update_task."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "t1",
                "updated_fields": ["flagged"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tasks([{"id": "t1", "flagged": True}])

            mock_client.update_task.assert_called_once()
            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["task_id"] == "t1"
            assert call_kwargs["flagged"] is True
            assert "Successfully updated task t1" in result
            assert "flagged" in result

    def test_update_tasks_single_item_no_changes(self):
        """Single item with no changes detected."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "t1",
                "updated_fields": [],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tasks([{"id": "t1", "flagged": True}])
            assert "no changes detected" in result

    def test_update_tasks_single_item_error(self):
        """Single item error returns error message."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": False,
                "task_id": "t1",
                "updated_fields": [],
                "error": "Task not found",
            }
            mock_get_client.return_value = mock_client

            result = update_tasks([{"id": "t1", "flagged": True}])
            assert "Error updating task t1" in result
            assert "Task not found" in result

    # ========================================================================
    # Multiple Tasks with Different Fields
    # ========================================================================

    def test_update_tasks_multiple_items_different_fields(self):
        """Multiple items, each with different fields."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.side_effect = [
                {
                    "success": True,
                    "task_id": "t1",
                    "updated_fields": ["flagged"],
                    "error": None,
                },
                {
                    "success": True,
                    "task_id": "t2",
                    "updated_fields": ["task_name", "due_date"],
                    "error": None,
                },
            ]
            mock_get_client.return_value = mock_client

            result = update_tasks([
                {"id": "t1", "flagged": True},
                {"id": "t2", "task_name": "Renamed", "due_date": "2026-04-01"},
            ])

            assert mock_client.update_task.call_count == 2
            # First call: flagged only
            call1 = mock_client.update_task.call_args_list[0].kwargs
            assert call1["task_id"] == "t1"
            assert call1["flagged"] is True
            assert "task_name" not in call1
            # Second call: task_name + due_date
            call2 = mock_client.update_task.call_args_list[1].kwargs
            assert call2["task_id"] == "t2"
            assert call2["task_name"] == "Renamed"
            assert call2["due_date"] == "2026-04-01"

            assert "Updated 2 of 2 tasks" in result

    def test_update_tasks_partial_failure(self):
        """One succeeds, one fails — summary includes both."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.side_effect = [
                {
                    "success": True,
                    "task_id": "t1",
                    "updated_fields": ["flagged"],
                    "error": None,
                },
                {
                    "success": False,
                    "task_id": "t2",
                    "updated_fields": [],
                    "error": "Task not found",
                },
            ]
            mock_get_client.return_value = mock_client

            result = update_tasks([
                {"id": "t1", "flagged": True},
                {"id": "t2", "flagged": True},
            ])

            assert "Updated 1 of 2 tasks" in result
            assert "t1" in result
            assert "FAILED" in result
            assert "Task not found" in result

    def test_update_tasks_with_exception(self):
        """Client raises exception for one task — caught and reported."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.side_effect = [
                {
                    "success": True,
                    "task_id": "t1",
                    "updated_fields": ["flagged"],
                    "error": None,
                },
                ValueError("Invalid task_id"),
            ]
            mock_get_client.return_value = mock_client

            result = update_tasks([
                {"id": "t1", "flagged": True},
                {"id": "t2", "completed": True},
            ])

            assert "Updated 1 of 2 tasks" in result
            assert "FAILED" in result
            assert "Invalid task_id" in result

    # ========================================================================
    # All Fields Passed Through
    # ========================================================================

    def test_update_tasks_with_all_fields(self):
        """Verify all TaskUpdate fields are passed through to client."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "t1",
                "updated_fields": ["task_name", "flagged"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tasks([{
                "id": "t1",
                "task_name": "New Name",
                "project_id": "proj-1",
                "parent_task_id": "parent-1",
                "note": "A note",
                "due_date": "2026-04-01",
                "defer_date": "2026-03-25",
                "planned_date": "2026-03-26",
                "flagged": True,
                "tags": ["work"],
                "add_tags": ["urgent"],
                "remove_tags": ["old"],
                "estimated_minutes": 30,
                "completed": False,
                "status": "active",
                "recurrence": "FREQ=WEEKLY",
                "repetition_method": "fixed",
                "sequential": True,
                "completed_by_children": True,
            }])

            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["task_id"] == "t1"
            assert call_kwargs["task_name"] == "New Name"
            assert call_kwargs["project_id"] == "proj-1"
            assert call_kwargs["parent_task_id"] == "parent-1"
            assert call_kwargs["note"] == "A note"
            assert call_kwargs["due_date"] == "2026-04-01"
            assert call_kwargs["defer_date"] == "2026-03-25"
            assert call_kwargs["planned_date"] == "2026-03-26"
            assert call_kwargs["flagged"] is True
            assert call_kwargs["tags"] == ["work"]
            assert call_kwargs["add_tags"] == ["urgent"]
            assert call_kwargs["remove_tags"] == ["old"]
            assert call_kwargs["estimated_minutes"] == 30
            assert call_kwargs["completed"] is False
            assert call_kwargs["status"] == "active"
            assert call_kwargs["recurrence"] == "FREQ=WEEKLY"
            assert call_kwargs["repetition_method"] == "fixed"
            assert call_kwargs["sequential"] is True
            assert call_kwargs["completed_by_children"] is True

    def test_update_tasks_excludes_none_fields(self):
        """Fields not set by user (None) should not be passed to client."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "t1",
                "updated_fields": ["flagged"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tasks([{"id": "t1", "flagged": True}])

            call_kwargs = mock_client.update_task.call_args.kwargs
            # Only task_id and flagged should be present
            assert set(call_kwargs.keys()) == {"task_id", "flagged"}

    def test_update_tasks_keeps_false_and_zero(self):
        """False and 0 values should be passed through (not treated as None)."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "t1",
                "updated_fields": ["flagged", "estimated_minutes"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tasks([{"id": "t1", "flagged": False, "estimated_minutes": 0}])

            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["flagged"] is False
            assert call_kwargs["estimated_minutes"] == 0

    # ========================================================================
    # Invalid Input
    # ========================================================================

    def test_update_tasks_invalid_input(self):
        """Invalid dict (missing id) returns error."""
        result = update_tasks([{"flagged": True}])
        assert "Error" in result

    def test_update_tasks_with_pydantic_objects(self):
        """TaskUpdate objects (not just dicts) are accepted."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "t1",
                "updated_fields": ["flagged"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            task = TaskUpdate(id="t1", flagged=True)
            result = update_tasks([task])

            mock_client.update_task.assert_called_once()
            assert "Successfully updated task t1" in result

    # ========================================================================
    # update_task delegates to update_tasks
    # ========================================================================

    def test_update_task_delegates_to_update_tasks(self):
        """update_task (single) delegates to the new update_tasks."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_task.return_value = {
                "success": True,
                "task_id": "task-001",
                "updated_fields": ["flagged"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_task("task-001", flagged=True)

            mock_client.update_task.assert_called_once()
            call_kwargs = mock_client.update_task.call_args.kwargs
            assert call_kwargs["task_id"] == "task-001"
            assert call_kwargs["flagged"] is True
            assert "Successfully updated task task-001" in result
