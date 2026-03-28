# Changelog

All notable changes to the OmniFocus MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.13.1] - 2026-03-28

Tool description overhaul — trimmed by 67% after blind eval research showed descriptions were 10x the MCP community norm. Adversarial API critic review identified and fixed four description gaps.

### Changed

- **Server instructions and tool docstrings trimmed by 67%** — 29K → 10K chars (#550, #552)
  - Server instructions: 3,580 → 1,400 chars (cut BATCH OPERATIONS, PLANNING PATTERN, INBOX, REVIEW)
  - Tool docstrings: avg 900 → 355 chars (let parameter names/types self-document)
  - Blind eval: trimmed version scores 98.6% vs 100% original on Claude

- **Strengthened effective dates language** to prevent agent hedging (#556, #561)
  - "include" → "always effective (inherited)", "WILL show", "not a bug"

- **Documented all three tag statuses** with availability effects (#557, #561)
  - Active (normal), On Hold (excludes from Available), Dropped (hidden, no availability effect)

- **Annotated `stalled_only` parameter** — was the only undescribed boolean filter (#555, #560)

- **Enumerated task `status` valid values** — was bare `status: str` (#558, #561)

- **Added drop+recurrence warning** — dropping without clearing recurrence spawns next occurrence (#550)

- **Added `next` field semantics** to server instructions (#550)

### Fixed

- **Duplicate scenario IDs** 53/54 → 70/71 in blind eval suite (#550)
- **Stale scenario #5** PASS criteria updated for v0.13.0 API (no single-item wrappers) (#550)
- **Scenario #13** relaxed from 4 queries to 3+ (removed PLANNING PATTERN dependency) (#550)

### Added

- **5x multi-run eval infrastructure** — `run_eval.py --runs 5` for variance analysis (#544, #559)
- **Regex + LLM auto-scoring** — `--scorer-model` flag for semantic scoring of explanation scenarios (#544)
- **macOS Keychain API key storage** for eval runner (#551, #554)
- **`--descriptions` and `--label` flags** for A/B testing different description versions (#550)
- **CI wait step** in `/merge-and-status` command — prevents confusing error when CI is pending (#553)
- **Adversarial API critic** workflow — ranked findings by agent mistake likelihood × severity (#544)
- **Post-fix eval rerun** confirming Claude at 100% and DeepSeek improved (#562, #563)

### Documentation

- **Blind eval results** — 5x runs across Claude (100%), DeepSeek (93.7%), Llama (89.7%)
- **Test docstrings** added to all 474 previously undocumented test methods (#547, #549)

## [0.13.0] - 2026-03-24

Unified batch CRUD for all entity types — tags and folders join tasks and projects with Pydantic model inputs. Deprecated single-item wrappers removed from MCP surface.

### Added

- **Unified `create_tags()` and `update_tags()`** with `TagCreate`/`TagUpdate` Pydantic models (#493, #541)
  - Batch tag creation and updates with per-item values
  - `create_tag`/`update_tag` deprecated to delegate

- **Unified `create_folders()` and `update_folders()`** with `FolderCreate`/`FolderUpdate` Pydantic models (#494, #542)
  - Batch folder creation and updates with per-item values
  - `create_folder`/`update_folder` deprecated to delegate

### Removed

- **8 deprecated single-item MCP tools** removed from agent-visible surface (#495, #543)
  - `create_task`, `update_task`, `create_project`, `update_project`, `create_tag`, `update_tag`, `create_folder`, `update_folder`
  - Functions remain as internal Python helpers; agents now use batch versions exclusively
  - MCP tool count: 29 → 21

### Changed

- **Eval scenarios updated** to use batch tool names throughout (71 scenarios)
- **tool_descriptions.md** cleaned up — removed 8 deprecated sections

## [0.12.1] - 2026-03-23

Test quality and eval accuracy release — driven by adversarial test quality review (#518). Refactored high-complexity helpers, fixed stale eval scenarios, and added missing test coverage.

### Added

- **4 dependency organization eval scenarios** (#531, #536)
  - Sequential action groups, mixed parallel/sequential chains, nested action groups, diamond dependencies

- **2 batch create eval scenarios** (#532, #535)
  - Tests whether agents discover `create_tasks` and `create_projects` for batch operations

- **6 E2E tests for batch create and round-trip update verification** (#533, #537)
  - `create_tasks` single/batch/field round-trip, `create_projects` batch, update flagged/name read-back

- **3 Pydantic conflict validation tests** (#534, #538)
  - `tags`+`add_tags` on `update_tasks`/`update_task`, `project_id`+`parent_task_id` on `create_tasks`

- **11 write benchmark assertions** (#534, #538)
  - All write operations now have regression thresholds (5.0s single, 15.0s batch)

- **Compound filter benchmark** for `get_projects` with stacked filters (#534, #538)

### Changed

- **Refactored `_filter_by_date_range`** — CC 26 → 5 via `_item_passes_date_check` helper (#512, #529)

- **Refactored `_post_process_projects`** — CC 28 → 18 via `_compute_project_types`, `_filter_projects_by_query`, `_compute_stalled_status` helpers (#521, #530)

- **Updated stale eval scenarios** (4, 5, 18, 50) to use new `list[TaskUpdate]`/`list[ProjectUpdate]` format (#532, #535)

- **Rewrote `update_tasks` in tool_descriptions.md** — was documenting old `task_ids` API (#532, #535)

- **Added `create_tasks` to tool_descriptions.md** — was missing entirely (#532, #535)

### Fixed

- **Brittle E2E assertion** in `update_projects` single-item test (#539)

## [0.12.0] - 2026-03-23

Unified batch CRUD release — Pydantic model inputs for create/update operations, full filter parity between `get_tasks` and `get_projects`, and project metadata enrichment.

### Added

- **Unified `create_tasks()` with Pydantic model input** (#489, #507)
  - Accepts `list[TaskCreate]` for batch task creation with full per-item control
  - Original `create_task()` now delegates to `create_tasks()` internally (#490, #508)

- **Unified `update_tasks()` with Pydantic model input** (#492, #509)
  - Accepts `list[TaskUpdate]` for batch updates with per-item values (not uniform fields)

- **Unified `create_projects()` with Pydantic model input** (#513, #515)
  - Accepts `list[ProjectCreate]` for batch project creation

- **Unified `update_projects()` with Pydantic model input** (#513, #516)
  - Accepts `list[ProjectUpdate]` for batch project updates with per-item values

- **`planned_before`/`planned_after` date filters on `get_tasks()`** (#510)
  - Filter tasks by planned date range, complementing existing due/defer filters

- **Tags field and `tag_filter` on `get_projects()`** (#511)
  - Projects now return their assigned tags; filterable by tag name

- **`flagged` field and `flagged_only` filter on `get_projects()`** (#500, #517)
  - Projects now return flagged status; filterable to show only flagged projects

- **`include_completed` and `completed_only` filters on `get_projects()`** (#501, #519)
  - Completed projects now hidden by default; retrievable with explicit filter

- **`planned_before`/`planned_after`/`planned_on` on `get_projects()`** (#520)
  - Filter projects by planned date range or specific day

- **`has_overdue_tasks` filter on `get_projects()`** (#502, #522)

- **16 connector-only filters exposed in server layer** (#503, #523)
  - `modified_after`, `modified_before`, `created_after`, `created_before`, `context_filter`, `completed_after`, `completed_before`, `status_filter`, `folder_filter` for tasks
  - `modified_after`, `modified_before`, `created_after`, `created_before`, `review_status`, `status_filter`, `folder_filter` for projects

- **Review interval in `get_projects()` output + all time units** (#505, #506, #524)
  - Projects return `review_interval_days`; `update_project` supports `review_interval_value` + `review_interval_unit` (days/weeks/months/years)

### Fixed

- **7 integration/E2E test failures** from API changes (#525, #526, #527)
  - Updated tests to use new Pydantic model signatures and `include_completed` filter

## [0.11.0] - 2026-03-22

API quality release — driven by adversarial API review (#451). Standardized types, cleaned up descriptions, added new features, and improved documentation clarity for LLM clients.

### Added

- **`include_dropped` parameter on `get_projects()`** (#460, #481)
  - Dropped projects were previously always filtered out; now retrievable for verification and audits

- **Per-method AppleScript tell/end-tell balance tests** (#459, #486)
  - 28 parametrized tests checking balance per connector method (tolerance 2)

- **Dropped project state verification** (#438, #485)
  - Integration test now verifies dropped status via read-back using include_dropped

### Changed

- **Standardized `sequential` parameter to `bool`** across all functions (#470, #478)
  - `update_project` and `update_projects` accepted `str`; now `bool` everywhere

- **Stripped development-history noise from docstrings** (#467, #480)
  - Removed ~300 tokens of "NEW (Phase X.Y)", "Redesign", consolidation lists

- **Removed legacy `name` parameter from `update_task`** (#476, #483)
  - Use `task_name` instead; `name` alias no longer in the MCP schema

- **Improved reorder descriptions** with worked-order examples (#472, #487)
  - `reorder_task("C", before_task_id="A") → [..., C, A, ...]`

- **Clarified `parent_tag` is by-name, not by-ID** (#474, #487)
  - Cross-references between `get_tags()` output (parentTagId) and set operations

- **Strengthened `status="dropped"` one-way warning** (#475, #487)

### Fixed

- **`get_projects` response text** now reflects active filter (#471, #479)
  - Was always "Found N active projects" even with `on_hold_only=True`

## [0.10.5] - 2026-03-21

### Added

- **E2E test coverage for 14 previously uncovered MCP functions** (#435, #450)
  - get_tasks (4 filter variants), get_projects, create_project, delete_projects
  - Tag lifecycle (create/update/delete), folder lifecycle, perspectives, focus

- **Unicode/emoji test fixture across all layers** (#434, #456)
  - 19 unit tests + 4 integration tests verifying round-trip for accented chars, emoji, CJK, Cyrillic

- **Performance baseline assertions in benchmarks** (#447, #453)
  - 19 read benchmarks now assert against 5x documented baselines — catches catastrophic regressions

- **Batch mode invariant tests** (#444, #452)
  - Verifies `a reference to` pattern exists in get_tasks, get_projects, and get_folders

- **8 new blind eval scenarios** (#440-#443, #463)
  - Under-covered tools (reorder, delete_tags, perspectives, folders), multi-step triage, error recovery, tags-format regression

- **Full blind eval run on Claude + 4 open-weight models** (#464, #465)
  - DeepSeek Chat matched Claude at 99.2%; Llama improved +6.1pp to 93.1% (0 FAILs)
  - All 9 new scenarios passed universally across all models

### Changed

- **get_folders converted to batch mode — 15x speedup** (#454, #462)
  - Replaced recursive per-folder AppleScript traversal with `a reference to flattened folders`
  - 28 folders: 4.0s → 0.26s

- **Benchmark iterations increased from 3 to 5** for read operations (#446, #463)

### Fixed

- **Hollow coverage tests strengthened** (#448, #449)
  - Added `assert_called_once_with` to 30 tests that previously only checked output strings

- **reviewInterval commented-out assertion replaced with pytest.xfail** (#437, #457)

- **AppleScript tell-block balance checker tightened** from tolerance 10 to 5 (#433, #458)

- **Folder rename and cross-folder project move integration tests** (#439, #461)

## [0.10.4] - 2026-03-20

### Added

- **Tags, flagged, estimated_minutes, recurrence on projects** (#417, #418)
  - `update_project` gains 7 new parameters: `tags`, `add_tags`, `remove_tags`, `flagged`, `estimated_minutes`, `recurrence`, `repetition_method`
  - `update_projects` (batch) gains 4 new parameters: `flagged`, `estimated_minutes`, `add_tags`, `remove_tags`
  - Projects are tasks in OmniFocus's data model — same AppleScript patterns apply

- **Tag reparenting via `update_tag(parent_tag=...)`** (#415, #416)
  - Move tags between parents: `update_tag(tag_id, parent_tag="People")`
  - Move to top level: `update_tag(tag_id, parent_tag="")`
  - Preserves all task associations

- **GitHub project polish** (#409, #419-#426)
  - MIT license (`LICENSE`)
  - PR template (`.github/PULL_REQUEST_TEMPLATE.md`)
  - SECURITY.md responsible disclosure policy
  - Dependabot for monthly dependency updates and security alerts
  - README badges (CI, coverage, Python version, license)
  - Required status checks on branch protection (CI must pass to merge)

### Fixed

- **Tag full replacement broken on all tasks** (#413, #414)
  - `update_task(tags=["X"])` was silently failing with -1700 on ALL tasks (not just dropped)
  - Root cause: AppleScript `set tags of theTask to {list}` can't coerce constructed tag lists
  - Rewrote to remove-all + add-each pattern (same as working `add_tags`/`remove_tags`)
  - Removed misleading "dropped task" error message from #404

## [0.10.3] - 2026-03-20

### Added

- **Drop entire recurring task series** (#405, #410)
  - `update_task(task_id, recurrence="", status="dropped")` now drops the whole series in a single call
  - Reordered internal command building so recurrence removal precedes `mark dropped`, preventing next occurrence from spawning
  - New blind eval scenario (#53) validates Claude discovers the pattern from tool descriptions

- **Test coverage threshold enforcement** (#396, #411)
  - `fail_under` raised from 89 → 90 in `pyproject.toml`
  - 55 new unit tests covering format helpers, error handlers, and batch response formatting
  - `server_fastmcp.py` coverage: 82% → 99%; overall: 90% → 95%
  - Added `make coverage` Makefile target
  - Excluded unreachable `if __name__ == "__main__"` from coverage

### Fixed

- **Normalized `create_task` tags parameter to native list** (#403, #406)
  - Changed `tags` from `Optional[str]` (JSON string) to `Optional[list[str]]`, matching `update_task`
  - Removed JSON parsing logic and unused `import json` from server
  - Clear error message when non-list type is passed

- **Clear error when modifying tags on dropped tasks** (#404, #407)
  - AppleScript type coercion error (-1700) on tag operations against dropped tasks now returns an actionable message instead of opaque error

- **Removed redundant Python-side query filter in `get_tasks`** (#398, #408)
  - `_post_process_tasks()` re-checked name/note containment after both upstream paths (whose clause and batch filter) already handled it
  - Removed dead code and `query` parameter from `_post_process_tasks()`

## [0.10.2] - 2026-03-19

### Added

- **`inInbox` boolean on tasks** (#378, #385)
  - `get_tasks` now returns `inInbox: true/false` for each task
  - Enables reliable inbox detection without relying on missing `containingProjectId`

- **`completed_by_children` on tasks (read/write)** (#379, #390)
  - `get_tasks` returns `completedByChildren` for action groups
  - `update_task` accepts `completed_by_children` to toggle auto-completion behavior

- **Blind eval scenarios for mutually exclusive tag creation** (#303, #392)
  - 2 new scenarios (53-54): create exclusive tag group, verify mutual exclusivity warning

- **Blind agent evals with open-weight models** (#342, #393)
  - Evaluated DeepSeek V3 (96%), Qwen 2.5 72B (91%), Mistral Large (88%), Llama 3.3 70B (87%)
  - Tool description improvements driven by open-weight failure analysis

- **Release review phases** (#388, #395)
  - Test coverage review (Phase 6), code review (Phase 7), documentation review (Phase 8)
  - Coverage threshold (`fail_under = 90`) added to `pyproject.toml`

- **Item counts in performance benchmark results** (#391, #394)
  - Benchmark output and profiling doc baselines now include number of items returned

### Fixed

- **`set_focus` cannot find nested folders** (#381, #384)
  - Changed `folders whose id is` to `flattened folders whose id is` for nested folder support

- **Missing `creationDate` and `modificationDate` in task/project output** (#377, #382)
  - Dates were fetched but omitted from formatted output

- **8 failing E2E tests** (#387, #389)
  - Wrong parameter names and `.fn` accessor issues in set_focus tests

- **E2E set_focus tests using wrong parameter names** (#383, #386)

### Changed

- **Documentation accuracy sweep** (#388, #395)
  - Coverage 91% → 90%, unit test count 787 → 803, API surface 22 → 23 (added `update_folder`)
  - README: updated eval results (52 → 54 scenarios, multi-model scores), added benchmark item counts
  - Removed tilde approximations from all benchmark tables

- **Metadata audit** (#376, #380)
  - Identified and documented all unexposed OmniFocus task/project properties

## [0.10.1] - 2026-03-17

### Added

- **`reorder_project` tool** (#357)
  - Move projects before/after other projects within a folder
  - Parallel implementation to `reorder_task` (23 tools total)
  - Blind eval scenario 52: PASS (104/104, 100%)

### Changed

- **All `get_tasks()` paths now use batch mode** (#368)
  - Eliminated per-task execution paths (`_build_per_task_mode_script` deleted, ~326 lines)
  - `inbox_only`: 9.13s → 0.64s (14x faster)
  - `get_tasks()` complexity: 24 → 15, `_build_task_filter_checks`: 54 → 35
  - Also fixes `get_tasks(include_completed=True)` timeout (#364) and `defer_relative` filter gap (#367)

### Fixed

- **`update_project(status='dropped')` now works** (#359)
  - Projects use `mark dropped` (command verb) and `set status to active status` (enum), not `set dropped to true/false`
  - Both single and batch paths fixed
  - Documented in APPLESCRIPT_GOTCHAS.md

- **`update_task(status='active')` now raises clear error** (#372)
  - OmniFocus does not support undropping tasks via any automation API (AppleScript or OmniAutomation)
  - Previously generated broken AppleScript that always failed
  - Now raises `ValueError` with explanation

- **Inherited availability for tasks in done/dropped containers** (#363)
  - Tasks in completed or dropped projects now correctly show `available: false`
  - Uses `effectively completed` and `effectively dropped` batch-readable properties

- **Integration test coverage for project status transitions** (#369)
  - Full lifecycle test: ACTIVE → ON_HOLD → ACTIVE → DROPPED → ACTIVE → DONE
  - Strengthened existing tests to verify actual status (not just success bool)
  - Batch project drop test added

### Removed

- Stale `docs/reference/API_REFERENCE.md` (3,024 lines) (#353)

## [0.10.0] - 2026-03-16

### Added

- **Project date support** (#329, #336, #337, #338)
  - `create_project`, `update_project`, `update_projects` now accept `due_date`, `defer_date`, `planned_date`
  - `get_projects` returns `dueDate`, `deferDate`, `plannedDate` for each project
  - Tasks inherit effective dates from their containing project

- **Blind eval scenarios for project dates and task movement** (#339, #340, #344)
  - 5 new scenarios (43-47): project date create/clear/read, subtask movement, text search
  - Total: 47 scenarios, 100% pass rate

### Changed

- **README rewrite** (#246, #341, #344)
  - Benefits-first positioning: comprehensive, fast, reliable, agent-friendly
  - Inline performance table with profiled benchmarks
  - Informed by landscape scan of 7 competing OmniFocus MCP servers

## [0.9.2] - 2026-03-16

### Changed

- **Major complexity reduction across core functions** (#265, #325, #328)
  - `get_tasks`: CC 135 → 24 (82% reduction, 8 helper methods extracted)
  - `update_task`: CC 55 → 7 (87% reduction, 3 helpers)
  - `update_tasks`: CC 46 → 10 (78% reduction, 3 helpers)
  - `get_projects`: CC 35 → 7 (80% reduction, 2 helpers)
  - 130 new unit tests for extracted helpers

### Fixed

- **OmniFocus crashes during integration tests** (#324, #326)
  - OmniAutomation (`evaluate javascript`) calls now skipped on headless test databases
  - Root cause: `get_tags()` exclusivity enrichment triggered silent OmniFocus crash

- **Review date conversion bugs** (#320, #330, #332, #334)
  - `update_project` `next_review_date` passed raw ISO to AppleScript (produced year 12169)
  - `update_project` `last_reviewed` had the same raw ISO bug
  - Both now use `_iso_to_applescript_date()` like all other date fields

- **JavaScript string escaping for OmniAutomation** (#318, #333)
  - New `_escape_js_string()` for proper JS escaping in `evaluate javascript` contexts
  - Replaces fragile `_escape_applescript_string() + .replace("'", "\\'")` pattern

- **6 integration tests with wrong API signatures** (#327, #331)
  - Fixed `update_tag(active=False)` → `update_tag(status="on_hold")`
  - Skipped tests blocked by missing project date params (#329) and date bug (#330)

### Maintenance

- Performance benchmarks for v0.9.1 baseline (#282, #323)
- Fixed stochastic blind eval failures (#314, #317)
- Split issue templates and updated contributing guide (#283, #316)
- Removed redundant /release-validate command (#321, #322)

## [0.9.1] - 2026-03-15

### Added

- **Next occurrence dates on recurring tasks** (#294, #311)
  - `get_tasks` returns `nextDueDate`, `nextDeferDate`, `nextPlannedDate` for recurring tasks
  - Shows dates of the next recurrence without completing the current one

- **Catch up automatically field** (#295, #312)
  - `get_tasks` returns `catchUpAutomatically` boolean from the repetition rule
  - When true, only one catch-up occurrence is created for missed recurrences

- **Mutually exclusive tag configuration** (#303, #313)
  - `get_tags` returns `childrenAreMutuallyExclusive` boolean (read via OmniAutomation)
  - `create_tag` and `update_tag` accept `children_are_mutually_exclusive` parameter
  - Agents can now detect when adding a tag will silently remove another

- **Sequential flag on action groups** (#307, #309)
  - `create_task` and `update_task` accept `sequential` parameter
  - Controls whether subtasks of an action group must be completed in order

- **Safe production integration testing** (#274, #308)
  - New `make test-prod` target for OmniAutomation tests against production DB
  - Sandbox folder pattern with UUID-named entities and automatic cleanup

### Changed

- **Effective dates documentation** (#298)
  - Clarified that `dueDate`, `deferDate`, `plannedDate` reflect inherited dates from project/parent

### Documentation

- OmniFocus archive access research findings (#247, #305)
- Mutually exclusive tag behavior research (#302, #304)
- Post-v0.9.0 gap analysis update (#293)

## [0.9.0] - 2026-03-13

### Added

- **Planned date support** (#252, #271)
  - `create_task` and `update_task` now accept `planned_date` for intention-based scheduling
  - `get_tasks` returns `plannedDate` field

- **Recurrence write support** (#272, #275)
  - `update_task` now accepts `recurrence` (iCal RRULE string) and `repetition_method` (`fixed`, `start_after_completion`, `due_after_completion`)
  - Allows creating and modifying recurring tasks via the MCP API

- **Human-readable repeat summary** (#260, #273)
  - `get_tasks` returns `repeatSummary` (e.g. "Every day") and `isRecurring` fields
  - Agents can describe recurrence patterns without parsing RRULE strings

- **Tag dropped status** (#259, #276)
  - `update_tag` now accepts `status: "dropped"` or `"active"` to archive/restore tags
  - `get_tags` returns `status` field

- **Folder dropped status + `update_folder`** (#258, #280)
  - New `update_folder` tool — update folder name or drop/restore folders
  - `get_folders` returns `status` field

- **Single Actions List project type** (#255, #279)
  - `get_projects` returns `projectType` as `"single_actions"` for SAL projects
  - `create_project` and `update_project` accept `project_type: "single_actions"`

- **`next_review_date` write** (#257, #281)
  - `update_project` and `update_projects` now accept `next_review_date` to explicitly set the next review date

- **`completedByChildren` project property** (#254, #285)
  - `get_projects` returns `completedByChildren` boolean
  - `create_project` and `update_project` accept `completed_by_children` to control auto-completion when last action is checked off

- **Stalled project detection** (#256, #287)
  - `get_projects` returns `stalled` boolean with `include_task_health=True`
  - New `stalled_only` parameter returns only active projects with no available actions
  - Projects with all tasks deferred are correctly excluded (they're scheduled, not stuck)

- **Effective dates (inherited from container)** (#253, #289)
  - `get_tasks` now reads `effective due date`, `effective defer date`, and `effective planned date` from OmniFocus
  - Tasks that inherit dates from their project now surface those dates in `dueDate`/`deferDate`/`plannedDate`
  - `get_tasks(overdue=True)` now catches tasks overdue via project inheritance

### Fixed

- **`repetition_method` docstring** (#277, #278)
  - Clarified that `due_after_completion` sets the next due date relative to completion, not the defer date

### Tests

- Added integration test coverage for `repeatSummary` positive case and `next_review_date` write path (#288, #291)

## [0.8.4] - 2026-03-11

### Fixed

- **create_task silently fails to assign On Hold tags** (#267, #269)
  - Removed `try/on error` wrapper from tag assignment AppleScript that silently swallowed errors
  - Now matches `update_task`'s proven pattern; non-existent tags raise errors instead of being silently skipped

- **available_only excludes tasks with On Hold tags** (#261, #268)
  - `get_tasks(available_only=True)` now pre-fetches On Hold tag names and excludes matching tasks
  - Matches OmniFocus's native Available perspective behavior

- **Perspectives type detection** (#248, #263, #266)
  - `get_perspectives` now correctly detects built-in vs custom perspective types
  - Fixed tag status reporting — `get_tags` now reads `allows next action` property instead of hardcoding "active"

### Changed

- **Tag filter performance** (#249, #250)
  - Tag-side pre-filter for `tag_filter` queries reduces unnecessary task iteration

### Documentation

- **Gap analysis and eval scenarios** (#264, #266)
  - Added `docs/omnifocus-mcp-gap-analysis.md` documenting API coverage gaps
  - Added 6 new blind agent eval scenarios for tag management and perspectives

## [0.8.3] - 2026-03-11

### Added

- **Full tag CRUD** (#226, #230, #231, #232, #233)
  - `create_tag` — create tags with optional parent nesting
  - `update_tag` — rename tags or set active/on-hold status
  - `delete_tags` — delete one or more tags (batch, with safety warnings)

- **Enhanced focus and perspectives** (#242, #243)
  - `set_focus` now supports multi-item focus (multiple projects/folders) and clear
  - `get_focus` — new tool to query currently focused items
  - `get_perspectives` now returns structured dicts with name, type (built-in/custom), and ID

- **Blind agent eval for tool usability** (#227, #244)
  - 18 scenarios across 5 categories testing whether agents can use tools from descriptions alone
  - Scored 36/36 (100%) after two docstring fixes, 0 critical safety failures
  - Eval framework in `evals/agent_tool_usability/`

- **Dependency and AppleScript safety audits** (#52, #54, #234)
  - `check_dependencies.sh` — pip-audit vulnerability scanning
  - `check_applescript_safety.sh` — detects unsafe variable naming patterns in AppleScript

### Changed

- **Enriched tool descriptions and server instructions** (#228, #229)
  - Added GTD concept documentation to server instructions block
  - Expanded all 21 tool docstrings with examples, format notes, and safety warnings
  - Added `tag_filter` example format and `create_task` sequential ordering note

### Documentation

- **Perspective and focus automation docs** (#235, #238, #240, #241)
  - Documented OmniFocus perspective automation capabilities and limitations
  - Documented focus automation: multi-item, clear, get_focus patterns

- **Testing requirements codified** (#236, #237)
  - Four-tier testing policy documented in CLAUDE.md
  - Added tag CRUD integration tests (6 tests in `TestTagCRUD`)

### Fixed

- **Release workflow** (#225)
  - Tags now created on main after PR merge (not on release branch before merge)
  - Prevents orphaned tags from squash/rebase merge SHA changes

## [0.8.2] - 2026-03-10

### Fixed

- **AppleScript injection hardening** (#222, #223)
  - Applied `_escape_applescript_string()` to all IDs embedded in AppleScript (`get_tasks`, `get_projects`, `delete_tasks`, `delete_projects`, `reorder_task`)
  - Escaped folder path components in `create_folder()` and tag names in `get_tasks()` tag filtering
  - Added `ValueError` handling to 9 MCP server tools that were missing it

### Changed

- **Batch write or-chain optimization** (#215, #219)
  - Applied `whose` or-chain pattern to `update_tasks()` and `update_projects()` bulk-settable fields
  - Near-constant time (~0.25s) regardless of batch size for flagged, estimated_minutes, due_date, defer_date, completed

- **Complexity refactoring** (#218, #220)
  - Extracted `_build_date_command` and `_build_tag_commands` helpers from `_build_task_update_commands`
  - Reduced cyclomatic complexity from CC 23 → CC 14

### Removed

- **Dead code cleanup** (#222, #223)
  - Removed 4 unused helper methods: `_build_date_command`, `_build_tag_commands`, `_build_task_update_commands`, `_build_project_update_commands`
  - Removed 16 associated dead code tests

### Documentation

- **Contribution policy** (#212, #221)
  - Added CONTRIBUTING.md clarifying this is a personal project not accepting external contributions
  - Added notice to README.md

## [0.8.1] - 2026-03-09

### Added

- **Write operation benchmarks** (#204, #208)
  - Benchmarks for batch updates, mark complete, and payload sizes
  - Baselines added to performance profiling documentation

- **Batch optimize `update_tasks()` and `update_projects()`** (#205, #209)
  - Single AppleScript call with internal repeat loop replaces N separate calls
  - 1.4-1.6x speedup for batch write operations

### Changed

- **Document structured updates as plugin-level orchestration** (#207, #216)
  - Added architecture guidance: project+tasks updates belong at plugin layer, not MCP API
  - Two fast MCP calls beat one complex combined function
  - Updated `/daily-wrapup` plugin to use `update_tasks` for batch completions

### Research

- **Group-scoped update patterns** (#210, #214)
  - Empirically tested containment-scoped property sets, `mark complete`, filtered scopes, and `whose` or-chain pattern
  - Or-chain achieves near-constant time (~0.25s) regardless of batch size — 2.9x faster than per-ID loop at 10 tasks
  - Documented in OMNIFOCUS_AUTOMATION_NOTES.md and PERFORMANCE_PROFILING.md

- **RTF note manipulation via OmniAutomation** (#206, #211)
  - Documented `evaluate javascript` for rich text access (`noteText`, `attributeRuns`, style attributes)
  - Discovered headless test database crash limitation — OmniAutomation features require manual testing
  - Documented RTF-safe append pattern vs RTF-destructive AppleScript pattern

## [0.8.0] - 2026-03-07

### Added

- **35x `get_projects()` performance optimization** (#201)
  - Batch property extraction via `a reference to` pattern eliminates per-project Apple Events
  - Global task batch with parallel counter lists for `include_task_health` and `include_last_activity`
  - 114 projects: 62s → 1.78s (all options enabled)
  - Extracted `_build_task_ops_blocks()` helper to keep cyclomatic complexity within thresholds

- **`get_tasks()` batch property extraction** (#196, #197)
  - Native `whose` clauses for filter pre-filtering (21-50x speedup on selective queries)
  - `a reference to` batch reads for all task properties in a single Apple Event per property type

- **Comprehensive benchmark infrastructure** (#194)
  - Test database setup/teardown scripts for reproducible profiling
  - AppleScript automation reference documentation

### Fixed

- **Tag filtering crash on list-type tags** (#199, #202)
  - `_filter_tasks_by_tags()` called `.split(',')` on a Python list (tags returned as JSON arrays from AppleScript)
  - Now handles both list and legacy string formats
  - Added `ensure_test_tags` fixture for integration tests requiring tags in the test database

- **Architecture and test suite review** (#174, #175, #193)
  - Fixed stale test assertions, dead tests, and `.fn` accessor pattern
  - Repaired broken test suite compatibility

### Changed

- **Batch subtask counts** (#200)
  - Per-project subtask counting now uses batch reads instead of per-task iteration
  - Fixed test database scripts for reliable profiling setup

## [0.7.3] - 2026-03-05

### Added

- **Performance benchmark suite** (#187, #190)
  - 15 benchmarks covering all major read and write operations
  - Compares against documented baselines from CLAUDE.md
  - Handles production database timeouts gracefully with `pytest.skip()`
  - Surfaced real performance regression on large databases (#191)

- **Release workflow automation** (#186)
  - New `/release` skill orchestrating 8-phase release process
  - Milestone check, version bump, changelog, validation, tagging, PR creation
  - Updated pre-tag hook to allow tags on `release/*` branches

- **Project task health** (#185)
  - `get_projects(include_task_health=True)` returns per-project task counts (remaining, available, overdue, deferred) in a single AppleScript call
  - Eliminates N+1 query pattern for project review workflows

- **Opt-in lastActivityDate** (#185)
  - `get_projects(include_last_activity=True)` makes expensive per-project calculations opt-in
  - Saves ~260ms for 33 projects when not needed

- **AppleScript query filter** (#185)
  - `get_tasks(query="...")` now filters in AppleScript (filter-first) instead of Python
  - Significant performance improvement for text search queries

### Fixed

- **Scripts audit** (#188, #189)
  - Fixed `check_client_server_parity.sh` referencing deleted `omnifocus_client.py` (renamed in v0.6.1)
  - Fixed `check_complexity.sh` referencing deleted `omnifocus_client.py`
  - Removed 8 dead/unreferenced scripts (-998 lines)
  - Removed 4 CI references to scripts that never existed
  - Updated integration-testing skill to remove references to deleted scripts

- **Claude Code config cleanup** (#184)
  - Modernized Claude Code configuration
  - Purged dead scaffolding and stale references

## [0.7.2] - 2025-11-18

### Added

- **CHANGELOG date validation** (#166)
  - New `check_changelog_date.sh` script verifies CHANGELOG date is not "TBD" before final release tags
  - Integrated as Check #10 in pre-tag hook (runs only for final release tags, not RC tags)
  - Updated release workflow documentation to clarify when CHANGELOG date should be updated

### Changed

- **Performance optimization for get_tasks() and get_projects()** (#170)
  - Profiled query performance and identified bottlenecks in selective filters
  - Optimized query construction to reduce overhead
  - ~15-20% performance improvement for filtered queries

- **Test fixture refactoring complete** (#168)
  - All 108 integration tests now use fixtures or try/finally cleanup patterns
  - Zero test database pollution (except unavoidable OmniFocus folder limitation)
  - 100% test isolation achieved

### Fixed

- **Test count synchronization** (#169)
  - Fixed test count mismatch between README.md (333) and TESTING.md (513)
  - Created `check_test_count_sync.sh` script to prevent future mismatches
  - Integrated into pre-commit warning and pre-tag blocking checks
  - TESTING.md is now single source of truth for test counts

## [0.7.1] - 2025-11-14

### Added

- Test fixtures infrastructure with automatic cleanup (#143)
- E2E test refactoring to use fixtures (#162)

### Changed

- **Performance improvement**: ~7.8× speedup in integration tests (from ~30 min to ~4 min)
  - Root cause: Replaced full-table scans with direct ID lookups via fixtures
  - E2E tests: 20 tests now pass in 32.94 seconds
  - Integration tests: 108 tests now pass in 232.60 seconds

## [0.7.0] - 2025-11-11

### Added

- **UI Navigation tool** (#77)
  - `set_focus()` - Focus OmniFocus window on specific projects or folders
  - AppleScript limitation: only projects and folders support focus (not tasks/tags)
  - Returns structured dict with success status
  - Complete test coverage (7 unit + 4 integration + 3 E2E tests)

- **Pending release detection** (#140)
  - New `check_pending_releases.sh` script detects RC tags without final releases
  - Enhanced `create_tag.sh` blocks new RC creation if pending releases exist
  - CI check runs on every push to detect incomplete releases
  - Updated CHANGELOG policy to prevent premature updates
  - Resolves incomplete v0.6.7 release (RC created but never finalized)

### Changed

- **Hygiene check execution order optimized** (#132)
  - Fast checks (1-6) run first: version sync, complexity, parity, milestone, ROADMAP sync, docs (~1-2s each)
  - Slow checks (7-8) run last: test coverage (~30s), all tests (~20-25 min)
  - Previous order had tests at position #2, now at position #8 (last)
  - Provides faster feedback when early checks fail

- **Pre-push git hook added** (#130)
  - Runs unit tests before push to catch failures early
  - Prevents pushing failing tests to remote
  - Complements CI monitoring for faster local feedback

- **Branch protection git hook enhanced** (#134)
  - Blocks commits to main/master during manual git operations
  - Allows hotfix commits (message contains "hotfix" or "emergency")
  - Allows commits to release/* branches
  - Provides backup enforcement for Claude Code hooks

### Fixed

- **Unit test timeout issue** (#129)
  - Fixed pytest configuration: changed `testpaths` from `["."]` to `["tests"]` in pyproject.toml
  - Root cause: pytest.ini → pyproject.toml migration inadvertently caused pytest to search outside tests directory
  - Deleted slow smoke tests in test_hygiene_scripts.py (9 tests taking 2-3 minutes each)
  - Unit tests now pass in ~2.5 minutes

- **Test coverage check returning empty percentage** (#131)
  - Fixed coverage check script: changed `--cov=src/omnifocus_mcp/omnifocus_connector` to `--cov=src/omnifocus_mcp`
  - Root cause: Coverage was trying to track a specific file path instead of the package
  - Coverage check now correctly reports coverage percentage

## [0.6.6] - 2025-11-02

### Added

- **Release process infrastructure** (#70, #108, #109)
  - Overhauled hygiene checks with review-and-approve workflow
  - Enhanced pre-tag hook to prompt for interactive quality checks on minor/major releases
  - Created automation candidates tracking system for recurring AI-process issues
  - Documented complete release process with patch/minor/major distinctions

- **Interactive quality check slash commands** (#86, #102, #103, #104)
  - `/doc-quality` - Comprehensive documentation quality assessment
  - `/code-quality` - Code quality analysis beyond basic complexity metrics
  - `/test-coverage` - Test coverage analysis with testing types recommendations
  - `/directory-check` - Directory organization and file structure review

- **Workflow enforcement and documentation** (#87, #88, #89, #94)
  - One-branch-per-issue workflow with branch naming conventions
  - Version update protocol decision tree (patch/minor/major requirements)
  - AI-process migration workflow for recurring issues
  - Git pre-commit hook for branch protection during manual operations

- **Claude Code hooks for automated enforcement** (#41, #42, #43, #66)
  - Branch validation (prevents commits to main/master)
  - Issue close verification (checks acceptance criteria)
  - CI monitoring (watches GitHub Actions after push)
  - Session context (loads branch, issues, recent commits)

### Changed

- **Documentation reorganization** (#93)
  - Updated ROADMAP.md to remove outdated content and add completed work sections
  - Updated version references across README, API_REFERENCE, CONTRIBUTING (v0.6.2 → v0.6.5)
  - Consolidated hygiene check documentation (9 checks → 7 automated + 4 interactive)

### Fixed

- **AI-process issue tracking and prevention** (#28, #31, #32, #34, #36, #72, #85)
  - Automated ROADMAP.md sync check (closed issues must be removed)
  - Test count synchronization check
  - Recurrence tracking and validation system
  - Prevention measure effectiveness validation
  - Proactive GitHub Actions monitoring

## [0.6.5] - 2025-10-28

### Fixed

- **Critical: AppleScript DONE status bug** (#83)
  - `update_project()` failed when setting status to DONE
  - OmniFocus requires `mark complete` verb instead of `set status to done`
  - All integration tests now pass (92/92, 100% success rate)

- **Integration test API migration** (#67, #79-#82)
  - Updated tests to use v0.6.0 API patterns (#79)
  - Added lastReviewDate and nextReviewDate fields to get_projects() API (#80)
  - Fixed delete operation assertions to check deleted_count instead of success (#81)
  - Fixed TaskStatus/ProjectStatus import paths to omnifocus_connector module (#82)
  - Added timestamp-based unique names to prevent test isolation issues

### Added

- **GitHub Actions CI workflow** (#69)
  - Automated unit testing on push/PR to main
  - Excludes integration tests (require local OmniFocus)
  - Includes complexity checks and client/server parity verification
  - Uses macOS runner with Python 3.10

- **Testing documentation** (#73)
  - Added comprehensive "Testing Setup" section to CONTRIBUTING.md
  - Documents test database setup with scripts/setup_test_database.sh
  - Explains differences between unit, integration, and E2E tests
  - Links to detailed INTEGRATION_TESTING.md guide

## [0.6.4] - 2025-10-25

### Fixed

- **Critical: Release hygiene enforcement** (#60)
  - v0.6.3 was released with placeholder hygiene checks that didn't actually run
  - Created actual check scripts:
    - `scripts/run_all_tests.sh` - Runs ALL test suites (unit + integration + e2e)
    - `scripts/check_test_coverage.sh` - Validates coverage, checks for TODO markers
    - `scripts/check_documentation.sh` - Verifies CHANGELOG entries, version sync, key docs exist
    - `scripts/check_code_quality.sh` - Checks complexity, TODOs, print statements, code smells
    - `scripts/check_directory_organization.sh` - Identifies orphaned files
  - Updated `scripts/git-hooks/pre-tag` to call actual checks instead of placeholders
  - Documentation check is now blocking (critical)
  - Coverage/quality/organization checks provide warnings but don't block

### Changed

- Added automation testing requirement to CLAUDE.md checklist
  - Requires testing both happy path and failure scenarios before releasing automation
  - Prevents releasing automation with only placeholder text

## [0.6.3] - 2025-10-25

### Added

- **Release workflow automation and validation** (#46)
  - GitHub Actions workflow for RC tags (`v*-rc*`) that validates release readiness
  - GitHub Actions workflow for final tags that creates releases and manages milestones
  - Git pre-tag hook that enforces hygiene checks locally before tag creation
  - Version sync automation through `scripts/sync_version.sh`
  - RC tag workflow: create `v0.6.3-rc1`, run checks, fix issues, create `v0.6.3-rc2`, repeat until clean, then create final `v0.6.3` tag

- **Milestone planning enforcement** (#45)
  - SessionStart hook now dynamically calculates current milestone from version
  - Shows active milestone with open issues list
  - Warns if no milestone exists for next version

- **Issue tracking workflow enforcement** (#44)
  - Pre-commit hook validates commit messages reference issue numbers
  - Exceptions for merge/revert/version bump commits
  - Prevents commits without proper tracking

### Documentation

- **Trunk-based development workflow** (#56)
  - Comprehensive documentation in README.md, CONTRIBUTING.md, ROADMAP.md
  - Single main branch strategy, tags mark releases, RC tags for validation
  - Contributor workflow and release workflow documented

- **Directory cleanup Sprint 1** (#49)
  - Archived 8 legacy mistake tracking scripts to `scripts/archive/mistake-tracking-legacy/`
  - Updated scripts/README.md and scripts/archive/README.md with migration notes
  - Documented dual hook systems (git vs Claude Code) in hook documentation

### Fixed

- **Hanging Bash hook tests** (#47)
  - Replaced `tests/test_hooks.sh` with Python pytest suite `tests/test_claude_code_hooks.py`
  - 11 comprehensive tests using temporary git repos for isolation
  - All tests pass in <1 second vs hanging indefinitely

- **Version synchronization** (#29, MISTAKE-003)
  - Automated version sync across pyproject.toml, CLAUDE.md, CHANGELOG.md, README.md
  - Version source of truth: pyproject.toml
  - Integrated into git pre-tag hook to prevent version drift

### Changed

- Migrated from GitFlow to trunk-based development
- RC tags now trigger comprehensive hygiene checks before final release
- Current version: v0.6.3 (Release Automation)

## [0.6.2] - 2025-10-25

### Added

- **Claude Code hooks for process enforcement** (#40, #41, #42, #43)
  - Implemented modular hook system in `scripts/hooks/` directory
  - **PreToolUse(Bash)**: Blocks commits to main branch (addresses #37)
    - Allows hotfixes with "hotfix" or "emergency" in commit message
    - Modular design with `check_*` functions for easy extension
  - **PostToolUse(Bash)**: Monitors GitHub Actions after git push (addresses #36, #39)
    - Automatically watches CI runs until completion
    - Blocks Claude if CI fails, requiring fixes before continuing
    - ~1-5ms overhead on non-push commands, intentional blocking on push
  - **SessionStart**: Loads project context at session start
    - Shows current branch, warns if on main
    - Displays open issues and milestone progress
    - Sets up environment variables
  - Configuration in `.claude/settings.json` (checked into version control)
  - Test suite in `tests/test_hooks.sh` (known issue #47 with test 2 hanging)

### Documentation

- **Comprehensive hook documentation** (2,500+ lines)
  - `docs/reference/CLAUDE_CODE_HOOKS.md` - Complete implementation guide (9 hook types, examples, best practices)
  - `docs/reference/HOOKS_COMPARISON.md` - Strategic comparison of hook systems (Git, GitHub Actions, Claude Code, pre-commit)
  - `docs/reference/HOOK_SOLUTIONS_FOR_ALL_ISSUES.md` - Analysis of how to prevent all 13 ai-process issues using hooks
- Updated `.claude/CLAUDE.md` with "Claude Code Hooks" section documenting active hooks
- Updated prevention scripts in issues #37 and #39 to check for hook implementation

### Fixed

- Improved `tests/test_hooks.sh` to avoid branch switching that caused hooks to disappear
  - Previous version tried to switch to main to test blocking, but hooks only exist on feature branch
  - New approach tests hooks on current branch without switching
  - Known issue: Test 2 hangs due to command substitution + nested quotes (#47)

### Changed

- Migrated issue #29 (version sync) to v0.6.3 milestone for release automation
- Current version: v0.6.2 (Claude Code Hooks)

## [0.6.1] - 2025-10-20

### Fixed

- **Critical bug: Project review date functionality**
  - Fixed `last_reviewed` parameter setting wrong OmniFocus property
  - Was setting "next review date", now correctly sets "last review date"
  - Added `next_review_date` parameter for explicit override of calculated review dates
  - Both single (`update_project`) and batch (`update_projects`) functions support both parameters
  - Tests: Added 2 new tests for review date functionality (458 total tests)

### Changed

- **Renamed omnifocus_client.py → omnifocus_connector.py**
  - Renamed module file: `omnifocus_client.py` → `omnifocus_connector.py`
  - Renamed class: `OmniFocusClient` → `OmniFocusConnector`
  - Updated all imports and references across codebase (34+ files)
  - **Rationale**: "Connector" is industry-standard terminology for system integrations
  - **Migration**: Update imports in your code:
    ```python
    # Old
    from omnifocus_mcp.omnifocus_client import OmniFocusClient

    # New
    from omnifocus_mcp.omnifocus_connector import OmniFocusConnector
    ```
  - **Impact**: No functionality changes, purely naming clarity

### Documentation

- Added comprehensive README files to all documentation subdirectories
  - `docs/archive/legacy/README.md` - Explains pre-v0.5.0 documentation
  - `docs/archive/planning/README.md` - Documents v0.6.0 API redesign planning phase
  - `docs/reference/README.md` - Technical reference navigation guide
  - `docs/guides/README.md` - Developer guide navigation and quick start
- Updated ROADMAP.md with accurate bug documentation for `last_reviewed` parameter
  - Documented that `last_reviewed` actually sets next review date (not last reviewed)
  - Added "What v0.6.0 Already Handles" section with comprehensive code examples
  - Removed 12+ outdated items already implemented in v0.6.0
  - Restructured into clear categories: Bug Fixes, Design Review, Research
- Moved ROADMAP_REVIEW_2025-10-19.md to docs/archive/planning/

### Tests

- All 333 tests passing with renamed module

## [0.6.0] - 2025-10-18

### Changed - BREAKING

- **Major API Redesign** - Consolidated 40+ functions down to 16 core functions for optimal MCP tool calling
  - **Comprehensive update functions** - All field updates now go through unified `update_task()` and `update_project()` functions
  - **Batch-safe operations** - Separate single/batch update functions prevent accidentally giving multiple items the same name
  - **Enhanced read functions** - `get_tasks()` and `get_projects()` now support direct ID lookup and full note retrieval
  - **Removed 26 deprecated functions** - See migration guide below

- **Removed Functions** (all functionality preserved in new API):
  - **Projects**: `get_project()`, `set_project_status()`, `drop_project()`, `drop_projects()`, `get_stalled_projects()`, `get_projects_due_for_review()`, `set_review_interval()`, `mark_project_reviewed()`
  - **Tasks**: `get_task()`, `get_subtasks()`, `add_task()`, `complete_task()`, `delete_task()`, `move_task()`, `drop_tasks()`, `create_inbox_task()`, `get_inbox_tasks()`, `search_tasks()`, `set_parent_task()`, `set_estimated_minutes()`, `add_tag_to_task()`
  - **Batch operations**: `complete_tasks()`, `move_tasks()`, `add_tag_to_tasks()`, `remove_tag_from_tasks()`
  - **Notes**: `add_note()`, `get_note()`

- **Migration Guide**:
  ```python
  # Projects
  get_project(id) → get_projects(project_id=id)[0]
  set_project_status(id, "on_hold") → update_project(id, status="on_hold")
  drop_project(id) → update_project(id, status="dropped")
  set_review_interval(id, 14) → update_project(id, review_interval_weeks=2)
  mark_project_reviewed(id) → update_project(id, last_reviewed="now")

  # Tasks
  get_task(id) → get_tasks(task_id=id)[0]
  get_subtasks(parent_id) → get_tasks(parent_task_id=parent_id)
  add_task(name, ...) → create_task(task_name=name, ...)
  complete_task(id) → update_task(id, completed=True)
  delete_task(id) → delete_tasks(id)
  move_task(id, proj_id) → update_task(id, project_id=proj_id)
  drop_tasks([ids]) → update_tasks([ids], status="dropped")
  set_estimated_minutes(id, 30) → update_task(id, estimated_minutes=30)
  add_tag_to_task(id, "urgent") → update_task(id, tags=["urgent"])

  # Batch operations
  complete_tasks([ids]) → update_tasks([ids], completed=True)
  move_tasks([ids], proj_id) → update_tasks([ids], project_id=proj_id)

  # Notes
  add_note(id, note, type) → update_task/update_project(id, note=note)
  get_note(id, type) → get_tasks/get_projects(id, include_full_notes=True)
  ```

### Added

- **Enhanced `update_project()`** - Comprehensive single project updates
  - All fields in one call: `project_name`, `note`, `folder_path`, `sequential`, `status`, `review_interval_weeks`, `last_reviewed`
  - Returns structured dict: `{success, project_id, updated_fields, error}`
  - Consolidates 8 specialized functions into one

- **New `update_projects()`** - Batch update multiple projects
  - Accepts single ID or list: `Union[str, list[str]]`
  - Safe fields only: `folder_path`, `sequential`, `status`, `review_interval_weeks`, `last_reviewed`
  - Excludes `project_name` and `note` (require unique values)
  - Returns: `{updated_count, failed_count, updated_ids, failures}`

- **Enhanced `update_task()`** - Comprehensive single task updates
  - 15+ fields in one call: `task_name`, `note`, `project_id`, `completed`, `flagged`, `due_date`, `defer_date`, `estimated_minutes`, `tags`, `status`, etc.
  - Returns structured dict: `{success, task_id, updated_fields, error}`
  - Consolidates 10+ specialized functions into one

- **New `update_tasks()`** - Batch update multiple tasks
  - Accepts single ID or list: `Union[str, list[str]]`
  - Safe fields only: `project_id`, `completed`, `flagged`, `due_date`, `defer_date`, `estimated_minutes`, `tags`, `status`, etc.
  - Excludes `task_name` and `note` (require unique values)
  - Returns: `{updated_count, failed_count, updated_ids, failures}`

- **Enhanced `get_tasks()`** - Added 3 consolidation parameters
  - `task_id` - Get single task directly: `get_tasks(task_id="abc123")`
  - `parent_task_id` - Get subtasks: `get_tasks(parent_task_id="parent-id")`
  - `include_full_notes` - Get complete notes instead of truncated

- **Enhanced `get_projects()`** - Added 2 consolidation parameters
  - `project_id` - Get single project directly: `get_projects(project_id="xyz789")`
  - `include_full_notes` - Get complete notes instead of truncated

- **`create_project()` enhancement** - Added `review_interval_weeks` parameter for setting GTD review cycles when creating projects

### Fixed

- **Parameter naming consistency** - `update_project()` uses `project_name` not `name` (matches `create_project`)
- **Test coverage** - 333 tests passing (100% pass rate), extensive test cleanup for deprecated functions
- **Type safety** - All update functions use proper Enum types with string fallback for MCP compatibility
- **Database safety bug** - Fixed DESTRUCTIVE_OPERATIONS set to include new function names (`create_task`, `update_task`, etc.)

### Removed

- Deleted 4 deprecated test files (search_tasks, get_subtasks, stalled_projects, task_estimated_minutes)
- Removed 1,600+ lines of deprecated test code
- Cleaned up 32 deprecated server test methods

### Documentation

- Updated API_REFERENCE.md with implementation status
- Created comprehensive API redesign plan (docs/API_REDESIGN_PLAN.md)
- Updated ARCHITECTURE.md with design rationale
- Enhanced TESTING.md with coverage details
- See `docs/migration/v0.6.md` for detailed migration guide

## [0.5.0] - 2025-10-09

### Changed - BREAKING
- **Tool Consolidation** - Reduced from 38 to 36 tools by eliminating redundant search wrappers
  - **Removed `search_projects()`** - Use `get_projects(query="...")` instead
  - **Removed `get_inbox_tasks()`** - Use `get_tasks(inbox_only=True)` instead
  - **Enhanced `get_projects()`** - Added `query` parameter for text search
  - **Enhanced `get_tasks()`** - Added `query` and `inbox_only` parameters
  - All 378 tests updated and passing
- **Safety Guards Removed from Production** - No longer block production database operations
  - Production mode (default): All operations allowed without configuration
  - Test mode (when `OMNIFOCUS_TEST_MODE=true`): Verifies correct test database is open
  - Removed 16 obsolete tests that enforced blocking behavior
  - Test mode still requires `OMNIFOCUS_TEST_DATABASE` to be set for safety

### Added
- **Powerful Query Combinations** - New parameters enable advanced filtering:
  - `get_tasks(query="mortgage", due_relative="this_week")` - Search with date filters
  - `get_tasks(query="urgent", inbox_only=True, flagged_only=True)` - Complex inbox queries
  - `get_projects(query="budget", status="active")` - Project search with filters

### Fixed
- **Critical: AppleScript variable naming conflict** in `get_tasks()` repetition info extraction
  - Variables `recurrence` and `repetitionMethod` conflicted with OmniFocus property names
  - Caused ALL tasks to be skipped with error: "Can't set recurrence of document 1 to ''"
  - Renamed to `recurrenceStr` and `repetitionMethodStr` to avoid conflicts
  - Fixed `get_tasks()` returning 0 results for all queries
- **Complete recurring tasks** - Use `mark complete` instead of setting `completed` property
  - Fixed error: "Can't set completed of inbox task to true" (-10006)
  - Now works correctly with recurring tasks and inbox tasks
  - Updated both `complete_task()` and `complete_tasks()` methods
- **Second AppleScript syntax error** in `get_tasks()` overdue filter
  - Fixed typo at line 1586: `eliftaskDueDate` → `else if taskDueDate`
  - Caused `get_tasks()` to return 0 results when overdue logic was evaluated
- **Performance: Added timeout parameter** to prevent infinite hangs
  - `run_applescript()` now accepts timeout parameter (default 60s, max 300s)
  - `get_tasks()` timeout defaults to 120s (handles ~738 tasks in 13-17s)
  - `get_projects()` timeout defaults to 90s

### Documentation
- Updated README with consolidated API usage examples
- Added tool consolidation analysis document
- Updated all test documentation

## [0.4.0] - 2025-10-08

### Added
- **Phase 7: Project Intelligence** - Comprehensive project analytics and management
  - `set_project_status()` - Change project status (active/on_hold/done)
  - `get_stalled_projects()` - Find projects with no recent activity
  - Project activity tracking (modificationDate, lastActivityDate)
  - Enhanced `get_project_aggregates()` with task distribution analysis
    - dueTodayCount, dueThisWeekCount, noDueDateCount fields
- **AppleScript Validation Tests** - Automated syntax checking to prevent typos
  - 3 new tests for common typo patterns, block structure, and tell block balancing
- **Tool Documentation Improvements** - 100% Returns documentation coverage
  - All 38 MCP tools now document their return format
  - Enhanced tool descriptions for better Claude Desktop selection
  - Clear differentiation between get_* and search_* patterns
  - Performance notes on batch operations

### Fixed
- **Critical AppleScript syntax error** in `get_project()` review interval code
  - Fixed typo: `elifintervalDays` → `else if intervalDays`
  - Would have caused runtime failures for projects with 1-6 day review intervals

### Changed
- **Code Refactoring** - Eliminated duplication and improved maintainability
  - Extracted `_format_task()` and `_format_project()` helper functions
  - Reduced code by 27 lines while maintaining all functionality
  - Removed redundant empty list checks (more Pythonic)
  - All 393 tests still passing

### Documentation
- Created comprehensive tool documentation audit
- Added analysis script for ongoing tool documentation quality checks
- Updated all tool descriptions for clarity

## [0.3.0] - 2025-09-XX

### Added
- Phase 2: Additional Primitives (13 new tools)
- Batch operations (complete_tasks, delete_tasks, move_tasks, etc.)
- Advanced filtering (available_only, overdue, tag filtering)
- Folder management
- Task hierarchy support
- Project review system
- Time estimation
- Perspectives support

### Changed
- Migrated to FastMCP framework (38% code reduction)
- Enhanced test coverage to 302 tests

## [0.2.0] - 2025-08-XX

### Added
- Phase 1: Foundation
- Core task management (add, update, complete)
- Project management (create, get, search)
- Tag support
- Inbox operations
- Multi-layer database safety system

## [0.1.0] - Initial Release

- Basic OmniFocus integration via AppleScript
- MCP protocol implementation
- Initial test suite
