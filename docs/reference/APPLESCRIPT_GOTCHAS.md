# AppleScript and OmniFocus Limitations

**Purpose:** Documents known limitations, workarounds, and gotchas when working with OmniFocus via AppleScript.

**Last Updated:** 2026-03-08

---

## Rich Text Notes

- ❌ **AppleScript `note` property is plain text only** — reads strip formatting, writes destroy it
- ✅ **OmniAutomation can read and write rich text** via `evaluate javascript`
- ⚠️ **OmniAutomation crashes on headless test databases** — only works with production DB (full UI context)
- **Implication:** The connector currently uses AppleScript for notes, so all note operations are plain-text-only. Rich text support would require switching note operations to OmniAutomation.

### Empirical Investigation (2026-03-08, Issue #206)

Five approaches were tested against real OmniFocus (v4, macOS). Initial testing on the headless test database produced crashes; subsequent testing on the production database (with manual confirmation before each step) revealed that OmniAutomation works correctly with full UI context.

#### 1. AppleScript `styled text` — No effect

The `note` property reports its class as `rich text`, but this is nominal only. Rich text sub-properties are not accessible:

```applescript
-- class of (note of t) returns "rich text" — but...
set attrRuns to attribute runs of (note of t)
-- ERROR: Can't get every attribute run of "..."

set firstRun to first attribute run of (note of t)
set f to font of firstRun
-- ERROR: Can't get font of "B".
```

Setting a note via `styled text` coercion is accepted but stores plain text:
```applescript
set styledNote to "Bold test" as styled text
set note of t to styledNote  -- Accepted, but no formatting applied
```

`rich text of note of t` fails: `Can't get rich text of note of inbox task`.

**Conclusion:** The AppleScript `note` property is a plain text string that claims to be `rich text` class. No rich text manipulation is possible through it.

#### 2. OmniAutomation (`evaluate javascript`) — Works on production DB

`evaluate javascript` is documented in OmniFocus's AppleScript dictionary for calling OmniAutomation from AppleScript.

**⚠️ Test database crash:** On the headless test database, `evaluate javascript` crashes OmniFocus silently when accessing OmniFocus objects (e.g., `Task.byIdentifier()`). Simple string expressions work, but any object model access causes a crash with no crash report dialog. OmniFocus restarts with the production database open. This is likely because the test database opens as a headless document without proper window/UI context.

**✅ Production database:** With the production database and full UI context, `evaluate javascript` works correctly for both reads and writes:

```applescript
tell application "OmniFocus"
    evaluate javascript "
        var tasks = flattenedTasks;
        var t = null;
        for (var i = 0; i < tasks.length; i++) {
            if (tasks[i].name === 'My Task') { t = tasks[i]; break; }
        }
        t.note = 'Note set via OmniAutomation';
        t.note;  // Returns the note
    "
end tell
```

**Conclusion:** `evaluate javascript` is viable for external automation on the production database. The crash is specific to headless/test database contexts.

#### 3. OmniAutomation Rich Text — Full read/write support

OmniAutomation exposes `task.noteText` (a `Text` object) with `attributeRuns` and `Style` API:

**Reading formatting:**
```applescript
tell application "OmniFocus"
    evaluate javascript "
        var t = flattenedTasks[0];  // find your task
        var runs = t.noteText.attributeRuns;
        var result = [];
        for (var j = 0; j < runs.length; j++) {
            var r = runs[j];
            result.push({
                text: r.string,
                fontWeight: r.style.get(Style.Attribute.FontWeight),
                fontItalic: r.style.get(Style.Attribute.FontItalic),
                underlineStyle: String(r.style.get(Style.Attribute.UnderlineStyle))
            });
        }
        JSON.stringify(result);
    "
end tell
```

**Available style attributes (tested):**

| Attribute | Values | Notes |
|-----------|--------|-------|
| `FontWeight` | 5 (normal), 11-12 (bold) | Setting to 11 produces bold |
| `FontItalic` | `true` / `false` | |
| `UnderlineStyle` | `None`, `Single` | Also `UnderlinePattern` (Solid) and `UnderlineColor` |
| `FontFamily` | e.g., `.AppleSystemUIFont` | |
| `FontSize` | e.g., 12 | |
| `BaselineOffset` | Number | |
| `Obliqueness` | Number | |
| `Expansion` | Number | |
| `BackgroundColor` | Color object | |
| `Link` | URL object | |

**Attributes that error:** `FontSlant`, `Underline`, `Strikethrough`, `ForegroundColor`, `Kern`, `Ligature`, `Shadow`, `StrokeWidth`, `Superscript`

**Writing formatting:**
```applescript
tell application "OmniFocus"
    evaluate javascript "
        var t = flattenedTasks[0];  // find your task
        t.noteText.style.set(Style.Attribute.FontWeight, 11);  // Bold
        t.noteText.style.set(Style.Attribute.FontItalic, true);  // Italic
    "
end tell
```

#### 4. AppleScript append — Destroys RTF

Confirmed empirically: a read-modify-write cycle via AppleScript's `note` property destroys all formatting.

**Before:** 10 attribute runs with bold, italic, and underline formatting.
**After `set note of t to (note of t) & " appended"`:** 1 attribute run, all plain text.

```applescript
-- This DESTROYS all rich text formatting:
set existingNote to note of t      -- Strips formatting to plain text
set note of t to existingNote & return & "Appended"  -- Writes plain text back
```

The `note of t` read returns plain text, so the write replaces all RTF with the plain text version.

#### 5. OmniAutomation append — Preserves RTF

Using `noteText.insert()` appends text without touching existing formatting:

```applescript
tell application "OmniFocus"
    evaluate javascript "
        var t = flattenedTasks[0];  // find your task
        var nt = t.noteText;
        var appendText = new Text('\\nAppended text', nt.style);
        nt.insert(nt.end, appendText);
    "
end tell
```

**Before:** 10 attribute runs with bold, italic, and underline formatting.
**After `insert()`:** 11 attribute runs — all original formatting preserved, new run appended as plain text with base style.

The `new Text(string, style)` constructor creates a Text object; `insert(position, textObj)` places it without modifying existing runs.

### Summary

| Approach | Result | Viable? |
|----------|--------|---------|
| AppleScript `styled text` | Accepted but no effect — note property is functionally plain text | No |
| AppleScript read-modify-write | Destroys RTF by design (read strips formatting) | No |
| OmniAutomation read (`noteText.attributeRuns`) | Full formatting data: bold, italic, underline, font, size | Yes (production DB only) |
| OmniAutomation write (`style.set()`) | Can set bold, italic, underline, and other attributes | Yes (production DB only) |
| OmniAutomation append (`noteText.insert()`) | Appends without destroying existing formatting | Yes (production DB only) |

### Implications for the Connector

**Current state:** The connector uses AppleScript `note of t` for all note operations. This is plain-text-only and will remain so unless note operations are migrated to OmniAutomation.

**What migration would enable:**
- Reading notes with formatting metadata (bold, italic, underline, links)
- Writing formatted notes
- Appending to notes without destroying existing formatting

**Migration risks:**
- `evaluate javascript` crashes on headless test databases — integration tests cannot cover OmniAutomation note operations
- The crash appears to be a bug in OmniFocus 4's AppleScript-to-OmniAutomation bridge when no UI context exists
- All OmniAutomation testing must be done manually against the production database

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

## Repetition Rule Property Writes Don't Persist (OF4)

- ❌ **`set recurrence of existingRule` runs without error but changes don't persist**
- ❌ **`set repetition method of existingRule` also doesn't persist**
- ✅ **`set repetition rule of theTask to missing value` works** (removing a rule)
- ✅ **OmniAutomation `new Task.RepetitionRule(ruleString, method)` works** (creating/replacing a rule)

### Empirical Investigation (2026-03-12, Issue #272)

Tested against OmniFocus 4.x on production. Both UI-created and programmatically-created repetition rules exhibit the same behavior.

**What doesn't work (AppleScript property mutations):**
```applescript
-- These run without error but the changes DON'T PERSIST:
set theRule to repetition rule of theTask
set recurrence of theRule to "FREQ=WEEKLY"       -- Silent no-op
set repetition method of theRule to fixed repetition  -- Silent no-op
```

Verified by reading back the rule in a separate AppleScript call — original values unchanged. This applies to ALL repetition rules in OmniFocus 4.x, regardless of how they were created (UI or API).

**What works (remove via AppleScript):**
```applescript
set repetition rule of theTask to missing value  -- Persists correctly
```

**What works (create/replace via OmniAutomation):**
```applescript
tell application "OmniFocus"
    evaluate javascript "
        var t = Task.byIdentifier('task-id');
        t.repetitionRule = new Task.RepetitionRule('FREQ=WEEKLY', Task.RepetitionMethod.Fixed);
    "
end tell
```

### Connector Implementation

The connector uses a two-call pattern for recurrence writes:
1. **Main AppleScript call** — handles all standard property updates (name, note, dates, tags, etc.)
2. **Separate OmniAutomation call** — handles recurrence set/modify via `evaluate javascript`

Remove operations use a single AppleScript call with `set repetition rule to missing value`.

⚠️ **Testing constraint:** `evaluate javascript` crashes on headless test databases. Integration tests for recurrence write run against production with `OMNIFOCUS_PROD_TEST=true`.

---

## Mutually Exclusive Tag Groups

- ✅ **Exclusivity is enforced at the data model level** — adding tag B from an exclusive group silently removes tag A, even via AppleScript
- ❌ **AppleScript/SDEF cannot read or write the exclusivity configuration** — `mutually exclusive` is not an SDEF property
- ✅ **OmniAutomation can read and write it** via `Tag.childrenAreMutuallyExclusive`

### Empirical Investigation (2026-03-14, Issue #302)

Tested with a parent tag "Mutual Exclusion Test" configured as exclusive in the UI, with child tags "Option 1", "Option 2", "Option 3".

**Enforcement test (AppleScript):**
```applescript
-- Add Option 1 to a task
set tagObj1 to first flattened tag whose name is "Option 1"
add tagObj1 to tags of tempTask
-- tags of tempTask → {"Option 1"}

-- Add Option 2 (same exclusive group)
set tagObj2 to first flattened tag whose name is "Option 2"
add tagObj2 to tags of tempTask
-- tags of tempTask → {"Option 2"} — Option 1 was silently removed!
```

Adding all three sequentially results in only the last one surviving: `{Option 3}`.

**OmniAutomation access:**
```applescript
tell application "OmniFocus"
    evaluate javascript "
        var tag = flattenedTags.byName('Mutual Exclusion Test');
        tag.childrenAreMutuallyExclusive;  // → true (readable)
        tag.childrenAreMutuallyExclusive = false;  // writable
    "
end tell
```

⚠️ **Testing constraint:** Like all OmniAutomation features, `evaluate javascript` crashes on headless test databases. Testing must be done against the production DB.

### Implications for the Connector

- `update_task(add_tags=["Option 2"])` on a task with "Option 1" will silently remove "Option 1" — this is OmniFocus behavior, not a connector bug
- The connector currently cannot detect or warn about this because it doesn't read `childrenAreMutuallyExclusive`
- Future enhancement: expose `childrenAreMutuallyExclusive` in `get_tags` so agents can understand tag group behavior

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

See `../guides/INTEGRATION_TESTING.md` for setup and procedures.

---

## Additional Resources

- **OmniFocus AppleScript Dictionary:** Available in Script Editor (File → Open Dictionary → OmniFocus)
- **Integration Testing Guide:** `../guides/INTEGRATION_TESTING.md`
- **Bug History:** `CHANGELOG.md` (search for "AppleScript" to see past issues)
- **Architecture Decisions:** `../reference/ARCHITECTURE.md` (explains why certain patterns exist)
