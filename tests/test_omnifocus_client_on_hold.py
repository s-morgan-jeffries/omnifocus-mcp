"""Tests for on_hold_only filter in get_projects."""
import json
from unittest import mock
import pytest
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


@pytest.fixture
def client():
    """Create an OmniFocusConnector instance."""
    return OmniFocusConnector()


class TestGetProjectsOnHold:
    """Tests for on_hold_only filter in get_projects."""

    def test_get_projects_on_hold_only(self, client):
        """Test filtering for only on-hold projects."""
        on_hold_projects_json = json.dumps([
            {
                "id": "proj-001",
                "name": "On Hold Project",
                "status": "on hold",
                "folder": "Work",
                "note": "Waiting for approval"
            }
        ])
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = on_hold_projects_json
            projects = client.get_projects(on_hold_only=True)
            assert len(projects) == 1
            assert projects[0]['name'] == "On Hold Project"
            assert projects[0]['status'] == "on hold"
            # Verify the filter is in the script
            call_args = mock_run.call_args[0][0]
            assert "on hold" in call_args.lower()
            # Should skip non-on-hold projects
            assert "skip" in call_args.lower() or "error" in call_args.lower()
