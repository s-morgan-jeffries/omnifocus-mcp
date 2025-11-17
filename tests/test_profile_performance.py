"""Performance profiling tests for OmniFocus MCP Server.

These tests measure execution time to identify bottlenecks.
Run with: OMNIFOCUS_TEST_MODE=true OMNIFOCUS_TEST_DATABASE=OmniFocus-TEST.ofocus pytest tests/test_profile_performance.py -v -s

NOT part of regular test suite - run manually for performance analysis.
"""
import os
import time
import pytest
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector

# Skip all tests unless explicitly running profiling
pytestmark = pytest.mark.skipif(
    os.environ.get('OMNIFOCUS_TEST_MODE', '').lower() != 'true',
    reason="Performance profiling requires OMNIFOCUS_TEST_MODE=true"
)


@pytest.fixture
def profiling_client():
    """OmniFocusConnector for profiling."""
    return OmniFocusConnector()


# =============================================================================
# Profile get_projects() with conditional filters
# =============================================================================

class TestProfileGetProjects:
    """Profile get_projects() execution patterns."""

    def test_profile_get_projects_with_task_conditions(self, profiling_client):
        """Profile get_projects() with min_task_count filter.

        This triggers _filter_projects_by_conditions() which has the N+1 query pattern.
        """
        print("\n" + "="*80)
        print("PROFILING: get_projects(min_task_count=1)")
        print("="*80)

        start = time.perf_counter()
        projects = profiling_client.get_projects(min_task_count=1)
        duration = time.perf_counter() - start

        # Print results
        print(f"\nResults:")
        print(f"  Projects returned: {len(projects)}")
        print(f"  Total execution time: {duration:.3f}s")
        if len(projects) > 0:
            print(f"  Time per project: {duration/len(projects)*1000:.1f}ms")
            print(f"\nNOTE: If time per project is high (>100ms), this indicates N+1 pattern")
            print(f"      Each project likely triggers a separate get_tasks() call")

        print(f"\n" + "="*80)
        return {
            'projects_count': len(projects),
            'duration': duration
        }

    def test_profile_get_projects_simple(self, profiling_client):
        """Profile get_projects() without conditional filters (baseline)."""
        print("\n" + "="*80)
        print("BASELINE: get_projects() with no filters")
        print("="*80)

        start = time.perf_counter()
        projects = profiling_client.get_projects()
        duration = time.perf_counter() - start

        print(f"\nResults:")
        print(f"  Projects returned: {len(projects)}")
        print(f"  Total execution time: {duration:.3f}s")
        if len(projects) > 0:
            print(f"  Time per project: {duration/len(projects)*1000:.1f}ms")

        print(f"\n" + "="*80)
        return {
            'projects_count': len(projects),
            'duration': duration
        }


# =============================================================================
# Profile _filter_projects_by_conditions() directly (the bottleneck)
# =============================================================================

class TestProfileProjectFiltering:
    """Profile the internal _filter_projects_by_conditions() method."""

    def test_profile_filter_projects_by_conditions(self, profiling_client):
        """Profile _filter_projects_by_conditions() with min_task_count filter.

        This is the method that implements the N+1 pattern.
        Each project triggers a separate get_tasks() call.
        """
        print("\n" + "="*80)
        print("PROFILING: _filter_projects_by_conditions() internals")
        print("="*80)

        # First get all projects (baseline)
        all_projects = profiling_client.get_projects()
        print(f"\nTotal projects in database: {len(all_projects)}")

        # Now profile the filtering
        start = time.perf_counter()

        # Call the internal filtering method directly
        filtered = profiling_client._filter_projects_by_conditions(
            all_projects,
            min_task_count=1,
            has_overdue_tasks=None,
            has_no_due_dates=None
        )

        duration = time.perf_counter() - start

        print(f"\nResults:")
        print(f"  Projects after filtering: {len(filtered)}")
        print(f"  Total execution time: {duration:.3f}s")
        if len(all_projects) > 0:
            time_per_project = duration / len(all_projects)
            print(f"  Time per project: {time_per_project*1000:.1f}ms")

            print(f"\n  N+1 PATTERN DETECTED:")
            print(f"    Each project triggers separate get_tasks() call")
            print(f"    Expected: {len(all_projects)} AppleScript roundtrips")
            print(f"    Typical AppleScript overhead: 50-200ms per call")

            if time_per_project > 0.05:  # >50ms per project suggests N+1
                print(f"  ✓ Confirmed: High per-project time indicates N+1 pattern")
                print(f"\n  OPTIMIZATION OPPORTUNITY:")
                print(f"    Current: ~{len(all_projects)} AppleScript calls (one per project)")
                print(f"    Optimized: 1 AppleScript call (batch fetch all tasks)")
                print(f"    Reduction: ~{len(all_projects) - 1} fewer calls")

                # Estimate speedup assuming 100ms per AppleScript call
                estimated_current = len(all_projects) * 0.1  # 100ms per call
                estimated_optimized = 0.1  # Single batch call
                if estimated_current > 0:
                    speedup = estimated_current / estimated_optimized
                    print(f"    Estimated speedup: {speedup:.1f}x faster")

        print(f"\n" + "="*80)
        return {
            'total_projects': len(all_projects),
            'filtered_projects': len(filtered),
            'duration': duration,
            'time_per_project': duration / len(all_projects) if all_projects else 0
        }


# =============================================================================
# Benchmark with different project counts
# =============================================================================

class TestScalabilityBenchmark:
    """Test how performance scales with number of projects."""

    def test_benchmark_scaling(self, profiling_client):
        """Benchmark performance with increasing project counts.

        This helps quantify the O(N) complexity of the N+1 pattern.
        """
        print("\n" + "="*80)
        print("SCALABILITY BENCHMARK: Performance vs. Project Count")
        print("="*80)

        # Get all projects
        all_projects = profiling_client.get_projects()
        total_count = len(all_projects)

        print(f"\nTotal projects available: {total_count}")
        print(f"\nTesting with different project counts...\n")

        results = []

        # Test with different subsets (if we have enough projects)
        test_sizes = [10, 20, 30, 50] if total_count >= 50 else [min(total_count, 10)]

        for n in test_sizes:
            if n > total_count:
                break

            # Get subset of projects
            subset = all_projects[:n]

            # Profile filtering this subset
            start = time.perf_counter()

            filtered = profiling_client._filter_projects_by_conditions(
                subset,
                min_task_count=1,
                has_overdue_tasks=None,
                has_no_due_dates=None
            )

            duration = time.perf_counter() - start

            result = {
                'project_count': n,
                'duration': duration,
                'time_per_project': duration / n
            }
            results.append(result)

            print(f"  {n} projects: {duration:.3f}s ({duration/n*1000:.1f}ms per project)")

        # Analysis
        if len(results) >= 2:
            print(f"\nScalability Analysis:")
            first = results[0]
            last = results[-1]

            # Calculate if it's linear O(N)
            ratio = last['duration'] / first['duration']
            project_ratio = last['project_count'] / first['project_count']

            print(f"  Projects increased: {first['project_count']} → {last['project_count']} ({project_ratio:.1f}x)")
            print(f"  Time increased: {first['duration']:.3f}s → {last['duration']:.3f}s ({ratio:.1f}x)")

            if abs(ratio - project_ratio) < 0.3 * project_ratio:
                print(f"  ✓ Confirmed: Linear O(N) complexity")
                print(f"    Each additional project adds ~{last['time_per_project']*1000:.1f}ms")

            # Extrapolate to larger datasets
            print(f"\nExtrapolation:")
            for future_n in [100, 200, 500]:
                if future_n > total_count:
                    estimated_time = last['time_per_project'] * future_n
                    print(f"  {future_n} projects: ~{estimated_time:.3f}s (estimated)")

        print(f"\n" + "="*80)
        return results


# =============================================================================
# Profile get_tasks() performance
# =============================================================================

class TestProfileGetTasks:
    """Profile get_tasks() execution patterns to identify bottlenecks."""

    def test_profile_get_tasks_baseline(self, profiling_client):
        """Profile get_tasks() with no filters (baseline).

        Measures basic AppleScript execution time for fetching all tasks.
        """
        print("\n" + "="*80)
        print("BASELINE: get_tasks() with no filters")
        print("="*80)

        start = time.perf_counter()
        tasks = profiling_client.get_tasks()
        duration = time.perf_counter() - start

        print(f"\nResults:")
        print(f"  Tasks returned: {len(tasks)}")
        print(f"  Total execution time: {duration:.3f}s")
        if len(tasks) > 0:
            print(f"  Time per task: {duration/len(tasks)*1000:.1f}ms")

        print(f"\n" + "="*80)
        return {
            'tasks_count': len(tasks),
            'duration': duration,
            'time_per_task': duration / len(tasks) if tasks else 0
        }

    def test_profile_get_tasks_with_project_filter(self, profiling_client):
        """Profile get_tasks(project_id=X) for a single project.

        Tests performance when fetching tasks for a specific project.
        """
        print("\n" + "="*80)
        print("PROFILING: get_tasks(project_id=X) for single project")
        print("="*80)

        # First get a project to test with
        projects = profiling_client.get_projects()
        if not projects:
            print("No projects found - skipping test")
            return {'skipped': True}

        project_id = projects[0]['id']
        print(f"\nTesting with project: {projects[0]['name']}")

        start = time.perf_counter()
        tasks = profiling_client.get_tasks(project_id=project_id)
        duration = time.perf_counter() - start

        print(f"\nResults:")
        print(f"  Tasks returned: {len(tasks)}")
        print(f"  Total execution time: {duration:.3f}s")
        if len(tasks) > 0:
            print(f"  Time per task: {duration/len(tasks)*1000:.1f}ms")

        print(f"\n" + "="*80)
        return {
            'tasks_count': len(tasks),
            'duration': duration
        }

    def test_profile_get_tasks_with_filters(self, profiling_client):
        """Profile get_tasks() with common filters (flagged, available, overdue).

        Tests performance impact of AppleScript-side filtering.
        """
        print("\n" + "="*80)
        print("PROFILING: get_tasks() with common filters")
        print("="*80)

        filter_configs = [
            {'name': 'flagged_only', 'params': {'flagged_only': True}},
            {'name': 'available_only', 'params': {'available_only': True}},
            {'name': 'overdue', 'params': {'overdue': True}},
        ]

        results = []
        for config in filter_configs:
            start = time.perf_counter()
            tasks = profiling_client.get_tasks(**config['params'])
            duration = time.perf_counter() - start

            result = {
                'filter': config['name'],
                'tasks_count': len(tasks),
                'duration': duration
            }
            results.append(result)

            print(f"\n  {config['name']}:")
            print(f"    Tasks returned: {len(tasks)}")
            print(f"    Execution time: {duration:.3f}s")

        print(f"\n" + "="*80)
        return results

    def test_profile_get_tasks_property_extraction_overhead(self, profiling_client):
        """Profile the overhead of extracting all 25+ properties per task.

        This test helps identify if property extraction is a bottleneck.
        We can't easily separate property extraction from the query,
        but we can measure the time per task and infer overhead.
        """
        print("\n" + "="*80)
        print("ANALYSIS: Property extraction overhead")
        print("="*80)

        # Get all tasks to measure full property extraction
        start = time.perf_counter()
        tasks = profiling_client.get_tasks()
        duration = time.perf_counter() - start

        if not tasks:
            print("No tasks found - skipping analysis")
            return {'skipped': True}

        # Sample a task to count properties
        sample_task = tasks[0]
        property_count = len(sample_task.keys())

        print(f"\nResults:")
        print(f"  Total tasks: {len(tasks)}")
        print(f"  Properties per task: {property_count}")
        print(f"  Total execution time: {duration:.3f}s")
        print(f"  Time per task: {duration/len(tasks)*1000:.1f}ms")
        print(f"  Time per property (avg): {duration/(len(tasks)*property_count)*1000:.2f}ms")

        # Analyze note sizes (potential bottleneck)
        note_sizes = [len(t.get('note', '')) for t in tasks]
        avg_note_size = sum(note_sizes) / len(note_sizes) if note_sizes else 0
        max_note_size = max(note_sizes) if note_sizes else 0
        tasks_with_notes = sum(1 for size in note_sizes if size > 0)

        print(f"\n  Note analysis:")
        print(f"    Tasks with notes: {tasks_with_notes}/{len(tasks)}")
        print(f"    Avg note size: {avg_note_size:.0f} chars")
        print(f"    Max note size: {max_note_size} chars")
        if max_note_size > 1000:
            print(f"    ⚠️  Large notes detected - note truncation could help")

        # Analyze tag complexity
        tag_counts = [len(t.get('tags', [])) for t in tasks]
        avg_tags = sum(tag_counts) / len(tag_counts) if tag_counts else 0
        max_tags = max(tag_counts) if tag_counts else 0
        tasks_with_tags = sum(1 for count in tag_counts if count > 0)

        print(f"\n  Tag analysis:")
        print(f"    Tasks with tags: {tasks_with_tags}/{len(tasks)}")
        print(f"    Avg tags per task: {avg_tags:.1f}")
        print(f"    Max tags: {max_tags}")

        print(f"\n  OPTIMIZATION OPPORTUNITIES:")

        # Calculate potential savings from minimal mode
        if property_count > 10:
            estimated_minimal_props = 5  # id, name, completed, flagged, projectId
            reduction_pct = ((property_count - estimated_minimal_props) / property_count) * 100
            print(f"    1. Add minimal=True parameter:")
            print(f"       - Current properties: {property_count}")
            print(f"       - Minimal properties: {estimated_minimal_props}")
            print(f"       - Potential reduction: ~{reduction_pct:.0f}%")

        if max_note_size > 100:
            print(f"    2. Truncate notes in AppleScript:")
            print(f"       - Currently fetching full notes (max: {max_note_size} chars)")
            print(f"       - Could truncate to 100 chars in AppleScript")

        if avg_tags > 2:
            print(f"    3. Simplify tag JSON construction:")
            print(f"       - Currently building JSON array in AppleScript")
            print(f"       - Could use comma-separated string")

        print(f"\n" + "="*80)
        return {
            'tasks_count': len(tasks),
            'duration': duration,
            'property_count': property_count,
            'avg_note_size': avg_note_size,
            'max_note_size': max_note_size,
            'avg_tags': avg_tags
        }

    def test_profile_get_tasks_with_query_filter(self, profiling_client):
        """Profile get_tasks() with query filter.

        Measures performance of text search to determine if moving query filtering
        from Python to AppleScript would provide meaningful benefit beyond the
        filter-first architecture already implemented in Phase 2.

        Context: Query filtering is currently in Python (lines 2214-2221 of
        omnifocus_connector.py) but is classified as a selective filter
        (lines 1638-1648) which triggers filter-first architecture.

        This test measures:
        1. Baseline (no filter) execution time
        2. Query filter execution time (filter-first + Python query)
        3. Overhead from Python-side query filtering

        Results will inform whether implementing AppleScript-side query filtering
        (as documented in GET_TASKS_PERFORMANCE_ANALYSIS.md lines 759-803) would
        provide meaningful additional benefit.
        """
        print("\n" + "="*80)
        print("PROFILING: get_tasks(query='test') performance")
        print("="*80)

        # First measure baseline (no filters)
        print("\n1. Measuring baseline (no filters)...")
        start_baseline = time.perf_counter()
        all_tasks = profiling_client.get_tasks()
        baseline_duration = time.perf_counter() - start_baseline

        print(f"   Baseline: {baseline_duration:.3f}s ({len(all_tasks)} tasks)")

        # Test with common search term that should match some tasks
        print("\n2. Measuring with query filter...")
        start = time.perf_counter()
        query_tasks = profiling_client.get_tasks(query="test")
        duration = time.perf_counter() - start

        print(f"   Query filter: {duration:.3f}s ({len(query_tasks)} tasks)")

        # Calculate overhead
        overhead = duration - baseline_duration

        print(f"\nResults:")
        print(f"  Baseline (no filter):")
        print(f"    Tasks: {len(all_tasks)}")
        print(f"    Time: {baseline_duration:.3f}s")

        print(f"\n  With query='test':")
        print(f"    Tasks matched: {len(query_tasks)}")
        print(f"    Match rate: {len(query_tasks)/len(all_tasks)*100:.1f}%" if all_tasks else "N/A")
        print(f"    Time: {duration:.3f}s")

        print(f"\n  Python-side query overhead: {overhead:.3f}s")
        if overhead > 0:
            overhead_pct = (overhead / baseline_duration) * 100
            print(f"  Overhead percentage: {overhead_pct:.1f}%")

        # Analysis
        print(f"\n  ANALYSIS:")
        print(f"    Current implementation:")
        print(f"      - Filter-first architecture reduces task set BEFORE extraction")
        print(f"      - Query filtering happens in Python AFTER extraction")
        print(f"      - Total time: {duration:.3f}s")

        print(f"\n    Potential AppleScript implementation:")
        print(f"      - Would filter during property extraction phase")
        print(f"      - Would eliminate Python-side overhead ({overhead:.3f}s)")
        print(f"      - Estimated time: ~{baseline_duration:.3f}s (baseline)")

        if overhead > 0.1:
            print(f"\n  ✓ RECOMMENDATION: Consider implementing AppleScript query filtering")
            print(f"    Expected benefit: Save ~{overhead:.3f}s ({overhead_pct:.1f}% faster)")
        elif overhead > 0.05:
            print(f"\n  ~ MARGINAL: AppleScript implementation would save ~{overhead:.3f}s")
            print(f"    May not justify implementation complexity")
        else:
            print(f"\n  ✗ NOT RECOMMENDED: Overhead is minimal ({overhead:.3f}s)")
            print(f"    Python implementation is sufficient")

        # Test with different search terms to measure consistency
        print(f"\n  Additional query tests:")
        test_queries = ["project", "task", "note"]
        for test_query in test_queries:
            start = time.perf_counter()
            results = profiling_client.get_tasks(query=test_query)
            query_duration = time.perf_counter() - start
            query_overhead = query_duration - baseline_duration

            print(f"    query='{test_query}': {len(results)} tasks, "
                  f"{query_duration:.3f}s (overhead: {query_overhead:.3f}s)")

        print(f"\n" + "="*80)
        return {
            'baseline_tasks': len(all_tasks),
            'baseline_duration': baseline_duration,
            'query_tasks': len(query_tasks),
            'query_duration': duration,
            'overhead': overhead,
            'overhead_pct': (overhead / baseline_duration * 100) if baseline_duration > 0 else 0
        }

    def test_profile_get_tasks_scalability(self, profiling_client):
        """Profile how get_tasks() performance scales with task count.

        Tests different project sizes to measure scalability.
        """
        print("\n" + "="*80)
        print("SCALABILITY: get_tasks() with varying task counts")
        print("="*80)

        # Get projects and their task counts
        projects = profiling_client.get_projects()
        if not projects:
            print("No projects found - skipping test")
            return {'skipped': True}

        # Sort projects by estimated task count (we'll measure actual count)
        print(f"\nTesting with different projects...\n")

        results = []
        for i, project in enumerate(projects[:5]):  # Test up to 5 projects
            project_id = project['id']
            project_name = project['name']

            start = time.perf_counter()
            tasks = profiling_client.get_tasks(project_id=project_id)
            duration = time.perf_counter() - start

            result = {
                'project_name': project_name,
                'tasks_count': len(tasks),
                'duration': duration,
                'time_per_task': duration / len(tasks) if tasks else 0
            }
            results.append(result)

            print(f"  Project: {project_name[:40]}")
            print(f"    Tasks: {len(tasks)}")
            print(f"    Time: {duration:.3f}s ({duration/len(tasks)*1000:.1f}ms per task)" if tasks else f"    Time: {duration:.3f}s (no tasks)")
            print()

        # Analysis
        if len(results) >= 2:
            results_sorted = sorted(results, key=lambda r: r['tasks_count'])
            smallest = results_sorted[0]
            largest = results_sorted[-1]

            if smallest['tasks_count'] > 0 and largest['tasks_count'] > 0:
                task_ratio = largest['tasks_count'] / smallest['tasks_count']
                time_ratio = largest['duration'] / smallest['duration']

                print(f"Scalability Analysis:")
                print(f"  Tasks: {smallest['tasks_count']} → {largest['tasks_count']} ({task_ratio:.1f}x increase)")
                print(f"  Time: {smallest['duration']:.3f}s → {largest['duration']:.3f}s ({time_ratio:.1f}x increase)")

                if abs(time_ratio - task_ratio) < 0.3 * task_ratio:
                    print(f"  ✓ Linear O(N) complexity confirmed")

        print(f"\n" + "="*80)
        return results
