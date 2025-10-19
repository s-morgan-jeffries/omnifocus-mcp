# OmniFocus MCP Server - Project Memory (ARCHIVE)

**⚠️ ARCHIVE NOTICE:** This file is a historical snapshot preserved from the v0.6.0 API redesign implementation phase (October 2025). It contains detailed implementation guidance that was actively used during the redesign but is no longer needed now that the project is in maintenance mode.

**For current project guidelines:** See `.claude/CLAUDE.md` (streamlined maintenance-mode version)

**Archived:** 2025-10-19
**Original Last Updated:** 2025-10-17 (API Redesign Phase)
**Original Version Status:** v0.5.0 → v1.0.0 (in progress)

**This file is automatically loaded by Claude Code when working on this project.**

It contains:
- Critical development rules (TDD, testing, code quality)
- Architecture principles and API design guidelines
- Current project status and implementation roadmap
- Common development tasks and troubleshooting

**For Claude Code:** Follow the guidelines in this file strictly.  
**For human developers:** This documents our practices and serves as onboarding material.

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

**See `docs/TESTING.md` for complete testing strategy, procedures, and coverage details.**

**Quick commands:**
```bash
make test                  # All unit tests (fast, ~0.53s)
make test-integration      # Real OmniFocus tests (~10-30s, requires setup)
make test-e2e              # End-to-end MCP tool tests (requires setup)
pytest tests/test_file.py  # Specific test file
```

**⚠️ THREE LEVELS OF TESTING - ALL ARE REQUIRED:**
1. **Unit Tests** - Mock AppleScript, fast, run always
2. **Integration Tests** - Real OmniFocus via client, catches AppleScript bugs
3. **E2E Tests** - Full MCP tool → client → OmniFocus stack, catches parameter conversion bugs

**Integration ≠ E2E:** They test different layers and catch different bugs!

**⚠️ For integration/E2E tests:** Setup required - see "Testing Strategy for Redesign" section later in this file or `docs/INTEGRATION_TESTING.md`

**Key testing files:**
- `tests/test_omnifocus_client.py` - Core client unit tests (149 tests)
- `tests/test_server_fastmcp.py` - MCP server tests (33 tests)
- `tests/test_integration_real.py` - Real OmniFocus integration (3 tests, skipped by default)
- `tests/test_e2e_real.py` - Full stack E2E tests (skipped by default)
- `tests/test_safety_guards.py` - Database protection tests (13 tests)

**Test coverage standards:** 89% overall (see TESTING.md for details)

### Code Quality Standards

**See `docs/CODE_QUALITY.md` for complexity metrics, Radon guidelines, and quality thresholds.**

**Before committing:**
```bash
./scripts/check_complexity.sh  # Check cyclomatic complexity
```

**Complexity targets:**
- **A-B rating (CC 1-10)**: Simple, easy to test ✅ TARGET for new code
- **C rating (CC 11-20)**: Acceptable for complex business logic ⚠️
- **D-F rating (CC 21+)**: Requires documentation or refactoring 🔴
  - **Document** if complexity is inherent to the problem (like `get_tasks()`)
  - **Refactor** if complexity is accidental (can be simplified)
  - Ask: "Could this be multiple simpler functions?"

**Intentionally complex functions (documented exceptions):**
- `get_tasks()` - F (CC 66) - 21 parameters, complex filtering
- `update_task()` - D (CC 27) - 10+ optional properties
- `get_projects()` - D (CC 23) - Comprehensive property extraction

### Code Standards

- Python 3.10+ required
- Use type hints for all function parameters and return values
- Follow existing code patterns in the codebase
- AppleScript safety checks are enabled by default for production database protection

---

## Architecture & API Design

**📚 For complete architectural rationale, detailed examples, and full context:**

@docs/ARCHITECTURE.md

**Note:** The `@` syntax automatically imports this file into Claude Code's context. ARCHITECTURE.md is loaded when Claude Code starts and contains:
- Full design rationale explaining "why" behind decisions
- Worked examples showing decision-making process  
- Complete anti-pattern catalog with detailed explanations
- Type signature templates you can copy/paste

**When Claude references ARCHITECTURE.md:**
Claude Code has this content available at all times for architecture decisions, but you should explicitly consult it when:
- Making architectural decisions about API design
- Unsure why a specific rule exists
- Need examples of correct implementation patterns
- Evaluating whether a new function is truly necessary

**⚡ Quick Decision Tree - Use This BEFORE Adding Any Function:**

1. ⚠️ **Can existing `update_X()` handle this?** (90% of cases: YES)
   - Setting a field? → Add to `update_task()` or `update_project()`
   - Example: Need to flag a task? → `update_task(task_id, flagged=True)`
   - See "Type Safety Examples" section later in this file for correct patterns

2. ⚠️ **Can existing `get_X()` handle this with a parameter?** (9% of cases: YES)
   - Filtering data? → Add parameter to `get_tasks()` or `get_projects()`
   - Example: Need overdue tasks? → `get_tasks(overdue=True)`
   - See docs/ARCHITECTURE.md for filtering pattern examples

3. ⚠️ **Is this truly specialized logic?** (1% of cases: MAYBE)
   - Positioning? Recursive operations? UI state changes?
   - Example: `reorder_task()` has complex before/after logic
   - See docs/ARCHITECTURE.md "When to Add a New Function" section

**If you answered NO to all three questions:**

You likely DO need a new function (this is rare!). Follow these steps:

1. Document your reasoning in the function docstring
2. Add the new pattern to docs/ARCHITECTURE.md as a worked example
3. Explain in your commit message why existing functions couldn't handle this
4. Add example to docs/ARCHITECTURE.md "When to Add a New Function" section
5. Follow the CRUD pattern templates from docs/ARCHITECTURE.md

### Anti-Patterns (NEVER DO THESE)

```
❌ Field-specific setters: set_due_date(), set_flag(), set_estimated_minutes()
   ✅ Use: update_task(task_id, due_date=X, flagged=True, estimated_minutes=Y)

❌ Specialized filters as functions: get_stalled_projects(), get_overdue_tasks()
   ✅ Use: get_tasks() with parameters or client-side filtering

❌ Completion-specific function: complete_task()
   ✅ Use: update_task(task_id, completed=True)

❌ Status-specific function: drop_task()
   ✅ Use: update_task(task_id, status=TaskStatus.DROPPED)

❌ Hierarchy-specific function: move_task()
   ✅ Use: update_task(task_id, project_id=X)

❌ Upsert pattern: create_or_update_task(task_id=None, ...)
   ✅ Use: Keep create/update separate for clarity

❌ String booleans: flagged="true"
   ✅ Use: flagged=True

❌ Formatted text returns: "Task 1: ...\nTask 2: ..."
   ✅ Use: [{"id": "1", ...}, {"id": "2", ...}]
```

### Core Principles (DO NOT VIOLATE)

1. **Minimize tool call overhead**: Comprehensive update functions over specialized operations
2. **Prevent errors**: Separate single/batch updates for fields requiring unique values
3. **Consistency**: Use `{entity}_name` pattern (project_name, task_name)
4. **Union types**: Use `Union[str, list[str]]` for delete operations, NOT for updates
5. **MCP-first**: Keep create/update separate (no upsert pattern)
6. **Structured returns**: Return `list[dict]` or `dict`, never formatted text strings

### API Update Function Design (CRITICAL)

**Single update functions** (update_task, update_project):
- Accept single entity ID only: `entity_id: str`
- Include ALL fields that can be updated (name, note, status, dates, tags, etc.)
- Return: `dict` with success, entity_id, updated_fields, error

**Batch update functions** (update_tasks, update_projects):
- Accept single or multiple IDs: `entity_ids: Union[str, list[str]]`
- Include ONLY fields safe to apply uniformly
- MUST EXCLUDE: names, notes (require unique values)
- Return: `dict` with updated_count, failed_count, updated_ids, failures

**Why separate?** Prevents accidentally giving multiple tasks the same name or overwriting unique notes.

**Error Handling:**

Single operations:
- Parameter validation errors → Raise `ValueError` immediately
- OmniFocus errors (not found, invalid state) → Return dict with success=False
- Never raise exceptions for runtime OmniFocus errors

Batch operations:
- Parameter validation errors → Raise `ValueError` immediately  
- Individual item failures → Continue processing, report in failures list
- Always return dict with counts and failure details

---

## Project Status

### Current vs Target State

**Current Implementation (v0.5.0 - October 2025):**
- 26 MCP tools in production
- Based on original architecture (pre-redesign)
- See CHANGELOG.md for v0.5.0 details

**Target Implementation (Redesign):**
- 16 core functions (see "Final API Structure" section later in this file)
- Following new architecture principles in docs/ARCHITECTURE.md
- Breaking changes expected

**Recent Consolidation (v0.5.0):**
We already did one consolidation:
- Removed `search_projects()` → Use `get_projects(query=...)`
- Removed `get_inbox_tasks()` → Use `get_tasks(inbox_only=True)`
- Result: 38 → 36 → 26 tools

**See `docs/MIGRATION_v0.5.md` for the consolidation pattern we followed.**

### Major API Redesign (2025-10-17)

We completed a comprehensive API redesign to optimize for MCP tool calling:

**Key Changes:**
- Consolidated 40 functions → 16 core functions
- Created comprehensive `update_task()` and `update_project()` functions
- Deleted specialized operations: `complete_task()`, `flag_task()`, `move_task()`, etc.
- All updates now go through unified update functions
- Separated single/batch updates for safety (names and notes)

**See docs/ARCHITECTURE.md for detailed rationale.**

### Implementation Status

**Completed ✅**
- [x] API design and architecture documentation
- [x] docs/ARCHITECTURE.md with rationale and examples
- [x] .claude/CLAUDE.md for project context

**In Progress 🔄**
- [ ] Implement redesigned API following docs/ARCHITECTURE.md
- [ ] Write tests for new API (TDD approach)
- [ ] Verify all 16 functions work correctly

**Not Started ⏳**
- [ ] Update client applications to use new API
- [ ] Performance benchmarking
- [ ] Documentation for end users

---

## Working with Legacy Code

**Pattern from v0.5.0 consolidation (see `docs/MIGRATION_v0.5.md`):**

### Phase 1: Add New Alongside Old

```python
# Old function (keep working)
def search_projects(query: str):
    """DEPRECATED: Use get_projects(query=...) instead"""
    return get_projects(query=query)

# New function (enhanced)  
def get_projects(
    query: Optional[str] = None,  # NEW parameter
    status: Optional[str] = None,
    ...
):
    # Implementation
```

### Phase 2: Update Tests
- Keep old tests passing (backward compatibility)
- Add new tests for enhanced functionality
- Mark old tests as testing deprecated functions

### Phase 3: Deprecation Period
- Update CHANGELOG.md with migration guide
- Add deprecation warnings to old functions
- Update all internal call sites to use new API

### Phase 4: Removal (Next Major Version)
- Remove deprecated functions
- Remove old tests
- Clean up documentation

**For this redesign:** Follow the same pattern but at larger scale.

### File Organization During Transition

- **Legacy functions:** Keep in current locations with `# DEPRECATED` comments
- **New functions:** Add with clear `# NEW API (Redesign)` comments
- **Tests:** Create `test_api_redesign.py` for new API tests

**Don't delete old functions yet** - They're still in use until migration is complete.

---

## Starting the Redesign Implementation

**First time working on this project?**

1. Read this entire CLAUDE.md file first
2. Review docs/ARCHITECTURE.md for design rationale
3. Check docs/API_REFERENCE.md to see the target API
4. Ensure test environment is set up (see Testing Requirements section at top)
5. Run `make test` to verify everything works
6. Then proceed with Step 1 below

**You should be working on this if the implementation status shows items unchecked.**

### Step 1: Implement Core Update Functions

Start with the highest-impact functions:
1. `update_task()` - Single task, all fields
2. `update_tasks()` - Batch update, safe fields only
3. `update_project()` - Single project, all fields
4. `update_projects()` - Batch update, safe fields only

**Why start here?** These are the foundation that eliminates 15+ specialized functions.

### Step 2: Implement Enhanced Get Functions

Next, implement the comprehensive read functions:
1. `get_tasks()` - With all parameters (task_id, parent_task_id, include_full_notes, etc.)
2. `get_projects()` - With all parameters (project_id, include_full_notes, etc.)

**Why next?** Tests need these to verify update operations worked.

### Step 3: Implement Delete Functions

Then the cleanup operations:
1. `delete_tasks()` - Union[str, list[str]]
2. `delete_projects()` - Union[str, list[str]]

### Step 4: Verify and Deprecate

Finally, verify everything works and clean up:
1. Run full test suite
2. Mark old functions as deprecated
3. Update documentation
4. Create migration guide

---

## Testing Strategy for Redesign

### Test Organization

Create new test files for redesigned API:
```
tests/
├── test_api_redesign_update.py    # update_task, update_tasks, etc.
├── test_api_redesign_get.py       # get_tasks, get_projects
├── test_api_redesign_delete.py    # delete_tasks, delete_projects
└── test_legacy/                   # Move old tests here eventually
    └── test_original_api.py
```

### TDD During Refactor

1. **Write test for new signature** - Before implementation
2. **Test should fail** - Function doesn't exist yet
3. **Implement new function** - Make test pass
4. **Don't break old tests** - Keep legacy working during transition
5. **Integration tests last** - After individual functions work

### Test Naming Convention

```python
# New API tests
def test_update_task_sets_multiple_fields():
    """NEW API: update_task() can set name, due_date, and flagged in one call"""
    
# Legacy API tests  
def test_complete_task_marks_done():
    """LEGACY: complete_task() still works (deprecated)"""
```

### Integration Testing (CRITICAL)

**From our experience (CHANGELOG.md v0.5.0):**
- Bug: `elifintervalDays` (typo) - unit tests with mocks didn't catch it
- Bug: `eliftaskDueDate` (typo) - unit tests with mocks didn't catch it
- Only real OmniFocus execution caught these

**During redesign:**
1. Write unit tests first (TDD approach)
2. Implement function
3. **Run integration tests before committing**
4. **Run E2E tests before committing** (separate from integration!)
5. Use test database (see `docs/INTEGRATION_TESTING.md` for real OmniFocus testing setup and troubleshooting)

**Setup integration testing:**
```bash
./scripts/setup_test_database.sh
export OMNIFOCUS_TEST_MODE=true
export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"
make test-integration  # Client → AppleScript → OmniFocus
make test-e2e          # MCP tool → Client → AppleScript → OmniFocus
```

### E2E Testing (CRITICAL - DO NOT SKIP)

**E2E tests are NOT the same as integration tests!**

**Integration tests:** test_integration_real.py
- Tests: `client.get_tasks()` → AppleScript → OmniFocus
- Catches: AppleScript syntax errors, typos, logic bugs

**E2E tests:** test_e2e_real.py
- Tests: `server.get_tasks.fn()` → `client.get_tasks()` → AppleScript → OmniFocus
- Catches: Parameter conversion bugs (JSON strings), response formatting issues
- Example bugs only E2E catches: `tags='["tag"]'` vs `tags=["tag"]`

**⚠️ ALWAYS add E2E tests for new/modified MCP tools - they catch a different class of bugs!**

---

## OmniFocus/AppleScript Limitations

**Critical context for implementation:**

### Rich Text Notes
- ❌ Cannot read formatted/rich text (OmniFocus API limitation)
- ✅ Can only access plain text via AppleScript
- ⚠️ Updating notes removes all formatting
- Document this warning in all note-related functions

### Variable Naming Conflicts
- ❌ Don't use OmniFocus property names as variable names
- Example: `recurrence` and `repetitionMethod` conflict with OmniFocus properties
- Use suffixes: `recurrenceStr`, `repetitionMethodStr`
- See CHANGELOG.md v0.5.0 for details on this bug

### Recurring Tasks
- Use `mark complete` instead of setting `completed` property
- Direct property setting fails for recurring tasks
- See CHANGELOG.md v0.5.0 for details

### Performance Notes

**Context:** OmniFocus operations via AppleScript can be slow for large databases.

**Known performance characteristics:**
- `get_tasks()` - ~738 tasks in 13-17s (from CHANGELOG.md v0.5.0)
- Default timeout: 60s, can be increased to 300s
- Batch operations are more efficient than loops

**When implementing:**
1. **Avoid N+1 queries** - Fetch once, process in memory
2. **Use batch operations** - Don't loop calling single operations
3. **Consider timeouts** - Large databases may need longer timeouts
4. **Test with realistic data** - Not just 5 tasks

**Timeout guidelines:**
- Single item operations: 60s default
- Batch operations: 120s default  
- Full database queries: 120-180s

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

### Adding a New Function

**STOP!** Before adding a new function:

1. Check the Quick Decision Tree above - can existing functions handle this?
2. Review docs/ARCHITECTURE.md anti-patterns section
3. If truly necessary, follow the CRUD pattern from docs/ARCHITECTURE.md
4. **Write tests first** (see "Test-Driven Development" section at top)
5. Check complexity with `./scripts/check_complexity.sh` after implementation

### Modifying Existing Function

1. **Write test first** demonstrating desired behavior (see "Test-Driven Development" section at top)
2. Run test to confirm it fails
3. Implement minimal code to pass the test
4. Ensure changes follow docs/ARCHITECTURE.md principles
5. Update both single and batch versions if applicable
6. Run all tests to verify no regressions
7. Check complexity hasn't increased significantly

### Implementing Redesigned API

The codebase contains legacy functions that predate the redesign. When implementing new signatures:

1. Check docs/API_REFERENCE.md for the "Enhanced proposed signature"
2. **Write tests first** for the new signature (see "Test-Driven Development" section at top)
3. Implement following docs/ARCHITECTURE.md principles
4. Consolidate specialized functions into update/get functions per architecture
5. **Run integration tests** to catch AppleScript errors
6. **Run E2E tests** to catch parameter conversion errors (DO NOT SKIP!)
7. Verify all tests pass
8. Check complexity with `./scripts/check_complexity.sh`

### Before Declaring Work "Complete" - Verification Checklist

**⚠️ DO NOT say "done" or commit until ALL of these are verified:**

1. **Core functionality intact:**
   - [ ] List all remaining functions - do we have exactly what we expect?
   - [ ] No accidental deletions of needed functions
   - [ ] No orphaned/unused functions remaining

2. **All test levels passing:**
   - [ ] Unit tests pass (`make test`)
   - [ ] Integration tests pass (`make test-integration`)
   - [ ] E2E tests pass (`make test-e2e`) - NOT optional!

3. **Automated scripts verified:**
   - [ ] If used deletion/modification scripts, manually verify what was changed
   - [ ] Check line counts make sense (e.g., if deleting 5 functions, shouldn't delete 2000 lines)
   - [ ] Spot-check: open modified files and verify changes look correct

4. **Documentation updated:**
   - [ ] CHANGELOG.md if needed
   - [ ] API_REDESIGN_PLAN.md status updated
   - [ ] CODE_QUALITY.md complexity numbers updated if changed

**Common mistakes to avoid:**
- ❌ Assuming integration tests = E2E tests (they're different!)
- ❌ Trusting deletion scripts without verification
- ❌ Not checking if "additional kept functions" are actually used
- ❌ Declaring victory before running all three test levels

### Deleting Functions Safely

**⚠️ When using automated scripts to delete functions:**

1. **ALWAYS verify what will be deleted FIRST:**
   ```python
   # Good: Print what will be deleted, get confirmation
   print(f"Will delete {len(functions)} functions:")
   for func in functions:
       print(f"  - {func}")
   # Then delete
   ```

2. **Check line counts are reasonable:**
   - Deleting 5 functions shouldn't remove 2000 lines
   - If numbers look wrong, STOP and investigate

3. **Verify preserved functions:**
   ```bash
   # After deletion, check what remains
   grep "^    def " file.py | wc -l  # Should match expected count
   ```

4. **Test the script on a copy first:**
   ```bash
   cp file.py file.py.backup
   # Run script on file.py
   # Verify changes
   # If wrong: mv file.py.backup file.py
   ```

5. **Use git as safety net:**
   ```bash
   # If script deletes too much
   git checkout file.py  # Restore and fix script
   ```

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

---

## Maintaining Project Documentation

### When to Update CHANGELOG.md

Update `CHANGELOG.md` when you:
- **Complete a function implementation** - Add to "Added" section under current version
- **Change function signatures** - Add to "Changed - BREAKING" section
- **Fix bugs** - Add to "Fixed" section
- **Remove/consolidate functions** - Document in "Changed - BREAKING" with migration path

**Format:** Follow [Keep a Changelog](https://keepachangelog.com/) format  
**Version:** Use semantic versioning (MAJOR.MINOR.PATCH)  
**Scope:** Focus on what changed technically and how users are affected

**Example entry:**
```markdown
## [Unreleased]

### Changed - BREAKING
- **Consolidated update operations** - Removed `complete_task()`, `flag_task()`, `move_task()`
  - Use `update_task(task_id, completed=True, flagged=True, project_id=X)` instead
  - All field updates now go through single comprehensive function
```

### When to Update docs/ROADMAP.md

Update `docs/ROADMAP.md` when you:
- **Complete a major milestone** - Move items from "In Progress" to "Completed"
- **Change project phase** - Update current phase status
- **Add new planned features** - Document in appropriate phase section
- **Make architectural decisions** - Update "Open Questions" or relevant sections

**Current Phase:** API Redesign Implementation (update status as functions are implemented)

**Example update:**
```markdown
### In Progress 🔄
- [x] Implement redesigned API following docs/ARCHITECTURE.md
- [x] Write tests for new API (TDD approach)
- [ ] Verify all 16 functions work correctly
```

### When to Update docs/API_REFERENCE.md

**During implementation:** Use docs/API_REFERENCE.md as your specification reference. It documents the original 40-function API and the redesign proposals.

**After implementation is complete:** Update docs/API_REFERENCE.md to reflect the actual implemented API:
- Mark which "Enhanced proposed signatures" were implemented
- Document any deviations from the proposals (with rationale)
- Update return format documentation with actual formats
- Add "Implementation Notes" sections for tricky details discovered during implementation

**The file serves as:**
- Specification during implementation (read-only)
- Historical record after implementation (what we had → what we built)
- Reference for understanding evolution of the API

### When to Update docs/ARCHITECTURE.md

Update `docs/ARCHITECTURE.md` when you:
- **Discover new anti-patterns** - Add to anti-patterns section with explanation
- **Make architectural decisions** - Document the decision, rationale, and alternatives considered
- **Add worked examples** - When you solve a complex design problem, add an example
- **Clarify existing principles** - If something was confusing, improve the explanation
- **Find edge cases** - Document edge cases that inform future decisions

**DO update for:**
- New design patterns discovered during implementation
- Clarifications that would help future developers
- Examples that illustrate the principles better
- Architectural lessons learned from the implementation

**DO NOT update for:**
- Implementation details (those go in code comments)
- Bug fixes (those go in CHANGELOG.md)
- Routine code changes (those need no docs update)

### When to Update docs/TESTING.md

Update `docs/TESTING.md` when you:
- **Add new test types** - Document what they test and how to run them
- **Change test organization** - Update file structure examples
- **Add new fixtures** - Document what they provide
- **Change test requirements** - Update prerequisites or setup instructions
- **Update test coverage** - Refresh the coverage statistics tables
- **Add new edge cases** - Document what edge cases are now tested

**Example scenarios:**
- Added `test_api_redesign_*.py` files → Document in "Test Types" section
- Changed pytest configuration → Update "Running Tests" section
- New safety guard test → Update "Safety Guard Tests" section

### When to Update docs/CODE_QUALITY.md

Update `docs/CODE_QUALITY.md` when you:
- **Add intentionally complex function** - Document it with CC rating and rationale
- **Refactor complex function** - Update its CC rating
- **Change complexity thresholds** - Update the guidelines section
- **Update Radon configuration** - Document new settings

**Format for documenting complex functions:**
```markdown
### function_name() [Rating - CC XX]
**Why it's complex:**
- Reason 1 (e.g., 15 parameters for comprehensive filtering)
- Reason 2 (e.g., AppleScript must be self-contained)
- Reason 3 (e.g., Complex date handling logic)

**Documented in code:** See `file.py:line_number`
```

### When to Update docs/INTEGRATION_TESTING.md

Update `docs/INTEGRATION_TESTING.md` when you:
- **Add new integration tests** - Document what they test
- **Change test database setup** - Update setup instructions
- **Add new troubleshooting scenarios** - Document solutions
- **Change environment requirements** - Update prerequisites section

---

## After Redesign Implementation is Complete

### Overview

When the API redesign (40→16 functions) is complete, Claude Code should help transition the project from active development mode to maintenance mode. This includes updating documentation and streamlining this CLAUDE.md file itself.

### Step 1: Update Project Status
- [ ] Mark all implementation items as complete in this file (search for "In Progress 🔄")
- [ ] Update docs/ROADMAP.md phase status to "Complete ✅"
- [ ] **Create new version in CHANGELOG.md** (v1.0.0 for breaking changes, or v0.6.0 for minor)
- [ ] Add completion entry to CHANGELOG.md under new version with:
  - Summary of redesign (40→16 functions)
  - Migration guide reference
  - Breaking changes list

### Step 2: Update Documentation
- [ ] **Update docs/API_REFERENCE.md**:
  - Mark all "Enhanced proposed signatures" as "Implemented" or "Modified"
  - Document actual implemented signatures (if they differ from proposals)
  - Add "Implementation Notes" for any deviations from original design
  - Update return format examples with actual formats
- [ ] **Create docs/API_v1.md** documenting the final 16-function API:
  - Complete function signatures
  - Parameter descriptions
  - Return formats
  - Usage examples
  - Migration guide from v0.5.0
- [ ] **Update README.md**:
  - Replace examples with new API patterns
  - Update tool count (26→16)
  - Add migration guide link
  - Update feature list
- [ ] **Update docs/ARCHITECTURE.md** (if needed):
  - Add any new patterns discovered during implementation
  - Document any architectural decisions made during development
  - Add worked examples from implementation

### Step 3: Transition CLAUDE.md to Maintenance Mode

**IMPORTANT**: Once the redesign is verified complete and stable, streamline this CLAUDE.md file for maintenance mode.

#### 3.1 Create Archive

First, preserve the redesign-phase version:

```bash
# Archive the current comprehensive version
cp .claude/CLAUDE.md .claude/CLAUDE-redesign-phase.md

# Commit the archive
git add .claude/CLAUDE-redesign-phase.md
git commit -m "docs: archive redesign-phase CLAUDE.md for historical reference"
```

#### 3.2 Streamline CLAUDE.md

**Target**: Reduce from ~478 lines to ~250 lines by removing redesign-specific content.

**Sections to REMOVE** (they're in the archive if needed):
- "Working with Legacy Code" section (lines ~145-180)
  - Phase 1-4 migration pattern no longer needed
  - Deprecation strategies are complete
- "Starting the Redesign Implementation" section (lines ~181-220)
  - Step-by-step implementation guide no longer needed
  - First-time developer onboarding for redesign is complete
- "Testing Strategy for Redesign" section (lines ~221-260)
  - TDD during refactor guidance no longer needed
  - Keep only general testing requirements

**Sections to CONDENSE**:
- "Project Status" - Remove "In Progress" items, keep only:
  ```markdown
  ## Project Status
  
  **Current Version**: v1.0.0 (Maintenance Mode)
  **API Functions**: 16 core functions (redesign complete)
  **Test Coverage**: [update with final numbers]
  
  The API redesign (40→16 functions) completed [date]. 
  See `.claude/CLAUDE-redesign-phase.md` for historical implementation guidance.
  ```

- "After Redesign Implementation is Complete" - Remove this entire section (it's now done!)

**Sections to KEEP** (these are ongoing):
- 🚨 CRITICAL: Read This First (TDD, testing, code quality)
- Architecture & API Design (decision tree and principles)
- Common Development Tasks
- Maintaining Project Documentation
- Before Every Commit checklist
- Documentation Reference

#### 3.3 Update File Header

Change the intro to reflect maintenance mode:

```markdown
# OmniFocus MCP Server - Project Memory

**Last Updated:** [DATE]  
**Current Version:** v1.0.0 (Maintenance Mode)

**This file is automatically loaded by Claude Code when working on this project.**

The API redesign (40→16 functions) is complete. This file contains ongoing 
development guidelines for maintaining and enhancing the codebase.

**For redesign implementation history**: See `.claude/CLAUDE-redesign-phase.md`
```

#### 3.4 Execute Streamlining

**Before making changes**, Claude should:

1. **Verify redesign is truly complete**:
   - All 16 target functions implemented and tested
   - Migration guide published
   - Documentation updated
   - No outstanding "In Progress" items

2. **Show preview**:
   - Display sections that will be removed
   - Show condensed sections
   - Confirm total line count reduction (~250 lines target)

3. **Get approval**: 
   Ask user: "Ready to streamline CLAUDE.md for maintenance mode? This will:
   - Remove redesign-specific implementation guidance
   - Keep all critical rules and ongoing practices
   - Archive current version as CLAUDE-redesign-phase.md"

4. **Execute and commit**:
   ```bash
   # After manual edits or script-based modification
   git add .claude/CLAUDE.md
   git commit -m "docs: streamline CLAUDE.md for maintenance mode post-redesign"
   ```

### Step 4: Migration Period Management

During the deprecation period (one major version):

- [ ] Create `docs/MIGRATION_v1.0.md` with:
  - Complete function mapping (old→new)
  - Code examples for each change
  - Common patterns and replacements
  - Troubleshooting guide
- [ ] Add deprecation warnings to old functions
- [ ] Update all internal call sites to use new API
- [ ] Monitor user questions/issues about migration

### Step 5: Final Cleanup (v2.0.0)

When ready for next major version:

- [ ] Remove all deprecated functions from codebase
- [ ] Remove old tests (keep only v1.0.0+ tests)
- [ ] Move `docs/MIGRATION_v1.0.md` to `docs/archives/`
- [ ] Update `docs/ROADMAP.md` with next phase
- [ ] Update CHANGELOG.md with v2.0.0 entry

---

## Automation Suggestion for Claude Code

**For Claude Code**: When you detect that all implementation tasks are complete (by checking ROADMAP.md, test results, and this file), proactively suggest:

> "🎉 The API redesign appears complete! All 16 functions are implemented and tested.
> 
> Should I help you transition to maintenance mode? This includes:
> 1. Updating all documentation (CHANGELOG, API_REFERENCE, README)
> 2. Creating the v1.0.0 release
> 3. Streamlining CLAUDE.md for ongoing maintenance
> 
> I can show you a preview of changes before making them."

This ensures nothing is forgotten during the transition.

---

## If Something Goes Wrong

### Rollback Strategy

If the redesign causes critical issues:

1. **Immediate:** Revert to last known good commit
   ```bash
   git revert <commit-hash>
   ```

2. **Communication:** Document what broke in GitHub issue

3. **Analysis:** 
   - What tests didn't catch it?
   - Was it an integration test gap?
   - Was it a complexity issue?

4. **Fix Forward:**
   - Add regression test
   - Fix the issue
   - Re-deploy

**Prevention:**
- Run full test suite before committing
- Run integration tests with real OmniFocus
- Check complexity hasn't spiked
- Test with realistic data sizes

---

## Getting Help

### During Implementation

If you're stuck or uncertain:

1. **Check the decision tree** - 90% of questions answered by "Can existing function handle this?"
2. **Read docs/ARCHITECTURE.md** - Worked examples show how similar decisions were made
3. **Check docs/MIGRATION_v0.5.md** - See how we did the last consolidation
4. **Look at test patterns** - Existing tests show the expected patterns
5. **Check docs/CODE_QUALITY.md** - Maybe it's a complexity issue?

### Red Flags

**Stop and ask for human review if:**
- 🛑 Creating a new function rated D or F complexity
- 🛑 Test coverage drops below 85%
- 🛑 Breaking more than 10 existing tests
- 🛑 Unsure if a function should exist
- 🛑 Considering modifying docs/ARCHITECTURE.md in a major way

### Questions for Human

When asking for help, provide:
- What you're trying to accomplish
- What the decision tree suggested
- Why you think that might not apply
- What alternative you're considering
- Test results or complexity metrics if relevant

---

## Before Every Commit

**⚠️ IMPORTANT: Review "Before Declaring Work Complete - Verification Checklist" section above!**

**Run this checklist:**
- [ ] **Tests written first** - All new code has tests
- [ ] **All THREE test levels pass:**
  - [ ] Unit tests: `make test`
  - [ ] Integration tests: `make test-integration`
  - [ ] E2E tests: `make test-e2e` (DO NOT SKIP!)
- [ ] **Complexity checked** - Run `./scripts/check_complexity.sh`
- [ ] **Decision tree followed** - No new functions without consulting tree
- [ ] **Automated scripts verified** - If used, manually checked what changed
- [ ] **Core functions verified** - No accidental deletions, no orphaned functions
- [ ] **Documentation updated** - CHANGELOG.md, ROADMAP.md, or other docs if needed
- [ ] **Architecture followed** - Reviewed relevant sections of docs/ARCHITECTURE.md

**If tests are failing:**
- Don't commit until they pass
- If you can't fix them quickly, create a failing test as a TODO
- Document why the test is failing in the test itself
- Consider if this indicates an architectural problem

**If using automated deletion/modification scripts:**
- Verify line counts are reasonable
- Manually inspect changes in modified files
- Check that expected functions remain
- Use git to restore if anything went wrong

**Key principles:**
- Minimize functions - Prefer parameters on existing functions
- Prevent errors - Separate single/batch updates for unique fields
- Follow v0.5.0 pattern - See docs/MIGRATION_v0.5.md for consolidation approach
- Reference docs/ARCHITECTURE.md for any architectural questions (auto-imported)

---

## Documentation Reference

### Project Documentation Files

- **This file:** `.claude/CLAUDE.md` - Project memory and critical rules
- **Architecture:** @docs/ARCHITECTURE.md - Complete design rationale and worked examples
- **API Spec:** `docs/API_REFERENCE.md` - Original 40 functions with redesign proposals
- **Testing Guide:** `docs/TESTING.md` - Complete testing strategy, procedures, and coverage details
- **Code Quality:** `docs/CODE_QUALITY.md` - Complexity metrics, Radon guidelines, and quality thresholds
- **Integration Tests:** `docs/INTEGRATION_TESTING.md` - Real OmniFocus testing setup and troubleshooting
- **Migration Guide:** `docs/MIGRATION_v0.5.md` - v0.5.0 consolidation pattern
- **Project Roadmap:** `docs/ROADMAP.md` - Project history, phases, and status
- **Release History:** `CHANGELOG.md` - Version history and technical changes

### Quick Decision Guide

1. **Architecture questions** → See @docs/ARCHITECTURE.md (imported, always available)
2. **API design questions** → See docs/API_REFERENCE.md for proposed signatures
3. **Can I add this function?** → NO, check the decision tree first
4. **Should I write the test first?** → YES, always (see "Test-Driven Development" section at top)
5. **Is this field safe for batch updates?** → If it requires unique values (name/note), NO
6. **What's been implemented?** → See docs/ROADMAP.md for current status
7. **What changed recently?** → See CHANGELOG.md for version history
8. **How do I test this?** → See docs/TESTING.md for complete guide
9. **Is my code too complex?** → Run `./scripts/check_complexity.sh`
10. **How do I test with real OmniFocus?** → See docs/INTEGRATION_TESTING.md for setup and troubleshooting