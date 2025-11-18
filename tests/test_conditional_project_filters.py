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

            # Mock batch task fetching
            with mock.patch.object(client, '_get_tasks_batch_for_filtering') as mock_batch:
                mock_batch.return_value = {
                    "p1": [{"id": "t1"}, {"id": "t2"}, {"id": "t3"}, {"id": "t4"}, {"id": "t5"}, {"id": "t6"}],
                    "p2": [{"id": "t1"}, {"id": "t2"}],
                    "p3": [{"id": "t1"}, {"id": "t2"}, {"id": "t3"}, {"id": "t4"}, {"id": "t5"}]
                }

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

            with mock.patch.object(client, '_get_tasks_batch_for_filtering') as mock_batch:
                mock_batch.return_value = {
                    "p1": [{"id": "t1", "dueDate": "2024-01-01T00:00:00Z"}],  # Overdue
                    "p2": [{"id": "t1", "dueDate": "2026-01-01T00:00:00Z"}]   # Future
                }

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

            with mock.patch.object(client, '_get_tasks_batch_for_filtering') as mock_batch:
                mock_batch.return_value = {
                    "p1": [{"id": "t1", "dueDate": ""}],
                    "p2": [{"id": "t1", "dueDate": "2026-01-01T00:00:00Z"}],
                    "p3": [{"id": "t1", "dueDate": ""}, {"id": "t2", "dueDate": ""}]
                }

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

            with mock.patch.object(client, '_get_tasks_batch_for_filtering') as mock_batch:
                mock_batch.return_value = {
                    "p1": [
                        {"id": "t1", "dueDate": "2024-01-01T00:00:00Z"},  # Overdue
                        {"id": "t2", "dueDate": ""},
                        {"id": "t3", "dueDate": ""},
                        {"id": "t4", "dueDate": ""},
                        {"id": "t5", "dueDate": ""},
                        {"id": "t6", "dueDate": ""}
                    ],
                    "p2": [
                        {"id": "t1", "dueDate": ""},
                        {"id": "t2", "dueDate": ""},
                        {"id": "t3", "dueDate": ""}
                    ]
                }

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


class TestBatchTaskFetching:
    """Tests for _get_tasks_batch_for_filtering optimization."""

    def test_batch_fetch_returns_tasks_grouped_by_project(self, client):
        """Test that batch method returns tasks grouped by project ID."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # Mock AppleScript response with JSON array of project task data
            mock_run.return_value = '''[
                {
                    "projectId": "p1",
                    "tasks": [
                        {"id": "t1", "projectId": "p1", "dueDate": "2025-01-15T00:00:00Z"},
                        {"id": "t2", "projectId": "p1", "dueDate": ""}
                    ]
                },
                {
                    "projectId": "p2",
                    "tasks": [
                        {"id": "t3", "projectId": "p2", "dueDate": "2025-02-01T00:00:00Z"}
                    ]
                },
                {
                    "projectId": "p3",
                    "tasks": []
                }
            ]'''

            result = client._get_tasks_batch_for_filtering(["p1", "p2", "p3"])

            # Verify structure
            assert isinstance(result, dict)
            assert len(result) == 3

            # Verify p1 tasks
            assert "p1" in result
            assert len(result["p1"]) == 2
            assert result["p1"][0]["id"] == "t1"
            assert result["p1"][0]["dueDate"] == "2025-01-15T00:00:00Z"
            assert result["p1"][1]["id"] == "t2"
            assert result["p1"][1]["dueDate"] == ""

            # Verify p2 tasks
            assert "p2" in result
            assert len(result["p2"]) == 1
            assert result["p2"][0]["id"] == "t3"

            # Verify p3 (empty)
            assert "p3" in result
            assert len(result["p3"]) == 0

    def test_batch_fetch_with_empty_project_list(self, client):
        """Test batch method with empty project list."""
        result = client._get_tasks_batch_for_filtering([])

        assert isinstance(result, dict)
        assert len(result) == 0

    def test_batch_fetch_generates_correct_applescript(self, client):
        """Test that batch method generates correct AppleScript with project ID checks."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'

            client._get_tasks_batch_for_filtering(["p1", "p2", "p3"])

            # Verify AppleScript was called once
            assert mock_run.call_count == 1

            # Verify script contains project ID checks
            script = mock_run.call_args[0][0]
            assert 'if projId is "p1"' in script
            assert 'or projId is "p2"' in script
            assert 'or projId is "p3"' in script

            # Verify script contains handlers at top level (not inside tell blocks)
            assert '-- Helper to format ISO date' in script
            assert 'on formatDate(d)' in script
            assert 'on joinList(theList, theDelimiter)' in script
            # Verify handlers come before tell block
            assert script.index('on formatDate') < script.index('tell application')

    def test_filter_projects_uses_batch_fetch(self, client):
        """Test that _filter_projects_by_conditions uses batch fetching."""
        projects = [
            {"id": "p1", "name": "Project 1"},
            {"id": "p2", "name": "Project 2"},
            {"id": "p3", "name": "Project 3"}
        ]

        with mock.patch.object(client, '_get_tasks_batch_for_filtering') as mock_batch:
            # Mock batch method to return task data
            mock_batch.return_value = {
                "p1": [{"id": "t1"}, {"id": "t2"}, {"id": "t3"}, {"id": "t4"}, {"id": "t5"}, {"id": "t6"}],
                "p2": [{"id": "t1"}, {"id": "t2"}],
                "p3": [{"id": "t1"}, {"id": "t2"}, {"id": "t3"}, {"id": "t4"}, {"id": "t5"}]
            }

            result = client._filter_projects_by_conditions(
                projects,
                min_task_count=5,
                has_overdue_tasks=None,
                has_no_due_dates=None
            )

            # Verify batch method was called once with all project IDs
            mock_batch.assert_called_once_with(["p1", "p2", "p3"])

            # Verify correct projects returned (5+ tasks)
            assert len(result) == 2
            assert result[0]["id"] == "p1"
            assert result[1]["id"] == "p3"

    def test_batch_fetch_optimization_eliminates_n_plus_one(self, client):
        """Test that batch optimization eliminates N+1 query pattern."""
        projects = [{"id": f"p{i}", "name": f"Project {i}"} for i in range(1, 11)]

        with mock.patch.object(client, '_get_tasks_batch_for_filtering') as mock_batch:
            # Mock batch method to return empty tasks
            mock_batch.return_value = {f"p{i}": [] for i in range(1, 11)}

            client._filter_projects_by_conditions(
                projects,
                min_task_count=1,
                has_overdue_tasks=None,
                has_no_due_dates=None
            )

            # Verify batch method called ONCE (not 10 times)
            assert mock_batch.call_count == 1

            # Verify called with all project IDs
            called_ids = mock_batch.call_args[0][0]
            assert len(called_ids) == 10
            assert called_ids == [f"p{i}" for i in range(1, 11)]
