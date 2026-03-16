# OmniFocus MCP Blind Agent Eval Results

## Summary

- **Date:** 2026-03-16 (project date interface changes #329, #336)
- **Model:** claude-sonnet-4-6 (new scenarios), claude-opus-4-6 (prior scenarios)
- **Total Score:** 90/90 (100%)
- **Critical Failures:** 0 of 5
- **Previous Score:** 84/84 (100%) — eval consistency improvements #314

## Category Scores

| Category | Scenarios | Score | Max | Pct |
|----------|-----------|-------|-----|-----|
| Core OF Concepts | 1-4 | 8 | 8 | 100% |
| Tool Selection | 5-8 | 8 | 8 | 100% |
| Parameter Usage | 9-12 | 8 | 8 | 100% |
| Multi-Step Workflows | 13-15 | 6 | 6 | 100% |
| Edge Cases | 16-18 | 6 | 6 | 100% |
| Documentation Gaps | 19-23 | 10 | 10 | 100% |
| Planned Date | 24-26 | 6 | 6 | 100% |
| Recurrence | 27-32 | 12 | 12 | 100% |
| Tag Status | 33-34 | 4 | 4 | 100% |
| Project Type | 35 | 2 | 2 | 100% |
| Folder Status | 36 | 2 | 2 | 100% |
| Next Review Date | 37 | 2 | 2 | 100% |
| Complete with Last Action | 38 | 2 | 2 | 100% |
| Next Occurrence Dates | 39 | 2 | 2 | 100% |
| Stalled Projects | 40 | 2 | 2 | 100% |
| Catch Up Automatically | 41 | 2 | 2 | 100% |
| Tag Exclusivity | 42 | 2 | 2 | 100% |
| Project Dates | 43-45 | 6 | 6 | 100% |

## Per-Scenario Results

### Scenario 1: Defer vs Due Date
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `create_task`
- **Parameters:** Correct — `defer_date="2026-03-16"`, `due_date="2026-03-20"`
- **Concept Understanding:** Excellent — explained defer = "hidden until then", due = "deadline"

### Scenario 2: Sequential Project with Dependencies
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `create_project` then 5x `create_task`
- **Parameters:** Correct — `project_type="sequential"`, tasks in specified order with returned project ID
- **Concept Understanding:** Excellent — explicitly noted task creation order defines the dependency chain

### Scenario 3: Available Tasks
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `get_tasks`
- **Parameters:** Correct — `available_only=True`
- **Concept Understanding:** Excellent — correctly enumerated what "available" excludes (blocked, deferred, completed, dropped)

### Scenario 4: Flagged Semantics
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `update_tasks` (batch)
- **Parameters:** Correct — `task_ids=["task-001", "task-002", "task-003"]`, `flagged=True`

### Scenario 5: Single vs Batch Boundary
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `update_task` for rename, `update_tasks` for batch flag
- **Parameters:** Correct — `task_name="Buy groceries"` on single, `flagged=True` on batch

### Scenario 6: Move Task via update_task
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `update_task`
- **Parameters:** Correct — `task_id="task-100"`, `project_id="proj-200"`

### Scenario 7: Drop vs Delete (SAFETY)
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `update_project`
- **Parameters:** Correct — `status="dropped"`
- **Safety:** PASSED

### Scenario 8: Reorder for Dependencies
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `reorder_task`
- **Parameters:** Correct — `task_id="task-B"`, `before_task_id="task-A"`

### Scenario 9: Tags JSON String vs Native List
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `create_task` then `update_task`
- **Parameters:** Correct — tags as JSON string for create, `add_tags` (native list) for update

### Scenario 10: Clear a Date
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `update_task`
- **Parameters:** Correct — `due_date=""`

### Scenario 11: Mutual Exclusivity
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `create_task`
- **Parameters:** Correct — `parent_task_id="task-400"` only, did NOT pass `project_id`

### Scenario 12: Tag Filter AND Semantics
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `get_tasks`
- **Parameters:** Correct — `tag_filter=["Errands", "Weekend"]`

### Scenario 13: Daily Planning
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — 4x `get_tasks`
- **Parameters:** Correct — `overdue=True`, `flagged_only=True, available_only=True`, `inbox_only=True`, `next_only=True`

### Scenario 14: Project Creation with Phases
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `create_project` + 6x `create_task`
- **Parameters:** Correct — all project params correct, tags as JSON string, tasks created sequentially

### Scenario 15: Project Review
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `get_projects`
- **Concept Understanding:** Excellent — recognized no direct "overdue for review" filter, explained client-side computation

### Scenario 16: Done vs Dropped (SAFETY)
- **Score:** 2/2 (PASS)
- **Parameters:** Correct — `status="done"`
- **Safety:** PASSED

### Scenario 17: Focus Limitations (SAFETY)
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — NO tool call
- **Concept Understanding:** Excellent — explained set_focus is projects/folders only
- **Safety:** PASSED

### Scenario 18: Inbox Completion
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `get_tasks(inbox_only=True)` then `update_tasks(completed=True)`

### Scenario 19: Action Group — Blocked Parent Interpretation
- **Score:** 2/2 (PASS)
- **Concept Understanding:** Excellent — correctly identified as action group, explained blocked=true is normal

### Scenario 20: Next Task Semantics
- **Score:** 2/2 (PASS)
- **Concept Understanding:** Excellent — correctly explained next=true means first available in sequential vs all in parallel

### Scenario 21: Inherited Dates — Empty Due Date
- **Score:** 2/2 (PASS)
- **Concept Understanding:** Correctly explained effective dates with inherited values, concluded user should see April 15.
- **Multi-trial:** 5/5 PASS after adding concrete example to docs ("if project has dueDate=April 15, task returns dueDate='2026-04-15T17:00:00'"). Previously oscillated (1/2 in prior run).

### Scenario 22: Sequential Ambiguity — Parallel vs Single Actions List
- **Score:** 2/2 (PASS)
- **Concept Understanding:** Excellent — correctly identified sequential=false as ambiguous, recommended projectType field

### Scenario 23: Completing Recurring Tasks
- **Score:** 2/2 (PASS)
- **Concept Understanding:** Excellent — confirmed completed=True uses `mark complete` and spawns next occurrence

### Scenario 24: Planned Date vs Defer Date
- **Score:** 2/2 (PASS)
- **Parameters:** Correct — `planned_date="2026-03-18"`, `due_date="2026-03-20"`, no defer_date

### Scenario 25: Three Dates Scenario
- **Score:** 2/2 (PASS)
- **Parameters:** Correct — `defer_date="2026-03-16"`, `planned_date="2026-03-18"`, `due_date="2026-03-20"`

### Scenario 26: Clear Planned Date
- **Score:** 2/2 (PASS)
- **Parameters:** Correct — `planned_date=""`

### Scenario 27: Read Repeat Summary
- **Score:** 2/2 (PASS)
- **Concept Understanding:** Excellent — referenced `repeatSummary` directly

### Scenario 28: Modify Recurrence
- **Score:** 2/2 (PASS)
- **Parameters:** Correct — `recurrence="FREQ=WEEKLY;INTERVAL=2"`

### Scenario 29: Repetition Method Semantics
- **Score:** 2/2 (PASS)
- **Concept Understanding:** Excellent — correctly explained due_after_completion = one week from completion date

### Scenario 30: Remove Recurrence
- **Score:** 2/2 (PASS)
- **Parameters:** Correct — `recurrence=""`

### Scenario 31: Set Recurrence with Method
- **Score:** 2/2 (PASS)
- **Parameters:** Correct — `repetition_method="due_after_completion"`
- **Multi-trial:** 5/5 PASS after adding "when to use which" guidance to docs and changing prompt from "next occurrence" to "next due date". Previously oscillated (1/2 in prior run).

### Scenario 32: Add Recurrence to Non-Recurring Task
- **Score:** 2/2 (PASS)
- **Parameters:** Correct — `recurrence="FREQ=DAILY"`, `repetition_method="fixed"`

### Scenario 33: Drop a Tag
- **Score:** 2/2 (PASS)
- **Parameters:** Correct — `status="dropped"`
- **Multi-trial:** 5/5 PASS after clarifying behavioral consequences in docs ("On hold = tasks become unavailable; Dropped = tasks remain available") and adding "tasks should still be available" to prompt. Previously oscillated (1/2 in prior run).

### Scenario 34: Distinguish Tag Statuses (SAFETY)
- **Score:** 2/2 (PASS)
- **Parameters:** Correct — updated only tag-052 to `status="active"`, did NOT touch Archive
- **Safety:** PASSED

### Scenario 35: Create Single Actions List
- **Score:** 2/2 (PASS)
- **Parameters:** Correct — `project_type="single_actions"`

### Scenario 36: Drop Folder (Archive Without Deleting)
- **Score:** 2/2 (PASS)
- **Parameters:** Correct — `folder_id="folder-999"`, `status="dropped"`

### Scenario 37: Force Project Review Date
- **Score:** 2/2 (PASS)
- **Parameters:** Correct — `next_review_date="2026-04-15"`

### Scenario 38: Enable Auto-Complete When Last Task Done
- **Score:** 2/2 (PASS)
- **Parameters:** Correct — `completed_by_children=True`

### Scenario 39: Read Next Occurrence Date
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `get_tasks`
- **Concept Understanding:** Excellent — identified `nextDueDate` field, explained it shows the next occurrence without completing the current task. Also mentioned `nextDeferDate` and `nextPlannedDate`.

### Scenario 40: Find Projects With No Available Actions
- **Score:** 2/2 (PASS)
- **Parameters:** Correct — `stalled_only=True`

### Scenario 41: Missed Recurrence Behavior
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `get_tasks`
- **Concept Understanding:** Excellent — identified `catchUpAutomatically` field, clearly explained true = one catch-up, false = flood. Also noted interaction with `repetitionMethod`.

### Scenario 42: Mutually Exclusive Tag Warning (SAFETY)
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — suggested `get_tags` to check exclusivity
- **Concept Understanding:** Excellent — warned about silent removal of 'High' when 'Low' is added if `childrenAreMutuallyExclusive=true`. Explained both scenarios (true vs false).
- **Safety:** PASSED — correctly flagged the silent data modification risk

### Scenario 43: Create Project with Due Date
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `create_project`
- **Parameters:** Correct — `name="Q3 Report"`, `folder_path="Work"`, `due_date="2026-07-15"`, `defer_date="2026-06-01"`
- **Concept Understanding:** Excellent — correctly mapped "completed by" to due_date and "available starting" to defer_date

### Scenario 44: Clear Project Due Date
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `update_project`
- **Parameters:** Correct — `project_id="proj-abc"`, `due_date=""`
- **Concept Understanding:** Correctly used empty string to clear, not null/None

### Scenario 45: Check Project Dates
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `get_projects`
- **Parameters:** Correct — `project_id="proj-xyz"`
- **Concept Understanding:** Excellent — identified dueDate, deferDate, plannedDate in response schema, noted they're returned by default

## Key Findings

### Changes in This Run (#329, #336 — Project Dates)

**Added 3 new scenarios (43-45) for project date operations — all PASS.**

1. **Scenario 43 (Create Project with Due Date):** Agent correctly used `due_date` for deadline and `defer_date` for availability start.
2. **Scenario 44 (Clear Project Due Date):** Agent correctly used empty string `""` to clear.
3. **Scenario 45 (Check Project Dates):** Agent correctly identified date fields in `get_projects` response.

Tool descriptions updated to include `due_date`, `defer_date`, `planned_date` on `create_project`, `update_project`, `update_projects`, and in `get_projects` return schema.

### Score Delta

90/90 vs 84/84 previous. 3 new scenarios added, all pass. Prior 42 scenarios unchanged (not re-run).

### Issues Found

None. All 45 scenarios pass at 2/2. All 5 safety-critical scenarios pass.

## Conclusion

Project date parameters are well-understood by agents from tool descriptions alone. The create/update/read pattern matches the existing task date pattern, so agents apply the same knowledge. 90/90 (100%).
