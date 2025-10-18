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

## TDD Implementation Checklist (CRITICAL!)

**For EVERY function, follow this complete TDD cycle:**

### Client Layer (omnifocus_client.py)
1. ✅ **Write client tests FIRST** - Unit tests with mocked AppleScript
2. ✅ **Run tests → Confirm FAIL** - Tests should fail (function not implemented)
3. ✅ **Implement client function** - Add/enhance function in omnifocus_client.py
4. ✅ **Run tests → Confirm PASS** - All tests should pass
5. ✅ **Check complexity** - Run `./scripts/check_complexity.sh`

### Server Layer (server_fastmcp.py)
6. ✅ **Write server tests FIRST** - MCP tool tests with mocked client
7. ✅ **Run tests → Confirm FAIL** - Tests should fail (MCP tool not updated)
8. ✅ **Implement/update MCP tool** - Add/enhance @mcp.tool() function
9. ✅ **Run tests → Confirm PASS** - All tests should pass

### Integration Layer (test_integration_real.py)
10. ✅ **Write/update integration tests** - Tests client→AppleScript→OmniFocus
11. ✅ **Run integration tests** - `make test-integration` (safety guards enabled)

### End-to-End (E2E) Layer (test_e2e_real.py)
12. **Write/update E2E tests** - Tests MCP tool→client→AppleScript→OmniFocus
13. **Run E2E tests** - `make test-e2e` (full server stack with real OmniFocus)

### Documentation
14. ✅ **Update CODE_QUALITY.md** - If complexity is D/F, document rationale
15. **Update this plan** - Mark function as complete

### Commit
16. ✅ **Commit all layers together** - Client + Server + Tests in one commit

**⚠️ NEVER skip steps 6-9 (server layer)!**
**⚠️ NEVER skip steps 10-11 (integration tests)!**
**⚠️ NEVER skip steps 12-13 (E2E tests)!**

---

## Implementation Order & Analysis

---

## PHASE 1: Complete Task Functions (3 remaining)

### 1.1 update_tasks() - BATCH TASK UPDATES ✅ COMPLETED
**Priority:** HIGH (completes task update consolidation)
**Actual Complexity:** C (CC 16) - within acceptable range
**Completion Date:** 2025-10-18

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

**Client Tests (test_api_redesign_update.py):** ~15 tests
- Test single ID (Union type handling)
- Test multiple IDs
- Test partial failures (continue processing)
- Test all field combinations
- Test conflict validation (project_id vs parent_task_id, tags vs add_tags)
- Test that task_name/note are NOT accepted (ValueError)
- Test dict return format with counts

**Server Tests (test_server_redesign_update.py):** ~10 tests
- Test single ID string (Union type)
- Test list of IDs
- Test all field combinations
- Test dict handling from client
- Test formatted response for Claude

**Integration Tests (test_integration_real.py):** ~2 tests
- Test batch update with real OmniFocus
- Test partial failures in real environment

**E2E Tests (test_e2e_real.py):** ~2 tests
- Test MCP tool with batch IDs
- Test MCP tool with single ID string (Union type)
- Verify human-readable response format

**Implementation Notes:**
- ✅ Client layer: 17 tests (all PASS)
- ✅ Server layer: 7 tests (all PASS)
- ✅ Integration layer: 1 test added
- ✅ E2E layer: 2 tests added (test_update_tasks_batch_e2e, test_update_tasks_single_id_string_e2e)
- Uses **kwargs to catch task_name/note and raise helpful ValueError
- Calls update_task() internally for each task (simple loop implementation)
- Proper partial failure handling (continues processing, reports failures)
- Complexity C (16) - acceptable for batch operations, no documentation needed

---

### 1.2 delete_tasks() - ENHANCED WITH UNION TYPE ✅ COMPLETED
**Priority:** HIGH (consolidates delete operations)
**Actual Complexity:** B (CC 7) - excellent
**Completion Date:** 2025-10-18

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

**Client Tests:** ~5 tests
- Test single ID string (Union type)
- Test list of IDs
- Test empty list handling
- Test partial failures
- Test not found errors

**Server Tests:** ~3 tests
- Test single ID via MCP
- Test list of IDs via MCP
- Test error handling

**Integration Tests:** ~1 test
- Test deletion with real OmniFocus

**E2E Tests (test_e2e_real.py):** ~2 tests
- Test MCP tool with batch delete
- Test MCP tool with single ID (Union type)
- Verify human-readable response format

**Implementation Notes:**
- ✅ Client layer: 8 tests (all PASS)
- ✅ Server layer: 5 tests (all PASS)
- ✅ Integration layer: 1 test updated
- ✅ E2E layer: 2 tests added (test_delete_tasks_e2e, test_delete_single_task_e2e)
- Changed return type from int to dict (consistency with new API)
- AppleScript returns count, we infer which tasks succeeded (first N)
- Complexity B (7) - excellent, well within acceptable range

---

### 1.3 create_task() - MERGE WITH create_inbox_task() ✅ COMPLETED
**Priority:** MEDIUM (completes task creation consolidation)
**Actual Complexity:** C (CC 20) - acceptable for complex business logic
**Completion Date:** 2025-10-18

**Consolidates:**
- add_task() (rename to create_task)
- create_inbox_task() ✅

**Implemented Signature:**
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

**Implementation Notes:**
- ✅ Client layer: 9 tests (all PASS)
- ✅ Server layer: 7 tests (all PASS)
- ✅ Integration layer: 1 test added (test_create_task_real)
- ✅ E2E layer: 5 tests added (project, inbox, tags, dates, error handling)
- Three creation paths: inbox (project_id=None), project (project_id set), subtask (parent_task_id set)
- Conflict validation: Raises ValueError if both project_id and parent_task_id specified
- Returns task ID (string) instead of bool like legacy add_task()
- Server handles JSON string tags parameter, converts to list for client
- Fixed 4 legacy tests to handle delete_tasks() dict return format
- **E2E tests caught AppleScript bug**: `inbox` vs `make new inbox task` syntax

---

## PHASE 2: Implement Project Functions (4 functions)

**⚠️ IMPORTANT**: All Phase 2+ functions MUST include E2E tests in test_e2e_real.py!
- Follow the same 16-step TDD checklist (including steps 12-13 for E2E)
- Add E2E test strategy section to each function below
- E2E tests verify: MCP tool → client → AppleScript → OmniFocus

### 2.1 update_project() - ENHANCE EXISTING ✅ COMPLETED
**Priority:** HIGH (consolidates project updates)
**Actual Complexity:** D (CC 22) ✅ (estimated CC ~30)

**Consolidates:**
- update_project() (enhance existing) ✅
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

**Client Tests:** ~15 tests
- Test all new fields (status, review_interval, last_reviewed)
- Test status enum and string acceptance
- Test multiple field updates
- Test error handling
- Test dict return format

**Server Tests:** ~10 tests
- Test all new parameters via MCP
- Test status enum handling
- Test dict handling from client
- Test formatted response

**Integration Tests:** ~2 tests
- Test review_interval update with real OmniFocus
- Test status changes in real environment

**E2E Tests (test_e2e_real.py):** ~4 tests
- Test MCP tool with single field update
- Test MCP tool with multiple fields
- Test status enum via MCP layer
- Verify human-readable response
- Test error handling

**Implementation Notes:**
- ✅ Client layer: 17 tests added, all pass
- ✅ Server layer: 10 tests added, all pass (fixed bool/string handling for sequential parameter)
- ✅ Integration layer: 5 tests added, all pass
- ✅ E2E layer: 4 tests added (test_update_project_set_status_e2e, test_update_project_review_interval_e2e, test_update_project_multiple_fields_e2e, test_update_project_error_handling_e2e), all pass
- ✅ CODE_QUALITY.md updated with D (CC 22) documentation
- ✅ AppleScript bugs fixed:
  - Review interval: Must use record format `{unit:week, steps:N, fixed:true}`, not just a number
  - Folder move: Must use `move theProject to end of projects of targetFolder`, not `set folder of`
  - Folder path delimiter: Uses ">" not ":"
- ✅ Known issues documented:
  - get_project() reviewInterval parsing bug (returns None) - noted in integration tests
  - get_project() status returns with " status" suffix - test expectations adjusted

---

### 2.2 update_projects() - NEW BATCH FUNCTION ✅ COMPLETED
**Priority:** HIGH (completes project update consolidation)
**Actual Complexity:** C (CC 12) ✅ (estimated CC ~20)

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

**Client Tests:** ~12 tests
- Test single ID (Union type)
- Test multiple IDs
- Test partial failures
- Test all field combinations
- Test that project_name/note are NOT accepted (ValueError)

**Server Tests:** ~8 tests
- Test single ID via MCP
- Test list of IDs
- Test all field combinations
- Test error handling

**Integration Tests:** ~2 tests
- Test batch project updates with real OmniFocus
- Test partial failures

**E2E Tests (test_e2e_real.py):** ~2 tests
- Test MCP tool with batch project IDs
- Test MCP tool with single ID string (Union type)
- Verify human-readable response

**Implementation Notes:**
- ✅ Client layer: 14 tests added, all pass
- ✅ Server layer: 7 tests added, all pass (handles bool/string for sequential parameter)
- ✅ Integration layer: 2 tests added
- ✅ E2E layer: 2 tests added (test_update_projects_batch_e2e, test_update_projects_single_id_e2e)
- ✅ CODE_QUALITY.md updated with C (CC 12) rating
- ✅ Implementation uses loop calling update_project() for each ID (simple, maintainable)
- ✅ Properly rejects project_name and note parameters via **kwargs pattern
- ✅ Supports Union[str, list[str]] for project_ids

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

**Test Strategy:**

**Client Tests:** ~5 tests
- Test single ID (Union type)
- Test list of IDs
- Test partial failures

**Server Tests:** ~3 tests
- Test single ID via MCP
- Test list of IDs via MCP

**Integration Tests:** ~1 test
- Test deletion with real OmniFocus

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

**Test Strategy (if enhanced):**

**Client Tests:** ~3 tests
- Test new status parameter
- Test new review_interval_weeks parameter

**Server Tests:** ~2 tests
- Test new parameters via MCP

**Integration Tests:** ~1 test
- Test enhanced creation with real OmniFocus

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

**Client Tests:** ~8 tests
- Test task_id filter
- Test parent_task_id filter
- Test include_full_notes flag (returns full note, not truncated)
- Test combinations

**Server Tests:** ~5 tests
- Test task_id parameter via MCP
- Test parent_task_id parameter via MCP
- Test include_full_notes flag

**Integration Tests:** ~2 tests
- Test task_id retrieval with real OmniFocus
- Test include_full_notes with real OmniFocus

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

**Client Tests:** ~6 tests
- Test project_id filter
- Test include_full_notes flag
- Test combinations with existing filters (on_hold_only, query)

**Server Tests:** ~4 tests
- Test project_id parameter via MCP
- Test include_full_notes flag

**Integration Tests:** ~1 test
- Test project_id retrieval with real OmniFocus

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

**CRITICAL: Every function must have ALL THREE layers tested!**

| Function | Client Tests | Server Tests | Integration Tests | Total |
|----------|-------------|--------------|-------------------|-------|
| update_tasks() | 15 | 10 | 2 | 27 |
| delete_tasks() | 5 | 3 | 1 | 9 |
| create_task() | 8 | 5 | 2 | 15 |
| update_project() | 15 | 10 | 2 | 27 |
| update_projects() | 12 | 8 | 2 | 22 |
| delete_projects() | 5 | 3 | 1 | 9 |
| create_project() (if enhanced) | 3 | 2 | 1 | 6 |
| get_tasks() enhancements | 8 | 5 | 2 | 15 |
| get_projects() enhancements | 6 | 4 | 1 | 11 |
| **TOTAL** | **77** | **50** | **14** | **141 tests** |

**Existing Tests to Update:**
- Tests calling deprecated functions: ~100+ tests
- Strategy: Update to use new dict return formats

**Test Files:**
- `tests/test_api_redesign_update.py` - Client layer tests
- `tests/test_server_redesign_update.py` - Server layer tests
- `tests/test_integration_real.py` - Integration tests (real OmniFocus)

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

