# OmniFocus MCP Server - Implementation Roadmap

**Based on:** Gap analysis + user priorities
**Target coverage:** ~95% of use cases
**Total estimated effort:** 16-20 weeks

## User Priorities (Confirmed)

✅ Batch operations
✅ Advanced search/filtering
✅ Recurring tasks
✅ Project management intelligence
✅ Attachments
✅ Conditional/complex queries
⚠️ Archive access (challenging - see notes below)

---

## Phase 1: Quick Wins (Week 1-2) ⚠️ CRITICAL - START HERE

**Goal:** Fix the most glaring gaps with minimal effort
**Estimated effort:** 1-2 weeks
**Impact:** 30% of critical gaps resolved

### Tasks

1. **Single item retrieval** (TDD)
   - `get_task(task_id: str)` → returns full task details
   - `get_project(project_id: str)` → returns full project details
   - **Why:** Eliminates inefficient "fetch all and filter" pattern

2. **Dropped task filtering** (TDD)
   - Add `dropped_only: bool` parameter to `get_tasks()`
   - **Why:** User requested, enables dropped task review workflow

3. **Blocked task support** (TDD)
   - Add `blocked: bool` field to task responses
   - Add `blocked_only: bool` parameter to `get_tasks()`
   - **Why:** Essential for GTD "waiting for" contexts

4. **Next action support** (TDD)
   - Add `next: bool` field to task responses
   - Add `next_only: bool` parameter to `get_tasks()`
   - **Why:** Core GTD concept - identify immediately actionable tasks

5. **On-hold project filtering** (TDD)
   - Add `on_hold_only: bool` parameter to `get_projects()`
   - **Why:** Parallel to dropped task filtering

---

## Phase 2: Essential Metadata (Week 3-5) 🔥 HIGH IMPACT

**Goal:** Complete the data model with missing fields
**Estimated effort:** 2-3 weeks
**Impact:** Enables advanced scenarios

### Tasks

1. **Task hierarchy** (TDD)
   - Add `parentTaskId: str | None` to task responses
   - Add `get_subtasks(task_id: str)` method
   - **Why:** Navigate task hierarchies, understand dependencies

2. **Project statistics** (TDD)
   - Add to `get_project()` response:
     - `taskCount: int` - total tasks
     - `completedTaskCount: int` - completed tasks
     - `remainingTaskCount: int` - active tasks
     - `completionPercentage: float` - progress
   - **Why:** Dashboard views, project health monitoring

3. **Time estimates in responses** (TDD)
   - Add `estimatedMinutes: int | None` to task responses
   - **Why:** Time management, workload planning

4. **Review metadata** (TDD)
   - Add to project responses:
     - `reviewInterval: str | None` - e.g., "1 week"
     - `lastReviewDate: str | None` - ISO format
     - `nextReviewDate: str | None` - calculated
   - **Why:** GTD weekly review workflow

5. **Relative date filters** (TDD)
   - Add `due_relative: str` parameter to `get_tasks()`
     - Values: "today", "tomorrow", "this_week", "next_week", "overdue"
   - Add `defer_relative: str` parameter
   - **Why:** "What's due today?" queries

6. **Time estimate filtering** (TDD)
   - Add `max_estimated_minutes: int` parameter to `get_tasks()`
   - Add `has_estimate: bool` parameter (true = has estimate, false = no estimate)
   - **Why:** "What can I do in 15 minutes?" queries

---

## Phase 3: Batch Operations (Week 6-8) 🔥 USER PRIORITY

**Goal:** Enable bulk actions for efficiency
**Estimated effort:** 2-3 weeks
**Impact:** Massive efficiency gains for bulk operations

### Tasks

1. **Batch task completion** (TDD)
   - `complete_tasks(task_ids: list[str])` → returns success count
   - **Why:** Complete meeting action items in one call

2. **Batch task movement** (TDD)
   - `move_tasks(task_ids: list[str], target_project_id: str | None)`
   - If `target_project_id` is None, moves to inbox
   - **Why:** Reorganize after planning session

3. **Batch tagging** (TDD)
   - `add_tag_to_tasks(task_ids: list[str], tag_name: str)`
   - `remove_tag_from_tasks(task_ids: list[str], tag_name: str)`
   - **Why:** Bulk categorization

4. **Batch dropping** (TDD)
   - `drop_tasks(task_ids: list[str])`
   - **Why:** Clean up after project cancellation

5. **Batch deletion** (TDD)
   - `delete_tasks(task_ids: list[str])`
   - `delete_projects(project_ids: list[str])`
   - **Why:** Bulk cleanup operations

---

## Phase 4: Advanced Search & Filtering (Week 9-11) 🔥 USER PRIORITY

**Goal:** Complex queries and searches
**Estimated effort:** 2-3 weeks
**Impact:** Power-user scenarios, conditional queries

### Tasks

1. **Boolean tag logic** (TDD)
   - Extend `get_tasks()` with:
     - `tag_filter_mode: str` - "and" | "or" | "not"
     - `tag_filter: list[str]` - existing parameter
   - **Why:** "Show tasks tagged work OR office but NOT waiting"

2. **Full-text search** (TDD)
   - `search_tasks(query: str, search_note: bool = True)` → list of tasks
   - `search_projects(query: str, search_note: bool = True)` → list of projects
   - **Why:** "Find anything mentioning 'budget'"

3. **Date range filtering** (TDD)
   - Add to `get_tasks()`:
     - `created_after: str` - ISO date
     - `created_before: str` - ISO date
     - `modified_after: str` - ISO date
     - `modified_before: str` - ISO date
   - **Why:** "Tasks created last week"

4. **Sorting options** (TDD)
   - Add `sort_by: str` parameter to `get_tasks()` and `get_projects()`
     - Values: "name", "due_date", "defer_date", "created_date", "modified_date", "priority"
   - Add `sort_order: str` - "asc" | "desc"
   - **Why:** "Show tasks sorted by due date"

5. **Aggregation queries** (TDD)
   - `get_project_aggregates(project_id: str)` → dict with:
     - `totalEstimatedMinutes: int`
     - `earliestDueDate: str | None`
     - `latestDueDate: str | None`
     - `overdueTaskCount: int`
   - **Why:** Project dashboard, workload analysis

6. **Conditional filters** (TDD)
   - Add to `get_projects()`:
     - `min_task_count: int` - projects with at least N tasks
     - `has_overdue_tasks: bool` - projects with overdue tasks
     - `has_no_due_dates: bool` - projects with no upcoming deadlines
   - **Why:** "Projects with 5+ tasks where at least one is overdue"

---

## Phase 5: Recurring Tasks (Week 12-14) 🔥 USER PRIORITY

**Goal:** Full recurring task support
**Estimated effort:** 2-3 weeks
**Impact:** Critical for users with recurring workflows

### Tasks

1. **Query recurring task info** (TDD)
   - Add to task responses:
     - `isRecurring: bool`
     - `repetitionRule: str | None` - human-readable (e.g., "Every Monday")
     - `nextOccurrence: str | None` - ISO date
   - **Why:** See which tasks are recurring

2. **Create recurring tasks** (TDD)
   - Extend `add_task()` with:
     - `repetition_rule: str` - AppleScript repetition format
   - Document common patterns (daily, weekly, monthly, etc.)
   - **Why:** "Create task that repeats every Monday"

3. **Update recurring tasks** (TDD)
   - Extend `update_task()` with:
     - `repetition_rule: str | None` - update or clear repetition
   - **Why:** Modify existing recurring tasks

4. **Filter by recurring status** (TDD)
   - Add `recurring_only: bool` parameter to `get_tasks()`
   - **Why:** "Show all my recurring tasks"

**Note:** Recurring task support requires understanding OmniFocus's repetition AppleScript syntax. May need research phase.

---

## Phase 6: Attachments (Week 15-16) 🔥 USER PRIORITY

**Goal:** Manage file attachments on tasks/projects
**Estimated effort:** 1-2 weeks
**Impact:** Document management, reference materials

### Tasks

1. **List attachments** (TDD)
   - `get_attachments(item_id: str, item_type: str = "task")` → list of attachments
   - Returns: `[{name: str, path: str, size: int}]`
   - **Why:** See what files are attached

2. **Add attachments** (TDD)
   - `add_attachment(item_id: str, file_path: str, item_type: str = "task")`
   - **Why:** "Attach this PDF to my 'File taxes' task"

3. **Remove attachments** (TDD)
   - `remove_attachment(item_id: str, attachment_name: str, item_type: str = "task")`
   - **Why:** Clean up obsolete attachments

4. **Include attachment info in responses** (TDD)
   - Add `attachmentCount: int` to task/project responses
   - Optional: Add `attachments: list` if detailed
   - **Why:** Know at a glance if items have attachments

**Note:** May need to handle file encoding/transfer for MCP protocol. Investigate if Claude Desktop can access local files directly.

---

## Phase 7: Project Intelligence (Week 17-18) 🔥 USER PRIORITY

**Goal:** Advanced project queries and metadata
**Estimated effort:** 1-2 weeks
**Impact:** Project portfolio management

### Tasks

1. **Project activity tracking** (TDD)
   - Add to project responses:
     - `lastModifiedDate: str | None` - ISO format
     - `lastActivityDate: str | None` - last task created/completed
   - Add `modified_after` filter to `get_projects()`
   - **Why:** "Projects not touched in a month"

2. **Project status management** (TDD)
   - `set_project_status(project_id: str, status: str)`
     - Status values: "active" | "on_hold" | "done" | "dropped"
   - Add `status: str` to project responses
   - **Why:** Manage project lifecycle

3. **Project health queries** (TDD)
   - `get_stalled_projects(days_inactive: int = 30)` → list of projects
   - Returns projects with no recent activity
   - **Why:** Identify neglected projects

4. **Task distribution analysis** (TDD)
   - Add to `get_project_aggregates()`:
     - `overdueTaskCount: int`
     - `dueTodayCount: int`
     - `dueThisWeekCount: int`
     - `noDueDateCount: int`
   - **Why:** Project deadline pressure analysis

---

## Phase 8: Archive Access (Week 19-20) ⚠️ CHALLENGING

**Goal:** Query archived/completed items
**Estimated effort:** 2-3 weeks
**Impact:** Historical analysis, mistake recovery

### Archive Location Found

- **Path:** `/Users/Morgan/Library/Group Containers/34YW5XSRB7.com.omnigroup.OmniFocus/com.omnigroup.OmniFocus3/com.omnigroup.OmniFocusModel/ArchiveDatabase.db`
- **Size:** 17 MB (has data!)
- **Format:** SQLite database
- **Note:** This is OmniFocus 3 archive; OF4 may use different location/schema

### Challenges

1. **AppleScript doesn't access archives** - Must query SQLite directly
2. **Schema unknown** - Need to reverse-engineer database structure
3. **Version differences** - OF3 vs OF4 schemas may differ
4. **Sync complexity** - Archive may not be up-to-date
5. **Security** - Direct database access bypasses OmniFocus's normal access controls

### Recommended Approach

**Option A: Direct SQLite Access** (recommended)
- Use Python `sqlite3` to query archive database directly
- Pros: Full access to archived data
- Cons: Schema reverse-engineering required, version brittleness

**Option B: AppleScript + Export**
- Have OmniFocus export archive data via AppleScript
- Pros: Uses official API
- Cons: AppleScript may not support archive access

**Option C: Skip for now**
- Wait for OmniFocus to add official archive API
- Implement if/when needed
- Pros: No technical debt
- Cons: Feature unavailable

### Tasks (if pursuing Option A)

1. **Reverse-engineer archive schema** (Research)
   - Open `ArchiveDatabase.db` with SQLite browser
   - Document table structure and relationships
   - Compare OF3 vs OF4 schemas

2. **Read-only archive queries** (TDD)
   - `search_archive(query: str)` → list of archived tasks/projects
   - `get_archived_project(project_id: str)` → archived project details
   - `get_archived_task(task_id: str)` → archived task details
   - **Why:** "Find that task I dropped last month"

3. **Archive date filtering** (TDD)
   - `get_archived_items(archived_after: str, archived_before: str)`
   - **Why:** "What did I complete in Q1?"

**Recommendation:** Start with Option C (skip), implement Option A later if real need emerges.

---

## Summary Timeline

| Phase | Weeks | Features | User Priority | Effort |
|-------|-------|----------|---------------|--------|
| Phase 1 | 1-2 | Quick wins (get single items, dropped filter) | ⚠️ Critical | Low |
| Phase 2 | 3-5 | Essential metadata (hierarchy, stats, estimates) | 🔥 High | Medium |
| Phase 3 | 6-8 | Batch operations | ✅ User requested | Medium |
| Phase 4 | 9-11 | Advanced search & filtering | ✅ User requested | High |
| Phase 5 | 12-14 | Recurring tasks | ✅ User requested | Medium |
| Phase 6 | 15-16 | Attachments | ✅ User requested | Medium |
| Phase 7 | 17-18 | Project intelligence | ✅ User requested | Medium |
| Phase 8 | 19-20 | Archive access | ✅ User requested | High* |

**Total:** 16-20 weeks (excluding archive if skipped)

*Archive access has high complexity due to direct database access requirements

## Coverage After Each Phase

- **Current:** ~60%
- **After Phase 1:** ~70%
- **After Phase 2:** ~85%
- **After Phase 3:** ~90%
- **After Phase 4:** ~93%
- **After Phase 5:** ~95%
- **After Phase 6:** ~96%
- **After Phase 7:** ~97%
- **After Phase 8:** ~99%

## Immediate Next Steps

1. **Review this roadmap** - confirm priorities
2. **Start Phase 1** - implement quick wins using TDD
3. **Re-evaluate after Phase 1** - adjust timeline based on velocity
4. **Consider archive approach** - decide on Option A/B/C before Phase 8

## Notes on Archive Access

Given the complexity, I recommend:
1. **Skip archive for initial implementation** (Phases 1-7)
2. **Revisit after Phase 7** when you have real-world experience with the MCP server
3. **Consider alternative:** Add a manual "export archive to JSON" feature users can trigger from OmniFocus, then query the JSON

This approach delivers 97% coverage without the technical risk of direct database access.
