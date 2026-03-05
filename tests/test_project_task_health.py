"""Tests for get_projects() include_task_health parameter.

This parameter returns per-project task health data (remaining, available,
overdue, deferred counts) in a single AppleScript call, eliminating the N+1
pattern where project review workflows call get_tasks() per project.

Expected performance improvement: ~20-30x for project review (33 projects
at 2.3s each = 76s -> single call at 2-4s).
"""
import json
import pytest
from unittest.mock import patch
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


@pytest.fixture
def client():
    return OmniFocusConnector(enable_safety_checks=False)


class TestIncludeTaskHealthParameter:
    """Test that include_task_health adds health fields to project response."""

    def test_get_projects_accepts_include_task_health_param(self, client):
        """get_projects() should accept include_task_health parameter."""
        mock_json = json.dumps([{
            "id": "proj-1", "name": "Project", "note": "",
            "status": "active", "folderPath": "",
            "lastActivityDate": None,
        }])
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            # Should not raise TypeError for unexpected keyword
            projects = client.get_projects(include_task_health=True)
            assert len(projects) == 1

    def test_task_health_includes_remaining_count(self, client):
        """When include_task_health=True, response includes remainingCount."""
        mock_json = json.dumps([{
            "id": "proj-1", "name": "Project", "note": "",
            "status": "active", "folderPath": "",
            "lastActivityDate": None,
            "remainingCount": 5,
            "availableCount": 3,
            "overdueCount": 1,
            "deferredCount": 1,
            "hasDeferredOnly": False,
        }])
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_projects(include_task_health=True)
            assert projects[0]['remainingCount'] == 5

    def test_task_health_includes_available_count(self, client):
        """When include_task_health=True, response includes availableCount."""
        mock_json = json.dumps([{
            "id": "proj-1", "name": "Project", "note": "",
            "status": "active", "folderPath": "",
            "lastActivityDate": None,
            "remainingCount": 5,
            "availableCount": 3,
            "overdueCount": 0,
            "deferredCount": 2,
            "hasDeferredOnly": False,
        }])
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_projects(include_task_health=True)
            assert projects[0]['availableCount'] == 3

    def test_task_health_includes_overdue_count(self, client):
        """When include_task_health=True, response includes overdueCount."""
        mock_json = json.dumps([{
            "id": "proj-1", "name": "Project", "note": "",
            "status": "active", "folderPath": "",
            "lastActivityDate": None,
            "remainingCount": 5,
            "availableCount": 3,
            "overdueCount": 2,
            "deferredCount": 0,
            "hasDeferredOnly": False,
        }])
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_projects(include_task_health=True)
            assert projects[0]['overdueCount'] == 2

    def test_task_health_includes_deferred_count(self, client):
        """When include_task_health=True, response includes deferredCount."""
        mock_json = json.dumps([{
            "id": "proj-1", "name": "Project", "note": "",
            "status": "active", "folderPath": "",
            "lastActivityDate": None,
            "remainingCount": 3,
            "availableCount": 0,
            "overdueCount": 0,
            "deferredCount": 3,
            "hasDeferredOnly": True,
        }])
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_projects(include_task_health=True)
            assert projects[0]['deferredCount'] == 3

    def test_task_health_includes_has_deferred_only(self, client):
        """When all remaining tasks are blocked/deferred, hasDeferredOnly=True."""
        mock_json = json.dumps([{
            "id": "proj-1", "name": "Project", "note": "",
            "status": "active", "folderPath": "",
            "lastActivityDate": None,
            "remainingCount": 3,
            "availableCount": 0,
            "overdueCount": 0,
            "deferredCount": 3,
            "hasDeferredOnly": True,
        }])
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_projects(include_task_health=True)
            assert projects[0]['hasDeferredOnly'] is True

    def test_task_health_false_by_default(self, client):
        """Without include_task_health, health fields should not be in response."""
        mock_json = json.dumps([{
            "id": "proj-1", "name": "Project", "note": "",
            "status": "active", "folderPath": "",
            "lastActivityDate": None,
        }])
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_projects()
            assert 'remainingCount' not in projects[0]
            assert 'availableCount' not in projects[0]
            assert 'overdueCount' not in projects[0]

    def test_task_health_applescript_includes_task_iteration(self, client):
        """When include_task_health=True, AppleScript should iterate tasks."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_projects(include_task_health=True)
            script = mock_run.call_args[0][0]
            # AppleScript should contain task health counting logic
            assert 'remainingCount' in script
            assert 'availableCount' in script
            assert 'overdueCount' in script

    def test_task_health_applescript_absent_when_false(self, client):
        """When include_task_health=False, AppleScript should not iterate tasks for health."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_projects(include_task_health=False)
            script = mock_run.call_args[0][0]
            assert 'remainingCount' not in script


class TestIncludeTaskHealthServerLayer:
    """Test that the server layer passes include_task_health correctly."""

    def test_server_passes_include_task_health_to_client(self):
        """Server get_projects() should pass include_task_health to client."""
        from unittest import mock
        import omnifocus_mcp.server_fastmcp as server

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_projects.return_value = [
                {"id": "proj-1", "name": "Project", "status": "active",
                 "remainingCount": 5, "availableCount": 3,
                 "overdueCount": 1, "deferredCount": 1,
                 "hasDeferredOnly": False}
            ]
            mock_get_client.return_value = mock_client

            result = server.get_projects(include_task_health=True)

            call_kwargs = mock_client.get_projects.call_args[1]
            assert call_kwargs['include_task_health'] is True

    def test_server_formats_health_fields(self):
        """Server should format health fields in output text."""
        from unittest import mock
        import omnifocus_mcp.server_fastmcp as server

        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.get_projects.return_value = [
                {"id": "proj-1", "name": "Project", "status": "active",
                 "remainingCount": 5, "availableCount": 3,
                 "overdueCount": 1, "deferredCount": 1,
                 "hasDeferredOnly": False}
            ]
            mock_get_client.return_value = mock_client

            result = server.get_projects(include_task_health=True)
            assert "Remaining Tasks: 5" in result
            assert "Available Tasks: 3" in result
            assert "Overdue Tasks: 1" in result
            assert "On Track" in result
