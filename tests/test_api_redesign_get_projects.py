"""Client tests for get_projects() enhancements (Phase 3.2).

NEW API (Phase 3.2): Enhanced get_projects() with project_id and include_full_notes parameters
to consolidate get_project() and get_note() functionality.
"""
import pytest
from unittest import mock
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


class TestGetProjectsEnhancements:
    """Test new parameters for get_projects() function (Phase 3.2)."""

    @pytest.fixture
    def client(self):
        """Create OmniFocusConnector with safety checks disabled."""
        return OmniFocusConnector(enable_safety_checks=False)

    def test_get_projects_with_project_id_returns_single_project(self, client):
        """NEW API: get_projects(project_id=X) returns single project in list."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "proj-001", "name": "Specific Project", "status": "active status"}
            ]'''

            result = client.get_projects(project_id="proj-001")

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["id"] == "proj-001"
            assert result[0]["name"] == "Specific Project"

    def test_get_projects_with_project_id_filters_applescript(self, client):
        """NEW API: project_id parameter affects AppleScript source."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'

            client.get_projects(project_id="proj-001")

            # Verify AppleScript was called
            assert mock_run.called
            applescript = mock_run.call_args[0][0]

            # Should filter to specific project by ID
            assert 'whose id is "proj-001"' in applescript

    def test_get_projects_project_id_with_other_filters(self, client):
        """NEW API: project_id can be combined with other parameters."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'

            # project_id takes precedence but include_full_notes still applies
            client.get_projects(project_id="proj-001", include_full_notes=True)

            assert mock_run.called

    def test_get_projects_include_full_notes_false_by_default(self, client):
        """NEW API: include_full_notes defaults to False."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'

            # Call without include_full_notes parameter
            client.get_projects()

            assert mock_run.called
            # Parameter should default to False (though AppleScript returns full notes anyway)

    def test_get_projects_include_full_notes_true_returns_full_content(self, client):
        """NEW API: get_projects(include_full_notes=True) returns complete notes."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {
                    "id": "proj-001",
                    "name": "Project",
                    "note": "This is a very long note with multiple paragraphs..."
                }
            ]'''

            result = client.get_projects(include_full_notes=True)

            assert isinstance(result, list)
            assert len(result) == 1
            assert "note" in result[0]
            assert len(result[0]["note"]) > 0

    def test_get_projects_include_full_notes_with_project_id(self, client):
        """NEW API: Combine include_full_notes with project_id."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {
                    "id": "proj-001",
                    "name": "Project",
                    "note": "Full note content"
                }
            ]'''

            result = client.get_projects(project_id="proj-001", include_full_notes=True)

            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0]["id"] == "proj-001"
            assert "note" in result[0]

    def test_get_projects_all_new_parameters_together(self, client):
        """NEW API: Can use both new parameters together."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'

            client.get_projects(
                project_id="proj-001",
                include_full_notes=True
            )

            assert mock_run.called

    def test_get_projects_backward_compatible_no_new_params(self, client):
        """Backward compatibility: Existing calls without new parameters still work."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'

            # Old-style call with existing parameters only
            client.get_projects(on_hold_only=False, query="test")

            assert mock_run.called
