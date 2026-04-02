"""Tests for server_fastmcp.py coverage gaps.

Covers format helpers, error handlers, and batch response formatting
that were previously untested.
"""
from unittest import mock

import pytest

import omnifocus_mcp.server_fastmcp as server
from omnifocus_mcp.server_fastmcp import _format_task, _format_project


# ============================================================================
# Category A: Format helpers
# ============================================================================


class TestFormatTaskBranches:
    """Cover optional field branches in _format_task()."""

    def _task(self, **overrides):
        base = {"id": "t1", "name": "T", "completed": False}
        base.update(overrides)
        return base

    def test_planned_date(self):
        """Planned date field included in formatted output."""
        result = _format_task(self._task(plannedDate="2026-03-20"))
        assert "Planned: 2026-03-20" in result

    def test_next_due_date(self):
        """Next due date field included in formatted output."""
        result = _format_task(self._task(nextDueDate="2026-04-01"))
        assert "Next Due: 2026-04-01" in result

    def test_next_defer_date(self):
        """Next defer date field included in formatted output."""
        result = _format_task(self._task(nextDeferDate="2026-04-02"))
        assert "Next Defer: 2026-04-02" in result

    def test_next_planned_date(self):
        """Next planned date field included in formatted output."""
        result = _format_task(self._task(nextPlannedDate="2026-04-03"))
        assert "Next Planned: 2026-04-03" in result

    def test_repeat_summary(self):
        """Repeat summary field included in formatted output."""
        result = _format_task(self._task(repeatSummary="Every week"))
        assert "Repeats: Every week" in result

    def test_is_recurring_without_repeat_summary(self):
        """Recurring task falls back to recurrence rule when no repeat summary."""
        result = _format_task(self._task(isRecurring=True, recurrence="FREQ=WEEKLY"))
        assert "Repeats: FREQ=WEEKLY" in result

    def test_is_recurring_without_repeat_summary_or_recurrence(self):
        """Recurring task shows generic yes when no summary or recurrence rule."""
        result = _format_task(self._task(isRecurring=True))
        assert "Repeats: Yes" in result

    def test_catch_up_automatically(self):
        """Catch up automatically true branch included in formatted output."""
        result = _format_task(self._task(catchUpAutomatically=True))
        assert "Catch Up Automatically: True" in result

    def test_catch_up_automatically_false(self):
        """Catch up automatically false branch included in formatted output."""
        result = _format_task(self._task(catchUpAutomatically=False))
        assert "Catch Up Automatically: False" in result


class TestFormatProjectBranches:
    """Cover optional field branches in _format_project()."""

    def _base_project(self, **overrides):
        proj = {"id": "p1", "name": "P", "status": "active"}
        proj.update(overrides)
        return proj

    def test_dropped_date(self):
        """Dropped date field included in formatted project output."""
        result = _format_project(self._base_project(droppedDate="2026-01-15"))
        assert "Dropped Date: 2026-01-15" in result

    def test_health_appropriately_scheduled(self):
        """Health shows appropriately scheduled when all tasks are deferred."""
        proj = self._base_project(
            remainingCount=2,
            availableCount=0,
            overdueCount=0,
            deferredCount=2,
            hasDeferredOnly=True,
        )
        result = _format_project(proj)
        assert "Health: Appropriately Scheduled" in result

    def test_health_no_remaining_tasks(self):
        """Health shows no remaining tasks when all counts are zero."""
        proj = self._base_project(
            remainingCount=0,
            availableCount=0,
            overdueCount=0,
            deferredCount=0,
        )
        result = _format_project(proj)
        assert "Health: No Remaining Tasks" in result

    def test_health_stuck(self):
        """Health shows stuck when remaining tasks exist but none are available or deferred."""
        proj = self._base_project(
            remainingCount=3,
            availableCount=0,
            overdueCount=0,
            deferredCount=0,
        )
        result = _format_project(proj)
        assert "Health: Stuck" in result

    def test_stalled(self):
        """Stalled status shown when project is stalled."""
        proj = self._base_project(
            remainingCount=1,
            availableCount=1,
            overdueCount=0,
            deferredCount=0,
            stalled=True,
        )
        result = _format_project(proj)
        assert "Stalled: Yes" in result


# ============================================================================
# Category B: Error handlers and empty results
# ============================================================================


class TestGetProjectsEdgeCases:
    """Cover empty/query branches in get_projects()."""

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_query_no_results(self, mock_gc):
        """Empty result message returned when project query matches nothing."""
        mock_gc.return_value.get_projects.return_value = []
        result = server.get_projects(query="nonexistent")
        assert "No active projects found matching 'nonexistent'" in result
        mock_gc.return_value.get_projects.assert_called_once()
        call_kwargs = mock_gc.return_value.get_projects.call_args[1]
        assert call_kwargs["query"] == "nonexistent"

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_query_with_results(self, mock_gc):
        """Result count and query shown in header when projects match."""
        mock_gc.return_value.get_projects.return_value = [
            {"id": "p1", "name": "Match", "status": "active"},
        ]
        result = server.get_projects(query="Match")
        assert "Found 1 active projects matching 'Match':" in result
        mock_gc.return_value.get_projects.assert_called_once()
        call_kwargs = mock_gc.return_value.get_projects.call_args[1]
        assert call_kwargs["query"] == "Match"


    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_planned_on_expands_to_range(self, mock_gc):
        """Planned on date expands to planned_after and planned_before range."""
        mock_gc.return_value.get_projects.return_value = []
        server.get_projects(planned_on="2026-03-23")
        call_kwargs = mock_gc.return_value.get_projects.call_args[1]
        assert call_kwargs["planned_after"] == "2026-03-23"
        assert call_kwargs["planned_before"] == "2026-03-24"

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_planned_on_conflicts_with_planned_after(self, mock_gc):
        """Error returned when planned_on used with planned_after."""
        result = server.get_projects(planned_on="2026-03-23", planned_after="2026-03-20")
        assert "Error" in result
        assert "mutually exclusive" in result

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_planned_after_passed_to_client(self, mock_gc):
        """Planned after and before parameters forwarded to client."""
        mock_gc.return_value.get_projects.return_value = []
        server.get_projects(planned_after="2026-03-20", planned_before="2026-03-25")
        call_kwargs = mock_gc.return_value.get_projects.call_args[1]
        assert call_kwargs["planned_after"] == "2026-03-20"
        assert call_kwargs["planned_before"] == "2026-03-25"

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_due_on_expands_to_range(self, mock_gc):
        """due_on date expands to due_after and due_before range for projects."""
        mock_gc.return_value.get_projects.return_value = []
        server.get_projects(due_on="2026-04-01")
        call_kwargs = mock_gc.return_value.get_projects.call_args[1]
        assert call_kwargs["due_after"] == "2026-04-01"
        assert call_kwargs["due_before"] == "2026-04-02"

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_due_on_conflicts_with_due_before(self, mock_gc):
        """Error returned when due_on used with due_before for projects."""
        result = server.get_projects(due_on="2026-04-01", due_before="2026-04-10")
        assert "Error" in result
        assert "mutually exclusive" in result

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_due_after_passed_to_project_client(self, mock_gc):
        """due_after is passed through to client.get_projects."""
        mock_gc.return_value.get_projects.return_value = []
        server.get_projects(due_after="2026-04-01")
        call_kwargs = mock_gc.return_value.get_projects.call_args[1]
        assert call_kwargs["due_after"] == "2026-04-01"

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_created_on_expands_to_range(self, mock_gc):
        """created_on date expands to created_after and created_before range for projects."""
        mock_gc.return_value.get_projects.return_value = []
        server.get_projects(created_on="2026-04-01")
        call_kwargs = mock_gc.return_value.get_projects.call_args[1]
        assert call_kwargs["created_after"] == "2026-04-01"
        assert call_kwargs["created_before"] == "2026-04-02"


class TestCreateProjectEdgeCases:
    """Cover review_interval and note branches in create_project()."""

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_review_interval_in_response(self, mock_gc):
        """Review interval field included in create project response."""
        mock_gc.return_value.create_project.return_value = "proj-123"
        result = server.create_project(name="Test", review_interval_weeks=2)
        assert "Review Interval:" in result
        mock_gc.return_value.create_project.assert_called_once()
        call_kwargs = mock_gc.return_value.create_project.call_args[1]
        assert call_kwargs["review_interval_weeks"] == 2

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_note_in_response(self, mock_gc):
        """Note field included in create project response."""
        mock_gc.return_value.create_project.return_value = "proj-123"
        result = server.create_project(name="Test", note="Some note")
        assert "Note:" in result
        mock_gc.return_value.create_project.assert_called_once()
        call_kwargs = mock_gc.return_value.create_project.call_args[1]
        assert call_kwargs["note"] == "Some note"


class TestUpdateProjectsEdgeCases:
    """Cover error paths in update_projects()."""

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_all_updates_failed(self, mock_gc):
        """Failure details shown when all batch project updates fail."""
        mock_gc.return_value.update_project.side_effect = [
            {"success": False, "project_id": "p1", "updated_fields": [], "error": "not found"},
            {"success": False, "project_id": "p2", "updated_fields": [], "error": "not found"},
        ]
        result = server.update_projects(projects=[
            {"id": "p1", "status": "active"},
            {"id": "p2", "status": "active"},
        ])
        assert "FAILED" in result
        assert "not found" in result
        assert mock_gc.return_value.update_project.call_count == 2

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_exception_handler(self, mock_gc):
        """Exception during batch project update surfaces error message."""
        mock_gc.return_value.update_project.side_effect = RuntimeError("boom")
        result = server.update_projects(projects=[{"id": "p1", "status": "active"}])
        assert "Error" in result
        assert "boom" in result


class TestGetTasksEdgeCases:
    """Cover empty/query branches in get_tasks()."""

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_query_no_results(self, mock_gc):
        """Empty result message returned when task query matches nothing."""
        mock_gc.return_value.get_tasks.return_value = []
        result = server.get_tasks(query="missing")
        assert "No tasks found matching 'missing'" in result
        mock_gc.return_value.get_tasks.assert_called_once()
        call_kwargs = mock_gc.return_value.get_tasks.call_args[1]
        assert call_kwargs["query"] == "missing"

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_planned_on_expands_to_range(self, mock_gc):
        """Planned on date expands to planned_after and planned_before range for tasks."""
        mock_gc.return_value.get_tasks.return_value = []
        server.get_tasks(planned_on="2026-03-23")
        call_kwargs = mock_gc.return_value.get_tasks.call_args[1]
        assert call_kwargs["planned_after"] == "2026-03-23"
        assert call_kwargs["planned_before"] == "2026-03-24"

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_planned_on_conflicts_with_planned_after(self, mock_gc):
        """Error returned when planned_on used with planned_after for tasks."""
        result = server.get_tasks(planned_on="2026-03-23", planned_after="2026-03-20")
        assert "Error" in result
        assert "mutually exclusive" in result

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_due_on_expands_to_range(self, mock_gc):
        """due_on date expands to due_after and due_before range for tasks."""
        mock_gc.return_value.get_tasks.return_value = []
        server.get_tasks(due_on="2026-04-01")
        call_kwargs = mock_gc.return_value.get_tasks.call_args[1]
        assert call_kwargs["due_after"] == "2026-04-01"
        assert call_kwargs["due_before"] == "2026-04-02"

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_due_on_conflicts_with_due_after(self, mock_gc):
        """Error returned when due_on used with due_after for tasks."""
        result = server.get_tasks(due_on="2026-04-01", due_after="2026-03-20")
        assert "Error" in result
        assert "mutually exclusive" in result

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_defer_on_expands_to_range(self, mock_gc):
        """defer_on date expands to defer_after and defer_before range for tasks."""
        mock_gc.return_value.get_tasks.return_value = []
        server.get_tasks(defer_on="2026-04-01")
        call_kwargs = mock_gc.return_value.get_tasks.call_args[1]
        assert call_kwargs["defer_after"] == "2026-04-01"
        assert call_kwargs["defer_before"] == "2026-04-02"

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_defer_on_conflicts_with_defer_before(self, mock_gc):
        """Error returned when defer_on used with defer_before for tasks."""
        result = server.get_tasks(defer_on="2026-04-01", defer_before="2026-04-10")
        assert "Error" in result
        assert "mutually exclusive" in result

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_due_after_passed_to_client(self, mock_gc):
        """due_after is passed through to client.get_tasks."""
        mock_gc.return_value.get_tasks.return_value = []
        server.get_tasks(due_after="2026-04-01")
        call_kwargs = mock_gc.return_value.get_tasks.call_args[1]
        assert call_kwargs["due_after"] == "2026-04-01"

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_defer_before_passed_to_client(self, mock_gc):
        """defer_before is passed through to client.get_tasks."""
        mock_gc.return_value.get_tasks.return_value = []
        server.get_tasks(defer_before="2026-04-10")
        call_kwargs = mock_gc.return_value.get_tasks.call_args[1]
        assert call_kwargs["defer_before"] == "2026-04-10"

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_inbox_no_results(self, mock_gc):
        """Empty inbox message returned when no inbox tasks exist."""
        mock_gc.return_value.get_tasks.return_value = []
        result = server.get_tasks(inbox_only=True)
        assert "No tasks in inbox" in result
        mock_gc.return_value.get_tasks.assert_called_once()
        call_kwargs = mock_gc.return_value.get_tasks.call_args[1]
        assert call_kwargs["inbox_only"] is True

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_query_and_inbox_with_results(self, mock_gc):
        """Combined query and inbox filter shows count with both labels."""
        mock_gc.return_value.get_tasks.return_value = [
            {"id": "t1", "name": "Buy milk", "completed": False},
        ]
        result = server.get_tasks(query="milk", inbox_only=True)
        assert "Found 1 inbox tasks matching 'milk':" in result
        mock_gc.return_value.get_tasks.assert_called_once()
        call_kwargs = mock_gc.return_value.get_tasks.call_args[1]
        assert call_kwargs["query"] == "milk"
        assert call_kwargs["inbox_only"] is True

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_query_with_results(self, mock_gc):
        """Result count and query shown in header when tasks match."""
        mock_gc.return_value.get_tasks.return_value = [
            {"id": "t1", "name": "Report", "completed": False},
            {"id": "t2", "name": "Report v2", "completed": False},
        ]
        result = server.get_tasks(query="Report")
        assert "Found 2 tasks matching 'Report':" in result
        mock_gc.return_value.get_tasks.assert_called_once()
        call_kwargs = mock_gc.return_value.get_tasks.call_args[1]
        assert call_kwargs["query"] == "Report"


class TestUpdateTaskEdgeCases:
    """Cover zero-changes branch in update_task()."""

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_no_changes_detected(self, mock_gc):
        """No-changes message returned when update_task has no fields to update."""
        mock_gc.return_value.update_task.return_value = {
            "success": True,
            "updated_fields": [],
        }
        result = server.update_task(task_id="t1")
        assert "no changes detected" in result
        mock_gc.return_value.update_task.assert_called_once()
        call_kwargs = mock_gc.return_value.update_task.call_args[1]
        assert call_kwargs["task_id"] == "t1"


class TestUpdateTasksEdgeCases:
    """Cover single failure branch in update_tasks()."""

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_single_failure(self, mock_gc):
        """Error message includes task ID and reason when batch task update fails."""
        mock_gc.return_value.update_task.return_value = {
            "success": False,
            "task_id": "t1",
            "updated_fields": [],
            "error": "not found",
        }
        result = server.update_tasks([{"id": "t1", "flagged": True}])
        assert "Error updating task t1: not found" in result
        mock_gc.return_value.update_task.assert_called_once()
        call_kwargs = mock_gc.return_value.update_task.call_args.kwargs
        assert call_kwargs["task_id"] == "t1"
        assert call_kwargs["flagged"] is True


class TestGetTagsEdgeCases:
    """Cover empty tags and mutually exclusive branch."""

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_empty_tags(self, mock_gc):
        """Zero count message returned when no tags exist."""
        mock_gc.return_value.get_tags.return_value = []
        result = server.get_tags()
        assert "Found 0 tags" in result
        mock_gc.return_value.get_tags.assert_called_once()

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_mutually_exclusive_tag(self, mock_gc):
        """Mutually exclusive flag shown in formatted tag output."""
        mock_gc.return_value.get_tags.return_value = [
            {"id": "tag1", "name": "Priority", "status": "active", "childrenAreMutuallyExclusive": True},
        ]
        result = server.get_tags()
        assert "Children Are Mutually Exclusive: Yes" in result
        mock_gc.return_value.get_tags.assert_called_once()


# ============================================================================
# Category C: Batch operations
# ============================================================================


class TestDeleteTagsEdgeCases:
    """Cover failure and exception branches in delete_tags()."""

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_single_tag_delete_failed(self, mock_gc):
        """Failure message returned when single tag deletion fails."""
        mock_gc.return_value.delete_tags.return_value = {
            "deleted_count": 0,
            "failed_count": 1,
        }
        result = server.delete_tags(tag_ids="tag1")
        assert "Failed to delete tag" in result
        mock_gc.return_value.delete_tags.assert_called_once_with("tag1")

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_multiple_tags_all_failed(self, mock_gc):
        """Failure message includes total count when all batch tag deletes fail."""
        mock_gc.return_value.delete_tags.return_value = {
            "deleted_count": 0,
            "failed_count": 3,
        }
        result = server.delete_tags(tag_ids=["t1", "t2", "t3"])
        assert "Failed to delete all 3 tags" in result
        mock_gc.return_value.delete_tags.assert_called_once_with(["t1", "t2", "t3"])

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_exception_handler(self, mock_gc):
        """Exception during tag deletion surfaces error message."""
        mock_gc.return_value.delete_tags.side_effect = RuntimeError("boom")
        result = server.delete_tags(tag_ids="tag1")
        assert "Error deleting tags:" in result


class TestDeleteTasksEdgeCases:
    """Cover failure and exception branches in delete_tasks()."""

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_single_task_delete_failed(self, mock_gc):
        """Failure message returned when single task deletion fails."""
        mock_gc.return_value.delete_tasks.return_value = {
            "deleted_count": 0,
            "failed_count": 1,
        }
        result = server.delete_tasks(task_ids="task1")
        assert "Failed to delete task" in result
        mock_gc.return_value.delete_tasks.assert_called_once_with("task1")

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_exception_handler(self, mock_gc):
        """Exception during task deletion surfaces error message."""
        mock_gc.return_value.delete_tasks.side_effect = RuntimeError("boom")
        result = server.delete_tasks(task_ids="task1")
        assert "Error deleting tasks:" in result


class TestDeleteProjectsEdgeCases:
    """Cover delete_projects response formatting and exception branches."""

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_single_project_deleted(self, mock_gc):
        """Success message returned for single project deletion."""
        mock_gc.return_value.delete_projects.return_value = {
            "deleted_count": 1,
            "failed_count": 0,
        }
        result = server.delete_projects(project_ids="p1")
        assert "Successfully deleted 1 project" in result
        mock_gc.return_value.delete_projects.assert_called_once_with("p1")

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_multiple_projects_deleted(self, mock_gc):
        """Success message with plural count for multiple project deletions."""
        mock_gc.return_value.delete_projects.return_value = {
            "deleted_count": 3,
            "failed_count": 0,
        }
        result = server.delete_projects(project_ids=["p1", "p2", "p3"])
        assert "Successfully deleted 3 projects" in result
        mock_gc.return_value.delete_projects.assert_called_once_with(["p1", "p2", "p3"])

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_partial_failure(self, mock_gc):
        """Partial failure message shows deleted and failed counts."""
        mock_gc.return_value.delete_projects.return_value = {
            "deleted_count": 1,
            "failed_count": 1,
        }
        result = server.delete_projects(project_ids=["p1", "p2"])
        assert "Deleted 1 of 2 projects (1 failed)" in result
        mock_gc.return_value.delete_projects.assert_called_once_with(["p1", "p2"])

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_single_project_id_total_count(self, mock_gc):
        """Failure message computes total from string input as count of one."""
        mock_gc.return_value.delete_projects.return_value = {
            "deleted_count": 0,
            "failed_count": 1,
        }
        result = server.delete_projects(project_ids="p1")
        assert "Deleted 0 of 1 projects (1 failed)" in result
        mock_gc.return_value.delete_projects.assert_called_once_with("p1")

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_exception_handler(self, mock_gc):
        """Exception during project deletion surfaces error message."""
        mock_gc.return_value.delete_projects.side_effect = RuntimeError("boom")
        result = server.delete_projects(project_ids="p1")
        assert "Error deleting projects:" in result


class TestCreateFolderEdgeCases:
    """Cover root-level and exception branches in create_folder()."""

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_create_at_root(self, mock_gc):
        """Root level location shown when folder created without parent."""
        mock_gc.return_value.create_folder.return_value = "folder-123"
        result = server.create_folder(name="New Folder")
        assert "at root level" in result
        mock_gc.return_value.create_folder.assert_called_once()

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_exception_handler(self, mock_gc):
        """Exception during folder creation surfaces error message."""
        mock_gc.return_value.create_folder.side_effect = RuntimeError("boom")
        result = server.create_folder(name="Bad Folder")
        assert "error" in result.lower()


class TestUpdateFolderEdgeCases:
    """Cover success and failure paths in update_folder()."""

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_single_field_updated(self, mock_gc):
        """Success message lists the single updated field name."""
        mock_gc.return_value.update_folder.return_value = {
            "success": True,
            "updated_fields": ["name"],
        }
        result = server.update_folder(folder_id="f1", name="Renamed")
        assert "Successfully updated folder f1" in result
        assert "name" in result
        mock_gc.return_value.update_folder.assert_called_once_with(folder_id="f1", name="Renamed")

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_multiple_fields_updated(self, mock_gc):
        """Success message lists all updated field names."""
        mock_gc.return_value.update_folder.return_value = {
            "success": True,
            "updated_fields": ["name", "status"],
        }
        result = server.update_folder(folder_id="f1", name="Renamed", status="dropped")
        assert "name" in result and "status" in result
        mock_gc.return_value.update_folder.assert_called_once_with(folder_id="f1", name="Renamed", status="dropped")

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_failure(self, mock_gc):
        """Error message includes folder ID when update fails."""
        mock_gc.return_value.update_folder.return_value = {
            "success": False,
            "error": "folder not found",
        }
        result = server.update_folder(folder_id="f1", name="X")
        assert "Error updating folder f1" in result
        mock_gc.return_value.update_folder.assert_called_once_with(folder_id="f1", name="X")


class TestReorderTaskEdgeCases:
    """Cover success, failure, and exception paths in reorder_task()."""

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_success_before(self, mock_gc):
        """Success message includes before-task reference."""
        mock_gc.return_value.reorder_task.return_value = True
        result = server.reorder_task(task_id="t1", before_task_id="t2")
        assert "before task t2" in result
        mock_gc.return_value.reorder_task.assert_called_once_with("t1", "t2", None)

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_success_after(self, mock_gc):
        """Success message includes after-task reference."""
        mock_gc.return_value.reorder_task.return_value = True
        result = server.reorder_task(task_id="t1", after_task_id="t3")
        assert "after task t3" in result
        mock_gc.return_value.reorder_task.assert_called_once_with("t1", None, "t3")

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_failure(self, mock_gc):
        """Failure message returned when task reorder returns false."""
        mock_gc.return_value.reorder_task.return_value = False
        result = server.reorder_task(task_id="t1", before_task_id="t2")
        assert "Failed to reorder task" in result

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_value_error(self, mock_gc):
        """ValueError during task reorder surfaces validation message."""
        mock_gc.return_value.reorder_task.side_effect = ValueError("bad input")
        result = server.reorder_task(task_id="t1", before_task_id="t2")
        assert "Error: bad input" in result

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_exception_handler(self, mock_gc):
        """Exception during task reorder surfaces error message."""
        mock_gc.return_value.reorder_task.side_effect = RuntimeError("boom")
        result = server.reorder_task(task_id="t1", before_task_id="t2")
        assert "Error reordering task:" in result


class TestReorderProjectEdgeCases:
    """Cover success, failure, and exception paths in reorder_project()."""

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_success_before(self, mock_gc):
        """Success message includes before-project reference."""
        mock_gc.return_value.reorder_project.return_value = True
        result = server.reorder_project(project_id="p1", before_project_id="p2")
        assert "before project p2" in result
        mock_gc.return_value.reorder_project.assert_called_once_with("p1", "p2", None)

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_success_after(self, mock_gc):
        """Success message includes after-project reference."""
        mock_gc.return_value.reorder_project.return_value = True
        result = server.reorder_project(project_id="p1", after_project_id="p3")
        assert "after project p3" in result
        mock_gc.return_value.reorder_project.assert_called_once_with("p1", None, "p3")

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_failure(self, mock_gc):
        """Failure message returned when project reorder returns false."""
        mock_gc.return_value.reorder_project.return_value = False
        result = server.reorder_project(project_id="p1", before_project_id="p2")
        assert "Failed to reorder project" in result

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_value_error(self, mock_gc):
        """ValueError during project reorder surfaces validation message."""
        mock_gc.return_value.reorder_project.side_effect = ValueError("bad input")
        result = server.reorder_project(project_id="p1", before_project_id="p2")
        assert "Error: bad input" in result

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_exception_handler(self, mock_gc):
        """Exception during project reorder surfaces error message."""
        mock_gc.return_value.reorder_project.side_effect = RuntimeError("boom")
        result = server.reorder_project(project_id="p1", before_project_id="p2")
        assert "Error reordering project:" in result


class TestSwitchPerspectiveEdgeCases:
    """Cover exception branch in switch_perspective()."""

    @mock.patch("omnifocus_mcp.server_fastmcp.get_client")
    def test_exception_handler(self, mock_gc):
        """Exception during perspective switch surfaces error message."""
        mock_gc.return_value.switch_perspective.side_effect = RuntimeError("boom")
        result = server.switch_perspective(perspective_name="Custom")
        assert "Error switching perspective:" in result
