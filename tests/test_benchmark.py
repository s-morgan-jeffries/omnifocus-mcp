"""Performance benchmarks for OmniFocus MCP operations.

Measures timing of all major operations against a real OmniFocus instance.
Reports results with comparison to documented baselines from CLAUDE.md.

Prerequisites:
    export OMNIFOCUS_TEST_MODE=true
    export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"
    OmniFocus must be running with test database active.

Usage:
    pytest tests/test_benchmark.py -v -s
"""
import os
import statistics
import subprocess
import time
import uuid
import warnings

import pytest

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


pytestmark = pytest.mark.skipif(
    os.environ.get('OMNIFOCUS_TEST_MODE', '').lower() != 'true',
    reason="Benchmarks require OMNIFOCUS_TEST_MODE=true"
)

# Documented baselines from CLAUDE.md (seconds)
BASELINES = {
    "get_tasks (all)": 2.3,
    "get_projects (all)": 0.9,
    "get_projects (task_health)": None,  # No documented baseline yet
    "get_projects (last_activity)": None,
    "get_tasks (flagged)": None,
    "get_tasks (query)": None,
    "create_task": 0.4,
    "update_task": 0.4,
    "delete_tasks": 0.4,
    "create_project": 0.4,
    "update_project": 0.4,
    "delete_projects": 0.4,
    "get_folders": None,
    "get_tags": None,
    "get_perspectives": None,
}

ITERATIONS = 3
READ_ITERATIONS = 1  # Single iteration for slow read operations
SLOWDOWN_THRESHOLD = 2.0  # Warn if >2x slower than baseline


def _median_time(func, iterations=ITERATIONS):
    """Run func multiple times and return median elapsed time."""
    times = []
    result = None
    for _ in range(iterations):
        start = time.perf_counter()
        result = func()
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    return statistics.median(times), result


def _report(name, elapsed, baseline=None):
    """Print benchmark result with optional baseline comparison."""
    msg = f"  {name}: {elapsed:.3f}s"
    if baseline is not None:
        ratio = elapsed / baseline
        if ratio > SLOWDOWN_THRESHOLD:
            msg += f" (SLOW: {ratio:.1f}x baseline {baseline:.1f}s)"
        else:
            msg += f" ({ratio:.1f}x baseline {baseline:.1f}s)"
    print(msg)


@pytest.fixture(scope="module")
def client():
    return OmniFocusConnector(enable_safety_checks=True)


@pytest.fixture(scope="module")
def test_project(client):
    """Create a project with tasks for benchmarking write operations."""
    name = f"Benchmark {uuid.uuid4()}"
    project_id = client.create_project(name)
    yield project_id
    try:
        client.delete_projects(project_id)
    except Exception as e:
        warnings.warn(f"Failed to clean up benchmark project: {e}")


class TestReadBenchmarks:
    """Benchmark read operations (non-destructive)."""

    def test_get_tasks_all(self, client):
        """Benchmark get_tasks() with no filters."""
        try:
            elapsed, tasks = _median_time(
                lambda: client.get_tasks(timeout=300), iterations=READ_ITERATIONS
            )
            _report("get_tasks (all)", elapsed, BASELINES["get_tasks (all)"])
            print(f"    returned {len(tasks)} tasks")
        except subprocess.TimeoutExpired:
            print("  get_tasks (all): TIMEOUT (>300s) — database too large for unfiltered query")
            pytest.skip("get_tasks() timed out — database too large for unfiltered query")

    def test_get_tasks_flagged(self, client):
        """Benchmark get_tasks() with flagged filter."""
        elapsed, tasks = _median_time(
            lambda: client.get_tasks(flagged_only=True, timeout=300),
            iterations=READ_ITERATIONS,
        )
        _report("get_tasks (flagged)", elapsed, BASELINES["get_tasks (flagged)"])
        print(f"    returned {len(tasks)} tasks")

    def test_get_tasks_query(self, client):
        """Benchmark get_tasks() with query filter."""
        elapsed, tasks = _median_time(
            lambda: client.get_tasks(query="test", timeout=300),
            iterations=READ_ITERATIONS,
        )
        _report("get_tasks (query)", elapsed, BASELINES["get_tasks (query)"])
        print(f"    returned {len(tasks)} tasks")

    def test_get_projects_all(self, client):
        """Benchmark get_projects() baseline."""
        elapsed, projects = _median_time(
            lambda: client.get_projects(timeout=300), iterations=READ_ITERATIONS
        )
        _report("get_projects (all)", elapsed, BASELINES["get_projects (all)"])
        print(f"    returned {len(projects)} projects")

    def test_get_projects_task_health(self, client):
        """Benchmark get_projects() with include_task_health."""
        elapsed, projects = _median_time(
            lambda: client.get_projects(include_task_health=True, timeout=300),
            iterations=READ_ITERATIONS,
        )
        _report("get_projects (task_health)", elapsed, BASELINES["get_projects (task_health)"])
        print(f"    returned {len(projects)} projects")

    def test_get_projects_last_activity(self, client):
        """Benchmark get_projects() with include_last_activity."""
        elapsed, projects = _median_time(
            lambda: client.get_projects(include_last_activity=True, timeout=300),
            iterations=READ_ITERATIONS,
        )
        _report("get_projects (last_activity)", elapsed, BASELINES["get_projects (last_activity)"])
        print(f"    returned {len(projects)} projects")

    def test_get_folders(self, client):
        """Benchmark get_folders()."""
        elapsed, folders = _median_time(lambda: client.get_folders())
        _report("get_folders", elapsed, BASELINES["get_folders"])
        print(f"    returned {len(folders)} folders")

    def test_get_tags(self, client):
        """Benchmark get_tags()."""
        elapsed, tags = _median_time(lambda: client.get_tags())
        _report("get_tags", elapsed, BASELINES["get_tags"])
        print(f"    returned {len(tags)} tags")

    def test_get_perspectives(self, client):
        """Benchmark get_perspectives()."""
        elapsed, perspectives = _median_time(lambda: client.get_perspectives())
        _report("get_perspectives", elapsed, BASELINES["get_perspectives"])
        print(f"    returned {len(perspectives)} perspectives")


class TestWriteBenchmarks:
    """Benchmark write operations (creates and cleans up test data)."""

    def test_create_task(self, client, test_project):
        """Benchmark create_task()."""
        task_ids = []

        def create():
            tid = client.create_task(
                f"Bench task {uuid.uuid4()}", project_id=test_project
            )
            task_ids.append(tid)
            return tid

        elapsed, _ = _median_time(create)
        _report("create_task", elapsed, BASELINES["create_task"])

        # Cleanup
        for tid in task_ids:
            try:
                client.delete_tasks(tid)
            except Exception:
                pass

    def test_update_task(self, client, test_project):
        """Benchmark update_task()."""
        task_id = client.create_task(
            f"Bench update {uuid.uuid4()}", project_id=test_project
        )
        try:
            elapsed, _ = _median_time(
                lambda: client.update_task(task_id, flagged=True)
            )
            _report("update_task", elapsed, BASELINES["update_task"])
        finally:
            try:
                client.delete_tasks(task_id)
            except Exception:
                pass

    def test_delete_task(self, client, test_project):
        """Benchmark delete_tasks() (single task)."""
        times = []
        for _ in range(ITERATIONS):
            task_id = client.create_task(
                f"Bench delete {uuid.uuid4()}", project_id=test_project
            )
            start = time.perf_counter()
            client.delete_tasks(task_id)
            times.append(time.perf_counter() - start)
        elapsed = statistics.median(times)
        _report("delete_tasks", elapsed, BASELINES["delete_tasks"])

    def test_create_project(self, client):
        """Benchmark create_project()."""
        project_ids = []

        def create():
            pid = client.create_project(f"Bench proj {uuid.uuid4()}")
            project_ids.append(pid)
            return pid

        elapsed, _ = _median_time(create)
        _report("create_project", elapsed, BASELINES["create_project"])

        for pid in project_ids:
            try:
                client.delete_projects(pid)
            except Exception:
                pass

    def test_update_project(self, client, test_project):
        """Benchmark update_project()."""
        elapsed, _ = _median_time(
            lambda: client.update_project(test_project, flagged=True)
        )
        _report("update_project", elapsed, BASELINES["update_project"])

    def test_delete_project(self, client):
        """Benchmark delete_projects() (single project)."""
        times = []
        for _ in range(ITERATIONS):
            pid = client.create_project(f"Bench del proj {uuid.uuid4()}")
            start = time.perf_counter()
            client.delete_projects(pid)
            times.append(time.perf_counter() - start)
        elapsed = statistics.median(times)
        _report("delete_projects", elapsed, BASELINES["delete_projects"])
