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

        assert len(tools) == 4
        tool_names = [tool.name for tool in tools]
        assert "get_projects" in tool_names
        assert "search_projects" in tool_names
        assert "add_task" in tool_names
        assert "add_note" in tool_names

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
