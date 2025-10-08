"""Tests for project activity tracking (modification and activity dates)."""

import json
import pytest
from unittest.mock import patch
from omnifocus_mcp.omnifocus_client import OmniFocusClient


@pytest.fixture
def client():
    """Create an OmniFocusClient instance."""
    return OmniFocusClient(enable_safety_checks=False)


class TestProjectModificationDate:
    """Test that modificationDate is included in project responses."""

    def test_get_projects_includes_modification_date(self, client):
        """Projects should include modificationDate field."""
        mock_json = json.dumps([{
            "id": "proj-123",
            "name": "Test Project",
            "note": "",
            "status": "active",
            "folderPath": "Work",
            "modificationDate": "2025-10-07T14:30:00Z"
        }])

        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_projects()

        assert len(projects) == 1
        assert projects[0]['modificationDate'] == "2025-10-07T14:30:00Z"

    def test_get_projects_modification_date_null_if_missing(self, client):
        """Projects without modification date should have null."""
        mock_json = json.dumps([{
            "id": "proj-123",
            "name": "Test Project",
            "note": "",
            "status": "active",
            "folderPath": "",
            "modificationDate": None
        }])

        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_projects()

        assert projects[0]['modificationDate'] is None


class TestProjectActivityDate:
    """Test that lastActivityDate is included in project responses."""

    def test_get_projects_includes_last_activity_date(self, client):
        """Projects should include lastActivityDate field."""
        mock_json = json.dumps([{
            "id": "proj-123",
            "name": "Test Project",
            "note": "",
            "status": "active",
            "folderPath": "",
            "modificationDate": "2025-10-07T14:30:00Z",
            "lastActivityDate": "2025-10-08T10:15:00Z"
        }])

        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_projects()

        assert len(projects) == 1
        assert projects[0]['lastActivityDate'] == "2025-10-08T10:15:00Z"

    def test_get_projects_activity_date_null_if_no_activity(self, client):
        """Projects with no task activity should have null lastActivityDate."""
        mock_json = json.dumps([{
            "id": "proj-123",
            "name": "Empty Project",
            "note": "",
            "status": "active",
            "folderPath": "",
            "modificationDate": "2025-10-01T00:00:00Z",
            "lastActivityDate": None
        }])

        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_projects()

        assert projects[0]['lastActivityDate'] is None

    def test_get_project_single_includes_dates(self, client):
        """get_project() should also include modification and activity dates."""
        mock_json = json.dumps({
            "id": "proj-123",
            "name": "Test Project",
            "note": "",
            "status": "active",
            "folderPath": "",
            "taskCount": 5,
            "completedTaskCount": 2,
            "remainingTaskCount": 3,
            "completionPercentage": 40.0,
            "reviewInterval": None,
            "lastReviewDate": None,
            "nextReviewDate": None,
            "modificationDate": "2025-10-07T14:30:00Z",
            "lastActivityDate": "2025-10-08T10:15:00Z"
        })

        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            project = client.get_project("proj-123")

        assert project['modificationDate'] == "2025-10-07T14:30:00Z"
        assert project['lastActivityDate'] == "2025-10-08T10:15:00Z"
