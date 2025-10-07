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


class TestInboxOperations:
    """Integration tests for inbox operations."""

    @pytest.fixture
    def mock_inbox_tasks(self):
        """Mock AppleScript output for inbox tasks."""
        return json.dumps([
            {
                "id": "inbox-001",
                "name": "Quick capture task",
                "note": "Remember to process this",
                "completed": False,
                "flagged": True,
                "dueDate": "2025-10-15T17:00:00",
                "deferDate": "",
                "tags": "urgent"
            },
            {
                "id": "inbox-002",
                "name": "Another inbox item",
                "note": "",
                "completed": False,
                "flagged": False,
                "dueDate": "",
                "deferDate": "",
                "tags": ""
            }
        ])

    @pytest.mark.asyncio
    async def test_get_inbox_tasks_flow(self, mock_inbox_tasks):
        """Test getting inbox tasks end-to-end."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = mock_inbox_tasks

            result = await server.call_tool("get_inbox_tasks", {})

            assert "Found 2 inbox tasks" in result[0].text
            assert "Quick capture task" in result[0].text
            assert "inbox-001" in result[0].text
            assert "AppleScript" in mock_run.call_args[0][0]

    @pytest.mark.asyncio
    async def test_create_inbox_task_basic(self):
        """Test creating basic inbox task."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = await server.call_tool("create_inbox_task", {
                "task_name": "Quick inbox item"
            })

            assert "Successfully created inbox task" in result[0].text
            assert "Quick inbox item" in result[0].text

    @pytest.mark.asyncio
    async def test_create_inbox_task_with_all_properties(self):
        """Test creating inbox task with all properties."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = await server.call_tool("create_inbox_task", {
                "task_name": "Important inbox task",
                "note": "Detailed description",
                "due_date": "2025-10-20T14:00:00",
                "flagged": True
            })

            assert "Successfully created inbox task" in result[0].text
            # Verify AppleScript received all parameters
            call_script = mock_run.call_args[0][0]
            assert "Important inbox task" in call_script
            assert "Detailed description" in call_script
            assert "October 20, 2025" in call_script
            assert "flagged:true" in call_script

    @pytest.mark.asyncio
    async def test_inbox_workflow_capture_and_review(self, mock_inbox_tasks):
        """Test realistic inbox workflow: capture then review."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # Step 1: Capture multiple quick items
            mock_run.return_value = "true"
            for task_name in ["Call dentist", "Buy groceries", "Review report"]:
                result = await server.call_tool("create_inbox_task", {
                    "task_name": task_name
                })
                assert "Successfully" in result[0].text

            # Step 2: Review inbox
            mock_run.return_value = mock_inbox_tasks
            result = await server.call_tool("get_inbox_tasks", {})
            assert "Found 2 inbox tasks" in result[0].text

            assert mock_run.call_count == 4  # 3 creates + 1 get

    @pytest.mark.asyncio
    async def test_empty_inbox(self):
        """Test handling of empty inbox."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "[]"

            result = await server.call_tool("get_inbox_tasks", {})
            assert "No tasks in inbox" in result[0].text or "Found 0" in result[0].text


class TestTagOperations:
    """Integration tests for tag operations."""

    @pytest.fixture
    def mock_tags(self):
        """Mock AppleScript output for tags."""
        return json.dumps([
            {"id": "tag-001", "name": "urgent", "status": "active"},
            {"id": "tag-002", "name": "work", "status": "active"},
            {"id": "tag-003", "name": "personal", "status": "active"},
            {"id": "tag-004", "name": "waiting", "status": "active"}
        ])

    @pytest.fixture
    def mock_tasks(self):
        """Mock AppleScript output for tasks."""
        return json.dumps([
            {
                "id": "task-001",
                "name": "Task without tags",
                "note": "",
                "completed": False,
                "flagged": False,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "",
                "deferDate": "",
                "completionDate": "",
                "tags": ""
            }
        ])

    @pytest.mark.asyncio
    async def test_get_tags_flow(self, mock_tags):
        """Test getting all tags end-to-end."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = mock_tags

            result = await server.call_tool("get_tags", {})

            assert "Found 4 tags" in result[0].text
            assert "urgent" in result[0].text
            assert "work" in result[0].text

    @pytest.mark.asyncio
    async def test_add_tag_to_task_flow(self):
        """Test adding tag to task end-to-end."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = await server.call_tool("add_tag_to_task", {
                "task_id": "task-001",
                "tag_name": "urgent"
            })

            assert "Successfully added tag 'urgent'" in result[0].text
            assert "task-001" in result[0].text

    @pytest.mark.asyncio
    async def test_tag_organization_workflow(self, mock_tags, mock_tasks):
        """Test realistic tag organization workflow."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # Step 1: Review available tags
            mock_run.return_value = mock_tags
            result = await server.call_tool("get_tags", {})
            assert "Found 4 tags" in result[0].text

            # Step 2: Get tasks to organize
            mock_run.return_value = mock_tasks
            result = await server.call_tool("get_tasks", {})
            assert "task-001" in result[0].text

            # Step 3: Add tags to organize
            mock_run.return_value = "true"
            result = await server.call_tool("add_tag_to_task", {
                "task_id": "task-001",
                "tag_name": "work"
            })
            assert "Successfully" in result[0].text

            result = await server.call_tool("add_tag_to_task", {
                "task_id": "task-001",
                "tag_name": "urgent"
            })
            assert "Successfully" in result[0].text

            assert mock_run.call_count == 4  # 1 get_tags + 1 get_tasks + 2 add_tag

    @pytest.mark.asyncio
    async def test_tag_with_special_characters(self):
        """Test adding tag with special characters."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = await server.call_tool("add_tag_to_task", {
                "task_id": "task-001",
                "tag_name": "high-priority/urgent"
            })

            assert "Successfully" in result[0].text
            call_script = mock_run.call_args[0][0]
            assert "high-priority/urgent" in call_script


class TestTaskLifecycle:
    """Integration tests for task lifecycle operations."""

    @pytest.fixture
    def mock_tasks_with_incomplete(self):
        """Mock tasks including incomplete ones."""
        return json.dumps([
            {
                "id": "task-001",
                "name": "Active task",
                "note": "Needs completion",
                "completed": False,
                "flagged": True,
                "projectId": "proj-001",
                "projectName": "Test Project",
                "dueDate": "2025-10-15T17:00:00",
                "deferDate": "",
                "completionDate": "",
                "tags": "urgent"
            }
        ])

    @pytest.mark.asyncio
    async def test_complete_task_flow(self, mock_tasks_with_incomplete):
        """Test completing task end-to-end."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # Step 1: Get tasks to find one to complete
            mock_run.return_value = mock_tasks_with_incomplete
            result = await server.call_tool("get_tasks", {})
            assert "Active task" in result[0].text
            assert "task-001" in result[0].text

            # Step 2: Complete the task
            mock_run.return_value = "true"
            result = await server.call_tool("complete_task", {
                "task_id": "task-001"
            })
            assert "Successfully completed task" in result[0].text
            assert "task-001" in result[0].text

    @pytest.mark.asyncio
    async def test_update_task_flow(self, mock_tasks_with_incomplete):
        """Test updating task end-to-end."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # Step 1: Get task to update
            mock_run.return_value = mock_tasks_with_incomplete
            result = await server.call_tool("get_tasks", {})
            assert "task-001" in result[0].text

            # Step 2: Update task name and note
            mock_run.return_value = "true"
            result = await server.call_tool("update_task", {
                "task_id": "task-001",
                "name": "Updated task name",
                "note": "Updated with more details"
            })
            assert "Successfully updated task" in result[0].text

    @pytest.mark.asyncio
    async def test_update_task_dates(self):
        """Test updating task dates."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = await server.call_tool("update_task", {
                "task_id": "task-001",
                "due_date": "2025-12-31T23:59:00",
                "defer_date": "2025-12-01T09:00:00"
            })

            assert "Successfully updated task" in result[0].text
            call_script = mock_run.call_args[0][0]
            assert "December 31, 2025" in call_script
            assert "December 01, 2025" in call_script

    @pytest.mark.asyncio
    async def test_update_task_flagged_status(self):
        """Test updating task flagged status."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = await server.call_tool("update_task", {
                "task_id": "task-001",
                "flagged": True
            })

            assert "Successfully updated task" in result[0].text
            call_script = mock_run.call_args[0][0]
            assert "flagged" in call_script

    @pytest.mark.asyncio
    async def test_task_review_and_update_workflow(self, mock_tasks_with_incomplete):
        """Test realistic task review and update workflow."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # Step 1: Get tasks for review
            mock_run.return_value = mock_tasks_with_incomplete
            result = await server.call_tool("get_tasks", {
                "flagged_only": True
            })
            assert "Active task" in result[0].text

            # Step 2: Update task with new information
            mock_run.return_value = "true"
            result = await server.call_tool("update_task", {
                "task_id": "task-001",
                "note": "Added notes from meeting",
                "due_date": "2025-10-20T17:00:00"
            })
            assert "Successfully" in result[0].text

            # Step 3: Add tag for context
            result = await server.call_tool("add_tag_to_task", {
                "task_id": "task-001",
                "tag_name": "waiting"
            })
            assert "Successfully" in result[0].text

            assert mock_run.call_count == 3


class TestEnhancedEdgeCases:
    """Enhanced edge case testing."""

    @pytest.mark.asyncio
    async def test_date_boundary_past_date(self):
        """Test task with past due date."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Overdue task",
                "due_date": "2020-01-01"
            })

            assert "Successfully" in result[0].text
            # OmniFocus should accept past dates

    @pytest.mark.asyncio
    async def test_date_boundary_far_future(self):
        """Test task with far future date."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Long-term goal",
                "due_date": "2030-12-31T23:59:00"
            })

            assert "Successfully" in result[0].text

    @pytest.mark.asyncio
    async def test_defer_date_after_due_date(self):
        """Test task where defer date is after due date (edge case)."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            # This is logically odd but should still work
            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Task with odd dates",
                "due_date": "2025-10-15",
                "defer_date": "2025-10-20"  # Defer after due
            })

            # Should succeed - OmniFocus allows this
            assert "Successfully" in result[0].text

    @pytest.mark.asyncio
    async def test_task_with_only_defer_date(self):
        """Test task with defer date but no due date."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Task to defer",
                "defer_date": "2025-11-01"
            })

            assert "Successfully" in result[0].text

    @pytest.mark.asyncio
    async def test_multiple_tags_on_task(self):
        """Test adding multiple tags to a task."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            # Create task with initial tags
            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Multi-tagged task",
                "tags": ["urgent", "work", "waiting", "high-priority"]
            })

            assert "Successfully" in result[0].text
            call_script = mock_run.call_args[0][0]
            assert "urgent" in call_script
            assert "work" in call_script
            assert "waiting" in call_script
            assert "high-priority" in call_script

    @pytest.mark.asyncio
    async def test_very_long_tag_list(self):
        """Test task with many tags (10+ tags)."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            many_tags = [f"tag-{i}" for i in range(15)]
            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Task with many tags",
                "tags": many_tags
            })

            assert "Successfully" in result[0].text

    @pytest.mark.asyncio
    async def test_extremely_long_note(self):
        """Test task with very long note (5000+ characters)."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            long_note = "This is a detailed note. " * 200  # ~5000 chars
            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Task with long note",
                "note": long_note
            })

            assert "Successfully" in result[0].text

    @pytest.mark.asyncio
    async def test_deep_folder_hierarchy(self):
        """Test project in deep folder hierarchy."""
        deep_projects = json.dumps([{
            "id": "deep-001",
            "name": "Deeply nested project",
            "note": "In a deep hierarchy",
            "status": "active",
            "folderPath": "Level1 > Level2 > Level3 > Level4 > Level5"
        }])

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = deep_projects

            result = await server.call_tool("get_projects", {})
            assert "Level5" in result[0].text

    @pytest.mark.asyncio
    async def test_rapid_task_creation(self):
        """Test creating multiple tasks rapidly to same project."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            # Simulate rapid task creation
            for i in range(10):
                result = await server.call_tool("add_task", {
                    "project_id": "proj-001",
                    "task_name": f"Rapid task {i}"
                })
                assert "Successfully" in result[0].text

            assert mock_run.call_count == 10

    @pytest.mark.asyncio
    async def test_mixed_operations_sequence(self):
        """Test sequence of mixed read/write operations."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # Create
            mock_run.return_value = "true"
            await server.call_tool("create_inbox_task", {"task_name": "Task 1"})

            # Read
            mock_run.return_value = json.dumps([])
            await server.call_tool("get_projects", {})

            # Update
            mock_run.return_value = "true"
            await server.call_tool("update_task", {
                "task_id": "task-001",
                "name": "Updated"
            })

            # Read
            mock_run.return_value = json.dumps([])
            await server.call_tool("get_inbox_tasks", {})

            # Complete
            mock_run.return_value = "true"
            await server.call_tool("complete_task", {"task_id": "task-001"})

            assert mock_run.call_count == 5

    @pytest.mark.asyncio
    async def test_empty_string_edge_cases(self):
        """Test operations with empty strings."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            # Empty note is allowed
            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Task without note",
                "note": ""
            })
            assert "Successfully" in result[0].text

    @pytest.mark.asyncio
    async def test_update_task_clear_dates(self):
        """Test clearing task dates by updating to empty string."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = await server.call_tool("update_task", {
                "task_id": "task-001",
                "due_date": "",  # Clear due date
                "defer_date": ""  # Clear defer date
            })

            assert "Successfully" in result[0].text
            call_script = mock_run.call_args[0][0]
            assert "missing value" in call_script  # AppleScript for null

    @pytest.mark.asyncio
    async def test_large_number_of_projects(self):
        """Test handling 500 projects."""
        large_dataset = json.dumps([
            {
                "id": f"proj-{i:04d}",
                "name": f"Project {i}",
                "note": f"Note {i}",
                "status": "active",
                "folderPath": f"Folder {i // 50}"
            }
            for i in range(500)
        ])

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = large_dataset

            result = await server.call_tool("get_projects", {})
            assert "Found 500 active projects" in result[0].text

    @pytest.mark.asyncio
    async def test_task_with_all_properties_maximum(self):
        """Test task with every possible property set to maximum values."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = await server.call_tool("add_task", {
                "project_id": "proj-001",
                "task_name": "Maximum properties task with a very long name that tests the limits",
                "note": "Very detailed note " * 100,
                "due_date": "2030-12-31T23:59:59",
                "defer_date": "2025-01-01T00:00:00",
                "flagged": True,
                "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"]
            })

            assert "Successfully" in result[0].text
