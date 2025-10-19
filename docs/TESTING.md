# Testing Guide

This document describes the testing strategy and procedures for the OmniFocus MCP server.

## Table of Contents

- [Test Suite Overview](#test-suite-overview)
- [Database Safety](#database-safety)
- [Running Tests](#running-tests)
- [Test Types](#test-types)
- [Setting Up Real OmniFocus Testing](#setting-up-real-omnifocus-testing)
- [Test Coverage Details](#test-coverage-details)

## Test Suite Overview

The project has two types of tests:

1. **Unit Tests** - Test individual components with mocked dependencies
2. **Integration Tests (Real)** - Test with real OmniFocus (requires setup)

**Total Test Coverage**: 333 tests (v0.6.0)
- Unit tests (omnifocus_client.py core) ✅ All passing
- Unit tests (FastMCP server) ✅ All passing
- Integration tests (real OmniFocus) ⏭️ 123 skipped by default

**Test Execution**: ~0.53 seconds for all mocked tests
**Code Coverage**: 89% overall

## Database Safety

### ⚠️ CRITICAL: Production Database Protection

The OmniFocus client includes multi-layer safety guards to prevent accidental corruption of your production database:

**Safety Layers:**

1. **Environment Variable Checks**
   - `OMNIFOCUS_TEST_MODE` must be set to `true`
   - `OMNIFOCUS_TEST_DATABASE` must specify the test database name

2. **Database Name Whitelist**
   - Only these database names are allowed:
     - `OmniFocus-TEST.ofocus`
     - `OmniFocus-Dev.ofocus`
     - `OmniFocus-Staging.ofocus`

3. **Runtime Verification**
   - Before each destructive operation, AppleScript verifies the active database name
   - Operations are blocked if the name doesn't match expectations

**Protected Operations (v0.6.0 API):**
- `create_task`
- `create_project`
- `update_task`
- `update_tasks`
- `update_project`
- `update_projects`
- `delete_tasks`
- `delete_projects`

**Read-Only Operations** (always allowed):
- `get_projects`
- `get_tasks`
- `get_tags`
- `get_folders`
- `get_perspectives`

### How Safety Guards Work

```python
# WITHOUT test mode - operations are blocked
client = OmniFocusClient(enable_safety_checks=True)
client.create_task(...)  # ❌ Raises DatabaseSafetyError

# WITH test mode - operations verify database name
export OMNIFOCUS_TEST_MODE=true
export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"
client = OmniFocusClient(enable_safety_checks=True)
client.create_task(...)  # ✅ Verifies database, then proceeds

# For unit tests with mocked AppleScript
client = OmniFocusClient(enable_safety_checks=False)
client.create_task(...)  # ✅ No safety checks (for testing only!)
```

## Running Tests

### Quick Test (Unit + Integration with Mocks)

```bash
# Run all fast tests (no OmniFocus required)
pytest tests/

# Run with coverage
pytest tests/ --cov=src/omnifocus_mcp --cov-report=term-missing

# Run specific test file
pytest tests/test_omnifocus_client.py -v

# Run specific test
pytest tests/test_omnifocus_client.py::TestOmniFocusClient::test_create_task_success -v
```

### Safety Guard Tests

```bash
# Test that safety guards work correctly
pytest tests/test_safety_guards.py -v
```

These tests verify:
- Destructive operations are blocked without test mode ✅
- Database name verification works ✅
- Configuration validation is correct ✅
- Safety checks can be disabled for unit tests ✅
- Read-only operations always allowed ✅

### Real OmniFocus Integration Tests

**⚠️ WARNING**: These tests interact with a REAL OmniFocus database!

```bash
# Setup (one time)
./scripts/setup_test_database.sh

# Configure environment
export OMNIFOCUS_TEST_MODE=true
export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"

# Run real integration tests
pytest tests/test_integration_real.py -v
```

**Prerequisites:**
1. OmniFocus 4.x must be installed
2. OmniFocus must be running
3. Test database must be created (via setup script)
4. Test database must be the active database in OmniFocus
5. Environment variables must be set

## Test Types

### Unit Tests (`test_omnifocus_client.py`)

Tests individual client methods with mocked AppleScript execution.

**Coverage**: 79 tests
- AppleScript execution
- Project operations (get, search)
- Task operations (get, create, update, delete)
- Inbox operations
- Tag operations
- Edge cases (Unicode, special characters, long strings)
- Error handling

**Example (v0.6.0 API):**
```python
def test_create_task_success(self, client):
    """Test successful task creation."""
    with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
        mock_run.return_value = json.dumps({"success": True, "task_id": "task-001"})
        result = client.create_task(task_name="New Task", project_id="proj-001", note="Task note")
        assert result["success"] is True
```

### FastMCP Server Tests (`test_server_fastmcp.py`)

Tests MCP tool functions with mocked client.

**Coverage**: Tests for MCP tool layer (v0.6.0 API)
- Get client singleton pattern
- Project tools: get_projects, create_project, update_project, update_projects, delete_projects
- Task tools: get_tasks, create_task, update_task, update_tasks, delete_tasks, reorder_task
- Folder tools: get_folders, create_folder
- Perspective tools: get_perspectives, switch_perspective
- Tag tools: get_tags
- **Coverage**: Server layer wrapping client functions

**Example (v0.6.0 API):**
```python
async def test_full_flow_get_project_then_create_task(self):
    """Test getting a project and then creating a task in it."""
    with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
        # Get project
        mock_run.return_value = json.dumps([{"id": "proj-001", "name": "Project"}])
        project_result = await server.call_tool("get_projects", {"query": "test"})

        # Create task
        mock_run.return_value = json.dumps({"success": True, "task_id": "task-001"})
        create_result = await server.call_tool("create_task", {
            "project_id": "proj-001",
            "task_name": "Test Task"
        })
        assert create_result["success"] is True
```

### Safety Guard Tests (`test_safety_guards.py`)

Tests that verify the database safety system works correctly.

**Coverage**: 13 tests
- Operations blocked without test mode
- Database name verification
- Configuration validation
- Safety checks can be disabled for unit tests
- Read-only operations always allowed

**Example (v0.6.0 API):**
```python
def test_create_task_blocked_without_test_mode(self, client_with_safety):
    """Test that create_task is blocked without test mode."""
    with pytest.raises(DatabaseSafetyError) as exc_info:
        client_with_safety.create_task(task_name="Task Name", project_id="proj-001")
    assert "Cannot perform destructive operation" in str(exc_info.value)
```

### Real Integration Tests (`test_integration_real.py`)

Tests that interact with actual OmniFocus via AppleScript.

**Coverage**: 13 tests (skipped unless configured)
- Real project/task/tag retrieval
- Real task creation and modification
- Real completion and updates
- Real inbox operations
- Real tag operations
- Safety guard verification with real database

**Example (v0.6.0 API):**
```python
def test_create_task_real(self, client, test_project_id):
    """Test creating a task in real OmniFocus."""
    result = client.create_task(
        task_name="Integration Test Task",
        project_id=test_project_id,
        note="Created by integration test"
    )
    assert result["success"] is True

    # Verify it was created
    tasks = client.get_tasks(project_id=test_project_id)
    task_names = [t['name'] for t in tasks]
    assert "Integration Test Task" in task_names
```

## Setting Up Real OmniFocus Testing

### Step 1: Create Test Database

Run the setup script:

```bash
./scripts/setup_test_database.sh
```

This script will:
1. Verify your production database exists
2. Create a test database at the same location
3. Populate it with test data (projects, tasks, tags)
4. Provide instructions for environment variables

**Test Database Location:**
```
~/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application Support/OmniFocus/OmniFocus-TEST.ofocus
```

### Step 2: Configure Environment

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
export OMNIFOCUS_TEST_MODE=true
export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"
```

Or set for a single session:

```bash
export OMNIFOCUS_TEST_MODE=true
export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"
```

### Step 3: Switch to Test Database

**IMPORTANT**: OmniFocus 4.8.3 does not have a "File > Open Database" menu option.

To switch databases:

1. Close OmniFocus completely
2. Rename your production database temporarily:
   ```bash
   cd ~/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application\ Support/OmniFocus/
   mv OmniFocus.ofocus OmniFocus.ofocus.backup
   mv OmniFocus-TEST.ofocus OmniFocus.ofocus
   ```
3. Launch OmniFocus (will open the test database)
4. Run your tests
5. When done, switch back:
   ```bash
   cd ~/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application\ Support/OmniFocus/
   mv OmniFocus.ofocus OmniFocus-TEST.ofocus
   mv OmniFocus.ofocus.backup OmniFocus.ofocus
   ```

**Alternative**: Create an AppleScript or shell function to automate database switching.

### Step 4: Run Tests

```bash
# Verify environment
echo $OMNIFOCUS_TEST_MODE
echo $OMNIFOCUS_TEST_DATABASE

# Run tests
pytest tests/test_integration_real.py -v
```

### Step 5: Verify Safety Guards

After running tests, verify in OmniFocus:
- Check that test tasks were created
- Verify your production database was not modified
- Confirm the test database name matches expectations

## Test Coverage Details

### Coverage by File

| File | Statements | Coverage | Missing Lines |
|------|:----------:|:--------:|:-------------:|
| `omnifocus_client.py` | 425 | **97%** | 13 (mostly error handling) |
| `server_fastmcp.py` | 328 | **73%** | 90 (mostly optional formatting) |
| `server.py` (legacy) | 214 | **96%** | 9 (error edges) |
| **Overall** | **970** | **88%** | **112** |

### Client Operations Coverage (v0.6.0 API)

**Note:** All 16 core v0.6.0 MCP tools have comprehensive unit and integration test coverage. The table below represents test counts from the v0.5.0 era with 25+ functions. For detailed current test coverage, see test files in `tests/` directory.

**Current Test Summary (v0.6.0):**
- **333 passing tests** across all 16 MCP tools
- Unit tests: Mock-based testing of all client functions
- Integration tests: Real OmniFocus database testing
- FastMCP tests: Server-level MCP tool testing
- Full coverage of create/get/update/delete operations for tasks, projects, folders, tags, perspectives

### Edge Cases Tested

**String Handling:**
- ✅ Double quotes in strings
- ✅ Backslashes in strings
- ✅ Newlines and tabs
- ✅ Unicode characters (Japanese, Chinese, etc.)
- ✅ Emoji characters
- ✅ Markdown-like characters (**, _, `)
- ✅ Empty strings
- ✅ Very long strings (5,000-10,000 chars)

**Error Conditions:**
- ✅ AppleScript subprocess errors
- ✅ JSON parsing errors
- ✅ Empty output from AppleScript
- ✅ Invalid project/task IDs
- ✅ Missing required parameters
- ✅ Database safety violations

**Data Conditions:**
- ✅ Empty result lists
- ✅ Projects/tasks with empty fields
- ✅ Large datasets (500 projects)
- ✅ Deep folder hierarchies (5 levels)
- ✅ None as arguments

**Date/Time Edge Cases:**
- ✅ Past dates (2020-01-01)
- ✅ Far future dates (2030-12-31)
- ✅ Defer date after due date (logically odd but valid)
- ✅ Task with only defer date (no due date)
- ✅ Clearing dates (update to empty string)

**Task Property Edge Cases:**
- ✅ Multiple tags on single task (4 tags)
- ✅ Very long tag list (15 tags)
- ✅ Extremely long notes (5000+ characters)
- ✅ Task with all properties at maximum values
- ✅ Rapid operations (10 tasks in sequence)
- ✅ Mixed operation sequences (create → read → update → read → complete)

## Test Development Guidelines

### Adding New Tests

1. **Unit tests** for new client methods go in `test_omnifocus_client.py`
2. **FastMCP server tests** go in `test_server_fastmcp.py`
3. **Real integration tests** go in `test_integration_real.py`
4. **Safety guard tests** go in `test_safety_guards.py`

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Use descriptive names: `test_add_task_with_due_date_and_flags`

### Fixtures

Always disable safety checks for mocked tests:

```python
@pytest.fixture
def client(self):
    """Create a client instance for testing."""
    return OmniFocusClient(enable_safety_checks=False)
```

Enable safety checks for real integration tests:

```python
@pytest.fixture
def client(self):
    """Create a client for real OmniFocus testing."""
    return OmniFocusClient(enable_safety_checks=True)
```

### Mocking AppleScript

Use `unittest.mock` to mock AppleScript execution:

```python
from unittest import mock

def test_something(self, client):
    with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
        mock_run.return_value = "expected output"
        result = client.some_method()
        assert result == expected
```

## Continuous Integration

The test suite is designed to run in CI without requiring OmniFocus:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pytest tests/ --cov=src/omnifocus_mcp --cov-report=xml
```

Real integration tests are skipped automatically when `OMNIFOCUS_TEST_MODE` is not set.

## Troubleshooting

### "Database safety check FAILED"

**Cause**: You're trying to run destructive operations against the production database.

**Solution**:
1. Verify environment variables are set
2. Switch to test database in OmniFocus
3. Verify database name matches `OMNIFOCUS_TEST_DATABASE`

### "Cannot perform destructive operation without test mode"

**Cause**: `OMNIFOCUS_TEST_MODE` is not set to `true`.

**Solution**:
```bash
export OMNIFOCUS_TEST_MODE=true
export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"
```

### "No module named 'omnifocus_mcp'"

**Cause**: Package not installed or wrong Python environment.

**Solution**:
```bash
# Activate virtual environment
source venv/bin/activate

# Install in development mode
pip install -e .
```

### "OmniFocus error: Application isn't running"

**Cause**: OmniFocus is not running.

**Solution**: Launch OmniFocus before running real integration tests.

### Tests hang or timeout

**Cause**: AppleScript waiting for user interaction or OmniFocus is busy.

**Solution**:
1. Close any open OmniFocus dialogs
2. Make sure OmniFocus is not syncing
3. Try running tests one at a time with `-v` flag

## Safety Checklist

Before running real integration tests:

- [ ] Test database created (`./scripts/setup_test_database.sh`)
- [ ] Environment variables set (`OMNIFOCUS_TEST_MODE`, `OMNIFOCUS_TEST_DATABASE`)
- [ ] Test database is active in OmniFocus
- [ ] Production database is backed up (optional but recommended)
- [ ] You understand that tests will modify the active database

**If in doubt, run with safety checks enabled. The system will block operations if configuration is incorrect.**

## Test Metrics

- **Total Tests**: 333 (v0.6.0 - reduced from 393 in v0.5.0)
- **Passing**: 333 (all unit tests with mocks)
- **Skipped**: 123 (integration tests, require real OmniFocus setup)
- **Execution Time**: ~110s for all unit tests
- **Test Reduction**: v0.6.0 API consolidation removed deprecated function tests
  - Unit tests (FastMCP server): 33 tests
  - Real OmniFocus tests: 3 tests (skipped by default)
- **Code Coverage**: 89% overall
  - `omnifocus_client.py`: 97%
  - `server_fastmcp.py`: 73%
