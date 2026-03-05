---
name: applescript-omnifocus
description: Use when writing, modifying, or debugging ANY AppleScript that interacts with OmniFocus. Also use when encountering AppleScript errors, unexpected OmniFocus behavior, or when adding new connector methods. Covers variable naming traps, rich text limitations, recurring task handling, date formats, string escaping, and batch operation patterns.
---

# AppleScript + OmniFocus Patterns

This skill covers the hard-won knowledge about scripting OmniFocus via AppleScript. These are not obvious from documentation and have caused real bugs in this project.

## Critical: Variable Naming Conflicts

OmniFocus AppleScript has a dangerous quirk: if you use a variable name that matches an OmniFocus property, AppleScript silently reads the property instead of your variable.

**Bug-causing names (NEVER use as variables):**
`name`, `note`, `status`, `flagged`, `completed`, `sequential`, `due date`, `defer date`, `estimated minutes`, `repetition rule`, `repetition method`

**Safe naming pattern:** Always prefix with the entity type:
```applescript
-- BAD: "name" collides with OmniFocus property
set name to "My Task"
set name of theTask to name  -- reads property of theTask, not your variable!

-- GOOD: prefixed variable name
set taskName to "My Task"
set name of theTask to taskName  -- works correctly
```

**Real bug from this project:** A variable called `status` inside a `tell task` block caused OmniFocus to read the task's status property instead of the variable value, producing silent data corruption. The `elifintervalDays` typo story: unit tests passed because they mocked AppleScript, but integration tests against real OmniFocus caught the variable collision. This is why integration tests exist.

## Rich Text Notes Limitation

OmniFocus stores notes as rich text internally. The AppleScript API exposes this inconsistently:

- **Reading:** `note of task` returns plain text (stripped of formatting)
- **Writing:** `set note of task to "text"` replaces the entire note with plain text, destroying any rich text formatting

**There is no workaround.** You cannot preserve rich text through the AppleScript API. Document this to users and warn when overwriting notes.

## Recurring Task Completion

Two ways to complete a task — only one handles recurrence correctly:

```applescript
-- CORRECT: Creates next occurrence for recurring tasks
mark complete theTask

-- WRONG: Just marks this instance done, no next occurrence spawned
set completed of theTask to true
```

Use `mark complete` (the AppleScript command) for any task that might recur. Use `set completed to true` only when you specifically want to kill a recurring task's future occurrences.

The connector uses `mark complete` by default in `update_task()` when `completed=True` is passed.

## JSON Construction in AppleScript

AppleScript has no native JSON support and no module system. Every AppleScript block that needs to return structured data must include inline JSON helper functions.

**Current pattern (used 9x in the connector):**
```applescript
on escapeJSON(theText)
    set resultText to ""
    repeat with i from 1 to count of theText
        set c to character i of theText
        if c is "\"" then
            set resultText to resultText & "\\\""
        else if c is "\\" then
            set resultText to resultText & "\\\\\\\\"
        else
            set resultText to resultText & c
        end if
    end repeat
    return resultText
end escapeJSON
```

This duplication is intentional and necessary. Do not try to "DRY" it — AppleScript blocks must be self-contained because `osascript -e` executes each block independently.

## Date Format Conversion

AppleScript uses locale-dependent date strings. The connector normalizes to ISO 8601:

- **AppleScript format:** `"March 5, 2026 5:00:00 PM"`
- **ISO 8601 format:** `"2026-03-05T17:00:00"`
- **Conversion:** `_iso_to_applescript_date()` in the connector handles both directions

When writing new date-handling code, always use the existing converter rather than building date strings manually.

## String Escaping

Always escape user-provided strings before embedding in AppleScript:

```python
name_escaped = self._escape_applescript_string(name)
script = f'set name of theTask to "{name_escaped}"'
```

The `_escape_applescript_string()` method handles quotes and backslashes. Without this, a task name containing `"` will break the AppleScript block silently.

## Batch Operation Patterns

**Single AppleScript call for multiple items** is always faster than multiple calls:

```applescript
-- GOOD: One call, N items (100-300ms total)
tell application "OmniFocus"
    tell front document
        repeat with t in flattened tasks
            -- process all tasks in one block
        end repeat
    end tell
end tell

-- BAD: N calls, one item each (100-300ms PER call)
for task_id in task_ids:
    script = f'tell application "OmniFocus" ... get task {task_id} ...'
    run_applescript(script)  # 100-300ms each!
```

**When batch is not possible:** Some operations (like `mark complete`) must be done per-task because they trigger OmniFocus-internal workflows. In these cases, accept the overhead.

## Error Handling Pattern

AppleScript errors should be caught in the script and returned as prefixed strings:

```applescript
try
    -- operation
    return "SUCCESS"
on error errMsg
    return "ERROR: " & errMsg
end try
```

The Python side then checks for the prefix:
```python
result = run_applescript(script)
if result.startswith("ERROR:"):
    raise Exception(result)
```

This is more reliable than catching `subprocess.CalledProcessError`, which doesn't always contain useful error messages from OmniFocus.

## Database Safety System

The connector has a safety system that prevents destructive operations on production data:

- Requires `OMNIFOCUS_TEST_MODE=true` and `OMNIFOCUS_TEST_DATABASE=OmniFocus-TEST.ofocus`
- Each destructive operation calls `_verify_database_safety()` which runs an AppleScript to check the current database name
- Operations tracked in `DESTRUCTIVE_OPERATIONS` set: create, update, delete, reorder

This adds ~100ms per destructive call but prevents catastrophic data loss. Do not bypass it.

## OmniFocus-Specific AppleScript Quirks

- **`first flattened task whose id is X`** — works for tasks. Use `flattened projects` for projects, `folders` for folders.
- **`front document` vs `default document`** — `front document` is for UI operations, `default document` for data operations. Some operations require one or the other.
- **Focus** — only projects and folders can be focused. Attempting to focus a task or tag raises an error.
- **Perspectives** — perspective names are accessed via `perspective names` (plural), switching via `set perspective name of window to X`.
- **Move operations** — `move task to before/after referenceTask` requires both tasks to be in the same project and at the same hierarchy level.
