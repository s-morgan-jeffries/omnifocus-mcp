# Changelog

All notable changes to the OmniFocus MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
