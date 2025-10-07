# OmniFocus MCP Server: Focused Roadmap

**Status**: Core implementation complete. Considering optional enhancements.

---

## Vision

Provide a **clean, complete, well-tested MCP server** that exposes all OmniFocus primitives to AI assistants like Claude Desktop.

**What this IS:**
- A protocol adapter between MCP and OmniFocus
- A set of primitives for AI-powered OmniFocus workflows
- A foundation for building intelligent task management workflows

**What this is NOT:**
- An email processor
- A calendar sync service
- A meeting transcription tool
- An analytics dashboard
- A standalone application

---

## Current Status: v0.2.0

### ✅ Core Implementation Complete (Phase 1)

**12 MCP Tools Implemented:**

1. `get_projects` - List all active projects
2. `search_projects` - Search projects by name/note/folder
3. `create_project` - Create new project with folder placement
4. `get_tasks` - Query tasks with flexible filtering
5. `add_task` - Create task with full GTD properties
6. `update_task` - Modify existing task
7. `complete_task` - Mark task as complete
8. `get_inbox_tasks` - List inbox items
9. `create_inbox_task` - Quick capture to inbox
10. `get_tags` - List all available tags
11. `add_tag_to_task` - Add tag to task
12. `add_note` - Append note to project

**Quality Metrics:**
- ✅ 210 passing tests (79 client + 79 server + 40 integration + 13 safety)
- ✅ ~0.47s execution time for full test suite
- ✅ FastMCP 2.0 architecture (38% less code)
- ✅ Multi-layer database safety system
- ✅ Type-safe with auto-generated schemas
- ✅ Comprehensive documentation

---

## Potential Future Enhancements

These are **optional** enhancements that maintain MCP server scope:

### 1. Additional OmniFocus Primitives

**Priority: Medium**

If OmniFocus supports these via AppleScript:

- `delete_task(task_id)` - Remove a task
- `delete_project(project_id)` - Remove a project
- `move_task(task_id, new_project_id)` - Move task between projects
- `get_folders()` - List folder hierarchy
- `create_folder(name, parent_path)` - Create folders
- `get_perspectives()` - List custom perspectives
- `get_available_tasks()` - Get available (not blocked/deferred) tasks
- `defer_task(task_id, defer_until)` - Defer task to future date

**Considerations:**
- Only add if genuinely useful
- Maintain test coverage (TDD approach)
- Keep safety guards for destructive operations

---

### 2. Enhanced Query Capabilities

**Priority: Low**

Make existing tools more powerful:

- `get_tasks()` enhancements:
  - `due_soon=True` - Already implemented! ✅
  - `overdue=True` - Tasks past due date
  - `tag_filter=["urgent", "work"]` - Filter by multiple tags
  - `available_only=True` - Only actionable tasks
  - `sort_by="due_date"` - Sort results

- `search_projects()` enhancements:
  - `status_filter=["active", "on_hold"]` - Filter by status
  - `folder_filter="Work"` - Search within folder

**Considerations:**
- These are nice-to-have, not essential
- Current tools already handle most use cases
- Can be done via multiple tool calls if needed

---

### 3. Batch Operations

**Priority: Low**

Allow multiple operations in one call:

- `batch_add_tasks(project_id, tasks)` - Add multiple tasks at once
- `batch_complete_tasks(task_ids)` - Complete multiple tasks
- `batch_tag_tasks(task_ids, tag_name)` - Tag multiple tasks

**Considerations:**
- Reduces MCP round trips
- More complex to implement and test
- May not be worth the complexity

---

### 4. Performance Optimizations

**Priority: Low**

Current performance is good, but could be better:

- Cache project/tag lists (with TTL)
- Optimize AppleScript for large datasets
- Add pagination for large result sets
- Parallel AppleScript execution

**Considerations:**
- Current performance is acceptable
- Premature optimization may add complexity
- Only pursue if users report slowness

---

### 5. Enhanced Error Messages

**Priority: Medium**

Make errors more actionable:

- Better error messages when project/task not found
- Suggestions for misspelled folder paths
- Validate tag names before attempting to add
- Check if project is sequential before adding tasks

**Considerations:**
- Improves user experience
- Can be added incrementally
- Should not sacrifice performance

---

## What We Will NOT Add

These belong elsewhere, not in the MCP server:

### ❌ Application Logic
- Email processing
- Calendar integration
- Meeting transcription
- Analytics/reporting
- Template systems (use prompts)
- Automation workflows (use Claude)

### ❌ External Integrations
- GitHub sync (separate mcp-github server)
- Jira sync (separate mcp-jira server)
- Slack notifications
- Time tracking (separate service)

### ❌ Intelligence Layer
- AI-powered suggestions
- Pattern learning
- Smart scheduling
- Priority scoring
- Context prediction

**Why not?** These are application features that should *use* the MCP server, not be part of it.

---

## Decision Framework

When considering new features, ask:

1. **Is it an OmniFocus primitive?**
   - ✅ Yes → Consider adding
   - ❌ No → Probably doesn't belong

2. **Can OmniFocus AppleScript do it?**
   - ✅ Yes → Potentially feasible
   - ❌ No → Not possible

3. **Does it add complexity?**
   - 📊 Low → Probably worth it
   - 📊 High → Needs strong justification

4. **Can it be done with existing tools?**
   - ✅ Yes → Don't add (use multiple calls)
   - ❌ No → Consider adding

5. **Is it testable?**
   - ✅ Yes → Can implement with TDD
   - ❌ No → Reconsider design

---

## Versioning Strategy

- **v0.2.x** - Bug fixes, documentation updates
- **v0.3.0** - Additional primitives (if needed)
- **v0.4.0** - Enhanced queries (if needed)
- **v1.0.0** - When stable and production-ready

---

## Testing Standards

All new features must meet these standards:

- ✅ TDD approach (write tests first)
- ✅ Unit tests for client methods
- ✅ Integration tests for workflows
- ✅ Safety guard tests if destructive
- ✅ Edge case coverage
- ✅ Documentation with examples
- ✅ No regressions (all tests pass)

---

## Documentation Standards

All tools must have:

- ✅ Clear docstring with args/return
- ✅ FastMCP auto-generates schema from types
- ✅ Examples in TESTING.md
- ✅ Error cases documented
- ✅ Safety considerations noted

---

## Maintenance Philosophy

**Prefer:**
- ✅ Simple over clever
- ✅ Explicit over implicit
- ✅ Tested over fast
- ✅ Clear over concise
- ✅ Stable over feature-rich

**Avoid:**
- ❌ Feature creep
- ❌ Premature optimization
- ❌ Breaking changes
- ❌ Untested code
- ❌ Clever tricks

---

## Success Metrics

The MCP server is successful if:

1. ✅ **Complete**: Exposes all useful OmniFocus primitives
2. ✅ **Correct**: No data loss, accurate results
3. ✅ **Fast**: <1s response time for operations
4. ✅ **Tested**: High coverage, TDD approach
5. ✅ **Safe**: Protects production database
6. ✅ **Maintainable**: Clean code, good docs
7. ✅ **Stable**: No breaking changes
8. ⏭️ **Used**: People actually use it with Claude Desktop

---

## Community Contributions

Welcome contributions that:
- Add missing OmniFocus primitives
- Fix bugs
- Improve documentation
- Add test coverage
- Optimize performance

Please don't contribute:
- Application logic (email, calendar, etc.)
- External integrations (GitHub, Jira, etc.)
- Intelligence features (AI, ML, etc.)

---

## Long-Term Vision

**Year 1:**
- ✅ Complete core implementation (DONE)
- ⏭️ Real-world usage with Claude Desktop
- ⏭️ Bug fixes and stability improvements
- ⏭️ Community feedback

**Year 2+:**
- Maintain stable API
- Add primitives only when clearly needed
- Focus on reliability over features
- Serve as example of well-built MCP server

---

## Next Immediate Steps

1. ⏭️ **Test with Claude Desktop**
   - Configure MCP in Claude Desktop
   - Try real workflows
   - Gather feedback

2. ⏭️ **Documentation**
   - Write setup guide for Claude Desktop
   - Add workflow examples
   - Create troubleshooting guide

3. ⏭️ **Stability**
   - Monitor for bugs
   - Fix issues as they arise
   - Keep tests passing

4. ⏭️ **Consider**
   - Additional primitives (only if needed)
   - Performance optimizations (only if slow)
   - Enhanced errors (nice to have)

---

*This is a living document. Update as we learn from real-world usage.*
