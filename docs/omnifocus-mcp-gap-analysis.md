# OmniFocus MCP Connector — Gap Analysis

*Produced March 11, 2026. Compared against OmniFocus 4.8.4 Reference Manual, MCP connector v0.8.3, and omnifocus-analysis.md.*

---

## 1. Confirmed Gaps (OF supports, connector doesn't expose)

Ranked by likely utility for a power user with Claude integration.

### Tier 1: High Utility — Would Improve Daily Workflows

**1.1. Planned Date (new in OF 4.7)**
- OF added `planned date` as a first-class date property alongside defer and due. It represents *when you plan to work on something* with no availability or overdue constraints.
- AppleScript exposes `planned date` (read/write), `effective planned date`, and `next planned date`.
- The connector does not read, write, or return `planned date` anywhere.
- **Impact:** Morgan's daily planning workflow (flag cleanup, contextual surfacing) would benefit from planned dates as a scheduling signal distinct from due dates. The `/plan-my-day` plugin could assign planned dates to tasks surfaced during morning planning.
- **Effort:** Medium — add to `create_task`, `update_task`, `get_tasks` return schema, and batch property extraction.

**1.2. Effective Dates (inherited values)**
- OF distinguishes between directly-assigned dates and inherited dates (from project/action group). The Inspector shows "Deferred with container", "Due with container", etc.
- AppleScript exposes `effective due date`, `effective defer date`, `effective planned date`, `effective completed date`.
- The connector reads `due date` and `defer date` directly, which returns `missing value` for tasks that inherit their dates from their project. These tasks appear to have no dates even though they functionally do.
- **Impact:** A task in a project with due date 2026-03-20 currently appears in `get_tasks()` with `dueDate: ""` unless the task has its own due date. This means overdue/due-soon queries may miss tasks that are effectively overdue via inheritance.
- **Effort:** Low — read `effective due date` and `effective defer date` alongside direct dates, or add an `include_effective_dates` flag.

**1.3. "Complete with last action" (project property)**
- OF projects can be set to auto-complete when their last action is resolved. This is a meaningful property for project status tracking — a project with this enabled and one remaining task is essentially "almost done."
- AppleScript: `completed by children` (boolean, read/write).
- The connector doesn't expose this. `create_project` and `update_project` don't accept it; `get_projects` doesn't return it.
- **Impact:** Affects how project completion should be interpreted. The SKILL.md should at minimum document this behavior.
- **Effort:** Low — add to project create/update/return.

**1.4. Single Actions List (project type)**
- OF has three project types: Parallel, Sequential, and Single Actions List. The connector only exposes `sequential` (boolean), conflating Parallel and Single Actions List.
- A Single Actions List is fundamentally different: it has no completion goal, cannot auto-complete, and represents a grab-bag of loosely related tasks (exactly the "to-dos" catch-all pattern in Morgan's database).
- AppleScript: single actions lists have `sequential = false` and are distinguished by other properties (no `completed by children` option, different class behavior). The exact AppleScript representation should be verified.
- **Impact:** The 11+ "to-dos" catch-all projects in Morgan's database are likely Single Actions Lists. Understanding and correctly creating them matters for project structure.
- **Effort:** Medium — need to verify AppleScript detection pattern, add to create/update/get.

**1.5. Stalled Projects (derived state)**
- A "stalled" project is an active project with no remaining actions. This is a key review signal — it means the project needs attention (add tasks or complete/drop it).
- OF's custom perspective engine can filter for this. AppleScript doesn't expose it directly but it's computable: active project where `number of available tasks = 0` and `number of remaining tasks = 0`.
- The connector doesn't surface this. `get_projects(include_task_health=True)` returns `remainingCount` which could be used client-side, but there's no `stalled_only` filter.
- **Impact:** The `/project-review` plugin would benefit from surfacing stalled projects automatically.
- **Effort:** Low — add a computed `stalled` field to project returns when `include_task_health=True`, or add a `stalled_only` filter.

### Tier 2: Medium Utility — Would Improve Specific Workflows

**2.1. Action Groups (documentation gap + behavior)**
- An "action group" is a task with subtasks. It can be Parallel or Sequential, and the parent task appears as "blocked" while its subtasks are active.
- The connector returns `subtaskCount` and `sequential` on tasks, so the data is there, but the concept isn't documented in the tool descriptions. An agent seeing a task with `blocked: true` and `subtaskCount: 3` has no way to know this is normal action group behavior.
- **Impact:** This confused Claude in past conversations (per the analysis doc). Documentation fix, not code.
- **Effort:** Very low — add to server instructions block.

**2.2. Repeat Rule Details**
- The connector returns `isRecurring`, `recurrence` (raw RRULE string), and `repetitionMethod`. But it doesn't parse the RRULE or expose it in a human-readable form.
- OF4 added new repeat features: "Based On" (defer/planned/due), "Catch up automatically", "End after N completions", and "Only On" specific days. These may or may not be represented in the RRULE string.
- **Impact:** An agent cannot currently tell Claude "this task repeats every Monday" — it would need to parse `FREQ=WEEKLY;INTERVAL=1;BYDAY=MO` itself.
- **Effort:** Medium — add a parsed repeat summary to task returns (e.g., `repeatSummary: "Every Monday"`). Alternatively, this is SKILL.md documentation territory.

**2.3. Folder Status (Active vs Dropped)**
- Folders can be Active or Dropped. Dropping a folder drops all contained projects.
- `get_folders()` doesn't return folder status. There's no `update_folder` to change status.
- **Impact:** Low day-to-day, but relevant for database cleanup workflows.
- **Effort:** Low.

**2.4. Tag Status: Dropped**
- Tags can be Active, On Hold, or Dropped. The connector's `update_tag` supports `active` (boolean for active/on-hold toggle) but doesn't support setting a tag to Dropped.
- **Impact:** Marginal — dropping tags is rare.
- **Effort:** Very low.

**2.5. Review: Next Review Date (read/write)**
- The connector exposes `review_interval_weeks` and `last_reviewed` on projects. But `next_review_date` is not returned or writable.
- OF calculates it as `last_reviewed + review_interval`, but it can be manually overridden to force an early review.
- AppleScript: `next review date` (read/write).
- **Impact:** Would simplify the `/project-review` plugin — currently must compute next review date client-side.
- **Effort:** Very low — add to project returns and `update_project`.

### Tier 3: Low Utility — Niche or Not Automatable

**3.1. Notifications**
- OF supports multiple notification types per item (defer, planned, latest start, due, before-due, custom).
- AppleScript has partial notification access. Writing notifications is limited.
- **Impact:** Calendar integration will handle time-based reminders. Low priority for MCP.
- **Effort:** High for limited return.

**3.2. Tag Locations / Nearby**
- Tags can have GPS locations. The Nearby perspective shows items by proximity.
- AppleScript does NOT expose tag locations. Not automatable.
- **Impact:** None — cannot be implemented.

**3.3. Custom Perspective Creation/Configuration**
- Cannot create or configure custom perspective rules via AppleScript. Can only create blank perspectives.
- Omni Automation (JavaScript) has some capability here, but crashes on test databases.
- **Impact:** Morgan already has custom perspectives configured in the UI. Read-only access (which we have) is sufficient.
- **Effort:** Not feasible.

**3.4. Attachments**
- Tasks/projects can have file attachments embedded in notes.
- AppleScript access to attachments is limited/undocumented.
- **Impact:** Low for MCP use case.

**3.5. Time Zone (Floating vs Fixed)**
- Per-item setting affecting date interpretation. `should use floating time zone` is readable via AppleScript.
- **Impact:** Edge case. Morgan operates in one time zone.
- **Effort:** Very low to read, but adds complexity.

**3.6. Mutually Exclusive Tag Groups (new in OF 4.7)**
- Tag groups can be marked so only one child tag can be assigned per item.
- AppleScript access uncertain — likely not exposed.
- **Impact:** Niche.

---

## 2. Documentation Improvements

### 2.1. Server Instructions Block

**Current gap: Action groups not explained.**
Add after the SEQUENTIAL VS PARALLEL section:
> ACTION GROUPS: A task with subtasks is an "action group." It can be parallel or sequential, just like a project. The parent task appears as `blocked: true` while its subtasks are active — this is normal behavior, not an error. Check `subtaskCount > 0` to identify action groups.

**Current gap: "Next" task semantics not explained.**
Add to the SEQUENTIAL VS PARALLEL section:
> The `next` field on a task is true when it is the first available action in a sequential project or action group. In parallel projects, all incomplete tasks have `next: true`.

**Current gap: Blocked semantics incomplete.**
The server instructions say "Blocked (waiting on predecessor in sequential project)" but don't mention that action group parents are also blocked. Add:
> A task with active subtasks (action group parent) also appears as `blocked: true` — this indicates the task itself can't be completed until its subtasks are resolved.

**Current gap: Single Actions Lists not mentioned.**
Add:
> SINGLE ACTIONS LISTS: A third project type (alongside Parallel and Sequential). Contains loosely related tasks with no completion goal — the project never auto-completes. Useful for ongoing collections like "Errands" or domain-specific catch-all lists.

### 2.2. Tool Descriptions

**`get_tasks` return schema — missing `available` field documentation.**
The return description lists `available` but doesn't explain the derivation: available = not completed AND not dropped AND not blocked AND not deferred. Add this.

**`get_projects` return schema — `sequential` ambiguity.**
Currently `sequential: true/false` but doesn't distinguish Parallel from Single Actions List (both are `false`). At minimum, document this limitation.

**`create_project` — `sequential` parameter.**
Currently: "If True, tasks must be completed in order." Should note: "If False, creates a parallel project. Single Actions Lists cannot currently be created via this API."

**`update_task` — `completed` parameter.**
Currently: "Mark task complete/incomplete." Should clarify: "Uses `mark complete` internally, which correctly handles recurring tasks by spawning the next occurrence. Setting `completed=False` uncompletes the task."

**`get_tasks` — inherited dates not mentioned.**
Add a note: "Date fields (dueDate, deferDate) show directly-assigned dates only. Tasks that inherit dates from their project/action group will show empty date fields even though they are functionally subject to those dates."

### 2.3. CLAUDE.md / Architecture Docs

**Performance section — tag_filter is now optimized.**
Update the baselines table: `get_tasks(tag_filter)` is now ~0.7s (was 120s+ timeout). This was fixed in #249.

---

## 3. Bugs Confirmed or Suspected

### 3.1. CONFIRMED: `get_perspectives` type detection (#248)
All perspectives reported as "built-in." Custom perspectives (Daily Worklist, Informatics, Nightly Review, etc.) are not distinguished. Filed as #248.

**Root cause (suspected):** Built-in perspectives in AppleScript return `missing value` for `id` and `name` properties. The type detection logic likely checks the wrong property or uses a heuristic that fails.

### 3.2. FIXED: `get_tasks(tag_filter=...)` timeout (#249)
Was timing out at 120s+ due to full table scan. Fixed by tag-side pre-filter in #249. Now ~0.7s.

### 3.3. SUSPECTED: Inherited dates not returned
Tasks inheriting due/defer dates from their project show empty date fields in `get_tasks()` results. This means:
- `get_tasks(overdue=True)` may miss tasks that are effectively overdue via project inheritance
- A task displayed as "due March 20" in the OF UI appears as `dueDate: ""` in MCP results

This should be verified against real OmniFocus to confirm whether `whose due date < (current date)` catches inherited dates or only direct ones. If `whose` respects effective dates but the property read doesn't, the filter results are correct but the returned data is misleading.

### 3.4. SUSPECTED: `get_tasks(available_only=True)` may not account for On Hold tags
OF considers a task unavailable if it has an On Hold tag. The connector's availability check computes: `not completed AND not dropped AND not blocked AND not deferred`. It's unclear whether On Hold tag status is factored in.

The `whose` clause for available tasks and the batch availability computation should be audited against OF's native Available perspective to confirm parity.

### 3.5. SUSPECTED: Uncomplete operation may fail in batch
Per APPLESCRIPT_GOTCHAS.md, `set completed of collection to false` fails with error -10006. Uncompleting must be done per-task. The connector's `update_task(completed=False)` and `update_tasks(completed=False)` should be tested to confirm they handle this correctly.

---

## Summary: Priority Recommendations

| Priority | Item | Type | Effort |
|----------|------|------|--------|
| **P1** | Planned date support | Gap | Medium |
| **P1** | Effective dates (inherited) | Gap + Bug | Low-Medium |
| **P1** | Action group documentation | Doc | Very Low |
| **P1** | "Next" task semantics | Doc | Very Low |
| **P1** | Blocked semantics (action groups) | Doc | Very Low |
| **P2** | Single Actions List project type | Gap | Medium |
| **P2** | Complete with last action | Gap | Low |
| **P2** | Stalled projects | Gap | Low |
| **P2** | Next review date | Gap | Very Low |
| **P2** | Inherited dates audit | Bug | Low |
| **P2** | Available + On Hold tags audit | Bug | Low |
| **P3** | Folder status | Gap | Low |
| **P3** | Repeat rule parsing | Gap | Medium |
| **P3** | Tag dropped status | Gap | Very Low |
| **P3** | Uncomplete batch audit | Bug | Low |
