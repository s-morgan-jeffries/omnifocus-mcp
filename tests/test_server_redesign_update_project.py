"""Tests for update_project() MCP tool (API Redesign - Phase 2, Server Layer).

This file tests the MCP server layer for update_project().
Tests are written FIRST (TDD) before implementing server changes.
"""
import pytest
from unittest import mock

# Import server module
import omnifocus_mcp.server_fastmcp as server

# Extract function from FunctionTool wrapper
update_project = server.update_project


class TestUpdateProjectServerRedesign:
    """Tests for update_project() MCP tool (NEW API - Phase 2, Server Layer)."""

    # ========================================================================
    # Status Updates
    # ========================================================================

    def test_update_project_set_status(self):
        """Server: update_project() MCP tool can set project status."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "proj-001",
                "updated_fields": ["status"]
            }
            mock_get_client.return_value = mock_client

            result = update_project(project_id="proj-001", status="active")

            mock_client.update_project.assert_called_once_with(
                project_id="proj-001",
                project_name=None,
                folder_path=None,
                note=None,
                sequential=None,
                project_type=None,
                status="active",
                review_interval_weeks=None,
                last_reviewed=None,
                next_review_date=None,
                completed_by_children=None
            )

            assert isinstance(result, str)
            assert "success" in result.lower() or "updated" in result.lower()

    # ========================================================================
    # Review Interval
    # ========================================================================

    def test_update_project_set_review_interval(self):
        """Server: update_project() MCP tool can set review interval."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "proj-001",
                "updated_fields": ["review_interval_weeks"]
            }
            mock_get_client.return_value = mock_client

            result = update_project(project_id="proj-001", review_interval_weeks=2)

            mock_client.update_project.assert_called_once()
            call_kwargs = mock_client.update_project.call_args[1]
            assert call_kwargs["review_interval_weeks"] == 2

            assert isinstance(result, str)

    # ========================================================================
    # Last Reviewed
    # ========================================================================

    def test_update_project_mark_reviewed(self):
        """Server: update_project() MCP tool can mark project as reviewed."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "proj-001",
                "updated_fields": ["last_reviewed"]
            }
            mock_get_client.return_value = mock_client

            result = update_project(project_id="proj-001", last_reviewed="2025-10-18")

            mock_client.update_project.assert_called_once()
            call_kwargs = mock_client.update_project.call_args[1]
            assert call_kwargs["last_reviewed"] == "2025-10-18"

            assert isinstance(result, str)

    # ========================================================================
    # Multiple Fields
    # ========================================================================

    def test_update_project_multiple_fields(self):
        """Server: update_project() MCP tool can update multiple fields."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "proj-001",
                "updated_fields": ["project_name", "status", "review_interval_weeks"]
            }
            mock_get_client.return_value = mock_client

            result = update_project(
                project_id="proj-001",
                project_name="Updated Project",
                status="active",
                review_interval_weeks=4
            )

            assert isinstance(result, str)
            # Should mention multiple updated fields
            assert "3" in result or "updated" in result.lower()

    # ========================================================================
    # Existing Fields (Regression)
    # ========================================================================

    def test_update_project_existing_fields(self):
        """Server: Existing fields (project_name, note, sequential) still work."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "proj-001",
                "updated_fields": ["project_name", "note", "sequential"]
            }
            mock_get_client.return_value = mock_client

            result = update_project(
                project_id="proj-001",
                project_name="New Name",
                note="New note",
                sequential=True
            )

            mock_client.update_project.assert_called_once()
            call_kwargs = mock_client.update_project.call_args[1]
            assert call_kwargs["project_name"] == "New Name"
            assert call_kwargs["note"] == "New note"
            assert call_kwargs["sequential"] is True

            assert isinstance(result, str)

    # ========================================================================
    # Error Handling
    # ========================================================================

    def test_update_project_handles_client_failure(self):
        """Server: update_project() handles client failures gracefully."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = {
                "success": False,
                "project_id": "proj-999",
                "updated_fields": [],
                "error": "Project not found"
            }
            mock_get_client.return_value = mock_client

            result = update_project(project_id="proj-999", status="active")

            assert isinstance(result, str)
            assert "error" in result.lower() or "failed" in result.lower()
            assert "not found" in result.lower() or "999" in result

    def test_update_project_handles_client_exception(self):
        """Server: update_project() handles client ValueError gracefully."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.side_effect = ValueError("Invalid status")
            mock_get_client.return_value = mock_client

            result = update_project(project_id="proj-001", status="invalid")
            assert isinstance(result, str)
            assert "error" in result.lower()
            assert "invalid status" in result.lower()

    # ========================================================================
    # Response Format
    # ========================================================================

    def test_update_project_returns_human_readable_response(self):
        """Server: update_project() returns human-readable response for Claude."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "proj-001",
                "updated_fields": ["status", "review_interval_weeks"]
            }
            mock_get_client.return_value = mock_client

            result = update_project(
                project_id="proj-001",
                status="on_hold",
                review_interval_weeks=2
            )

            assert isinstance(result, str)
            assert len(result) > 20  # Should be descriptive
            # Should mention what was updated
            assert "proj-001" in result or "project" in result.lower()

    def test_update_project_mentions_updated_fields(self):
        """Server: Response mentions which fields were updated."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "proj-001",
                "updated_fields": ["project_name", "note"]
            }
            mock_get_client.return_value = mock_client

            result = update_project(
                project_id="proj-001",
                project_name="New Name",
                note="New note"
            )

            assert isinstance(result, str)
            # Should mention the updated fields somehow
            assert "2" in result or "name" in result.lower() or "updated" in result.lower()

    # ========================================================================
    # Folder Path
    # ========================================================================

    def test_update_project_folder_path(self):
        """Server: update_project() can move project to different folder."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "proj-001",
                "updated_fields": ["folder_path"]
            }
            mock_get_client.return_value = mock_client

            result = update_project(
                project_id="proj-001",
                folder_path="Work : Projects"
            )

            mock_client.update_project.assert_called_once()
            call_kwargs = mock_client.update_project.call_args[1]
            assert call_kwargs["folder_path"] == "Work : Projects"

            assert isinstance(result, str)


class TestUpdateProjectNextReviewDate:
    """Tests for next_review_date parameter in update_project server tool."""

    def test_update_project_next_review_date_passed_to_connector(self):
        """next_review_date is passed through to the connector."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "proj-001",
                "updated_fields": ["next_review_date"]
            }
            mock_get_client.return_value = mock_client

            result = update_project(project_id="proj-001", next_review_date="2026-04-01")

            call_kwargs = mock_client.update_project.call_args[1]
            assert call_kwargs["next_review_date"] == "2026-04-01"
            assert "updated" in result.lower() or "success" in result.lower()


class TestUpdateProjectCompletedByChildren:
    """Tests for completed_by_children parameter in update_project server tool."""

    def test_update_project_completed_by_children_passed_to_connector(self):
        """completed_by_children=True is passed through to the connector."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_project.return_value = {
                "success": True,
                "project_id": "proj-001",
                "updated_fields": ["completed_by_children"]
            }
            mock_get_client.return_value = mock_client

            result = update_project(project_id="proj-001", completed_by_children=True)

            call_kwargs = mock_client.update_project.call_args[1]
            assert call_kwargs["completed_by_children"] is True
            assert "updated" in result.lower() or "success" in result.lower()
