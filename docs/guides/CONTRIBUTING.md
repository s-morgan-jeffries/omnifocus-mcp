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

```bash
# 1. All milestone features merged to main
# Each PR has passed CI individually

# 2. Tag release candidate
git checkout main
git pull
git tag v0.6.3-rc1
git push --tags

# 3. GitHub Actions runs comprehensive hygiene checks
# - Test coverage review (subagent)
# - Documentation completeness (subagent)
# - Code quality review (subagent)
# - Directory organization (subagent)
# - Version sync verification
# - Milestone status (all issues closed)

# 4. If checks fail, fix and tag rc2
git commit -m "fix: address hygiene issues"
git tag v0.6.3-rc2
git push --tags

# 5. When all checks pass, tag final release
git tag v0.6.3
git push --tags
# GitHub Actions auto-creates release and closes milestone
```

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

See `../guides/TESTING.md` for complete details on:

1. **Unit Tests** - Mock AppleScript, fast, run always (~333 tests, ~2 minutes)
2. **Integration Tests** - Real OmniFocus via client, catches AppleScript bugs (3 tests, skipped by default)
3. **E2E Tests** - Full MCP tool → client → OmniFocus stack, catches parameter conversion bugs

**Quick commands:**
```bash
make test                  # All unit tests (fast)
make test-integration      # Real OmniFocus tests (requires setup)
make test-e2e              # End-to-end MCP tool tests (requires setup)
pytest tests/test_file.py  # Specific test file
```

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
