# OmniFocus MCP Server: Development Roadmap

## Status: Phase 3 (API Redesign) Complete ✅

**Current Version:** v0.7.0 (November 2025)

**Project Status:** Maintenance mode - Core MCP server is feature-complete with 16 comprehensive tools covering all OmniFocus primitives.

**Latest:**
- v0.7.0 (Nov 2025): Release process infrastructure, interactive quality checks, workflow enforcement, Claude Code hooks
- v0.6.5 (Oct 2025): Fixed AppleScript DONE status bug, added GitHub Actions CI, comprehensive testing documentation
- v0.6.4 (Oct 2025): Implemented actual hygiene check scripts (was placeholder automation in v0.6.3)
- v0.6.3 (Oct 2025): Trunk-based workflow with RC tags, git hooks for release hygiene
- v0.6.2 (Oct 2025): Added Claude Code hooks for automated workflow enforcement
- v0.6.1 (Oct 2025): Fixed project review date bug, renamed `omnifocus_client` → `omnifocus_connector`

**Note**: This roadmap has been revised. The original vision included email forwarding, calendar integration, and other application-layer features. However, these don't belong in an MCP server - they should be separate services or applications that *use* the MCP server.

---

## Vision

**Original Vision**: Transform OmniFocus from a manual task manager into an intelligent AI-powered productivity system.

**Revised Vision**: Provide a clean, complete, well-tested MCP server that exposes all OmniFocus primitives to AI assistants like Claude.

**Achieved**: ✅ 16 comprehensive MCP tools, 89% test coverage, type-safe API, batch operations, production-ready.

---

## Current State (v0.7.0 - November 2025)

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

**UI Navigation (1 tool):**
- ✅ `set_focus` - Focus OmniFocus window on project or folder

### Test Coverage

**333 passing tests** with 89% overall code coverage. See [../guides/TESTING.md](../guides/TESTING.md) for detailed breakdown.

### Database Safety

- ✅ Multi-layer safety system
- ✅ Environment variable checks
- ✅ Database name whitelist
- ✅ Runtime verification via AppleScript
- ✅ All destructive operations protected

### Development Process & Workflow

**Branching Strategy (v0.6.3+):** Trunk-based development
- Single `main` branch (always releasable, tests pass)
- Feature branches short-lived (merge within days)
- Tags mark releases (v0.6.3, v0.6.4, etc.)
- RC tags trigger hygiene checks (v0.6.3-rc1, rc2, etc.)
- **Rationale:** Modern CI/CD best practice - faster feedback, simpler workflow, better automation
- **See:** `../guides/CONTRIBUTING.md` for complete workflow
- **Decision:** Issue #56 (Oct 2025) - replaced GitFlow approach

**Test-Driven Development:** Non-negotiable
- Write failing test first
- Implement minimal code to pass
- Three-tier testing: unit, integration, e2e
- 89% code coverage

**Workflow Enforcement:** Automated via Claude Code hooks (v0.6.2+)
- Blocks commits to main branch
- Monitors CI failures after git push
- Loads project context at session start
- **See:** `.claude/CLAUDE.md` for hook documentation

**Release Hygiene Checks:** Automated quality gates (v0.6.3-v0.7.0)
- Git pre-tag hook runs comprehensive checks on RC tags
- 7 critical automated checks (must pass to release)
- 3 interactive checks (qualitative feedback via slash commands)
- Review-and-approve workflow for acceptable failures
- **See:** `docs/reference/HYGIENE_CHECK_CRITERIA.md` for complete criteria
- **See:** `docs/guides/CONTRIBUTING.md` for release process

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

## Recent Completed Work

### v0.7.0 - Hygiene Check System Overhaul ✅ (October-November 2025)

**Completed:** Comprehensive hygiene check system with review-and-approve workflow (#70)

**Key changes:**
- ✅ Promoted test coverage to critical check with 85% threshold enforcement
- ✅ Streamlined to 7 automated critical checks (from 10)
- ✅ Separated automated (critical) from interactive (qualitative) checks
- ✅ Implemented review-and-approve workflow for acceptable failures
- ✅ Added ROADMAP.md sync check (#34) - ensures closed issues removed from active sections
- ✅ Branch protection git hook (#94) - blocks commits to main except hotfixes
- ✅ CI monitoring documentation (#36)
- ✅ Comprehensive hygiene criteria documentation

**What was removed from automated checks:**
- Code quality (subjective, no objective threshold) - now interactive slash command
- Directory organization (minor, subjective) - now interactive slash command

**See:** `docs/reference/HYGIENE_CHECK_CRITERIA.md` for complete pass/fail criteria

### v0.6.3-v0.6.5 - Workflow Automation ✅ (October 2025)

**Completed:**
- ✅ Claude Code hooks implementation (v0.6.2) - automatic workflow enforcement
- ✅ GitHub Issues migration (v0.6.2) - centralized tracking for all issues
- ✅ Trunk-based development with RC tags (v0.6.3)
- ✅ Git hooks for release hygiene (v0.6.3-v0.6.4)
- ✅ GitHub Actions CI workflow (v0.6.5)
- ✅ Comprehensive testing documentation (v0.6.5)

### v0.6.2 - Automation Infrastructure ✅ (October 2025)

**Completed:** Recursive self-improvement system implementation

**A. Claude Code Hooks**
- ✅ Automatic enforcement via `.claude/settings.json`
- ✅ Pre-tool hooks block commits to main branch
- ✅ Post-tool hooks monitor CI failures after git push
- ✅ Session start hooks load project context
- ✅ Issue close verification prevents premature closure

**B. GitHub Issues Migration**
- ✅ Complete migration from MISTAKES.md to GitHub Issues
- ✅ Label system: `ai-process`, `bug`, `enhancement`, `documentation`
- ✅ Recurrence tracking via duplicate issues (standard GitHub practice)
- ✅ Version workflow: Backlog → Milestone → Release
- ✅ Native automation via GitHub Actions, CLI, notifications

**See:** `.claude/CLAUDE.md` for complete hook documentation

---

## Upcoming Work

**Status:** The v0.7.0 API is feature-complete and stable. The project is in maintenance mode with 17 open GitHub Issues tracking future improvements.

**Current open issues (as of November 2025):**
- **Bug:** #78 - get_tasks() and get_projects() full_notes parameter not working (high priority)
- **Enhancement:** #50 - Performance optimization for slow operations (~10s for overdue tasks)
- **Enhancement:** #51 - Refactor high-complexity functions (technical debt)
- **Workflow:** #93 - Phase 7 comprehensive documentation updates (in progress)
- **Workflow:** #89 - Migrate recurring AI-process issues into automated checks
- **Workflow:** #87 - Adopt one-branch-per-issue workflow
- **Workflow:** #88 - Define version update protocol
- **Testing:** #92 - Add smoke tests for hygiene check scripts (low priority)
- **Release:** #65 - Test release branch workflow end-to-end
- **Release:** #54 - Add AppleScript safety audit to hygiene checks
- **Release:** #53 - Implement performance regression testing
- **Release:** #52 - Add dependency security audit to hygiene checks
- **Documentation:** #86 - Interactive documentation quality check slash command
- **Documentation:** #76 - Create user surveys (foundation models and humans)
- **Documentation:** #71 - Create reusable AI development workflow template
- **Documentation:** #64 - Add PR and issue templates for contributors

**See:** [GitHub Issues](https://github.com/your-org/omnifocus-mcp/issues) for complete list and details.

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

**🤔 UI Navigation - Partially Implemented**
- ✅ `set_focus(item_id, item_type="project"|"folder")` - Focus window on project or folder (IMPLEMENTED in v0.7.0)
  - **AppleScript Limitation:** Tasks and tags cannot be focused (OmniFocus restriction)
  - Only supports `item_type="project"` or `item_type="folder"`
  - Raises clear error for unsupported types with explanation
- ❌ Tab management - Not available via AppleScript (API doesn't expose tabs property)

**Resolution:** UI navigation is appropriate for MCP server (precedent: `switch_perspective()`). Implemented within AppleScript limitations. Future: May add task/tag navigation if OmniFocus exposes it.

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

**Last Updated:** November 1, 2025
