# OmniFocus MCP Server - Project Memory

**Last Updated:** 2025-10-25
**Current Version:** v0.6.5 (Integration Tests & CI)

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

**For redesign implementation history:** `docs/archive/CLAUDE-redesign-phase.md` (archived)

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

## Before Starting Work

**Create a feature branch for any non-trivial work:**

```bash
git checkout -b feature/description  # For new features
git checkout -b fix/description      # For bug fixes
git checkout -b docs/description     # For documentation
```

**Only work directly on main for:**
- Hotfixes that need immediate deployment
- Trivial documentation typos (single-line README fixes, etc.)
- Emergency rollbacks

**Why:** Feature branches allow you to:
- Test changes in isolation before merging
- Get feedback via PR before affecting main
- Easily roll back if something goes wrong
- Keep main branch stable and deployable

**See:** Issue #37 (ai-process) for why this matters

**Automated enforcement:** Claude Code hooks automatically prevent commits to main branch (see below).

---

## Claude Code Hooks (Automated Enforcement)

**Version:** v0.6.2+

This project uses Claude Code hooks to automatically enforce workflow compliance. Hooks run during Claude Code sessions and cannot be bypassed.

### Active Hooks

**PreToolUse(Bash) - Branch Validation** (#41)
- **Blocks:** Commits to main/master branch
- **Allows:** Hotfixes (message contains "hotfix" or "emergency")
- **Allows:** Commits to release/* branches (for release preparation)
- **Why:** Prevents working directly on main (#37)
- **Config:** `.claude/settings.json` → `scripts/hooks/pre_bash.sh`

**PreToolUse(Bash) - Issue Close Verification** (#66)
- **Blocks:** All `gh issue close` commands
- **Requires:** Verification of acceptance criteria before proceeding
- **Prompts:** Claude to review criteria, create tracking issues, get user approval
- **Bypass:** After user approval, prefix command with `CLAUDE_VERIFIED=1`
- **Why:** Prevents closing issues without verifying all acceptance criteria (#63)
- **Config:** `.claude/settings.json` → `scripts/hooks/pre_bash.sh`

**PostToolUse(Bash) - CI Monitoring** (#42)
- **Monitors:** GitHub Actions after every `git push`
- **Blocks:** Claude if CI fails (must fix before continuing)
- **Why:** Prevents unnoticed CI failures (#36, #39)
- **Config:** `.claude/settings.json` → `scripts/hooks/post_bash.sh`

**SessionStart - Project Context** (#43)
- **Loads:** Current branch, open issues, recent commits
- **Warns:** If on main branch at session start
- **Why:** Provides situational awareness
- **Config:** `.claude/settings.json` → `scripts/hooks/session_start.sh`

### How Hooks Work

Hooks are modular bash scripts that run automatically:
- **PreToolUse:** Before tool execution (can block commands)
- **PostToolUse:** After tool execution (can inform Claude of failures)
- **SessionStart:** At session start (injects context)

Each hook script has a modular design with `check_*` functions for easy extension.

### Hook Development

**To add new checks:**
1. Open relevant hook script (e.g., `scripts/hooks/pre_bash.sh`)
2. Add new `check_*` function
3. Add function name to `CHECKS` array
4. Test manually: `echo '{"tool_input":{"command":"test"}}' | ./scripts/hooks/pre_bash.sh`
5. **Restart Claude Code session** to activate (hooks load at startup)

**IMPORTANT:** Hook configuration is loaded at session start. Changes to hook scripts or `.claude/settings.json` require restarting Claude Code to take effect.

**Testing hooks:**
- Manual test: Use echo with JSON input (see step 4 above)
- Runtime test: Add debug logging to `/tmp/hook_name.log` and restart session
- Verify hook runs: Check log file after triggering relevant tool

**Documentation:**
- Complete guide: `docs/reference/CLAUDE_CODE_HOOKS.md`
- Comparison: `docs/reference/HOOKS_COMPARISON.md`
- Issue solutions: `docs/reference/HOOK_SOLUTIONS_FOR_ALL_ISSUES.md`

### Git Hooks (Backup Enforcement)

**Note:** Git hooks (`scripts/git-hooks/`) were the primary enforcement mechanism in v0.6.1 and earlier, but are now **secondary** to Claude Code hooks (v0.6.2+).

**Why Claude Code hooks are preferred:**
- Run during AI coding sessions (primary use case)
- Can block AI actions in real-time
- Modular design for easy extension
- Integrated with Claude Code workflow

**Git hooks provide backup enforcement for:**
- **Branch protection** - Blocks commits to main/master (except hotfixes) during manual git operations (#94)
- **Pre-commit mistake detection** - Validates commits (missing tests, server exposure, docs)
- **Commit message formatting** - Enforces conventional commit format
- **Release hygiene checks** - Runs quality gates on RC tags (pre-tag hook)

**Installation (recommended):**
```bash
ln -sf ../../scripts/git-hooks/pre-commit .git/hooks/pre-commit
ln -sf ../../scripts/git-hooks/commit-msg .git/hooks/commit-msg
ln -sf ../../scripts/git-hooks/pre-tag .git/hooks/pre-tag
```

Both systems coexist. Claude Code hooks are the primary enforcement mechanism, while git hooks provide backup validation during manual git operations.

---

## Before Every Commit

**Run this checklist:**
- [ ] **Tests written first** - All new code has tests (unit, integration, AND e2e)
- [ ] **All tests pass** - Run `make test` - NEVER merge feature branches without passing tests locally
- [ ] **Integration tests pass** - Run `make test-integration`
- [ ] **E2E tests pass** - Run `make test-e2e` (new/modified client functions need MCP tool tests)
- [ ] **Server exposure verified** - Run `./scripts/check_client_server_parity.sh`
- [ ] **Complexity checked** - Run `./scripts/check_complexity.sh`
- [ ] **Decision tree followed** - No new functions without consulting tree
- [ ] **Documentation updated** - CHANGELOG.md, ROADMAP.md, or other docs if needed
  - Verify cross-references exist; breaking changes need migration guide (MIGRATION_vX.Y.md pattern)
  - If tests added/removed: Update count in `docs/guides/TESTING.md` only (single source of truth)
  - **If fixing bug listed in ROADMAP.md:** Remove from "Upcoming Work" section after fix
  - **If completing roadmap item:** Update ROADMAP.md status (remove or move to "Completed" as appropriate)
  - **If closing issue listed in ROADMAP.md:** Remove from active sections (checked automatically via #34)
- [ ] **Architecture followed** - Reviewed relevant sections of `docs/ARCHITECTURE.md`
- [ ] **Automation tested end-to-end** - If adding workflow automation (hooks, scripts), verify it actually works:
  - Test happy path (automation allows correct behavior)
  - Test failure path (automation catches intentional errors)
  - Don't release automation that only has placeholder text
- [ ] **Issues filed with labels** - All new issues have appropriate labels (see Issue Tracking section)

**If tests are failing:**
- Don't commit until they pass
- If you can't fix them quickly, create a failing test as a TODO
- Document why the test is failing in the test itself
- Consider if this indicates an architectural problem

See `docs/guides/CONTRIBUTING.md` for complete pre-commit workflow.

---

## After Every Push

**CI Monitoring is Automatic:**

When you run `git push`, the PostToolUse(Bash) hook automatically:
1. Detects the push command
2. Waits 5 seconds for CI to start
3. Fetches the latest GitHub Actions run ID
4. Watches the run until completion (`gh run watch`)
5. **Blocks Claude if CI fails** - You must fix failures before continuing
6. Reports success if CI passes

**You don't need to manually monitor CI** - the hook handles it automatically (#42).

**If CI fails:**
- Hook shows the run URL and blocks further actions
- Fetch detailed logs: `gh run view <run-id> --log-failed`
- Fix the failure
- Push the fix (hook monitors again)
- Continue when CI passes

**Manual monitoring (if needed):**
```bash
# Get latest run
gh run list --limit 1

# Watch specific run
gh run watch <run-id>

# View failure logs
gh run view <run-id> --log-failed
```

**Note:** This automated monitoring prevents the mistake in #36 (pushing and not monitoring CI).

---

## Before Closing Issues

**CRITICAL: Check acceptance criteria before claiming an issue is "done".**

When resolving an issue:
- [ ] **Check acceptance criteria** - Every issue has acceptance criteria in its description
- [ ] **Verify ALL criteria met** - Not "mostly done" or "4/5" - ALL must be satisfied
- [ ] **Test the implementation** - Ensure solution actually works as specified
- [ ] **Close with verification** - Comment listing which commits address which criteria

**Example closing comment:**
```
Completed all acceptance criteria:
- ✅ Criterion 1: Description (commit abc123)
- ✅ Criterion 2: Description (commit def456)
- ✅ Criterion 3: Description (commit ghi789)
```

**NEVER claim an issue is "done" or "completed" without checking its acceptance criteria.**

---

## When Creating RC Tags (Release Process)

**Context:** Release candidates (RC tags like `v0.6.6-rc1`) trigger comprehensive hygiene checks via git pre-tag hook.

### Claude Code Behavior During RC Tag Creation

When you run `git tag v0.6.6-rc1`:

1. **Git pre-tag hook runs automatically** (not Claude Code hook)
   - Runs 9 hygiene checks (5 automated, 4 interactive)
   - Creates results file: `.hygiene-check-results-v0.6.6-rc1.txt`
   - Shows summary with critical/warning counts

2. **If critical checks FAIL**, hook provides two options:

   **Option A: Fix issues and retry**
   ```bash
   # Review what failed
   less .hygiene-check-results-v0.6.6-rc1.txt
   # Fix the issues
   git commit -m "fix: address hygiene check findings"
   # Retry (runs checks again)
   git tag v0.6.6-rc1
   ```

   **Option B: Review and approve** (for acceptable issues)
   ```bash
   # Review failures thoroughly
   less .hygiene-check-results-v0.6.6-rc1.txt
   # If issues are acceptable (e.g., known complexity), approve
   ./scripts/approve_hygiene_checks.sh v0.6.6-rc1
   # Retry (now proceeds with approval)
   git tag v0.6.6-rc1
   ```

3. **If only warnings** (non-critical), hook prompts interactively:
   - "Review detailed results? (y/n)"
   - "Have you reviewed the warnings and decided they are acceptable? (y/n)"
   - Answer 'y' to proceed

### When to Use Fix vs. Approve

**Use "Fix" for:**
- Version sync mismatches (always fix)
- Test failures (always fix)
- Complexity threshold violations on NEW code (refactor)
- Milestone has open issues (close or move them)

**Use "Approve" for:**
- Known complexity in documented exceptions (get_tasks, update_task)
- Intentional TODOs with tracking issues
- Directory organization suggestions (minor)
- Long lines in generated code or data

### Important Notes

- **Approval is tag-specific**: Each RC tag needs its own approval if checks fail
- **Don't abuse approval**: Use it for genuinely acceptable issues, not to skip quality checks
- **Document exceptions**: If approving complexity/quality issues, ensure they're documented in code
- **CI still runs**: GitHub Actions runs automated checks on push (may find additional issues)

**See:** `docs/reference/HYGIENE_CHECK_CRITERIA.md` for complete pass/fail criteria

---

## Issue Tracking

This project uses GitHub Issues for all tracking: bugs, features, documentation, and AI process failures.

### When to File Issues

**File immediately when you encounter:**
- **Bug:** Something not working as expected → label: `bug`
- **AI Process Failure:** Violated TDD, forgot tests, missed docs, workflow errors → label: `ai-process`
- **Feature Idea:** New functionality to consider → label: `enhancement`
- **Documentation Gap:** Missing or outdated docs → label: `documentation`

**All issues start in Backlog (no milestone assigned). They will be reviewed during version planning.**

### Labels (REQUIRED)

**Every issue MUST have labels applied.** Labels enable search, filtering, and project organization.

**Type labels (choose one):**
- `bug` - Something not working as expected
- `enhancement` - New feature or improvement
- `documentation` - Docs updates, missing docs, doc fixes
- `ai-process` - Process failure (forgot tests, violated TDD, etc.)

**Additional labels (choose all that apply):**
- `workflow` - Branch strategy, release process, CI/CD
- `release-process` - Version management, tagging, milestones
- `testing` - Test infrastructure, coverage, test fixes
- `technical-debt` - Code cleanup, refactoring, maintenance
- `security` - Security improvements, vulnerability fixes
- `performance` - Speed, efficiency, resource usage

**Severity labels (for bugs and ai-process only):**
- `critical` - Blocks release, major functionality broken
- `high` - Significant impact, needs attention soon
- `medium` - Moderate impact, normal priority
- `low` - Minor impact, nice to have

**Examples:**
```bash
# Bug with severity
gh issue create --label "bug,security,critical"

# Enhancement with categories
gh issue create --label "enhancement,performance,release-process"

# Documentation update
gh issue create --label "documentation,workflow"

# AI process failure
gh issue create --label "ai-process,missing-tests,high"
```

### Filing AI Process Failures

Use the "AI Process Failure" issue template:

```bash
gh issue create \
  --title "[AI-PROCESS] Brief description of what went wrong" \
  --label "ai-process,category,severity"
```

**Required labels:**
- `ai-process` (type)
- **Category:** `missing-docs`, `missing-tests`, `missing-automation`, `architecture-violation`, `tdd-violation`, or `other`
- **Severity:** `critical`, `high`, `medium`, or `low`

**Template includes:**
- What happened (clear description)
- Context (files, functions, commits, date)
- Impact on project/user
- Root cause analysis
- Prevention measures (immediate fix + long-term)
- Prevention script (executable bash for automated checking)

### Recurrence Handling

**Standard GitHub practice:** File new issue every time (don't search first)

During triage, human reviews and marks duplicates:
- Search for similar issues
- If duplicate: Add `duplicate` label, comment "Duplicate of #X", close
- Original issue tracks recurrences via linked duplicates
- Recurrence count = number of duplicate issues

### Automatic Recurrence Detection

The `check_recurrence.sh` script runs in CI to verify prevention measures:

```bash
./scripts/check_recurrence.sh
```

**How it works:**
- Fetches all open `ai-process` issues
- Extracts "Prevention Script" from each issue body
- Runs the script - if it fails, prevention has failed
- Reports which issues have recurred
- Human then files new issue, marks as duplicate

**Prevention scripts must be executable bash** in issue body:
```markdown
## Prevention Script

```bash
# Check if prevention is in place
if grep -q "checklist item" .claude/CLAUDE.md; then
    exit 0  # Prevention holding
else
    exit 1  # Prevention failed
fi
```
```

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
