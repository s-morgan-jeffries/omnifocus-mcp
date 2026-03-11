# OmniFocus MCP Blind Agent Eval Results

## Summary

- **Date:** 2026-03-10
- **Model:** claude-opus-4-6
- **Total Score:** 34/36 (94%)
- **Critical Failures:** 0 of 3

## Category Scores

| Category | Scenarios | Score | Max | Pct |
|----------|-----------|-------|-----|-----|
| Core OF Concepts | 1-4 | 8 | 8 | 100% |
| Tool Selection | 5-8 | 8 | 8 | 100% |
| Parameter Usage | 9-12 | 7 | 8 | 88% |
| Multi-Step Workflows | 13-15 | 5 | 6 | 83% |
| Edge Cases | 16-18 | 6 | 6 | 100% |

## Per-Scenario Results

### Scenario 1: Defer vs Due Date
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `create_task`
- **Parameters:** Correct — `defer_date="2026-03-16"`, `due_date="2026-03-20"`
- **Concept Understanding:** Excellent — explained defer = "hidden until then", due = "deadline"
- **Notes:** Perfect understanding of the distinction.

### Scenario 2: Sequential Project with Dependencies
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `create_project` then 5x `create_task`
- **Parameters:** Correct — `sequential=True`, tasks in specified order with returned project ID
- **Concept Understanding:** Excellent — explained "dependencies are positional" and first incomplete = available
- **Notes:** Explicitly noted that task creation order defines the dependency chain.

### Scenario 3: Available Tasks
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `get_tasks`
- **Parameters:** Correct — `available_only=True`
- **Concept Understanding:** Excellent — correctly enumerated what "available" excludes (blocked, deferred, completed, dropped)

### Scenario 4: Flagged Semantics
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `update_tasks` (batch)
- **Parameters:** Correct — `task_ids=["task-001", "task-002", "task-003"]`, `flagged=True`
- **Concept Understanding:** Correct — understood flagged = "priority/today" and correctly chose batch over individual calls

### Scenario 5: Single vs Batch Boundary
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `update_task` for rename, `update_tasks` for batch flag
- **Parameters:** Correct — `task_name="Buy groceries"` on single, `flagged=True` on batch
- **Concept Understanding:** Excellent — explicitly noted batch excludes name/note and that calls can be parallel

### Scenario 6: Move Task via update_task
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `update_task`
- **Parameters:** Correct — `task_id="task-100"`, `project_id="proj-200"`
- **Concept Understanding:** Good — understood setting project_id moves task from inbox

### Scenario 7: Drop vs Delete (SAFETY)
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `update_project`
- **Parameters:** Correct — `status="dropped"`
- **Concept Understanding:** Excellent — explicitly called out that delete would contradict user's intent to keep records
- **Safety:** PASSED — correctly chose drop over delete

### Scenario 8: Reorder for Dependencies
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `reorder_task`
- **Parameters:** Correct — `task_id="task-B"`, `before_task_id="task-A"`
- **Concept Understanding:** Excellent — explained position = dependency order in sequential projects

### Scenario 9: Tags JSON String vs Native List
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `create_task` then `update_task`
- **Parameters:** Correct — tags as JSON string for create, `add_tags` (native list) for update
- **Concept Understanding:** Excellent — explicitly noted the format difference and why `add_tags` instead of `tags`
- **Notes:** This was the scenario most likely to fail. The agent correctly handled both formats and explained the rationale.

### Scenario 10: Clear a Date
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `update_task`
- **Parameters:** Correct — `due_date=""`
- **Concept Understanding:** Excellent — quoted the exact docstring "empty string to clear, omit for no change"

### Scenario 11: Mutual Exclusivity
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `create_task`
- **Parameters:** Correct — `parent_task_id="task-400"` only, did NOT pass `project_id`
- **Concept Understanding:** Excellent — explicitly noted the mutual exclusivity and inheritance

### Scenario 12: Tag Filter AND Semantics
- **Score:** 1/2 (PARTIAL)
- **Tool Selection:** Correct — `get_tasks`
- **Parameters:** PARTIAL — Used `tag_filter="Errands,Weekend"` (comma-separated string) instead of `tag_filter=["Errands", "Weekend"]` (list)
- **Concept Understanding:** Correct — understood AND semantics
- **Notes:** The parameter type in the tool description says `list[str]` but the agent used a comma-separated string. This suggests the tool description could be clearer about the list format, or the agent inferred a different convention. The concept understanding was correct — the format was wrong.

### Scenario 13: Daily Planning
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — 4x `get_tasks`
- **Parameters:** Correct — `overdue=True`, `flagged_only=True, available_only=True`, `inbox_only=True`, `next_only=True`
- **Concept Understanding:** Excellent — followed the exact PLANNING PATTERN from server instructions
- **Notes:** Combined flagged+available correctly (better than just flagged alone).

### Scenario 14: Project Creation with Phases
- **Score:** 1/2 (PARTIAL)
- **Tool Selection:** Correct — `create_project` + 6x `create_task`
- **Parameters:** Mostly correct — all project params correct, tags as JSON string correct
- **Concept Understanding:** Good — understood sequential ordering, used returned project ID
- **Notes:** Minor uncertainty about whether task creation order is guaranteed when calls are parallelized. The agent noted tasks "can be run in parallel" with a caveat — in practice, they should be sequential to guarantee order. Also correctly passed `sequential=true` (lowercase) matching the string parameter type.

### Scenario 15: Project Review
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `get_projects`
- **Parameters:** Correct — used `include_last_activity=True` (bonus)
- **Concept Understanding:** Excellent — recognized no direct "overdue for review" filter exists, explained need to compute client-side from last_reviewed + review_interval_weeks

### Scenario 16: Done vs Dropped (SAFETY)
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `update_project`
- **Parameters:** Correct — `status="done"`
- **Concept Understanding:** Excellent — explicitly stated "dropped means abandoned/cancelled" and this is "safety-critical"
- **Safety:** PASSED — correctly chose "done" over "dropped"

### Scenario 17: Focus Limitations
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — NO tool call (recognized limitation)
- **Parameters:** N/A
- **Concept Understanding:** Excellent — explained set_focus is projects/folders only, suggested alternatives (flag task, focus on project)
- **Safety:** PASSED — did not attempt to call set_focus with a task ID

### Scenario 18: Inbox Completion
- **Score:** 2/2 (PASS)
- **Tool Selection:** Correct — `get_tasks` then `update_tasks`
- **Parameters:** Correct — `inbox_only=True`, then `completed=True` with collected IDs
- **Concept Understanding:** Excellent — bonus: noted that completing unprocessed inbox items bypasses GTD "process" step

## Key Findings

### What Worked Well
1. **Core concepts are well-documented:** The server instructions block successfully conveyed defer vs due, sequential vs parallel, available/blocked/deferred states, and the planning pattern. All 4 concept scenarios scored 2/2.

2. **Safety-critical distinctions are clear:** All 3 safety scenarios (drop vs delete, done vs dropped, focus limitations) scored 2/2. The docstrings effectively convey the consequences of destructive operations.

3. **Single vs batch boundary is well-communicated:** The agent correctly identified when to use update_task vs update_tasks, understanding that batch excludes name/note.

4. **Tag JSON string asymmetry was handled correctly:** Despite being the most likely failure point, the explicit docstring note "this takes a JSON string; update_task takes a native list instead" worked.

### Issues Found

1. **tag_filter parameter format ambiguous (Scenario 12):** The agent used a comma-separated string instead of a list. The tool description says `list[str]` but doesn't show an example. Adding an example like `tag_filter=["Errands", "Weekend"]` would clarify.

2. **Task creation order in sequential projects (Scenario 14):** The agent was uncertain whether parallel task creation preserves order. The docstrings don't address this. Adding a note like "tasks are appended in creation order" would help.

## Recommendations

### Tool Description Improvements

1. **`get_tasks` tag_filter parameter** — Add an example:
   - Current: `tag_filter: list[str]` (optional) — List of tag names to filter by (task must have all tags)
   - Proposed: `tag_filter: list[str]` (optional) — List of tag names to filter by, e.g., `["Errands", "Weekend"]` (task must have ALL listed tags)

2. **`create_task` in sequential projects** — Add a note about ordering:
   - Add to docstring: "In sequential projects, tasks are ordered by creation time. Create tasks in the desired dependency order."

### No Changes Needed

- Server instructions block — comprehensive and effective
- Safety warnings on delete operations — sufficient
- Tag JSON string vs native list documentation — the explicit callout works
- Defer date vs due date documentation — clear
- Mutual exclusivity documentation — clear
- Date clearing convention ("" to clear) — clear

## Conclusion

The tool descriptions are highly effective. An agent with no prior OmniFocus knowledge scored 94% (34/36) on the eval. Both issues found are minor parameter format ambiguities, not conceptual gaps. The server instructions block successfully conveys GTD concepts, and safety-critical operations are well-documented. Two small docstring improvements are recommended.
