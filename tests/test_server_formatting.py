"""
Tests for server formatting functions and edge cases.

These tests target uncovered code paths in server_fastmcp.py to increase
test coverage from 84% to 85%+.
"""

import pytest
from omnifocus_mcp.server_fastmcp import (
    _truncate_note,
    _format_task,
    _format_project
)


class TestNoteTruncation:
    """Test note truncation helper function."""

    def test_truncate_long_note(self):
        """Test that long notes are truncated with ellipsis."""
        long_note = "a" * 300  # Longer than default max_length (100)
        result = _truncate_note(long_note)
        assert len(result) == 103  # 100 + "..."
        assert result.endswith("...")
        assert result[:100] == long_note[:100]

    def test_short_note_not_truncated(self):
        """Test that short notes are returned unchanged."""
        short_note = "This is a short note"
        result = _truncate_note(short_note)
        assert result == short_note
        assert not result.endswith("...")


class TestTaskFormatting:
    """Test task formatting function."""

    def test_format_task_with_all_optional_fields(self):
        """Test formatting task with all optional fields present."""
        task = {
            "id": "task123",
            "name": "Test Task",
            "projectName": "Test Project",
            "completed": False,
            "dropped": True,
            "blocked": True,
            "numberOfAvailableTasks": 2,
            "available": True,
            "next": True,
            "flagged": True,
            "dueDate": "2025-12-01",
            "deferDate": "2025-11-20",
            "estimatedMinutes": 60,
            "tags": ["tag1", "tag2"],
            "note": "This is a test note",
            "parentTaskId": "parent123"
        }

        result = _format_task(task)

        # Check all fields are present
        assert "ID: task123" in result
        assert "Name: Test Task" in result
        assert "Project: Test Project" in result
        assert "Completed: False" in result
        assert "Dropped: Yes" in result
        assert "Blocked: Yes (but has 2 available subtask(s))" in result
        assert "Available: True" in result
        assert "Next: Yes" in result
        assert "Flagged: Yes" in result
        assert "Due: 2025-12-01" in result
        assert "Defer: 2025-11-20" in result
        assert "Estimated: 60 minutes" in result
        assert "Tags:" in result
        assert "Note: This is a test note" in result
        assert "Parent Task ID: parent123" in result

    def test_format_task_blocked_without_available_subtasks(self):
        """Test formatting blocked task without available subtasks."""
        task = {
            "id": "task123",
            "name": "Blocked Task",
            "projectName": "Project",
            "completed": False,
            "blocked": True,
            "numberOfAvailableTasks": 0
        }

        result = _format_task(task)
        assert "Blocked: Yes\n" in result
        assert "available subtask" not in result

    def test_format_task_with_full_note(self):
        """Test formatting task with full note (no truncation)."""
        long_note = "a" * 300
        task = {
            "id": "task123",
            "name": "Task",
            "projectName": "Project",
            "completed": False,
            "note": long_note
        }

        result = _format_task(task, truncate_notes=False)
        assert f"Note: {long_note}" in result
        assert "..." not in result

    def test_format_task_with_truncated_note(self):
        """Test formatting task with truncated note."""
        long_note = "a" * 300
        task = {
            "id": "task123",
            "name": "Task",
            "projectName": "Project",
            "completed": False,
            "note": long_note
        }

        result = _format_task(task, truncate_notes=True)
        assert "Note:" in result
        assert "..." in result


class TestProjectFormatting:
    """Test project formatting function."""

    def test_format_project_with_all_fields(self):
        """Test formatting project with all optional fields."""
        project = {
            "id": "proj123",
            "name": "Test Project",
            "status": "active",
            "note": "Project notes",
            "sequential": True,
            "creationDate": "2025-11-01",
            "folderPath": "Work/Active"
        }

        result = _format_project(project)

        assert "ID: proj123" in result
        assert "Name: Test Project" in result
        assert "Status: active" in result
        assert "Note: Project notes" in result
        assert "Sequential: True" in result
        assert "Created: 2025-11-01" in result
        assert "Folder: Work/Active" in result

    def test_format_project_with_long_note(self):
        """Test formatting project with long note (truncated by default)."""
        long_note = "x" * 300
        project = {
            "id": "proj123",
            "name": "Project",
            "status": "active",
            "note": long_note
        }

        result = _format_project(project)
        assert "Note:" in result
        assert "..." in result

    def test_format_project_with_full_note(self):
        """Test formatting project with full note (no truncation)."""
        long_note = "x" * 300
        project = {
            "id": "proj123",
            "name": "Project",
            "status": "active",
            "note": long_note
        }

        result = _format_project(project, truncate_notes=False)
        assert f"Note: {long_note}" in result
        assert result.count("x") >= 300
