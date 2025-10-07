# Testing Documentation

## Test Suite Overview

The OmniFocus MCP server has comprehensive test coverage with **67 tests** across 3 test files, all passing.

### Test Files

1. **[test_omnifocus_client.py](test_omnifocus_client.py)** - 26 tests
   - Unit tests for the OmniFocusClient class
   - Tests for AppleScript execution and error handling
   - Tests for all client methods (get_projects, add_task, add_note, search_projects)

2. **[test_server.py](test_server.py)** - 29 tests
   - Unit tests for MCP server handlers
   - Tests for all 4 MCP tools
   - Schema validation tests
   - Error handling and edge cases

3. **[test_integration.py](test_integration.py)** - 12 tests
   - End-to-end integration tests
   - Real-world usage scenarios
   - Multi-step workflows
   - Client state management

## Running Tests

### Run All Tests
```bash
./venv/bin/pytest
```

### Run Specific Test File
```bash
./venv/bin/pytest test_omnifocus_client.py
./venv/bin/pytest test_server.py
./venv/bin/pytest test_integration.py
```

### Run with Verbose Output
```bash
./venv/bin/pytest -v
```

### Run Specific Test
```bash
./venv/bin/pytest test_server.py::TestCallToolGetProjects::test_get_projects_success
```

## Test Coverage

### OmniFocusClient Coverage

#### `get_projects()`
- ✅ Successful project retrieval
- ✅ Empty projects list
- ✅ No output from AppleScript
- ✅ Invalid JSON parsing
- ✅ Subprocess errors
- ✅ Special characters in project data

#### `add_task()`
- ✅ Successful task addition
- ✅ Task with special characters (quotes, backslashes, newlines)
- ✅ Task without note
- ✅ Task addition failure
- ✅ Subprocess errors
- ✅ Empty strings

#### `add_note()`
- ✅ Successful note addition
- ✅ Note with special characters
- ✅ Note addition failure
- ✅ Subprocess errors
- ✅ Very long notes (10,000+ characters)

#### `search_projects()`
- ✅ Search by name
- ✅ Search by note content
- ✅ Search by folder path
- ✅ Case-insensitive search
- ✅ No results
- ✅ Multiple matches

### MCP Server Coverage

#### `list_tools()`
- ✅ Returns all 4 tools
- ✅ Schema validation for all tools

#### `call_tool("get_projects")`
- ✅ Success with multiple projects
- ✅ Empty projects list
- ✅ Long note truncation (>100 chars)
- ✅ Exception handling
- ✅ Empty folder paths display as "(root)"

#### `call_tool("search_projects")`
- ✅ Successful search
- ✅ No results
- ✅ Missing query parameter
- ✅ Empty query string
- ✅ Exception handling

#### `call_tool("add_task")`
- ✅ Success with note
- ✅ Success without note
- ✅ Missing project_id
- ✅ Missing task_name
- ✅ Special characters
- ✅ Task addition failure
- ✅ Exception handling

#### `call_tool("add_note")`
- ✅ Success
- ✅ Missing project_id
- ✅ Missing note_text
- ✅ Very long note (5,000+ chars)
- ✅ Note addition failure
- ✅ Exception handling

#### Unknown Tool Handling
- ✅ Returns appropriate error message

### Integration Test Coverage

#### Full Flow Tests
- ✅ Get projects end-to-end
- ✅ Search then add task workflow
- ✅ Special characters throughout stack
- ✅ Error propagation
- ✅ Multiple concurrent operations
- ✅ Empty database scenario
- ✅ Large dataset (100 projects)

#### Real-World Scenarios
- ✅ Project review workflow
- ✅ Failed task creation handling
- ✅ Unicode and emoji support (Japanese text, emojis)

#### Client State Tests
- ✅ Client instance reused across calls
- ✅ Client survives errors

## Edge Cases Tested

### String Handling
- ✅ Double quotes in strings
- ✅ Backslashes in strings
- ✅ Newlines and tabs
- ✅ Unicode characters (Japanese, Chinese, etc.)
- ✅ Emoji characters
- ✅ Markdown-like characters (**, _, `)
- ✅ Empty strings
- ✅ Very long strings (5,000-10,000 chars)

### Error Conditions
- ✅ AppleScript subprocess errors
- ✅ JSON parsing errors
- ✅ Empty output from AppleScript
- ✅ Invalid project IDs
- ✅ Missing required parameters
- ✅ OmniFocus not running
- ✅ Permission denied errors

### Data Conditions
- ✅ Empty projects list
- ✅ Projects with empty notes
- ✅ Projects with empty folder paths
- ✅ Large datasets (100+ projects)
- ✅ Projects with minimal data
- ✅ None as arguments

## Test Strategy

### Unit Tests
Unit tests use mocking to isolate components:
- Mock `run_applescript()` to test OmniFocusClient without AppleScript
- Mock `client` methods to test MCP server handlers independently
- Fast execution (<0.1s per file)

### Integration Tests
Integration tests mock only at the AppleScript boundary:
- Test full flow from MCP tool call through client
- Verify AppleScript commands are constructed correctly
- Test realistic multi-step workflows
- Still fast (<0.3s) due to AppleScript mocking

### Mocking Strategy
```python
# Client tests mock at AppleScript level
with mock.patch('omnifocus_client.run_applescript') as mock_run:
    mock_run.return_value = json.dumps([...])
    result = client.get_projects()

# Server tests mock at client method level
with mock.patch.object(server.client, 'get_projects', return_value=[...]):
    result = await server.call_tool("get_projects", {})
```

## Failure Modes Covered

1. **OmniFocus Application Issues**
   - App not running → Error message returned
   - Permission denied → Exception caught and returned as error
   - App crashed during operation → Subprocess error caught

2. **Data Issues**
   - Malformed JSON from AppleScript → Exception caught, error message returned
   - Empty results → Handled gracefully with "Found 0 projects"
   - Special characters breaking AppleScript → Properly escaped before sending

3. **Parameter Issues**
   - Missing required parameters → Clear error messages
   - Invalid project IDs → AppleScript error caught and returned
   - Empty/None values → Handled appropriately

4. **Resource Issues**
   - Very long notes/names → Handled without crashes
   - Large datasets → Processed successfully
   - Unicode/emoji → Full support

## Continuous Testing

### Before Committing
```bash
./venv/bin/pytest
```

### Before Releasing
```bash
./venv/bin/pytest -v --tb=long
```

### Testing with Real OmniFocus
To test with the actual OmniFocus application (not mocked):
1. Ensure OmniFocus is running
2. Remove/disable mocks in test files
3. Use test projects to avoid modifying real data

## Test Maintenance

### Adding New Features
When adding new features:
1. Write unit tests for the client method
2. Write unit tests for the server handler
3. Write integration test for the full flow
4. Test edge cases and error conditions

### Updating Tests
When updating code:
1. Run tests to ensure no regressions
2. Update tests if behavior changes
3. Add new tests for new edge cases discovered

## Known Limitations

- Tests use mocking and don't test actual AppleScript execution
- Tests don't verify AppleScript syntax correctness (would need real OmniFocus)
- Performance tests not included (all operations are I/O bound to OmniFocus)
- No tests for macOS permission prompts (OS-level)

## Future Test Improvements

- [ ] Add code coverage reporting (pytest-cov)
- [ ] Add performance/benchmark tests
- [ ] Add tests for concurrent MCP client connections
- [ ] Add manual test scenarios for real OmniFocus testing
- [ ] Add tests for AppleScript syntax validation
