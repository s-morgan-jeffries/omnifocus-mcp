"""Tests for project statistics in get_project."""
import json
from unittest import mock
import pytest
from omnifocus_mcp.omnifocus_client import OmniFocusClient


@pytest.fixture
def client():
    """Create an OmniFocusClient instance."""
    return OmniFocusClient()


class TestProjectStatistics:
    """Tests for project statistics."""

    def test_get_project_includes_statistics(self, client):
        """Test that get_project includes task counts and completion percentage."""
        project_json = json.dumps({
            "id": "proj-001",
            "name": "Test Project",
            "note": "A test project",
            "status": "active",
            "folderPath": "Work",
            "taskCount": 10,
            "completedTaskCount": 6,
            "remainingTaskCount": 4,
            "completionPercentage": 60.0
        })

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = project_json
            projects = client.get_projects(project_id="proj-001")

            assert len(projects) == 1

            project = projects[0]

            assert project['id'] == "proj-001"
            assert project['name'] == "Test Project"
            assert project['taskCount'] == 10
            assert project['completedTaskCount'] == 6
            assert project['remainingTaskCount'] == 4
            assert project['completionPercentage'] == 60.0

    def test_get_project_zero_tasks(self, client):
        """Test project statistics with zero tasks."""
        project_json = json.dumps({
            "id": "proj-002",
            "name": "Empty Project",
            "note": "",
            "status": "active",
            "folderPath": "",
            "taskCount": 0,
            "completedTaskCount": 0,
            "remainingTaskCount": 0,
            "completionPercentage": 0.0
        })

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = project_json
            projects = client.get_projects(project_id="proj-002")

            assert len(projects) == 1

            project = projects[0]

            assert project['taskCount'] == 0
            assert project['completedTaskCount'] == 0
            assert project['remainingTaskCount'] == 0
            assert project['completionPercentage'] == 0.0

    def test_get_project_all_completed(self, client):
        """Test project statistics with all tasks completed."""
        project_json = json.dumps({
            "id": "proj-003",
            "name": "Completed Project",
            "note": "",
            "status": "done",
            "folderPath": "",
            "taskCount": 5,
            "completedTaskCount": 5,
            "remainingTaskCount": 0,
            "completionPercentage": 100.0
        })

        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = project_json
            projects = client.get_projects(project_id="proj-003")

            assert len(projects) == 1

            project = projects[0]

            assert project['taskCount'] == 5
            assert project['completedTaskCount'] == 5
            assert project['remainingTaskCount'] == 0
            assert project['completionPercentage'] == 100.0
