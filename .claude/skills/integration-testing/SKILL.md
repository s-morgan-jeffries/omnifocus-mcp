---
name: integration-testing
description: Use when setting up, running, or debugging integration tests against real OmniFocus. Also use when unit tests pass but behavior seems wrong, when adding new AppleScript operations, or when you need to understand why mocked tests are insufficient for this project. Covers the test database system, fixture setup, and the specific class of bugs that only integration tests catch.
---

# OmniFocus Integration Testing

Unit tests in this project mock AppleScript execution. This is fast but dangerous — mocked tests cannot catch AppleScript-level bugs. Integration tests run against a real OmniFocus instance and have caught critical bugs that unit tests missed.

## Why Integration Tests Matter Here

**The `elifintervalDays` story:** A variable naming typo in AppleScript went undetected by 400+ unit tests because they mocked `run_applescript()`. The AppleScript was syntactically valid Python-side, but at runtime, AppleScript interpreted `elifintervalDays` as something unexpected. Only integration tests against real OmniFocus caught it.

**Classes of bugs only integration tests catch:**
- Variable naming conflicts with OmniFocus properties (see applescript-omnifocus skill)
- AppleScript syntax that's valid but produces wrong results
- OmniFocus version-specific behavior changes
- Timing issues with AppleScript execution
- Rich text handling inconsistencies
- Recurring task completion behavior differences

## Test Database Setup

Integration tests use a separate OmniFocus database to prevent production data corruption.

### Initial Setup
```bash
# Create test database in OmniFocus
# File > New Database > name it "OmniFocus-TEST"

# Set environment variables
export OMNIFOCUS_TEST_MODE=true
export OMNIFOCUS_TEST_DATABASE=OmniFocus-TEST.ofocus

# Generate test fixtures
./scripts/setup_test_database.sh
# Or for comprehensive test data:
./scripts/setup_comprehensive_test_data.sh
```

### Switching Databases
```bash
# Switch to test database (sets env vars, switches OmniFocus)
./scripts/local/switch_to_test_db.sh

# Switch back to production
./scripts/local/switch_to_prod_db.sh
```

### Cleaning Up
```bash
# Remove test data (keeps database)
./scripts/cleanup_test_data.sh

# Remove comprehensive test data
./scripts/cleanup_comprehensive_test_data.sh
```

## Running Integration Tests

```bash
# All integration tests
make test-integration

# Specific test file
pytest tests/test_integration_real.py -v

# E2E tests (full MCP stack)
make test-e2e
pytest tests/test_e2e_real.py -v
```

**Prerequisites:**
- OmniFocus must be running
- Test database must be active (check with `./scripts/local/switch_to_test_db.sh`)
- Test fixtures must be loaded

## Three-Tier Testing Strategy

| Tier | Speed | What it catches | When to run |
|------|-------|-----------------|-------------|
| **Unit** (mocked) | ~2min, 544 tests | Python logic errors, parameter validation, response formatting | Every change (`make test`) |
| **Integration** (real OF) | ~30s | AppleScript bugs, OmniFocus API quirks, variable naming conflicts | New AppleScript code, before merge |
| **E2E** (full MCP) | ~30s | MCP tool registration, parameter passing, end-to-end flow | New/modified tools, before release |

## Test Fixtures

The project uses TaskPaper-format fixtures for consistent test data. Test fixtures are defined in scripts and imported into OmniFocus via AppleScript.

**Key fixture scripts:**
- `scripts/setup_test_database.sh` — Basic fixtures (projects, tasks, tags)
- `scripts/setup_comprehensive_test_data.sh` — Extended fixtures for performance testing

**Fixture design principles:**
- Fixtures create known-state data that tests can assert against
- Each test file documents which fixtures it depends on
- Fixtures are idempotent — running setup twice doesn't create duplicates

## Writing Integration Tests

```python
import pytest

# Mark as integration test (skipped unless test DB is active)
@pytest.mark.integration
def test_create_and_retrieve_task():
    """Integration test against real OmniFocus."""
    client = OmniFocusConnector(enable_safety_checks=True)

    # Create
    task_id = client.create_task(name="Integration Test Task", project_name="Test Project")
    assert task_id is not None

    # Retrieve and verify
    tasks = client.get_tasks(task_id=task_id)
    assert len(tasks) == 1
    assert tasks[0]["name"] == "Integration Test Task"

    # Cleanup
    client.delete_tasks(task_id)
```

**Key patterns:**
- Always clean up created data (delete tasks/projects you create)
- Use `@pytest.mark.integration` to allow selective running
- Test against known fixture data when possible
- Verify both the happy path and error cases (e.g., invalid IDs)

## When to Write Integration Tests

**Always write integration tests when:**
- Adding or modifying AppleScript code
- Changing how data is serialized/deserialized from OmniFocus
- Adding new filter parameters to get_tasks() or get_projects()
- Modifying recurring task handling
- Changing date conversion logic

**Unit tests are sufficient when:**
- Changing Python-only logic (formatting, validation)
- Modifying server-level parameter handling
- Updating response formatting in server_fastmcp.py

## Detailed Setup Guide

For complete setup instructions including troubleshooting, see `docs/guides/INTEGRATION_TESTING.md`.
