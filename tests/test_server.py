"""Unit tests for MCP server handlers."""
import pytest
from unittest import mock
from mcp.types import TextContent

# Import server module
from omnifocus_mcp import server


class TestListTools:
    """Tests for the list_tools handler."""

    @pytest.mark.asyncio
    async def test_list_tools_returns_all_tools(self):
        """Test that list_tools returns all expected tools."""
        tools = await server.list_tools()

        assert len(tools) == 11
        tool_names = [tool.name for tool in tools]
        assert "get_projects" in tool_names
        assert "search_projects" in tool_names
        assert "add_task" in tool_names
        assert "add_note" in tool_names
        assert "get_tasks" in tool_names
        assert "complete_task" in tool_names
        assert "update_task" in tool_names
        assert "get_inbox_tasks" in tool_names
        assert "create_inbox_task" in tool_names
        assert "get_tags" in tool_names
        assert "add_tag_to_task" in tool_names

    @pytest.mark.asyncio
    async def test_list_tools_schema_validation(self):
        """Test that all tools have valid schemas."""
        tools = await server.list_tools()

        for tool in tools:
            assert tool.name
            assert tool.description
            assert tool.inputSchema
            assert "type" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"
            assert "properties" in tool.inputSchema
            assert "required" in tool.inputSchema


class TestCallToolGetProjects:
    """Tests for the get_projects tool handler."""

    @pytest.fixture
    def sample_projects(self):
        """Sample projects data."""
        return [
            {
                "id": "proj-001",
                "name": "Test Project",
                "note": "Short note",
                "status": "active",
                "folderPath": "Work"
            },
            {
                "id": "proj-002",
                "name": "Another Project",
                "note": "x" * 150,  # Long note to test truncation
                "status": "active",
                "folderPath": ""
            }
        ]

    @pytest.mark.asyncio
    async def test_get_projects_success(self, sample_projects):
        """Test successful project retrieval."""
        with mock.patch.object(server.client, 'get_projects', return_value=sample_projects):
            result = await server.call_tool("get_projects", {})

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "Found 2 active projects" in result[0].text
            assert "Test Project" in result[0].text
            assert "proj-001" in result[0].text

    @pytest.mark.asyncio
    async def test_get_projects_empty(self):
        """Test handling of empty projects list."""
        with mock.patch.object(server.client, 'get_projects', return_value=[]):
            result = await server.call_tool("get_projects", {})

            assert len(result) == 1
            assert "Found 0 active projects" in result[0].text

    @pytest.mark.asyncio
    async def test_get_projects_truncates_long_notes(self, sample_projects):
        """Test that long notes are truncated in output."""
        with mock.patch.object(server.client, 'get_projects', return_value=sample_projects):
            result = await server.call_tool("get_projects", {})

            assert "..." in result[0].text  # Long note should be truncated

    @pytest.mark.asyncio
    async def test_get_projects_handles_exception(self):
        """Test error handling when get_projects raises exception."""
        with mock.patch.object(server.client, 'get_projects', side_effect=Exception("OmniFocus error")):
            result = await server.call_tool("get_projects", {})

            assert len(result) == 1
            assert "Error" in result[0].text
            assert "OmniFocus error" in result[0].text


class TestCallToolSearchProjects:
    """Tests for the search_projects tool handler."""

    @pytest.fixture
    def sample_projects(self):
        """Sample projects data."""
        return [
            {
                "id": "proj-001",
                "name": "Budget Review",
                "note": "Q4 financial review",
                "status": "active",
                "folderPath": "Work > Finance"
            }
        ]

    @pytest.mark.asyncio
    async def test_search_projects_success(self, sample_projects):
        """Test successful project search."""
        with mock.patch.object(server.client, 'search_projects', return_value=sample_projects):
            result = await server.call_tool("search_projects", {"query": "budget"})

            assert len(result) == 1
            assert "Found 1 projects matching 'budget'" in result[0].text
            assert "Budget Review" in result[0].text

    @pytest.mark.asyncio
    async def test_search_projects_no_results(self):
        """Test search with no matching results."""
        with mock.patch.object(server.client, 'search_projects', return_value=[]):
            result = await server.call_tool("search_projects", {"query": "nonexistent"})

            assert len(result) == 1
            assert "No projects found matching 'nonexistent'" in result[0].text

    @pytest.mark.asyncio
    async def test_search_projects_missing_query(self):
        """Test search without query parameter."""
        result = await server.call_tool("search_projects", {})

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "query parameter is required" in result[0].text

    @pytest.mark.asyncio
    async def test_search_projects_empty_query(self):
        """Test search with empty query string."""
        result = await server.call_tool("search_projects", {"query": ""})

        assert len(result) == 1
        assert "Error" in result[0].text

    @pytest.mark.asyncio
    async def test_search_projects_handles_exception(self):
        """Test error handling when search_projects raises exception."""
        with mock.patch.object(server.client, 'search_projects', side_effect=Exception("Search failed")):
            result = await server.call_tool("search_projects", {"query": "test"})

            assert len(result) == 1
            assert "Error" in result[0].text


class TestCallToolAddTask:
    """Tests for the add_task tool handler."""

    @pytest.mark.asyncio
    async def test_add_task_success(self):
        """Test successful task addition."""
        with mock.patch.object(server.client, 'add_task', return_value=True):
            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "New Task",
                "note": "Task note"
            })

            assert len(result) == 1
            assert "Successfully added task 'New Task'" in result[0].text
            assert "proj-001" in result[0].text

    @pytest.mark.asyncio
    async def test_add_task_without_note(self):
        """Test adding task without note."""
        with mock.patch.object(server.client, 'add_task', return_value=True):
            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Task without note"
            })

            assert len(result) == 1
            assert "Successfully added task" in result[0].text

    @pytest.mark.asyncio
    async def test_add_task_failure(self):
        """Test handling of task addition failure."""
        with mock.patch.object(server.client, 'add_task', return_value=False):
            result = await server.call_tool("add_task", {
                "project_id": "invalid-id",
                "task_name": "Task"
            })

            assert len(result) == 1
            assert "Failed to add task" in result[0].text

    @pytest.mark.asyncio
    async def test_add_task_missing_project_id(self):
        """Test adding task without project_id."""
        result = await server.call_tool("add_task", {
            "task_name": "Task"
        })

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "project_id" in result[0].text

    @pytest.mark.asyncio
    async def test_add_task_missing_task_name(self):
        """Test adding task without task_name."""
        result = await server.call_tool("add_task", {
            "project_id": "proj-001"
        })

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "task_name" in result[0].text

    @pytest.mark.asyncio
    async def test_add_task_with_special_characters(self):
        """Test adding task with special characters."""
        with mock.patch.object(server.client, 'add_task', return_value=True):
            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": 'Task with "quotes"',
                "note": "Note\nwith\nnewlines"
            })

            assert len(result) == 1
            assert "Successfully added task" in result[0].text

    @pytest.mark.asyncio
    async def test_add_task_handles_exception(self):
        """Test error handling when add_task raises exception."""
        with mock.patch.object(server.client, 'add_task', side_effect=Exception("Add failed")):
            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Task"
            })

            assert len(result) == 1
            assert "Error" in result[0].text

    @pytest.mark.asyncio
    async def test_add_task_with_due_date(self):
        """Test adding task with due date."""
        with mock.patch.object(server.client, 'add_task', return_value=True):
            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Task with due date",
                "due_date": "2025-10-15"
            })

            assert len(result) == 1
            assert "Successfully added task" in result[0].text
            assert "due 2025-10-15" in result[0].text

    @pytest.mark.asyncio
    async def test_add_task_with_defer_date(self):
        """Test adding task with defer date."""
        with mock.patch.object(server.client, 'add_task', return_value=True):
            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Task with defer date",
                "defer_date": "2025-10-08"
            })

            assert len(result) == 1
            assert "Successfully added task" in result[0].text
            assert "defer 2025-10-08" in result[0].text

    @pytest.mark.asyncio
    async def test_add_task_flagged(self):
        """Test adding flagged task."""
        with mock.patch.object(server.client, 'add_task', return_value=True):
            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Flagged task",
                "flagged": True
            })

            assert len(result) == 1
            assert "Successfully added task" in result[0].text
            assert "flagged" in result[0].text

    @pytest.mark.asyncio
    async def test_add_task_with_tags(self):
        """Test adding task with tags."""
        with mock.patch.object(server.client, 'add_task', return_value=True):
            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Task with tags",
                "tags": ["urgent", "work"]
            })

            assert len(result) == 1
            assert "Successfully added task" in result[0].text
            assert "tags: urgent, work" in result[0].text

    @pytest.mark.asyncio
    async def test_add_task_with_all_properties(self):
        """Test adding task with all properties."""
        with mock.patch.object(server.client, 'add_task', return_value=True):
            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Complete task",
                "note": "Task description",
                "due_date": "2025-10-15T17:00:00",
                "defer_date": "2025-10-08T09:00:00",
                "flagged": True,
                "tags": ["urgent", "important"]
            })

            assert len(result) == 1
            assert "Successfully added task 'Complete task'" in result[0].text
            assert "due 2025-10-15T17:00:00" in result[0].text
            assert "defer 2025-10-08T09:00:00" in result[0].text
            assert "flagged" in result[0].text
            assert "tags: urgent, important" in result[0].text
            # Verify client.add_task was called with all parameters
            server.client.add_task.assert_called_once_with(
                "proj-001",
                "Complete task",
                note="Task description",
                due_date="2025-10-15T17:00:00",
                defer_date="2025-10-08T09:00:00",
                flagged=True,
                tags=["urgent", "important"]
            )


class TestCallToolGetTasks:
    """Tests for the get_tasks tool handler."""

    @pytest.fixture
    def sample_tasks(self):
        """Sample tasks data."""
        return [
            {
                "id": "task-001",
                "name": "Test Task",
                "note": "Task note",
                "completed": False,
                "flagged": True,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "2025-10-15T17:00:00",
                "deferDate": "2025-10-08T09:00:00",
                "completionDate": "",
                "tags": "urgent, work"
            },
            {
                "id": "task-002",
                "name": "Another Task",
                "note": "x" * 150,  # Long note to test truncation
                "completed": False,
                "flagged": False,
                "projectId": "proj-002",
                "projectName": "Another Project",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": ""
            }
        ]

    @pytest.mark.asyncio
    async def test_get_tasks_all(self, sample_tasks):
        """Test getting all tasks."""
        with mock.patch.object(server.client, 'get_tasks', return_value=sample_tasks):
            result = await server.call_tool("get_tasks", {})

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "Found 2 tasks" in result[0].text
            assert "Test Task" in result[0].text
            assert "task-001" in result[0].text
            assert "🚩 Flagged" in result[0].text

    @pytest.mark.asyncio
    async def test_get_tasks_by_project(self, sample_tasks):
        """Test getting tasks filtered by project."""
        with mock.patch.object(server.client, 'get_tasks', return_value=sample_tasks):
            result = await server.call_tool("get_tasks", {"project_id": "proj-001"})

            assert len(result) == 1
            assert "Found 2 tasks from project proj-001" in result[0].text
            server.client.get_tasks.assert_called_once_with(
                project_id="proj-001",
                include_completed=False,
                flagged_only=False
            )

    @pytest.mark.asyncio
    async def test_get_tasks_include_completed(self, sample_tasks):
        """Test getting tasks including completed ones."""
        with mock.patch.object(server.client, 'get_tasks', return_value=sample_tasks):
            result = await server.call_tool("get_tasks", {"include_completed": True})

            assert len(result) == 1
            assert "(including completed)" in result[0].text
            server.client.get_tasks.assert_called_once_with(
                project_id=None,
                include_completed=True,
                flagged_only=False
            )

    @pytest.mark.asyncio
    async def test_get_tasks_flagged_only(self, sample_tasks):
        """Test getting only flagged tasks."""
        with mock.patch.object(server.client, 'get_tasks', return_value=sample_tasks):
            result = await server.call_tool("get_tasks", {"flagged_only": True})

            assert len(result) == 1
            assert "(flagged only)" in result[0].text
            server.client.get_tasks.assert_called_once_with(
                project_id=None,
                include_completed=False,
                flagged_only=True
            )

    @pytest.mark.asyncio
    async def test_get_tasks_empty(self):
        """Test handling of empty tasks list."""
        with mock.patch.object(server.client, 'get_tasks', return_value=[]):
            result = await server.call_tool("get_tasks", {})

            assert len(result) == 1
            assert "No tasks found" in result[0].text

    @pytest.mark.asyncio
    async def test_get_tasks_with_all_filters(self, sample_tasks):
        """Test getting tasks with all filters."""
        with mock.patch.object(server.client, 'get_tasks', return_value=sample_tasks):
            result = await server.call_tool("get_tasks", {
                "project_id": "proj-001",
                "include_completed": True,
                "flagged_only": True
            })

            assert len(result) == 1
            assert "from project proj-001" in result[0].text
            assert "(flagged only)" in result[0].text
            assert "(including completed)" in result[0].text

    @pytest.mark.asyncio
    async def test_get_tasks_truncates_long_notes(self, sample_tasks):
        """Test that long task notes are truncated in output."""
        with mock.patch.object(server.client, 'get_tasks', return_value=sample_tasks):
            result = await server.call_tool("get_tasks", {})

            assert "..." in result[0].text  # Long note should be truncated

    @pytest.mark.asyncio
    async def test_get_tasks_handles_exception(self):
        """Test error handling when get_tasks raises exception."""
        with mock.patch.object(server.client, 'get_tasks', side_effect=Exception("OmniFocus error")):
            result = await server.call_tool("get_tasks", {})

            assert len(result) == 1
            assert "Error" in result[0].text
            assert "OmniFocus error" in result[0].text


class TestCallToolCompleteTask:
    """Tests for the complete_task tool handler."""

    @pytest.mark.asyncio
    async def test_complete_task_success(self):
        """Test successfully completing a task."""
        with mock.patch.object(server.client, 'complete_task', return_value=True):
            result = await server.call_tool("complete_task", {"task_id": "task-001"})

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "Successfully completed task" in result[0].text
            assert "task-001" in result[0].text
            server.client.complete_task.assert_called_once_with("task-001")

    @pytest.mark.asyncio
    async def test_complete_task_failure(self):
        """Test handling of task completion failure."""
        with mock.patch.object(server.client, 'complete_task', return_value=False):
            result = await server.call_tool("complete_task", {"task_id": "task-001"})

            assert len(result) == 1
            assert "Failed to complete task" in result[0].text
            assert "task-001" in result[0].text

    @pytest.mark.asyncio
    async def test_complete_task_missing_task_id(self):
        """Test completing task without task_id."""
        result = await server.call_tool("complete_task", {})

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "task_id" in result[0].text

    @pytest.mark.asyncio
    async def test_complete_task_handles_exception(self):
        """Test error handling when complete_task raises exception."""
        with mock.patch.object(server.client, 'complete_task', side_effect=Exception("Task not found")):
            result = await server.call_tool("complete_task", {"task_id": "task-001"})

            assert len(result) == 1
            assert "Error" in result[0].text
            assert "Task not found" in result[0].text


class TestCallToolUpdateTask:
    """Tests for the update_task tool handler."""

    @pytest.mark.asyncio
    async def test_update_task_name(self):
        """Test updating task name."""
        with mock.patch.object(server.client, 'update_task', return_value=True):
            result = await server.call_tool("update_task", {
                "task_id": "task-001",
                "name": "Updated Name"
            })

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "Successfully updated task" in result[0].text
            assert "task-001" in result[0].text
            server.client.update_task.assert_called_once_with(
                "task-001",
                name="Updated Name",
                note=None,
                due_date=None,
                defer_date=None,
                flagged=None
            )

    @pytest.mark.asyncio
    async def test_update_task_multiple_fields(self):
        """Test updating multiple task fields."""
        with mock.patch.object(server.client, 'update_task', return_value=True):
            result = await server.call_tool("update_task", {
                "task_id": "task-001",
                "name": "New Name",
                "note": "New note",
                "due_date": "2025-12-25",
                "flagged": True
            })

            assert len(result) == 1
            assert "Successfully updated task" in result[0].text
            assert "name" in result[0].text
            assert "note" in result[0].text
            assert "due_date" in result[0].text
            assert "flagged" in result[0].text

    @pytest.mark.asyncio
    async def test_update_task_failure(self):
        """Test handling of task update failure."""
        with mock.patch.object(server.client, 'update_task', return_value=False):
            result = await server.call_tool("update_task", {
                "task_id": "task-001",
                "name": "New Name"
            })

            assert len(result) == 1
            assert "Failed to update task" in result[0].text
            assert "task-001" in result[0].text

    @pytest.mark.asyncio
    async def test_update_task_missing_task_id(self):
        """Test updating task without task_id."""
        result = await server.call_tool("update_task", {"name": "New Name"})

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "task_id" in result[0].text

    @pytest.mark.asyncio
    async def test_update_task_handles_exception(self):
        """Test error handling when update_task raises exception."""
        with mock.patch.object(server.client, 'update_task', side_effect=Exception("Update failed")):
            result = await server.call_tool("update_task", {
                "task_id": "task-001",
                "name": "New Name"
            })

            assert len(result) == 1
            assert "Error" in result[0].text
            assert "Update failed" in result[0].text


class TestCallToolInboxOperations:
    """Tests for inbox operation tool handlers."""

    @pytest.fixture
    def sample_inbox_tasks(self):
        """Sample inbox tasks data."""
        return [
            {
                "id": "inbox-001",
                "name": "Quick Capture",
                "note": "Need to process",
                "completed": False,
                "flagged": False,
                "dueDate": "",
                "deferDate": "",
                "tags": ""
            },
            {
                "id": "inbox-002",
                "name": "Flagged Item",
                "note": "",
                "completed": False,
                "flagged": True,
                "dueDate": "2025-10-15T17:00:00",
                "deferDate": "",
                "tags": "urgent"
            }
        ]

    @pytest.mark.asyncio
    async def test_get_inbox_tasks_success(self, sample_inbox_tasks):
        """Test getting inbox tasks."""
        with mock.patch.object(server.client, 'get_inbox_tasks', return_value=sample_inbox_tasks):
            result = await server.call_tool("get_inbox_tasks", {})

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "Found 2 inbox tasks" in result[0].text
            assert "Quick Capture" in result[0].text
            assert "🚩 Flagged" in result[0].text

    @pytest.mark.asyncio
    async def test_get_inbox_tasks_empty(self):
        """Test handling of empty inbox."""
        with mock.patch.object(server.client, 'get_inbox_tasks', return_value=[]):
            result = await server.call_tool("get_inbox_tasks", {})

            assert len(result) == 1
            assert "No tasks in inbox" in result[0].text or "0 inbox tasks" in result[0].text

    @pytest.mark.asyncio
    async def test_get_inbox_tasks_handles_exception(self):
        """Test error handling when get_inbox_tasks raises exception."""
        with mock.patch.object(server.client, 'get_inbox_tasks', side_effect=Exception("Inbox error")):
            result = await server.call_tool("get_inbox_tasks", {})

            assert len(result) == 1
            assert "Error" in result[0].text
            assert "Inbox error" in result[0].text

    @pytest.mark.asyncio
    async def test_create_inbox_task_success(self):
        """Test creating inbox task."""
        with mock.patch.object(server.client, 'create_inbox_task', return_value=True):
            result = await server.call_tool("create_inbox_task", {
                "task_name": "Quick capture"
            })

            assert len(result) == 1
            assert "Successfully created inbox task" in result[0].text
            assert "Quick capture" in result[0].text
            server.client.create_inbox_task.assert_called_once_with(
                "Quick capture",
                note=None,
                due_date=None,
                flagged=None
            )

    @pytest.mark.asyncio
    async def test_create_inbox_task_with_properties(self):
        """Test creating inbox task with additional properties."""
        with mock.patch.object(server.client, 'create_inbox_task', return_value=True):
            result = await server.call_tool("create_inbox_task", {
                "task_name": "Important task",
                "note": "Task details",
                "due_date": "2025-10-15",
                "flagged": True
            })

            assert len(result) == 1
            assert "Successfully created inbox task" in result[0].text
            server.client.create_inbox_task.assert_called_once_with(
                "Important task",
                note="Task details",
                due_date="2025-10-15",
                flagged=True
            )

    @pytest.mark.asyncio
    async def test_create_inbox_task_missing_name(self):
        """Test creating inbox task without task_name."""
        result = await server.call_tool("create_inbox_task", {})

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "task_name" in result[0].text

    @pytest.mark.asyncio
    async def test_create_inbox_task_failure(self):
        """Test handling of inbox task creation failure."""
        with mock.patch.object(server.client, 'create_inbox_task', return_value=False):
            result = await server.call_tool("create_inbox_task", {
                "task_name": "Task"
            })

            assert len(result) == 1
            assert "Failed to create inbox task" in result[0].text

    @pytest.mark.asyncio
    async def test_create_inbox_task_handles_exception(self):
        """Test error handling when create_inbox_task raises exception."""
        with mock.patch.object(server.client, 'create_inbox_task', side_effect=Exception("Creation failed")):
            result = await server.call_tool("create_inbox_task", {
                "task_name": "Task"
            })

            assert len(result) == 1
            assert "Error" in result[0].text
            assert "Creation failed" in result[0].text


class TestCallToolTagOperations:
    """Tests for tag operation tool handlers."""

    @pytest.fixture
    def sample_tags(self):
        """Sample tags data."""
        return [
            {"id": "tag-001", "name": "urgent", "status": "active"},
            {"id": "tag-002", "name": "work", "status": "active"},
            {"id": "tag-003", "name": "personal", "status": "active"}
        ]

    @pytest.mark.asyncio
    async def test_get_tags_success(self, sample_tags):
        """Test getting all tags."""
        with mock.patch.object(server.client, 'get_tags', return_value=sample_tags):
            result = await server.call_tool("get_tags", {})

            assert len(result) == 1
            assert isinstance(result[0], TextContent)
            assert "Found 3 tags" in result[0].text
            assert "urgent" in result[0].text
            assert "work" in result[0].text
            assert "personal" in result[0].text

    @pytest.mark.asyncio
    async def test_get_tags_empty(self):
        """Test handling of empty tags list."""
        with mock.patch.object(server.client, 'get_tags', return_value=[]):
            result = await server.call_tool("get_tags", {})

            assert len(result) == 1
            assert "No tags found" in result[0].text or "0 tags" in result[0].text

    @pytest.mark.asyncio
    async def test_get_tags_handles_exception(self):
        """Test error handling when get_tags raises exception."""
        with mock.patch.object(server.client, 'get_tags', side_effect=Exception("Tags error")):
            result = await server.call_tool("get_tags", {})

            assert len(result) == 1
            assert "Error" in result[0].text
            assert "Tags error" in result[0].text

    @pytest.mark.asyncio
    async def test_add_tag_to_task_success(self):
        """Test adding tag to task."""
        with mock.patch.object(server.client, 'add_tag_to_task', return_value=True):
            result = await server.call_tool("add_tag_to_task", {
                "task_id": "task-001",
                "tag_name": "urgent"
            })

            assert len(result) == 1
            assert "Successfully added tag 'urgent' to task" in result[0].text
            assert "task-001" in result[0].text
            server.client.add_tag_to_task.assert_called_once_with("task-001", "urgent")

    @pytest.mark.asyncio
    async def test_add_tag_to_task_missing_task_id(self):
        """Test adding tag without task_id."""
        result = await server.call_tool("add_tag_to_task", {"tag_name": "urgent"})

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "task_id" in result[0].text

    @pytest.mark.asyncio
    async def test_add_tag_to_task_missing_tag_name(self):
        """Test adding tag without tag_name."""
        result = await server.call_tool("add_tag_to_task", {"task_id": "task-001"})

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "tag_name" in result[0].text

    @pytest.mark.asyncio
    async def test_add_tag_to_task_failure(self):
        """Test handling of tag addition failure."""
        with mock.patch.object(server.client, 'add_tag_to_task', return_value=False):
            result = await server.call_tool("add_tag_to_task", {
                "task_id": "task-001",
                "tag_name": "urgent"
            })

            assert len(result) == 1
            assert "Failed to add tag" in result[0].text

    @pytest.mark.asyncio
    async def test_add_tag_to_task_handles_exception(self):
        """Test error handling when add_tag_to_task raises exception."""
        with mock.patch.object(server.client, 'add_tag_to_task', side_effect=Exception("Tag not found")):
            result = await server.call_tool("add_tag_to_task", {
                "task_id": "task-001",
                "tag_name": "urgent"
            })

            assert len(result) == 1
            assert "Error" in result[0].text
            assert "Tag not found" in result[0].text


class TestCallToolAddNote:
    """Tests for the add_note tool handler."""

    @pytest.mark.asyncio
    async def test_add_note_success(self):
        """Test successful note addition."""
        with mock.patch.object(server.client, 'add_note', return_value=True):
            result = await server.call_tool("add_note", {
                "project_id": "proj-001",
                "note_text": "Additional note"
            })

            assert len(result) == 1
            assert "Successfully added note" in result[0].text
            assert "proj-001" in result[0].text

    @pytest.mark.asyncio
    async def test_add_note_failure(self):
        """Test handling of note addition failure."""
        with mock.patch.object(server.client, 'add_note', return_value=False):
            result = await server.call_tool("add_note", {
                "project_id": "invalid-id",
                "note_text": "Note"
            })

            assert len(result) == 1
            assert "Failed to add note" in result[0].text

    @pytest.mark.asyncio
    async def test_add_note_missing_project_id(self):
        """Test adding note without project_id."""
        result = await server.call_tool("add_note", {
            "note_text": "Note"
        })

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "project_id" in result[0].text

    @pytest.mark.asyncio
    async def test_add_note_missing_note_text(self):
        """Test adding note without note_text."""
        result = await server.call_tool("add_note", {
            "project_id": "proj-001"
        })

        assert len(result) == 1
        assert "Error" in result[0].text
        assert "note_text" in result[0].text

    @pytest.mark.asyncio
    async def test_add_note_with_long_text(self):
        """Test adding very long note."""
        with mock.patch.object(server.client, 'add_note', return_value=True):
            long_note = "x" * 5000
            result = await server.call_tool("add_note", {
                "project_id": "proj-001",
                "note_text": long_note
            })

            assert len(result) == 1
            assert "Successfully added note" in result[0].text

    @pytest.mark.asyncio
    async def test_add_note_handles_exception(self):
        """Test error handling when add_note raises exception."""
        with mock.patch.object(server.client, 'add_note', side_effect=Exception("Add failed")):
            result = await server.call_tool("add_note", {
                "project_id": "proj-001",
                "note_text": "Note"
            })

            assert len(result) == 1
            assert "Error" in result[0].text


class TestCallToolUnknown:
    """Tests for unknown tool handling."""

    @pytest.mark.asyncio
    async def test_unknown_tool_name(self):
        """Test handling of unknown tool names."""
        result = await server.call_tool("nonexistent_tool", {})

        assert len(result) == 1
        assert "Unknown tool" in result[0].text
        assert "nonexistent_tool" in result[0].text


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    @pytest.mark.asyncio
    async def test_tool_with_none_arguments(self):
        """Test tool call with None as arguments."""
        with mock.patch.object(server.client, 'get_projects', return_value=[]):
            result = await server.call_tool("get_projects", None)
            # Should handle None gracefully
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_unicode_in_tool_arguments(self):
        """Test handling Unicode in tool arguments."""
        with mock.patch.object(server.client, 'add_task', return_value=True):
            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "タスク 🎉",
                "note": "メモ"
            })

            assert len(result) == 1
            assert "Successfully added task" in result[0].text

    @pytest.mark.asyncio
    async def test_empty_folder_path(self):
        """Test handling of projects with empty folder paths."""
        projects = [{
            "id": "proj-001",
            "name": "Root Project",
            "note": "Note",
            "status": "active",
            "folderPath": ""
        }]

        with mock.patch.object(server.client, 'get_projects', return_value=projects):
            result = await server.call_tool("get_projects", {})

            assert len(result) == 1
            assert "(root)" in result[0].text  # Empty folder path should show as (root)

    @pytest.mark.asyncio
    async def test_project_with_markdown_in_name(self):
        """Test handling of projects with markdown-like characters in name."""
        projects = [{
            "id": "proj-001",
            "name": "**Bold** _italic_ `code`",
            "note": "# Header",
            "status": "active",
            "folderPath": "Test"
        }]

        with mock.patch.object(server.client, 'get_projects', return_value=projects):
            result = await server.call_tool("get_projects", {})

            assert len(result) == 1
            # Should not break markdown formatting
            assert result[0].text
