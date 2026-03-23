"""Tests for update_projects() MCP tool (unified Pydantic model, #513).

Tests the new unified update_projects() that accepts list[ProjectUpdate],
replacing the old batch-same-values version.
"""
import pytest
from unittest import mock

# Import the MCP tool function
import omnifocus_mcp.server_fastmcp as server


class TestUpdateProjectsUnified:
    """Tests for unified update_projects() with list[ProjectUpdate] (#513)."""

    def test_single_item(self):
        """Single project update returns detailed format."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "p1",
                "updated_fields": ["status"]
            }
            mock_get_client.return_value = mock_client

            result = server.update_projects(projects=[{"id": "p1", "status": "on_hold"}])

            mock_client.update_project.assert_called_once_with(
                project_id="p1",
                status="on_hold",
            )
            assert isinstance(result, str)
            assert "p1" in result
            assert "success" in result.lower() or "updated" in result.lower()

    def test_multiple_items_different_fields(self):
        """Multiple projects with different fields each."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.side_effect = [
                {
                    "success": True,
                    "project_id": "p1",
                    "updated_fields": ["status"]
                },
                {
                    "success": True,
                    "project_id": "p2",
                    "updated_fields": ["project_name"]
                },
            ]
            mock_get_client.return_value = mock_client

            result = server.update_projects(projects=[
                {"id": "p1", "status": "on_hold"},
                {"id": "p2", "project_name": "Renamed"},
            ])

            assert mock_client.update_project.call_count == 2
            # First call: status on p1
            first_call = mock_client.update_project.call_args_list[0]
            assert first_call[1]["project_id"] == "p1"
            assert first_call[1]["status"] == "on_hold"
            # Second call: project_name on p2
            second_call = mock_client.update_project.call_args_list[1]
            assert second_call[1]["project_id"] == "p2"
            assert second_call[1]["project_name"] == "Renamed"

            assert isinstance(result, str)
            assert "2" in result  # Updated count
            assert "p1" in result
            assert "p2" in result

    def test_partial_failure(self):
        """One succeeds, one fails — reports both."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.side_effect = [
                {
                    "success": True,
                    "project_id": "p1",
                    "updated_fields": ["status"]
                },
                {
                    "success": False,
                    "project_id": "p2",
                    "updated_fields": [],
                    "error": "Project not found"
                },
            ]
            mock_get_client.return_value = mock_client

            result = server.update_projects(projects=[
                {"id": "p1", "status": "on_hold"},
                {"id": "p2", "status": "active"},
            ])

            assert isinstance(result, str)
            assert "1" in result  # 1 succeeded
            assert "p2" in result  # Failed ID mentioned
            assert "FAILED" in result or "failed" in result.lower()

    def test_all_fields_passthrough(self):
        """Verify model_dump passes all fields to connector."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "p1",
                "updated_fields": ["project_name", "status", "flagged", "due_date",
                                   "defer_date", "tags", "recurrence"]
            }
            mock_get_client.return_value = mock_client

            result = server.update_projects(projects=[{
                "id": "p1",
                "project_name": "Test",
                "folder_path": "Work",
                "note": "A note",
                "sequential": True,
                "project_type": "sequential",
                "status": "active",
                "review_interval_weeks": 2,
                "last_reviewed": "2026-03-01",
                "next_review_date": "2026-03-15",
                "completed_by_children": True,
                "due_date": "2026-04-01",
                "defer_date": "2026-03-20",
                "planned_date": "2026-03-25",
                "flagged": True,
                "estimated_minutes": 60,
                "tags": ["work"],
                "recurrence": "FREQ=WEEKLY",
                "repetition_method": "fixed",
            }])

            mock_client.update_project.assert_called_once()
            kwargs = mock_client.update_project.call_args[1]
            assert kwargs["project_id"] == "p1"
            assert kwargs["project_name"] == "Test"
            assert kwargs["folder_path"] == "Work"
            assert kwargs["note"] == "A note"
            assert kwargs["sequential"] is True
            assert kwargs["project_type"] == "sequential"
            assert kwargs["status"] == "active"
            assert kwargs["review_interval_weeks"] == 2
            assert kwargs["last_reviewed"] == "2026-03-01"
            assert kwargs["next_review_date"] == "2026-03-15"
            assert kwargs["completed_by_children"] is True
            assert kwargs["due_date"] == "2026-04-01"
            assert kwargs["defer_date"] == "2026-03-20"
            assert kwargs["planned_date"] == "2026-03-25"
            assert kwargs["flagged"] is True
            assert kwargs["estimated_minutes"] == 60
            assert kwargs["tags"] == ["work"]
            assert kwargs["recurrence"] == "FREQ=WEEKLY"
            assert kwargs["repetition_method"] == "fixed"
            # id should NOT be in kwargs (excluded by model_dump)
            assert "id" not in kwargs

    def test_delegation_from_update_project(self):
        """Old update_project delegates to update_projects correctly."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "p1",
                "updated_fields": ["flagged"]
            }
            mock_get_client.return_value = mock_client

            # Call the old update_project function
            result = server.update_project(project_id="p1", flagged=True)

            # Should still call client.update_project via delegation
            mock_client.update_project.assert_called_once()
            kwargs = mock_client.update_project.call_args[1]
            assert kwargs["project_id"] == "p1"
            assert kwargs["flagged"] is True
            assert "success" in result.lower() or "updated" in result.lower()

    def test_add_and_remove_tags(self):
        """update_projects passes add_tags and remove_tags correctly."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "p1",
                "updated_fields": ["add_tags", "remove_tags"]
            }
            mock_get_client.return_value = mock_client

            result = server.update_projects(projects=[{
                "id": "p1",
                "add_tags": ["new-tag"],
                "remove_tags": ["old-tag"],
            }])

            kwargs = mock_client.update_project.call_args[1]
            assert kwargs["add_tags"] == ["new-tag"]
            assert kwargs["remove_tags"] == ["old-tag"]

    def test_exception_during_update(self):
        """Exception from connector is caught and reported."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.side_effect = ValueError("Invalid status")
            mock_get_client.return_value = mock_client

            result = server.update_projects(projects=[{"id": "p1", "status": "bad"}])

            assert isinstance(result, str)
            assert "error" in result.lower()
            assert "Invalid status" in result

    def test_invalid_input(self):
        """Invalid project input returns error."""
        result = server.update_projects(projects=[{"not_a_field": "bad"}])
        assert isinstance(result, str)
        assert "error" in result.lower()

    def test_empty_update_no_fields(self):
        """Project with only id and no fields still calls connector."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "p1",
                "updated_fields": []
            }
            mock_get_client.return_value = mock_client

            result = server.update_projects(projects=[{"id": "p1"}])

            mock_client.update_project.assert_called_once_with(project_id="p1")
            assert isinstance(result, str)
