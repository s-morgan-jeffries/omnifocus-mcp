"""Tests for update_project() function (API Redesign - Phase 2).

This file tests the enhanced update_project() function that consolidates:
- set_project_status()
- drop_project()
- set_review_interval()
- mark_project_reviewed()

NEW API changes:
- Returns dict instead of bool
- Adds status parameter (ProjectStatus enum)
- Adds review_interval_weeks parameter
- Adds last_reviewed parameter
- Follows same pattern as update_task()
"""
import pytest
from unittest import mock
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector, ProjectStatus


class TestUpdateProjectRedesign:
    """Tests for update_project() function (NEW API - Phase 2)."""

    @pytest.fixture
    def client(self):
        """Create a client with safety checks disabled for unit testing."""
        return OmniFocusConnector(enable_safety_checks=False)

    # ========================================================================
    # New Fields - Status
    # ========================================================================

    def test_update_project_set_status_enum(self, client):
        """NEW API: update_project() can set status using ProjectStatus enum."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_project("proj-001", status=ProjectStatus.ON_HOLD)

            assert result["success"] is True
            assert result["project_id"] == "proj-001"
            assert "status" in result["updated_fields"]

            # Verify AppleScript contains status update
            call_args = mock_run.call_args[0][0]
            assert "on hold" in call_args.lower()

    def test_update_project_set_status_string(self, client):
        """NEW API: update_project() can set status using string."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_project("proj-001", status="active")

            assert result["success"] is True
            assert "status" in result["updated_fields"]

            call_args = mock_run.call_args[0][0]
            assert "active" in call_args.lower()

    def test_update_project_drop_status(self, client):
        """NEW API: update_project() can drop a project (status=ProjectStatus.DROPPED)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_project("proj-001", status=ProjectStatus.DROPPED)

            assert result["success"] is True
            assert "status" in result["updated_fields"]

            call_args = mock_run.call_args[0][0]
            assert "dropped" in call_args.lower()

    def test_update_project_complete_status(self, client):
        """NEW API: update_project() can mark project as done."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_project("proj-001", status=ProjectStatus.DONE)

            assert result["success"] is True
            assert "status" in result["updated_fields"]

            call_args = mock_run.call_args[0][0]
            assert "done" in call_args.lower()

    # ========================================================================
    # New Fields - Review Interval
    # ========================================================================

    def test_update_project_set_review_interval(self, client):
        """NEW API: update_project() can set review interval in weeks."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_project("proj-001", review_interval_weeks=2)

            assert result["success"] is True
            assert "review_interval_weeks" in result["updated_fields"]

            call_args = mock_run.call_args[0][0]
            # Should convert weeks to days for OmniFocus
            assert "14" in call_args or "review interval" in call_args.lower()

    def test_update_project_clear_review_interval(self, client):
        """NEW API: update_project() can clear review interval (set to 0)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_project("proj-001", review_interval_weeks=0)

            assert result["success"] is True
            assert "review_interval_weeks" in result["updated_fields"]

    # ========================================================================
    # New Fields - Last Reviewed
    # ========================================================================

    def test_update_project_mark_reviewed(self, client):
        """NEW API: update_project() can mark project as reviewed with date."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_project("proj-001", last_reviewed="2025-10-18")

            assert result["success"] is True
            assert "last_reviewed" in result["updated_fields"]

            call_args = mock_run.call_args[0][0]
            assert "2025-10-18" in call_args or "reviewed" in call_args.lower()

    def test_update_project_mark_reviewed_now(self, client):
        """NEW API: update_project() can mark project as reviewed now (empty string or 'now')."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_project("proj-001", last_reviewed="now")

            assert result["success"] is True
            assert "last_reviewed" in result["updated_fields"]

    # ========================================================================
    # Existing Fields (Regression)
    # ========================================================================

    def test_update_project_existing_fields_still_work(self, client):
        """NEW API: Existing fields (name, note, sequential) still work."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_project(
                "proj-001",
                project_name="New Name",
                note="New note",
                sequential=True
            )

            assert result["success"] is True
            assert "project_name" in result["updated_fields"]
            assert "note" in result["updated_fields"]
            assert "sequential" in result["updated_fields"]

    # ========================================================================
    # Multiple Fields
    # ========================================================================

    def test_update_project_multiple_fields_at_once(self, client):
        """NEW API: update_project() can update multiple fields simultaneously."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_project(
                "proj-001",
                project_name="Updated Project",
                status=ProjectStatus.ACTIVE,
                review_interval_weeks=4,
                last_reviewed="2025-10-18"
            )

            assert result["success"] is True
            assert len(result["updated_fields"]) == 4
            assert "project_name" in result["updated_fields"]
            assert "status" in result["updated_fields"]
            assert "review_interval_weeks" in result["updated_fields"]
            assert "last_reviewed" in result["updated_fields"]

    # ========================================================================
    # Return Format
    # ========================================================================

    def test_update_project_returns_structured_dict(self, client):
        """NEW API: update_project() returns dict with success, project_id, updated_fields."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_project("proj-001", status=ProjectStatus.ACTIVE)

            assert isinstance(result, dict)
            assert "success" in result
            assert "project_id" in result
            assert "updated_fields" in result
            assert result["project_id"] == "proj-001"

    def test_update_project_success_has_no_error_key(self, client):
        """NEW API: Successful updates don't include error key."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_project("proj-001", status=ProjectStatus.ACTIVE)

            assert result["success"] is True
            assert "error" not in result or result.get("error") is None

    def test_update_project_failure_has_error_key(self, client):
        """NEW API: Failed updates include error key with message."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "false"

            result = client.update_project("proj-999", status=ProjectStatus.ACTIVE)

            assert result["success"] is False
            assert "error" in result
            assert result["error"] is not None

    # ========================================================================
    # Validation
    # ========================================================================

    def test_update_project_requires_project_id(self, client):
        """NEW API: update_project() raises ValueError if project_id is empty."""
        with pytest.raises(ValueError, match="project_id"):
            client.update_project("", status=ProjectStatus.ACTIVE)

    def test_update_project_requires_at_least_one_field(self, client):
        """NEW API: update_project() raises ValueError if no fields provided."""
        with pytest.raises(ValueError, match="At least one field"):
            client.update_project("proj-001")

    def test_update_project_invalid_status_string(self, client):
        """NEW API: update_project() raises ValueError for invalid status string."""
        with pytest.raises(ValueError, match="status"):
            client.update_project("proj-001", status="invalid_status")

    # ========================================================================
    # Folder Path (if we want to add it)
    # ========================================================================

    def test_update_project_folder_path(self, client):
        """NEW API: update_project() can move project to different folder."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_project("proj-001", folder_path="Work : Projects")

            assert result["success"] is True
            assert "folder_path" in result["updated_fields"]

            call_args = mock_run.call_args[0][0]
            assert "Work" in call_args and "Projects" in call_args
