"""Tests for redesigned API update functions (update_task, update_tasks, update_project, update_projects).

This file tests the NEW API (v1.0.0 redesign) following the architecture principles
documented in docs/ARCHITECTURE.md and docs/API_REFERENCE.md.
"""
import json
import subprocess
from unittest import mock
import pytest

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector, TaskStatus, ProjectStatus


class TestUpdateTaskRedesign:
    """Tests for enhanced update_task() function (NEW API).

    The redesigned update_task() consolidates multiple specialized functions:
    - complete_task() -> update_task(task_id, completed=True)
    - drop_task() -> update_task(task_id, status=TaskStatus.DROPPED)
    - move_task() -> update_task(task_id, project_id=X)
    - set_parent_task() -> update_task(task_id, parent_task_id=X)
    - set_estimated_minutes() -> update_task(task_id, estimated_minutes=X)
    - add_tag_to_task() -> update_task(task_id, add_tags=[...])
    """

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusConnector(enable_safety_checks=False)

    # ========================================================================
    # Core Functionality Tests
    # ========================================================================

    def test_update_task_single_field_task_name(self, client):
        """NEW API: update_task() can update just the task name."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                task_name="Updated Task Name"
            )

            assert result["success"] is True
            assert result["task_id"] == "task-123"
            assert "task_name" in result["updated_fields"]
            mock_run.assert_called_once()

    def test_update_task_multiple_fields_at_once(self, client):
        """NEW API: update_task() can update multiple fields in a single call."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                task_name="Updated Name",
                due_date="2025-12-31",
                flagged=True,
                estimated_minutes=60
            )

            assert result["success"] is True
            assert result["task_id"] == "task-123"
            assert "task_name" in result["updated_fields"]
            assert "due_date" in result["updated_fields"]
            assert "flagged" in result["updated_fields"]
            assert "estimated_minutes" in result["updated_fields"]

    def test_update_task_move_to_project(self, client):
        """NEW API: update_task() can move task to different project (replaces move_task)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                project_id="proj-456"
            )

            assert result["success"] is True
            assert "project_id" in result["updated_fields"]

    def test_update_task_make_subtask(self, client):
        """NEW API: update_task() can make task a subtask (replaces set_parent_task)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                parent_task_id="task-parent"
            )

            assert result["success"] is True
            assert "parent_task_id" in result["updated_fields"]

    def test_update_task_set_completion(self, client):
        """NEW API: update_task() can mark task complete (replaces complete_task)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                completed=True
            )

            assert result["success"] is True
            assert "completed" in result["updated_fields"]

    def test_update_task_set_status_enum(self, client):
        """NEW API: update_task() can set status using enum (replaces drop_task)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                status=TaskStatus.DROPPED
            )

            assert result["success"] is True
            assert "status" in result["updated_fields"]

    def test_update_task_set_status_string(self, client):
        """NEW API: update_task() accepts status as string (flexible MCP client support)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                status="dropped"
            )

            assert result["success"] is True
            assert "status" in result["updated_fields"]

    def test_update_task_add_tags(self, client):
        """NEW API: update_task() can add tags incrementally (replaces add_tag_to_task)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                add_tags=["urgent", "work"]
            )

            assert result["success"] is True
            assert "add_tags" in result["updated_fields"]

    def test_update_task_remove_tags(self, client):
        """NEW API: update_task() can remove tags incrementally."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                remove_tags=["old-tag"]
            )

            assert result["success"] is True
            assert "remove_tags" in result["updated_fields"]

    def test_update_task_replace_tags(self, client):
        """NEW API: update_task() can replace all tags at once."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                tags=["tag1", "tag2", "tag3"]
            )

            assert result["success"] is True
            assert "tags" in result["updated_fields"]

    def test_update_task_estimated_minutes(self, client):
        """NEW API: update_task() can set estimated time (replaces set_estimated_minutes)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                estimated_minutes=120
            )

            assert result["success"] is True
            assert "estimated_minutes" in result["updated_fields"]

    def test_update_task_clear_due_date(self, client):
        """NEW API: update_task() can clear dates by passing empty string."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                due_date=""
            )

            assert result["success"] is True
            assert "due_date" in result["updated_fields"]

    def test_update_task_clear_defer_date(self, client):
        """NEW API: update_task() can clear defer date."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                defer_date=""
            )

            assert result["success"] is True
            assert "defer_date" in result["updated_fields"]

    # ========================================================================
    # Conflict Resolution Tests
    # ========================================================================

    def test_update_task_rejects_both_project_and_parent(self, client):
        """NEW API: update_task() raises ValueError when both project_id and parent_task_id provided."""
        with pytest.raises(ValueError) as exc_info:
            client.update_task(
                task_id="task-123",
                project_id="proj-456",
                parent_task_id="task-parent"
            )

        assert "Cannot specify both parent_task_id and project_id" in str(exc_info.value)

    def test_update_task_rejects_tags_with_add_tags(self, client):
        """NEW API: update_task() raises ValueError when both tags and add_tags provided."""
        with pytest.raises(ValueError) as exc_info:
            client.update_task(
                task_id="task-123",
                tags=["tag1", "tag2"],
                add_tags=["tag3"]
            )

        assert "Cannot specify both tags and add_tags" in str(exc_info.value)

    def test_update_task_rejects_tags_with_remove_tags(self, client):
        """NEW API: update_task() raises ValueError when both tags and remove_tags provided."""
        with pytest.raises(ValueError) as exc_info:
            client.update_task(
                task_id="task-123",
                tags=["tag1", "tag2"],
                remove_tags=["tag3"]
            )

        assert "Cannot specify both tags and remove_tags" in str(exc_info.value)

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    def test_update_task_returns_error_dict_on_not_found(self, client):
        """NEW API: update_task() returns error dict (not exception) when task not found."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, 'osascript', stderr="Task not found"
            )

            result = client.update_task(
                task_id="nonexistent",
                task_name="New Name"
            )

            assert result["success"] is False
            assert result["task_id"] == "nonexistent"
            assert "error" in result
            assert "Task not found" in result["error"] or "Error" in result["error"]

    def test_update_task_requires_at_least_one_field(self, client):
        """NEW API: update_task() raises ValueError when no fields provided."""
        with pytest.raises(ValueError) as exc_info:
            client.update_task(task_id="task-123")

        assert "At least one field must be provided" in str(exc_info.value)

    def test_update_task_requires_task_id(self, client):
        """NEW API: update_task() raises ValueError when task_id is empty."""
        with pytest.raises(ValueError) as exc_info:
            client.update_task(task_id="", task_name="New Name")

        assert "task_id is required" in str(exc_info.value)

    # ========================================================================
    # Return Format Tests
    # ========================================================================

    def test_update_task_returns_structured_dict(self, client):
        """NEW API: update_task() returns dict, not bool."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                task_name="New Name"
            )

            assert isinstance(result, dict)
            assert "success" in result
            assert "task_id" in result
            assert "updated_fields" in result

    def test_update_task_includes_updated_fields_list(self, client):
        """NEW API: update_task() includes list of fields that were updated."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                task_name="New Name",
                flagged=True
            )

            assert isinstance(result["updated_fields"], list)
            assert len(result["updated_fields"]) == 2
            assert "task_name" in result["updated_fields"]
            assert "flagged" in result["updated_fields"]

    def test_update_task_success_has_no_error_key(self, client):
        """NEW API: Successful update_task() returns dict with no error key."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_task(
                task_id="task-123",
                task_name="New Name"
            )

            assert result["success"] is True
            assert result.get("error") is None

    def test_update_task_failure_has_error_key(self, client):
        """NEW API: Failed update_task() returns dict with error key."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(
                1, 'osascript', stderr="Something went wrong"
            )

            result = client.update_task(
                task_id="task-123",
                task_name="New Name"
            )

            assert result["success"] is False
            assert "error" in result
            assert isinstance(result["error"], str)


class TestUpdateTasksRedesign:
    """Tests for update_tasks() batch function (NEW API).

    Key differences from update_task():
    - Accepts Union[str, list[str]] for task_ids
    - EXCLUDES task_name and note (require unique values)
    - Returns dict with counts (updated_count, failed_count, etc.)
    - Continues processing on individual failures
    """

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusConnector(enable_safety_checks=False)

    # ========================================================================
    # Union Type Handling (Single vs Multiple IDs)
    # ========================================================================

    def test_update_tasks_accepts_single_id_string(self, client):
        """NEW API: update_tasks() accepts single ID as string (Union type)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"  # update_task expects "true"

            result = client.update_tasks("task-001", flagged=True)

            assert result["updated_count"] == 1
            assert result["failed_count"] == 0
            assert "task-001" in result["updated_ids"]

    def test_update_tasks_accepts_list_of_ids(self, client):
        """NEW API: update_tasks() accepts list of IDs."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"  # update_task expects "true"

            result = client.update_tasks(
                ["task-001", "task-002", "task-003"],
                flagged=True
            )

            assert result["updated_count"] == 3
            assert result["failed_count"] == 0
            assert len(result["updated_ids"]) == 3

    # ========================================================================
    # Field Exclusions (task_name, note NOT allowed)
    # ========================================================================

    def test_update_tasks_rejects_task_name_parameter(self, client):
        """NEW API: update_tasks() raises ValueError if task_name provided."""
        with pytest.raises(ValueError) as exc_info:
            client.update_tasks(["task-001"], task_name="New Name")

        assert "task_name" in str(exc_info.value).lower()
        assert "unique" in str(exc_info.value).lower() or "not allowed" in str(exc_info.value).lower()

    def test_update_tasks_rejects_note_parameter(self, client):
        """NEW API: update_tasks() raises ValueError if note provided."""
        with pytest.raises(ValueError) as exc_info:
            client.update_tasks(["task-001"], note="New note")

        assert "note" in str(exc_info.value).lower()
        assert "unique" in str(exc_info.value).lower() or "not allowed" in str(exc_info.value).lower()

    # ========================================================================
    # Batch Operations (All Fields)
    # ========================================================================

    def test_update_tasks_with_flagged(self, client):
        """NEW API: update_tasks() can set flagged on multiple tasks."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"  # update_task expects "true"

            result = client.update_tasks(["task-001", "task-002"], flagged=True)

            assert result["updated_count"] == 2
            assert result["failed_count"] == 0

    def test_update_tasks_with_completed(self, client):
        """NEW API: update_tasks() can mark multiple tasks complete."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"  # update_task expects "true"

            result = client.update_tasks(
                ["task-001", "task-002", "task-003"],
                completed=True
            )

            assert result["updated_count"] == 3

    def test_update_tasks_with_status(self, client):
        """NEW API: update_tasks() can set status on multiple tasks."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"  # update_task expects "true"

            result = client.update_tasks(
                ["task-001", "task-002"],
                status=TaskStatus.DROPPED
            )

            assert result["updated_count"] == 2

    def test_update_tasks_with_project_id(self, client):
        """NEW API: update_tasks() can move multiple tasks to project."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"  # update_task expects "true"

            result = client.update_tasks(
                ["task-001", "task-002"],
                project_id="proj-456"
            )

            assert result["updated_count"] == 2

    def test_update_tasks_with_add_tags(self, client):
        """NEW API: update_tasks() can add tags to multiple tasks."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"  # update_task expects "true"

            result = client.update_tasks(
                ["task-001", "task-002"],
                add_tags=["urgent", "work"]
            )

            assert result["updated_count"] == 2

    def test_update_tasks_with_estimated_minutes(self, client):
        """NEW API: update_tasks() can set estimated time on multiple tasks."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"  # update_task expects "true"

            result = client.update_tasks(
                ["task-001", "task-002", "task-003"],
                estimated_minutes=60
            )

            assert result["updated_count"] == 3

    # ========================================================================
    # Conflict Validation
    # ========================================================================

    def test_update_tasks_rejects_project_id_and_parent_task_id(self, client):
        """NEW API: update_tasks() raises ValueError if both project_id and parent_task_id."""
        with pytest.raises(ValueError) as exc_info:
            client.update_tasks(
                ["task-001"],
                project_id="proj-456",
                parent_task_id="task-parent"
            )

        assert "project_id" in str(exc_info.value).lower()
        assert "parent_task_id" in str(exc_info.value).lower()

    def test_update_tasks_rejects_tags_and_add_tags(self, client):
        """NEW API: update_tasks() raises ValueError if both tags and add_tags."""
        with pytest.raises(ValueError) as exc_info:
            client.update_tasks(
                ["task-001"],
                tags=["tag1"],
                add_tags=["tag2"]
            )

        assert "tags" in str(exc_info.value).lower()
        assert "add_tags" in str(exc_info.value).lower()

    # ========================================================================
    # Return Format
    # ========================================================================

    def test_update_tasks_returns_dict_with_counts(self, client):
        """NEW API: update_tasks() returns dict with success/failure counts."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"  # update_task expects "true"

            result = client.update_tasks(["task-001", "task-002"], flagged=True)

            assert isinstance(result, dict)
            assert "updated_count" in result
            assert "failed_count" in result
            assert "updated_ids" in result
            assert "failures" in result

    def test_update_tasks_includes_updated_ids_list(self, client):
        """NEW API: update_tasks() includes list of successfully updated IDs."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"  # update_task expects "true"

            result = client.update_tasks(["task-001", "task-002"], flagged=True)

            assert isinstance(result["updated_ids"], list)
            assert len(result["updated_ids"]) == 2

    # ========================================================================
    # Partial Failures
    # ========================================================================

    def test_update_tasks_continues_on_partial_failures(self, client):
        """NEW API: update_tasks() continues processing when individual tasks fail."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # Simulate 2 successes and 1 failure
            def side_effect(*args):
                script = args[0]
                if "task-invalid" in script:
                    raise subprocess.CalledProcessError(1, "osascript", stderr="Task not found")
                return "true"

            mock_run.side_effect = side_effect

            result = client.update_tasks(
                ["task-001", "task-002", "task-invalid"],
                flagged=True
            )

            assert result["updated_count"] == 2
            assert result["failed_count"] == 1
            assert len(result["failures"]) == 1
            assert result["failures"][0]["task_id"] == "task-invalid"

    # ========================================================================
    # Validation
    # ========================================================================

    def test_update_tasks_requires_task_ids(self, client):
        """NEW API: update_tasks() raises ValueError if task_ids empty."""
        with pytest.raises(ValueError) as exc_info:
            client.update_tasks([], flagged=True)

        assert "task_ids" in str(exc_info.value).lower()

    def test_update_tasks_requires_at_least_one_field(self, client):
        """NEW API: update_tasks() raises ValueError if no fields provided."""
        with pytest.raises(ValueError) as exc_info:
            client.update_tasks(["task-001"])

        assert "at least one field" in str(exc_info.value).lower()
