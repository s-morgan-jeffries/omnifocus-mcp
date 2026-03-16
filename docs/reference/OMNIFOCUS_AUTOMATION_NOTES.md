# OmniFocus Automation Notes

Reference notes from reviewing OmniFocus automation documentation and AppleScript scripting dictionary.
Sources: omni-automation.com, AppleScript `properties of` introspection.

## Key Discovery: Batch-Readable Counting Properties

These properties work with `a reference to` batch reads (one Apple Event for all tasks):

| Property | Type | Description |
|----------|------|-------------|
| `number of tasks` | Integer | Direct subtask count — **replaces per-task `count of (tasks of t)` IPC** |
| `number of available tasks` | Integer | Available subtask count (already used) |
| `number of completed tasks` | Integer | Completed subtask count |
| `effectively completed` | Boolean | True if task or any ancestor is completed |
| `effectively dropped` | Boolean | True if task or any ancestor is dropped |
| `in inbox` | Boolean | Whether task is in inbox |

**Impact:** `number of tasks` eliminates the dominant remaining per-task IPC bottleneck in batch mode (~17ms per task × N tasks).

## Task Properties (Complete List from AppleScript)

Verified via `properties of first flattened task`:

### Scalar Properties
- `id`, `name`, `note`, `class`
- `flagged`, `completed`, `dropped`, `blocked`, `next`, `sequential`
- `in inbox`, `effectively completed`, `effectively dropped`
- `completed by children`

### Date Properties
- `creation date`, `modification date`, `completion date`, `dropped date`
- `due date`, `defer date`, `planned date`
- `effective due date`, `effective defer date`, `effective planned date`, `effective completed date`
- `next due date`, `next defer date`, `next planned date`
- `should use floating time zone`

### Counting Properties
- `number of tasks` (direct subtasks)
- `number of available tasks`
- `number of completed tasks`

### Relationship Properties
- `containing project` (Project ref)
- `parent task` (Task ref)
- `container` (Task/Project/Document ref)
- `containing document` (Document ref)
- `primary tag` (Tag ref or missing value)

### Other
- `estimated minutes` (Number or missing value)
- `repetition rule` (RepetitionRule or missing value)
- `repetition` (deprecated alias)

## Task Object (OmniAutomation/JavaScript)

From omni-automation.com/omnifocus/task.html:

### Hierarchy Properties (not in AppleScript)
- `hasChildren` (Boolean, r/o) — "more efficiently than checking if children is empty"
- `children` (Array of Task, r/o) — direct child tasks
- `flattenedTasks` (TaskArray, r/o) — all tasks recursively
- `flattenedChildren` (TaskArray, r/o) — alias

### Task.Status Enum
- Available, Blocked, Completed, Dropped, DueSoon, Next, Overdue
- Accessed via `taskStatus` property

### Methods (OmniAutomation only)
- `apply(function)` — recursive task tree iteration
- `markComplete(date)`, `markIncomplete()`, `drop(allOccurrences)`
- Tag operations: `addTag`, `addTags`, `removeTag`, `removeTags`, `clearTags`
- `Task.byIdentifier(id)` — direct lookup
- `Task.byParsingTransportText(text)` — create from text

## Project Properties

### Counting (computed per-project in current implementation)
- No native `remainingCount`, `availableCount`, `overdueCount`, `deferredCount` properties
- These must be computed from task iteration (our current approach)
- Could potentially use batch reads on `flattened tasks of proj` per project

### Status
- `status` — Active, Done, Dropped, OnHold
- `taskStatus` — inherited task status
- `nextTask` (r/o) — next completable task
- `lastReviewDate`, `nextReviewDate`

## OmniAutomation vs AppleScript

- OmniAutomation (JavaScript) runs inside OmniFocus, eliminating IPC overhead
- `evaluate javascript` can call OmniAutomation from AppleScript and return results
- AppleScript via `osascript` remains the primary interface for external MCP servers
- `a reference to` batch reads are the best AppleScript optimization available

### `evaluate javascript` (2026-03-08, Issue #206)

The `evaluate javascript` AppleScript command calls OmniAutomation from AppleScript. It works correctly on the production database with full UI context, but **crashes on headless test databases**.

**Production database (works):**
- Can access OmniFocus objects (`flattenedTasks`, task properties, etc.)
- Can read and write data, including rich text formatting via `noteText`
- Returns results as strings (use `JSON.stringify()` for structured data)

**Headless test database (crashes):**
- Simple string expressions work: `evaluate javascript "\"hello\""` returns correctly
- Accessing OmniFocus objects (e.g., `Task.byIdentifier()`) causes a silent crash
- No crash report dialog is shown; OmniFocus restarts with the production database
- Tested twice with consistent crashes
- Likely cause: test database opens without proper window/UI context that OmniAutomation requires

**Mitigation (v0.9.2, #324):** The connector detects test mode (`self._test_mode`) and skips all `evaluate javascript` calls on headless test databases. Affected operations default to safe fallbacks (e.g., `childrenAreMutuallyExclusive=False` for `get_tags()`). OmniAutomation features are tested via `make test-prod` against the production database with sandbox isolation.

**Implication:** OmniAutomation features require `make test-prod` (production database with sandbox folder). Standard integration tests (`make test-integration`) skip OmniAutomation calls automatically.

### Rich Text via OmniAutomation

OmniAutomation provides full rich text access through `task.noteText` (a `Text` object):

- **`task.note`** — plain string (same as AppleScript `note of task`)
- **`task.noteText`** — `Text` object with `attributeRuns`, `style`, `string`, `insert()`, `end`

**Readable style attributes:**
- `Style.Attribute.FontWeight` — 5 (normal), 11-12 (bold)
- `Style.Attribute.FontItalic` — boolean
- `Style.Attribute.UnderlineStyle` — None, Single
- `Style.Attribute.UnderlinePattern` — Solid
- `Style.Attribute.FontFamily`, `FontSize`, `BaselineOffset`, `Obliqueness`, `Expansion`

**RTF-safe append pattern:**
```javascript
var nt = task.noteText;
var appendText = new Text('\nNew text', nt.style);
nt.insert(nt.end, appendText);
// Existing formatting preserved, new text appended with base style
```

**RTF-destructive pattern (AppleScript):**
```applescript
set note of t to (note of t) & " appended"
-- Destroys ALL formatting — read strips RTF, write replaces it
```

## Group-Scoped Updates (2026-03-09, Issue #210)

OmniFocus AppleScript supports setting properties on collections of tasks in a single operation, bypassing the per-task ID lookup cost.

### Containment-scoped property sets

Set a property on all tasks in a project at once:

```applescript
tell front document
    set theProject to first flattened project whose name is "My Project"
    set flagged of every flattened task of theProject to true
    set estimated minutes of every flattened task of theProject to 30
end tell
```

**Works for:** `flagged`, `estimated minutes`, and other settable scalar properties.

### Containment-scoped mark complete

```applescript
mark complete every flattened task of theProject
```

Works. Uses the `mark complete` verb (not property assignment), so recurring tasks will spawn next occurrences correctly.

### Filtered containment scopes

`whose` clauses combine with containment scoping:

```applescript
-- Flag only incomplete, unflagged tasks in a project
set flagged of (every flattened task of theProject whose flagged is false and completed is false) to true
```

Multi-condition `whose` filters work. Only matching tasks are affected.

### Arbitrary ID set scoping (whose or-chain)

Target specific tasks by ID without per-task lookups:

```applescript
-- Works: or-chained whose clause
set flagged of (every flattened task whose id is "abc" or id is "def" or id is "ghi") to true
```

**Does NOT work:** `whose id is in {"abc", "def"}` — error -1700, can't convert list to specifier.

The `or`-chain pattern scales to at least 10 IDs. For Python code generation:

```python
clauses = " or ".join(f'id is "{tid}"' for tid in task_ids)
script = f'set flagged of (every flattened task whose {clauses}) to true'
```

### Performance characteristics

| Approach | N=1 | N=3 | N=5 | N=10 |
|----------|-----|-----|-----|------|
| Per-ID loop (current) | 0.24s | 0.36s | 0.48s | 0.73s |
| Whose or-chain | 0.22s | 0.23s | 0.23s | 0.25s |
| Containment scope | — | — | — | 0.21s |

Key insight: **whose or-chain time is nearly constant (~0.22-0.25s) regardless of batch size**, while per-ID loop scales linearly at ~0.05s/task. At 10 tasks, or-chain is 2.9x faster.

### Limitations

- `whose id is in {list}` syntax is not supported (error -1700)
- `set completed of collection to false` fails (error -10006) — uncomplete must be done per-task
- Containment scope applies to ALL tasks in a project; use `whose` filters for subsets
- The `or`-chain approach has unknown upper limits on clause count (tested up to 10)

## Task.RepetitionRule (OmniAutomation)

Added 2026-03-12 (Issue #272). AppleScript property writes on repetition rules don't persist in OmniFocus 4.x — OmniAutomation is the only reliable way to set or modify recurrence.

### Constructor

```javascript
new Task.RepetitionRule(ruleString, method)
```

- `ruleString` — iCalendar RRULE string (e.g., `"FREQ=WEEKLY;BYDAY=MO,WE,FR"`)
- `method` — `Task.RepetitionMethod` enum value

### Task.RepetitionMethod Enum

| Enum Value | Connector Name | AppleScript Reads As | Behavior |
|-----------|---------------|---------------------|----------|
| `Task.RepetitionMethod.Fixed` | `"fixed"` | `fixed repetition` | Next occurrence on fixed schedule regardless of completion date |
| `Task.RepetitionMethod.DueDate` | `"due_after_completion"` | `due after completion` | Next due date calculated from completion date |
| `Task.RepetitionMethod.DeferUntilDate` | `"start_after_completion"` | `start after completion` | Next defer date calculated from completion date |
| `Task.RepetitionMethod.None` | — | — | No repetition |

### Reading Existing Rules

```javascript
var t = Task.byIdentifier('task-id');
if (t.repetitionRule) {
    t.repetitionRule.ruleString;  // e.g., "FREQ=DAILY;INTERVAL=1"
    t.repetitionRule.method;      // Task.RepetitionMethod enum value
}
```

### Setting/Replacing a Rule

```javascript
var t = Task.byIdentifier('task-id');
t.repetitionRule = new Task.RepetitionRule('FREQ=WEEKLY', Task.RepetitionMethod.Fixed);
```

### Removing a Rule

Removing works via both AppleScript and OmniAutomation:

```applescript
-- AppleScript (preferred — simpler, no JS crash risk on test DB)
set repetition rule of theTask to missing value
```

```javascript
// OmniAutomation
task.repetitionRule = null;
```

### Changing Method Only (Preserving RRULE)

Read the existing rule string, then create a new rule with the same string and new method:

```javascript
var t = Task.byIdentifier('task-id');
if (t.repetitionRule) {
    var rr = t.repetitionRule.ruleString;
    t.repetitionRule = new Task.RepetitionRule(rr, Task.RepetitionMethod.DueDate);
}
```

## Future Investigation

- `taskStatus` enum could simplify availability calculations (Available, Blocked, etc.)
  but need to verify it matches our current logic
- `effective*` date properties (effectiveDueDate, effectiveDeferDate) might simplify
  inherited date calculations
- `planned date` (v4.7+) is a new property we don't currently expose

## Perspective Automation (March 2026)

Tested against OmniFocus 4.8.4 with Pro license.

### AppleScript

**Full CRUD on custom perspectives:**
- `get every perspective` — returns all perspectives (built-in + custom)
- `make new perspective with properties {name:"X"}` — creates empty custom perspective
- `set name of perspective to "Y"` — renames
- `delete perspective` — deletes

**Only 3 properties exposed:** `class`, `name`, `id`. No filter rules, sorting, grouping, or icons.

**Built-in vs custom:** Built-in perspectives (Inbox, Projects, Tags, Forecast, Flagged, Nearby, Review) return `class:item` and `missing value` for name/id. Custom perspectives return `class:custom perspective` with stable IDs.

### OmniAutomation (JavaScript)

**Read + rename only:**
- `Perspective.Custom.all` / `Perspective.BuiltIn.all` — list perspectives
- `Perspective.Custom.byName(name)` / `Perspective.Custom.byIdentifier(id)` — lookup
- `p.name = "X"` — rename works (writable property)
- No constructor (`new Perspective.Custom()` throws TypeError)
- No `remove` method
- `fileWrapper` / `writeFileRepresentationIntoDirectory` — export support

**Built-in perspectives:** `Perspective.BuiltIn.Inbox`, `.Projects`, `.Tags`, `.Forecast`, `.Flagged`, `.Nearby`, `.Review`, `.Search` — have names but no IDs.

### Limitation

Cannot programmatically configure what a perspective shows (filter rules, sorting, grouping, icons). Created perspectives are blank — users must configure them in the OmniFocus UI.

## Focus Automation (March 2026)

Tested against OmniFocus 4.8.4.

### AppleScript

**Multi-item focus:** `set focus to {project1, project2, folder1}` — any mix of projects and folders.

**Read focus:** `get every item of focus` returns focused items with class (project/folder) and name. `count of every item of focus` returns 0 when unfocused.

**Clear focus:** `set focus to {}` (empty list). `missing value` does NOT work.

**Focus + perspectives:** Focus persists across perspective switches. Setting focus on a project then switching to "Flagged" shows only flagged items within that project. This is the primary mechanism for programmatically narrowing what the user sees.

### OmniAutomation (JavaScript)

Focus is read-only: `window.focus` returns a `SectionArray` with `.length` and `.byName()`. Cannot set focus via JS.

### Key Insight

Focus + perspective switching is more useful than programmatic perspective creation. While perspectives can't have their filter rules set via API (#235), focus can narrow scope to specific projects/folders, and perspective switching applies filters within that scope. This combination achieves ad-hoc filtered views without needing custom perspective configuration.
