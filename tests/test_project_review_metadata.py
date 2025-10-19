"""Tests for review metadata in project responses."""
import json
from unittest import mock
import pytest
from omnifocus_mcp.omnifocus_client import OmniFocusClient


@pytest.fixture
def client():
    """Create an OmniFocusClient instance."""
    return OmniFocusClient()


class TestProjectReviewMetadata:
    """Tests for review metadata in projects."""

    def test_get_project_includes_review_metadata(self, client):
        """Test that get_projects includes review interval and dates."""
        # get_projects returns a list, not a single dict
        project_json = json.dumps([{
            "id": "proj-001",
            "name": "Test Project",
            "note": "",
            "status": "active",
            "folderPath": "Work",
            "taskCount": 5,
            "completedTaskCount": 2,
            "remainingTaskCount": 3,
            "completionPercentage": 40.0,
            "reviewInterval": "1 week",
            "lastReviewDate": "2025-10-01T12:00:00",
            "nextReviewDate": "2025-10-08T12:00:00"
        }])

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = project_json
            projects = client.get_projects(project_id="proj-001")

            assert len(projects) == 1

            project = projects[0]

            assert project['reviewInterval'] == "1 week"
            assert project['lastReviewDate'] == "2025-10-01T12:00:00"
            assert project['nextReviewDate'] == "2025-10-08T12:00:00"

    def test_get_project_no_review_interval(self, client):
        """Test project with no review interval set."""
        # get_projects returns a list, not a single dict
        project_json = json.dumps([{
            "id": "proj-002",
            "name": "No Review Project",
            "note": "",
            "status": "active",
            "folderPath": "",
            "taskCount": 0,
            "completedTaskCount": 0,
            "remainingTaskCount": 0,
            "completionPercentage": 0.0,
            "reviewInterval": None,
            "lastReviewDate": None,
            "nextReviewDate": None
        }])

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = project_json
            projects = client.get_projects(project_id="proj-002")

            assert len(projects) == 1

            project = projects[0]

            assert project['reviewInterval'] is None
            assert project['lastReviewDate'] is None
            assert project['nextReviewDate'] is None

    def test_get_project_never_reviewed(self, client):
        """Test project with review interval but never reviewed."""
        # get_projects returns a list, not a single dict
        project_json = json.dumps([{
            "id": "proj-003",
            "name": "New Project",
            "note": "",
            "status": "active",
            "folderPath": "",
            "taskCount": 3,
            "completedTaskCount": 0,
            "remainingTaskCount": 3,
            "completionPercentage": 0.0,
            "reviewInterval": "2 weeks",
            "lastReviewDate": None,
            "nextReviewDate": "2025-10-15T12:00:00"
        }])

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = project_json
            projects = client.get_projects(project_id="proj-003")

            assert len(projects) == 1

            project = projects[0]

            assert project['reviewInterval'] == "2 weeks"
            assert project['lastReviewDate'] is None
            assert project['nextReviewDate'] == "2025-10-15T12:00:00"
