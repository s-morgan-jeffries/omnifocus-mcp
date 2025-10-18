"""Server tests for get_tasks() enhancements (Phase 3.1)."""
import pytest
from unittest import mock
import omnifocus_mcp.server_fastmcp as server

class TestGetTasksServerEnhancements:
    """Server tests for get_tasks() new parameters."""
    
    def test_get_tasks_with_task_id_parameter(self):
        """Server: get_tasks(task_id=X) passes to client."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_tasks.return_value = [
                {"id": "task-001", "name": "Task", "completed": False}
            ]
            mock_get_client.return_value = mock_client

            get_tasks = server.get_tasks.fn
            result = get_tasks(task_id="task-001")

            # Verify task_id was passed correctly
            call_kwargs = mock_client.get_tasks.call_args[1]
            assert call_kwargs['task_id'] == "task-001"
            assert isinstance(result, str)
            assert "task-001" in result
    
    def test_get_tasks_with_parent_task_id_parameter(self):
        """Server: get_tasks(parent_task_id=X) passes to client."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_tasks.return_value = []
            mock_get_client.return_value = mock_client

            get_tasks = server.get_tasks.fn
            result = get_tasks(parent_task_id="parent-001")

            # Verify parent_task_id was passed correctly
            call_kwargs = mock_client.get_tasks.call_args[1]
            assert call_kwargs['parent_task_id'] == "parent-001"
            assert isinstance(result, str)
    
    def test_get_tasks_with_include_full_notes_parameter(self):
        """Server: get_tasks(include_full_notes=True) passes to client."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_tasks.return_value = []
            mock_get_client.return_value = mock_client

            get_tasks = server.get_tasks.fn
            result = get_tasks(include_full_notes=True)

            # Verify include_full_notes was passed correctly
            call_kwargs = mock_client.get_tasks.call_args[1]
            assert call_kwargs['include_full_notes'] is True
            assert isinstance(result, str)
