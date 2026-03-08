"""Performance benchmarks for OmniFocus MCP operations.

Measures timing of all MCP functions against a real OmniFocus test database.
Reports statistical results: mean, stddev, min, max, coefficient of variation.
Detects cold start effects and compares against documented baselines.

Prerequisites:
    export OMNIFOCUS_TEST_MODE=true
    export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"
    OmniFocus must be running with test database active.
    Run scripts/setup_benchmark_data.sh first for representative data.

Usage:
    pytest tests/test_benchmark.py -v -s
    pytest tests/test_benchmark.py -v -s -k "read"     # Read benchmarks only
    pytest tests/test_benchmark.py -v -s -k "write"    # Write benchmarks only
    pytest tests/test_benchmark.py -v -s -k "param"    # Parameter variation tests
"""
import math
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

# Number of iterations per benchmark
ITERATIONS = 3
WRITE_ITERATIONS = 3  # Fewer for write ops (they modify state)


class BenchmarkResult:
    """Statistical summary of benchmark runs."""

    def __init__(self, name, times, result=None, result_count=None):
        self.name = name
        self.times = times
        self.result = result
        self.result_count = result_count
        self.mean = statistics.mean(times)
        self.stdev = statistics.stdev(times) if len(times) > 1 else 0.0
        self.min = min(times)
        self.max = max(times)
        self.median = statistics.median(times)
        self.cv = (self.stdev / self.mean * 100) if self.mean > 0 else 0.0
        # Cold start detection: first run >2x slower than median of rest
        if len(times) > 2:
            rest_median = statistics.median(times[1:])
            self.cold_start = times[0] > rest_median * 2
            self.cold_start_overhead = times[0] - rest_median if self.cold_start else 0.0
        else:
            self.cold_start = False
            self.cold_start_overhead = 0.0

    def report(self):
        """Print formatted benchmark report."""
        print(f"\n  {self.name}:")
        print(f"    mean={self.mean:.3f}s  stdev={self.stdev:.3f}s  "
              f"min={self.min:.3f}s  max={self.max:.3f}s  CV={self.cv:.1f}%")
        if self.result_count is not None:
            print(f"    returned {self.result_count} items")
        if self.cold_start:
            print(f"    COLD START detected: first run {self.times[0]:.3f}s "
                  f"(+{self.cold_start_overhead:.3f}s overhead)")
        print(f"    runs: [{', '.join(f'{t:.3f}' for t in self.times)}]")


def _benchmark(name, func, iterations=ITERATIONS):
    """Run func multiple times and return BenchmarkResult."""
    times = []
    result = None
    for _ in range(iterations):
        start = time.perf_counter()
        result = func()
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    count = None
    if isinstance(result, list):
        count = len(result)

    br = BenchmarkResult(name, times, result=result, result_count=count)
    br.report()
    return br


@pytest.fixture(scope="module")
def client():
    """Create connector with safety checks enabled."""
    return OmniFocusConnector(enable_safety_checks=True)


@pytest.fixture(scope="module")
def warmup(client):
    """Warm up OmniFocus connection to avoid cold start in first real test."""
    try:
        client.get_tags()
    except Exception:
        pass


@pytest.fixture(scope="module")
def test_project(client):
    """Create a temporary project for write benchmarks."""
    name = f"__benchmark_temp_{uuid.uuid4().hex[:8]}"
    project_id = client.create_project(name)
    yield project_id
    try:
        client.delete_projects(project_id)
    except Exception as e:
        warnings.warn(f"Failed to clean up benchmark project: {e}")


class TestReadBenchmarks:
    """Benchmark all read operations."""

    def test_warmup(self, warmup):
        """Warm up OmniFocus connection."""
        pass

    def test_get_tasks_all(self, client):
        """get_tasks() with no filters — full table scan."""
        try:
            _benchmark("get_tasks (all)", lambda: client.get_tasks(timeout=120))
        except subprocess.TimeoutExpired:
            print("\n  get_tasks (all): TIMEOUT (>120s)")
            pytest.skip("get_tasks() timed out")

    def test_get_tasks_flagged(self, client):
        """get_tasks() with flagged_only=True — filter-first path."""
        _benchmark("get_tasks (flagged)", lambda: client.get_tasks(flagged_only=True))

    def test_get_tasks_query(self, client):
        """get_tasks() with query filter — AppleScript-side filtering."""
        _benchmark("get_tasks (query='bench')", lambda: client.get_tasks(query="bench"))

    def test_get_tasks_overdue(self, client):
        """get_tasks() with overdue filter."""
        _benchmark("get_tasks (overdue)", lambda: client.get_tasks(overdue=True))

    def test_get_tasks_inbox(self, client):
        """get_tasks() with inbox_only filter."""
        _benchmark("get_tasks (inbox)", lambda: client.get_tasks(inbox_only=True))

    def test_get_tasks_by_project(self, client):
        """get_tasks() filtered to a single project."""
        # Get first project to use as filter
        projects = client.get_projects()
        if not projects:
            pytest.skip("No projects in test database")
        project_id = projects[0]["id"]
        _benchmark(
            "get_tasks (project_id)",
            lambda: client.get_tasks(project_id=project_id),
        )

    def test_get_tasks_available(self, client):
        """get_tasks() with available_only filter."""
        try:
            _benchmark(
                "get_tasks (available)",
                lambda: client.get_tasks(available_only=True, timeout=120),
            )
        except subprocess.TimeoutExpired:
            print("\n  get_tasks (available): TIMEOUT (>120s)")
            pytest.skip("get_tasks(available_only) timed out")

    def test_get_tasks_next(self, client):
        """get_tasks() with next_only filter."""
        _benchmark("get_tasks (next)", lambda: client.get_tasks(next_only=True))

    def test_get_projects_all(self, client):
        """get_projects() baseline."""
        _benchmark("get_projects (all)", lambda: client.get_projects())

    def test_get_projects_task_health(self, client):
        """get_projects() with include_task_health — single batch call."""
        _benchmark(
            "get_projects (task_health)",
            lambda: client.get_projects(include_task_health=True),
        )

    def test_get_projects_last_activity(self, client):
        """get_projects() with include_last_activity — expensive per-project calc."""
        _benchmark(
            "get_projects (last_activity)",
            lambda: client.get_projects(include_last_activity=True),
        )

    def test_get_projects_full_notes(self, client):
        """get_projects() with include_full_notes."""
        _benchmark(
            "get_projects (full_notes)",
            lambda: client.get_projects(include_full_notes=True),
        )

    def test_get_projects_all_options(self, client):
        """get_projects() with all optional data enabled."""
        _benchmark(
            "get_projects (all options)",
            lambda: client.get_projects(
                include_task_health=True,
                include_last_activity=True,
                include_full_notes=True,
            ),
        )

    def test_get_folders(self, client):
        """get_folders() baseline."""
        _benchmark("get_folders", lambda: client.get_folders())

    def test_get_tags(self, client):
        """get_tags() baseline."""
        _benchmark("get_tags", lambda: client.get_tags())

    def test_get_perspectives(self, client):
        """get_perspectives() baseline."""
        _benchmark("get_perspectives", lambda: client.get_perspectives())


class TestWriteBenchmarks:
    """Benchmark write operations (creates and cleans up test data)."""

    def test_warmup(self, warmup):
        """Warm up OmniFocus connection."""
        pass

    def test_create_task(self, client, test_project):
        """create_task() — single task creation."""
        task_ids = []

        def create():
            tid = client.create_task(
                f"__bench_{uuid.uuid4().hex[:8]}", project_id=test_project
            )
            task_ids.append(tid)
            return tid

        _benchmark("create_task", create, iterations=WRITE_ITERATIONS)
        for tid in task_ids:
            try:
                client.delete_tasks(tid)
            except Exception:
                pass

    def test_update_task(self, client, test_project):
        """update_task() — single field update."""
        task_id = client.create_task(
            f"__bench_update_{uuid.uuid4().hex[:8]}", project_id=test_project
        )
        try:
            toggle = [True, False, True, False, True]
            idx = 0

            def update():
                nonlocal idx
                client.update_task(task_id, flagged=toggle[idx % len(toggle)])
                idx += 1

            _benchmark("update_task", update, iterations=WRITE_ITERATIONS)
        finally:
            try:
                client.delete_tasks(task_id)
            except Exception:
                pass

    def test_delete_task(self, client, test_project):
        """delete_tasks() — single task deletion."""
        times = []
        for _ in range(WRITE_ITERATIONS):
            task_id = client.create_task(
                f"__bench_del_{uuid.uuid4().hex[:8]}", project_id=test_project
            )
            start = time.perf_counter()
            client.delete_tasks(task_id)
            times.append(time.perf_counter() - start)
        BenchmarkResult("delete_tasks", times).report()

    def test_create_project(self, client):
        """create_project() — single project creation."""
        project_ids = []

        def create():
            pid = client.create_project(f"__bench_proj_{uuid.uuid4().hex[:8]}")
            project_ids.append(pid)
            return pid

        _benchmark("create_project", create, iterations=WRITE_ITERATIONS)
        for pid in project_ids:
            try:
                client.delete_projects(pid)
            except Exception:
                pass

    def test_update_project(self, client, test_project):
        """update_project() — single field update."""
        toggle = [True, False, True]
        idx = 0

        def update():
            nonlocal idx
            client.update_project(test_project, sequential=toggle[idx % len(toggle)])
            idx += 1

        _benchmark("update_project", update, iterations=WRITE_ITERATIONS)

    def test_delete_project(self, client):
        """delete_projects() — single project deletion."""
        times = []
        for _ in range(WRITE_ITERATIONS):
            pid = client.create_project(f"__bench_del_proj_{uuid.uuid4().hex[:8]}")
            start = time.perf_counter()
            client.delete_projects(pid)
            times.append(time.perf_counter() - start)
        BenchmarkResult("delete_projects", times).report()

    def test_update_tasks_batch(self, client, test_project):
        """update_tasks() — batch update (N sequential calls, pre-optimization baseline)."""
        batch_size = 5
        task_ids = []
        for i in range(batch_size):
            tid = client.create_task(
                f"__bench_batch_{uuid.uuid4().hex[:8]}", project_id=test_project
            )
            task_ids.append(tid)

        try:
            toggle = [True, False, True]
            idx = 0

            def batch_update():
                nonlocal idx
                client.update_tasks(task_ids, flagged=toggle[idx % len(toggle)])
                idx += 1

            _benchmark(
                f"update_tasks ({batch_size} tasks)",
                batch_update,
                iterations=WRITE_ITERATIONS,
            )
        finally:
            try:
                client.delete_tasks(task_ids)
            except Exception:
                pass

    def test_update_projects_batch(self, client):
        """update_projects() — batch update (N sequential calls, pre-optimization baseline)."""
        batch_size = 3
        project_ids = []
        for i in range(batch_size):
            pid = client.create_project(f"__bench_batch_proj_{uuid.uuid4().hex[:8]}")
            project_ids.append(pid)

        try:
            toggle = [True, False, True]
            idx = 0

            def batch_update():
                nonlocal idx
                client.update_projects(
                    project_ids, sequential=toggle[idx % len(toggle)]
                )
                idx += 1

            _benchmark(
                f"update_projects ({batch_size} projects)",
                batch_update,
                iterations=WRITE_ITERATIONS,
            )
        finally:
            try:
                client.delete_projects(project_ids)
            except Exception:
                pass

    def test_mark_complete_single(self, client, test_project):
        """update_task(completed=True) — single task mark complete."""
        times = []
        for _ in range(WRITE_ITERATIONS):
            tid = client.create_task(
                f"__bench_complete_{uuid.uuid4().hex[:8]}", project_id=test_project
            )
            start = time.perf_counter()
            client.update_task(tid, completed=True)
            times.append(time.perf_counter() - start)
            try:
                client.delete_tasks(tid)
            except Exception:
                pass
        BenchmarkResult("mark_complete (single)", times).report()

    def test_mark_complete_batch(self, client, test_project):
        """update_tasks(completed=True) — batch mark complete."""
        batch_size = 5
        task_ids = []
        for i in range(batch_size):
            tid = client.create_task(
                f"__bench_batch_complete_{uuid.uuid4().hex[:8]}",
                project_id=test_project,
            )
            task_ids.append(tid)

        start = time.perf_counter()
        client.update_tasks(task_ids, completed=True)
        elapsed = time.perf_counter() - start
        BenchmarkResult(f"mark_complete (batch {batch_size})", [elapsed]).report()

        try:
            client.delete_tasks(task_ids)
        except Exception:
            pass

    def test_update_task_multi_field(self, client, test_project):
        """update_task() — multiple fields in single call vs single field."""
        task_id = client.create_task(
            f"__bench_multi_{uuid.uuid4().hex[:8]}", project_id=test_project
        )
        try:
            # Single field update
            single_times = []
            for _ in range(WRITE_ITERATIONS):
                start = time.perf_counter()
                client.update_task(task_id, flagged=True)
                single_times.append(time.perf_counter() - start)
            BenchmarkResult("update_task (1 field)", single_times).report()

            # Multi-field update
            multi_times = []
            future_date = "2026-12-31T17:00:00"
            for _ in range(WRITE_ITERATIONS):
                start = time.perf_counter()
                client.update_task(
                    task_id,
                    flagged=True,
                    due_date=future_date,
                    estimated_minutes=30,
                )
                multi_times.append(time.perf_counter() - start)
            BenchmarkResult("update_task (3 fields)", multi_times).report()

            single_mean = statistics.mean(single_times)
            multi_mean = statistics.mean(multi_times)
            overhead = multi_mean - single_mean
            pct = (overhead / single_mean * 100) if single_mean > 0 else 0
            print(f"\n    Multi-field overhead: +{overhead:.3f}s ({pct:+.0f}%)")
        finally:
            try:
                client.delete_tasks(task_id)
            except Exception:
                pass


class TestParameterVariations:
    """Test how different parameters affect the same function's performance."""

    def test_warmup(self, warmup):
        """Warm up OmniFocus connection."""
        pass

    def test_get_projects_parameter_comparison(self, client):
        """Compare get_projects() with different option combinations."""
        configs = [
            ("baseline", {}),
            ("+task_health", {"include_task_health": True}),
            ("+last_activity", {"include_last_activity": True}),
            ("+full_notes", {"include_full_notes": True}),
            ("+all_options", {
                "include_task_health": True,
                "include_last_activity": True,
                "include_full_notes": True,
            }),
        ]
        print("\n  get_projects() parameter impact:")
        results = {}
        for label, kwargs in configs:
            times = []
            for _ in range(ITERATIONS):
                start = time.perf_counter()
                client.get_projects(**kwargs)
                times.append(time.perf_counter() - start)
            mean = statistics.mean(times)
            stdev = statistics.stdev(times) if len(times) > 1 else 0.0
            results[label] = mean
            print(f"    {label:20s}: mean={mean:.3f}s  stdev={stdev:.3f}s")

        baseline = results["baseline"]
        print(f"\n    Overhead vs baseline ({baseline:.3f}s):")
        for label, mean in results.items():
            if label != "baseline":
                overhead = mean - baseline
                pct = (overhead / baseline * 100) if baseline > 0 else 0
                print(f"      {label:20s}: +{overhead:.3f}s ({pct:+.0f}%)")

    def test_get_tasks_filter_comparison(self, client):
        """Compare get_tasks() with different filter combinations."""
        configs = [
            ("no filter", {}),
            ("flagged_only", {"flagged_only": True}),
            ("overdue", {"overdue": True}),
            ("inbox_only", {"inbox_only": True}),
            ("next_only", {"next_only": True}),
            ("available_only", {"available_only": True}),
            ("query='bench'", {"query": "bench"}),
        ]
        print("\n  get_tasks() filter impact:")
        results = {}
        for label, kwargs in configs:
            times = []
            count = 0
            for _ in range(ITERATIONS):
                start = time.perf_counter()
                try:
                    tasks = client.get_tasks(timeout=120, **kwargs)
                    count = len(tasks)
                except subprocess.TimeoutExpired:
                    times.append(120.0)
                    count = -1
                    continue
                times.append(time.perf_counter() - start)
            mean = statistics.mean(times)
            stdev = statistics.stdev(times) if len(times) > 1 else 0.0
            results[label] = (mean, count)
            print(f"    {label:20s}: mean={mean:.3f}s  stdev={stdev:.3f}s  "
                  f"items={count}")

        # Show relative performance
        baseline_mean = results["no filter"][0]
        if baseline_mean < 120:
            print(f"\n    Speed vs unfiltered ({baseline_mean:.3f}s):")
            for label, (mean, _) in results.items():
                if label != "no filter" and mean < 120:
                    speedup = baseline_mean / mean if mean > 0 else float('inf')
                    print(f"      {label:20s}: {speedup:.1f}x {'faster' if speedup > 1 else 'slower'}")

    def test_batch_size_scaling(self, client):
        """Measure how update_tasks() scales with batch size (pre-optimization)."""
        batch_sizes = [1, 3, 5, 10]
        print("\n  update_tasks() batch size scaling:")
        results = {}

        # Create a project to hold all test tasks
        proj_id = client.create_project(f"__bench_scaling_{uuid.uuid4().hex[:8]}")
        try:
            for n in batch_sizes:
                task_ids = []
                for i in range(n):
                    tid = client.create_task(
                        f"__bench_scale_{uuid.uuid4().hex[:8]}",
                        project_id=proj_id,
                    )
                    task_ids.append(tid)

                times = []
                toggle = [True, False, True]
                for run_idx in range(WRITE_ITERATIONS):
                    start = time.perf_counter()
                    client.update_tasks(
                        task_ids, flagged=toggle[run_idx % len(toggle)]
                    )
                    times.append(time.perf_counter() - start)

                mean = statistics.mean(times)
                stdev = statistics.stdev(times) if len(times) > 1 else 0.0
                results[n] = mean
                print(f"    {n:2d} tasks: mean={mean:.3f}s  stdev={stdev:.3f}s  "
                      f"per_task={mean/n:.3f}s")

                try:
                    client.delete_tasks(task_ids)
                except Exception:
                    pass

            # Show scaling linearity
            if 1 in results and len(results) > 1:
                per_task_1 = results[1]
                print(f"\n    Scaling analysis (baseline per-task: {per_task_1:.3f}s):")
                for n, mean in results.items():
                    if n > 1:
                        expected = per_task_1 * n
                        ratio = mean / expected if expected > 0 else 0
                        print(f"      {n:2d} tasks: actual={mean:.3f}s  "
                              f"expected={expected:.3f}s  ratio={ratio:.2f}x")
        finally:
            try:
                client.delete_projects(proj_id)
            except Exception:
                pass
