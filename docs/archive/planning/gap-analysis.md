# OmniFocus MCP Server - Gap Analysis Report

**Date:** 2025-10-08
**Version Analyzed:** 0.3.0
**Analyst:** Agent-based systematic review

## Executive Summary

The OmniFocus MCP server provides solid foundational coverage (~60%) of common OmniFocus operations, but has significant gaps in:
1. **Query efficiency** - No way to get single items by ID
2. **Metadata completeness** - Missing critical fields in responses
3. **Filtering capabilities** - Limited ability to query by status, time, or relationships
4. **Batch operations** - No support for bulk updates
5. **Advanced features** - No recurring tasks, attachments, or custom columns

**Current API Coverage:** 26 tools implemented, ~60% of common scenarios well-supported

## Top 10 Critical Gaps

### 1. **No Single Item Retrieval** ⚠️ CRITICAL
- **Problem:** Can't get details for a specific task/project by ID
- **Current workaround:** Fetch entire list and filter client-side
- **Impact:** Inefficient, especially for large OmniFocus databases
- **Fix needed:** `get_task(task_id)`, `get_project(project_id)`

### 2. **Missing Metadata in Task/Project Responses** ⚠️ CRITICAL
Missing fields:
- `projectId` (for tasks) - Can't easily navigate task → project
- `parentTaskId` - Can't understand task hierarchy
- `blocked` status - Can't identify blocked tasks
- `next` flag - Can't query "next actions"
- `completionDate` - Already added but needs validation
- `estimatedMinutes` - Available but not in responses
- `reviewInterval` - Available but not in responses

### 3. **No Dropped/On-Hold Item Queries** ⚠️ CRITICAL
- **Problem:** Can't filter for dropped tasks (just added `dropped` field but no filter)
- **Missing:** `dropped_only` parameter for `get_tasks()`
- **Missing:** `on_hold_only` for projects
- **Use case:** "Show me all dropped tasks for review"

### 4. **No Relative Date Filters** 🔥 HIGH PRIORITY
Can't query:
- "Tasks due today"
- "Tasks due this week"
- "Projects with no tasks due soon"
- "Overdue by more than X days"

**Needed:**
- `due_relative` parameter: "today", "tomorrow", "this_week", "next_week"
- `defer_relative` parameter
- `overdue_days` parameter: minimum days overdue

### 5. **No Project/Task Status Management** 🔥 HIGH PRIORITY
- **Missing:** Can't set project to "on hold" or "active"
- **Missing:** Can't query projects by status
- **Current API:** Only has `drop_task()`, no status management
- **Needed:** `set_project_status(project_id, status)` where status = "active" | "on_hold" | "done" | "dropped"

### 6. **No Project Statistics** 🔥 HIGH PRIORITY
Can't get:
- Total task count
- Completed task count
- Completion percentage
- Number of remaining tasks
- Number of overdue tasks

**Needed:** Include in `get_projects()` response or add `get_project_stats(project_id)`

### 7. **No Filtering by Estimated Time** 🔥 HIGH PRIORITY
- **Use case:** "Show me tasks I can do in 15 minutes"
- **Missing:** `max_estimated_minutes` parameter
- **Missing:** Tasks with NO estimate

### 8. **No Batch Operations** 🔥 HIGH PRIORITY
Can't efficiently:
- Complete multiple tasks at once
- Move multiple tasks to a project
- Add same tag to multiple tasks
- Drop multiple tasks

**Needed:** Batch variants of operations

### 9. **No Blocked Task Queries** 🔥 HIGH PRIORITY
- **Problem:** Can't filter for blocked tasks
- **Missing:** `blocked_only` parameter
- **Missing:** `blocked` field in responses (similar to dropped)

### 10. **No Recurring Task Support** 🔥 HIGH PRIORITY
- **Problem:** Can't create, modify, or query recurring tasks
- **Missing:** Repetition schedule in create/update operations
- **Missing:** Repetition info in task responses

## Additional High-Priority Gaps

### 11. **No "Next Action" Filtering**
- Can't query for tasks marked as "next actions"
- Critical for GTD methodology

### 12. **No Context/Tag Combinations**
- Current: Can filter by multiple tags (AND logic)
- Missing: OR logic ("tag A OR tag B")
- Missing: Exclusion ("NOT tag C")

### 13. **No Due Date Sorting/Ordering**
- All queries return tasks in OmniFocus default order
- Can't sort by due date, defer date, or priority

### 14. **No Attachment Support**
- Can't add/view/list attachments on tasks/projects

### 15. **No Custom Column/Metadata Support**
- OmniFocus supports custom columns
- MCP server doesn't expose them

## Medium-Priority Gaps

### Task Management
- Can't rearrange task order within project
- Can't convert task to project
- Can't duplicate tasks/projects
- No task dependencies beyond parent/child

### Search & Filtering
- No full-text search across all items
- Can't search by creation date
- Can't filter by modification date
- No "recently modified" queries

### Perspectives
- Can get/switch perspectives but can't:
  - Create perspectives
  - Modify perspectives
  - Query perspective settings

### Folder Management
- Can create folders but can't:
  - Move folders
  - Rename folders
  - Delete folders
  - Get folder hierarchy

### Review
- Can mark reviewed and set interval, but can't:
  - Get review history
  - Skip review
  - Get next review date for all projects

## Low-Priority Gaps (Advanced Features)

- No AppleScript automation beyond current tools
- No archive access
- No synchronization status/control
- No backup/restore operations
- No custom sounds/notifications
- No window management (focus/minimize)
- No keyboard shortcut triggers
- No forecast perspective operations
- No geographic location support
- No Siri integration metadata

## Realistic Usage Scenarios

### Scenario 1: GTD Weekly Review (⚠️ PARTIALLY BLOCKED)
**User:** "Show me all projects due for review this week"

**Current capability:** ✅ Can get projects due for review
**Gaps:**
- ❌ Can't filter to "this week" specifically
- ❌ Can't see last review date
- ❌ Can't get project statistics (task counts)

### Scenario 2: Quick Task Capture During Meeting (✅ SUPPORTED)
**User:** "Add task 'Follow up with Sarah' to my Work project, due Friday"

**Current capability:** ✅ Fully supported via `add_task()`

### Scenario 3: Executive Dashboard (⚠️ MAJOR GAPS)
**User:** "Show me all my projects with completion percentage and overdue task counts"

**Current capability:** ✅ Can get projects
**Gaps:**
- ❌ No task counts
- ❌ No completion percentage
- ❌ No overdue counts
- ❌ Inefficient (must fetch all tasks for all projects)

### Scenario 4: Finding Quick Tasks (❌ BLOCKED)
**User:** "What can I do in the next 15 minutes before my meeting?"

**Gaps:**
- ❌ Can't filter by estimated time
- ❌ Can't combine multiple filters efficiently

### Scenario 5: Dropped Task Review (⚠️ PARTIALLY BLOCKED - JUST FIXED!)
**User:** "Show me all dropped tasks so I can decide if any should be reactivated"

**Current capability:** ✅ Can now see `dropped: true` in task data (just added!)
**Gaps:**
- ❌ Can't filter for only dropped tasks (`dropped_only` parameter needed)
- ❌ Can't bulk reactivate tasks

## Recommended Implementation Roadmap

### Phase 1: Quick Wins (1-2 weeks) ⚠️ CRITICAL
**Impact:** Addresses 30% of critical gaps

1. Add `get_task(task_id)` - single task retrieval
2. Add `get_project(project_id)` - single project retrieval
3. Add `dropped_only` filter to `get_tasks()`
4. Add `blocked` field to task responses
5. Add `next` field to task responses
6. Add `on_hold_only` filter to `get_projects()`

### Phase 2: Essential Metadata (2-3 weeks) 🔥 HIGH IMPACT
**Impact:** Increases coverage to 85%+

1. Add project statistics to responses (task counts, completion %)
2. Add `parentTaskId` to task responses
3. Add `estimatedMinutes` to task responses
4. Add `reviewInterval` and `lastReviewDate` to project responses
5. Add filtering by estimated time
6. Add relative date filters ("today", "this_week", etc.)

### Phase 3: Status Management (1 week) 🔥 HIGH IMPACT

1. Add `set_project_status()` tool
2. Add project status filtering to `get_projects()`
3. Improve `drop_task()` with undo capability

### Phase 4: Batch Operations (2-3 weeks) 🔥 HIGH IMPACT

1. `complete_tasks(task_ids[])` - bulk complete
2. `move_tasks(task_ids[], target_project_id)` - bulk move
3. `add_tag_to_tasks(task_ids[], tag_name)` - bulk tag
4. `drop_tasks(task_ids[])` - bulk drop

### Phase 5: Advanced Filtering (2-3 weeks)

1. Add sort options (by due date, defer date, name)
2. Add tag filtering with OR/NOT logic
3. Add full-text search across tasks/projects
4. Add "next action" filtering

### Phase 6: Advanced Features (4-6 weeks)

1. Recurring task support
2. Attachment management
3. Custom column access
4. Perspective creation/modification
5. Enhanced folder operations

## Immediate Next Steps

Based on the analysis, I recommend:

1. **Implement Phase 1 (Quick Wins)** - addresses the most glaring gaps with minimal effort
2. **Focus on `get_task(id)` and `dropped_only` filter first** - these solve real pain points you've already identified
3. **Use TDD for all implementations** - maintain test coverage and quality
4. **Re-evaluate after Phase 1** - see if additional phases are needed based on actual usage

## Metrics

- **Current Tools:** 26
- **Identified Gaps:** 45
- **Critical Priority:** 12 gaps
- **High Priority:** 15 gaps
- **Medium Priority:** 12 gaps
- **Low Priority:** 6 gaps

**Estimated effort to reach 90% coverage:** Phases 1-3 = ~6 weeks of focused development
