"""Integration tests for performance optimization features.

Tests include_task_health, include_last_activity, and query filter
against a real OmniFocus instance. These catch AppleScript-level bugs
that unit tests with mocked run_applescript() miss.

Prerequisites:
    export OMNIFOCUS_TEST_MODE=true
    export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"
    OmniFocus must be running with test database active.

Usage:
    pytest tests/test_integration_performance.py -v
"""
import os
import uuid
import warnings
import pytest

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


pytestmark = pytest.mark.skipif(
    os.environ.get('OMNIFOCUS_TEST_MODE', '').lower() != 'true',
    reason="Real OmniFocus tests require OMNIFOCUS_TEST_MODE=true"
)


@pytest.fixture(scope="module")
def client():
    return OmniFocusConnector(enable_safety_checks=True)


@pytest.fixture(scope="function")
def project_with_tasks(client):
    """Create a project with several tasks for health testing."""
    name = f"Health Test {uuid.uuid4()}"
    project_id = client.create_project(name)

    task_ids = []
    # Create a few tasks
    for i in range(3):
        tid = client.create_task(f"Task {i+1} for health", project_id=project_id)
        task_ids.append(tid)

    yield project_id, task_ids

    # Cleanup
    for tid in task_ids:
        try:
            client.delete_tasks(tid)
        except Exception:
            pass
    try:
        client.delete_projects(project_id)
    except Exception as e:
        warnings.warn(f"Failed to clean up project {project_id}: {e}")


class TestIncludeTaskHealthIntegration:
    """Test include_task_health against real OmniFocus."""

    def test_task_health_returns_counts(self, client, project_with_tasks):
        """include_task_health should return integer counts for a real project."""
        project_id, task_ids = project_with_tasks
        projects = client.get_projects(
            project_id=project_id,
            include_task_health=True,
        )
        assert len(projects) == 1
        proj = projects[0]

        assert isinstance(proj['remainingCount'], int)
        assert isinstance(proj['availableCount'], int)
        assert isinstance(proj['overdueCount'], int)
        assert isinstance(proj['deferredCount'], int)
        assert isinstance(proj['hasDeferredOnly'], bool)

        # With 3 active tasks, remaining should be >= 3
        assert proj['remainingCount'] >= 3
        assert proj['availableCount'] >= 1

    def test_task_health_absent_by_default(self, client, project_with_tasks):
        """Without include_task_health, health fields should not appear."""
        project_id, _ = project_with_tasks
        projects = client.get_projects(project_id=project_id)
        assert len(projects) == 1
        assert 'remainingCount' not in projects[0]

    def test_task_health_all_projects(self, client):
        """include_task_health should work across all projects without error."""
        projects = client.get_projects(include_task_health=True)
        assert len(projects) > 0
        for proj in projects:
            assert 'remainingCount' in proj
            assert 'availableCount' in proj


class TestIncludeLastActivityIntegration:
    """Test include_last_activity against real OmniFocus."""

    def test_last_activity_returns_date_or_null(self, client, project_with_tasks):
        """include_last_activity should populate lastActivityDate."""
        project_id, _ = project_with_tasks
        projects = client.get_projects(
            project_id=project_id,
            include_last_activity=True,
        )
        assert len(projects) == 1
        # With tasks created, lastActivityDate should be populated
        assert projects[0]['lastActivityDate'] is not None

    def test_last_activity_null_by_default(self, client, project_with_tasks):
        """Without include_last_activity, lastActivityDate should be null."""
        project_id, _ = project_with_tasks
        projects = client.get_projects(project_id=project_id)
        assert len(projects) == 1
        assert projects[0]['lastActivityDate'] is None


class TestQueryFilterIntegration:
    """Test AppleScript-side query filtering against real OmniFocus."""

    def test_query_filters_by_name(self, client, project_with_tasks):
        """Query should filter tasks by name in AppleScript."""
        _, task_ids = project_with_tasks
        # Search for the known task name pattern
        tasks = client.get_tasks(query="Task 1 for health")
        matching = [t for t in tasks if t['id'] in task_ids]
        assert len(matching) >= 1

    def test_query_returns_empty_for_nonsense(self, client):
        """Query with gibberish should return no tasks."""
        tasks = client.get_tasks(query="xyzzy_no_match_12345")
        assert len(tasks) == 0

    def test_query_combined_with_flagged(self, client, project_with_tasks):
        """Query combined with flagged_only should work (both in AppleScript)."""
        # Should not error even if no flagged tasks match
        tasks = client.get_tasks(query="health", flagged_only=True)
        assert isinstance(tasks, list)
