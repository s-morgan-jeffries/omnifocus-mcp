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

## Next Steps

For the MCP server:
1. ✅ Test with Claude Desktop
2. ✅ Documentation updates
3. ⏭️ Potential enhancements (see MCP_ROADMAP.md)

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
