# Roadmap Alignment Review (2025-10-19)

**Agent Analysis:** Independent review of roadmap vs. v0.6.0 architecture

**Grade:** B+ (75-80% aligned)

## Executive Summary

The roadmap contains significant outdated content from pre-v0.6.0 phases. Of 20+ items:
- **12+ items should be removed** (already implemented or violate principles)
- **2 items are ready to implement** (1 critical bug, 1 code quality)
- **4 items need design review** (determine if primitive vs application logic)
- **2 items need research** (technical blockers)

## Critical Findings

### ✅ Ready to Implement (2 items)

**1. Fix mark_project_reviewed() Bug - CRITICAL**
- Sets `next review date` instead of `last review date`
- Blocks GTD workflow (user-reported)
- **Effort:** 5 minutes (one-line AppleScript fix)
- **Recommendation:** Implement immediately

**2. Rename omnifocus_client.py → omnifocus_connector.py**
- Code quality improvement
- Industry-standard terminology
- **Effort:** 1-2 hours
- **Recommendation:** Low priority, can proceed when time allows

### ❌ Already Implemented - Remove from Roadmap (8 items)

1. **move_project()** → Use `update_project(id, folder_path=X)` ✅ EXISTS
2. **move_projects()** → Use `update_projects(ids, folder_path=X)` ✅ EXISTS
3. **archive_projects()** → Use `update_projects(ids, status=DONE)` ✅ EXISTS
4. **Batch operations expansion** → Use `update_tasks()/update_projects()` parameters ✅ EXISTS
5. **parent_task_id in create_task** → Already supported ✅ EXISTS
6. **mark_projects_reviewed()** → Use `update_projects(ids, last_reviewed="now")` ✅ EXISTS
7. **set_review_intervals()** → Use `update_projects(ids, review_interval_weeks=X)` ✅ EXISTS
8. **set_estimated_minutes_batch()** → Use `update_tasks(ids, estimated_minutes=X)` ✅ EXISTS

**Key Insight:** The roadmap author didn't understand that v0.6.0's comprehensive `update_X()` functions already handle all these use cases via parameters.

### 🚫 Violates Architectural Principles - Remove (4+ items)

1. **Dedicated set_note() function** - Violates "no field-specific setters" anti-pattern
2. **Field-specific batch setters** - Should use comprehensive `update_X()` functions
3. **Status-specific functions** - Violates consolidated update pattern
4. **Move/hierarchy-specific functions** - Should use `update_X(folder_path)` or `update_X(project_id)`

**From ARCHITECTURE.md Anti-Patterns:**
- ❌ Field-specific setters: `set_due_date()`, `set_flag()`, `set_note()`
- ❌ Specialized filters as functions: `get_stalled_projects()`, `get_overdue_tasks()`
- ❌ Status-specific functions: `complete_task()`, `drop_task()`, `archive_projects()`

### 🤔 Needs Design Review (4 items)

**1. merge_projects(source_ids, target_id)**
- Multi-step operation (get tasks, move tasks, delete projects)
- **Question:** Server convenience function or client-side workflow?
- **Defer until:** Real user demonstrates workflow need
- **Can be done client-side:** Use existing primitives

**2. split_project(project_id, task_ids, new_name)**
- Multi-step operation (create project, move tasks)
- **Question:** Server convenience function or client-side workflow?
- **Defer until:** Real user demonstrates workflow need
- **Can be done client-side:** Use existing primitives

**3. show_project() / show_task()**
- UI navigation (focus OmniFocus window on item)
- **Precedent:** `switch_perspective()` is also UI control
- **AppleScript verified:** `set focus of front document window to item` works
- **Question:** Is UI navigation MCP server's responsibility?
- **Defer until:** User demonstrates this blocks real workflows

**4. Specialized operations clarification**
- Need to determine: OmniFocus primitive or application logic?
- Decision tree: Can `update_X()` handle it? (90% yes)

### 🔬 Needs Research - Technical Blockers (2 items)

**1. Attachments**
- `get_attachments()`, `add_attachment()`, `remove_attachment()`
- **Blocker:** Unclear how MCP/Claude Desktop handles local file paths
- **Research:** MCP file operation specification, security implications
- **Defer until:** MCP file handling is understood

**2. Archive Access**
- `search_archive()`, `get_archived_project()`, `get_archived_task()`
- **Blocker:** Direct SQLite access is high-risk
- **Research:** Archive database structure, safety guarantees, version differences
- **Defer until:** Safety approach proven, real user need demonstrated

## Architectural Principles Summary

### Core Principles (from ARCHITECTURE.md)

1. **Minimize tool call overhead** - Comprehensive update functions over specialized operations
2. **Prevent user errors** - Separate single/batch updates for unique-value fields
3. **Consistency over convenience** - Predictable patterns
4. **Union types for variable quantities** - `Union[str, list[str]]` for delete operations
5. **MCP-first design** - Keep create/update separate
6. **Structured returns** - Return `list[dict]` or `dict`

### Quick Decision Tree

Before adding any function:
1. **Can existing `update_X()` handle this?** (90% of cases: YES)
2. **Can existing `get_X()` handle this with a parameter?** (9% of cases: YES)
3. **Is this truly specialized logic?** (1% of cases: MAYBE)

### Anti-Patterns (Never Implement)

- ❌ Field-specific setters
- ❌ Specialized filters as functions
- ❌ Completion-specific functions
- ❌ Status-specific functions
- ❌ Hierarchy-specific functions
- ❌ Upsert patterns

## Current v0.6.0 API State

### 16 MCP Tools (Complete)

**Projects (5):** create, get, update, update (batch), delete
**Tasks (6):** create, get, update, update (batch), delete, reorder
**Folders (2):** create, get
**Tags (1):** get
**Perspectives (2):** get, switch

**Test Coverage:** 333 passing tests (89% coverage)

### What v0.6.0 Already Handles

**Project Operations:**
```python
# Move projects
update_project(id, folder_path="new/path")
update_projects([ids], folder_path="Archive")

# Archive/complete
update_projects([ids], status=ProjectStatus.DONE)

# Set review intervals
update_projects([ids], review_interval_weeks=4)

# Mark reviewed
update_projects([ids], last_reviewed="now")

# Change status
update_projects([ids], status=ProjectStatus.ON_HOLD)
```

**Task Operations:**
```python
# Move tasks
update_task(id, project_id=new_project)
update_tasks([ids], project_id=new_project)

# Complete/flag/estimate
update_tasks([ids], completed=True)
update_tasks([ids], flagged=True)
update_tasks([ids], estimated_minutes=30)

# Add tags
update_tasks([ids], add_tags=["urgent"])

# Reparent
update_tasks([ids], parent_task_id=new_parent)
```

## Key Insights

### 1. Roadmap Reflects Pre-v0.6.0 Thinking

Many items were written when 40+ specialized functions existed. The v0.6.0 redesign already solved these by consolidating into comprehensive `update_X()` functions.

### 2. Confusion About Batch Operations

The roadmap doesn't understand that `update_tasks()` and `update_projects()` ARE the batch operations. They accept `Union[str, list[str]]` and handle all "missing" batch operations via parameters.

### 3. Legitimate Gaps Are Rare

Of 20+ roadmap items, only 2 are immediately actionable. The rest are either already implemented, violate principles, need design review, or need research.

**This validates the v0.6.0 architecture** - the 16-function API really does cover the primitives.

### 4. Project Reorganization Is Complex

The 5 "project cleanup" operations reveal:
- 2 already exist (move, archive)
- 2 are complex multi-step operations (merge, split)

The complex ones need design decisions:
- Server convenience function? (wraps multiple primitives)
- Client-side workflow? (user chains operations)
- OmniFocus primitive? (belongs in MCP server)

## Recommendations

### Update Roadmap Structure

Replace "Upcoming Work" section with:

**Immediate:**
1. Fix mark_project_reviewed() bug (CRITICAL - 5 min)

**Short-Term:**
2. Rename omnifocus_client → omnifocus_connector (LOW - 1-2 hours)

**Under Investigation:**
3. merge_projects() - Multi-step operation (design review)
4. split_project() - Multi-step operation (design review)
5. show_project()/show_task() - UI navigation (design review)

**Future Research:**
6. Attachments - File operations (MCP spec unclear)
7. Archive access - SQLite access (high risk)

**Remove:**
8. All items already implemented (8 items)
9. All items violating principles (4+ items)

### Add "v0.6.0 Capabilities" Section

Before "Upcoming Work", clarify what already exists to prevent proposing redundant functions.

### Add Maintenance Note

Warn maintainers that roadmap contains pre-v0.6.0 items and to check ARCHITECTURE.md decision tree before adding anything.

## Summary Statistics

- **Total roadmap items analyzed:** 20+
- **Ready to implement:** 2 (10%)
- **Needs design review:** 4 (20%)
- **Needs research:** 2 (10%)
- **Should be removed:** 12+ (60%)

**Recommendation:** Clean up roadmap to reflect v0.6.0 maturity. Most items should be removed as they contradict the architectural principles that shaped the current API.

---

**Status:** Review complete, recommendations provided
**Next Step:** Discuss with maintainer before implementing changes
**Generated:** 2025-10-19
