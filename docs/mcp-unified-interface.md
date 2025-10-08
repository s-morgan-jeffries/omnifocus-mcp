# MCP Unified Interface: Claude Desktop Perspective

**Date:** 2025-10-08
**Purpose:** Show how AppleScript + JXA modules appear as unified interface to Claude

## What Claude Desktop Sees

From Claude's perspective, **there is no difference** between AppleScript-based and JXA-based tools. Everything looks like the same OmniFocus API.

### Tool Discovery

When Claude Desktop connects to the MCP server, it receives a list of available tools:

```json
{
  "tools": [
    {
      "name": "get_tasks",
      "description": "Get tasks from OmniFocus",
      "inputSchema": {
        "type": "object",
        "properties": {
          "project_id": {"type": "string"},
          "flagged_only": {"type": "boolean"}
        }
      }
    },
    {
      "name": "add_task",
      "description": "Add a new task to OmniFocus",
      "inputSchema": {
        "type": "object",
        "properties": {
          "project_id": {"type": "string"},
          "task_name": {"type": "string"},
          "note": {"type": "string"}
        },
        "required": ["project_id", "task_name"]
      }
    },
    {
      "name": "get_attachments",
      "description": "Get all attachments for a task",
      "inputSchema": {
        "type": "object",
        "properties": {
          "task_id": {"type": "string"}
        },
        "required": ["task_id"]
      }
    },
    {
      "name": "add_attachment",
      "description": "Add a file attachment to a task",
      "inputSchema": {
        "type": "object",
        "properties": {
          "task_id": {"type": "string"},
          "file_path": {"type": "string"}
        },
        "required": ["task_id", "file_path"]
      }
    }
  ]
}
```

**Notice:** Claude sees **no indication** that some tools use AppleScript and others use JXA. They're all just "OmniFocus tools".

## User Conversation Example

```
User: "Create a task called 'Review Q4 budget' in my Finance project"

Claude: I'll create that task for you.
[Calls: add_task(project_id="finance-123", task_name="Review Q4 budget")]
→ Uses AppleScript internally

Response: "Task created successfully"

User: "Attach the budget spreadsheet at /Documents/Q4-budget.xlsx to that task"

Claude: I'll attach that file to the task.
[Calls: add_attachment(task_id="task-456", file_path="/Documents/Q4-budget.xlsx")]
→ Uses JXA internally

Response: "Attachment added successfully"

User: "What files are attached to that task?"

Claude: Let me check the attachments.
[Calls: get_attachments(task_id="task-456")]
→ Uses JXA internally

Response: "The task has 1 attachment: Q4-budget.xlsx (125KB)"
```

**From Claude's perspective:** All three operations are the same type of thing - OmniFocus operations. No visible distinction.

## Implementation: Unified MCP Interface

```python
# src/omnifocus_mcp/server_fastmcp.py

from mcp.server.fastmcp import FastMCP
from .omnifocus_client import OmniFocusClient
from .attachments import OmniFocusAttachments

mcp = FastMCP("OmniFocus")

# Singleton instances
_client = None
_attachments = None

def get_client():
    global _client
    if _client is None:
        _client = OmniFocusClient()
    return _client

def get_attachments():
    global _attachments
    if _attachments is None:
        _attachments = OmniFocusAttachments()
    return _attachments


# AppleScript-based tool (core functionality)
@mcp.tool()
def add_task(project_id: str, task_name: str, note: str = "") -> str:
    """Add a new task to OmniFocus.

    Args:
        project_id: ID of the project
        task_name: Name of the task
        note: Optional note for the task

    Returns:
        Success message
    """
    client = get_client()
    # Internally uses AppleScript, but Claude doesn't know/care
    success = client.add_task(
        project_id=project_id,
        task_name=task_name,
        note=note
    )
    return "Task created successfully" if success else "Failed to create task"


# JXA-based tool (attachments)
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
    # Internally uses JXA, but Claude doesn't know/care
    success = attachments.add_attachment(task_id, file_path)
    return "Attachment added successfully" if success else "Failed to add attachment"


# JXA-based tool (attachments)
@mcp.tool()
def get_attachments(task_id: str) -> str:
    """Get all attachments for a task.

    Args:
        task_id: ID of the task

    Returns:
        JSON array of attachments with name, size, and index
    """
    attachments = get_attachments()
    # Internally uses JXA, but Claude doesn't know/care
    result = attachments.get_attachments(task_id)
    return json.dumps(result, indent=2)
```

**Key Point:** The `@mcp.tool()` decorator exposes both AppleScript and JXA functions identically. Claude just sees "tools".

## Error Handling: Also Unified

```python
# Both modules raise Python exceptions the same way

# AppleScript error
try:
    client.add_task(...)
except Exception as e:
    return f"Error creating task: {e}"

# JXA error
try:
    attachments.add_attachment(...)
except Exception as e:
    return f"Error adding attachment: {e}"
```

**From Claude's view:** Same error format, regardless of underlying implementation.

## Data Format: Unified JSON

### Task Data (AppleScript)
```json
{
  "id": "task-123",
  "name": "Review budget",
  "projectId": "proj-456",
  "dueDate": "2025-10-15T00:00:00Z",
  "tags": "finance, urgent",
  "attachmentCount": 2
}
```

### Attachment Data (JXA)
```json
[
  {
    "name": "Q4-budget.xlsx",
    "preferredName": "Q4-budget.xlsx",
    "size": 128450,
    "index": 0
  },
  {
    "name": "notes.pdf",
    "preferredName": "notes.pdf",
    "size": 45230,
    "index": 1
  }
]
```

**Both return JSON** - Claude doesn't care which script language generated it.

## Complex Workflow: Seamless Integration

```
User: "Create a new task called 'File taxes' in my Personal project,
       set the due date to April 15th, and attach my W2 form"

Claude's internal plan:
1. Find Personal project ID → get_projects() [AppleScript]
2. Create task → add_task() [AppleScript]
3. Set due date → update_task() [AppleScript]
4. Attach W2 → add_attachment() [JXA]

[Executes all 4 tool calls]

All tools return consistent JSON/text responses
Claude synthesizes: "✓ Created task 'File taxes' in Personal project,
                     due April 15, 2025, with W2.pdf attached"
```

**User experience:** Perfectly smooth. No indication of different backends.

## Advanced: Mixed Operations

```python
# Claude might do this in one conversation:

# 1. AppleScript: Get tasks
tasks = get_tasks(project_id="proj-123")

# 2. For each task (AppleScript results):
for task in tasks:
    # 3. JXA: Check attachments
    attachments = get_attachments(task_id=task['id'])

    # 4. AppleScript: Update task based on attachment count
    if len(attachments) == 0:
        update_task(task_id=task['id'], flagged=True)
```

**Seamless mixing** of AppleScript and JXA operations. Claude has no idea it's switching between execution models.

## What Claude CAN'T See

❌ Which language executes the tool (AppleScript vs JXA)
❌ Internal subprocess calls
❌ Whether module is optional
❌ Execution performance differences
❌ Testing complexity

## What Claude DOES See

✅ Tool name and description
✅ Input parameters (schema)
✅ Return value (JSON/text)
✅ Error messages
✅ Success/failure status

## Implementation Benefits

### 1. **Transparent to Users**

User doesn't need to know:
- "Use get_tasks for AppleScript features"
- "Use get_attachments for JXA features"

They just use **OmniFocus features**.

### 2. **Consistent Developer Experience**

```python
# Adding any new tool is the same pattern:

@mcp.tool()
def my_new_feature(param: str) -> str:
    """Do something."""
    # Can use AppleScript OR JXA internally
    # Claude doesn't care
    return result
```

### 3. **Easy Migration Path**

If we later want to move something from AppleScript to JXA:

```python
# Before
@mcp.tool()
def get_tasks(...):
    client = get_client()  # AppleScript
    return client.get_tasks()

# After - SAME INTERFACE
@mcp.tool()
def get_tasks(...):
    tasks = get_tasks_via_jxa()  # Switched to JXA
    return tasks  # Same return format
```

**Claude Desktop sees no difference** - same tool name, same parameters, same response.

### 4. **Graceful Feature Additions**

New attachment tools just appear in Claude's tool list:

```python
# Week 1: No attachment support
tools = ["get_tasks", "add_task", "update_task", ...]

# Week 2: Add attachment module
tools = ["get_tasks", "add_task", "update_task", ...,
         "get_attachments", "add_attachment", "remove_attachment"]
```

**From Claude's view:** "Cool, OmniFocus gained new capabilities!"

No indication it's a different implementation approach.

## MCP Protocol Perspective

```
┌─────────────────────────────────────────────────────────┐
│                     Claude Desktop                       │
│                                                          │
│  "I need to use OmniFocus MCP tools to help the user"  │
└─────────────────────────────────────────────────────────┘
                          │
                          │ MCP Protocol (JSON-RPC)
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   MCP Server (Python)                    │
│                                                          │
│  @mcp.tool() decorators expose unified interface        │
│                                                          │
│  ┌──────────────────┐      ┌──────────────────┐       │
│  │  AppleScript     │      │  JXA             │       │
│  │  Tools           │      │  Tools           │       │
│  │  - get_tasks     │      │  - get_attach.   │       │
│  │  - add_task      │      │  - add_attach.   │       │
│  │  - update_task   │      │  - remove_attach.│       │
│  └──────────────────┘      └──────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

**To Claude:** Everything above the MCP Protocol line is transparent. Just sees "OmniFocus MCP Server" with a list of tools.

## Real-World Example: Claude's Perspective

### User Request
```
User: "I have a task called 'Prepare presentation' - can you attach my
       slide deck and also add a due date of next Friday?"
```

### Claude's Tool Calls (What It Sees)

```json
// 1. Find the task
CALL: search_tasks(query="Prepare presentation")
RESPONSE: [{"id": "task-789", "name": "Prepare presentation", ...}]

// 2. Set due date (AppleScript internally)
CALL: update_task(task_id="task-789", due_date="2025-10-17T17:00:00Z")
RESPONSE: "Task updated successfully"

// 3. Add attachment (JXA internally)
CALL: add_attachment(task_id="task-789", file_path="/Users/Morgan/Documents/slides.pptx")
RESPONSE: "Attachment added successfully"
```

### Claude's Response to User
```
I've updated your "Prepare presentation" task:
- Set due date to Friday, October 17, 2025 at 5:00 PM
- Attached slides.pptx to the task

Is there anything else you'd like me to do with this task?
```

**Claude has no idea** that:
- Step 2 used AppleScript's `update_task` implementation
- Step 3 used JXA's `add_attachment` implementation
- Two completely different execution paths were used

**It just knows:** "I called OmniFocus tools and they worked."

## Conclusion

**Yes, completely unified from Claude's perspective.**

The separation between AppleScript and JXA is purely an **implementation detail** hidden behind the MCP tool interface.

**Benefits:**
- ✅ Users get seamless OmniFocus integration
- ✅ We get clean architecture separation
- ✅ Each module can evolve independently
- ✅ Testing stays manageable
- ✅ Can add/modify features without breaking the interface

**This is actually ideal MCP design** - expose clean, unified tools while using the best implementation approach for each feature internally.
