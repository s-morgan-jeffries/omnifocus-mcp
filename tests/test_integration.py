"""Integration tests for the MCP server.

These tests verify end-to-end functionality with mocked AppleScript execution.
They test the full flow from MCP tool call through the client to AppleScript.
"""
import json
import pytest
from unittest import mock

from omnifocus_mcp import server
from omnifocus_mcp.omnifocus_client import OmniFocusClient


class TestIntegration:
    """Integration tests with mocked AppleScript."""

    @pytest.fixture
    def mock_applescript_projects(self):
        """Mock AppleScript output for get_projects."""
        return json.dumps([
            {
                "id": "proj-001",
                "name": "Integration Test Project",
                "note": "Testing the full stack",
                "status": "active",
                "folderPath": "Test > Integration"
            }
        ])

    @pytest.mark.asyncio
    async def test_full_flow_get_projects(self, mock_applescript_projects):
        """Test full flow from MCP call to AppleScript and back."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = mock_applescript_projects

            # Call through MCP server
            result = await server.call_tool("get_projects", {})

            # Verify AppleScript was called
            assert mock_run.called
            assert "tell application \"OmniFocus\"" in mock_run.call_args[0][0]

            # Verify result
            assert len(result) == 1
            assert "Integration Test Project" in result[0].text
            assert "proj-001" in result[0].text

    @pytest.mark.asyncio
    async def test_full_flow_search_then_add_task(self, mock_applescript_projects):
        """Test searching for a project and then adding a task to it."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # First call: search projects
            mock_run.return_value = mock_applescript_projects
            search_result = await server.call_tool("search_projects", {"query": "Integration"})

            assert "Integration Test Project" in search_result[0].text

            # Second call: add task to found project
            mock_run.return_value = "true"
            add_result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Test Task",
                "note": "Added via integration test"
            })

            assert "Successfully added task" in add_result[0].text

            # Verify both AppleScript calls were made
            assert mock_run.call_count == 2

    @pytest.mark.asyncio
    async def test_full_flow_with_special_characters(self):
        """Test full flow with special characters throughout."""
        special_projects = json.dumps([{
            "id": "proj-special",
            "name": 'Project with "quotes" and \\backslashes',
            "note": "Note with\nnewlines\tand tabs",
            "status": "active",
            "folderPath": "Test > Special \"Chars\""
        }])

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # Get projects with special characters
            mock_run.return_value = special_projects
            result = await server.call_tool("get_projects", {})
            assert 'quotes' in result[0].text

            # Add task with special characters
            mock_run.return_value = "true"
            add_result = await server.call_tool("add_task", {
                "project_id": "proj-special",
                "task_name": 'Task with "quotes"',
                "note": "Note\nwith\nnewlines"
            })
            assert "Successfully added task" in add_result[0].text

    @pytest.mark.asyncio
    async def test_error_propagation(self):
        """Test that errors propagate correctly through the stack."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # Simulate AppleScript error
            mock_run.return_value = ""

            result = await server.call_tool("get_projects", {})

            # Error should be caught and returned as text
            assert "Error" in result[0].text

    @pytest.mark.asyncio
    async def test_multiple_concurrent_operations(self, mock_applescript_projects):
        """Test handling multiple operations in sequence."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # Operation 1: Get projects
            mock_run.return_value = mock_applescript_projects
            result1 = await server.call_tool("get_projects", {})
            assert len(result1) == 1

            # Operation 2: Search projects
            mock_run.return_value = mock_applescript_projects
            result2 = await server.call_tool("search_projects", {"query": "Test"})
            assert len(result2) == 1

            # Operation 3: Add task
            mock_run.return_value = "true"
            result3 = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Task 1"
            })
            assert "Successfully" in result3[0].text

            # Operation 4: Add note
            mock_run.return_value = "true"
            result4 = await server.call_tool("add_note", {
                "project_id": "proj-001",
                "note_text": "Note 1"
            })
            assert "Successfully" in result4[0].text

            # Verify all operations executed
            assert mock_run.call_count == 4

    @pytest.mark.asyncio
    async def test_empty_database_scenario(self):
        """Test behavior when OmniFocus has no projects."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "[]"

            # Get projects should return empty
            result = await server.call_tool("get_projects", {})
            assert "Found 0 active projects" in result[0].text

            # Search should return no results
            result = await server.call_tool("search_projects", {"query": "anything"})
            assert "No projects found" in result[0].text

    @pytest.mark.asyncio
    async def test_large_dataset(self):
        """Test handling of large number of projects."""
        # Create 100 projects
        large_dataset = json.dumps([
            {
                "id": f"proj-{i:03d}",
                "name": f"Project {i}",
                "note": f"Note for project {i}",
                "status": "active",
                "folderPath": f"Folder {i // 10}"
            }
            for i in range(100)
        ])

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = large_dataset

            result = await server.call_tool("get_projects", {})

            assert "Found 100 active projects" in result[0].text
            # Verify some project names are in output
            assert "Project" in result[0].text


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    @pytest.mark.asyncio
    async def test_project_review_workflow(self):
        """Test a typical project review workflow."""
        projects = json.dumps([
            {
                "id": "work-001",
                "name": "Q4 Planning",
                "note": "Review goals and metrics",
                "status": "active",
                "folderPath": "Work > Planning"
            },
            {
                "id": "work-002",
                "name": "Team 1-on-1s",
                "note": "Weekly meetings",
                "status": "active",
                "folderPath": "Work > Management"
            }
        ])

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # Step 1: Review all projects
            mock_run.return_value = projects
            result = await server.call_tool("get_projects", {})
            assert "Q4 Planning" in result[0].text

            # Step 2: Search for planning-related projects
            result = await server.call_tool("search_projects", {"query": "planning"})
            assert "Q4 Planning" in result[0].text

            # Step 3: Add follow-up task
            mock_run.return_value = "true"
            result = await server.call_tool("add_task", {
                "project_id": "work-001",
                "task_name": "Review Q3 metrics",
                "note": "Compare against Q4 goals"
            })
            assert "Successfully" in result[0].text

            # Step 4: Add note with insights
            result = await server.call_tool("add_note", {
                "project_id": "work-001",
                "note_text": "Key insight: Focus on team productivity metrics"
            })
            assert "Successfully" in result[0].text

    @pytest.mark.asyncio
    async def test_handling_failed_task_creation(self):
        """Test graceful handling when task creation fails."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # Simulate task creation failure
            mock_run.return_value = "false: Project not found"

            result = await server.call_tool("add_task", {
                "project_id": "nonexistent-id",
                "task_name": "This will fail"
            })

            assert "Error" in result[0].text

    @pytest.mark.asyncio
    async def test_unicode_and_emoji_support(self):
        """Test support for Unicode and emoji in all fields."""
        unicode_projects = json.dumps([{
            "id": "unicode-001",
            "name": "プロジェクト 🎉",
            "note": "メモ with emoji 🚀",
            "status": "active",
            "folderPath": "フォルダ > サブフォルダ"
        }])

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = unicode_projects

            # Get projects with Unicode
            result = await server.call_tool("get_projects", {})
            assert "🎉" in result[0].text

            # Add task with Unicode
            mock_run.return_value = "true"
            result = await server.call_tool("add_task", {
                "project_id": "unicode-001",
                "task_name": "タスク 💡",
                "note": "詳細情報"
            })
            assert "Successfully" in result[0].text


class TestClientState:
    """Test that client maintains proper state across calls."""

    @pytest.mark.asyncio
    async def test_client_instance_reused(self):
        """Test that the same client instance is used across calls."""
        # The server module creates a single client instance
        client1 = server.client
        client2 = server.client

        assert client1 is client2

    @pytest.mark.asyncio
    async def test_client_survives_errors(self):
        """Test that client remains functional after errors."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # First call fails
            mock_run.return_value = ""
            result1 = await server.call_tool("get_projects", {})
            assert "Error" in result1[0].text

            # Second call succeeds
            mock_run.return_value = "[]"
            result2 = await server.call_tool("get_projects", {})
            assert "Found 0" in result2[0].text

            # Client should still be functional
            assert server.client is not None
