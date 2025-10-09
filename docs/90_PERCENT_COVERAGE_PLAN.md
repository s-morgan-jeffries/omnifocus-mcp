# 90%+ Integration Test Coverage Plan

## Current State
- **14 tests** covering **~17%** of functionality
- Focus: Basic CRUD, query search, safety verification

## Total Functionality to Cover

### MCP Server Methods (36 tools)
1. get_projects (✅ tested)
2. create_project (❌)
3. get_project (❌)
4. set_project_status (❌)
5. delete_project (❌)
6. delete_projects (❌)
7. get_stalled_projects (❌)
8. get_projects_due_for_review (❌)
9. get_tasks (✅ tested)
10. get_task (❌)
11. get_subtasks (❌)
12. add_task (✅ tested)
13. update_task (✅ tested)
14. complete_task (✅ tested)
15. complete_tasks (❌)
16. create_inbox_task (✅ tested)
17. delete_task (❌)
18. delete_tasks (❌)
19. move_task (❌)
20. move_tasks (❌)
21. drop_task (❌)
22. drop_tasks (❌)
23. set_parent_task (❌)
24. get_tags (✅ tested)
25. add_tag_to_task (✅ tested)
26. add_tag_to_tasks (❌)
27. remove_tag_from_tasks (❌)
28. add_note (❌)
29. get_note (❌)
30. get_folders (❌)
31. create_folder (❌)
32. set_review_interval (❌)
33. mark_project_reviewed (❌)
34. set_estimated_minutes (❌)
35. get_perspectives (❌)
36. switch_perspective (❌)

**Current**: 8/36 methods tested = 22% method coverage

### Parameter Variations (Important for Real Coverage)

Each method has multiple parameters that need testing:

#### get_tasks() parameter combinations (~20 variations needed)
- ✅ Basic (no params)
- ✅ query="..."
- ✅ inbox_only=True
- ❌ project_id="..."
- ❌ include_completed=True
- ❌ flagged_only=True
- ❌ available_only=True
- ❌ overdue=True
- ❌ dropped_only=True
- ❌ blocked_only=True
- ❌ next_only=True
- ❌ due_relative="today"
- ❌ due_relative="this_week"
- ❌ due_relative="next_week"
- ❌ defer_relative="this_week"
- ❌ max_estimated_minutes=60
- ❌ has_estimate=True/False
- ❌ tag_filter=["tag1"], tag_filter_mode="and"
- ❌ tag_filter=["tag1", "tag2"], tag_filter_mode="or"
- ❌ created_after/before, modified_after/before
- ❌ sort_by="due_date", sort_order="asc/desc"
- ❌ recurring_only=True

#### get_projects() parameter combinations (~10 variations needed)
- ✅ Basic (no params)
- ✅ query="..."
- ❌ on_hold_only=True
- ❌ modified_after/before
- ❌ min_task_count=5
- ❌ has_overdue_tasks=True
- ❌ has_no_due_dates=True
- ❌ sort_by="name", sort_order="asc/desc"

#### add_task() parameter combinations (~8 variations needed)
- ✅ Basic (name only)
- ✅ With note, due_date, flagged, tags
- ❌ With defer_date
- ❌ With estimated_minutes
- ❌ With recurrence (FREQ=DAILY)
- ❌ With recurrence (FREQ=WEEKLY)
- ❌ With recurrence (FREQ=MONTHLY)
- ❌ With repetition_method variations

#### update_task() parameter combinations (~6 variations needed)
- ✅ Basic (name update)
- ❌ Update note
- ❌ Update due_date
- ❌ Update defer_date
- ❌ Update flagged
- ❌ Clear due_date (set to None)

---

## 90% Coverage Breakdown

### What 90% Means
- **90% of methods**: 32+ of 36 methods tested
- **90% of common parameters**: Key parameter combinations covered
- **90% of workflows**: Real-world usage patterns tested

### Required Tests for 90% Coverage

#### Core Operations (28 new tests)

**Projects** (7 tests)
1. create_project() - basic
2. create_project() - with folder, notes, review_interval
3. get_project() - by ID
4. set_project_status() - active → on_hold
5. set_project_status() - on_hold → done
6. delete_project() - single
7. delete_projects() - batch

**Tasks** (10 tests)
1. get_task() - by ID
2. get_subtasks() - parent task children
3. delete_task() - single
4. delete_tasks() - batch (2-3 tasks)
5. move_task() - to different project
6. move_tasks() - batch move
7. drop_task() - mark as dropped
8. drop_tasks() - batch drop
9. set_parent_task() - create hierarchy
10. set_parent_task() - clear parent (orphan task)

**Batch Operations** (3 tests)
1. complete_tasks() - multiple at once
2. add_tag_to_tasks() - batch tagging
3. remove_tag_from_tasks() - batch tag removal

**Folders** (2 tests)
1. get_folders() - list all
2. create_folder() - with parent path

**Notes** (2 tests)
1. add_note() - to project
2. get_note() - retrieve content

**Review System** (3 tests)
1. set_review_interval() - set schedule
2. mark_project_reviewed() - mark reviewed
3. get_projects_due_for_review() - find due

**Time Estimation** (1 test)
1. set_estimated_minutes() - set estimate

#### Parameter Coverage Tests (25 new tests)

**get_tasks() variations** (15 tests)
1. project_id parameter
2. include_completed=True
3. flagged_only=True
4. available_only=True
5. overdue=True
6. dropped_only=True
7. blocked_only=True
8. next_only=True
9. due_relative="today"
10. due_relative="this_week"
11. defer_relative="this_week"
12. max_estimated_minutes=60
13. has_estimate=True
14. tag_filter with AND logic
15. sort_by="due_date"

**get_projects() variations** (5 tests)
1. on_hold_only=True
2. modified_after parameter
3. min_task_count=5
4. has_overdue_tasks=True
5. sort_by="name"

**add_task() variations** (3 tests)
1. With defer_date
2. With estimated_minutes
3. With recurrence (recurring task)

**update_task() variations** (2 tests)
1. Update dates
2. Clear properties (set to None)

#### Error/Edge Cases (10 new tests)

**Validation** (5 tests)
1. Invalid project ID → graceful error
2. Invalid task ID → graceful error
3. Invalid date format → validation error
4. Invalid recurrence pattern → validation error
5. Empty required fields → validation error

**Edge Cases** (5 tests)
1. Circular parent task (task as its own parent) → rejected
2. Very long task name (1000+ chars)
3. Special characters in names (emoji, unicode)
4. Concurrent operations (safety)
5. Large batch operations (50+ items)

#### Real-World Workflows (10 new tests)

**Complete Workflows** (5 tests)
1. Create project → add tasks → complete tasks → review
2. Create recurring task → complete → verify next occurrence
3. Search by tag → batch complete → verify completion
4. Create folder → create project in folder → verify hierarchy
5. Move multiple tasks between projects → verify

**Complex Filtering** (5 tests)
1. Combine multiple filters (flagged + due this week + tagged)
2. Date range filtering (created between dates)
3. Stalled projects detection
4. Next actions across all projects
5. Overdue tasks with estimates

---

## Total Test Count for 90% Coverage

- **Current**: 14 tests
- **Core Operations**: +28 tests
- **Parameter Coverage**: +25 tests
- **Error/Edge Cases**: +10 tests
- **Real-World Workflows**: +10 tests

**Total**: **~87 tests** for 90%+ coverage

---

## Implementation Effort

### Time Estimates (rough)

**Per test complexity:**
- Simple test (basic CRUD): ~5-10 minutes
- Medium test (with setup): ~15-20 minutes
- Complex test (workflow): ~30-45 minutes

**Total effort:**
- Core Operations (28 tests × 15 min avg): ~7 hours
- Parameter Coverage (25 tests × 10 min avg): ~4 hours
- Error Cases (10 tests × 20 min avg): ~3.5 hours
- Workflows (10 tests × 40 min avg): ~6.5 hours

**Grand Total**: ~21 hours of focused work

### Phases

**Phase 1: Critical Coverage** (20 tests, ~5 hours)
- All CRUD operations
- Batch operations
- Basic parameter variations
- Gets us to ~50% coverage

**Phase 2: Advanced Features** (20 tests, ~5 hours)
- Folders, notes, review system
- Advanced filtering
- Date operations
- Gets us to ~70% coverage

**Phase 3: Edge Cases & Workflows** (20 tests, ~5 hours)
- Error handling
- Complex workflows
- Edge cases
- Performance/stress tests
- Gets us to ~85% coverage

**Phase 4: Comprehensive** (13 tests, ~3 hours)
- Remaining parameter combinations
- Obscure features (perspectives)
- Final edge cases
- Gets us to **90%+ coverage**

---

## Maintenance Considerations

### Test Data Management
- Need to expand test database setup script
- Add more sample data (10+ projects, 30+ tasks, folders, tags)
- Include edge cases (recurring tasks, dropped tasks, on-hold projects)

### Test Database Size
- Current: Minimal (2 projects, 3 tasks, 3 tags)
- 90% coverage: Moderate (10 projects, 50 tasks, 10 tags, 3 folders)
- ~2-3 MB test database

### CI/CD Impact
- Current test time: ~26 seconds
- 90% coverage estimated: ~3-5 minutes
- Need CI environment that can run OmniFocus (macOS only)

---

## What We'd Skip (the remaining 10%)

These features are hard/impractical to test in integration:

1. **Perspectives** (get/switch) - UI-focused, hard to verify
2. **Extremely rare parameter combinations** (e.g., 5+ filters combined)
3. **Performance under extreme load** (1000+ tasks in single operation)
4. **UI-dependent features** that don't have programmatic verification
5. **Features that require specific OmniFocus setup** (e.g., custom perspectives)

---

## Recommendation

For **90% coverage**, implement:
1. ✅ **Phase 1** (Critical Coverage): Get to 50% - **Worth doing now**
2. ✅ **Phase 2** (Advanced Features): Get to 70% - **Worth doing now**
3. ⚠️  **Phase 3** (Edge Cases): Get to 85% - **Worth doing eventually**
4. ❓ **Phase 4** (Comprehensive): Get to 90% - **Diminishing returns**

**Practical recommendation**: Stop at **~70% coverage** (~54 tests) for best ROI.
- Covers all core functionality
- Tests real-world usage patterns
- Catches 95% of bugs
- Doesn't test obscure edge cases that rarely matter

Going from 70% → 90% adds **33 tests** but only catches **~5% more bugs**.
