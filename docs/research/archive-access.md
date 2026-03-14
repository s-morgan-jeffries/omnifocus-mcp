# OmniFocus Archive Access via AppleScript

**Date:** 2026-03-14
**Issue:** #247
**Status:** Research complete

---

## Summary

OmniFocus archive databases can be opened and queried via AppleScript as a second document. Full read access to task and project properties works. Modification of existing tasks works. Creation of new tasks, cross-document moves, and programmatic archiving do not work. OmniAutomation cannot access the archive document.

## Archive Location

The archive file is stored at the user-configured location:

```
~/Library/Mobile Documents/com~apple~CloudDocs/OmniFocus/Archive/Archive.ofocus-archive
```

This path may vary per user depending on their OmniFocus archive configuration (File > Archive > Set Archive Location).

## Capability Matrix

| Capability | Status | Notes |
|-----------|--------|-------|
| Open archive via `open` command | ✅ | Appears as document named "Archive" |
| Read task properties | ✅ | name, id, note, dates, status, flagged, containing project, tags |
| Read project list | ✅ | Full `flattened projects` access |
| `whose` clause filtering | ✅ | Works at project scope; times out on full archive (22K+ tasks) |
| Modify existing tasks | ✅ | Can update note and other properties |
| Project search by name | ✅ | `first flattened project whose name is "X"` works |
| Create new tasks | ❌ | "AppleEvent handler failed" |
| Move tasks to main DB | ❌ | "Cannot move objects from one document to another" |
| Programmatic archiving | ❌ | No SDEF command — "Archive Old Items" is menu-only |
| OmniAutomation access | ❌ | `document` global only sees main DB; no multi-document API |

## Code Examples

### Opening the Archive

```applescript
tell application "OmniFocus"
    open "/path/to/Archive.ofocus-archive"
    -- Archive appears as: first document whose name is "Archive"
end tell
```

### Reading Archive Tasks

```applescript
tell application "OmniFocus"
    set archDoc to first document whose name is "Archive"

    -- Count all tasks
    set taskCount to count of flattened tasks of archDoc

    -- Read properties from a task
    set proj to first flattened project of archDoc
    set t to first flattened task of proj
    set taskName to name of t
    set taskNote to note of t
    set taskCompleted to completed of t
    set taskProject to name of containing project of t
end tell
```

### Searching Archive Projects

```applescript
tell application "OmniFocus"
    set archDoc to first document whose name is "Archive"

    -- Find a project by name
    set proj to first flattened project of archDoc whose name is "My Project"
    set taskCount to count of flattened tasks of proj

    -- whose clause works at project scope
    set completedTasks to flattened tasks of proj whose completed is true
end tell
```

### Modifying Archive Tasks

```applescript
tell application "OmniFocus"
    set archDoc to first document whose name is "Archive"
    set proj to first flattened project of archDoc
    set t to first flattened task of proj

    -- Modification works
    set note of t to "Updated note"
end tell
```

### What Fails

```applescript
tell application "OmniFocus"
    set archDoc to first document whose name is "Archive"

    -- Creating tasks fails
    make new inbox task in archDoc with properties {name:"Test"}
    -- ERROR: AppleEvent handler failed

    -- Moving between documents fails
    set mainDoc to first document whose name is "OmniFocus"
    set t to first flattened task of first flattened project of archDoc
    move t to end of inbox tasks of mainDoc
    -- ERROR: Cannot move objects from one document to another
end tell
```

## Performance Considerations

- **Full-archive `whose` clauses time out** on large archives (22K+ tasks) due to the 60-second AppleEvent timeout. Filter at project scope instead.
- **Opening the archive** adds a second document to OmniFocus. The connector's `default document` continues to point to the main database.
- **`front document`** may change depending on which window is focused — use `first document whose name is "Archive"` for reliable access.

## OmniAutomation Limitation

OmniAutomation's `evaluate javascript` environment only exposes the main database via global variables (`flattenedTasks`, `flattenedProjects`, `document`, etc.). There is no multi-document API — `documents` is undefined. This means:

- Tag properties like `childrenAreMutuallyExclusive` cannot be read from archive tags
- Any OmniAutomation-only features (rich text, recurrence rules) are not available on archive data

## Implications for the Connector

**What's feasible now:**
- A `get_archived_tasks` or `search_archive` function that opens the archive and queries by project name
- Reading full task/project properties from archive data
- Scoped queries (by project) to avoid timeout issues

**What's not feasible:**
- Moving tasks from archive back to the main database (UI-only via drag-and-drop)
- Triggering "Archive Old Items" programmatically
- Using OmniAutomation features on archive data

**Design considerations:**
- The archive path is user-configurable — the connector would need a config setting or auto-discovery
- Opening/closing the archive document has side effects (changes OmniFocus window state)
- The archive should be opened read-only to avoid accidental modifications
- Large archives need project-scoped queries to stay within timeout limits
