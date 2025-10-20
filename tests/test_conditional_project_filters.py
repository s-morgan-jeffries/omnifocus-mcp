"""Tests for conditional project filtering."""
import pytest
from unittest import mock

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


@pytest.fixture
def client():
    """Create a client with safety checks disabled."""
    return OmniFocusConnector(enable_safety_checks=False)


class TestConditionalProjectFilters:
    """Tests for conditional project filtering."""

    def test_min_task_count_filter(self, client):
        """Test filtering projects by minimum task count."""
        # Mock get_projects to return base projects
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "p1", "name": "Project 1", "status": "active"},
                {"id": "p2", "name": "Project 2", "status": "active"},
                {"id": "p3", "name": "Project 3", "status": "active"}
            ]'''

            # Mock get_tasks for each project
            with mock.patch.object(client, 'get_tasks') as mock_get_tasks:
                def get_tasks_side_effect(project_id, **kwargs):
                    if project_id == "p1":
                        return [{"id": "t1"}, {"id": "t2"}, {"id": "t3"}, {"id": "t4"}, {"id": "t5"}, {"id": "t6"}]
                    elif project_id == "p2":
                        return [{"id": "t1"}, {"id": "t2"}]
                    elif project_id == "p3":
                        return [{"id": "t1"}, {"id": "t2"}, {"id": "t3"}, {"id": "t4"}, {"id": "t5"}]
                    return []

                mock_get_tasks.side_effect = get_tasks_side_effect

                projects = client.get_projects(min_task_count=5)

                # Should return only projects with 5+ tasks
                assert len(projects) == 2
                assert projects[0]['id'] == "p1"
                assert projects[1]['id'] == "p3"

    def test_has_overdue_tasks_filter(self, client):
        """Test filtering projects that have overdue tasks."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "p1", "name": "Project 1", "status": "active"},
                {"id": "p2", "name": "Project 2", "status": "active"}
            ]'''

            with mock.patch.object(client, 'get_tasks') as mock_get_tasks:
                def get_tasks_side_effect(project_id, **kwargs):
                    if project_id == "p1":
                        # Has overdue task (past date)
                        return [{"id": "t1", "dueDate": "2024-01-01T00:00:00Z"}]
                    elif project_id == "p2":
                        # No overdue tasks (future date)
                        return [{"id": "t1", "dueDate": "2026-01-01T00:00:00Z"}]
                    return []

                mock_get_tasks.side_effect = get_tasks_side_effect

                projects = client.get_projects(has_overdue_tasks=True)

                # Should return only project with overdue tasks
                assert len(projects) == 1
                assert projects[0]['id'] == "p1"

    def test_has_no_due_dates_filter(self, client):
        """Test filtering projects with no upcoming deadlines."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "p1", "name": "Project 1", "status": "active"},
                {"id": "p2", "name": "Project 2", "status": "active"},
                {"id": "p3", "name": "Project 3", "status": "active"}
            ]'''

            with mock.patch.object(client, 'get_tasks') as mock_get_tasks:
                def get_tasks_side_effect(project_id, **kwargs):
                    if project_id == "p1":
                        return [{"id": "t1", "dueDate": ""}]
                    elif project_id == "p2":
                        return [{"id": "t1", "dueDate": "2026-01-01T00:00:00Z"}]
                    elif project_id == "p3":
                        return [{"id": "t1", "dueDate": ""}, {"id": "t2", "dueDate": ""}]
                    return []

                mock_get_tasks.side_effect = get_tasks_side_effect

                projects = client.get_projects(has_no_due_dates=True)

                # Should return projects where NO tasks have due dates
                assert len(projects) == 2
                assert projects[0]['id'] == "p1"
                assert projects[1]['id'] == "p3"

    def test_combined_conditional_filters(self, client):
        """Test combining multiple conditional filters."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "p1", "name": "Project 1", "status": "active"},
                {"id": "p2", "name": "Project 2", "status": "active"}
            ]'''

            with mock.patch.object(client, 'get_tasks') as mock_get_tasks:
                def get_tasks_side_effect(project_id, **kwargs):
                    if project_id == "p1":
                        # 6 tasks, 1 overdue
                        return [
                            {"id": "t1", "dueDate": "2024-01-01T00:00:00Z"},
                            {"id": "t2", "dueDate": ""},
                            {"id": "t3", "dueDate": ""},
                            {"id": "t4", "dueDate": ""},
                            {"id": "t5", "dueDate": ""},
                            {"id": "t6", "dueDate": ""}
                        ]
                    elif project_id == "p2":
                        # Only 3 tasks, no overdue
                        return [
                            {"id": "t1", "dueDate": ""},
                            {"id": "t2", "dueDate": ""},
                            {"id": "t3", "dueDate": ""}
                        ]
                    return []

                mock_get_tasks.side_effect = get_tasks_side_effect

                # Filter for projects with 5+ tasks AND overdue tasks
                projects = client.get_projects(min_task_count=5, has_overdue_tasks=True)

                assert len(projects) == 1
                assert projects[0]['id'] == "p1"

    def test_no_conditional_filters(self, client):
        """Test that omitting filters returns all projects."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "p1", "name": "Project 1", "status": "active"},
                {"id": "p2", "name": "Project 2", "status": "active"}
            ]'''

            projects = client.get_projects()

            # Should return all projects when no filters applied
            assert len(projects) == 2
