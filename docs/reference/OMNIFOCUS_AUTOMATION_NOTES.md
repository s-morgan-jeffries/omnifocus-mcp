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
- **BUT** cannot return results to external callers (documented limitation)
- AppleScript via `osascript` is the only option for external MCP servers
- `a reference to` batch reads are the best AppleScript optimization available

## Future Investigation

- `taskStatus` enum could simplify availability calculations (Available, Blocked, etc.)
  but need to verify it matches our current logic
- `effective*` date properties (effectiveDueDate, effectiveDeferDate) might simplify
  inherited date calculations
- `planned date` (v4.7+) is a new property we don't currently expose
