"""Tests for redesigned API delete functions (delete_tasks, delete_projects).

This file tests the NEW API (v1.0.0 redesign) following the architecture principles
documented in docs/ARCHITECTURE.md and docs/API_REFERENCE.md.
"""
import subprocess
from unittest import mock
import pytest

from omnifocus_mcp.omnifocus_client import OmniFocusClient


@pytest.fixture
def client():
    """Create a test client with safety checks disabled."""
    return OmniFocusClient(enable_safety_checks=False)


class TestDeleteTasksRedesign:
    """Tests for enhanced delete_tasks() function (NEW API).

    Key enhancements:
    - Accepts Union[str, list[str]] for task_ids (single or multiple)
    - Returns dict instead of int (consistency with new API)
    - Return format: {"deleted_count": int, "failed_count": int, "deleted_ids": list, "failures": list}
    """

    # ========================================================================
    # Union Type Handling (Single vs Multiple IDs)
    # ========================================================================

    def test_delete_tasks_accepts_single_id_string(self, client):
        """NEW API: delete_tasks() accepts single ID as string (Union type)."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "1"  # 1 task deleted

            result = client.delete_tasks("task-001")

            assert result["deleted_count"] == 1
            assert result["failed_count"] == 0
            assert "task-001" in result["deleted_ids"]

    def test_delete_tasks_accepts_list_of_ids(self, client):
        """NEW API: delete_tasks() accepts list of IDs."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "3"  # 3 tasks deleted

            result = client.delete_tasks(["task-001", "task-002", "task-003"])

            assert result["deleted_count"] == 3
            assert result["failed_count"] == 0
            assert len(result["deleted_ids"]) == 3

    # ========================================================================
    # Return Format (Dict instead of int)
    # ========================================================================

    def test_delete_tasks_returns_dict_with_counts(self, client):
        """NEW API: delete_tasks() returns dict instead of int."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "2"

            result = client.delete_tasks(["task-001", "task-002"])

            assert isinstance(result, dict)
            assert "deleted_count" in result
            assert "failed_count" in result
            assert "deleted_ids" in result
            assert "failures" in result

    def test_delete_tasks_includes_deleted_ids_list(self, client):
        """NEW API: delete_tasks() includes list of successfully deleted IDs."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "2"

            result = client.delete_tasks(["task-001", "task-002"])

            assert isinstance(result["deleted_ids"], list)
            assert len(result["deleted_ids"]) == 2
            assert "task-001" in result["deleted_ids"]
            assert "task-002" in result["deleted_ids"]

    # ========================================================================
    # Partial Failures
    # ========================================================================

    def test_delete_tasks_handles_partial_failures(self, client):
        """NEW API: delete_tasks() continues processing when individual tasks fail."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # Simulate 2 out of 3 deleted (1 not found)
            mock_run.return_value = "2"

            result = client.delete_tasks(
                ["task-001", "task-002", "task-invalid"]
            )

            assert result["deleted_count"] == 2
            assert result["failed_count"] == 1
            assert len(result["deleted_ids"]) == 2

    def test_delete_tasks_handles_all_failures(self, client):
        """NEW API: delete_tasks() handles case where all tasks fail to delete."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # Simulate 0 deleted (all not found)
            mock_run.return_value = "0"

            result = client.delete_tasks(["task-invalid-1", "task-invalid-2"])

            assert result["deleted_count"] == 0
            assert result["failed_count"] == 2
            assert len(result["deleted_ids"]) == 0

    # ========================================================================
    # Validation
    # ========================================================================

    def test_delete_tasks_requires_task_ids(self, client):
        """NEW API: delete_tasks() raises ValueError if task_ids empty."""
        with pytest.raises(ValueError) as exc_info:
            client.delete_tasks([])

        assert "task_ids" in str(exc_info.value).lower() or "empty" in str(exc_info.value).lower()

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_delete_tasks_with_single_id_in_list(self, client):
        """NEW API: delete_tasks() handles single-item list correctly."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "1"

            result = client.delete_tasks(["task-001"])

            assert result["deleted_count"] == 1
            assert len(result["deleted_ids"]) == 1
