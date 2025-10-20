# Developer Guides

Essential guides for daily development work on the OmniFocus MCP Server.

## Quick Start for New Contributors

**Read in this order:**
1. [CONTRIBUTING.md](#contributingmd) - Start here - development workflow and TDD requirements
2. [TESTING.md](#testingmd) - Daily reference for running tests and understanding coverage
3. [INTEGRATION_TESTING.md](#integration_testingmd) - Setup for real OmniFocus testing

**Before every commit:**
- ✅ Tests written first (TDD approach)
- ✅ All tests pass (`make test`)
- ✅ Complexity checked (`./scripts/check_complexity.sh`)
- ✅ Architecture principles followed

---

## Documents

### CONTRIBUTING.md

**Purpose:** Complete development workflow, TDD requirements, and pre-commit checklist

**Read this FIRST** if you're new to the project.

**When to use:**
- ✅ Setting up your development environment
- ✅ Before making any code changes (understand TDD workflow)
- ✅ Before committing (check pre-commit checklist)
- ✅ Understanding code review process
- ✅ Learning project conventions

**Key sections:**
- **Test-Driven Development (TDD)** - Non-negotiable requirement, write tests first
- **Development Workflow** - Step-by-step process for changes
- **Pre-Commit Checklist** - What to verify before committing
- **Code Standards** - Type hints, naming conventions, formatting
- **Architecture Guidelines** - When to add functions, decision tree reference

**Size:** ~12KB - Comprehensive workflow guide

**Critical rule:** Always write tests BEFORE implementation. The project follows strict TDD.

**Also see:** `../../.claude/CLAUDE.md` for project memory and context loaded by Claude Code

### TESTING.md

**Purpose:** Testing strategy, test types, running tests, and coverage details

**Daily reference** for test operations.

**When to use:**
- ✅ Running tests (`make test`, `make test-integration`)
- ✅ Understanding test coverage (89% overall, detailed breakdown included)
- ✅ Writing new tests (see test patterns and examples)
- ✅ Debugging test failures
- ✅ Understanding what each test file covers

**Key sections:**
- **Quick Commands** - `make test`, `make test-integration`, `pytest tests/test_file.py`
- **Test Types** - Unit (fast, mocked), Integration (real OmniFocus), E2E
- **Test Coverage Details** - 89% overall, broken down by module
- **Test Organization** - What each test file covers (33 test files total)
- **Writing Tests** - Patterns, fixtures, best practices

**Test count:** 333 passing tests

**Coverage breakdown:**
- omnifocus_client.py: 94% (core implementation)
- server_fastmcp.py: 82% (MCP server)
- Overall: 89%

**Size:** ~16KB - Comprehensive testing reference

### INTEGRATION_TESTING.md

**Purpose:** Real OmniFocus testing setup, troubleshooting, and procedures

**When to use:**
- ✅ Setting up test OmniFocus database (first time setup)
- ✅ Running real OmniFocus tests (catches AppleScript bugs unit tests miss)
- ✅ Troubleshooting AppleScript errors
- ✅ Debugging why tests pass but real OmniFocus behavior is wrong
- ✅ Understanding test database requirements

**Key sections:**
- **Setup Instructions** - Creating test database, environment variables
- **Running Integration Tests** - `make test-integration`, timeout configuration
- **Troubleshooting** - Common issues and solutions
- **Test Database Management** - Setup scripts, clean state verification
- **Why Integration Tests Matter** - Examples of bugs only caught by real OmniFocus

**Size:** ~7KB - Focused on integration testing

**Critical lessons learned:**
- Unit tests with mocks didn't catch typos like `elifintervalDays` or `eliftaskDueDate`
- Only real OmniFocus execution caught these bugs
- Always run integration tests before committing significant changes

**Related:** See `../reference/APPLESCRIPT_GOTCHAS.md` for AppleScript-specific issues

---

## How These Guides Work Together

### First Time Setup

1. **Read CONTRIBUTING.md** - Understand TDD workflow and project standards
2. **Follow setup steps** in CONTRIBUTING.md - Install dependencies, configure environment
3. **Run initial tests** using commands from TESTING.md - Verify environment works
4. **Setup integration testing** using INTEGRATION_TESTING.md - Create test database

### Daily Development

1. **Write test first** (CONTRIBUTING.md TDD section)
2. **Run tests frequently** (TESTING.md quick commands)
3. **Check complexity** before committing (CONTRIBUTING.md pre-commit checklist)
4. **Run integration tests** for significant changes (INTEGRATION_TESTING.md)

### Debugging

1. **Start with TESTING.md** - Understand what the failing test covers
2. **Check test patterns** in TESTING.md - Verify test is correctly structured
3. **If integration test fails** - See INTEGRATION_TESTING.md troubleshooting
4. **If AppleScript error** - Consult `../reference/APPLESCRIPT_GOTCHAS.md`

### Code Review

1. **CONTRIBUTING.md checklist** - Verify all items checked
2. **TESTING.md coverage** - Ensure tests exist and pass
3. **INTEGRATION_TESTING.md** - Verify integration tests run if needed

---

## Common Development Tasks

### Running Tests

```bash
# All unit tests (fast, ~0.53s)
make test

# Integration tests (real OmniFocus, ~10-30s)
make test-integration

# Specific test file
pytest tests/test_omnifocus_client.py -v

# Specific test
pytest tests/test_omnifocus_client.py::test_create_task -v
```

See [TESTING.md](#testingmd) for more commands and options.

### Before Committing

```bash
# 1. All tests pass
make test

# 2. Check complexity
./scripts/check_complexity.sh

# 3. Run integration tests for significant changes
make test-integration

# 4. Review pre-commit checklist in CONTRIBUTING.md
```

### Setting Up Integration Testing

```bash
# 1. Create test database (see INTEGRATION_TESTING.md for details)
./scripts/setup_test_database.sh

# 2. Set environment variable
export OMNIFOCUS_TEST_MODE=true
export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"

# 3. Run integration tests
make test-integration
```

---

## TDD Workflow (Critical)

**From CONTRIBUTING.md - This is NON-NEGOTIABLE:**

1. **Write test first** - Demonstrates desired behavior
2. **Run test** - Verify it fails (confirms test is valid)
3. **Implement minimal code** - Make test pass
4. **Run test again** - Verify it passes
5. **Run all tests** - Ensure no regressions
6. **Check complexity** - Run `./scripts/check_complexity.sh`

**DO NOT write implementation before tests.**

This project has 89% test coverage because TDD is strictly followed. Keep it that way.

---

## Key Project Standards

**From CONTRIBUTING.md:**

- **Type hints required** for all function parameters and return values
- **Python 3.10+ features** allowed and encouraged
- **Complexity targets:**
  - A-B rating (CC 1-10): Target for new code
  - C rating (CC 11-20): Acceptable for complex business logic
  - D-F rating (CC 21+): Requires documentation or refactoring
- **Architecture principles:** Follow decision tree in `../reference/ARCHITECTURE.md`
- **Database safety:** AppleScript safety checks enabled by default

**Test standards (from TESTING.md):**
- Unit tests: Mock all OmniFocus interactions
- Integration tests: Real OmniFocus, test database only
- E2E tests: Full workflow verification
- Target: 90% coverage (currently 89%)

---

## See Also

- **Architecture Principles:** `../reference/ARCHITECTURE.md` - Design patterns and decision-making
- **API Reference:** `../reference/API_REFERENCE.md` - Complete API documentation
- **Code Quality:** `../reference/CODE_QUALITY.md` - Complexity metrics and standards
- **Project Guidelines:** `../../.claude/CLAUDE.md` - Project memory for Claude Code
- **Roadmap:** `../project/ROADMAP.md` - Current state and future work

---

## Document Maintenance

### When to Update

**CONTRIBUTING.md:**
- Changes to development workflow
- New TDD requirements
- Updated code standards
- New pre-commit checks

**TESTING.md:**
- Test count changes
- Coverage percentage updates
- New test types added
- Testing procedure changes

**INTEGRATION_TESTING.md:**
- New integration test setup steps
- Troubleshooting new issues
- Environment requirement changes
- Test database setup changes

---

**Last Updated:** October 20, 2025
