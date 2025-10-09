# Changelog

All notable changes to the OmniFocus MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
