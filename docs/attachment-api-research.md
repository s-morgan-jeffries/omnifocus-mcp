# OmniFocus Attachment API Research

**Date:** 2025-10-08
**Purpose:** Investigate OmniFocus attachment support for MCP server implementation

## Summary

**Conclusion:** OmniFocus 4 attachment support via AppleScript is **severely limited**. Full attachment functionality requires **Omni Automation** (JavaScript-based API).

## Key Findings

### 1. AppleScript API Limitations

**Can do:**
- ✅ Create file attachments: `tell the note of task` → `make new file attachment`
- ✅ Count attachments: `count of file attachments of note of task`
- ✅ Check if attachments exist

**Cannot do:**
- ❌ Read attachment file names
- ❌ Read attachment properties
- ❌ Get file size or metadata
- ❌ Delete specific attachments by name
- ❌ Distinguish between embedded vs linked attachments

**Error when accessing properties:**
```applescript
-- Returns special character "￼" (object replacement character)
-- Cannot access: file name, embedded, size, etc.
-- Error: "Can't get file name of '￼'"
```

### 2. Omni Automation API (JavaScript)

OmniFocus 4 provides full attachment support via Omni Automation:

**Available methods:**
- `task.attachments` - Array of FileWrapper objects
- `task.addAttachment(attachment:FileWrapper)` - Add attachment
- `task.removeAttachmentAtIndex(index:Number)` - Remove by index
- `task.attachments = []` - Remove all attachments

**FileWrapper properties:**
- `filename` - File name
- `preferredFilename` - Display name
- `contents` - File data (Data object)

### 3. Testing Results

**Creating attachments (AppleScript):**
```applescript
tell application "OmniFocus"
  tell front document
    set testTask to make new inbox task with properties {name:"Test"}
    tell the note of testTask
      make new file attachment with properties {file name:POSIX file "/path/to/file.txt", embedded:false}
    end tell
  end tell
end tell
```

**Result:** ✅ Attachment created successfully
**But:** ❌ Cannot read back attachment details

## Recommendations

### Option A: Limited AppleScript Implementation (Recommended for now)

Implement basic attachment support with these limitations:

**Implement:**
1. ✅ Add attachmentCount to task/project responses (read-only)
2. ✅ add_attachment() - create attachments (file path only)
3. ⚠️ get_attachments() - return count only (no file names)
4. ❌ remove_attachment() - NOT POSSIBLE via AppleScript

**User impact:**
- Can add attachments ✅
- Can see attachment count ✅
- Cannot list attachment names ❌
- Cannot remove attachments ❌

### Option B: Omni Automation Integration (Future enhancement)

Implement full attachment support using Omni Automation JavaScript API.

**Requirements:**
- Execute JavaScript via Omni Automation
- Handle FileWrapper objects
- Potentially use JXA (JavaScript for Automation) to bridge

**Benefits:**
- Full attachment functionality
- Read file names, sizes, metadata
- Remove specific attachments
- List all attachments with details

**Challenges:**
- Different execution model (JavaScript vs AppleScript)
- May require running separate automation scripts
- More complex integration with Python MCP server

### Option C: Skip Phase 6 Attachments

Given the API limitations, consider skipping Phase 6 and moving to Phase 7 (Project Intelligence), which can be fully implemented with AppleScript.

**Rationale:**
- Partial implementation has limited value
- Full implementation requires significant rearchitecture
- Other phases provide more immediate value

## Implementation Plan (If Proceeding with Option A)

### 1. Add attachmentCount Field (Read-only)

Add to `get_tasks()` and `get_projects()` responses:

```python
# In AppleScript
set attCount to count of file attachments of note of theTask

# In JSON response
"attachmentCount": attCount
```

### 2. Implement add_attachment()

```python
def add_attachment(
    self,
    item_id: str,
    file_path: str,
    item_type: str = "task",
    embedded: bool = False
) -> bool:
    """Add a file attachment to a task or project.

    Args:
        item_id: ID of the task or project
        file_path: Absolute path to the file to attach
        item_type: "task" or "project"
        embedded: If True, embed file in database; if False, link to file

    Returns:
        bool: True if attachment added successfully

    Note: Cannot read back attachment details due to AppleScript API limitations.
    """
```

### 3. Document Limitations

Clearly document in:
- Method docstrings
- README.md
- API documentation

That attachment support is **write-only** via AppleScript.

## Code Examples

### Reading Attachment Count

```applescript
tell application "OmniFocus"
  tell front document
    set theTask to first flattened task whose id is "task-id"
    set attCount to count of file attachments of note of theTask
    return attCount
  end tell
end tell
```

### Adding Attachment

```applescript
tell application "OmniFocus"
  tell front document
    set theTask to first flattened task whose id is "task-id"
    tell the note of theTask
      make new file attachment with properties {file name:POSIX file "/path/to/file.txt", embedded:false}
    end tell
  end tell
end tell
```

### Checking If Attachments Exist

```applescript
tell application "OmniFocus"
  tell front document
    set theTask to first flattened task whose id is "task-id"
    set attCount to count of file attachments of note of theTask
    if attCount > 0 then
      -- Has attachments
    else
      -- No attachments
    end if
  end tell
end tell
```

## References

- OmniFocus Omni Automation: https://omni-automation.com/omnifocus/task-attachment.html
- AppleScript Changes: https://support.omnigroup.com/omnifocus-applescript-changes/
- Forum Discussion: https://discourse.omnigroup.com/t/access-to-embedded-attachment/21225

## Decision Required

**Recommendation:** Skip Phase 6 (Attachments) due to AppleScript API limitations and proceed to Phase 7 (Project Intelligence), which can be fully implemented.

**Alternative:** Implement Option A (limited support) with clear documentation of limitations if attachment creation alone provides value.
