# OmniFocus MCP Connector — Gap Analysis

*Produced March 11, 2026. Updated March 18, 2026 post-v0.10.1. Compared against OmniFocus 4.8.4 Reference Manual, MCP connector v0.10.1, and OmniFocus SDEF.*

---

## 1. Confirmed Gaps (OF supports, connector doesn't expose)

Ranked by likely utility for a power user with Claude integration.

### Tier 1: High Utility — Would Improve Daily Workflows

**1.1. Planned Date (new in OF 4.7)** ✅ IMPLEMENTED in v0.9.0 (#254)
- Added `planned_date` to `create_task`, `update_task`, and `get_tasks` return schema.
- `effective planned date` read path also implemented in v0.9.0 (#253).

**1.2. Effective Dates (inherited values)** ✅ IMPLEMENTED in v0.9.0 (#253)
- Connector now reads `effective due date`, `effective defer date`, `effective planned date` throughout — both in `whose` clauses and batch/per-task property reads.
- Tasks inheriting dates from their project now correctly surface those dates.

**1.3. "Complete with last action" (project property)** ✅ IMPLEMENTED in v0.9.0 (#256)
- `completed_by_children` added to `create_project`, `update_project`, `get_projects`.

**1.4. Single Actions List (project type)** ✅ IMPLEMENTED in v0.9.0 (#255)
- `project_type` field added, with values `"parallel"`, `"sequential"`, `"single_actions"`.
- Create and update support all three types.

**1.5. Stalled Projects (derived state)** ✅ IMPLEMENTED in v0.9.0 (#287)
- `stalled_only` filter added to `get_projects`.
- `stalled` boolean field returned for all projects when `include_task_health=True`.

### Tier 2: Medium Utility — Would Improve Specific Workflows

**2.1. Action Groups (documentation gap + behavior)**
- Still a documentation gap. `subtaskCount` and `sequential` are returned on tasks, but the action group concept isn't explained in tool descriptions.
- **Impact:** An agent seeing `blocked: true` with `subtaskCount: 3` has no context that this is normal action group behavior.
- **Effort:** Very low — add to server instructions block.

**2.2. Repeat Rule Details** ✅ FULLY IMPLEMENTED
- Connector returns `isRecurring`, `recurrence` (raw RRULE string), `repetitionMethod`, `repeatSummary` (human-readable), and `catchUpAutomatically`.
- `repeatSummary` closes the human-readability gap. `catchUpAutomatically` added in v0.9.1 (see §4.2).
- **Status:** Fully addressed.

**2.3. Folder Status (Active vs Dropped)** ✅ IMPLEMENTED in v0.9.0 (#258)
- `status` field (active/dropped) added to `get_folders`. `update_folder` supports status changes.

**2.4. Tag Status: Dropped** ✅ IMPLEMENTED in v0.9.0 (#259)
- `update_tag(status="dropped")` now supported.

**2.5. Review: Next Review Date (read/write)** ✅ IMPLEMENTED in v0.9.0 (#257)
- `next_review_date` added to `update_project` and `get_projects` return schema.

### Tier 3: Low Utility — Niche or Not Automatable

**3.1. Notifications**
- OF supports multiple notification types per item (defer, planned, latest start, due, before-due, custom).
- AppleScript has partial notification access. Writing notifications is limited.
- **Impact:** Calendar integration will handle time-based reminders. Low priority for MCP.
- **Effort:** High for limited return.

**3.2. Tag Locations / Nearby**
- Tags can have GPS locations. The Nearby perspective shows items by proximity.
- **Correction from original doc:** The OmniFocus SDEF *does* expose a `location` property on tags (`latitude`, `longitude`, `altitude`, `radius`, `trigger`). Prior assessment that AppleScript doesn't expose this was incorrect.
- **Revised assessment:** Reading/writing tag locations via AppleScript is technically feasible. However, the use case for MCP (Claude assigning GPS-based contexts to tags) is niche enough to remain Tier 3.
- **Effort:** Low — but no clear workflow benefit identified.

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
- See §4.3 for updated assessment.

**3.6. Mutually Exclusive Tag Groups (new in OF 4.7)**
- Tag groups can be marked so only one child tag from the group can be assigned per item.
- **SDEF research finding:** The `mutually exclusive` *configuration* is NOT in the OmniFocus SDEF — it cannot be created or read via AppleScript.
- **OmniAutomation finding (2026-03-14):** The property `Tag.childrenAreMutuallyExclusive` IS readable and writable via `evaluate javascript`. This means the connector can detect and configure exclusivity through OmniAutomation, even though AppleScript/SDEF cannot.
- **Enforcement finding (2026-03-14):** OmniFocus enforces exclusivity at the **data model level**, not just the UI. Adding a second tag from an exclusive group via AppleScript silently removes the first — only the last-assigned tag survives. This is OmniFocus behavior, not controllable by the connector.
- **Impact:** The connector currently cannot warn about silent tag removal because it doesn't read `childrenAreMutuallyExclusive`. Future enhancement: expose this property in `get_tags` and optionally in `create_tag`/`update_tag`.

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

**Current gap: Single Actions Lists not mentioned.** ✅ IMPLEMENTED in v0.9.0 (#255)
Added to server instructions as part of project type support.

### 2.2. Tool Descriptions

**`get_tasks` return schema — missing `available` field documentation.**
The return description lists `available` but doesn't explain the derivation: available = not completed AND not dropped AND not blocked AND not deferred. Add this.

**`get_projects` return schema — `sequential` ambiguity.** ✅ RESOLVED in v0.9.0 (#255)
`project_type` field now returns `"parallel"`, `"sequential"`, or `"single_actions"` explicitly.

**`create_project` — `sequential` parameter.** ✅ RESOLVED in v0.9.0 (#255)
Replaced by `project_type` parameter.

**`update_task` — `completed` parameter.**
Currently: "Mark task complete/incomplete." Should clarify: "Uses `mark complete` internally, which correctly handles recurring tasks by spawning the next occurrence. Setting `completed=False` uncompletes the task."

**`get_tasks` — inherited dates.** ✅ RESOLVED in v0.9.0 (#253)
Now returns effective dates, including inherited ones. Docstring updated.

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

### 3.3. FIXED: Inherited dates not returned (#253) ✅ RESOLVED in v0.9.0
Connector now reads `effective due date`, `effective defer date`, `effective planned date`. Tasks inheriting dates from their project/action group now surface those dates correctly.

### 3.4. SUSPECTED: `get_tasks(available_only=True)` may not account for On Hold tags
OF considers a task unavailable if it has an On Hold tag. The connector's availability check computes: `not completed AND not dropped AND not blocked AND not deferred`. It's unclear whether On Hold tag status is factored in.

The `whose` clause for available tasks and the batch availability computation should be audited against OF's native Available perspective to confirm parity.

### 3.5. SUSPECTED: Uncomplete operation may fail in batch
Per APPLESCRIPT_GOTCHAS.md, `set completed of collection to false` fails with error -10006. Uncompleting must be done per-task. The connector's `update_task(completed=False)` and `update_tasks(completed=False)` should be tested to confirm they handle this correctly.

---

## 4. New Gaps Found via SDEF Research (March 13, 2026)

These items were not in the original gap analysis. Discovered by reading the OmniFocus SDEF directly.

### 4.1. Next Occurrence Dates on Recurring Tasks ✅ IMPLEMENTED

The SDEF exposes three read-only properties on tasks:
- `next defer date` — defer date of the next occurrence (recurring tasks)
- `next due date` — due date of the next occurrence
- `next planned date` — planned date of the next occurrence

These return `missing value` for non-recurring tasks. For recurring tasks, they allow an agent to reason about *when the next instance will become relevant* without completing the current one.

- **Implemented:** `nextDueDate`, `nextDeferDate`, `nextPlannedDate` added to batch property extraction and `get_tasks` return schema.
- **Status:** Fully addressed.

### 4.2. `catch up automatically` in Repetition Rule ✅ IMPLEMENTED

The `repetition rule` record in the SDEF includes a `catch up automatically` boolean property. When `true`, if a task with recurrence is missed, only one catch-up occurrence is scheduled (not one per missed interval). When `false`, each missed occurrence is scheduled individually.

- **Implemented:** `catchUpAutomatically` extracted from the repetition rule and included in `get_tasks` return schema.
- **Status:** Fully addressed.

### 4.3. `should use floating time zone`

Tasks and projects have a `should use floating time zone` boolean property. When `true`, due dates are interpreted in "local time" regardless of time zone — useful for travelers who want "9am wherever I am" rather than "9am UTC-5."

- **Current state:** Not read or returned anywhere.
- **Impact:** Edge case for Morgan's current workflows (single time zone), but could cause confusing behavior if tasks were created with floating time zone in another app.
- **Effort:** Very low — add to get_tasks/get_projects return schema as read-only.
- **Priority:** Low. Could be Tier 3 / won't-fix.
- **Filed:** No issue needed unless prioritized.

---

## 5. New Gaps Found via Metadata Audit (March 18, 2026)

These items were identified during the v0.10.2 metadata audit (#376).

### 5.1. Display Bug: Task Dates Not Shown (#377)

The connector fetches `creationDate`, `modificationDate`, `completionDate`, and `droppedDate` for tasks, but `_format_task` in `server_fastmcp.py` does not include them in the output. Agents never see these dates on tasks.

Additionally, `_format_project` only displays `creationDate` — `modificationDate`, `completionDate`, and `droppedDate` are fetched but not displayed for projects either.

- **Impact:** Agents cannot reason about when tasks/projects were created, last modified, completed, or dropped.
- **Effort:** Very low — add conditional output lines to `_format_task` and `_format_project`.
- **Filed:** #377 (v0.10.2)

### 5.2. `in_inbox` Boolean on Tasks (#378)

The SDEF exposes `in inbox` (boolean) on tasks. Currently, inbox membership must be inferred from `projectName: "N/A"` or by using `get_tasks(source="inbox")`.

- **Impact:** Low-medium. An explicit boolean is unambiguous and useful for agents triaging tasks.
- **Effort:** Very low — one additional batch property read.
- **Filed:** #378 (v0.10.2, read-only)

### 5.3. `completed_by_children` on Tasks (#379)

`completed_by_children` is supported on projects (create, update, get) but not on tasks. Tasks with subtasks (action groups) also support this property — when true, completing all subtasks auto-completes the parent.

- **Impact:** Medium. Agents managing action groups can't see or control this behavior.
- **Effort:** Low — mirror existing project implementation for tasks.
- **Filed:** #379 (v0.10.2, read/write)

### 5.4. `primary_tag` on Tasks — Deferred

The SDEF exposes `primary tag` (the first tag in a task's tag list). Since we already return the full `tags` array, this is redundant with `tags[0]`.

- **Decision:** Skip. No issue filed.

### 5.5. Mutually Exclusive Tag Configuration (#303)

`Tag.childrenAreMutuallyExclusive` is readable/writable via OmniAutomation. Research completed in #302. Implementation designed in #303, previously blocked on #274 (production test infrastructure), now unblocked.

- **Filed:** #303 (v0.10.2, read/write via OmniAutomation)

---

## Summary: Priority Recommendations (updated March 18, 2026)

### Implemented

| Item | Type | Version |
|------|------|---------|
| Planned date support | Gap | ✅ v0.9.0 |
| Effective dates (inherited) | Gap + Bug | ✅ v0.9.0 |
| Single Actions List project type | Gap | ✅ v0.9.0 |
| Complete with last action (projects) | Gap | ✅ v0.9.0 |
| Stalled projects | Gap | ✅ v0.9.0 |
| Next review date | Gap | ✅ v0.9.0 |
| Inherited dates audit | Bug | ✅ v0.9.0 |
| Folder status | Gap | ✅ v0.9.0 |
| Tag dropped status | Gap | ✅ v0.9.0 |
| Next occurrence dates | Gap | ✅ v0.9.1 |
| `catch up automatically` | Gap | ✅ v0.9.1 |
| Repeat rule details (full) | Gap | ✅ v0.9.1 |

### Open — Filed for v0.10.2

| Priority | Item | Type | Effort | Issue |
|----------|------|------|--------|-------|
| **P1** | Task/project date display bug | Bug | Very Low | #377 |
| **P2** | `in_inbox` boolean on tasks | Gap | Very Low | #378 |
| **P2** | `completed_by_children` on tasks | Gap | Low | #379 |
| **P2** | Mutually exclusive tag configuration | Gap | Medium | #303 |

### Open — Unfiled / Deferred

| Priority | Item | Type | Effort | Notes |
|----------|------|------|--------|-------|
| **P1** | Action group documentation | Doc | Very Low | Tool description improvement |
| **P1** | "Next" task semantics | Doc | Very Low | Tool description improvement |
| **P1** | Blocked semantics (action groups) | Doc | Very Low | Tool description improvement |
| **P2** | Available + On Hold tags audit | Bug | Low | May affect `available_only` accuracy |
| **P3** | Uncomplete batch audit | Bug | Low | `set completed to false` may fail in batch |
| **P3** | Tag locations | Gap | Low | Feasible but low-value |
| **P3** | `should use floating time zone` | Gap | Very Low | Edge case |
| **Skip** | `primary_tag` on tasks | Gap | Very Low | Redundant with `tags[0]` |
