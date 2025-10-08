"""Tests for stalled project detection."""

import json
import pytest
from unittest.mock import patch
from omnifocus_mcp.omnifocus_client import OmniFocusClient


@pytest.fixture
def client():
    """Create an OmniFocusClient instance."""
    return OmniFocusClient(enable_safety_checks=False)


class TestGetStalledProjects:
    """Test get_stalled_projects() method."""

    def test_get_stalled_projects_default_30_days(self, client):
        """Should return projects with no activity in 30+ days."""
        mock_json = json.dumps([
            {
                "id": "proj-stale-1",
                "name": "Stale Project 1",
                "status": "active",
                "lastActivityDate": "2024-09-01T00:00:00Z",  # Old
                "daysInactive": 37
            },
            {
                "id": "proj-stale-2",
                "name": "Stale Project 2",
                "status": "active",
                "lastActivityDate": "2024-09-05T00:00:00Z",  # Old
                "daysInactive": 33
            }
        ])

        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_stalled_projects()

        assert len(projects) == 2
        assert projects[0]['name'] == "Stale Project 1"
        assert projects[0]['daysInactive'] == 37
        assert projects[1]['daysInactive'] == 33

    def test_get_stalled_projects_custom_threshold(self, client):
        """Should accept custom inactivity threshold."""
        mock_json = json.dumps([
            {
                "id": "proj-stale-1",
                "name": "Stale Project",
                "status": "active",
                "lastActivityDate": "2025-09-20T00:00:00Z",
                "daysInactive": 18
            }
        ])

        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_stalled_projects(days_inactive=14)

        assert len(projects) == 1
        assert projects[0]['daysInactive'] == 18

    def test_get_stalled_projects_empty_result(self, client):
        """Should return empty list when no stalled projects."""
        mock_json = json.dumps([])

        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_stalled_projects()

        assert len(projects) == 0

    def test_get_stalled_projects_only_active_status(self, client):
        """Should only return active projects (not on hold, done, or dropped)."""
        # This is tested by verifying AppleScript filters by status
        mock_json = json.dumps([
            {
                "id": "proj-active-stale",
                "name": "Active Stale",
                "status": "active",
                "lastActivityDate": "2024-08-01T00:00:00Z",
                "daysInactive": 68
            }
        ])

        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_stalled_projects()

        # Verify the AppleScript filters for active status
        call_args = mock_run.call_args[0][0]
        assert 'status of proj is not active' in call_args  # Uses negation to skip non-active
        assert len(projects) == 1

    def test_get_stalled_projects_no_activity_date(self, client):
        """Should handle projects with no activity (lastActivityDate is null)."""
        mock_json = json.dumps([
            {
                "id": "proj-no-activity",
                "name": "No Activity Project",
                "status": "active",
                "lastActivityDate": None,
                "daysInactive": None
            }
        ])

        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_stalled_projects()

        assert len(projects) == 1
        assert projects[0]['lastActivityDate'] is None
        assert projects[0]['daysInactive'] is None

    def test_get_stalled_projects_sorted_by_days_inactive(self, client):
        """Should return projects sorted by days inactive (most stale first)."""
        mock_json = json.dumps([
            {
                "id": "proj-1",
                "name": "Most Stale",
                "status": "active",
                "lastActivityDate": "2024-07-01T00:00:00Z",
                "daysInactive": 99
            },
            {
                "id": "proj-2",
                "name": "Less Stale",
                "status": "active",
                "lastActivityDate": "2024-09-01T00:00:00Z",
                "daysInactive": 37
            },
            {
                "id": "proj-3",
                "name": "Least Stale",
                "status": "active",
                "lastActivityDate": "2024-09-10T00:00:00Z",
                "daysInactive": 28
            }
        ])

        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            projects = client.get_stalled_projects()

        # Projects should already be sorted by AppleScript
        assert projects[0]['daysInactive'] == 99
        assert projects[1]['daysInactive'] == 37
        assert projects[2]['daysInactive'] == 28
