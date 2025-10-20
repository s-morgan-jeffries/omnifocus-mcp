# JXA Attachment Module Design

**Date:** 2025-10-08
**Purpose:** Design for optional JXA-based attachment support alongside existing AppleScript implementation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              MCP Server (server_fastmcp.py)              │
└─────────────────────────────────────────────────────────┘
                          │
                          ├─────────────────────────────────┐
                          ▼                                 ▼
        ┌─────────────────────────────┐   ┌─────────────────────────────┐
        │   OmniFocusConnector           │   │  OmniFocusAttachments       │
        │   (AppleScript-based)       │   │  (JXA-based)                │
        │   - Core functionality      │   │  - Attachment operations    │
        │   - Tasks, Projects, etc.   │   │  - Optional module          │
        └─────────────────────────────┘   └─────────────────────────────┘
                    │                                  │
                    ▼                                  ▼
            run_applescript()                  run_jxa_script()
```

## Implementation

### 1. New JXA Helper Function

```python
# src/omnifocus_mcp/jxa_helpers.py

import subprocess
from typing import Any, Optional


def run_jxa_script(script: str) -> str:
    """Execute a JXA (JavaScript for Automation) script.

    Args:
        script: JavaScript code to execute

    Returns:
        str: Script output

    Raises:
        subprocess.CalledProcessError: If script execution fails
    """
    result = subprocess.run(
        ['osascript', '-l', 'JavaScript', '-e', script],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()
```

### 2. Attachment Module Class

```python
# src/omnifocus_mcp/attachments.py

import json
import os
from typing import Any, Optional
from .jxa_helpers import run_jxa_script


class OmniFocusAttachments:
    """Handle OmniFocus file attachments using JXA.

    This is an optional module that provides full attachment support
    using JavaScript for Automation (JXA) instead of AppleScript.

    Note: Requires OmniFocus Pro.
    """

    def __init__(self, enable_safety_checks: bool = True):
        """Initialize the attachments module.

        Args:
            enable_safety_checks: Whether to verify database before operations
        """
        self.enable_safety_checks = enable_safety_checks

    def get_attachments(
        self,
        item_id: str,
        item_type: str = "task"
    ) -> list[dict[str, Any]]:
        """Get all attachments for a task or project.

        Args:
            item_id: ID of the task or project
            item_type: "task" or "project"

        Returns:
            List of attachment dictionaries with:
            - name: str - file name
            - preferredName: str - display name
            - size: int - file size in bytes
            - index: int - position in attachment list

        Example:
            >>> attachments = client.get_attachments("task-123")
            >>> for att in attachments:
            ...     print(f"{att['name']} ({att['size']} bytes)")
        """
        if item_type not in ["task", "project"]:
            raise ValueError("item_type must be 'task' or 'project'")

        script = f'''
        const app = Application("OmniFocus");
        const doc = app.defaultDocument;

        // Find the item
        const items = doc.flattenedTasks;
        const item = items.whose({{id: "{item_id}"}})[0];

        if (!item) {{
            throw new Error("Item not found: {item_id}");
        }}

        // Get attachments
        const attachments = item.attachments();
        const result = [];

        for (let i = 0; i < attachments.length; i++) {{
            const att = attachments[i];
            result.push({{
                name: att.filename(),
                preferredName: att.preferredFilename(),
                size: att.contents().length,
                index: i
            }});
        }}

        JSON.stringify(result);
        '''

        try:
            output = run_jxa_script(script)
            return json.loads(output) if output else []
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error getting attachments: {e.stderr}")

    def add_attachment(
        self,
        item_id: str,
        file_path: str,
        item_type: str = "task"
    ) -> bool:
        """Add a file attachment to a task or project.

        Args:
            item_id: ID of the task or project
            file_path: Absolute path to the file to attach
            item_type: "task" or "project"

        Returns:
            bool: True if attachment added successfully

        Raises:
            ValueError: If file doesn't exist
            Exception: If attachment fails

        Example:
            >>> client.add_attachment("task-123", "/path/to/document.pdf")
            True
        """
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")

        if item_type not in ["task", "project"]:
            raise ValueError("item_type must be 'task' or 'project'")

        # Read file contents
        with open(file_path, 'rb') as f:
            file_data = f.read()

        # Convert to base64 for passing to JXA
        import base64
        encoded_data = base64.b64encode(file_data).decode('ascii')
        file_name = os.path.basename(file_path)

        script = f'''
        const app = Application("OmniFocus");
        const doc = app.defaultDocument;

        // Find the item
        const items = doc.flattenedTasks;
        const item = items.whose({{id: "{item_id}"}})[0];

        if (!item) {{
            throw new Error("Item not found: {item_id}");
        }}

        // Decode base64 data
        const encodedData = "{encoded_data}";
        const data = $.NSData.alloc.initWithBase64EncodedStringOptions(encodedData, 0);

        // Create FileWrapper
        const wrapper = $.NSFileWrapper.alloc.initRegularFileWithContents(data);
        wrapper.preferredFilename = "{file_name}";

        // Add attachment
        item.addAttachment(wrapper);

        "true";
        '''

        try:
            result = run_jxa_script(script)
            return result == "true"
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error adding attachment: {e.stderr}")

    def remove_attachment(
        self,
        item_id: str,
        attachment_index: int,
        item_type: str = "task"
    ) -> bool:
        """Remove an attachment from a task or project.

        Args:
            item_id: ID of the task or project
            attachment_index: Index of the attachment to remove (0-based)
            item_type: "task" or "project"

        Returns:
            bool: True if attachment removed successfully

        Example:
            >>> # Remove the first attachment
            >>> client.remove_attachment("task-123", 0)
            True
        """
        if item_type not in ["task", "project"]:
            raise ValueError("item_type must be 'task' or 'project'")

        script = f'''
        const app = Application("OmniFocus");
        const doc = app.defaultDocument;

        // Find the item
        const items = doc.flattenedTasks;
        const item = items.whose({{id: "{item_id}"}})[0];

        if (!item) {{
            throw new Error("Item not found: {item_id}");
        }}

        // Remove attachment
        item.removeAttachmentAtIndex({attachment_index});

        "true";
        '''

        try:
            result = run_jxa_script(script)
            return result == "true"
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error removing attachment: {e.stderr}")

    def remove_attachment_by_name(
        self,
        item_id: str,
        attachment_name: str,
        item_type: str = "task"
    ) -> bool:
        """Remove an attachment by name from a task or project.

        Args:
            item_id: ID of the task or project
            attachment_name: Name of the attachment to remove
            item_type: "task" or "project"

        Returns:
            bool: True if attachment removed successfully

        Raises:
            ValueError: If attachment not found

        Example:
            >>> client.remove_attachment_by_name("task-123", "document.pdf")
            True
        """
        # First, get all attachments to find the index
        attachments = self.get_attachments(item_id, item_type)

        for att in attachments:
            if att['name'] == attachment_name or att['preferredName'] == attachment_name:
                return self.remove_attachment(item_id, att['index'], item_type)

        raise ValueError(f"Attachment not found: {attachment_name}")

    def get_attachment_content(
        self,
        item_id: str,
        attachment_index: int,
        item_type: str = "task"
    ) -> bytes:
        """Get the contents of an attachment.

        Args:
            item_id: ID of the task or project
            attachment_index: Index of the attachment (0-based)
            item_type: "task" or "project"

        Returns:
            bytes: File contents

        Example:
            >>> content = client.get_attachment_content("task-123", 0)
            >>> with open("/tmp/downloaded.pdf", "wb") as f:
            ...     f.write(content)
        """
        if item_type not in ["task", "project"]:
            raise ValueError("item_type must be 'task' or 'project'")

        script = f'''
        const app = Application("OmniFocus");
        const doc = app.defaultDocument;

        // Find the item
        const items = doc.flattenedTasks;
        const item = items.whose({{id: "{item_id}"}})[0];

        if (!item) {{
            throw new Error("Item not found: {item_id}");
        }}

        // Get attachment
        const attachments = item.attachments();
        if ({attachment_index} >= attachments.length) {{
            throw new Error("Attachment index out of range");
        }}

        const att = attachments[{attachment_index}];
        const data = att.contents();

        // Convert to base64 for transport
        data.base64EncodedStringWithOptions(0).js;
        '''

        try:
            import base64
            encoded = run_jxa_script(script)
            return base64.b64decode(encoded)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error reading attachment: {e.stderr}")
```

### 3. Integration with MCP Server

```python
# src/omnifocus_mcp/server_fastmcp.py

from mcp.server.fastmcp import FastMCP
from .omnifocus_connector import OmniFocusConnector

# Optional: Only import if user wants attachment support
try:
    from .attachments import OmniFocusAttachments
    ATTACHMENTS_AVAILABLE = True
except ImportError:
    ATTACHMENTS_AVAILABLE = False

mcp = FastMCP("OmniFocus MCP Server")

# Singleton instances
_client: OmniFocusConnector | None = None
_attachments: OmniFocusAttachments | None = None


def get_client() -> OmniFocusConnector:
    """Get or create the OmniFocus client singleton."""
    global _client
    if _client is None:
        _client = OmniFocusConnector(enable_safety_checks=True)
    return _client


def get_attachments() -> OmniFocusAttachments:
    """Get or create the OmniFocus attachments client singleton."""
    if not ATTACHMENTS_AVAILABLE:
        raise Exception("Attachment support not available. Install JXA dependencies.")

    global _attachments
    if _attachments is None:
        _attachments = OmniFocusAttachments(enable_safety_checks=True)
    return _attachments


# Existing tools (using AppleScript client)
@mcp.tool()
def get_tasks(project_id: str | None = None) -> str:
    """Get tasks from OmniFocus."""
    client = get_client()
    tasks = client.get_tasks(project_id=project_id)
    return json.dumps(tasks, indent=2)


# New attachment tools (using JXA attachments module)
@mcp.tool()
def get_attachments(task_id: str) -> str:
    """Get all attachments for a task.

    Returns JSON array of attachments with name, size, and index.
    Requires OmniFocus Pro and JXA support.
    """
    attachments = get_attachments()  # Gets the attachments client
    result = attachments.get_attachments(task_id)
    return json.dumps(result, indent=2)


@mcp.tool()
def add_attachment(task_id: str, file_path: str) -> str:
    """Add a file attachment to a task.

    Args:
        task_id: ID of the task
        file_path: Absolute path to the file to attach

    Returns:
        Success message
    """
    attachments = get_attachments()
    success = attachments.add_attachment(task_id, file_path)
    return "Attachment added successfully" if success else "Failed to add attachment"


@mcp.tool()
def remove_attachment(task_id: str, attachment_name: str) -> str:
    """Remove an attachment from a task.

    Args:
        task_id: ID of the task
        attachment_name: Name of the attachment to remove

    Returns:
        Success message
    """
    attachments = get_attachments()
    success = attachments.remove_attachment_by_name(task_id, attachment_name)
    return "Attachment removed successfully" if success else "Failed to remove attachment"
```

## Usage Examples

### From Python Code

```python
# Using the core client (AppleScript)
client = OmniFocusConnector()
tasks = client.get_tasks()  # Works as before

# Using the attachments module (JXA)
attachments = OmniFocusAttachments()

# List attachments
atts = attachments.get_attachments("task-123")
print(f"Task has {len(atts)} attachments:")
for att in atts:
    print(f"  - {att['name']} ({att['size']} bytes)")

# Add attachment
attachments.add_attachment("task-123", "/path/to/document.pdf")

# Remove attachment
attachments.remove_attachment_by_name("task-123", "document.pdf")

# Download attachment
content = attachments.get_attachment_content("task-123", 0)
with open("/tmp/downloaded.pdf", "wb") as f:
    f.write(content)
```

### From Claude Desktop (MCP)

```
User: "Show me attachments on task abc123"
Claude: [calls get_attachments tool]

Response:
[
  {
    "name": "meeting-notes.pdf",
    "preferredName": "meeting-notes.pdf",
    "size": 245680,
    "index": 0
  },
  {
    "name": "budget-spreadsheet.xlsx",
    "preferredName": "budget-spreadsheet.xlsx",
    "size": 89234,
    "index": 1
  }
]

User: "Remove the budget spreadsheet attachment"
Claude: [calls remove_attachment tool with name="budget-spreadsheet.xlsx"]

Response: "Attachment removed successfully"
```

## Advantages of This Approach

### 1. **Separation of Concerns**
- Core functionality (95% of features) stays simple with AppleScript
- Complex attachment logic isolated in separate module
- Each module can be tested independently

### 2. **Graceful Degradation**
```python
# If JXA/attachments not available, core still works
try:
    from .attachments import OmniFocusAttachments
    HAS_ATTACHMENTS = True
except ImportError:
    HAS_ATTACHMENTS = False
    # Core functionality still available!
```

### 3. **Optional Installation**
Users who don't need attachments don't pay the complexity cost:
```bash
# Minimal install (core features only)
pip install omnifocus-mcp

# Full install with attachments
pip install omnifocus-mcp[attachments]
```

### 4. **Independent Evolution**
- Can update AppleScript code without touching JXA
- Can enhance attachments without affecting core
- Different test suites, different dependencies

### 5. **Clear Documentation**
```python
def get_attachments(...):
    """Get attachments for a task.

    **Note:** Requires JXA support. This is an optional feature.
    Core task management works without attachment support.
    """
```

## Testing Strategy

### Core Client Tests (Existing)
```python
# tests/test_omnifocus_connector.py
# All existing tests continue to work unchanged
def test_get_tasks(client):
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(stdout="...")
        tasks = client.get_tasks()
        # etc.
```

### Attachment Module Tests (New, Separate)
```python
# tests/test_attachments.py
from omnifocus_mcp.attachments import OmniFocusAttachments

def test_get_attachments():
    attachments = OmniFocusAttachments(enable_safety_checks=False)

    with patch('omnifocus_mcp.jxa_helpers.run_jxa_script') as mock_jxa:
        mock_jxa.return_value = json.dumps([
            {"name": "file.pdf", "preferredName": "file.pdf", "size": 1024, "index": 0}
        ])

        result = attachments.get_attachments("task-123")

        assert len(result) == 1
        assert result[0]['name'] == 'file.pdf'
        # Verify JXA script was called
        assert 'Application("OmniFocus")' in mock_jxa.call_args[0][0]
```

## Migration Path

### Phase 1: Current State
- ✅ Core functionality with AppleScript
- ✅ No attachment support

### Phase 2: Add JXA Module (Optional)
- ✅ Core unchanged
- ✅ Add attachments.py module
- ✅ Add jxa_helpers.py
- ✅ Add optional MCP tools
- ✅ Document as optional feature

### Phase 3: User Adoption
- Users who need attachments can use them
- Users who don't need attachments unaffected
- Gather feedback on JXA reliability

### Phase 4: Potential Future (If Successful)
- Could gradually migrate other features to JXA
- But only if clear benefits emerge
- Core can stay AppleScript indefinitely

## Potential Issues & Solutions

### Issue 1: JXA Doesn't Support Everything

**Problem:** Some OmniFocus features might not work well in JXA

**Solution:** Keep those in AppleScript. Hybrid approach is fine:
```python
# Core tasks: AppleScript
client.get_tasks()
client.add_task()

# Only attachments: JXA
attachments.get_attachments()
```

### Issue 2: Performance Differences

**Problem:** JXA might be slower/faster than AppleScript

**Solution:**
- Benchmark and document
- If slower, note in docs that attachment operations may take longer
- If faster, great bonus!

### Issue 3: Error Messages Different

**Problem:** JXA errors look different from AppleScript errors

**Solution:** Normalize in the attachment module:
```python
try:
    result = run_jxa_script(script)
except subprocess.CalledProcessError as e:
    # Transform JXA error to consistent format
    raise Exception(f"Error getting attachments: {parse_jxa_error(e.stderr)}")
```

### Issue 4: Debugging Harder

**Problem:** Two execution models to debug

**Solution:**
- Separate test suites
- Clear logging in each module
- Document execution model in each file

## Implementation Effort

### Minimal Viable Attachment Support

**Time estimate:** 2-3 days

**Tasks:**
1. Create `jxa_helpers.py` (1 hour)
   - `run_jxa_script()` function
   - Basic error handling

2. Create `attachments.py` (4-6 hours)
   - `get_attachments()` method
   - `add_attachment()` method
   - `remove_attachment_by_name()` method

3. Add MCP tools (1-2 hours)
   - 3 new tools in server_fastmcp.py
   - Error handling for missing module

4. Write tests (4-6 hours)
   - Mock JXA execution
   - Test each method
   - Test error cases

5. Documentation (2-3 hours)
   - Update README
   - Add usage examples
   - Document optional nature

**Total:** ~16-20 hours of work

### Full Attachment Support

**Additional features:**
- `get_attachment_content()` - download files
- `remove_all_attachments()` - bulk remove
- Attachment metadata (creation date, type, etc.)

**Additional time:** +4-6 hours

## Decision Tree

```
Do users need attachment support?
│
├─ NO → Skip Phase 6, proceed to Phase 7
│       (Recommended: 97% coverage achieved)
│
├─ MAYBE → Implement minimal JXA module
│          - get_attachments() ✓
│          - add_attachment() ✓
│          - remove_attachment() ✓
│          - Document as optional ✓
│          - Gather user feedback
│
└─ YES, CRITICAL → Implement full JXA module
                   - All CRUD operations
                   - Download capabilities
                   - Comprehensive testing
                   - Polish error handling
```

## Recommendation

**For now: Skip Phase 6** and proceed to Phase 7.

**Rationale:**
1. No user demand yet for attachments
2. Phase 7 provides more value (project intelligence)
3. Can add JXA attachment module later if needed
4. Keeps current momentum going

**If attachment support becomes critical later:**
- Implement minimal JXA module (2-3 days)
- Doesn't affect existing functionality
- Clear upgrade path