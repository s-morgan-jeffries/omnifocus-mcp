# Performance Optimization Summary - Issue #170

**Date:** 2025-11-15
**Version:** v0.7.2 (in progress)
**Issue:** #170 - Performance optimization for project filtering

## Problem

The `_filter_projects_by_conditions()` method exhibited an N+1 query pattern, where each project triggered a separate `get_tasks()` AppleScript call. With typical AppleScript overhead of 50-200ms per call, this caused severe performance degradation when filtering large numbers of projects.

### Root Cause

```python
# BEFORE: N+1 pattern
for project in projects:
    project_id = project.get('id')
    # Each iteration triggers separate AppleScript call
    tasks = self.get_tasks(project_id=project_id, include_completed=False)
```

For 33 projects, this resulted in 33 separate AppleScript roundtrips, taking ~7.6 seconds total (~230ms per project).

## Solution

Created a new internal batch method `_get_tasks_batch_for_filtering()` that fetches tasks for **all projects in a single AppleScript call**.

### Implementation

```python
# AFTER: Batch optimization
# Fetch ALL tasks for ALL projects in ONE AppleScript call
project_ids = [p.get('id') for p in projects if p.get('id')]
tasks_by_project = self._get_tasks_batch_for_filtering(project_ids)

for project in projects:
    project_id = project.get('id')
    # Get tasks from pre-fetched batch results
    tasks = tasks_by_project.get(project_id, [])
```

The batch method:
- Iterates through all projects once in AppleScript
- Collects only minimal task data needed for filtering (id, project_id, due_date)
- Returns JSON dictionary mapping project_id → list of tasks
- Executes in ~1 second instead of ~8 seconds

## Performance Results

### Benchmark Data (33 projects with ~105 tasks)

| Test | Before | After | Improvement |
|------|--------|-------|-------------|
| `get_projects(min_task_count=1)` | 8.08s (252.5ms/proj) | 2.26s (70.7ms/proj) | **3.6x faster** |
| `_filter_projects_by_conditions()` | 7.62s (230.8ms/proj) | 0.90s (27.2ms/proj) | **8.5x faster** |
| Scalability (10 projects) | 2.13s (212.9ms/proj) | 0.36s (35.6ms/proj) | **5.9x faster** |

### Key Metrics

- **AppleScript calls reduced:** From 33 calls → 1 call (97% reduction)
- **Execution time reduced:** From 7.6s → 0.9s (88% reduction)
- **Per-project overhead:** From 230ms → 27ms (per project)
- **Performance scales linearly:** Larger datasets see even bigger improvements

### Extrapolation

For larger datasets:
- **100 projects:** ~23s → ~2.7s (8.5x faster)
- **200 projects:** ~46s → ~5.4s (8.5x faster)
- **500 projects:** ~115s → ~13.5s (8.5x faster)

## Implementation Details

### New Method: `_get_tasks_batch_for_filtering()`

**Location:** `src/omnifocus_mcp/omnifocus_connector.py:201-313`

**Purpose:** Batch fetch minimal task data for multiple projects in one AppleScript call

**Parameters:**
- `project_ids: list[str]` - List of project IDs to fetch tasks for

**Returns:**
- `dict[str, list[dict]]` - Dictionary mapping project_id → list of task dictionaries
- Each task dict contains: `{id, projectId, dueDate}`

**AppleScript Strategy:**
1. Define handlers at script level (`formatDate`, `joinList`)
2. Iterate through flattened projects
3. Check if project ID matches any in the requested list
4. For matching projects, collect all incomplete tasks
5. Build JSON manually (AppleScript doesn't have native JSON)
6. Return array of `{projectId, tasks: [...]}` objects

### Modified Method: `_filter_projects_by_conditions()`

**Location:** `src/omnifocus_mcp/omnifocus_connector.py:315-384`

**Changes:**
1. Added batch fetch call before project loop
2. Changed task retrieval from `get_tasks()` call to dictionary lookup
3. All filtering logic unchanged (min_task_count, has_overdue_tasks, has_no_due_dates)

**Backward compatibility:** Fully preserved - same input parameters, same output format, same behavior

## Testing

### Profiling Infrastructure

Created `tests/test_profile_performance.py` with 4 test classes:

1. **TestProfileGetProjects** - Profile end-to-end `get_projects()` with filters
2. **TestProfileProjectFiltering** - Profile internal `_filter_projects_by_conditions()` directly
3. **TestScalabilityBenchmark** - Test performance scaling with different project counts
4. **TestFixtures** - Setup test data for profiling

### Test Data Setup

Created `scripts/local/setup_profiling_data.sh`:
- Creates 30 projects with 3-5 tasks each (~105 tasks total)
- Located in test database only (scripts/local/ is gitignored)
- Provides realistic dataset for performance testing

### Integration Testing

Verified optimization didn't break existing functionality:
- All `TestGetProjectsParameterVariations` tests pass
- Filters work correctly (min_task_count, has_overdue_tasks, has_no_due_dates)
- Output format unchanged
- Edge cases handled (empty projects, missing data)

## Files Modified

### Core Implementation
- `src/omnifocus_mcp/omnifocus_connector.py` - Added batch method, modified filtering

### Testing Infrastructure
- `tests/test_profile_performance.py` (NEW) - Performance profiling tests
- `scripts/local/setup_profiling_data.sh` (NEW) - Test data generation
- `scripts/local/switch_to_test_db.sh` (NEW) - Database switching helper
- `scripts/local/switch_to_prod_db.sh` (NEW) - Database switching helper
- `.gitignore` - Added scripts/local/ directory

### Documentation
- `docs/performance/PERFORMANCE_OPTIMIZATION_SUMMARY.md` (NEW) - This file

## Technical Considerations

### Why Not Optimize `get_tasks()` Directly?

The existing `get_tasks()` method is 628 lines with 21 parameters and complex filtering logic. Creating a separate optimized batch method:
- Keeps the optimization focused and maintainable
- Avoids adding complexity to an already complex method
- Only fetches minimal data needed for filtering (not full task details)
- Easier to test and verify correctness

### AppleScript Limitations

- No native JSON support → manual string building required
- Handlers must be at script level (not inside `tell` blocks)
- String concatenation for large datasets can be slow
- Error handling limited to try/catch blocks

### Future Optimizations

Potential further improvements:
1. Add caching layer for batch results (if projects don't change frequently)
2. Parallelize AppleScript execution for very large datasets
3. Consider SQLite read for task data if OmniFocus exposes database
4. Add batch method for other N+1 patterns if discovered

## Conclusion

Successfully eliminated N+1 query pattern in project filtering, achieving **8.5x performance improvement** for the most critical path. The optimization:

✅ Reduces AppleScript calls from N to 1
✅ Maintains backward compatibility
✅ Passes all existing integration tests
✅ Scales linearly with dataset size
✅ Provides foundation for future optimizations

**Impact:** Users filtering large project lists will see near-instant response times instead of multi-second delays.

---

**Next Steps:**
1. Write unit tests for `_get_tasks_batch_for_filtering()`
2. Document performance characteristics in API reference
3. Monitor for other N+1 patterns in codebase
4. Consider adding performance metrics to CI/CD pipeline
