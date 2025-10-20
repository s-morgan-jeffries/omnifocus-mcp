"""Tests for date range filtering."""
import pytest
from unittest import mock

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


@pytest.fixture
def client():
    """Create a client with safety checks disabled."""
    return OmniFocusConnector(enable_safety_checks=False)


class TestTaskDateRangeFiltering:
    """Tests for task date range filtering."""

    def test_created_after_filter(self, client):
        """Test filtering tasks created after a date."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Task 1", "completed": false, "creationDate": "2025-01-15T10:00:00Z"},
                {"id": "t2", "name": "Task 2", "completed": false, "creationDate": "2025-01-20T10:00:00Z"},
                {"id": "t3", "name": "Task 3", "completed": false, "creationDate": "2025-01-10T10:00:00Z"}
            ]'''

            tasks = client.get_tasks(created_after="2025-01-12T00:00:00Z")

            assert len(tasks) == 2
            assert tasks[0]['id'] == "t1"
            assert tasks[1]['id'] == "t2"

    def test_created_before_filter(self, client):
        """Test filtering tasks created before a date."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Task 1", "completed": false, "creationDate": "2025-01-15T10:00:00Z"},
                {"id": "t2", "name": "Task 2", "completed": false, "creationDate": "2025-01-05T10:00:00Z"}
            ]'''

            tasks = client.get_tasks(created_before="2025-01-10T00:00:00Z")

            assert len(tasks) == 1
            assert tasks[0]['id'] == "t2"

    def test_created_date_range(self, client):
        """Test filtering tasks within a creation date range."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Task 1", "completed": false, "creationDate": "2025-01-15T10:00:00Z"},
                {"id": "t2", "name": "Task 2", "completed": false, "creationDate": "2025-01-20T10:00:00Z"},
                {"id": "t3", "name": "Task 3", "completed": false, "creationDate": "2025-01-05T10:00:00Z"}
            ]'''

            tasks = client.get_tasks(created_after="2025-01-10T00:00:00Z", created_before="2025-01-18T00:00:00Z")

            assert len(tasks) == 1
            assert tasks[0]['id'] == "t1"

    def test_modified_after_filter(self, client):
        """Test filtering tasks modified after a date."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Task 1", "completed": false, "modificationDate": "2025-01-15T10:00:00Z"},
                {"id": "t2", "name": "Task 2", "completed": false, "modificationDate": "2025-01-20T10:00:00Z"}
            ]'''

            tasks = client.get_tasks(modified_after="2025-01-18T00:00:00Z")

            assert len(tasks) == 1
            assert tasks[0]['id'] == "t2"

    def test_modified_before_filter(self, client):
        """Test filtering tasks modified before a date."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Task 1", "completed": false, "modificationDate": "2025-01-15T10:00:00Z"},
                {"id": "t2", "name": "Task 2", "completed": false, "modificationDate": "2025-01-20T10:00:00Z"}
            ]'''

            tasks = client.get_tasks(modified_before="2025-01-18T00:00:00Z")

            assert len(tasks) == 1
            assert tasks[0]['id'] == "t1"

    def test_no_creation_date(self, client):
        """Test that tasks without creation dates are handled."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Task 1", "completed": false, "creationDate": "2025-01-15T10:00:00Z"},
                {"id": "t2", "name": "Task 2", "completed": false, "creationDate": ""}
            ]'''

            tasks = client.get_tasks(created_after="2025-01-10T00:00:00Z")

            # Task without creation date should not match
            assert len(tasks) == 1
            assert tasks[0]['id'] == "t1"

    def test_invalid_date_format(self, client):
        """Test that invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            client.get_tasks(created_after="not-a-date")


class TestProjectDateRangeFiltering:
    """Tests for project date range filtering."""

    def test_modified_after_filter(self, client):
        """Test filtering projects modified after a date."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "p1", "name": "Project 1", "status": "active", "modificationDate": "2025-01-15T10:00:00Z"},
                {"id": "p2", "name": "Project 2", "status": "active", "modificationDate": "2025-01-20T10:00:00Z"}
            ]'''

            projects = client.get_projects(modified_after="2025-01-18T00:00:00Z")

            assert len(projects) == 1
            assert projects[0]['id'] == "p2"

    def test_modified_before_filter(self, client):
        """Test filtering projects modified before a date."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "p1", "name": "Project 1", "status": "active", "modificationDate": "2025-01-15T10:00:00Z"},
                {"id": "p2", "name": "Project 2", "status": "active", "modificationDate": "2025-01-20T10:00:00Z"}
            ]'''

            projects = client.get_projects(modified_before="2025-01-18T00:00:00Z")

            assert len(projects) == 1
            assert projects[0]['id'] == "p1"
