"""Integration tests for performance optimization features.

Tests include_task_health, include_last_activity, query filter, and
batch write benchmarks against a real OmniFocus instance.

Prerequisites:
    export OMNIFOCUS_TEST_MODE=true
    export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"
    OmniFocus must be running with test database active.

Usage:
    pytest tests/test_integration_performance.py -v
    pytest tests/test_integration_performance.py::TestBatchWritePerformance -v -s
"""
import os
import time
import uuid
import warnings
import pytest

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector, run_applescript


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


# ============================================================================
# Batch Write Performance Benchmarks (#215)
# ============================================================================

@pytest.fixture(scope="class")
def ensure_bench_tag():
    """Ensure bench-tag exists in OmniFocus for tag benchmarks."""
    try:
        run_applescript('''
            tell application "OmniFocus"
                tell front document
                    try
                        first flattened tag whose name is "bench-tag"
                    on error
                        make new tag with properties {name:"bench-tag"}
                    end try
                end tell
            end tell
        ''')
    except Exception as e:
        warnings.warn(f"Failed to create bench-tag: {e}")


def _create_n_tasks(client, n):
    """Create a project with N tasks, return (project_id, task_ids)."""
    project_name = f"bench-write-{uuid.uuid4()}"
    project_id = client.create_project(project_name)
    task_ids = []
    for i in range(n):
        tid = client.create_task(f"bench-task-{i}", project_id=project_id)
        task_ids.append(tid)
    return project_id, task_ids


def _create_n_projects(client, n):
    """Create N projects, return list of project IDs."""
    project_ids = []
    for i in range(n):
        pid = client.create_project(f"bench-proj-{uuid.uuid4()}-{i}")
        project_ids.append(pid)
    return project_ids


class TestBatchWritePerformance:
    """Benchmark batch write operations with or-chain optimization (#215).

    Measures real-world performance of update_tasks() and update_projects()
    for bulk-settable fields (or-chain) vs per-task fields (repeat loop).
    Each benchmark runs 3 iterations and reports mean time.

    Run with: pytest ... -v -s  (need -s for benchmark output)
    """

    @pytest.fixture(scope="function")
    def bench_tasks_5(self, client):
        project_id, task_ids = _create_n_tasks(client, 5)
        yield task_ids
        try:
            client.delete_tasks(task_ids)
        except Exception:
            pass
        try:
            client.delete_projects(project_id)
        except Exception:
            pass

    @pytest.fixture(scope="function")
    def bench_tasks_10(self, client):
        project_id, task_ids = _create_n_tasks(client, 10)
        yield task_ids
        try:
            client.delete_tasks(task_ids)
        except Exception:
            pass
        try:
            client.delete_projects(project_id)
        except Exception:
            pass

    @pytest.fixture(scope="function")
    def bench_projects_5(self, client):
        project_ids = _create_n_projects(client, 5)
        yield project_ids
        try:
            client.delete_projects(project_ids)
        except Exception:
            pass

    @pytest.fixture(scope="function")
    def bench_projects_10(self, client):
        project_ids = _create_n_projects(client, 10)
        yield project_ids
        try:
            client.delete_projects(project_ids)
        except Exception:
            pass

    # --- Task benchmarks: bulk (or-chain) ---

    def test_update_tasks_bulk_flagged_n5(self, client, bench_tasks_5):
        times = []
        for _ in range(3):
            start = time.perf_counter()
            client.update_tasks(bench_tasks_5, flagged=True)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            client.update_tasks(bench_tasks_5, flagged=False)
        mean = sum(times) / len(times)
        print(f"\nBENCHMARK: update_tasks(flagged) N=5 mean={mean:.3f}s times={[f'{t:.3f}' for t in times]}")
        assert mean < 10  # Sanity check

    def test_update_tasks_bulk_flagged_n10(self, client, bench_tasks_10):
        times = []
        for _ in range(3):
            start = time.perf_counter()
            client.update_tasks(bench_tasks_10, flagged=True)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            client.update_tasks(bench_tasks_10, flagged=False)
        mean = sum(times) / len(times)
        print(f"\nBENCHMARK: update_tasks(flagged) N=10 mean={mean:.3f}s times={[f'{t:.3f}' for t in times]}")
        assert mean < 10

    # --- Task benchmarks: per-task (repeat loop) ---

    def test_update_tasks_per_task_tags_n5(self, client, bench_tasks_5, ensure_bench_tag):
        times = []
        for _ in range(3):
            start = time.perf_counter()
            client.update_tasks(bench_tasks_5, add_tags=["bench-tag"])
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            client.update_tasks(bench_tasks_5, remove_tags=["bench-tag"])
        mean = sum(times) / len(times)
        print(f"\nBENCHMARK: update_tasks(add_tags) N=5 mean={mean:.3f}s times={[f'{t:.3f}' for t in times]}")
        assert mean < 30

    def test_update_tasks_per_task_tags_n10(self, client, bench_tasks_10, ensure_bench_tag):
        times = []
        for _ in range(3):
            start = time.perf_counter()
            client.update_tasks(bench_tasks_10, add_tags=["bench-tag"])
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            client.update_tasks(bench_tasks_10, remove_tags=["bench-tag"])
        mean = sum(times) / len(times)
        print(f"\nBENCHMARK: update_tasks(add_tags) N=10 mean={mean:.3f}s times={[f'{t:.3f}' for t in times]}")
        assert mean < 30

    # --- Project benchmarks: bulk (or-chain) ---

    def test_update_projects_bulk_status_n5(self, client, bench_projects_5):
        times = []
        for _ in range(3):
            start = time.perf_counter()
            client.update_projects(bench_projects_5, status="on_hold")
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            client.update_projects(bench_projects_5, status="active")
        mean = sum(times) / len(times)
        print(f"\nBENCHMARK: update_projects(status) N=5 mean={mean:.3f}s times={[f'{t:.3f}' for t in times]}")
        assert mean < 10

    def test_update_projects_bulk_status_n10(self, client, bench_projects_10):
        times = []
        for _ in range(3):
            start = time.perf_counter()
            client.update_projects(bench_projects_10, status="on_hold")
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            client.update_projects(bench_projects_10, status="active")
        mean = sum(times) / len(times)
        print(f"\nBENCHMARK: update_projects(status) N=10 mean={mean:.3f}s times={[f'{t:.3f}' for t in times]}")
        assert mean < 10

    def test_update_projects_bulk_sequential_n5(self, client, bench_projects_5):
        times = []
        for _ in range(3):
            start = time.perf_counter()
            client.update_projects(bench_projects_5, sequential=True)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            client.update_projects(bench_projects_5, sequential=False)
        mean = sum(times) / len(times)
        print(f"\nBENCHMARK: update_projects(sequential) N=5 mean={mean:.3f}s times={[f'{t:.3f}' for t in times]}")
        assert mean < 10

    def test_update_projects_bulk_sequential_n10(self, client, bench_projects_10):
        times = []
        for _ in range(3):
            start = time.perf_counter()
            client.update_projects(bench_projects_10, sequential=True)
            elapsed = time.perf_counter() - start
            times.append(elapsed)
            client.update_projects(bench_projects_10, sequential=False)
        mean = sum(times) / len(times)
        print(f"\nBENCHMARK: update_projects(sequential) N=10 mean={mean:.3f}s times={[f'{t:.3f}' for t in times]}")
        assert mean < 10
