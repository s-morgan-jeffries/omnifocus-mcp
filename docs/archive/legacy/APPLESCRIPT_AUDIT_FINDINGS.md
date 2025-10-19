# AppleScript Interface Audit - Findings

**Date:** October 11, 2025
**Purpose:** Identify missing properties in OmniFocus MCP server for project cleanup/reorganization use case

---

## Executive Summary

✅ **EXCELLENT NEWS:** All critical timestamp properties needed for project cleanup are available in AppleScript!

This enables the full project reorganization workflow without limitations.

---

## Timestamp Properties Available

### Projects

| Property | Available | Type | Notes |
|----------|-----------|------|-------|
| `creation date` | ✅ YES | date | When project was created |
| `modification date` | ✅ YES | date | Last time project was modified |
| `completion date` | ✅ YES | date or missing value | When project was completed (if completed) |
| `dropped date` | ✅ YES | date or missing value | When project was dropped (if dropped) |
| `last review date` | ✅ YES | date or missing value | Last GTD review date |
| `next review date` | ✅ YES | date or missing value | Next scheduled review |

### Tasks

| Property | Available | Type | Notes |
|----------|-----------|------|-------|
| `creation date` | ✅ YES | date | When task was created |
| `modification date` | ✅ YES | date | Last time task was modified |
| `completion date` | ✅ YES | date or missing value | When task was completed (if completed) |
| `dropped date` | ✅ YES | date or missing value | When task was dropped (if dropped) |

### ❌ What's NOT Available

- **`last activity date`** - No direct property for "last task completion in project"
  - **Workaround**: Can be computed by getting all tasks and checking their `completion date` or `modification date`
  - **Alternative**: Use `modification date` of project as proxy (gets updated when tasks change)

---

## Current vs. Desired State

### Currently Exposed in MCP Server

**Projects (`get_project`):**
- ❌ creation date
- ❌ modification date
- ❌ completion date
- ❌ dropped date
- ✅ last review date (via `lastReviewDate`)
- ✅ next review date (via `nextReviewDate`)

**Tasks (`get_task`, `get_tasks`):**
- ❌ creation date
- ❌ modification date
- ❌ completion date
- ❌ dropped date

### Should Be Added

**HIGH PRIORITY - Projects:**
1. `creationDate` - Determine project age
2. `modificationDate` - Determine last activity (proxy for staleness)
3. `completionDate` - For completed projects
4. `droppedDate` - For dropped projects

**HIGH PRIORITY - Tasks:**
1. `creationDate` - Task age
2. `modificationDate` - Last activity on task
3. `completionDate` - When task was completed (for analytics)
4. `droppedDate` - When task was dropped

---

## Other Missing Properties Discovered

### Projects - Already Have
✅ `sequential` - Added in v0.5.0
✅ `number of tasks` - Exposed as `taskCount`
✅ `number of completed tasks` - Exposed as `completedTaskCount`
✅ `number of available tasks` - Exposed as `numberOfAvailableTasks` (v0.5.0)
✅ `blocked` - Exposed
✅ `flagged` - Exposed
✅ `status` - Exposed
✅ `folder` - Exposed as `folderPath`

### Projects - Missing But Lower Priority
- `estimated minutes` - Time estimate for project
- `repetition` / `repetition rule` - Recurring projects
- `primary tag` - Main tag assigned
- `effectively completed` - Computed completion status
- `effectively dropped` - Computed dropped status
- `root task` - Reference to root task object

### Tasks - Already Have
✅ `blocked` - Exposed
✅ `flagged` - Exposed
✅ `completed` - Exposed
✅ `sequential` - Exposed
✅ `number of tasks` / `number of completed tasks` - Exposed as `subtaskCount`
✅ `number of available tasks` - Exposed as `numberOfAvailableTasks` (v0.5.0)
✅ `in inbox` - Can be determined via `get_inbox_tasks()`
✅ `parent task` - Exposed as `parentTaskId` (v0.4.0)
✅ `containing project` - Exposed as `projectId` / `projectName`

### Tasks - Missing But Lower Priority
- `estimated minutes` - Time estimate for task
- `repetition` / `repetition rule` - Recurring tasks
- `primary tag` - Main tag assigned (we don't expose tags at all currently!)
- `next` - Boolean indicating if this is the next available action
- `assigned container` - For tasks that can be in multiple places

---

## Critical Gap: Tags

🚨 **MAJOR DISCOVERY**: We don't expose tags on individual tasks!

**Currently:**
- ✅ `get_tags()` - Lists all tags in database
- ✅ `add_tag_to_task(task_id, tag_name)` - Add tag to task
- ❌ **No way to see which tags a task has**

**Should Add:**
- `tags` field to task objects (array of tag names or IDs)
- This is essential for filtering and organization

---

## Implementation Priority

### Phase 1: Critical for Project Cleanup (v0.6.0)

**Projects:**
1. ✅ Add `creationDate` to `get_project()` and `get_projects()`
2. ✅ Add `modificationDate` to both
3. ✅ Add `completionDate` to both
4. ✅ Add `droppedDate` to both

**Tasks:**
1. ✅ Add `creationDate` to `get_task()` and `get_tasks()`
2. ✅ Add `modificationDate` to both
3. ✅ Add `completionDate` to both
4. ✅ Add `droppedDate` to both
5. ✅ Add `tags` array to both

**Queries:**
1. ✅ Add parameters to `get_stalled_projects()`:
   - `days_inactive` (default: 90)
   - `min_task_count` (default: 2)
2. ✅ New: `get_projects_by_activity(modified_before="2024-01-01")`
3. ✅ New: `get_projects_by_review(not_reviewed_in_days=90)`

**Estimated Effort:** Medium (2-3 days)
- AppleScript changes straightforward (properties exist)
- JSON formatting needs updating
- Tests need updating
- Documentation needs updating

### Phase 2: Batch Operations (v0.7.0)

1. `merge_projects(source_ids, target_id)` - Combine projects
2. `split_project(project_id, task_ids, new_project_name)` - Split project
3. `archive_projects(project_ids)` - Bulk archive
4. `complete_projects(project_ids)` - Bulk complete

**Estimated Effort:** High (4-5 days)
- Complex AppleScript for moving tasks
- Transaction safety considerations
- Comprehensive testing needed

### Phase 3: Nice-to-Have (v0.8.0)

1. Add `estimatedMinutes` to projects and tasks
2. Add `repetition` / `repetitionRule` to projects and tasks
3. Add `primaryTag` to projects and tasks
4. Project similarity detection (`suggest_projects_to_merge()`)

---

## Recommendations

### Immediate Next Steps

1. ✅ **Implement Phase 1 timestamps** - Unblocks project cleanup use case
2. ✅ **Add tags to task objects** - Critical missing feature
3. ✅ **Add configurable stalled detection** - Flexibility for users
4. Create comprehensive integration tests for new properties
5. Update documentation and ROADMAP

### Architecture Considerations

**Date Handling:**
- AppleScript dates are in format: `date Monday, November 20, 2023 at 2:51:58 PM`
- Need to convert to ISO 8601 format for JSON: `2023-11-20T14:51:58`
- Handle `missing value` gracefully (convert to `null` in JSON)

**Performance:**
- Getting timestamps adds minimal overhead (part of existing object fetch)
- Computing "last activity" from task completion dates could be expensive for projects with many tasks
- Consider caching or making it optional

**Backwards Compatibility:**
- Adding fields to existing responses is backwards compatible
- MCP clients that don't know about new fields will ignore them
- Existing tools continue to work

---

## Success Criteria

After implementing Phase 1, the project cleanup use case should be fully enabled:

✅ Claude can determine project age (`creationDate`)
✅ Claude can determine staleness (`modificationDate`)
✅ Claude can determine review status (`lastReviewDate`, `nextReviewDate`)
✅ Claude can filter by inactivity (configurable `get_stalled_projects()`)
✅ Claude can see which tasks have which tags (for organization recommendations)
✅ Users can systematically review and reorganize 100+ projects with AI guidance

---

## Example Output (After Implementation)

```json
{
  "id": "bTnBpONJObS",
  "name": "Get to know OmniFocus 4",
  "creationDate": "2023-11-20T14:51:58",
  "modificationDate": "2025-10-11T10:23:12",
  "lastReviewDate": "2024-05-27T21:59:55",
  "nextReviewDate": "2024-06-03T00:00:00",
  "completionDate": null,
  "droppedDate": null,
  "taskCount": 8,
  "completedTaskCount": 0,
  "numberOfAvailableTasks": 8,
  "sequential": false,
  "blocked": true,
  "status": "active"
}
```

```json
{
  "id": "kobktzLt39Y",
  "name": "Complete first task",
  "creationDate": "2023-11-20T14:52:10",
  "modificationDate": "2025-10-11T10:23:12",
  "completionDate": null,
  "droppedDate": null,
  "tags": ["tutorial", "high-priority"],
  "blocked": false,
  "flagged": true,
  "projectId": "bTnBpONJObS",
  "projectName": "Get to know OmniFocus 4"
}
```

---

## Conclusion

The AppleScript interface provides everything we need for the project cleanup use case!

**No blockers** - All critical timestamp properties are available.

**Quick win** - Phase 1 implementation is straightforward and high-impact.

**Ready to proceed** - Can start implementation immediately.
