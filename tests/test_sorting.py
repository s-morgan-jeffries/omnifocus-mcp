"""Tests for sorting functionality in get_tasks and get_projects."""
import pytest
from unittest import mock

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


@pytest.fixture
def client():
    """Create a client with safety checks disabled."""
    return OmniFocusConnector(enable_safety_checks=False)


class TestTaskSorting:
    """Tests for task sorting options."""

    def test_sort_by_name_asc(self, client):
        """Test sorting tasks by name ascending."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t3", "name": "Charlie", "completed": false},
                {"id": "t1", "name": "Alpha", "completed": false},
                {"id": "t2", "name": "Bravo", "completed": false}
            ]'''

            tasks = client.get_tasks(sort_by="name", sort_order="asc")

            assert len(tasks) == 3
            assert tasks[0]['name'] == "Alpha"
            assert tasks[1]['name'] == "Bravo"
            assert tasks[2]['name'] == "Charlie"

    def test_sort_by_name_desc(self, client):
        """Test sorting tasks by name descending."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Alpha", "completed": false},
                {"id": "t2", "name": "Bravo", "completed": false},
                {"id": "t3", "name": "Charlie", "completed": false}
            ]'''

            tasks = client.get_tasks(sort_by="name", sort_order="desc")

            assert len(tasks) == 3
            assert tasks[0]['name'] == "Charlie"
            assert tasks[1]['name'] == "Bravo"
            assert tasks[2]['name'] == "Alpha"

    def test_sort_by_due_date_asc(self, client):
        """Test sorting tasks by due date ascending."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Task 1", "completed": false, "dueDate": "2025-01-15T00:00:00Z"},
                {"id": "t2", "name": "Task 2", "completed": false, "dueDate": ""},
                {"id": "t3", "name": "Task 3", "completed": false, "dueDate": "2025-01-10T00:00:00Z"}
            ]'''

            tasks = client.get_tasks(sort_by="due_date", sort_order="asc")

            assert len(tasks) == 3
            # Tasks with dates should come first, sorted
            assert tasks[0]['id'] == "t3"  # Jan 10
            assert tasks[1]['id'] == "t1"  # Jan 15
            assert tasks[2]['id'] == "t2"  # No date (should be last)

    def test_sort_by_defer_date(self, client):
        """Test sorting tasks by defer date."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Task 1", "completed": false, "deferDate": "2025-01-20T00:00:00Z"},
                {"id": "t2", "name": "Task 2", "completed": false, "deferDate": "2025-01-10T00:00:00Z"}
            ]'''

            tasks = client.get_tasks(sort_by="defer_date", sort_order="asc")

            assert tasks[0]['id'] == "t2"  # Jan 10
            assert tasks[1]['id'] == "t1"  # Jan 20

    def test_sort_invalid_field(self, client):
        """Test that invalid sort field raises ValueError."""
        with pytest.raises(ValueError, match="Invalid sort_by"):
            client.get_tasks(sort_by="invalid_field")

    def test_sort_invalid_order(self, client):
        """Test that invalid sort order raises ValueError."""
        with pytest.raises(ValueError, match="Invalid sort_order"):
            client.get_tasks(sort_by="name", sort_order="invalid")

    def test_no_sort_returns_original_order(self, client):
        """Test that omitting sort parameters preserves original order."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t3", "name": "Charlie", "completed": false},
                {"id": "t1", "name": "Alpha", "completed": false}
            ]'''

            tasks = client.get_tasks()

            # Should preserve OmniFocus order (no sorting)
            assert tasks[0]['id'] == "t3"
            assert tasks[1]['id'] == "t1"


    def test_sort_by_planned_date_asc(self, client):
        """Test sorting tasks by planned_date ascending with empty dates at end."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "No plan", "plannedDate": "", "completed": false},
                {"id": "t2", "name": "Later", "plannedDate": "2026-04-10T09:00:00", "completed": false},
                {"id": "t3", "name": "Sooner", "plannedDate": "2026-04-01T09:00:00", "completed": false}
            ]'''

            tasks = client.get_tasks(sort_by="planned_date", sort_order="asc")

            assert tasks[0]['id'] == "t3"
            assert tasks[1]['id'] == "t2"
            assert tasks[2]['id'] == "t1"  # empty date at end

    def test_sort_by_creation_date_desc(self, client):
        """Test sorting tasks by creation_date descending."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Old", "creationDate": "2026-03-01T09:00:00", "completed": false},
                {"id": "t2", "name": "New", "creationDate": "2026-04-01T09:00:00", "completed": false}
            ]'''

            tasks = client.get_tasks(sort_by="creation_date", sort_order="desc")

            assert tasks[0]['id'] == "t2"
            assert tasks[1]['id'] == "t1"

    def test_sort_by_modification_date_asc(self, client):
        """Test sorting tasks by modification_date ascending."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Recent", "modificationDate": "2026-04-01T09:00:00", "completed": false},
                {"id": "t2", "name": "Older", "modificationDate": "2026-03-01T09:00:00", "completed": false}
            ]'''

            tasks = client.get_tasks(sort_by="modification_date", sort_order="asc")

            assert tasks[0]['id'] == "t2"
            assert tasks[1]['id'] == "t1"


class TestProjectSorting:
    """Tests for project sorting options."""

    def test_sort_projects_by_name_asc(self, client):
        """Test sorting projects by name ascending."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "p2", "name": "Bravo Project", "status": "active"},
                {"id": "p1", "name": "Alpha Project", "status": "active"}
            ]'''

            projects = client.get_projects(sort_by="name", sort_order="asc")

            assert len(projects) == 2
            assert projects[0]['name'] == "Alpha Project"
            assert projects[1]['name'] == "Bravo Project"

    def test_sort_projects_by_name_desc(self, client):
        """Test sorting projects by name descending."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "p1", "name": "Alpha Project", "status": "active"},
                {"id": "p2", "name": "Bravo Project", "status": "active"}
            ]'''

            projects = client.get_projects(sort_by="name", sort_order="desc")

            assert projects[0]['name'] == "Bravo Project"
            assert projects[1]['name'] == "Alpha Project"

    def test_sort_projects_by_due_date_asc(self, client):
        """Test sorting projects by due_date ascending with empty dates at end."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "p1", "name": "No Due", "dueDate": "", "status": "active"},
                {"id": "p2", "name": "Later", "dueDate": "2026-04-10T09:00:00", "status": "active"},
                {"id": "p3", "name": "Sooner", "dueDate": "2026-04-01T09:00:00", "status": "active"}
            ]'''

            projects = client.get_projects(sort_by="due_date", sort_order="asc")

            assert projects[0]['id'] == "p3"
            assert projects[1]['id'] == "p2"
            assert projects[2]['id'] == "p1"  # empty date at end

    def test_sort_projects_by_planned_date_desc(self, client):
        """Test sorting projects by planned_date descending."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "p1", "name": "Early", "plannedDate": "2026-03-01T09:00:00", "status": "active"},
                {"id": "p2", "name": "Late", "plannedDate": "2026-04-01T09:00:00", "status": "active"}
            ]'''

            projects = client.get_projects(sort_by="planned_date", sort_order="desc")

            assert projects[0]['id'] == "p2"
            assert projects[1]['id'] == "p1"

    def test_sort_projects_invalid_field(self, client):
        """Test that invalid sort field raises ValueError."""
        with pytest.raises(ValueError, match="Invalid sort_by"):
            client.get_projects(sort_by="invalid")
