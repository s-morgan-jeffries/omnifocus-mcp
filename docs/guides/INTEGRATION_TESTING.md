# Integration Testing Guide

## Overview

Integration tests validate that the OmniFocus MCP server actually works with a real OmniFocus instance. Unlike unit tests (which mock AppleScript), integration tests execute real AppleScript commands.

**Why we need them:**
- Unit tests with mocks don't catch AppleScript syntax errors
- We've had multiple production bugs (`elifintervalDays`, `eliftaskDueDate`) that mocks didn't catch
- Only real execution validates the full AppleScript → OmniFocus flow

## Quick Start

### 1. Set Up Test Database (One-time)

**IMPORTANT:** Integration tests require a dedicated test database to avoid modifying your production data.

```bash
# Run the setup script
./scripts/setup_test_database.sh
```

This will:
1. Create test data in OmniFocus (folders, projects, tasks, tags)
2. Copy your database to `OmniFocus-TEST.ofocus`
3. Provide environment variable instructions

### 2. Configure Environment

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
export OMNIFOCUS_TEST_MODE=true
export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"
```

Then reload:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

### 3. Run Integration Tests

```bash
# Run all integration tests
make test-integration

# Or directly with pytest
pytest tests/test_integration_real.py -v

# Run a specific test
pytest tests/test_integration_real.py::TestRealOmniFocusIntegration::test_get_tasks_with_query_real -v
```

## What Gets Tested

### Read Operations (Safe)
✅ `test_get_projects_real` - Fetch all projects
✅ `test_search_projects_real` - Search projects by query
✅ `test_get_tasks_real` - Fetch all tasks
✅ `test_get_tasks_with_query_real` - **NEW v0.5.0** - Search tasks by text
✅ `test_get_inbox_tasks_real` - **NEW v0.5.0** - Get inbox with `inbox_only=True`
✅ `test_get_tags_real` - Fetch all tags

### Write Operations (Test Database Only)
✅ `test_add_task_real` - Create a new task
✅ `test_complete_task_real` - Mark task complete
✅ `test_add_tag_to_task_real` - Apply tags
✅ Safety guards prevent writes to production database

## Manual Testing

For quick debugging without full test setup:

```bash
# Run the manual diagnostic script (read-only, safe for production)
./venv/bin/python3 tests/test_manual_query.py
```

This script:
- ✅ Safe: Read-only operations
- Shows how many tasks you have
- Tests query filtering
- Tests inbox_only parameter
- Provides diagnostic output

**When to use manual tests:**
- Debugging query issues with your real data
- Quick verification after code changes
- Don't want to set up test database

**When to use integration tests:**
- Before committing code
- After fixing AppleScript bugs
- Testing write operations safely

## Test Database Maintenance

### Recreate Test Database

If your test database gets corrupted or outdated:

```bash
./scripts/setup_test_database.sh
# Answer 'y' when prompted to recreate
```

### Verify Test Data

```bash
# Check that test database has expected structure
pytest tests/test_integration_real.py::TestRealOmniFocusIntegration::test_get_projects_real -v -s
```

Should show:
- At least 2 test projects
- At least 3 test tasks
- At least 3 test tags
- At least 1 inbox task

### Switch Between Databases

OmniFocus can only have one database active at a time. To switch:

1. **To test database:**
   ```bash
   # Close OmniFocus
   # Rename databases
   mv ~/Library/.../OmniFocus.ofocus ~/Library/.../OmniFocus-PROD.ofocus
   mv ~/Library/.../OmniFocus-TEST.ofocus ~/Library/.../OmniFocus.ofocus
   # Reopen OmniFocus
   ```

2. **Back to production:**
   ```bash
   # Close OmniFocus
   # Rename databases
   mv ~/Library/.../OmniFocus.ofocus ~/Library/.../OmniFocus-TEST.ofocus
   mv ~/Library/.../OmniFocus-PROD.ofocus ~/Library/.../OmniFocus.ofocus
   # Reopen OmniFocus
   ```

**Better approach:** Use OmniFocus's built-in database switching (File → Open Database)

## Troubleshooting

### Tests are skipped

**Problem:** All integration tests show as "SKIPPED"

**Solution:** Check environment variables:
```bash
echo $OMNIFOCUS_TEST_MODE      # Should be "true"
echo $OMNIFOCUS_TEST_DATABASE  # Should be "OmniFocus-TEST.ofocus"
```

If not set, add to `~/.zshrc` and run `source ~/.zshrc`.

### "Permission denied" or "OmniFocus not responding"

**Problem:** AppleScript can't communicate with OmniFocus

**Solution:**
1. Open System Settings → Privacy & Security → Automation
2. Ensure Terminal (or your IDE) has permission to control OmniFocus
3. Restart OmniFocus

### "Database safety check failed"

**Problem:** Safety guards preventing writes to production database

**Solution:** This is correct behavior! Verify:
1. `OMNIFOCUS_TEST_MODE=true` is set
2. You're using the test database
3. The test database filename contains "-TEST"

### Query tests failing

**Problem:** `test_get_tasks_with_query_real` fails with 0 results

**Possible causes:**
1. Test database doesn't have tasks with "Test" in the name
2. AppleScript syntax error preventing query from running
3. Tasks are marked as completed (query filters incomplete by default)

**Debug:**
```bash
# Run manual script to see actual data
./venv/bin/python3 tests/test_manual_query.py

# Run test with verbose output
pytest tests/test_integration_real.py::TestRealOmniFocusIntegration::test_get_tasks_with_query_real -v -s
```

## CI/CD Integration

For GitHub Actions or other CI:

```yaml
# .github/workflows/test.yml
- name: Run unit tests
  run: pytest tests/ --ignore=tests/test_integration_real.py

# Integration tests are manual only (require local OmniFocus)
```

**Note:** Integration tests cannot run in CI because they require:
- macOS with OmniFocus installed
- Interactive AppleScript execution
- Manual database setup

They should be run locally before releases.

## Best Practices

### Before Committing Code

1. Run unit tests: `make test`
2. Run integration tests: `make test-integration`
3. If any test fails, fix before committing

### After Fixing AppleScript Bugs

1. Add a unit test that would catch the syntax pattern
2. Verify with integration test that it actually works
3. Consider adding to `test_applescript_syntax.py` typo list

### When Adding New Query Features

1. Add unit test with mocked data
2. Add integration test with real OmniFocus
3. Update test database setup script if needed

## Adding New Integration Tests

To add a new integration test:

```python
def test_new_feature_real(self, client):
    """Test description."""
    # Arrange - use test data from setup script
    # Act - call client method
    result = client.new_method()

    # Assert - verify results
    assert result is not None
    assert expected_condition

    # Optional: print confirmation
    print(f"\n✓ New feature works correctly")
```

**Guidelines:**
- Name tests `test_*_real` to indicate integration test
- Use test data created by `setup_test_database.sh`
- Verify both success cases and data structure
- Add helpful print statements for manual inspection

## Summary

| Test Type | When to Run | Speed | Safety |
|-----------|------------|-------|--------|
| Unit tests | Always | Fast | ✓ Safe |
| Integration tests | Before commits | Slow | ✓ Safe (test DB) |
| Manual tests | Debugging | Fast | ✓ Safe (read-only) |

**Key takeaway:** Integration tests caught 2 critical bugs that unit tests missed. Run them before releases!
