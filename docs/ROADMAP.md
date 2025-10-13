# OmniFocus MCP Server: Development Roadmap

## Status: Phase 1 & 2 Complete ✅

**Note**: This roadmap has been revised. The original vision included email forwarding, calendar integration, and other application-layer features. However, these don't belong in an MCP server - they should be separate services or applications that *use* the MCP server.

**Phase 2 (Additional Primitives) is now COMPLETE**, bringing the server to **25 comprehensive MCP tools** covering all core OmniFocus functionality.

---

## Vision (Original)

Transform OmniFocus from a manual task manager into an intelligent AI-powered productivity system that bridges the gap between unstructured information (emails, meetings, conversations) and structured GTD workflows.

**Revised Vision**: Provide a clean, complete, well-tested MCP server that exposes all OmniFocus primitives to AI assistants like Claude.

---

## Phase 1: Foundation - COMPLETE ✅

### Goal
Enable basic AI-powered task management with proper OmniFocus structure

### Status: **COMPLETE**

All Phase 1 deliverables have been implemented and tested.

---

### Week 1-2: Enhanced Task API - ✅ COMPLETE

**What We Built:**
```python
# Full GTD support implemented
add_task(
    project_id="xyz",
    task_name="Call client about Q3 results",
    note="Discuss revenue targets and next steps",
    tags=["@calls", "@priority-high"],
    due_date="2025-10-15",
    defer_date="2025-10-14",
    flagged=True
)
```

**Deliverables:**
- ✅ Updated omnifocus_client.py with full property support
- ✅ Extended AppleScript to handle tags, dates, flags
- ✅ Added validation and error handling
- ✅ Wrote comprehensive tests (79 unit tests for client)
- ✅ Documentation with examples

**Success Criteria:**
- ✅ All GTD task properties supported
- ✅ 100% AppleScript success rate
- ✅ <1 second task creation time

---

### Week 3-4: Task Query & Operations - ✅ COMPLETE

**What We Built:**
```python
# Get tasks with filtering
tasks = get_tasks(
    project_id="xyz",
    flagged_only=True,
    include_completed=False
)

# Task operations
update_task(task_id, due_date="2025-10-20", flagged=True)
complete_task(task_id)
```

**Deliverables:**
- ✅ Implemented get_tasks with filtering
- ✅ Added update_task and complete_task
- ✅ Comprehensive filtering options
- ✅ Tests covering all query types (45 tests)

**Success Criteria:**
- ✅ Support all common filtering patterns
- ✅ Accurate task status detection
- ✅ Fast query performance

---

### Week 5-6: Project Management - ✅ COMPLETE

**What We Built:**
```python
# Create new project
create_project(
    name="Acme Corp - Website Redesign",
    folder_path="Clients > Active",
    note="8-week timeline, Team: Sarah (design), Mike (dev)",
    sequential=False  # parallel project
)
```

**Deliverables:**
- ✅ Implemented create_project
- ✅ Added get_project and search_projects
- ✅ Folder hierarchy management
- ✅ Tests and documentation (11 tests for create_project)

**Success Criteria:**
- ✅ Create complex project structures
- ✅ Accurate folder path resolution
- ✅ Proper sequential/parallel project types

---

### Week 7-8: Email Integration MVP - ❌ OUT OF SCOPE

**Status**: Not implemented - doesn't belong in MCP server.

**Reasoning**: Email forwarding is application logic, not an MCP primitive. This should be:
- A separate service that calls the MCP server, OR
- Handled by Claude Desktop with the user forwarding emails to Claude manually

The MCP server provides the primitives (`add_task`, `create_inbox_task`, etc.) but shouldn't run email receivers or parsers.

---

## Phase 1 Success Metrics - ✅ ACHIEVED

**Technical:**
- ✅ All core tools implemented and tested
- ✅ <1 second response time for operations
- ✅ >95% API success rate (mocked tests)
- ✅ Zero data loss bugs
- ✅ 210 passing tests with comprehensive coverage
- ✅ Multi-layer database safety system

**Architecture:**
- ✅ Migrated to FastMCP (38% code reduction)
- ✅ Clean decorator-based tool definitions
- ✅ Type-safe with auto-generated schemas
- ✅ Production-ready error handling

---

## Phase 2-4: Intelligence, Automation, Optimization - ⚠️ RECONSIDERED

**Status**: These phases mixed MCP primitives with application logic.

### What Belongs in MCP Server:
- ✅ **Already implemented** - All OmniFocus primitives complete

### What Doesn't Belong in MCP Server:
- ❌ Email processing
- ❌ Calendar integration
- ❌ Meeting transcription
- ❌ Analytics/dashboards
- ❌ Template systems (can be handled by prompts)
- ❌ GitHub/Jira integration (separate MCP servers)
- ❌ Time tracking (separate service)
- ❌ Voice interface
- ❌ Pattern learning

**These should be:**
1. **Separate services** that use the MCP server as a client
2. **Separate MCP servers** (e.g., calendar-mcp, github-mcp)
3. **Claude Desktop workflows** using the existing tools
4. **Prompt engineering** (templates, patterns)

---

## Phase 2: Additional Primitives - ✅ COMPLETE

### Goal
Expand MCP server to cover all essential OmniFocus primitives beyond the Phase 1 basics.

### Status: **COMPLETE** (v0.3.0)

All Phase 2 deliverables have been implemented and tested.

**What We Built:**
- ✅ Task deletion and management (delete, move, drop)
- ✅ Advanced task queries (available_only, overdue, tag filtering)
- ✅ Folder management (get, create)
- ✅ Task hierarchy (parent/child relationships)
- ✅ Project review system (GTD methodology)
- ✅ Time estimation
- ✅ Perspectives (OmniFocus Pro feature)

**Deliverables:**
- ✅ 13 new primitives implemented in omnifocus_client.py
- ✅ Enhanced existing tools (get_tasks with advanced filtering)
- ✅ 64 additional tests (143 total client tests)
- ✅ 30 FastMCP server tests (0% → 73% coverage)
- ✅ Updated all documentation

**Success Criteria:**
- ✅ All tier 1 & 2 primitives covered
- ✅ 88% overall code coverage
- ✅ Production-ready test suite (302 passing tests)

---

## Current State Summary

### Implemented (25 MCP Tools):

**Projects (4 tools):**
- ✅ `get_projects` - List all active projects
- ✅ `search_projects` - Search by name/note/folder
- ✅ `create_project` - Create new project with folder placement
- ✅ `delete_project` - Delete a project

**Tasks (9 tools):**
- ✅ `get_tasks` - Query tasks with advanced filtering (available, overdue, by tag)
- ✅ `add_task` - Create task with full properties
- ✅ `update_task` - Modify existing task
- ✅ `complete_task` - Mark task complete
- ✅ `delete_task` - Delete a task
- ✅ `move_task` - Move task between projects or to inbox
- ✅ `drop_task` - Remove task from project
- ✅ `set_parent_task` - Create task hierarchies
- ✅ `set_estimated_minutes` - Set time estimates

**Inbox (2 tools):**
- ✅ `get_inbox_tasks` - List inbox items
- ✅ `create_inbox_task` - Quick capture to inbox

**Tags (2 tools):**
- ✅ `get_tags` - List all tags
- ✅ `add_tag_to_task` - Tag a task

**Folders (2 tools):**
- ✅ `get_folders` - List folder hierarchy
- ✅ `create_folder` - Create folders with parent paths

**Project Review (3 tools):**
- ✅ `set_review_interval` - Configure review frequency
- ✅ `mark_project_reviewed` - Mark as reviewed
- ✅ `get_projects_due_for_review` - Find projects needing review

**Perspectives (2 tools):**
- ✅ `get_perspectives` - List custom perspectives
- ✅ `switch_perspective` - Change active perspective

**Notes (1 tool):**
- ✅ `add_note` - Append to project notes

### Test Coverage:

- **302 passing tests**
- 143 unit tests (omnifocus_client.py)
- 79 unit tests (legacy server.py)
- 30 unit tests (FastMCP server_fastmcp.py)
- 40 integration tests (end-to-end workflows)
- 13 safety guard tests
- 13 real OmniFocus tests (optional, require setup)
- **Execution time**: ~1.01s
- **Code coverage**: 88% (970 statements)
  - omnifocus_client.py: 97%
  - server_fastmcp.py: 73%
  - server.py: 96%

### Database Safety:

- ✅ Multi-layer safety system
- ✅ Environment variable checks
- ✅ Database name whitelist
- ✅ Runtime verification via AppleScript
- ✅ All destructive operations protected

---

## Technology Stack (Current)

### Backend
- **Language:** Python 3.10+
- **Framework:** FastMCP 2.0
- **OmniFocus API:** AppleScript bridge
- **Testing:** pytest with comprehensive mocking

### Not Implemented (Out of Scope)
- ~~Email integration~~
- ~~Calendar integration~~
- ~~Meeting transcription~~
- ~~Dev tool integrations~~
- ~~Time tracking~~
- ~~Cloud deployment~~

### Deployment
- **Current:** Local-only (user's machine via Claude Desktop)
- **Future:** Could be used by other MCP clients

---

## Success Criteria Summary

### Phase 1 (Foundation) - ✅ COMPLETE
- ✅ 100% GTD task properties supported
- ✅ Core OmniFocus primitives (12 tools)
- ✅ Database safety system
- ✅ Migrated to FastMCP

### Phase 2 (Additional Primitives) - ✅ COMPLETE
- ✅ All essential OmniFocus primitives (25 tools total)
- ✅ Advanced filtering and queries
- ✅ Project review (GTD)
- ✅ Perspectives support
- ✅ Comprehensive test coverage (302 tests, 88% coverage)
- ✅ FastMCP server tests (73% coverage)

### Future Phases - ⚠️ RECONSIDERED
These belong in separate services/servers, not the OmniFocus MCP server.

---

## Phase 3: Refinement & Polish - 🚧 IN PROGRESS

### v0.5.0 (October 2025) - ✅ COMPLETE

**Focus:** Claude Desktop compatibility improvements and API refinements

**Implemented:**
- ✅ Added `update_project()` tool (name, note, sequential)
- ✅ Fixed `get_project()` to include `sequential` field
- ✅ Fixed Optional[bool] parameter validation issues
  - `update_task(flagged)` now accepts "true"/"false" strings
  - `update_project(sequential)` now accepts "true"/"false" strings
  - Workaround for FastMCP known issue with Optional[bool] parameters
- ✅ Added plain text note warnings to all note-related tools
  - Documented that OmniFocus automation APIs only support plain text
  - Warned that updating notes removes rich text formatting
- ✅ Added comprehensive tests
  - 5 integration tests for update_project
  - 8 unit tests for string boolean parameter handling
  - 1 integration test for flag toggling
- ✅ Migrated TDD practices from hooks to CLAUDE.md
- ✅ Added availability status fields (`available`, `numberOfAvailableTasks`)
  - Clarified why blocked tasks appear in Available filter
- ✅ **Completed AppleScript audit** - Found all needed timestamps! (see `docs/APPLESCRIPT_AUDIT_FINDINGS.md`)
- ✅ **Added timestamp fields to all project/task methods**:
  - Projects: `creationDate`, `modificationDate`, `completionDate`, `droppedDate`
  - Tasks: `creationDate`, `modificationDate`, `completionDate`, `droppedDate`
  - All timestamps as ISO 8601 strings or null
- ✅ **Fixed tags to be arrays instead of strings**:
  - Tasks now return `tags: ["tag1", "tag2"]` instead of `"tag1, tag2"`
  - Proper JSON arrays for filtering and organization
- ✅ **Made `get_stalled_projects()` configurable**:
  - Added `min_task_count` parameter for filtering
  - Returns `lastActivityDate`, `daysInactive`, and `taskCount`
  - Filters and sorts by inactivity (most stale first)

**Known Limitations:**
- ❌ Cannot retrieve formatted/rich text notes (OmniFocus API limitation)
  - AppleScript only exposes plain text
  - OmniAutomation has RTF access but cannot be called externally with result retrieval

**Current Tool Count:** 26 MCP tools

**Test Coverage:** 392 passing tests (up from 302)

### Upcoming Work

**High Priority - Bug Fixes:**
- 🐛 **mark_project_reviewed() bug** (USER REPORTED)
  - **Issue**: Currently sets `next review date` to today instead of marking as reviewed
  - **Correct behavior**: Should set `last review date` to today, which triggers OmniFocus to calculate next review date based on review interval
  - **Fix**: Change AppleScript from `set next review date` to `set last review date`
  - **Impact**: GTD weekly review workflow broken - projects not properly marked as reviewed
  - **Priority**: HIGH - User actively using this for project cleanup workflow

**Code Quality - Clarity Improvements:**
- 📝 **Rename omnifocus_client.py to omnifocus_connector.py**
  - **Current**: `omnifocus_client.py` / `OmniFocusClient` class
  - **Proposed**: `omnifocus_connector.py` / `OmniFocusConnector` class
  - **Rationale**: "Connector" is industry-standard terminology for system integrations
  - **Benefits**:
    - Clearer architecture: "MCP server uses OmniFocus connector"
    - Avoids client/server confusion (server calling client sounds backwards)
    - Matches terminology used in data pipelines, ETL tools, integration platforms
  - **Scope**: Rename file, class, all references, update documentation
  - **Impact**: LOW - No functionality changes, better clarity for maintainers

**High Priority - Project Cleanup Use Case (IN PROGRESS):**
- 🎯 **Project Cleanup & Reorganization Assistant** (USE CASE #16)
  - **Status**: Core features COMPLETE ✅
  - ✅ Timestamps on all projects/tasks
  - ✅ Tags as arrays on tasks
  - ✅ Configurable stalled project detection
  - ⏳ **Remaining**: Project reorganization operations
    - `move_project(project_id, folder_path)` - Move project to different folder (MISSING PRIMITIVE)
    - `move_projects(project_ids, folder_path)` - Batch move projects to folder
    - `merge_projects(source_ids, target_id)` - Merge multiple projects
    - `split_project(project_id, task_ids, new_project_name)` - Split off tasks
    - `archive_projects(project_ids)` - Batch archive/complete
  - **Impact**: Very High for power users with mature databases
  - **See**: `docs/USE_CASES.md` for detailed workflow

**Under Consideration:**
- **Batch operations** (systematic expansion for efficiency):
  - **Currently implemented**:
    - ✅ Tasks: complete_tasks, move_tasks, drop_tasks, delete_tasks, add_tag_to_tasks, remove_tag_from_tasks
    - ✅ Projects: delete_projects, drop_projects
  - **Missing - High Priority**:
    - ❌ `mark_projects_reviewed(project_ids)` - Batch mark projects as reviewed (GTD workflow)
    - ❌ `update_tasks(task_ids, properties)` - Batch update task properties
    - ❌ `update_projects(project_ids, properties)` - Batch update project properties
    - ❌ `set_project_statuses(project_ids, status)` - Batch change project status
  - **Missing - Medium Priority**:
    - ❌ `set_review_intervals(project_ids, interval)` - Batch set review intervals
    - ❌ `set_estimated_minutes_batch(task_ids, minutes)` - Batch time estimates
    - ❌ `set_parent_tasks(task_ids, parent_task_id)` - Batch reparenting
  - **Rationale**: Reduce round-trip overhead for bulk operations, especially important for project cleanup/reorganization workflows
- Additional filtering options based on user feedback
- **UI navigation/focus commands**:
  - `show_project(project_id)` - Focus on a project in the OmniFocus window
  - `show_task(task_id)` - Focus on a task in the OmniFocus window
  - **Implementation**: Uses AppleScript `set focus of front document window to item`
  - **Rationale**: "Jump to this item" workflow after querying/searching
  - **Verified**: AppleScript command works - tested successfully
- **Task creation improvements**:
  - Add `parent_task_id` parameter to `add_task()` - Create subtasks directly without needing two-step process
  - **Current workaround**: Use `add_task()` then `set_parent_task()`
  - **Rationale**: More efficient workflow for creating task hierarchies
  - **Challenge**: AppleScript may require task to exist before setting parent (need to test)
- **Attachments** (user priority - document management):
  - `get_attachments(item_id, item_type="task")` - List attachments on tasks/projects
  - `add_attachment(item_id, file_path, item_type="task")` - Attach files
  - `remove_attachment(item_id, attachment_name, item_type="task")` - Remove attachments
  - Add `attachmentCount` field to task/project responses
  - **Rationale**: "Attach this PDF to my 'File taxes' task" workflow
  - **Challenge**: Need to investigate how MCP/Claude Desktop handles local file paths
- **Archive access** (challenging - requires direct SQLite access):
  - `search_archive(query: str)` - Search archived tasks/projects
  - `get_archived_project(project_id: str)` - Get archived project details
  - `get_archived_task(task_id: str)` - Get archived task details
  - **Rationale**: "Find that project I completed last year" workflow
  - **Challenge**: Archive is separate SQLite database (`ArchiveDatabase.db`), not accessible via AppleScript
  - **Research needed**: Reverse-engineer archive schema, ensure read-only safety, handle OF3/OF4 differences
- **Note management improvements** (open design question):
  - Should we add dedicated `set_note()` function (or `update_note()`) for explicit note-only updates?
  - Single function for both tasks and projects: `set_note(item_id, note, item_type="task")`?
  - Should note parameter remain in `update_task()` and `update_project()` for convenience?
  - Alternative: `append_note()` for non-destructive incremental updates?
  - **Rationale**: Updating notes is destructive (removes formatting), should be more intentional
  - **User workflow**: Generate Markdown notes in Claude, copy/paste into OmniFocus manually

---

## Next Steps

For the MCP server:
1. ✅ Test with Claude Desktop
2. ✅ Documentation updates
3. ⏳ Complete property audit
4. ⏭️ Additional enhancements based on usage patterns

For application-layer features:
1. Build separate services that use this MCP server
2. Or use Claude Desktop with this server + manual workflows
3. Or create separate MCP servers for other systems (calendar, email, etc.)

---

## Open Questions (Resolved)

1. **Pricing Model:** Free, open source MCP server
2. **OmniGroup Relationship:** Independent tool
3. **Data Privacy:** Local-only, no cloud processing
4. **Platform Support:** macOS only (OmniFocus limitation)
5. **Multi-user:** Individual-focused (as OmniFocus is)

---

*This roadmap reflects the completed Phase 1 implementation. See [MCP_ROADMAP.md](MCP_ROADMAP.md) for future MCP server enhancements.*
