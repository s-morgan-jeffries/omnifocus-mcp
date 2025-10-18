"""Tests for update_projects() MCP tool (NEW API - Phase 2, Function 2.2, Server Layer).

Tests the MCP server layer that wraps the client update_projects() function.
"""
import pytest
from unittest import mock

# Import the MCP tool function
import omnifocus_mcp.server_fastmcp as server


class TestUpdateProjectsServerRedesign:
    """Tests for update_projects() MCP tool (NEW API - Phase 2, Server Layer)."""

    def test_update_projects_batch_status(self):
        """Server: update_projects() MCP tool can set status on multiple projects."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_projects.return_value = {
                "updated_count": 3,
                "failed_count": 0,
                "updated_ids": ["proj-001", "proj-002", "proj-003"],
                "failures": []
            }
            mock_get_client.return_value = mock_client

            # Get the actual MCP tool function
            update_projects = server.update_projects.fn

            result = update_projects(
                project_ids=["proj-001", "proj-002", "proj-003"],
                status="active"
            )

            # Verify client was called correctly
            mock_client.update_projects.assert_called_once()
            call_kwargs = mock_client.update_projects.call_args[1]
            assert call_kwargs["project_ids"] == ["proj-001", "proj-002", "proj-003"]
            assert call_kwargs["status"] == "active"

            # Verify human-readable response
            assert isinstance(result, str)
            assert "3" in result  # Should mention count
            assert "success" in result.lower() or "updated" in result.lower()

    def test_update_projects_single_id_string(self):
        """Server: update_projects() MCP tool accepts single ID as string (Union type)."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_projects.return_value = {
                "updated_count": 1,
                "failed_count": 0,
                "updated_ids": ["proj-001"],
                "failures": []
            }
            mock_get_client.return_value = mock_client

            update_projects = server.update_projects.fn

            result = update_projects(project_ids="proj-001", status="on_hold")

            # Should pass single string to client
            call_kwargs = mock_client.update_projects.call_args[1]
            assert call_kwargs["project_ids"] == "proj-001"

            assert isinstance(result, str)
            assert "1" in result

    def test_update_projects_multiple_fields(self):
        """Server: update_projects() MCP tool can update multiple fields."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_projects.return_value = {
                "updated_count": 2,
                "failed_count": 0,
                "updated_ids": ["proj-001", "proj-002"],
                "failures": []
            }
            mock_get_client.return_value = mock_client

            update_projects = server.update_projects.fn

            result = update_projects(
                project_ids=["proj-001", "proj-002"],
                status="active",
                sequential="true",
                review_interval_weeks=4
            )

            call_kwargs = mock_client.update_projects.call_args[1]
            assert call_kwargs["status"] == "active"
            assert call_kwargs["sequential"] is True  # Converted from string
            assert call_kwargs["review_interval_weeks"] == 4

            assert "2" in result

    def test_update_projects_partial_failures(self):
        """Server: update_projects() MCP tool reports partial failures."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_projects.return_value = {
                "updated_count": 2,
                "failed_count": 1,
                "updated_ids": ["proj-001", "proj-003"],
                "failures": [{"project_id": "proj-002", "error": "Project not found"}]
            }
            mock_get_client.return_value = mock_client

            update_projects = server.update_projects.fn

            result = update_projects(
                project_ids=["proj-001", "proj-002", "proj-003"],
                status="done"
            )

            assert isinstance(result, str)
            # Should mention both successes and failures
            assert "2" in result  # Updated count
            assert "1" in result  # Failed count
            assert "proj-002" in result  # Failed project ID

    def test_update_projects_handles_client_exception(self):
        """Server: update_projects() MCP tool handles client exceptions gracefully."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_projects.side_effect = ValueError("Invalid status")
            mock_get_client.return_value = mock_client

            update_projects = server.update_projects.fn

            result = update_projects(
                project_ids=["proj-001"],
                status="invalid-status"
            )

            assert isinstance(result, str)
            assert "error" in result.lower()
            assert "invalid status" in result.lower()

    def test_update_projects_sequential_bool_conversion(self):
        """Server: update_projects() MCP tool converts sequential string to bool."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_projects.return_value = {
                "updated_count": 1,
                "failed_count": 0,
                "updated_ids": ["proj-001"],
                "failures": []
            }
            mock_get_client.return_value = mock_client

            update_projects = server.update_projects.fn

            # Test with "true"
            result = update_projects(project_ids="proj-001", sequential="true")
            call_kwargs = mock_client.update_projects.call_args[1]
            assert call_kwargs["sequential"] is True

            # Test with "false"
            result = update_projects(project_ids="proj-001", sequential="false")
            call_kwargs = mock_client.update_projects.call_args[1]
            assert call_kwargs["sequential"] is False

            # Test with bool (from tests)
            result = update_projects(project_ids="proj-001", sequential=True)
            call_kwargs = mock_client.update_projects.call_args[1]
            assert call_kwargs["sequential"] is True

    def test_update_projects_returns_human_readable_response(self):
        """Server: update_projects() MCP tool returns human-readable response."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_projects.return_value = {
                "updated_count": 5,
                "failed_count": 0,
                "updated_ids": ["p1", "p2", "p3", "p4", "p5"],
                "failures": []
            }
            mock_get_client.return_value = mock_client

            update_projects = server.update_projects.fn

            result = update_projects(
                project_ids=["p1", "p2", "p3", "p4", "p5"],
                status="active"
            )

            assert isinstance(result, str)
            # Should be user-friendly, not raw JSON
            assert "5" in result
            assert "project" in result.lower()
