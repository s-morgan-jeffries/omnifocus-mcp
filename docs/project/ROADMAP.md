# OmniFocus MCP Server: Development Roadmap

## Status: Phase 3 (API Redesign) Complete ✅

**Current Version:** v0.6.1 (October 2025)

**Project Status:** Maintenance mode - Core MCP server is feature-complete with 16 comprehensive tools covering all OmniFocus primitives.

**Latest:** v0.6.1 renamed `omnifocus_client` → `omnifocus_connector` for industry-standard terminology.

**Note**: This roadmap has been revised. The original vision included email forwarding, calendar integration, and other application-layer features. However, these don't belong in an MCP server - they should be separate services or applications that *use* the MCP server.

---

## Vision

**Original Vision**: Transform OmniFocus from a manual task manager into an intelligent AI-powered productivity system.

**Revised Vision**: Provide a clean, complete, well-tested MCP server that exposes all OmniFocus primitives to AI assistants like Claude.

**Achieved**: ✅ 16 comprehensive MCP tools, 89% test coverage, type-safe API, batch operations, production-ready.

---

## Current State (v0.6.0 - October 2025)

### 🎉 API Redesign Complete - 16 Core MCP Tools

**API Reduction:** 40+ functions → 16 core functions (60% reduction through two consolidations)

**Projects (5 tools):**
- ✅ `create_project` - Create with folder, status, and review interval
- ✅ `get_projects` - Enhanced with `project_id`, `include_full_notes` parameters
- ✅ `update_project` - Comprehensive single-project update (all fields)
- ✅ `update_projects` - Batch update (safe fields, excludes name/note)
- ✅ `delete_projects` - Union type: accepts single ID or list

**Tasks (6 tools):**
- ✅ `create_task` - Project tasks or inbox tasks (project_id=None)
- ✅ `get_tasks` - Enhanced with `task_id`, `parent_task_id`, `include_full_notes` parameters
- ✅ `update_task` - Comprehensive single-task update (all fields)
- ✅ `update_tasks` - Batch update (safe fields, excludes name/note)
- ✅ `delete_tasks` - Union type: accepts single ID or list
- ✅ `reorder_task` - Specialized positioning logic

**Folders (2 tools):**
- ✅ `create_folder` - With optional parent path
- ✅ `get_folders` - Returns folder hierarchy

**Tags (1 tool):**
- ✅ `get_tags` - Returns all available tags

**Perspectives (2 tools):**
- ✅ `get_perspectives` - List custom perspectives
- ✅ `switch_perspective` - Change active perspective

### Test Coverage

**333 passing tests** with 89% overall code coverage. See [../guides/TESTING.md](../guides/TESTING.md) for detailed breakdown.

### Database Safety

- ✅ Multi-layer safety system
- ✅ Environment variable checks
- ✅ Database name whitelist
- ✅ Runtime verification via AppleScript
- ✅ All destructive operations protected

---

## What v0.6.0 Already Handles

Many operations that might seem "missing" are already handled by the comprehensive update and get functions. Here are common patterns:

### Project Operations via update_project()

```python
# Move project to different folder
update_project(project_id, folder_path="Clients > Active")

# ⚠️ BUG: Parameter name is misleading - actually sets NEXT review date, not last reviewed
# See "Upcoming Work - Bug Fixes" section for details
update_project(project_id, last_reviewed="now")  # Despite name, sets next review to today

# Change project status (active/on-hold/done/dropped)
update_project(project_id, status=ProjectStatus.DONE)  # Archives project

# Set review interval
update_project(project_id, review_interval_weeks=2)

# Change project type
update_project(project_id, sequential=True)  # Make sequential

# Update multiple fields at once
update_project(
    project_id,
    folder_path="Archive > 2025",
    status=ProjectStatus.DONE,
    last_reviewed="now"
)
```

### Batch Project Operations via update_projects()

```python
# Move multiple projects to folder
update_projects(project_ids, folder_path="Archive > Q4")

# Archive multiple projects
update_projects(project_ids, status=ProjectStatus.DONE)

# ⚠️ BUG: Sets next review date (batch), not last reviewed (see Bug Fixes section)
update_projects(project_ids, last_reviewed="now")

# Set review interval for multiple projects
update_projects(project_ids, review_interval_weeks=4)

# Combine safe field updates
update_projects(
    project_ids,
    status=ProjectStatus.DONE,
    last_reviewed="now"
)
```

### Task Operations via update_task()

```python
# Complete a task
update_task(task_id, completed=True)

# Flag/unflag a task
update_task(task_id, flagged=True)

# Move task to different project
update_task(task_id, project_id=new_project_id)

# Move task to inbox
update_task(task_id, project_id=None)

# Set task status
update_task(task_id, status=TaskStatus.DROPPED)

# Set parent task (create subtask relationship)
update_task(task_id, parent_task_id=parent_id)

# Set time estimate
update_task(task_id, estimated_minutes=30)

# Update multiple fields at once
update_task(
    task_id,
    due_date="2025-10-25",
    flagged=True,
    estimated_minutes=45,
    tags=["@priority-high", "@calls"]
)
```

### Batch Task Operations via update_tasks()

```python
# Complete multiple tasks
update_tasks(task_ids, completed=True)

# Flag multiple tasks
update_tasks(task_ids, flagged=True)

# Move multiple tasks to project
update_tasks(task_ids, project_id=new_project_id)

# Set status for multiple tasks
update_tasks(task_ids, status=TaskStatus.DROPPED)

# Add tags to multiple tasks
update_tasks(task_ids, tags=["@review", "@urgent"])

# Set parent for multiple tasks
update_tasks(task_ids, parent_task_id=parent_id)

# Combine safe field updates
update_tasks(
    task_ids,
    flagged=True,
    estimated_minutes=30,
    tags=["@batch-processed"]
)
```

### Query Operations via get_tasks() and get_projects()

```python
# Get single task (replaces get_task)
get_tasks(task_id="task-123")

# Get single project (replaces get_project)
get_projects(project_id="proj-456")

# Get subtasks (replaces get_subtasks)
get_tasks(parent_task_id="parent-task-id")

# Get tasks in project
get_tasks(project_id="proj-456")

# Get full notes (replaces get_note)
get_tasks(task_id="task-123", include_full_notes=True)
get_projects(project_id="proj-456", include_full_notes=True)

# Get available tasks only
get_tasks(available_only=True)

# Get flagged tasks
get_tasks(flagged_only=True)

# Combine filters
get_tasks(
    project_id="proj-456",
    flagged_only=True,
    available_only=True
)
```

### Why This Design?

**Minimizes Tool Call Overhead:**
- Update multiple fields in one call instead of multiple calls
- Example: Old way required 3 calls (flag_task, set_due_date, add_tag), new way needs 1 call (update_task)

**Type Safety:**
- Enums prevent invalid status values
- Structured returns make parsing consistent
- Optional parameters with sensible defaults

**Batch Safety:**
- Separate batch functions prevent accidentally giving multiple items the same name
- `update_tasks()` excludes name/note (require unique values)
- `update_task()` includes all fields (safe for single item)

---

## Completed Phases

### Phase 1: Foundation ✅ COMPLETE

All core OmniFocus primitives (tasks, projects, folders, tags) implemented with comprehensive test coverage.

**Deliverables:**
- ✅ Full GTD task/project property support
- ✅ Database safety system
- ✅ Migrated to FastMCP
- ✅ 210 passing tests

### Phase 2: Additional Primitives ✅ COMPLETE

Expanded coverage to include advanced OmniFocus features (perspectives, project review, time estimates, task hierarchy).

**Deliverables:**
- ✅ 13 additional primitives
- ✅ Advanced filtering and queries
- ✅ Project review system (GTD)
- ✅ Perspectives support
- ✅ 302 passing tests (88% coverage)

### Phase 3: API Redesign ✅ COMPLETE

Major consolidation to optimize for MCP tool calling efficiency.

**v0.6.0 Achievements:**
- ✅ Reduced API surface: 40+ → 16 functions
- ✅ Comprehensive update functions handle all field changes
- ✅ Batch operations for efficiency
- ✅ Type-safe enums and structured returns
- ✅ Removed 26 deprecated functions
- ✅ 333 passing tests (89% coverage)

---

## Upcoming Work

**Status:** These items are logged for future consideration but not actively planned. The v0.6.0 API is feature-complete and stable.

### Priority 1 - Automation Improvements (NEXT SESSION)

**🤖 Recursive Self-Improvement System Enhancements**

Based on research completed 2025-10-20, the following automation improvements are planned for the next session:

**A. Claude Code Hooks Implementation** (30 min, 10x ROI - HIGHEST PRIORITY)
- **Problem:** Claude can easily ignore instructions, relying on memory alone
- **Solution:** Automatic enforcement via `.claude/hooks.json`
- **Implementation:**
  ```json
  {
    "pre_tool_use": {
      "Edit": "./hooks/check_tests_exist.sh",
      "Write": "./hooks/check_tests_exist.sh",
      "Bash": "./hooks/check_git_push_monitoring.sh"
    }
  }
  ```
- **Impact:** Blocks edits/writes without tests, enforces CI monitoring after pushes
- **Why it matters:** Prevents MISTAKE-009 (missing tests) and MISTAKE-011 (no CI monitoring)

**B. GitHub Issues Migration** (4-5 hours) - **DIRECT CUTOVER**
- **Problem:** MISTAKES.md is invisible to user, easy for Claude to ignore
- **Solution:** Complete migration to GitHub Issues (no hybrid period)
- **Decision:** Direct cutover is the right approach
  - Everything MISTAKES.md does can be rebuilt with GitHub CLI (`gh`)
  - Speed advantage of grep is negligible (~200ms API call vs instant)
  - Offline access not needed (always online when using Claude Code)
  - GitHub Issues advantages far outweigh markdown benefits
- **Implementation:**
  - One-time migration script (MISTAKES.md → GitHub Issues with labels)
  - Rebuild check_recurrence.sh using `gh issue list` and `gh issue comment`
  - Update all documentation references
  - Delete MISTAKES.md after verification
- **Benefits:**
  - User can see open issues without asking Claude
  - Labels, milestones, and grouping for better organization
  - Native GitHub automation (Actions, notifications)
  - Standard workflow (not reinventing the wheel)
  - Programmatic access via GitHub CLI (same as grep, just via API)
- **What we're rebuilding:**
  - Recurrence tracking: `gh issue comment` for recurrence detection
  - Statistics: `gh issue list --json | jq` for aggregation
  - Prevention docs: Same markdown, stored in issue body
  - Verification deadlines: Milestones or custom fields

**Additional Quick Wins** (identified by research, defer until after A & B):
- Pre-push git hooks (15 min) - Block pushes until checks pass
- pytest-watcher (10 min) - Continuous test running for instant TDD feedback
- VS Code task integration (20 min) - One-click buttons for common tasks
- MISTAKES.md template automation (10 min) - Script to generate entries

**Research completed:** Three independent agents analyzed current automation gaps. Full reports: [docs/research/2025-10-20-automation-research.md](../research/2025-10-20-automation-research.md)

### Immediate - Bug Fixes

**🐛 Project Review Date Functionality (CRITICAL BUG)**
- **Current bug**: The `last_reviewed` parameter is misnamed and misleading
  - **Actual behavior**: Sets the **next review date**, not the last reviewed date
  - **Code location**: `omnifocus_connector.py:918` - `set next review date of theProject to (current date)`
  - **Impact**: Cannot properly mark projects as reviewed per GTD methodology
  - **User sees**: Projects show future review date instead of being marked as "reviewed today"
- **Required fixes**:
  1. **Fix `last_reviewed` parameter**: Should set "last review date" property in OmniFocus
     - Need to research correct AppleScript property name
     - Test whether OmniFocus auto-calculates next review when last review is set
  2. **Add `next_review_date` parameter**: For explicit next review date setting
     - Should work in both `update_project()` and `update_projects()`
     - Allows manual override of calculated review schedule
  3. **Verify OmniFocus behavior**: Does setting "last review date" trigger auto-calculation?
  4. **Add integration tests**: Verify both parameters set correct OmniFocus properties
- **Priority**: CRITICAL - Blocks GTD weekly review workflow (user-reported)

### Under Investigation - Design Review Needed

These items need design discussion before implementation:

**🤔 Complex Multi-Step Operations**
- `merge_projects(source_ids, target_id)` - Merge multiple projects by moving all tasks
- `split_project(project_id, task_ids, new_project_name)` - Split tasks into new project

**Question:** Are these OmniFocus primitives or application workflows?
- Can be done client-side with existing tools (get_tasks, update_tasks, create_project, delete_projects)
- Should MCP server provide convenience wrappers for multi-step operations?
- Precedent: v0.6.0 philosophy is "expose primitives, not workflows"

**Decision needed before implementation.**

**🤔 UI Navigation**
- `show_project(project_id)` - Focus OmniFocus window on specific project
- `show_task(task_id)` - Focus OmniFocus window on specific task

**Question:** Does UI navigation belong in an MCP server?
- Precedent: `switch_perspective()` exists (UI control)
- AppleScript verified: `set focus of front document window to item` works
- Use case: "Jump to this item" after querying/searching

**Decision needed before implementation.**

### Future Research - Technical Blockers

**🔬 Attachments (File Handling)**
- `get_attachments(item_id, item_type="task")` - List attachments
- `add_attachment(item_id, file_path, item_type="task")` - Attach files
- `remove_attachment(item_id, attachment_name, item_type="task")` - Remove attachments

**Blocker:** How does MCP/Claude Desktop handle local file paths?
- Can MCP tools receive file paths as arguments?
- What's the security model?
- How do file permissions work?

**Research needed:** MCP file operation specification

**🔬 Archive Access (SQLite)**
- `search_archive(query)` - Search archived tasks/projects
- `get_archived_project(project_id)` - Get archived project details
- `get_archived_task(task_id)` - Get archived task details

**Blocker:** Direct SQLite access to `ArchiveDatabase.db` is high-risk
- Archive database structure is undocumented (reverse engineering needed)
- Read-only safety must be guaranteed
- OF3 vs OF4 schema differences
- Corruption risk if not handled correctly

**Research needed:**
- Reverse-engineer archive schema
- Build read-only safety layer
- Test across OmniFocus versions

---

## Out of Scope

These belong in separate services/applications that **use** the MCP server, not **in** the MCP server:

❌ Email forwarding/processing
❌ Calendar integration
❌ Meeting transcription
❌ GitHub/Jira integration (separate MCP servers)
❌ Time tracking (separate service)
❌ Analytics/dashboards (client applications)
❌ Template systems (can be handled by prompts)
❌ Voice interface
❌ Pattern learning/AI features

**These should be:**
1. Separate services that use this MCP server as a client
2. Separate MCP servers (e.g., calendar-mcp, github-mcp)
3. Claude Desktop workflows using existing tools
4. Prompt engineering (templates, patterns)

---

## Technology Stack

### Backend
- **Language:** Python 3.10+
- **Framework:** FastMCP 2.0
- **OmniFocus API:** AppleScript bridge
- **Testing:** pytest with comprehensive mocking and integration tests

### Deployment
- **Current:** Local-only (user's machine via Claude Desktop)
- **Future:** Could be used by other MCP clients

---

## Success Criteria (All Achieved ✅)

### Phase 1 (Foundation) - ✅ COMPLETE
- ✅ 100% GTD task properties supported
- ✅ Core OmniFocus primitives
- ✅ Database safety system
- ✅ Migrated to FastMCP

### Phase 2 (Additional Primitives) - ✅ COMPLETE
- ✅ All essential OmniFocus primitives
- ✅ Advanced filtering and queries
- ✅ Project review (GTD methodology)
- ✅ Perspectives support
- ✅ Comprehensive test coverage

### Phase 3 (API Redesign) - ✅ COMPLETE
- ✅ Consolidated to 16 core functions
- ✅ Minimized tool call overhead
- ✅ Type-safe with enums
- ✅ Batch operations
- ✅ 89% test coverage

---

## Next Steps

**For the MCP Server:**
1. ✅ Core functionality complete
2. ✅ Documentation complete
3. ✅ Test coverage excellent (89%)
4. ⏳ Bug fixes and enhancements based on real-world usage

**For Application-Layer Features:**
1. Build separate services that use this MCP server
2. Use Claude Desktop with this server + manual workflows
3. Create separate MCP servers for other systems (calendar, email, etc.)

---

## Open Questions (Resolved)

1. **Pricing Model:** Free, open source MCP server ✅
2. **OmniGroup Relationship:** Independent tool ✅
3. **Data Privacy:** Local-only, no cloud processing ✅
4. **Platform Support:** macOS only (OmniFocus limitation) ✅
5. **Multi-user:** Individual-focused (as OmniFocus is) ✅
6. **API Surface:** 16 core functions covering all primitives ✅
7. **Application Features:** Out of scope - separate services ✅

---

**Last Updated:** October 20, 2025
