#!/usr/bin/env python3
"""
Performance timing test to measure AppleScript execution time.

This test measures how long it takes to retrieve tasks from OmniFocus
to determine if timeout is the root cause of the query issue.

Usage:
    ./venv/bin/python3 tests/test_performance_timing.py
"""

import time
import sys
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


def time_operation(description: str, operation):
    """Time an operation and print results."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"{'='*60}")

    start = time.time()
    try:
        result = operation()
        elapsed = time.time() - start

        print(f"✓ SUCCESS in {elapsed:.2f} seconds")

        # Show result summary
        if isinstance(result, list):
            print(f"  Returned {len(result)} items")
            if result:
                # Show first item keys
                if isinstance(result[0], dict):
                    print(f"  Sample keys: {list(result[0].keys())[:5]}")

        return elapsed, result
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ FAILED after {elapsed:.2f} seconds")
        print(f"  Error: {e}")
        return elapsed, None


def main():
    print("OmniFocus AppleScript Performance Test")
    print("=" * 60)

    client = OmniFocusConnector()

    # Test 1: Get all incomplete tasks (the problematic query)
    elapsed1, tasks = time_operation(
        "get_tasks(include_completed=False) - Full dataset",
        lambda: client.get_tasks(include_completed=False, timeout=120)
    )

    if tasks:
        print(f"\nTotal incomplete tasks: {len(tasks)}")

        # Test 2: Filter for mortgage in Python (after retrieval)
        elapsed2, _ = time_operation(
            "Python filtering for 'mortgage' in task names",
            lambda: [t for t in tasks if 'mortgage' in t.get('name', '').lower()]
        )

        # Test 3: Get tasks with query parameter (AppleScript filtering)
        elapsed3, mortgage_tasks = time_operation(
            "get_tasks(query='mortgage') - AppleScript + Python filtering",
            lambda: client.get_tasks(query='mortgage', include_completed=False, timeout=120)
        )

        if mortgage_tasks:
            print(f"\nFound mortgage tasks: {len(mortgage_tasks)}")
            for task in mortgage_tasks[:3]:  # Show first 3
                print(f"  - {task.get('name')} (ID: {task.get('id')})")

    # Test 4: Get all projects
    elapsed4, projects = time_operation(
        "get_projects() - All projects",
        lambda: client.get_projects(timeout=90)
    )

    if projects:
        print(f"\nTotal projects: {len(projects)}")

    # Summary
    print("\n" + "="*60)
    print("PERFORMANCE SUMMARY")
    print("="*60)
    print(f"get_tasks (all incomplete): {elapsed1:.2f}s")
    if tasks:
        print(f"Python filtering:           {elapsed2:.2f}s")
        print(f"get_tasks (with query):     {elapsed3:.2f}s")
    print(f"get_projects:               {elapsed4:.2f}s")

    # Analysis
    print("\n" + "="*60)
    print("ANALYSIS")
    print("="*60)

    if elapsed1 > 30:
        print("⚠ WARNING: get_tasks() is taking >30 seconds")
        print("  This confirms AppleScript performance is the bottleneck")
        print("  Recommendations:")
        print("  1. ✓ Timeout parameter added (prevents infinite hangs)")
        print("  2. ☐ Optimize AppleScript JSON building")
        print("  3. ☐ Consider limiting properties extracted")
        print("  4. ☐ Add caching for repeated queries")
    elif elapsed1 > 10:
        print("⚠ CAUTION: get_tasks() is taking >10 seconds")
        print("  Performance optimization recommended")
    else:
        print("✓ Performance is acceptable (<10 seconds)")

    if tasks and elapsed3 > 0:
        if elapsed3 > elapsed1 * 1.1:
            print(f"\n⚠ Query filtering adds overhead: +{elapsed3 - elapsed1:.2f}s")
        else:
            print(f"\n✓ Query filtering is efficient: ~{elapsed3:.2f}s total")


if __name__ == "__main__":
    main()
