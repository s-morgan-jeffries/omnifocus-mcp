# MCP Tool Consolidation Analysis

## Current State: 38 MCP Tools

### Analysis Methodology
Reviewing all @mcp.tool() decorated functions to identify:
1. Redundant wrappers that could be consolidated via parameters
2. Single/batch operation pairs
3. Specialized getters that duplicate base functionality

---

## Category 1: Search/Filter Redundancy

### 1. `search_projects()` → consolidate into `get_projects()`
**Current:**
- `search_projects(query)` - searches name/note/folder, returns active projects only
- `get_projects(...)` - 10 filter parameters, no text search

**Evidence of redundancy:**
```python
# omnifocus_client.py:1414
def search_projects(self, query: str):
    all_projects = self.get_projects()  # Just calls get_projects!
    # ... Python filtering by query string
```

**Proposal:** Add `query: Optional[str] = None` to `get_projects()`
- Enables: `get_projects(query="mortgage", status="active")`
- Deletion: Remove `search_projects()` entirely

---

### 2. `get_inbox_tasks()` → consolidate into `get_tasks()`
**Current:**
- `get_inbox_tasks()` - separate AppleScript for inbox tasks only
- `get_tasks(...)` - 19 filter parameters, but can't filter to inbox only

**Evidence of redundancy:**
```applescript
# omnifocus_client.py:2556
set allInboxTasks to inbox tasks  # Special AppleScript property
```

**Proposal:** Add `inbox_only: bool = False` to `get_tasks()`
- When True, use `inbox tasks` instead of `flattened tasks` in AppleScript
- Enables: `get_tasks(inbox_only=True, flagged_only=True)`
- Deletion: Remove `get_inbox_tasks()` entirely

---

### 3. `search_tasks()` - NOT exposed as MCP tool
**Status:** Already hidden from Claude Desktop
- Exists in omnifocus_client.py but NOT in server_fastmcp.py
- No action needed (not contributing to tool count/confusion)

---

## Category 2: Single vs Batch Operations

### 4. Task Operations
- `complete_task(task_id)` - single
- `complete_tasks(task_ids)` - batch ✓ KEEP BOTH

**Analysis:** Batch is more efficient for AppleScript, not just a wrapper. Keep separate.

### 5. Task Movement
- `move_task(task_id, project_id)` - single
- `move_tasks(task_ids, project_id)` - batch ✓ KEEP BOTH

**Analysis:** Same as above - batch optimization justified.

### 6. Tag Operations
- `add_tag_to_task(task_id, tag_name)` - single
- `add_tag_to_tasks(task_ids, tag_name)` - batch ✓ KEEP BOTH
- `remove_tag_from_tasks(task_ids, tag_name)` - batch only

**Analysis:** Keep all - batch operations are performance optimizations.

### 7. Task Deletion
- `delete_task(task_id)` - single
- `delete_tasks(task_ids)` - batch ✓ KEEP BOTH

### 8. Project Deletion
- `delete_project(project_id)` - single
- `delete_projects(project_ids)` - batch ✓ KEEP BOTH

### 9. Drop Tasks
- `drop_task(task_id)` - single
- `drop_tasks(task_ids)` - batch ✓ KEEP BOTH

**Batch operations verdict:** All justified - they use single AppleScript calls for efficiency.

---

## Category 3: Specialized Getters

### 10. `get_project(project_id)` ✓ KEEP
**Analysis:** Single-item lookup by ID is distinct from filtered list queries. Keep.

### 11. `get_task(task_id)` ✓ KEEP
**Analysis:** Same as above.

### 12. `get_subtasks(parent_task_id)` ✓ KEEP
**Analysis:** Specialized query for task hierarchy. Could theoretically add `parent_task_id` to `get_tasks()`, but subtask queries are conceptually different enough to warrant separate tool.

### 13. `get_stalled_projects()` ✓ KEEP
**Analysis:** Complex business logic (projects with no recent activity). Not just a filter.

### 14. `get_projects_due_for_review()` ✓ KEEP
**Analysis:** Specific review workflow feature. Not a simple filter.

### 15. `get_tags()` ✓ KEEP
**Analysis:** List all tags - fundamentally different from filtering tasks by tags.

### 16. `get_folders()` ✓ KEEP
**Analysis:** List folder hierarchy - separate concern from projects.

### 17. `get_perspectives()` ✓ KEEP
**Analysis:** OmniFocus UI feature - not related to data queries.

---

## Category 4: CRUD Operations (All Distinct)

### Create
- `create_project()` ✓
- `create_inbox_task()` ✓ (specialized: no project required)
- `add_task()` ✓ (requires project)
- `create_folder()` ✓

### Update
- `update_task()` ✓
- `set_project_status()` ✓
- `set_parent_task()` ✓
- `set_review_interval()` ✓
- `set_estimated_minutes()` ✓
- `mark_project_reviewed()` ✓

### Notes
- `add_note()` ✓ (append to existing)
- `get_note()` ✓ (read full content)

### Navigation
- `switch_perspective()` ✓

---

## Summary: Proposed Consolidations

### Delete 2 tools (38 → 36):
1. **Delete `search_projects()`** - add `query` param to `get_projects()`
2. **Delete `get_inbox_tasks()`** - add `inbox_only` param to `get_tasks()`

### Changes Required:

#### A. Enhance `get_projects()`
```python
def get_projects(
    # ... existing 10 parameters ...
    query: Optional[str] = None,  # NEW
) -> list[dict]:
    """Get projects with optional filtering.

    Args:
        query: Search term to filter by name, note, or folder path
        # ... rest of existing docs ...
    """
```

#### B. Enhance `get_tasks()`
```python
def get_tasks(
    # ... existing 19 parameters ...
    query: Optional[str] = None,  # NEW
    inbox_only: bool = False,     # NEW
) -> list[dict]:
    """Get tasks with optional filtering.

    Args:
        query: Search term to filter by name or note
        inbox_only: Only return inbox tasks (ignores project_id if True)
        # ... rest of existing docs ...
    """
```

---

## Impact Analysis

### Benefits:
1. **Reduces Claude Desktop confusion** - 2 fewer overlapping tools
2. **Enables powerful combinations:**
   - `get_tasks(query="mortgage", due_relative="this_week")`
   - `get_projects(query="home", status="active", has_overdue_tasks=True)`
3. **Clearer API** - one powerful tool vs multiple limited ones
4. **Less code** - remove redundant wrapper functions

### Risks:
1. **Parameter count** - `get_tasks()` grows from 19 to 21 parameters
   - Mitigation: Still manageable, all optional with good defaults
2. **Breaking change** - tools are removed
   - Mitigation: Document in CHANGELOG, bump to 0.5.0
3. **Test updates** - need to update all tests using removed tools
   - Mitigation: Systematic test refactoring

---

## Recommendation

**Proceed with consolidation:**
- Delete: `search_projects()`, `get_inbox_tasks()`
- Enhance: `get_projects()`, `get_tasks()`
- Version: Bump to 0.5.0 (breaking API change)
- Testing: Update ~30 affected tests

**Do NOT consolidate:**
- Batch operations (performance justified)
- Specialized getters (distinct business logic)
- CRUD operations (all unique)

**Final count: 36 tools** (down from 38)
