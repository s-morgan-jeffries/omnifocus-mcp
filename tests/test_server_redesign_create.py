"""Tests for redesigned server API create functions (server_fastmcp.py layer).

This file tests the MCP server layer for the NEW API (v1.0.0 redesign).
Tests are written FIRST (TDD) before implementing server changes.
"""
from unittest import mock

# Import server module
import omnifocus_mcp.server_fastmcp as server

# Extract function from FunctionTool wrapper
create_task = server.create_task


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
                planned_date=None,
                flagged=False,
                tags=None,
                estimated_minutes=None,
                sequential=False,
                completed_by_children=False
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
                tags=["urgent", "work"],  # Native list, same as update_task
                estimated_minutes=60
            )

            mock_client.create_task.assert_called_once_with(
                task_name="Full Task",
                project_id="proj-123",
                parent_task_id=None,
                note="Task note",
                due_date="2025-12-31",
                defer_date="2025-12-01",
                planned_date=None,
                flagged=True,
                tags=["urgent", "work"],  # Parsed to list by server
                estimated_minutes=60,
                sequential=False,
                completed_by_children=False
            )
            assert "task-005" in result

    def test_create_task_tags_rejects_json_string(self):
        """Tags parameter must be a native list, not a JSON string."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_task.return_value = "task-006"
            mock_get_client.return_value = mock_client

            result = create_task(
                task_name="Task with JSON string tags",
                tags='["urgent", "work"]'  # Old format — should error
            )

            assert "error" in result.lower()
            mock_client.create_task.assert_not_called()

    # ========================================================================
    # Error Handling
    # ========================================================================

    def test_create_task_handles_client_error(self):
        """NEW API: Server handles client ValueError gracefully."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_task.side_effect = ValueError(
                "Cannot specify both project_id and parent_task_id"
            )
            mock_get_client.return_value = mock_client

            result = create_task(
                task_name="Bad Task",
                project_id="proj-123",
                parent_task_id="task-parent"
            )

            assert isinstance(result, str)
            assert "error" in result.lower()
            assert "project_id" in result.lower()
            assert "parent_task_id" in result.lower()

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


class TestCreateTasksUnified:
    """Tests for unified create_tasks() with Pydantic model input."""

    def test_create_tasks_single_item(self):
        """create_tasks with a single task returns same format as create_task."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_task.return_value = "task-001"
            mock_get_client.return_value = mock_client

            create_tasks = server.create_tasks
            result = create_tasks(tasks=[{"task_name": "Test Task", "project_id": "proj-1"}])

            assert isinstance(result, str)
            assert "task-001" in result
            assert "Successfully" in result
            mock_client.create_task.assert_called_once()
            call_kwargs = mock_client.create_task.call_args[1]
            assert call_kwargs["task_name"] == "Test Task"
            assert call_kwargs["project_id"] == "proj-1"

    def test_create_tasks_multiple_items(self):
        """create_tasks with multiple tasks returns summary."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_task.side_effect = ["task-001", "task-002", "task-003"]
            mock_get_client.return_value = mock_client

            create_tasks = server.create_tasks
            result = create_tasks(tasks=[
                {"task_name": "Task A"},
                {"task_name": "Task B", "flagged": True},
                {"task_name": "Task C", "tags": ["work"]},
            ])

            assert isinstance(result, str)
            assert "3" in result
            assert mock_client.create_task.call_count == 3

    def test_create_tasks_partial_failure(self):
        """create_tasks with one failure returns mixed results."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_task.side_effect = [
                "task-001",
                ValueError("Both project_id and parent_task_id"),
                "task-003",
            ]
            mock_get_client.return_value = mock_client

            create_tasks = server.create_tasks
            result = create_tasks(tasks=[
                {"task_name": "Good Task"},
                {"task_name": "Bad Task", "project_id": "p1", "parent_task_id": "t1"},
                {"task_name": "Also Good"},
            ])

            assert isinstance(result, str)
            assert "2" in result  # 2 succeeded
            assert "1" in result  # 1 failed
            assert "Bad Task" in result or "failed" in result.lower()

    def test_create_tasks_with_all_fields(self):
        """create_tasks passes all fields through to connector."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_task.return_value = "task-001"
            mock_get_client.return_value = mock_client

            create_tasks = server.create_tasks
            result = create_tasks(tasks=[{
                "task_name": "Full Task",
                "project_id": "proj-1",
                "note": "A note",
                "due_date": "2026-04-01",
                "defer_date": "2026-03-25",
                "planned_date": "2026-03-28",
                "flagged": True,
                "tags": ["work", "urgent"],
                "estimated_minutes": 30,
                "sequential": True,
                "completed_by_children": True,
            }])

            call_kwargs = mock_client.create_task.call_args[1]
            assert call_kwargs["task_name"] == "Full Task"
            assert call_kwargs["flagged"] is True
            assert call_kwargs["tags"] == ["work", "urgent"]
            assert call_kwargs["estimated_minutes"] == 30


class TestCreateProjectServerRedesign:
    """Tests for create_project() MCP tool ValueError handling."""

    def test_create_project_handles_value_error(self):
        """Server: create_project() catches ValueError and returns error string."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_project.side_effect = ValueError("Project name cannot be empty")
            mock_get_client.return_value = mock_client

            result = server.create_project(name="")
            assert isinstance(result, str)
            assert "error" in result.lower()


class TestCreateProjectsUnified:
    """Tests for unified create_projects() with Pydantic model input."""

    def test_create_projects_single_item(self):
        """create_projects with a single project returns detailed format."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_project.return_value = "proj-001"
            mock_get_client.return_value = mock_client

            create_projects = server.create_projects
            result = create_projects(projects=[{"name": "Test Project"}])

            assert isinstance(result, str)
            assert "proj-001" in result
            assert "Successfully" in result
            mock_client.create_project.assert_called_once()
            call_kwargs = mock_client.create_project.call_args[1]
            assert call_kwargs["name"] == "Test Project"

    def test_create_projects_multiple_items(self):
        """create_projects with multiple projects returns summary."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_project.side_effect = ["proj-001", "proj-002", "proj-003"]
            mock_get_client.return_value = mock_client

            create_projects = server.create_projects
            result = create_projects(projects=[
                {"name": "Project A"},
                {"name": "Project B", "sequential": True},
                {"name": "Project C", "folder_path": "Work"},
            ])

            assert isinstance(result, str)
            assert "3" in result
            assert mock_client.create_project.call_count == 3

    def test_create_projects_partial_failure(self):
        """create_projects with one failure returns mixed results."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_project.side_effect = [
                "proj-001",
                ValueError("Folder not found"),
                "proj-003",
            ]
            mock_get_client.return_value = mock_client

            create_projects = server.create_projects
            result = create_projects(projects=[
                {"name": "Good Project"},
                {"name": "Bad Project", "folder_path": "Nonexistent"},
                {"name": "Also Good"},
            ])

            assert isinstance(result, str)
            assert "2" in result  # 2 succeeded
            assert "Bad Project" in result
            assert "FAILED" in result

    def test_create_projects_with_all_fields(self):
        """create_projects passes all fields through to connector."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_project.return_value = "proj-001"
            mock_get_client.return_value = mock_client

            create_projects = server.create_projects
            result = create_projects(projects=[{
                "name": "Full Project",
                "note": "A note",
                "folder_path": "Work > Clients",
                "project_type": "sequential",
                "sequential": True,
                "review_interval_weeks": 2,
                "completed_by_children": True,
                "due_date": "2026-04-01",
                "defer_date": "2026-03-25",
                "planned_date": "2026-03-28",
            }])

            call_kwargs = mock_client.create_project.call_args[1]
            assert call_kwargs["name"] == "Full Project"
            assert call_kwargs["note"] == "A note"
            assert call_kwargs["folder_path"] == "Work > Clients"
            assert call_kwargs["project_type"] == "sequential"
            assert call_kwargs["sequential"] is True
            assert call_kwargs["review_interval_weeks"] == 2
            assert call_kwargs["completed_by_children"] is True
            assert call_kwargs["due_date"] == "2026-04-01"
            assert call_kwargs["defer_date"] == "2026-03-25"
            assert call_kwargs["planned_date"] == "2026-03-28"

    def test_create_project_delegates_to_create_projects(self):
        """Old create_project should delegate to create_projects."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_project.return_value = "proj-delegated"
            mock_get_client.return_value = mock_client

            result = server.create_project(
                name="Delegated Project",
                folder_path="Work",
                review_interval_weeks=4,
            )

            assert "proj-delegated" in result
            assert "Successfully" in result
            mock_client.create_project.assert_called_once()

    def test_create_projects_single_shows_type_info(self):
        """Single project creation shows type label in result."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_project.return_value = "proj-seq"
            mock_get_client.return_value = mock_client

            result = server.create_projects(projects=[{
                "name": "Sequential Project",
                "project_type": "sequential",
            }])

            assert "Sequential" in result
            assert "tasks completed in order" in result.lower()

    def test_create_projects_single_error(self):
        """Single project failure returns error string."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_project.side_effect = ValueError("Bad input")
            mock_get_client.return_value = mock_client

            result = server.create_projects(projects=[{"name": "Bad"}])

            assert "Error" in result
            assert "Bad input" in result
