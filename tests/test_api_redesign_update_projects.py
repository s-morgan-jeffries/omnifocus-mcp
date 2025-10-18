"""Tests for update_projects() function (NEW API - Phase 2, Function 2.2).

This is the BATCH version of update_project() that updates multiple projects at once.

Key differences from update_project():
- Accepts Union[str, list[str]] for project_ids (single or multiple)
- EXCLUDES project_name and note (require unique values)
- Returns dict with updated_count, failed_count, updated_ids, failures
- Continues processing even if some projects fail
"""
import pytest
from unittest import mock

from omnifocus_mcp.omnifocus_client import OmniFocusClient, ProjectStatus


class TestUpdateProjectsRedesign:
    """Tests for update_projects() batch function (NEW API - Phase 2)."""

    @pytest.fixture
    def client(self):
        """Create a client for testing."""
        return OmniFocusClient(enable_safety_checks=False)

    # ========================================================================
    # Basic Functionality Tests
    # ========================================================================

    def test_update_projects_accepts_single_id_string(self, client):
        """NEW API: update_projects() accepts single project ID as string (Union type)."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_projects("proj-001", status=ProjectStatus.ACTIVE)

            assert result["updated_count"] == 1
            assert result["failed_count"] == 0
            assert "proj-001" in result["updated_ids"]
            assert len(result["failures"]) == 0

    def test_update_projects_accepts_list_of_ids(self, client):
        """NEW API: update_projects() accepts list of project IDs."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_projects(
                ["proj-001", "proj-002", "proj-003"],
                status=ProjectStatus.ON_HOLD
            )

            assert result["updated_count"] == 3
            assert result["failed_count"] == 0
            assert len(result["updated_ids"]) == 3
            assert "proj-001" in result["updated_ids"]
            assert "proj-002" in result["updated_ids"]

    # ========================================================================
    # Field Update Tests
    # ========================================================================

    def test_update_projects_set_status(self, client):
        """NEW API: update_projects() can set status on multiple projects."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_projects(
                ["proj-001", "proj-002"],
                status=ProjectStatus.DONE
            )

            assert result["updated_count"] == 2
            assert result["failed_count"] == 0

    def test_update_projects_set_sequential(self, client):
        """NEW API: update_projects() can set sequential on multiple projects."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_projects(
                ["proj-001", "proj-002"],
                sequential=True
            )

            assert result["updated_count"] == 2

    def test_update_projects_set_folder_path(self, client):
        """NEW API: update_projects() can move multiple projects to folder."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_projects(
                ["proj-001", "proj-002"],
                folder_path="Work > Projects"
            )

            assert result["updated_count"] == 2

    def test_update_projects_set_review_interval(self, client):
        """NEW API: update_projects() can set review interval on multiple projects."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_projects(
                ["proj-001", "proj-002"],
                review_interval_weeks=4
            )

            assert result["updated_count"] == 2

    def test_update_projects_mark_reviewed(self, client):
        """NEW API: update_projects() can mark multiple projects as reviewed."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_projects(
                ["proj-001", "proj-002"],
                last_reviewed="now"
            )

            assert result["updated_count"] == 2

    def test_update_projects_multiple_fields_at_once(self, client):
        """NEW API: update_projects() can update multiple fields simultaneously."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_projects(
                ["proj-001", "proj-002"],
                status=ProjectStatus.ACTIVE,
                sequential=True,
                review_interval_weeks=2
            )

            assert result["updated_count"] == 2

    # ========================================================================
    # Error Handling Tests
    # ========================================================================

    def test_update_projects_partial_failure(self, client):
        """NEW API: update_projects() continues even if some projects fail."""
        call_count = [0]

        def mock_applescript(script):
            call_count[0] += 1
            if call_count[0] == 2:
                # Second call (proj-002) fails
                raise Exception("Project not found")
            return "true"

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript', side_effect=mock_applescript):
            result = client.update_projects(
                ["proj-001", "proj-002", "proj-003"],
                status=ProjectStatus.ACTIVE
            )

            assert result["updated_count"] == 2
            assert result["failed_count"] == 1
            assert len(result["failures"]) == 1
            assert result["failures"][0]["project_id"] == "proj-002"
            assert "proj-001" in result["updated_ids"]
            assert "proj-003" in result["updated_ids"]

    def test_update_projects_rejects_project_name(self, client):
        """NEW API: update_projects() rejects project_name (requires unique values)."""
        with pytest.raises(ValueError) as exc_info:
            client.update_projects(
                ["proj-001", "proj-002"],
                project_name="Same Name"  # type: ignore
            )

        assert "project_name" in str(exc_info.value).lower()
        assert "unique" in str(exc_info.value).lower() or "not supported" in str(exc_info.value).lower()

    def test_update_projects_rejects_note(self, client):
        """NEW API: update_projects() rejects note (requires unique values)."""
        with pytest.raises(ValueError) as exc_info:
            client.update_projects(
                ["proj-001", "proj-002"],
                note="Same Note"  # type: ignore
            )

        assert "note" in str(exc_info.value).lower()
        assert "unique" in str(exc_info.value).lower() or "not supported" in str(exc_info.value).lower()

    def test_update_projects_requires_project_ids(self, client):
        """NEW API: update_projects() requires project_ids parameter."""
        with pytest.raises(TypeError):
            client.update_projects(status=ProjectStatus.ACTIVE)  # type: ignore

    def test_update_projects_requires_at_least_one_field(self, client):
        """NEW API: update_projects() requires at least one field to update."""
        with pytest.raises(ValueError) as exc_info:
            client.update_projects(["proj-001"])

        assert "at least one field" in str(exc_info.value).lower()

    # ========================================================================
    # Return Format Tests
    # ========================================================================

    def test_update_projects_returns_dict_with_all_keys(self, client):
        """NEW API: update_projects() returns dict with all required keys."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.update_projects(["proj-001"], status=ProjectStatus.ACTIVE)

            assert isinstance(result, dict)
            assert "updated_count" in result
            assert "failed_count" in result
            assert "updated_ids" in result
            assert "failures" in result
            assert isinstance(result["updated_count"], int)
            assert isinstance(result["failed_count"], int)
            assert isinstance(result["updated_ids"], list)
            assert isinstance(result["failures"], list)
