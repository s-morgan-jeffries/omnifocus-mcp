# AppleScript and OmniFocus Limitations

**Purpose:** Documents known limitations, workarounds, and gotchas when working with OmniFocus via AppleScript.

**Last Updated:** 2025-10-19

---

## Rich Text Notes

- ❌ **Cannot read formatted/rich text** (OmniFocus API limitation)
- ✅ **Can only access plain text** via AppleScript
- ⚠️ **Updating notes removes all formatting**
- **Implication:** Document this warning in all note-related functions

**Technical Details:**
- OmniFocus supports rich text in notes (bold, italic, links, etc.)
- AppleScript API only exposes the plain text content
- OmniAutomation (JavaScript API) has RTF access but cannot be called externally with result retrieval
- When you update a note via AppleScript, any existing rich text formatting is lost

**Workaround:** None available. Document the limitation clearly in function descriptions.

---

## Variable Naming Conflicts

- ❌ **Don't use OmniFocus property names as variable names**
- **Problem:** Variable names that match OmniFocus properties cause silent failures
- **Common culprits:** `recurrence`, `repetitionMethod`, `dueDate`, `deferDate`

**Examples of bugs caused by this:**
```applescript
-- BAD: Variable name conflicts with property
set recurrence to "FREQ=WEEKLY"  -- FAILS silently
set task's recurrence to recurrence  -- Doesn't work!

-- GOOD: Use suffix to avoid conflict
set recurrenceStr to "FREQ=WEEKLY"
set task's recurrence to recurrenceStr  -- Works!
```

**Solution:** Use suffixes like `Str`, `Value`, or descriptive names:
- `recurrence` → `recurrenceStr` or `recurrenceValue`
- `repetitionMethod` → `repetitionMethodStr`
- `dueDate` → `dueDateValue`

**Reference:** See CHANGELOG.md v0.5.0 for bug details (`elifintervalDays`, `eliftaskDueDate` typos)

---

## Recurring Tasks

- ✅ **Use `mark complete` command** instead of setting `completed` property
- ❌ **Direct property setting fails** for recurring tasks
- **Reason:** Recurring tasks need special handling to create the next instance

**Correct Pattern:**
```applescript
tell application "OmniFocus"
    tell front document
        set theTask to first flattened task whose id is "task-id"
        mark complete theTask  -- Creates next recurrence
    end tell
end tell
```

**Incorrect Pattern:**
```applescript
-- DON'T DO THIS for recurring tasks
set completed of theTask to true  -- Doesn't create next instance!
```

**Reference:** See CHANGELOG.md v0.5.0 for implementation details

---

## Performance Characteristics

**Context:** OmniFocus operations via AppleScript can be slow for large databases.

**Benchmarks (from production use):**
- `get_tasks()` - ~738 tasks in 13-17 seconds
- Default timeout: 60s, configurable to 300s
- Batch operations are significantly more efficient than loops

**Implementation Guidelines:**

### 1. Avoid N+1 Queries
```python
# BAD: N+1 pattern (slow)
for task_id in task_ids:
    task = get_task(task_id)  # Separate AppleScript call each time
    process(task)

# GOOD: Fetch once, process in memory
tasks = get_tasks(task_ids=task_ids)  # Single AppleScript call
for task in tasks:
    process(task)
```

### 2. Use Batch Operations
```python
# BAD: Loop calling single operations
for task_id in task_ids:
    update_task(task_id, flagged=True)  # N AppleScript calls

# GOOD: Batch update
update_tasks(task_ids, flagged=True)  # 1 AppleScript call
```

### 3. Consider Timeouts
```python
# For operations on large datasets
result = run_applescript(script, timeout=180)  # 3 minutes
```

### 4. Test with Realistic Data
- Don't just test with 5 tasks
- Test with hundreds of tasks to catch performance issues
- Monitor timeout errors in production

**Timeout Guidelines:**
- Single item operations: 60s default
- Batch operations: 120s default
- Full database queries: 120-180s

---

## Common Error Patterns

### Error: "Can't get property X"

**Cause:** Variable name conflicts with OmniFocus property

**Example:**
```
AppleScript Error: Can't get property recurrence of "FREQ=WEEKLY"
```

**Solution:** Rename variable with suffix or different name (see "Variable Naming Conflicts" above)

---

### Error: "Timeout waiting for script"

**Cause:** Operation took longer than timeout threshold

**Common scenarios:**
- Querying all tasks in a large database
- Batch operations on many items
- Complex filtering that scans all projects

**Solution:**
- Increase timeout: `run_applescript(script, timeout=180)`
- Optimize query (use filters to reduce dataset)
- Break into smaller batches

---

### Error: "Recurring task not completing"

**Cause:** Using property setter instead of `mark complete` command

**Solution:** Use AppleScript `mark complete` command (see "Recurring Tasks" section)

---

## Testing Considerations

**Unit tests cannot catch:**
- Variable naming conflicts (typos like `elifintervalDays`)
- Property access patterns that fail silently
- Performance issues with large databases
- Timeout problems

**Always run integration tests** before committing:
```bash
make test-integration  # Tests with real OmniFocus
```

**Integration tests catch:**
- AppleScript syntax errors
- Variable naming conflicts
- Property access failures
- Actual performance characteristics

See `docs/INTEGRATION_TESTING.md` for setup and procedures.

---

## Additional Resources

- **OmniFocus AppleScript Dictionary:** Available in Script Editor (File → Open Dictionary → OmniFocus)
- **Integration Testing Guide:** `docs/INTEGRATION_TESTING.md`
- **Bug History:** `CHANGELOG.md` (search for "AppleScript" to see past issues)
- **Architecture Decisions:** `docs/ARCHITECTURE.md` (explains why certain patterns exist)
