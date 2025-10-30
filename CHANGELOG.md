# Changelog

All notable changes to the OmniFocus MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
