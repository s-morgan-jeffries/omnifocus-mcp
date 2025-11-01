# Contributing to OmniFocus MCP Server

Thank you for your interest in contributing! This document outlines the development workflow and guidelines.

**Last Updated:** 2025-10-19

---

## Before Every Commit

**Run this checklist:**

- [ ] **Tests written first** - All new code has tests (see [Test-Driven Development](#test-driven-development) below)
- [ ] **All tests pass** - Run `make test`
- [ ] **Integration tests pass** - Run `make test-integration` (see `../guides/INTEGRATION_TESTING.md` for setup)
- [ ] **Complexity checked** - Run `./scripts/check_complexity.sh`
- [ ] **Decision tree followed** - No new functions without consulting tree (see `../../.claude/CLAUDE.md`)
- [ ] **Documentation updated** - CHANGELOG.md, ROADMAP.md, or other docs if needed
  - **If closing issue listed in ROADMAP.md:** Remove from "Upcoming Work" or other active sections
- [ ] **Architecture followed** - Reviewed relevant sections of `../reference/ARCHITECTURE.md`

**If tests are failing:**
- Don't commit until they pass
- If you can't fix them quickly, create a failing test as a TODO
- Document why the test is failing in the test itself
- Consider if this indicates an architectural problem

---

## Issue Tracking

This project uses GitHub Issues for tracking bugs, features, documentation gaps, and AI process failures.

### Before Starting Work

**Create a feature branch:**
```bash
git checkout -b feature/description  # New features
git checkout -b fix/description      # Bug fixes
git checkout -b docs/description     # Documentation
```

**Only work on main for:** Hotfixes, trivial typo fixes, emergency rollbacks

### Picking Issues to Work On

**Priority order for contributors:**
1. **Milestone issues first** - Pick from current milestone (highest priority)
2. **Backlog issues** - Good first contributions, lower priority
3. **New issues** - File an issue before starting significant work

**Before starting:**
- Check if issue is already assigned (avoid duplicate work)
- Assign yourself to the issue: `gh issue edit <number> --add-assignee @me`
- Comment on issue: "Working on this" (coordinates with others)

**If you're unsure which issue to pick:**
- Look for `good first issue` label
- Ask in issue comments: "Is this still needed?"
- Start with documentation or testing issues

### Filing Issues

**File issues immediately when you encounter:**
- **Bugs** → `bug` label
- **Feature requests** → `enhancement` label
- **Documentation gaps** → `documentation` label
- **AI process failures** (forgot tests, violated TDD, missed docs) → `ai-process` label

**AI process failure example:**
```bash
gh issue create \
  --title "[AI-PROCESS] Worked directly on main instead of feature branch" \
  --label "ai-process,tdd-violation,medium"
```

Use template `.github/ISSUE_TEMPLATE/ai-process-failure.md` for structured reporting.

### Issue Labeling Requirements

**Every issue MUST have labels.** Labels enable search, filtering, and project organization.

**Required: Type label (choose at least one):**
- `bug` - Something not working as expected
- `enhancement` - New feature or improvement
- `documentation` - Docs updates, missing docs, doc fixes
- `ai-process` - Process failure (forgot tests, violated TDD, etc.)
- `question` - Request for information or clarification

**Optional: Workflow labels (add all that apply):**
- `workflow` - Branch strategy, release process, CI/CD
- `release-process` - Version management, tagging, milestones
- `testing` - Test infrastructure, coverage, test fixes
- `technical-debt` - Code cleanup, refactoring, maintenance
- `security` - Security improvements, vulnerability fixes
- `performance` - Speed, efficiency, resource usage

**Optional: Priority labels (for bugs and ai-process only):**
- `critical` - Blocks release, major functionality broken
- `high` - Significant impact, needs attention soon
- `medium` - Moderate impact, normal priority
- `low` - Minor impact, nice to have

**Examples:**
```bash
# Bug with priority
gh issue create --label "bug,security,critical"

# Enhancement with workflow categories
gh issue create --label "enhancement,performance,release-process"

# Documentation update
gh issue create --label "documentation,workflow"

# AI process failure
gh issue create --label "ai-process,missing-tests,high"
```

**Enforcement:** Claude Code session hooks may warn about unlabeled issues.

### Version Planning Workflow

1. **Issues filed** → Start in Backlog (no milestone)
2. **Version planning** → Review issues, assign to milestone (e.g., "v0.7.0")
3. **Development** → Work on milestone issues
4. **Pre-release** → Verify all milestone issues closed
5. **Release** → Close milestone, tag version

---

## Branching Strategy (Trunk-Based Development)

**Version:** v0.6.3+

This project follows **trunk-based development** - a modern approach aligned with CI/CD best practices.

### Core Principles

**Single `main` branch:**
- Always releasable (all tests pass)
- May contain unreleased features
- Tags mark official releases (v0.6.3, v0.6.4, etc.)
- RC tags trigger comprehensive hygiene checks (v0.6.3-rc1, rc2, etc.)

**Feature branches:**
- Short-lived (merge within days, not weeks)
- Branch from main, PR back to main
- Deleted after merge

**No long-lived development branches** (no `develop`, no `staging`)

### Contributor Workflow

```bash
# 1. Fork and clone (external contributors)
git clone https://github.com/YOUR-USERNAME/omnifocus-mcp.git
cd omnifocus-mcp

# 2. Create feature branch from main
git checkout main
git pull upstream main  # Or origin if maintainer
git checkout -b feature/my-feature  # Or fix/bug-name

# 3. Make small, focused changes
# - Follow TDD (write tests first)
# - Commit frequently with clear messages
# - Reference issue numbers (#47, #56, etc.)

# 4. Push and create PR
git push origin feature/my-feature
gh pr create --base main --title "feat: description (#issue)"

# 5. CI runs automatically
# - All tests must pass
# - Hygiene checks must pass
# - Complexity within limits

# 6. After merge, delete branch
git branch -d feature/my-feature
```

### Release Workflow (Maintainers Only)

**Architecture:** Release branches + Branch protection on main

**📚 Complete Process:** See [docs/reference/RELEASE_PROCESS.md](../reference/RELEASE_PROCESS.md) for:
- Patch vs Minor vs Major release processes
- Interactive quality check requirements
- Automation criteria and tracking
- Complete checklists

**Quick Reference:** The workflow below covers patch releases. Minor/major releases require additional interactive quality checks.

```bash
# 1. All milestone features merged to main via PRs
# Milestone shows 0 open issues

# 2. Create release branch from main
git checkout main
git pull
git checkout -b release/v0.6.4

# 3. Bump version and update CHANGELOG (on release branch)
./scripts/sync_version.sh  # Or manual edit of pyproject.toml
# Edit CHANGELOG.md to add v0.6.4 entry
git commit -m "chore: bump version to v0.6.4"

# 4. Create RC tag (MUST be on release/* branch)
# Pre-tag hook enforces: RC tags only on release branches
# Hook runs 7 automated hygiene checks:
# - Captures results to .hygiene-check-results-v0.6.4-rc1.txt
# - Shows summary with critical/warning counts
# - Prompts to review warnings if found
# - Requires acknowledgment before proceeding
git tag v0.6.4-rc1

# 5. Review hygiene results
# If critical checks FAIL, you have two options:

# Option A: Fix issues and retry
# Fix the issues identified in the hygiene check results
git commit -m "fix: address hygiene check findings"
git tag v0.6.4-rc1  # Retry (will run checks again)

# Option B: Review and approve (if issues are acceptable)
# Review the results file to understand failures
less .hygiene-check-results-v0.6.4-rc1.txt
# After reviewing, approve to proceed anyway
./scripts/approve_hygiene_checks.sh v0.6.4-rc1
# This creates .hygiene-approved-v0.6.4-rc1 file
git tag v0.6.4-rc1  # Now proceeds with approval

# If only WARNINGS (non-critical):
# Hook prompts interactively:
#   "Review detailed results? (y/n)"
#   "Have you reviewed the warnings and decided they are acceptable? (y/n)"
# Answer 'y' to proceed

# 6. Push release branch + RC tag
git push origin release/v0.6.4
git push origin v0.6.4-rc1
# GitHub Actions runs same checks (automated only)

# 7. If RC finds issues in CI, fix on release branch
git commit -m "fix: address CI findings"
git tag v0.6.4-rc2  # Hook compares vs rc1, shows improvement
git push origin release/v0.6.4 v0.6.4-rc2

# 8. When RC passes, create PR: release/v0.6.4 → main
gh pr create --base main --head release/v0.6.4 \
  --title "Release v0.6.4" \
  --body "Release v0.6.4\n\nRC testing complete: v0.6.4-rc2 passed all checks"

# 9. After PR merged (via GitHub UI or gh pr merge)
git checkout main
git pull

# 10. Tag final release (MUST be on main)
# Pre-tag hook enforces: final tags only on main
git tag v0.6.4
git push origin v0.6.4
# GitHub Actions creates release, closes milestone

# 11. Clean up
git branch -d release/v0.6.4
git push origin --delete release/v0.6.4
```

**Hygiene Checks Run on RC Tags:**

**Automated checks (block release if fail):**
1. Version sync verification
2. All test suites (unit + integration + e2e)
3. Code complexity thresholds (CC ≤ 20 for new code, documented exceptions for get_tasks/update_task)
4. Client-server parity
5. Milestone status (all issues closed)
6. Test coverage ≥85% (minimum threshold enforced)
7. ROADMAP.md sync (closed issues removed from active sections)

**Interactive checks (required for minor/major releases, run manually via slash commands):**
- `/doc-quality` - Documentation quality assessment
- `/code-quality` - Code quality review (TODOs, print statements, bare except)
- `/test-coverage` - Test coverage analysis beyond 85% threshold
- `/directory-check` - Directory organization assessment

**Patch releases (v0.6.x):** Interactive checks optional (use as needed)
**Minor releases (v0.x.0):** Interactive checks REQUIRED before RC tag (hook prompts for confirmation)
**Major releases (vX.0.0):** Interactive checks REQUIRED + external review

**See:** [docs/reference/RELEASE_PROCESS.md](../reference/RELEASE_PROCESS.md) for complete requirements

**Results saved to:** `.hygiene-check-results-{TAG}.txt` (gitignored)

**Review-and-Approve Workflow:**

When hygiene checks fail, the pre-tag hook provides two paths:

1. **Fix and retry** (recommended for critical issues):
   - Review `.hygiene-check-results-{TAG}.txt`
   - Fix the identified issues
   - Retry: `git tag {TAG}` (checks run again)

2. **Review and approve** (for acceptable issues):
   - Review results file thoroughly
   - Decide issues are acceptable (e.g., known complexity, intentional TODOs)
   - Run: `./scripts/approve_hygiene_checks.sh {TAG}`
   - Creates approval file: `.hygiene-approved-{TAG}`
   - Retry: `git tag {TAG}` (now proceeds with approval)

**Important:** Approval is tag-specific. Each RC tag requires its own approval if checks fail.

**See:** `docs/reference/HYGIENE_CHECK_CRITERIA.md` for detailed pass/fail criteria

### Why Trunk-Based?

**Modern CI/CD best practice:**
- Faster feedback loops (no long-lived branch merges)
- Simpler mental model (one branch)
- Better for automation (CI on every PR)
- Fewer merge conflicts (frequent small merges)

**vs. GitFlow (deprecated approach):**
- GitFlow uses `main` + `develop` + `release/*` branches
- Designed for pre-CI/CD era with manual, risky releases
- Adds complexity without benefit in modern workflows

**Key difference:** Main is always releasable *because* of strong CI/CD, not in spite of development.

---

## Git Hooks Setup (Recommended)

Git hooks provide backup enforcement of workflow rules during manual git operations. While Claude Code hooks handle AI coding sessions, git hooks catch mistakes during manual command-line work.

### Installation

Install git hooks by creating symlinks in `.git/hooks/`:

```bash
# Install all hooks at once
ln -sf ../../scripts/git-hooks/pre-commit .git/hooks/pre-commit
ln -sf ../../scripts/git-hooks/commit-msg .git/hooks/commit-msg
ln -sf ../../scripts/git-hooks/pre-tag .git/hooks/pre-tag
```

Or install individually:
```bash
# Branch protection (blocks commits to main/master)
ln -sf ../../scripts/git-hooks/pre-commit .git/hooks/pre-commit

# Commit message formatting
ln -sf ../../scripts/git-hooks/commit-msg .git/hooks/commit-msg

# Release hygiene checks
ln -sf ../../scripts/git-hooks/pre-tag .git/hooks/pre-tag
```

### What Each Hook Does

**pre-commit** - Branch protection and mistake detection:
- Blocks commits to `main`/`master` branches (except hotfixes)
- Detects common mistakes (missing tests, server exposure, docs)
- **Allows hotfixes:** Include "hotfix" or "emergency" in commit message

**commit-msg** - Message formatting:
- Enforces conventional commit format
- Ensures commit messages follow project standards

**pre-tag** - Release quality gates:
- Runs hygiene checks on RC tags (`v*-rc*`)
- Creates `.hygiene-check-results-{TAG}.txt`
- Implements review-and-approve workflow (see [Release Process](#release-process))

### Hotfix Example

If you need to commit directly to main for an emergency:

```bash
# This will be blocked
git commit -m "fix urgent bug"

# This will be allowed
git commit -m "hotfix: fix critical production bug"
```

### Notes

- **Git hooks are optional but recommended** - They catch mistakes during manual git operations
- **Claude Code hooks are always active** - They run during AI coding sessions (primary enforcement)
- **Git hooks provide backup** - For manual operations outside of Claude Code sessions
- **Hooks can be bypassed** - Use `git commit --no-verify` if absolutely necessary (not recommended)

**See:** `.claude/CLAUDE.md` "Claude Code Hooks" section for primary enforcement mechanism

---

## Testing Setup

Before running tests, you'll need to understand the three test types and their setup requirements:

### Test Types

1. **Unit Tests** (`make test`) - Fast, always run
   - Mock AppleScript execution
   - No OmniFocus required
   - ~333 tests, ~2 minutes
   - **Skips integration and E2E tests by default** (this is expected behavior)

2. **Integration Tests** (`make test-integration`) - Real OmniFocus required
   - Execute real AppleScript commands
   - Requires test database setup (one-time)
   - ~92 tests, ~10-15 minutes
   - Catch bugs that mocks don't (syntax errors, API mismatches)

3. **E2E Tests** (`make test-e2e`) - Full MCP stack required
   - Test MCP tool → client → OmniFocus flow
   - Requires test database setup (one-time)
   - Catch parameter conversion bugs

### Setting Up Test Database (One-Time)

**Required for integration and E2E tests only.** Unit tests work immediately.

```bash
# Run the setup script
./scripts/setup_test_database.sh
```

This creates a dedicated `OmniFocus-TEST.ofocus` database with test data (projects, tasks, folders, tags) and configures environment variables.

**The Makefile handles environment variables automatically** - you don't need to set them globally. Just run:
```bash
make test-integration  # Integration tests with test database
make test-e2e          # E2E tests with test database
```

**For detailed setup instructions, troubleshooting, and manual testing procedures:**
See [docs/guides/INTEGRATION_TESTING.md](../guides/INTEGRATION_TESTING.md)

### Quick Test Reference

```bash
make test                  # Unit tests only (fast, no setup required)
make test-integration      # Real OmniFocus tests (requires one-time setup)
make test-e2e              # End-to-end MCP tests (requires one-time setup)
pytest tests/test_file.py  # Specific test file
```

**Note:** When you run `make test`, it's normal and expected that integration and E2E tests are skipped. This allows fast testing without requiring OmniFocus or test database setup.

---

## Test-Driven Development (TDD)

This project follows Test-Driven Development (TDD). **This is non-negotiable.**

**Before making ANY code changes:**

1. **Write a failing test first** that demonstrates the desired behavior
2. **Run the test** to confirm it fails
3. **Implement the minimal code** to make the test pass
4. **Run the test again** to confirm it passes
5. **Run all tests** to ensure no regressions

**Do NOT write implementation code before writing tests.**

### Why TDD?

- **Catches bugs early** - Tests written before code catch design issues
- **Better design** - Writing tests first leads to more testable code
- **Regression protection** - All functionality has tests from day one
- **Documentation** - Tests serve as executable documentation
- **Confidence** - Can refactor knowing tests will catch breakage

### Three Levels of Testing

This project requires three types of tests for comprehensive validation:

1. **Unit Tests** - Mock AppleScript, fast, run always (~333 tests, ~2 minutes)
2. **Integration Tests** - Real OmniFocus via client, catches AppleScript bugs (~92 tests, ~10-15 minutes)
3. **E2E Tests** - Full MCP tool → client → OmniFocus stack, catches parameter conversion bugs

**See [Testing Setup](#testing-setup) section above for how to set up and run each test type.**

**Complete testing strategy and coverage details:** See `../guides/TESTING.md`

---

## Code Quality Standards

**Before committing:**
```bash
./scripts/check_complexity.sh  # Check cyclomatic complexity
```

**Complexity targets:**
- **A-B rating (CC 1-10)**: Simple, easy to test ✅ **TARGET for new code**
- **C rating (CC 11-20)**: Acceptable for complex business logic ⚠️
- **D-F rating (CC 21+)**: Requires documentation or refactoring 🔴
  - **Document** if complexity is inherent to the problem
  - **Refactor** if complexity is accidental (can be simplified)

See `../reference/CODE_QUALITY.md` for complete metrics and guidelines.

**Code standards:**
- Python 3.10+ required
- Use type hints for all function parameters and return values
- Follow existing code patterns in the codebase
- AppleScript safety checks are enabled by default for production database protection

---

## Development Workflow

### Adding a New Function

**STOP!** Before adding a new function, check if existing functions can handle it:

1. **Can existing `update_X()` handle this?** (90% of cases: YES)
   - Setting a field? → Add to `update_task()` or `update_project()`
   - Example: Need to flag a task? → `update_task(task_id, flagged=True)`

2. **Can existing `get_X()` handle this with a parameter?** (9% of cases: YES)
   - Filtering data? → Add parameter to `get_tasks()` or `get_projects()`
   - Example: Need overdue tasks? → `get_tasks(overdue=True)`

3. **Is this truly specialized logic?** (1% of cases: MAYBE)
   - Positioning? Recursive operations? UI state changes?
   - Example: `reorder_task()` has complex before/after logic

**See `../../.claude/CLAUDE.md` for the full decision tree and anti-patterns.**

**If you need a new function:**
1. **Review `../reference/ARCHITECTURE.md`** anti-patterns section
2. **Write tests first** (see TDD above)
3. **Document your reasoning** in the function docstring
4. **Add example to `../reference/ARCHITECTURE.md`** if it establishes a new pattern
5. **Check complexity** with `./scripts/check_complexity.sh` after implementation

### Modifying Existing Function

1. **Write test first** demonstrating desired behavior
2. **Run test** to confirm it fails
3. **Implement minimal code** to pass the test
4. **Ensure changes follow `../reference/ARCHITECTURE.md`** principles
5. **Update both single and batch versions** if applicable (e.g., `update_task` and `update_tasks`)
6. **Run all tests** to verify no regressions
7. **Check complexity** hasn't increased significantly

---

## Getting Help

### When to Ask for Human Review

**Stop and ask if:**
- 🛑 Creating a new function rated D or F complexity
- 🛑 Test coverage drops below 85%
- 🛑 Breaking more than 10 existing tests
- 🛑 Unsure if a function should exist
- 🛑 Considering modifying `../reference/ARCHITECTURE.md` in a major way

### Questions for Humans

When asking for help, provide:
- What you're trying to accomplish
- What the decision tree suggested
- Why you think that might not apply
- What alternative you're considering
- Test results or complexity metrics if relevant

---

## Documentation Updates

### When to Update Each Doc

**CHANGELOG.md** - Update when you:
- Complete a function implementation (add to "Added" section)
- Change function signatures (add to "Changed - BREAKING" section)
- Fix bugs (add to "Fixed" section)
- Remove/consolidate functions (document in "Changed - BREAKING" with migration path)

**ROADMAP.md** - Update when you:
- Complete a major milestone (move from "In Progress" to "Completed")
- Change project phase (update current phase status)
- Add new planned features (document in appropriate phase section)
- Make architectural decisions (update "Open Questions" or relevant sections)

**API_REFERENCE.md** - Update when you:
- Implement new functions (mark as implemented)
- Change function signatures (document actual vs proposed)
- Add new parameters (update parameter lists)
- After implementation is complete (add "Implementation Notes")

**ARCHITECTURE.md** - Update when you:
- Discover new anti-patterns (add with explanation)
- Make architectural decisions (document decision, rationale, alternatives)
- Add worked examples (when solving complex design problems)
- Clarify existing principles (if something was confusing)
- Find edge cases (document for future reference)

**TESTING.md** - Update when you:
- Add new test types (document what they test and how to run)
- Change test organization (update file structure examples)
- Add new fixtures (document what they provide)
- Change test requirements (update prerequisites or setup)
- Update test coverage (refresh statistics tables)
- Add new edge cases (document what's now tested)

**CODE_QUALITY.md** - Update when you:
- Add intentionally complex function (document with CC rating and rationale)
- Refactor complex function (update its CC rating)
- Change complexity thresholds (update guidelines)
- Update Radon configuration (document new settings)

**INTEGRATION_TESTING.md** - Update when you:
- Add new integration tests (document what they test)
- Change test database setup (update setup instructions)
- Add troubleshooting scenarios (document solutions)
- Change environment requirements (update prerequisites)

### Interactive Quality Checks

The project includes slash commands for qualitative assessments:

#### `/doc-quality` - Documentation Quality

**When to run:**
- Before minor/major version releases
- After significant documentation changes
- When onboarding new contributors
- Quarterly documentation audits

**What it checks:**
- README completeness and accuracy
- Foundation model interpretability
- Cross-reference integrity (all links valid?)
- Technical accuracy (code examples match API?)
- Clarity, consistency, and completeness

#### `/code-quality` - Code Quality

**When to run:**
- Before minor/major version releases
- After significant code changes
- When addressing technical debt
- During code reviews
- Quarterly code quality audits

**What it checks:**
- Cyclomatic complexity (D-F rated functions)
- TODO/FIXME markers and technical debt
- print() statements vs logging
- Bare except clauses
- Line length and readability
- Comparison against project standards

#### `/test-coverage` - Test Coverage

**When to run:**
- Before minor/major version releases
- After adding new features or functions
- When addressing test gaps
- During code reviews
- Quarterly test quality audits

**What it checks:**
- Coverage metrics vs 85% threshold
- TODO test markers in source
- Untested public functions
- Coverage gaps by module
- Test quality (edge cases, mocking)
- Testing types assessment (performance, property-based, security, compatibility)

#### `/directory-check` - Directory Organization

**When to run:**
- Before minor/major version releases
- When onboarding new contributors
- After significant restructuring
- During project audits
- Quarterly organization reviews

**What it checks:**
- Directory structure logic and intuitiveness
- File organization and placement
- Documentation structure and findability
- Archive organization
- Configuration file placement
- New contributor clarity

**Output:** All commands generate comprehensive quality reports with severity levels (Critical/Recommended/Minor)

**See:** `.claude/CLAUDE.md` Slash Commands section for details

---

## Commit Message Guidelines

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): subject

body

footer
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation only
- `test:` Adding or updating tests
- `refactor:` Code change that neither fixes a bug nor adds a feature
- `perf:` Performance improvement
- `chore:` Changes to build process or auxiliary tools

**Examples:**
```
feat(api): add review_interval_weeks parameter to create_project()

docs: update API_REFERENCE.md with v0.6.0 final API

test: fix mock return values in test_project_activity_tracking

fix: update DESTRUCTIVE_OPERATIONS set for new function names
```

---

## Pull Request Process

1. **Create feature branch** from `main`:
   ```bash
   git checkout -b feature/description
   ```

2. **Follow TDD** - Write tests first, then implementation

3. **Run full test suite**:
   ```bash
   make test                 # Unit tests
   make test-integration     # Integration tests (if applicable)
   ./scripts/check_complexity.sh  # Complexity check
   ```

4. **Update documentation** as needed (see "Documentation Updates" above)

5. **Commit with clear messages** (see "Commit Message Guidelines" above)

6. **Push and create PR**:
   ```bash
   git push origin feature/description
   gh pr create --title "feat: description" --body "..."
   ```

7. **Address review feedback** if applicable

8. **Merge** when approved and all tests pass

---

## Continuous Integration (CI Monitoring)

### Automatic CI Monitoring

**When you push code, CI monitoring is automatic** (#36, #42):

1. **Post-bash hook activates** - Detects `git push` commands
2. **Waits for GitHub Actions** - Gives CI ~5 seconds to start
3. **Monitors run until completion** - Uses `gh run watch`
4. **Blocks if CI fails** - You must fix before continuing
5. **Reports success** - Confirms all checks passed

**You don't need to manually monitor CI** - the Claude Code hook handles it automatically.

### If CI Fails

When the hook detects a CI failure:

```
❌ GitHub Actions CI failed after your push
View failure details: https://github.com/.../actions/runs/...

Fetch logs with: gh run view <run-id> --log-failed

You must fix CI failures before continuing.
```

**Next steps:**
1. Review the failure URL or fetch logs: `gh run view <run-id> --log-failed`
2. Fix the issue locally
3. Commit and push the fix
4. Hook monitors again automatically
5. Continue when CI passes

### Manual CI Monitoring (if needed)

If you need to manually check CI status:

```bash
# View recent runs
gh run list --limit 5

# Watch specific run
gh run watch <run-id>

# View failure details
gh run view <run-id> --log-failed

# View full logs
gh run view <run-id> --log
```

### CI Checks

GitHub Actions runs on every push and PR:
- Unit tests (~2 min, ~333 tests)
- Integration tests (~10-15 min, ~92 tests)
- E2E tests (MCP stack)
- Code quality checks
- Complexity analysis

**All checks must pass before merging to main.**

### Troubleshooting

**"No GitHub Actions run found":**
- CI may not have triggered yet (wait a few seconds)
- Check manually: `https://github.com/<repo>/actions`
- Verify `.github/workflows/` files are present

**"gh CLI not found":**
- Install: `brew install gh`
- Authenticate: `gh auth login`

**Hook not running:**
- Verify hook is installed: `ls -la .claude/settings.json`
- Check hook script exists: `scripts/hooks/post_bash.sh`
- Restart Claude Code session (hooks load at startup)

**See:** `.claude/CLAUDE.md` "Claude Code Hooks" and "After Every Push" sections for details.

---

## Project Structure

```
omnifocus-mcp/
├── .claude/
│   ├── CLAUDE.md                    # Project memory (maintenance mode)
│   └── CLAUDE-redesign-phase.md     # Historical implementation guidance
├── docs/
│   ├── APPLESCRIPT_GOTCHAS.md       # AppleScript limitations reference
│   ├── ARCHITECTURE.md              # Design decisions and patterns
│   ├── API_REFERENCE.md             # Complete API documentation
│   ├── CODE_QUALITY.md              # Complexity guidelines
│   ├── CONTRIBUTING.md              # This file
│   ├── INTEGRATION_TESTING.md       # Real OmniFocus testing setup
│   ├── ROADMAP.md                   # Project phases and status
│   └── TESTING.md                   # Testing strategy and coverage
├── src/omnifocus_mcp/
│   ├── omnifocus_connector.py          # Core OmniFocus client (16 functions)
│   └── server_fastmcp.py            # FastMCP server (MCP tool wrappers)
├── tests/
│   ├── test_omnifocus_connector.py     # Client unit tests
│   ├── test_server_fastmcp.py       # Server unit tests
│   ├── test_integration_real.py     # Real OmniFocus integration tests
│   └── test_e2e_real.py             # End-to-end MCP tests
└── CHANGELOG.md                     # Version history
```

---

## Additional Resources

- **Architecture Principles:** `../reference/ARCHITECTURE.md`
- **API Design Decisions:** `docs/API_REFERENCE.md`
- **Testing Guide:** `../guides/TESTING.md`
- **AppleScript Issues:** `docs/APPLESCRIPT_GOTCHAS.md`
- **Project Status:** `docs/ROADMAP.md`
- **Daily Workflow:** `../../.claude/CLAUDE.md`

---

## Making a Release

**Version bumping workflow** (prevents issue #29 - version sync issues):

1. **Update pyproject.toml** (authoritative source)
   ```toml
   version = "X.Y.Z"
   ```

2. **Add CHANGELOG.md entry** with new version header
   ```markdown
   ## [X.Y.Z] - YYYY-MM-DD
   ### Added / Changed / Fixed
   ```

3. **Update CLAUDE.md** "Current Version" line
   ```markdown
   **Current Version:** vX.Y.Z
   ```

4. **Verify version consistency**
   ```bash
   # Future: scripts/check_version_sync.sh (not yet implemented)
   grep 'version = ' pyproject.toml
   grep 'Current Version' .claude/CLAUDE.md
   head -20 CHANGELOG.md
   ```

5. **Commit version bump**
   ```bash
   git add pyproject.toml CHANGELOG.md .claude/CLAUDE.md
   git commit -m "chore: bump version to vX.Y.Z"
   ```

6. **Tag release** (if publishing)
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push --tags
   ```

**For breaking changes:** Create migration guide (MIGRATION_vX.Y.md) before release.

---

## Questions?

If this document doesn't answer your question:

1. Check `../../.claude/CLAUDE.md` for quick reference
2. Review relevant specialized docs listed above
3. Search git history for similar changes
4. Ask in GitHub issues

Thank you for contributing!
