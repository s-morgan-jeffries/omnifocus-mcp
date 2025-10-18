# API Redesign Implementation Plan: 40→16 Functions

## Current Status (Updated: 2025-10-18)

### ✅ COMPLETED - STEP 1 (update_task)

**Client Layer:**
1. **update_task()** - Enhanced with 15+ parameters
   - Status: IMPLEMENTED ✅
   - Signature: Added project_id, parent_task_id, tags, add_tags, remove_tags, estimated_minutes, completed, status
   - Return: Changed from bool to dict
   - Tests: 23 new client tests ✅
   - Legacy tests: 16 updated ✅
   - Complexity: F (CC 49) - Documented in CODE_QUALITY.md ✅
   - Commit: 9523e1a

**Server Layer:**
2. **update_task() MCP tool** - Enhanced server layer
   - Status: IMPLEMENTED ✅ (Following TDD!)
   - Tests written FIRST: 13 new server tests ✅
   - Confirmed FAIL → Implemented → Confirmed PASS ✅
   - Legacy tests: 4 updated ✅
   - Integration tests: 2 updated ✅
   - Commit: cf764d3

**Branch:** `feature/api-redesign-update-task`
**Total Tests:** 58 tests for update_task() (36 new + 22 updated)

### 📋 REMAINING WORK

## Implementation Order & Analysis

---

## PHASE 1: Complete Task Functions (3 remaining)

### 1.1 update_tasks() - BATCH TASK UPDATES
**Priority:** HIGH (completes task update consolidation)
**Estimated Complexity:** D (CC ~25)

**Consolidates:**
- complete_tasks() ✅
- drop_tasks() ✅
- move_tasks() ✅
- add_tag_to_tasks() ✅
- remove_tag_from_tasks() ✅

**New Signature:**
```python
def update_tasks(
    task_ids: Union[str, list[str]],  # Variable quantity
    # EXCLUDED: task_name, note (require unique values)
    flagged: Optional[bool] = None,
    status: Optional[TaskStatus] = None,
    completed: Optional[bool] = None,
    project_id: Optional[str] = None,
    parent_task_id: Optional[str] = None,
    tags: Optional[list[str]] = None,
    add_tags: Optional[list[str]] = None,
    remove_tags: Optional[list[str]] = None,
    due_date: Optional[str] = None,
    defer_date: Optional[str] = None,
    estimated_minutes: Optional[int] = None
) -> dict
```

**Return Format:**
```python
{
    "updated_count": int,
    "failed_count": int,
    "updated_ids": list[str],
    "failures": [{"task_id": str, "error": str}, ...]
}
```

**Test Strategy:**
- Test single ID (Union type handling)
- Test multiple IDs
- Test partial failures (continue processing)
- Test all field combinations
- Test conflict validation (project_id vs parent_task_id, tags vs add_tags)
- Test that task_name/note are NOT accepted

**Estimated Tests:** ~15 new tests

---

### 1.2 delete_tasks() - ENHANCED WITH UNION TYPE
**Priority:** HIGH (consolidates delete operations)
**Estimated Complexity:** B (CC ~8)

**Consolidates:**
- delete_task() ✅
- delete_tasks() (already exists, just enhance)

**Enhanced Signature:**
```python
def delete_tasks(
    task_ids: Union[str, list[str]]  # NEW: Accepts single or multiple
) -> dict
```

**Current Implementation:** Already accepts list[str]
**Change Needed:** Add Union[str, list[str]] support

**Test Strategy:**
- Test single ID string
- Test list of IDs
- Test empty list
- Test partial failures
- Test not found errors

**Estimated Tests:** ~5 new tests (modify existing)

---

### 1.3 create_task() - MERGE WITH create_inbox_task()
**Priority:** MEDIUM (completes task creation consolidation)
**Estimated Complexity:** C (CC ~12)

**Consolidates:**
- add_task() (rename to create_task)
- create_inbox_task() ✅

**Enhanced Signature:**
```python
def create_task(
    task_name: str,  # REQUIRED
    project_id: Optional[str] = None,  # None = inbox
    parent_task_id: Optional[str] = None,
    note: Optional[str] = None,
    due_date: Optional[str] = None,
    defer_date: Optional[str] = None,
    flagged: bool = False,
    tags: Optional[list[str]] = None,
    estimated_minutes: Optional[int] = None
) -> str  # Returns task_id
```

**Change Needed:**
- Rename add_task() to create_task()
- Make project_id optional (None = inbox)
- Remove create_inbox_task() function

**Test Strategy:**
- Test creation in project
- Test creation in inbox (project_id=None)
- Test with parent_task_id
- Test conflict (project_id + parent_task_id)
- Test all optional fields

**Estimated Tests:** ~8 new tests

---

## PHASE 2: Implement Project Functions (4 functions)

### 2.1 update_project() - ENHANCE EXISTING
**Priority:** HIGH (consolidates project updates)
**Estimated Complexity:** D (CC ~30)

**Consolidates:**
- update_project() (enhance existing)
- set_project_status() ✅
- drop_project() ✅
- set_review_interval() ✅
- mark_project_reviewed() ✅

**Enhanced Signature:**
```python
def update_project(
    project_id: str,
    project_name: Optional[str] = None,
    folder_path: Optional[str] = None,
    note: Optional[str] = None,
    sequential: Optional[bool] = None,
    status: Optional[ProjectStatus] = None,  # NEW
    review_interval_weeks: Optional[int] = None,  # NEW
    last_reviewed: Optional[str] = None  # NEW (ISO format)
) -> dict
```

**Return Format:**
```python
{
    "success": bool,
    "project_id": str,
    "updated_fields": list[str],
    "error": Optional[str]
}
```

**Test Strategy:**
- Test all new fields (status, review_interval, last_reviewed)
- Test status enum and string acceptance
- Test multiple field updates
- Test error handling
- Similar to update_task() testing

**Estimated Tests:** ~15 new tests

---

### 2.2 update_projects() - NEW BATCH FUNCTION
**Priority:** HIGH (completes project update consolidation)
**Estimated Complexity:** C (CC ~20)

**Consolidates:**
- drop_projects() ✅

**New Signature:**
```python
def update_projects(
    project_ids: Union[str, list[str]],
    # EXCLUDED: project_name, note (require unique values)
    status: Optional[ProjectStatus] = None,
    folder_path: Optional[str] = None,
    sequential: Optional[bool] = None,
    review_interval_weeks: Optional[int] = None,
    last_reviewed: Optional[str] = None
) -> dict
```

**Return Format:**
```python
{
    "updated_count": int,
    "failed_count": int,
    "updated_ids": list[str],
    "failures": [{"project_id": str, "error": str}, ...]
}
```

**Test Strategy:**
- Test single ID (Union type)
- Test multiple IDs
- Test partial failures
- Test all field combinations
- Test that project_name/note are NOT accepted

**Estimated Tests:** ~12 new tests

---

### 2.3 delete_projects() - ENHANCE WITH UNION TYPE
**Priority:** MEDIUM
**Estimated Complexity:** B (CC ~8)

**Consolidates:**
- delete_project() ✅
- delete_projects() (already exists, enhance)

**Enhanced Signature:**
```python
def delete_projects(
    project_ids: Union[str, list[str]]  # NEW: Single or multiple
) -> dict
```

**Change Needed:** Add Union type support

**Estimated Tests:** ~5 new tests

---

### 2.4 create_project() - KEEP AS-IS (ALREADY GOOD)
**Priority:** LOW (may just need minor enhancements)
**Estimated Complexity:** Current (no changes needed)

**Already supports:**
- name, folder_path, note, sequential

**Potential Enhancement:**
```python
def create_project(
    name: str,
    folder_path: Optional[str] = None,
    note: Optional[str] = None,
    sequential: bool = False,
    status: ProjectStatus = ProjectStatus.ACTIVE,  # NEW
    review_interval_weeks: Optional[int] = None  # NEW
) -> str
```

**Estimated Tests:** ~3 new tests (if enhanced)

---

## PHASE 3: Enhanced Read Functions (2 functions)

### 3.1 get_tasks() - ENHANCE EXISTING
**Priority:** MEDIUM
**Estimated Complexity:** Current F (CC 66) - already complex

**Enhancements Needed:**
```python
def get_tasks(
    task_id: Optional[str] = None,  # NEW: Filter to specific task
    parent_task_id: Optional[str] = None,  # NEW: Filter by parent
    include_full_notes: bool = False,  # NEW: Return full notes
    # ... existing parameters
) -> list[dict]
```

**Consolidates:**
- get_task() ✅ (via task_id parameter)
- get_subtasks() ✅ (via parent_task_id parameter)
- get_note() ✅ (via include_full_notes parameter)
- get_inbox_tasks() ✅ (via inbox_only parameter - already exists)

**Test Strategy:**
- Test task_id filter
- Test parent_task_id filter
- Test include_full_notes flag
- Test combinations

**Estimated Tests:** ~8 new tests

---

### 3.2 get_projects() - ENHANCE EXISTING
**Priority:** MEDIUM
**Estimated Complexity:** Current D (CC 23)

**Enhancements Needed:**
```python
def get_projects(
    project_id: Optional[str] = None,  # NEW: Filter to specific project
    include_full_notes: bool = False,  # NEW: Return full notes
    # ... existing parameters (on_hold_only, query)
) -> list[dict]
```

**Consolidates:**
- get_project() ✅ (via project_id parameter)
- get_note() ✅ (via include_full_notes parameter)

**Test Strategy:**
- Test project_id filter
- Test include_full_notes flag
- Test combinations with existing filters

**Estimated Tests:** ~6 new tests

---

## PHASE 4: Keep As-Is Functions (6 functions)

These functions are already well-designed and don't need changes:

### 4.1 Folders (2 functions)
- **create_folder()** ✅ - Already good
- **get_folders()** ✅ - Already good

### 4.2 Tags (1 function)
- **get_tags()** ✅ - Already good

### 4.3 Perspectives (2 functions)
- **get_perspectives()** ✅ - Already good
- **switch_perspective()** ✅ - Already good (UI operation)

### 4.4 Specialized Operations (1 function)
- **reorder_task()** ✅ - Specialized positioning logic, keep separate

**No changes needed for these 6 functions.**

---

## PHASE 5: Functions to DELETE (27 functions)

### 5.1 Delete from omnifocus_client.py (client layer)

**Task Operations (10 functions):**
1. complete_task() → update_task(completed=True)
2. complete_tasks() → update_tasks(completed=True)
3. drop_task() → update_task(status=DROPPED)
4. drop_tasks() → update_tasks(status=DROPPED)
5. move_task() → update_task(project_id=X)
6. move_tasks() → update_tasks(project_id=X)
7. set_parent_task() → update_task(parent_task_id=X)
8. set_estimated_minutes() → update_task(estimated_minutes=X)
9. add_tag_to_task() → update_task(add_tags=[...])
10. remove_tag_from_tasks() → update_tasks(remove_tags=[...])

**Project Operations (6 functions):**
11. drop_project() → update_project(status=DROPPED)
12. drop_projects() → update_projects(status=DROPPED)
13. set_review_interval() → update_project(review_interval_weeks=X)
14. mark_project_reviewed() → update_project(last_reviewed=today)
15. set_project_status() → update_project(status=X)
16. delete_project() → delete_projects(single_id)

**Read Operations (5 functions):**
17. get_task() → get_tasks(task_id=X)
18. get_project() → get_projects(project_id=X)
19. get_subtasks() → get_tasks(parent_task_id=X)
20. get_note() → get_{tasks|projects}(include_full_notes=True)
21. get_stalled_projects() → Client-side filtering

**Other Operations (4 functions):**
22. create_inbox_task() → create_task(project_id=None)
23. add_note() → Client-side (fetch + concat + update)
24. get_projects_due_for_review() → Client-side filtering
25. delete_task() → delete_tasks(single_id)
26. add_tag_to_tasks() → update_tasks(add_tags=[...])
27. search_projects() → Potentially keep or merge into get_projects

**Action:** Mark as deprecated with clear migration instructions

---

### 5.2 Delete from server_fastmcp.py (MCP server layer)

All 27 corresponding @mcp.tool() decorated functions must be removed.

**Strategy:**
1. Add deprecation warnings in v1.0.0
2. Remove in v1.1.0 or v2.0.0

---

## Summary: Final API Structure (16 Core Functions)

### Projects (5 functions)
1. ✅ create_project()
2. ✅ get_projects() (enhanced)
3. 🔄 update_project() (enhance existing)
4. ⭐ update_projects() (NEW)
5. 🔄 delete_projects() (enhance with Union)

### Tasks (6 functions)
1. 🔄 create_task() (rename + merge)
2. ✅ get_tasks() (enhance existing)
3. ✅ update_task() (DONE - Step 1)
4. ⭐ update_tasks() (NEW)
5. 🔄 delete_tasks() (enhance with Union)
6. ✅ reorder_task()

### Folders (2 functions)
7. ✅ create_folder()
8. ✅ get_folders()

### Tags (1 function)
9. ✅ get_tags()

### Perspectives (2 functions)
10. ✅ get_perspectives()
11. ✅ switch_perspective()

**Total: 16 functions** (down from 40)

---

## Implementation Roadmap

### Step 1: ✅ COMPLETED
- update_task() enhanced
- Enums added
- Tests passing

### Step 2: Complete Task Functions (Estimated: 3-4 days)
1. update_tasks() - 1-2 days
2. delete_tasks() enhancement - 0.5 days
3. create_task() rename/merge - 1 day

### Step 3: Complete Project Functions (Estimated: 3-4 days)
1. update_project() enhancement - 1-2 days
2. update_projects() NEW - 1-2 days
3. delete_projects() enhancement - 0.5 days
4. create_project() enhancement (optional) - 0.5 days

### Step 4: Enhanced Read Functions (Estimated: 2 days)
1. get_tasks() enhancements - 1 day
2. get_projects() enhancements - 1 day

### Step 5: Cleanup & Deprecation (Estimated: 1-2 days)
1. Mark 27 functions as deprecated
2. Add migration warnings
3. Update CHANGELOG.md
4. Update documentation
5. Create migration guide

**Total Estimated Time: 9-12 days**

---

## Testing Summary

**New Tests Needed:**
- update_tasks(): ~15 tests
- delete_tasks(): ~5 tests
- create_task(): ~8 tests
- update_project(): ~15 tests
- update_projects(): ~12 tests
- delete_projects(): ~5 tests
- get_tasks() enhancements: ~8 tests
- get_projects() enhancements: ~6 tests

**Total New Tests: ~74 tests**

**Existing Tests to Update:**
- Tests calling deprecated functions: ~100+ tests
- Strategy: Add deprecation warnings, keep tests passing

---

## Risk Assessment

### High Risk Areas
1. **Complexity**: update_tasks() and update_projects() will have F ratings
   - Mitigation: Document in CODE_QUALITY.md
2. **Breaking Changes**: Extensive API surface changes
   - Mitigation: Deprecation period, migration guide
3. **Integration Testing**: Need real OmniFocus validation
   - Mitigation: Run integration tests before each commit

### Medium Risk Areas
1. **AppleScript Errors**: Batch operations may reveal edge cases
   - Mitigation: Extensive error handling, test partial failures
2. **Performance**: Batch operations on large datasets
   - Mitigation: Test with realistic data sizes

### Low Risk Areas
1. **Read function enhancements**: Low risk, additive changes
2. **Keep-as-is functions**: No changes = no risk

---

## Success Criteria

- [ ] All 16 core functions implemented
- [ ] All new tests passing (74+ tests)
- [ ] All existing tests updated and passing
- [ ] Complexity documented for F-rated functions
- [ ] CHANGELOG.md updated
- [ ] Migration guide created
- [ ] Integration tests passing
- [ ] Documentation complete

