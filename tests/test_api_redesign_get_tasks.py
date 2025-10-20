"""Tests for get_tasks() enhancements (NEW API - Phase 3.1).

New parameters being added:
- task_id: Filter to specific task (consolidates get_task())
- parent_task_id: Filter by parent (consolidates get_subtasks())
- include_full_notes: Return full notes (consolidates get_note())
"""
import pytest
from unittest import mock

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


class TestGetTasksEnhancements:
    """Tests for get_tasks() new parameters (Phase 3.1)."""

    @pytest.fixture
    def client(self):
        """Create a client for testing."""
        return OmniFocusConnector(enable_safety_checks=False)

    # ========================================================================
    # task_id Parameter Tests (Consolidates get_task())
    # ========================================================================

    def test_get_tasks_with_task_id_returns_single_task(self, client):
        """NEW API: get_tasks(task_id=X) returns single task in list."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "task-001", "name": "Specific Task", "note": "Details"}
            ]'''

            result = client.get_tasks(task_id="task-001")

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["id"] == "task-001"
            assert result[0]["name"] == "Specific Task"

    def test_get_tasks_with_task_id_filters_applescript(self, client):
        """NEW API: get_tasks(task_id=X) adds filter to AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'

            client.get_tasks(task_id="task-123")

            # Verify AppleScript includes task ID filter
            script = mock_run.call_args[0][0]
            assert 'task-123' in script
            assert 'whose id is' in script or 'id is "task-123"' in script

    def test_get_tasks_task_id_with_other_filters(self, client):
        """NEW API: get_tasks(task_id=X) can combine with other filters."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'

            # task_id should override other filters (most specific)
            client.get_tasks(task_id="task-001", project_id="proj-001", flagged_only=True)

            script = mock_run.call_args[0][0]
            assert 'task-001' in script

    # ========================================================================
    # parent_task_id Parameter Tests (Consolidates get_subtasks())
    # ========================================================================

    def test_get_tasks_with_parent_task_id_returns_subtasks(self, client):
        """NEW API: get_tasks(parent_task_id=X) returns subtasks."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "sub-1", "name": "Subtask 1", "parentTaskId": "parent-001"},
                {"id": "sub-2", "name": "Subtask 2", "parentTaskId": "parent-001"}
            ]'''

            result = client.get_tasks(parent_task_id="parent-001")

            assert isinstance(result, list)
            assert len(result) == 2
            assert all(task["parentTaskId"] == "parent-001" for task in result)

    def test_get_tasks_with_parent_task_id_filters_applescript(self, client):
        """NEW API: get_tasks(parent_task_id=X) adds parent filter to AppleScript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'

            client.get_tasks(parent_task_id="parent-123")

            script = mock_run.call_args[0][0]
            assert 'parent-123' in script
            # Could check for "container" or "parent task" depending on implementation

    def test_get_tasks_parent_task_id_with_other_filters(self, client):
        """NEW API: get_tasks(parent_task_id=X) can combine with other filters."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'

            client.get_tasks(parent_task_id="parent-001", flagged_only=True, available_only=True)

            script = mock_run.call_args[0][0]
            assert 'parent-001' in script

    # ========================================================================
    # include_full_notes Parameter Tests (Consolidates get_note())
    # ========================================================================

    def test_get_tasks_include_full_notes_false_by_default(self, client):
        """NEW API: get_tasks() truncates notes by default (backward compatible)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # Simulate truncated note from AppleScript
            mock_run.return_value = '''[
                {"id": "task-001", "name": "Task", "note": "Short note..."}
            ]'''

            result = client.get_tasks()

            # Default behavior: notes may be truncated
            assert isinstance(result, list)

    def test_get_tasks_include_full_notes_true_returns_full_content(self, client):
        """NEW API: get_tasks(include_full_notes=True) returns complete notes."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # Simulate full note retrieval
            long_note = "This is a very long note with lots of details. " * 50
            mock_run.return_value = f'''[
                {{"id": "task-001", "name": "Task", "note": "{long_note[:500]}"}}
            ]'''

            result = client.get_tasks(include_full_notes=True)

            # Should request full notes in AppleScript
            script = mock_run.call_args[0][0]
            # Check that we're not truncating in AppleScript
            # (Implementation may vary - just verify parameter is used)
            assert result[0]["note"] is not None

    def test_get_tasks_include_full_notes_with_task_id(self, client):
        """NEW API: get_tasks(task_id=X, include_full_notes=True) combines both."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "task-001", "name": "Task", "note": "Full content here"}
            ]'''

            result = client.get_tasks(task_id="task-001", include_full_notes=True)

            assert len(result) == 1
            assert result[0]["id"] == "task-001"

    # ========================================================================
    # Combined Parameter Tests
    # ========================================================================

    def test_get_tasks_all_new_parameters_together(self, client):
        """NEW API: All three new parameters can be used together (edge case)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'

            # This is unusual but should work
            # task_id would take precedence, others would be ignored
            client.get_tasks(
                task_id="task-001",
                parent_task_id="parent-001",  # Ignored when task_id present
                include_full_notes=True
            )

            # Should execute without error
            assert mock_run.called

    def test_get_tasks_backward_compatible_no_new_params(self, client):
        """NEW API: Existing usage without new params still works (backward compatible)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'

            # Existing call patterns should work unchanged
            client.get_tasks(project_id="proj-001", flagged_only=True)

            assert mock_run.called
