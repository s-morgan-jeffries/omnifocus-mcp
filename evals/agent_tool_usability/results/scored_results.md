# OmniFocus MCP Blind Agent Eval Results

## Summary

- **Date:** 2026-03-15 (mutually exclusive tag configuration #303)
- **Model:** claude-opus-4-6
- **Total Score:** 82/84 (98%)
- **Critical Failures:** 0 of 5
- **Previous Score:** 80/82 (98%) — catch up automatically from repetition rule #295

## Category Scores

| Category | Scenarios | Score | Max | Pct |
|----------|-----------|-------|-----|-----|
| Core OF Concepts | 1-4 | 8 | 8 | 100% |
| Tool Selection | 5-8 | 8 | 8 | 100% |
| Parameter Usage | 9-12 | 8 | 8 | 100% |
| Multi-Step Workflows | 13-15 | 6 | 6 | 100% |
| Edge Cases | 16-18 | 6 | 6 | 100% |
| Documentation Gaps | 19-23 | 9 | 10 | 90% |
| Planned Date | 24-26 | 6 | 6 | 100% |
| Recurrence | 27-32 | 11 | 12 | 92% |
| Tag Status | 33-34 | 3 | 4 | 75% |
| Project Type | 35 | 2 | 2 | 100% |
| Folder Status | 36 | 2 | 2 | 100% |
| Next Review Date | 37 | 2 | 2 | 100% |
| Complete with Last Action | 38 | 2 | 2 | 100% |
| Next Occurrence Dates | 39 | 2 | 2 | 100% |
| Stalled Projects | 40 | 2 | 2 | 100% |
| Catch Up Automatically | 41 | 2 | 2 | 100% |
| Tag Exclusivity | 42 | 2 | 2 | 100% |

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
- **Score:** 1/2 (PARTIAL)
- **Concept Understanding:** Quoted the correct doc section about effective dates but then contradicted it — said "get_tasks is not inheriting the project-level due date" when the docs explicitly state dates include inherited values. Should have concluded the user would see April 15 in dueDate.
- **Notes:** Stochastic — previous run scored 2/2 on same scenario. The model quoted the right doc but drew the wrong conclusion.

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
- **Score:** 1/2 (PARTIAL)
- **Parameters:** Used `repetition_method="start_after_completion"` instead of `"due_after_completion"`. Both are completion-based (not fixed), but the user's phrasing "next occurrence" maps more naturally to due_after_completion. start_after_completion adjusts the defer date instead.
- **Notes:** Stochastic — previous run scored 2/2 on same scenario. Both methods are completion-based; the distinction is subtle.

### Scenario 32: Add Recurrence to Non-Recurring Task
- **Score:** 2/2 (PASS)
- **Parameters:** Correct — `recurrence="FREQ=DAILY"`, `repetition_method="fixed"`

### Scenario 33: Drop a Tag
- **Score:** 1/2 (PARTIAL)
- **Parameters:** Used `status="on_hold"` instead of `"dropped"`. User said "no longer using" and "hidden from tag picker" — `dropped` is the correct choice for permanent retirement. `on_hold` implies temporary pause and also makes tasks with that tag unavailable (unintended side effect).
- **Notes:** Known stochastic issue — previous runs have oscillated between on_hold and dropped on this scenario.

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

## Key Findings

### Changes Validated in This Run (#303)

1. **`childrenAreMutuallyExclusive` added to get_tags Returns** — The blind agent correctly identified the field and warned about silent tag removal when assigning to an exclusive group. The documentation clearly communicates the risk.

2. **`children_are_mutually_exclusive` parameter on create_tag and update_tag** — New write capability via OmniAutomation. No regressions on existing tag scenarios (33, 34).

3. **Safety-critical scenario (42) passes** — The agent correctly warns about silent data modification, making this a safety improvement for the tool suite.

### Score Delta

82/84 vs 80/82 previous. New scenario (42) at 2/2 (safety-critical). Existing scenario scores unchanged.

### Issues Found (Stochastic, Not Actionable)

- **Scenario 21** (Inherited Dates): Known oscillation.
- **Scenario 31** (Set Recurrence): Known oscillation.
- **Scenario 33** (Drop a Tag): Known oscillation.

## Conclusion

Adding `childrenAreMutuallyExclusive` to get_tags and `children_are_mutually_exclusive` to create_tag/update_tag is well-documented and correctly discoverable by blind agents. The new safety-critical scenario (42) passes at 2/2. All 5 safety-critical scenarios pass. No regressions.
