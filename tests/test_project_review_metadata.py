"""Tests for review metadata in project responses."""
import json
from unittest import mock
import pytest
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


@pytest.fixture
def client():
    """Create an OmniFocusConnector instance."""
    return OmniFocusConnector()


class TestProjectReviewMetadata:
    """Tests for review metadata in projects."""

    def test_get_project_includes_review_metadata(self, client):
        """Test that get_projects includes review interval and dates."""
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
            "reviewIntervalValue": 1,
            "reviewIntervalUnit": "week",
            "lastReviewDate": "2025-10-01T12:00:00",
            "nextReviewDate": "2025-10-08T12:00:00"
        }])

        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = project_json
            projects = client.get_projects(project_id="proj-001")

            assert len(projects) == 1

            project = projects[0]

            assert project['reviewIntervalValue'] == 1
            assert project['reviewIntervalUnit'] == "week"
            assert project['lastReviewDate'] == "2025-10-01T12:00:00"
            assert project['nextReviewDate'] == "2025-10-08T12:00:00"

    def test_get_project_no_review_interval(self, client):
        """Test project with no review interval set."""
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
            "reviewIntervalValue": 0,
            "reviewIntervalUnit": "",
            "lastReviewDate": None,
            "nextReviewDate": None
        }])

        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = project_json
            projects = client.get_projects(project_id="proj-002")

            assert len(projects) == 1

            project = projects[0]

            assert project['reviewIntervalValue'] == 0
            assert project['reviewIntervalUnit'] == ""
            assert project['lastReviewDate'] is None
            assert project['nextReviewDate'] is None

    def test_get_project_never_reviewed(self, client):
        """Test project with review interval but never reviewed."""
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
            "reviewIntervalValue": 2,
            "reviewIntervalUnit": "week",
            "lastReviewDate": None,
            "nextReviewDate": "2025-10-15T12:00:00"
        }])

        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = project_json
            projects = client.get_projects(project_id="proj-003")

            assert len(projects) == 1

            project = projects[0]

            assert project['reviewIntervalValue'] == 2
            assert project['reviewIntervalUnit'] == "week"
            assert project['lastReviewDate'] is None
            assert project['nextReviewDate'] == "2025-10-15T12:00:00"

    def test_get_project_monthly_review_interval(self, client):
        """Test project with monthly review interval."""
        project_json = json.dumps([{
            "id": "proj-004",
            "name": "Monthly Review Project",
            "note": "",
            "status": "active",
            "folderPath": "",
            "reviewIntervalValue": 3,
            "reviewIntervalUnit": "month",
            "lastReviewDate": "2026-01-15T12:00:00",
            "nextReviewDate": "2026-04-15T12:00:00"
        }])

        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = project_json
            projects = client.get_projects(project_id="proj-004")

            assert len(projects) == 1
            project = projects[0]

            assert project['reviewIntervalValue'] == 3
            assert project['reviewIntervalUnit'] == "month"


class TestUpdateProjectReviewInterval:
    """Tests for update_project review interval with all units."""

    def test_update_project_review_interval_value_and_unit(self, client):
        """Test update_project with review_interval_value and review_interval_unit."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_project(
                "proj-001",
                review_interval_value=3,
                review_interval_unit="month"
            )
            assert result["success"] is True
            assert "review_interval" in result["updated_fields"]
            # Verify AppleScript contains the correct unit
            call_args = mock_run.call_args[0][0]
            assert "unit:month, steps:3" in call_args

    def test_update_project_review_interval_day_unit(self, client):
        """Test update_project with day unit."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_project(
                "proj-001",
                review_interval_value=14,
                review_interval_unit="day"
            )
            assert result["success"] is True
            call_args = mock_run.call_args[0][0]
            assert "unit:day, steps:14" in call_args

    def test_update_project_review_interval_year_unit(self, client):
        """Test update_project with year unit."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_project(
                "proj-001",
                review_interval_value=1,
                review_interval_unit="year"
            )
            assert result["success"] is True
            call_args = mock_run.call_args[0][0]
            assert "unit:year, steps:1" in call_args

    def test_update_project_review_interval_invalid_unit(self, client):
        """Test update_project rejects invalid review_interval_unit."""
        with pytest.raises(ValueError, match="Invalid review_interval_unit"):
            client.update_project(
                "proj-001",
                review_interval_value=1,
                review_interval_unit="fortnight"
            )

    def test_update_project_review_interval_default_unit(self, client):
        """Test update_project defaults to week when no unit specified."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_project(
                "proj-001",
                review_interval_value=2
            )
            assert result["success"] is True
            call_args = mock_run.call_args[0][0]
            assert "unit:week, steps:2" in call_args

    def test_update_project_deprecated_weeks_still_works(self, client):
        """Test that deprecated review_interval_weeks still works."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_project(
                "proj-001",
                review_interval_weeks=4
            )
            assert result["success"] is True
            assert "review_interval" in result["updated_fields"]
            call_args = mock_run.call_args[0][0]
            assert "unit:week, steps:4" in call_args

    def test_update_project_value_overrides_weeks(self, client):
        """Test that review_interval_value takes precedence over review_interval_weeks."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.update_project(
                "proj-001",
                review_interval_weeks=2,
                review_interval_value=3,
                review_interval_unit="month"
            )
            assert result["success"] is True
            call_args = mock_run.call_args[0][0]
            # review_interval_value should win
            assert "unit:month, steps:3" in call_args


class TestUpdateProjectsReviewInterval:
    """Tests for update_projects (batch) review interval with all units."""

    def test_update_projects_review_interval_value_and_unit(self, client):
        """Test update_projects with review_interval_value and review_interval_unit."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"
            result = client.update_projects(
                ["proj-001", "proj-002"],
                review_interval_value=6,
                review_interval_unit="month"
            )
            assert result["updated_count"] == 2
            call_args = mock_run.call_args[0][0]
            assert "unit:month, steps:6" in call_args

    def test_update_projects_review_interval_invalid_unit(self, client):
        """Test update_projects rejects invalid review_interval_unit."""
        with pytest.raises(ValueError, match="Invalid review_interval_unit"):
            client.update_projects(
                ["proj-001"],
                review_interval_value=1,
                review_interval_unit="biweekly"
            )
