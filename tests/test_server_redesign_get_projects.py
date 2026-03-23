"""Server tests for get_projects() enhancements (Phase 3.2)."""
from unittest import mock
import omnifocus_mcp.server_fastmcp as server


class TestGetProjectsServerEnhancements:
    """Server tests for get_projects() new parameters."""

    def test_get_projects_with_project_id_parameter(self):
        """Server: get_projects(project_id=X) passes to client."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_projects.return_value = [
                {"id": "proj-001", "name": "Project", "status": "active status"}
            ]
            mock_get_client.return_value = mock_client

            result = server.get_projects(project_id="proj-001")

            # Verify project_id was passed correctly
            call_kwargs = mock_client.get_projects.call_args[1]
            assert call_kwargs['project_id'] == "proj-001"
            assert isinstance(result, str)
            assert "proj-001" in result

    def test_get_projects_with_include_full_notes_parameter(self):
        """Server: get_projects(include_full_notes=True) passes to client."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_projects.return_value = []
            mock_get_client.return_value = mock_client

            result = server.get_projects(include_full_notes=True)

            # Verify include_full_notes was passed correctly
            call_kwargs = mock_client.get_projects.call_args[1]
            assert call_kwargs['include_full_notes'] is True
            assert isinstance(result, str)

    def test_get_projects_handles_value_error(self):
        """Server: get_projects() catches ValueError and returns error string."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_projects.side_effect = ValueError("Invalid date range")
            mock_get_client.return_value = mock_client

            result = server.get_projects()
            assert isinstance(result, str)
            assert "error" in result.lower()
            assert "invalid date range" in result.lower()

    def test_get_projects_with_flagged_only_parameter(self):
        """Server: get_projects(flagged_only=True) passes to client."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_projects.return_value = [
                {"id": "proj-001", "name": "Flagged Project", "status": "active status", "flagged": True}
            ]
            mock_get_client.return_value = mock_client

            result = server.get_projects(flagged_only=True)

            call_kwargs = mock_client.get_projects.call_args[1]
            assert call_kwargs['flagged_only'] is True
            assert isinstance(result, str)
            assert "flagged projects" in result.lower()

    def test_get_projects_with_tag_filter_parameter(self):
        """Server: get_projects(tag_filter=["X"]) passes to client."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_projects.return_value = [
                {"id": "proj-001", "name": "Tagged Project", "status": "active status", "tags": ["High Priority"]}
            ]
            mock_get_client.return_value = mock_client

            result = server.get_projects(tag_filter=["High Priority"])

            call_kwargs = mock_client.get_projects.call_args[1]
            assert call_kwargs['tag_filter'] == ["High Priority"]
            assert isinstance(result, str)
            assert "Tagged Project" in result
