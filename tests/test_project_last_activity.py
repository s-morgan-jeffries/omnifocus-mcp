"""Tests for get_projects() include_last_activity parameter.

By default, lastActivityDate computation iterates ALL tasks (including completed)
per project, adding ~260ms overhead. Making it opt-in via include_last_activity
eliminates this cost for callers that don't need it.
"""
import json
import pytest
from unittest.mock import patch
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


@pytest.fixture
def client():
    return OmniFocusConnector(enable_safety_checks=False)


class TestIncludeLastActivityParameter:
    """Test that include_last_activity controls lastActivityDate computation."""

    def test_get_projects_accepts_include_last_activity_param(self, client):
        """get_projects() should accept include_last_activity parameter."""
        mock_json = json.dumps([{
            "id": "proj-1", "name": "Project", "note": "",
            "status": "active", "folderPath": "",
            "lastActivityDate": "2025-10-08T10:15:00Z",
        }])
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            # Should not raise TypeError
            projects = client.get_projects(include_last_activity=True)
            assert len(projects) == 1

    def test_last_activity_present_when_requested(self, client):
        """When include_last_activity=True, lastActivityDate should be populated."""
        mock_json = json.dumps([{
            "id": "proj-1", "name": "Project", "note": "",
            "status": "active", "folderPath": "",
            "lastActivityDate": "2025-10-08T10:15:00Z",
        }])
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_projects(include_last_activity=True)
            assert projects[0]['lastActivityDate'] == "2025-10-08T10:15:00Z"

    def test_last_activity_null_by_default(self, client):
        """Without include_last_activity, lastActivityDate should be null."""
        mock_json = json.dumps([{
            "id": "proj-1", "name": "Project", "note": "",
            "status": "active", "folderPath": "",
            "lastActivityDate": None,
        }])
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_projects()
            assert projects[0]['lastActivityDate'] is None

    def test_applescript_includes_task_iteration_when_requested(self, client):
        """When include_last_activity=True, AppleScript should iterate tasks."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_projects(include_last_activity=True)
            script = mock_run.call_args[0][0]
            assert 'lastActivity' in script
            assert 'creation date' in script

    def test_applescript_skips_task_iteration_by_default(self, client):
        """Without include_last_activity, AppleScript should skip task iteration."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_projects()
            script = mock_run.call_args[0][0]
            # Should not iterate tasks for activity date
            assert 'flattened tasks of proj' not in script or 'lastActivity' not in script
