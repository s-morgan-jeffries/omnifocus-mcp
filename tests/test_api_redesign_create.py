"""Tests for redesigned API create functions (create_task, create_project).

This file tests the NEW API (v1.0.0 redesign) following the architecture principles
documented in docs/ARCHITECTURE.md and docs/API_REFERENCE.md.
"""
from unittest import mock
import pytest

from omnifocus_mcp.omnifocus_client import OmniFocusClient


@pytest.fixture
def client():
    """Create a test client with safety checks disabled."""
    return OmniFocusClient(enable_safety_checks=False)


class TestCreateTaskRedesign:
    """Tests for create_task() function (NEW API - renamed from add_task).

    Key changes:
    - Renamed from add_task() to create_task()
    - project_id is now Optional (None = inbox)
    - Consolidates create_inbox_task() functionality
    - Added parent_task_id parameter
    - Added estimated_minutes parameter
    - Conflict validation: project_id + parent_task_id raises ValueError
    """

    # ========================================================================
    # Basic Creation (Project vs Inbox)
    # ========================================================================

    def test_create_task_in_project(self, client):
        """NEW API: create_task() creates task in specified project."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "task-001"

            result = client.create_task(
                task_name="Test Task",
                project_id="proj-123"
            )

            assert result == "task-001"
            # Verify AppleScript was called with project
            script = mock_run.call_args[0][0]
            assert "proj-123" in script

    def test_create_task_in_inbox(self, client):
        """NEW API: create_task() with project_id=None creates in inbox."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "task-002"

            result = client.create_task(
                task_name="Inbox Task",
                project_id=None
            )

            assert result == "task-002"
            # Verify AppleScript uses inbox
            script = mock_run.call_args[0][0]
            assert "inbox" in script.lower()

    def test_create_task_defaults_to_inbox(self, client):
        """NEW API: create_task() without project_id defaults to inbox."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "task-003"

            result = client.create_task(task_name="Default Inbox Task")

            assert result == "task-003"
            script = mock_run.call_args[0][0]
            assert "inbox" in script.lower()

    # ========================================================================
    # Hierarchy (parent_task_id)
    # ========================================================================

    def test_create_task_with_parent_task_id(self, client):
        """NEW API: create_task() can create subtask with parent_task_id."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "task-004"

            result = client.create_task(
                task_name="Subtask",
                parent_task_id="task-parent"
            )

            assert result == "task-004"
            script = mock_run.call_args[0][0]
            assert "task-parent" in script

    def test_create_task_rejects_project_id_and_parent_task_id(self, client):
        """NEW API: create_task() raises ValueError if both project_id and parent_task_id."""
        with pytest.raises(ValueError) as exc_info:
            client.create_task(
                task_name="Conflicting Task",
                project_id="proj-123",
                parent_task_id="task-parent"
            )

        assert "project_id" in str(exc_info.value).lower()
        assert "parent_task_id" in str(exc_info.value).lower()

    # ========================================================================
    # Optional Fields
    # ========================================================================

    def test_create_task_with_all_optional_fields(self, client):
        """NEW API: create_task() supports all optional fields."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "task-005"

            result = client.create_task(
                task_name="Full Task",
                project_id="proj-123",
                note="Task note",
                due_date="2025-12-31",
                defer_date="2025-12-01",
                flagged=True,
                tags=["urgent", "work"],
                estimated_minutes=60
            )

            assert result == "task-005"
            script = mock_run.call_args[0][0]
            assert "Full Task" in script
            assert "flagged:true" in script

    def test_create_task_with_estimated_minutes(self, client):
        """NEW API: create_task() supports estimated_minutes parameter."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "task-006"

            result = client.create_task(
                task_name="Timed Task",
                estimated_minutes=30
            )

            assert result == "task-006"
            script = mock_run.call_args[0][0]
            assert "estimated minutes" in script.lower()

    # ========================================================================
    # Return Format
    # ========================================================================

    def test_create_task_returns_task_id(self, client):
        """NEW API: create_task() returns task ID string."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "task-new-id"

            result = client.create_task(task_name="New Task")

            assert isinstance(result, str)
            assert result == "task-new-id"

    # ========================================================================
    # Required Parameters
    # ========================================================================

    def test_create_task_requires_task_name(self, client):
        """NEW API: create_task() requires task_name parameter."""
        # This will be caught by Python's type system at call time
        # Just verify the parameter is required in signature
        import inspect
        sig = inspect.signature(client.create_task)
        task_name_param = sig.parameters['task_name']
        assert task_name_param.default == inspect.Parameter.empty  # No default = required
