# OmniFocus Recurring Tasks Research

**Date:** 2025-10-08
**Purpose:** Understand how to work with recurring tasks in OmniFocus AppleScript API

## Key Findings

### Repetition Rule Structure

Every recurring task has a `repetition rule` property with two sub-properties:

1. **`recurrence`** (string): iCalendar (RFC 5545) RRULE format
   - Examples:
     - `"FREQ=DAILY"` - every day
     - `"FREQ=WEEKLY"` - every week
     - `"FREQ=WEEKLY;INTERVAL=8"` - every 8 weeks
     - `"FREQ=MONTHLY;BYMONTHDAY=7"` - 7th of every month
     - `"FREQ=YEARLY"` - every year
     - `"FREQ=DAILY;INTERVAL=70"` - every 70 days

2. **`repetition method`** (enum): How the task repeats
   - `fixed repetition` - repeats on a fixed schedule (e.g., every Monday)
   - `start after completion` - next instance starts X time after completing
   - `due after completion` - next instance due X time after completing

### Reading Recurring Tasks

```applescript
tell application "OmniFocus"
    tell front document
        set t to first flattened task whose name is "My Task"
        set repRule to repetition rule of t

        if repRule is not missing value then
            set rrule to recurrence of repRule
            set method to repetition method of repRule
            -- rrule = "FREQ=WEEKLY"
            -- method = fixed repetition
        end if
    end tell
end tell
```

### Creating Recurring Tasks

**Important:** You CANNOT create a repetition rule from scratch. You must:
1. Copy an existing repetition rule from ANY task
2. Modify its properties
3. Assign it to the new task

```applescript
tell application "OmniFocus"
    tell front document
        -- Step 1: Get ANY existing repetition rule as a template
        set templateRule to missing value
        repeat with t in flattened tasks
            try
                set templateRule to repetition rule of t
                if templateRule is not missing value then
                    exit repeat
                end if
            end try
        end repeat

        -- Step 2: Create the new task
        set newTask to make new inbox task with properties {name:"New recurring task"}

        -- Step 3: Assign the template rule
        set repetition rule of newTask to templateRule

        -- Step 4: Modify the rule properties
        set theRule to repetition rule of newTask
        set recurrence of theRule to "FREQ=DAILY"
        set repetition method of theRule to fixed repetition
    end tell
end tell
```

### Updating Recurring Tasks

```applescript
tell application "OmniFocus"
    tell front document
        set t to first flattened task whose name is "My Task"
        set repRule to repetition rule of t

        if repRule is not missing value then
            -- Modify the recurrence pattern
            set recurrence of repRule to "FREQ=WEEKLY;INTERVAL=2"

            -- Modify the repetition method
            set repetition method of repRule to start after completion
        end if
    end tell
end tell
```

### Removing Recurrence

```applescript
tell application "OmniFocus"
    tell front document
        set t to first flattened task whose name is "My Task"
        set repetition rule of t to missing value
    end tell
end tell
```

## Implementation Plan

### 1. Reading (add fields to task responses)

Add these fields to task dictionaries:
- `isRecurring` (bool): whether task has a repetition rule
- `recurrence` (str | None): the RRULE string if recurring
- `repetitionMethod` (str | None): "fixed", "start_after_completion", or "due_after_completion"

### 2. Creating (extend `add_task`)

Add optional parameters:
- `recurrence: Optional[str]` - iCalendar RRULE string
- `repetition_method: Optional[str]` - "fixed" (default), "start_after_completion", "due_after_completion"

Logic:
- If `recurrence` provided, copy a template rule, modify it, assign it

### 3. Updating (extend `update_task`)

Add optional parameters (same as creating):
- `recurrence: Optional[str]`
- `repetition_method: Optional[str]`

Logic:
- If task already has rule: modify it
- If task has no rule but recurrence provided: copy template and modify
- If recurrence is empty string: remove rule

### 4. Filtering (extend `get_tasks`)

Add parameter:
- `recurring_only: Optional[bool]`

Logic:
- Python-based filtering after getting all tasks

## iCalendar RRULE Reference

Common patterns:
- Daily: `FREQ=DAILY`
- Every N days: `FREQ=DAILY;INTERVAL=N`
- Weekly: `FREQ=WEEKLY`
- Every N weeks: `FREQ=WEEKLY;INTERVAL=N`
- Weekly on specific days: `FREQ=WEEKLY;BYDAY=MO,WE,FR`
- Monthly: `FREQ=MONTHLY`
- Monthly on specific day: `FREQ=MONTHLY;BYMONTHDAY=15`
- Monthly on Nth weekday: `FREQ=MONTHLY;BYDAY=2MO` (2nd Monday)
- Yearly: `FREQ=YEARLY`

Full RFC 5545 spec: https://tools.ietf.org/html/rfc5545#section-3.3.10
