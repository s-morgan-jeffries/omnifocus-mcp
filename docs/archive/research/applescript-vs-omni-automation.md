# AppleScript vs Omni Automation for OmniFocus MCP Server

**Date:** 2025-10-08
**Purpose:** Compare AppleScript and Omni Automation approaches for implementing the OmniFocus MCP server

## TL;DR

**Could we have implemented everything with Omni Automation?**

**Yes**, Omni Automation can do everything AppleScript can do, plus more (especially attachments). However, it would require a **fundamentally different architecture** and has significant **execution challenges** for an MCP server.

## Capability Comparison

### What Both Can Do

| Feature | AppleScript | Omni Automation |
|---------|-------------|-----------------|
| Create/Read/Update/Delete tasks | ✅ | ✅ |
| Create/Read/Update/Delete projects | ✅ | ✅ |
| Manage folders | ✅ | ✅ |
| Manage tags | ✅ | ✅ |
| Set dates (due, defer) | ✅ | ✅ |
| Recurring tasks | ✅ | ✅ |
| Batch operations | ✅ | ✅ |
| Search/filter tasks | ✅ | ✅ |
| Project statistics | ✅ | ✅ |
| Review intervals | ✅ | ✅ |
| Perspectives | ✅ | ✅ |
| Task completion | ✅ | ✅ |
| Task hierarchy | ✅ | ✅ |

### What Omni Automation Does Better

| Feature | AppleScript | Omni Automation |
|---------|-------------|-----------------|
| **File Attachments** | ❌ Read-only properties | ✅ Full CRUD |
| - List attachment names | ❌ | ✅ |
| - Read attachment metadata | ❌ | ✅ |
| - Remove specific attachments | ❌ | ✅ |
| - Get file contents | ❌ | ✅ |
| **Modern API Design** | Legacy | ✅ Modern JS |
| **Type Safety** | Weak | ✅ Stronger |
| **Async Operations** | No | ✅ Promises |
| **Cross-Platform** | macOS only | ✅ macOS/iOS/iPadOS |
| **Object-Oriented** | Limited | ✅ Full OOP |

### What AppleScript Does Better

| Feature | AppleScript | Omni Automation |
|---------|-------------|-----------------|
| **Command-line execution** | ✅ `osascript` | ⚠️ Complex |
| **System integration** | ✅ Native | ⚠️ Limited |
| **Documentation** | ✅ Extensive | ⚠️ Less common |
| **Python integration** | ✅ `subprocess.run` | ⚠️ Requires workarounds |

## Architecture Differences

### Current AppleScript Approach

```python
# Simple, direct execution
def get_tasks(self):
    script = '''
    tell application "OmniFocus"
        tell front document
            -- Get tasks
        end tell
    end tell
    '''
    result = subprocess.run(['osascript', '-e', script], capture_output=True)
    return json.loads(result.stdout)
```

**Pros:**
- ✅ Direct command-line execution
- ✅ Synchronous, predictable
- ✅ Easy to debug
- ✅ Well-documented pattern
- ✅ Works from Python subprocess

### Omni Automation Approach

Omni Automation scripts run **inside OmniFocus**, not as external commands. Execution options:

#### Option 1: URL Schemes
```python
# Would need to:
# 1. Install plugin in OmniFocus
# 2. Trigger via URL scheme
# 3. Get results back somehow
import webbrowser
webbrowser.open('omnifocus:///run-plugin?name=MyPlugin&param=value')
# But... how do we get the result back?
```

**Problems:**
- ❌ No built-in way to get results back to Python
- ❌ Asynchronous - can't wait for completion
- ❌ Would need intermediate storage (files, clipboard, etc.)
- ❌ Complex error handling

#### Option 2: JXA (JavaScript for Automation)
```python
# Could use JXA as a bridge
script = '''
const app = Application("OmniFocus");
const doc = app.defaultDocument;
// ... JavaScript code
'''
result = subprocess.run(['osascript', '-l', 'JavaScript', '-e', script])
```

**Pros:**
- ✅ Can execute from command line
- ✅ Can return results

**Problems:**
- ⚠️ JXA is different from Omni Automation
- ⚠️ Not all Omni Automation features available
- ⚠️ Would need to rewrite everything
- ⚠️ Less documented than AppleScript

#### Option 3: Hybrid Approach
```python
# Use AppleScript to trigger Omni Automation plugins
script = '''
tell application "OmniFocus"
    -- Somehow invoke plugin and get result
end tell
'''
```

**Problems:**
- ❌ AppleScript can't directly call Omni Automation
- ❌ Would need complex bridging mechanism
- ❌ Adds significant complexity

## Specific Feature Comparison

### File Attachments

**AppleScript:**
```applescript
-- Can create
tell the note of task
    make new file attachment with properties {file name:POSIX file "/path"}
end tell

-- Can count
set count to count of file attachments of note of task

-- CANNOT read names or properties
set name to file name of (item 1 of file attachments)  -- ERROR!
```

**Omni Automation:**
```javascript
// Full access
const attachments = task.attachments;  // Array of FileWrapper
console.log(attachments[0].filename);  // Works!
console.log(attachments[0].preferredFilename);
const data = attachments[0].contents;  // Get file data

// Add attachment
const wrapper = FileWrapper.withContents("file.txt", data);
task.addAttachment(wrapper);

// Remove attachment
task.removeAttachmentAtIndex(0);
task.attachments = [];  // Remove all
```

### Recurring Tasks

**AppleScript:**
```applescript
-- Get template rule, copy, modify
set templateRule to repetition rule of (some task)
set repetition rule of newTask to templateRule
set recurrence of (repetition rule of newTask) to "FREQ=WEEKLY"
```

**Omni Automation:**
```javascript
// More direct API (similar capability)
task.repetitionRule = new RepetitionRule({
    recurrence: "FREQ=WEEKLY",
    method: RepetitionMethod.Fixed
});
```

### Batch Operations

**Both work similarly well**

**AppleScript:**
```applescript
repeat with taskId in taskIdList
    set theTask to first flattened task whose id is taskId
    set completed of theTask to true
end repeat
```

**Omni Automation:**
```javascript
taskIds.forEach(id => {
    const task = flattenedTasks.byIdentifier(id);
    task.markComplete();
});
```

## Performance Considerations

### AppleScript
- ⚠️ String-based execution (parsing overhead)
- ⚠️ Process spawning for each call
- ✅ But: Fast enough for MCP use case

### Omni Automation
- ✅ Native JavaScript execution
- ✅ Potentially faster for complex operations
- ❌ But: Execution model overhead negates benefits

## Development Complexity

### Current AppleScript Implementation
- **Lines of Code:** ~2,500 (client) + tests
- **Execution Model:** Simple subprocess calls
- **Error Handling:** Straightforward
- **Testing:** Mockable with subprocess.run
- **Maintenance:** Well-understood patterns

### Hypothetical Omni Automation Implementation
- **Lines of Code:** Similar for core logic
- **Execution Model:** Complex (plugins + URL schemes OR JXA bridge)
- **Error Handling:** Multi-layer (Python → Bridge → JavaScript)
- **Testing:** Much more complex mocking
- **Maintenance:** New patterns, less community knowledge

## What Would Need to Change

If we rewrote using Omni Automation/JXA:

### 1. Execution Layer
```python
# Before (AppleScript)
result = run_applescript(script)

# After (JXA)
result = run_jxa_script(js_code)  # New function needed

# OR (Plugin-based)
result = trigger_omnifocus_plugin(plugin_name, params)  # Much more complex
```

### 2. Script Language
- Rewrite all AppleScript → JavaScript
- Learn Omni Automation API quirks
- Test on actual OmniFocus instance (no easy mocking)

### 3. Data Exchange
- AppleScript: Easy text/JSON return values
- Omni Automation: Would need bridging mechanism

### 4. Testing
- Current: Mock subprocess.run
- New: Would need to mock plugin execution or JXA runtime

## Recommendation

### For Core Functionality (Phases 1-5, 7)
**Stick with AppleScript** ✅

**Reasons:**
1. Works perfectly for 95% of features
2. Simple, well-tested execution model
3. Easy to maintain and debug
4. Community knowledge available
5. All current functionality working well

### For Attachments (Phase 6)
**Three options:**

**Option A: Skip** (Recommended)
- Deliver 97% coverage without attachments
- Revisit if user demand emerges

**Option B: Limited AppleScript**
- Add attachmentCount (read-only)
- Add add_attachment() (write-only)
- Document limitations clearly

**Option C: Future Enhancement**
- Later, add attachment support via JXA
- Separate optional module
- Doesn't affect core functionality

## Conclusion

**Could everything be done with Omni Automation?**

**Technically yes**, but it would require:
- ❌ Fundamental architecture change
- ❌ Complex execution bridging
- ❌ Significantly more development time
- ❌ More fragile testing
- ❌ Harder maintenance

**For minimal gain:**
- ✅ Better attachment support (only feature that matters)
- ⚠️ Slightly more modern API (no practical benefit)

**Current AppleScript approach is the right choice** for this MCP server. The only feature we miss is full attachment support, which isn't critical for most workflows.

## If Attachment Support Becomes Critical

**Recommendation:** Add JXA-based attachment module as **optional enhancement**

```python
# Core functionality: AppleScript (as-is)
class OmniFocusClient:
    def get_tasks(self):
        # AppleScript implementation

# Optional attachment support: JXA module
class OmniFocusAttachments:
    def get_attachments(self, task_id):
        # JXA implementation
    def add_attachment(self, task_id, file_path):
        # JXA implementation
```

**Benefits:**
- ✅ Keeps core simple and stable
- ✅ Adds attachments for users who need it
- ✅ Isolated risk
- ✅ Can test independently
