# OmniFocus MCP Server - Project Memory

**Last Updated:** 2025-10-19
**Current Version:** v0.6.0 (Maintenance Mode)

**This file is automatically loaded by Claude Code when working on this project.**

It contains:
- Critical development rules (TDD, testing, code quality)
- Architecture principles and API design guidelines
- Current project status
- Quick reference for common tasks

**For complete details:**
- Architecture decisions: @docs/reference/ARCHITECTURE.md (auto-imported)
- Testing procedures: docs/guides/TESTING.md
- Contribution workflow: docs/guides/CONTRIBUTING.md
- AppleScript gotchas: docs/reference/APPLESCRIPT_GOTCHAS.md

**For redesign implementation history:** `.claude/CLAUDE-redesign-phase.md` (archived)

---

## 🚨 CRITICAL: Read This First

### Test-Driven Development (TDD) - NON-NEGOTIABLE

This project follows Test-Driven Development (TDD).

**Before making ANY code changes:**

1. Write a failing test first that demonstrates the desired behavior
2. Run the test to confirm it fails
3. Implement the minimal code to make the test pass
4. Run the test again to confirm it passes
5. Run all tests to ensure no regressions

**Do NOT write implementation code before writing tests.**

### Testing Requirements

**See `docs/guides/TESTING.md` for complete testing strategy, procedures, and coverage details.**

**Quick commands:**
```bash
make test                  # All unit tests (fast, ~2min, 333 tests)
make test-integration      # Real OmniFocus tests (~10-30s, requires setup)
make test-e2e              # End-to-end MCP tool tests (requires setup)
```

**⚠️ THREE TIERS REQUIRED:** Unit (mock), Integration (real OmniFocus), E2E (full MCP stack)

See `docs/guides/TESTING.md` and `docs/guides/INTEGRATION_TESTING.md` for setup and procedures.

### Code Quality Standards

**Before committing:**
```bash
./scripts/check_complexity.sh  # Check cyclomatic complexity
```

**Complexity targets:**
- **A-B rating (CC 1-10)**: Simple, easy to test ✅ TARGET for new code
- **C rating (CC 11-20)**: Acceptable for complex business logic ⚠️
- **D-F rating (CC 21+)**: Requires documentation or refactoring 🔴

See `docs/reference/CODE_QUALITY.md` for complete metrics, Radon guidelines, and quality thresholds.

### Code Standards

Python 3.10+, type hints required, follow existing patterns, AppleScript safety checks enabled by default

---

## Architecture & API Design

**📚 For complete architectural rationale, detailed examples, and full context:**

@docs/reference/ARCHITECTURE.md

**Note:** The `@` syntax automatically imports this file into Claude Code's context. ARCHITECTURE.md contains:
- Full design rationale explaining "why" behind decisions
- Worked examples showing decision-making process
- Complete anti-pattern catalog with detailed explanations
- Type signature templates you can copy/paste

### ⚡ Quick Decision Tree - Use This BEFORE Adding Any Function

1. ⚠️ **Can existing `update_X()` handle this?** (90% of cases: YES)
   - Setting a field? → Add to `update_task()` or `update_project()`
   - Example: Need to flag a task? → `update_task(task_id, flagged=True)`

2. ⚠️ **Can existing `get_X()` handle this with a parameter?** (9% of cases: YES)
   - Filtering data? → Add parameter to `get_tasks()` or `get_projects()`
   - Example: Need overdue tasks? → `get_tasks(overdue=True)`

3. ⚠️ **Is this truly specialized logic?** (1% of cases: MAYBE)
   - Positioning? Recursive operations? UI state changes?
   - Example: `reorder_task()` has complex before/after logic

**If you answered NO to all three:** You likely DO need a new function (rare). See `docs/ARCHITECTURE.md` "When to Add a New Function" section.

### Anti-Patterns (NEVER DO THESE)

❌ Field-specific setters: `set_due_date()`, `set_flag()`, `set_estimated_minutes()`
✅ Use: `update_task(task_id, due_date=X, flagged=True, estimated_minutes=Y)`

❌ Specialized filters as functions: `get_stalled_projects()`, `get_overdue_tasks()`
✅ Use: `get_tasks()` with parameters or client-side filtering

❌ Completion-specific function: `complete_task()`
✅ Use: `update_task(task_id, completed=True)`

❌ Status-specific function: `drop_task()`
✅ Use: `update_task(task_id, status=TaskStatus.DROPPED)`

❌ Hierarchy-specific function: `move_task()`
✅ Use: `update_task(task_id, project_id=X)`

❌ String booleans: `flagged="true"`
✅ Use: `flagged=True`

❌ Formatted text returns: `"Task 1: ...\nTask 2: ..."`
✅ Use: `[{"id": "1", ...}, {"id": "2", ...}]`

See `docs/ARCHITECTURE.md` for complete anti-pattern catalog with rationale.

### Core Principles (DO NOT VIOLATE)

1. **Minimize tool call overhead**: Comprehensive update functions over specialized operations
2. **Prevent errors**: Separate single/batch updates for fields requiring unique values
3. **Consistency**: Use `{entity}_name` pattern (project_name, task_name)
4. **Union types**: Use `Union[str, list[str]]` for delete operations, NOT for updates
5. **MCP-first**: Keep create/update separate (no upsert pattern)
6. **Structured returns**: Return `list[dict]` or `dict`, never formatted text strings

---

## Project Status

**Current Version:** v0.6.0 (Maintenance Mode)
**API Functions:** 16 core functions (redesign complete October 2025)
**Test Coverage:** 89% overall (see `docs/guides/TESTING.md` for detailed breakdown)

The API redesign (40→16 functions) completed October 2025.

**See for details:**
- `docs/project/ROADMAP.md` - Project history and phases
- `CHANGELOG.md` - Version history and migration guide
- `.claude/CLAUDE-redesign-phase.md` - Implementation guidance (archived)

---

## Final API Structure (16 Functions)

**Projects (5):**
- `create_project()` - Create new project
- `get_projects()` - Read with filtering and optional full notes
- `update_project()` - Update single project (all fields)
- `update_projects()` - Batch update (limited fields, excludes name/note)
- `delete_projects()` - Delete one or many (Union type)

**Tasks (6):**
- `create_task()` - Create (inbox if no project)
- `get_tasks()` - Read with filtering and optional full notes
- `update_task()` - Update single task (all fields)
- `update_tasks()` - Batch update (limited fields, excludes name/note)
- `delete_tasks()` - Delete one or many (Union type)
- `reorder_task()` - Change task order (specialized logic)

**Folders (2):**
- `create_folder()` - Create folder with optional parent
- `get_folders()` - Read all folders with hierarchy

**Tags (1):**
- `get_tags()` - Read all available tags

**Perspectives (2):**
- `get_perspectives()` - Read all available perspectives
- `switch_perspective()` - Switch UI to different perspective

---

## Common Development Tasks

### Type Safety Examples

```python
# ✅ Good: Using Enums
def update_task(
    task_id: str,
    status: Optional[TaskStatus] = None,  # Enum
    flagged: Optional[bool] = None,       # bool, not string
    ...
) -> dict:  # Structured return
    ...

# ✅ Good: Union types for variable quantity
def delete_tasks(
    task_ids: Union[str, list[str]]  # Single or multiple
) -> dict:
    ...

# ❌ Bad: String booleans, string status
def update_task(
    task_id: str,
    status: str,  # Should be Enum
    flagged: str,  # Should be bool
    ...
) -> str:  # Should be dict
    ...
```

### Adding a New Function

**STOP!** Before adding:
1. Check the Quick Decision Tree above - can existing functions handle this?
2. Review `docs/ARCHITECTURE.md` anti-patterns section
3. **Write tests first** (TDD):
   - Unit tests (mock AppleScript)
   - Integration tests (real OmniFocus)
   - **E2E tests** (`tests/test_e2e_mcp_tools.py` - test MCP tool invocation)
4. **Expose in server** - Add corresponding tool in `server_fastmcp.py`
5. See `docs/guides/CONTRIBUTING.md` for full workflow

### Modifying Existing Function

See `docs/guides/CONTRIBUTING.md` for complete workflow including:
- Write test first (TDD)
- Update both single and batch versions if applicable
- Check complexity after changes

---

## Before Every Commit

**Run this checklist:**
- [ ] **Tests written first** - All new code has tests (unit, integration, AND e2e)
- [ ] **All tests pass** - Run `make test`
- [ ] **Integration tests pass** - Run `make test-integration`
- [ ] **E2E tests pass** - Run `make test-e2e` (new/modified client functions need MCP tool tests)
- [ ] **Server exposure verified** - Run `./scripts/check_client_server_parity.sh`
- [ ] **Complexity checked** - Run `./scripts/check_complexity.sh`
- [ ] **Decision tree followed** - No new functions without consulting tree
- [ ] **Documentation updated** - CHANGELOG.md, ROADMAP.md, or other docs if needed
  - Verify cross-references exist; breaking changes need migration guide (MIGRATION_vX.Y.md pattern)
  - If tests added/removed: Update count in `docs/guides/TESTING.md` only (single source of truth)
- [ ] **Architecture followed** - Reviewed relevant sections of `docs/ARCHITECTURE.md`

**If tests are failing:**
- Don't commit until they pass
- If you can't fix them quickly, create a failing test as a TODO
- Document why the test is failing in the test itself
- Consider if this indicates an architectural problem

See `docs/guides/CONTRIBUTING.md` for complete pre-commit workflow.

---

## Caught a Mistake?

### What Qualifies as a Mistake (vs. a Bug)?

**Mistakes** are architectural/process failures that violate established practices:
- ❌ Forgot to write test first (violated TDD)
- ❌ Added function without checking decision tree (violated architecture)
- ❌ Implemented in client but didn't expose in server (missing exposure)
- ❌ Breaking change without migration guide (missing docs)
- ❌ Function has CC > 20 without documentation (complexity spike)
- ❌ Test passes with mock but fails with real OmniFocus (missing integration test)

**Bugs** are implementation errors in otherwise correct code:
- ✅ Typo in variable name (`elifintervalDays`)
- ✅ Off-by-one error in loop
- ✅ Missing null check causing crash
- ✅ Incorrect return type

### Detection Criteria for AI Assistants

**When to suggest logging a mistake:**

1. **Missing Tests (missing-tests)**
   - Added function but didn't modify test file in same commit
   - Example: "Added `foo_task()` but `tests/test_foo.py` unchanged"
   - Suggest: "This looks like MISTAKE category: missing-tests. Should we log it?"

2. **Missing Server Exposure (missing-exposure)**
   - Added function to `omnifocus_client.py` but not to `server_fastmcp.py`
   - Can detect with: `./scripts/check_client_server_parity.sh`
   - Suggest: "Function not exposed as MCP tool. Log as missing-exposure?"

3. **Violated TDD (violated-tdd)**
   - Implementation commit comes before test commit
   - Large code addition without corresponding test changes
   - Suggest: "Test should have been written first (TDD). Log as violated-tdd?"

4. **Violated Architecture (violated-architecture)**
   - Added new function without consulting decision tree
   - Created field-specific setter instead of using `update_X()`
   - Example: `set_due_date()` instead of `update_task(due_date=X)`
   - Suggest: "This violates CRUD pattern. Check decision tree. Log as violated-architecture?"

5. **Missing Docs (missing-docs)**
   - CHANGELOG references file that doesn't exist
   - Version number mismatches across files
   - Test counts out of sync
   - Suggest: "Documentation references are broken. Log as missing-docs?"

6. **Complexity Spike (complexity-spike)**
   - Function rated D or F (CC > 20) without documentation in CODE_QUALITY.md
   - Suggest: "High complexity without documentation. Log as complexity-spike?"

### Workflow

If you discovered an architectural oversight (not a syntax error):

1. **Fix it first** - Don't leave it broken
2. **Log it** - Run `./scripts/log_mistake.sh` and edit `.claude/MISTAKES.md`
3. **Update status** - Use `./scripts/update_mistake_status.sh MISTAKE-XXX <status>`
4. **Reference in commit** - Use `Resolves: MISTAKE-XXX` footer

**Why?** Patterns (3+ similar) trigger CLAUDE.md improvements to prevent recurrence. The system measures effectiveness and improves detection over time.

---

## Documentation Reference

### Quick Decision Guide

1. **Architecture questions** → See @docs/reference/ARCHITECTURE.md (imported, always available)
2. **API design questions** → See `docs/API_REFERENCE.md` for complete function signatures
3. **Can I add this function?** → NO, check the decision tree first
4. **Should I write the test first?** → YES, always (TDD is non-negotiable)
5. **Is this field safe for batch updates?** → If it requires unique values (name/note), NO
6. **What's been implemented?** → See `docs/project/ROADMAP.md` for current status
7. **What changed recently?** → See `CHANGELOG.md` for version history
8. **How do I test this?** → See `docs/guides/TESTING.md` for complete guide
9. **Is my code too complex?** → Run `./scripts/check_complexity.sh`
10. **How do I test with real OmniFocus?** → See `docs/guides/INTEGRATION_TESTING.md` for setup

### Project Documentation Files

- **This file:** `.claude/CLAUDE.md` - Project memory and critical rules
- **Architecture:** @docs/reference/ARCHITECTURE.md - Complete design rationale (auto-imported)
- **API Spec:** `docs/API_REFERENCE.md` - Complete API documentation
- **Testing Guide:** `docs/guides/TESTING.md` - Testing strategy, procedures, and coverage
- **Code Quality:** `docs/reference/CODE_QUALITY.md` - Complexity metrics and Radon guidelines
- **Integration Tests:** `docs/guides/INTEGRATION_TESTING.md` - Real OmniFocus testing setup
- **AppleScript:** `docs/reference/APPLESCRIPT_GOTCHAS.md` - Limitations and workarounds
- **Contributing:** `docs/guides/CONTRIBUTING.md` - Development workflow and guidelines
- **Project Roadmap:** `docs/project/ROADMAP.md` - Project history, phases, and status
- **Release History:** `CHANGELOG.md` - Version history and technical changes
- **Historical:** `.claude/CLAUDE-redesign-phase.md` - Redesign implementation guidance (archived)
