# MCP Server Schema and API Design Review

## Executive Summary

This document provides a comprehensive analysis of the OmniFocus MCP server's schema design, identifies gaps and improvement opportunities, and recommends specific enhancements aligned with MCP protocol best practices and OmniFocus capabilities.

**Key Findings:**
- ✅ Current schemas are functional and follow basic MCP conventions
- ⚠️ Missing critical OmniFocus metadata (dates, contexts, tags, completion status)
- ⚠️ No output schemas defined (MCP 2025 best practice)
- ⚠️ Inconsistent error responses
- ⚠️ Limited extensibility for future enhancements
- ⚠️ Response format relies only on text formatting (should support structured data)

---

## 1. Current Schema Analysis

### 1.1 Tool: `get_projects`

#### Current Implementation
```python
Tool(
    name="get_projects",
    description="Get all active projects from OmniFocus with their folder hierarchy, names, notes, and status",
    inputSchema={
        "type": "object",
        "properties": {},
        "required": []
    }
)
```

**Current Response Format:**
```python
# Text-only response with manual formatting
f"Found {len(projects)} active projects:\n\n" +
"\n\n".join([
    f"**{p['name']}**\n"
    f"ID: {p['id']}\n"
    f"Folder: {p['folderPath'] or '(root)'}\n"
    f"Status: {p['status']}\n"
    f"Note: {p['note'][:100] + '...' if len(p['note']) > 100 else p['note']}"
])
```

#### Issues Identified

1. **Missing Input Options:**
   - No filter by status (active/on hold/completed/dropped)
   - No filter by folder
   - No limit/pagination options
   - No sort order specification

2. **Missing Output Schema:**
   - Clients don't know response structure ahead of time
   - No automatic validation
   - Text-only format prevents structured data usage

3. **Incomplete Data Model:**
   - Missing: due dates, defer dates, completion dates
   - Missing: contexts/tags
   - Missing: review dates and review status
   - Missing: estimated duration
   - Missing: sequential/parallel type
   - Missing: number of tasks
   - Missing: flagged status

4. **Response Format Issues:**
   - Note truncation at 100 chars loses data
   - No structured data for programmatic use
   - Markdown formatting hardcoded (not flexible)

---

### 1.2 Tool: `search_projects`

#### Current Implementation
```python
Tool(
    name="search_projects",
    description="Search OmniFocus projects by name, note content, or folder path",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query to match against project names, notes, or folder paths"
            }
        },
        "required": ["query"]
    }
)
```

#### Issues Identified

1. **Limited Search Capabilities:**
   - No field-specific search (name only, note only, etc.)
   - No case-sensitivity control
   - No regex support
   - No filter by status while searching

2. **Missing Input Parameters:**
   - No limit on results
   - No search scope specification
   - No tag/context filtering

3. **No Output Schema:**
   - Same response format issues as `get_projects`
   - No structured data support

4. **Implementation Limitations:**
   - Client-side filtering only (inefficient for large datasets)
   - Searches all fields unconditionally

---

### 1.3 Tool: `add_task`

#### Current Implementation
```python
Tool(
    name="add_task",
    description="Add a new task to a specific OmniFocus project",
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "The ID of the project to add the task to"
            },
            "task_name": {
                "type": "string",
                "description": "The name/title of the task"
            },
            "note": {
                "type": "string",
                "description": "Optional note/description for the task"
            }
        },
        "required": ["project_id", "task_name"]
    }
)
```

**Current Response:**
```python
# Success
f"Successfully added task '{task_name}' to project {project_id}"

# Failure
f"Failed to add task '{task_name}' to project {project_id}"
```

#### Issues Identified

1. **Missing Task Properties:**
   - No due date
   - No defer date
   - No context/tags
   - No flagged status
   - No estimated duration
   - No repeat/recurrence
   - No action groups (sequential/parallel tasks)

2. **Poor Error Handling:**
   - Generic failure message
   - No error details or reason codes
   - No guidance on how to fix

3. **No Output Schema:**
   - Doesn't return created task ID
   - Doesn't return created task details
   - Can't verify what was created

4. **Limited Validation:**
   - No validation that project_id exists before attempting
   - No validation of task_name format

---

### 1.4 Tool: `add_note`

#### Current Implementation
```python
Tool(
    name="add_note",
    description="Append a note to an existing OmniFocus project",
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "The ID of the project to add the note to"
            },
            "note_text": {
                "type": "string",
                "description": "The note text to append to the project"
            }
        },
        "required": ["project_id", "note_text"]
    }
)
```

#### Issues Identified

1. **Limited Functionality:**
   - Only supports append (not replace or prepend)
   - No ability to add notes to tasks
   - No note formatting options

2. **Poor Error Handling:**
   - Generic failure messages
   - No validation of project existence

3. **No Output Schema:**
   - Doesn't return updated note content
   - Can't verify what was actually written

---

## 2. Missing Tools and Functionality

Based on OmniFocus capabilities and MCP best practices, the following tools should be considered:

### 2.1 Task Management
- `get_tasks` - Retrieve tasks from a project or with specific filters
- `update_task` - Modify existing task properties
- `complete_task` - Mark a task as complete
- `delete_task` - Delete a task

### 2.2 Project Management
- `create_project` - Create a new project
- `update_project` - Modify project properties
- `get_project_details` - Get detailed information about a specific project

### 2.3 Context/Tags
- `get_contexts` - List available contexts/tags
- `add_context_to_task` - Assign context to task

### 2.4 Perspectives
- `get_perspectives` - List available perspectives
- `get_perspective_items` - Get items from a specific perspective

---

## 3. MCP Protocol Best Practices (2025)

Based on the latest MCP specification and best practices:

### 3.1 Output Schemas

**Best Practice:** All tools should define output schemas (introduced in MCP 2025-06-18 spec)

**Benefits:**
- Clients know response structure ahead of time
- Automatic validation of responses
- Better error detection
- Enables structured content usage

**Implementation Pattern:**
```python
Tool(
    name="get_projects",
    inputSchema={...},
    outputSchema={
        "type": "object",
        "properties": {
            "projects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "status": {"type": "string"},
                        # ... more properties
                    }
                }
            },
            "count": {"type": "integer"}
        },
        "required": ["projects", "count"]
    }
)
```

### 3.2 Structured Content Response

**Best Practice:** Return both TextContent (for backward compatibility) and structured_data

**Example:**
```python
return [TextContent(
    type="text",
    text="Found 3 projects: ...",
    structured_data={
        "projects": [...],
        "count": 3
    }
)]
```

### 3.3 Tool Design Principles

1. **Group Related Operations:** Don't create a tool for every API endpoint
2. **Higher-Level Functions:** Design tools for user tasks, not just API calls
3. **Clear Naming:** Use verb_noun pattern (get_projects, add_task)
4. **Comprehensive Descriptions:** Explain what the tool does and when to use it
5. **Sensible Defaults:** Make optional parameters actually optional with good defaults

### 3.4 Error Handling

**Best Practice:** Use consistent error response structure

**Recommended Pattern:**
```python
{
    "type": "text",
    "text": "Error: ...",
    "structured_data": {
        "error": {
            "code": "PROJECT_NOT_FOUND",
            "message": "Project with ID 'xyz' not found",
            "details": {
                "project_id": "xyz",
                "suggestions": ["Use get_projects to list available projects"]
            }
        }
    }
}
```

### 3.5 Schema Extensibility

**Best Practice:** Design schemas that can accept new fields without breaking

**Pattern:**
- Use "additionalProperties": false sparingly
- Document optional vs required clearly
- Version your schemas if needed
- Use clear property names that won't conflict

---

## 4. OmniFocus Data Model Analysis

### 4.1 Available Project Properties (from AppleScript)

Based on OmniFocus AppleScript documentation:

```javascript
// Core Properties
- id (string)
- name (string)
- note (string)
- status (active/on-hold/completed/dropped)

// Dates
- creation_date (date)
- modification_date (date)
- due_date (date or null)
- defer_date (date or null)
- completion_date (date or null)
- next_review_date (date or null)
- last_review_date (date or null)

// Hierarchy
- folder (reference to folder)
- folder_path (string, computed)

// Metadata
- completed (boolean, read-only)
- dropped (boolean, read-only)
- flagged (boolean)
- sequential (boolean) // vs parallel
- singleton_action_holder (boolean) // for single action lists

// Review
- review_interval (duration)
- next_review_date (date or null)

// Context/Tags (OmniFocus 3+)
- tags (array of tag references)
- context (reference, deprecated in OF3)

// Tasks
- root_task (reference) // root task containing all subtasks
- number_of_tasks (integer, computed)
- number_of_completed_tasks (integer, computed)
- number_of_available_tasks (integer, computed)
```

### 4.2 Available Task Properties

```javascript
// Core Properties
- id (string)
- name (string)
- note (string)
- completed (boolean, read-only)
- completion_date (date or null)

// Dates
- due_date (date or null)
- defer_date (date or null)
- effective_due_date (date or null, read-only)
- effective_defer_date (date or null, read-only)

// Metadata
- flagged (boolean)
- dropped (boolean)
- estimated_minutes (integer or null)
- sequential (boolean) // for action groups

// Context/Tags
- tags (array)
- context (reference, deprecated)

// Hierarchy
- parent_task (reference or null)
- containing_project (reference or null)

// Repeat
- repetition_rule (reference or null)
```

---

## 5. Recommended Schema Improvements

### 5.1 Enhanced `get_projects` Tool

#### Improved Input Schema
```python
Tool(
    name="get_projects",
    description="""Get projects from OmniFocus with filtering and sorting options.

    Returns detailed project information including hierarchy, dates, status, and task counts.
    Use filters to narrow down results by status, folder, or review status.
    """,
    inputSchema={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["active", "on-hold", "completed", "dropped", "all"],
                "description": "Filter projects by status (default: active)",
                "default": "active"
            },
            "folder_path": {
                "type": "string",
                "description": "Filter to projects in specific folder path (e.g., 'Work > Clients')"
            },
            "include_completed": {
                "type": "boolean",
                "description": "Include completed projects (default: false)",
                "default": False
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of projects to return (default: no limit)",
                "minimum": 1
            },
            "sort_by": {
                "type": "string",
                "enum": ["name", "due_date", "modification_date", "folder_path"],
                "description": "Sort order for results (default: name)",
                "default": "name"
            },
            "include_tasks": {
                "type": "boolean",
                "description": "Include task count and available tasks (default: true)",
                "default": True
            }
        },
        "required": []
    },
    outputSchema={
        "type": "object",
        "properties": {
            "projects": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "note": {"type": "string"},
                        "status": {
                            "type": "string",
                            "enum": ["active", "on-hold", "completed", "dropped"]
                        },
                        "folder_path": {
                            "type": ["string", "null"],
                            "description": "Folder hierarchy (e.g., 'Work > Projects')"
                        },
                        "dates": {
                            "type": "object",
                            "properties": {
                                "created": {"type": ["string", "null"], "format": "date-time"},
                                "modified": {"type": ["string", "null"], "format": "date-time"},
                                "due": {"type": ["string", "null"], "format": "date-time"},
                                "defer": {"type": ["string", "null"], "format": "date-time"},
                                "completed": {"type": ["string", "null"], "format": "date-time"},
                                "next_review": {"type": ["string", "null"], "format": "date-time"},
                                "last_review": {"type": ["string", "null"], "format": "date-time"}
                            }
                        },
                        "task_counts": {
                            "type": "object",
                            "properties": {
                                "total": {"type": "integer"},
                                "completed": {"type": "integer"},
                                "available": {"type": "integer"},
                                "remaining": {"type": "integer"}
                            }
                        },
                        "flags": {
                            "type": "object",
                            "properties": {
                                "flagged": {"type": "boolean"},
                                "sequential": {"type": "boolean"},
                                "completed": {"type": "boolean"},
                                "dropped": {"type": "boolean"}
                            }
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of tag names"
                        }
                    },
                    "required": ["id", "name", "status"]
                }
            },
            "count": {
                "type": "integer",
                "description": "Total number of projects returned"
            },
            "filters_applied": {
                "type": "object",
                "description": "Summary of filters that were applied"
            }
        },
        "required": ["projects", "count"]
    }
)
```

#### Improved Response Implementation
```python
async def call_tool_get_projects(arguments: dict) -> list[TextContent]:
    """Handle get_projects with enhanced filtering and structured output."""
    # Parse arguments with defaults
    status_filter = arguments.get("status", "active")
    folder_path = arguments.get("folder_path")
    include_completed = arguments.get("include_completed", False)
    limit = arguments.get("limit")
    sort_by = arguments.get("sort_by", "name")
    include_tasks = arguments.get("include_tasks", True)

    try:
        # Get projects with enhanced data
        projects = client.get_projects_enhanced(
            status=status_filter,
            folder_path=folder_path,
            include_completed=include_completed,
            include_tasks=include_tasks
        )

        # Apply sorting
        projects = sort_projects(projects, sort_by)

        # Apply limit
        if limit:
            projects = projects[:limit]

        # Build structured response
        structured_data = {
            "projects": projects,
            "count": len(projects),
            "filters_applied": {
                "status": status_filter,
                "folder_path": folder_path,
                "include_completed": include_completed
            }
        }

        # Build human-readable text (backward compatibility)
        text_parts = [f"Found {len(projects)} projects"]
        if folder_path:
            text_parts.append(f"in folder '{folder_path}'")
        text_parts.append(f"(status: {status_filter})")

        text = " ".join(text_parts) + ":\n\n"
        text += format_projects_as_text(projects)

        return [TextContent(
            type="text",
            text=text,
            structured_data=structured_data
        )]

    except Exception as e:
        logger.error(f"Error in get_projects: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error retrieving projects: {str(e)}",
            structured_data={
                "error": {
                    "code": "GET_PROJECTS_FAILED",
                    "message": str(e),
                    "details": {"arguments": arguments}
                }
            }
        )]
```

---

### 5.2 Enhanced `add_task` Tool

#### Improved Input Schema
```python
Tool(
    name="add_task",
    description="""Add a new task to an OmniFocus project.

    Creates a task with specified properties including dates, context, and flags.
    Returns the created task's ID and details for verification.
    """,
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "ID of the project to add the task to (required)"
            },
            "task_name": {
                "type": "string",
                "description": "Name/title of the task (required)",
                "minLength": 1
            },
            "note": {
                "type": "string",
                "description": "Optional note/description for the task"
            },
            "due_date": {
                "type": "string",
                "format": "date-time",
                "description": "Due date in ISO 8601 format (e.g., '2025-10-15T17:00:00Z')"
            },
            "defer_date": {
                "type": "string",
                "format": "date-time",
                "description": "Defer date in ISO 8601 format"
            },
            "estimated_minutes": {
                "type": "integer",
                "description": "Estimated duration in minutes",
                "minimum": 1
            },
            "flagged": {
                "type": "boolean",
                "description": "Mark task as flagged (default: false)",
                "default": False
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of tag names to apply to the task"
            },
            "parent_task_id": {
                "type": "string",
                "description": "ID of parent task (for subtasks)"
            }
        },
        "required": ["project_id", "task_name"]
    },
    outputSchema={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "task": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "name": {"type": "string"},
                    "project_id": {"type": "string"},
                    "created_date": {"type": "string", "format": "date-time"}
                },
                "required": ["id", "name", "project_id"]
            },
            "message": {"type": "string"}
        },
        "required": ["success", "message"]
    }
)
```

---

### 5.3 New Tool: `get_tasks`

```python
Tool(
    name="get_tasks",
    description="""Get tasks from OmniFocus with filtering options.

    Retrieve tasks from a specific project, or filter across all tasks by various criteria
    including due dates, flags, contexts, and completion status.
    """,
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "Filter to tasks in specific project"
            },
            "completed": {
                "type": "boolean",
                "description": "Filter by completion status (default: false, only incomplete)"
            },
            "flagged": {
                "type": "boolean",
                "description": "Filter to only flagged tasks"
            },
            "due_soon": {
                "type": "integer",
                "description": "Filter to tasks due within N days",
                "minimum": 0
            },
            "available_only": {
                "type": "boolean",
                "description": "Only include available tasks (not blocked by defer dates)",
                "default": True
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter to tasks with any of these tags"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of tasks to return",
                "minimum": 1
            }
        },
        "required": []
    },
    outputSchema={
        "type": "object",
        "properties": {
            "tasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "note": {"type": "string"},
                        "project_id": {"type": "string"},
                        "project_name": {"type": "string"},
                        "completed": {"type": "boolean"},
                        "flagged": {"type": "boolean"},
                        "dates": {
                            "type": "object",
                            "properties": {
                                "due": {"type": ["string", "null"], "format": "date-time"},
                                "defer": {"type": ["string", "null"], "format": "date-time"},
                                "completed": {"type": ["string", "null"], "format": "date-time"}
                            }
                        },
                        "estimated_minutes": {"type": ["integer", "null"]},
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "required": ["id", "name", "completed"]
                }
            },
            "count": {"type": "integer"}
        },
        "required": ["tasks", "count"]
    }
)
```

---

### 5.4 New Tool: `update_project`

```python
Tool(
    name="update_project",
    description="""Update properties of an existing OmniFocus project.

    Modify project name, notes, status, dates, or other properties.
    Only provided fields will be updated; others remain unchanged.
    """,
    inputSchema={
        "type": "object",
        "properties": {
            "project_id": {
                "type": "string",
                "description": "ID of project to update (required)"
            },
            "name": {
                "type": "string",
                "description": "New project name",
                "minLength": 1
            },
            "note": {
                "type": "string",
                "description": "Replace project note (use add_note to append)"
            },
            "status": {
                "type": "string",
                "enum": ["active", "on-hold"],
                "description": "Change project status"
            },
            "due_date": {
                "type": ["string", "null"],
                "format": "date-time",
                "description": "Set due date (null to clear)"
            },
            "defer_date": {
                "type": ["string", "null"],
                "format": "date-time",
                "description": "Set defer date (null to clear)"
            },
            "flagged": {
                "type": "boolean",
                "description": "Set flagged status"
            },
            "sequential": {
                "type": "boolean",
                "description": "Set sequential (vs parallel) mode"
            }
        },
        "required": ["project_id"]
    },
    outputSchema={
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "updated_fields": {
                "type": "array",
                "items": {"type": "string"}
            },
            "project": {
                "type": "object",
                "description": "Updated project state"
            },
            "message": {"type": "string"}
        },
        "required": ["success", "message"]
    }
)
```

---

## 6. Error Handling Improvements

### 6.1 Error Code System

Define consistent error codes:

```python
class ErrorCode:
    # Project errors
    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
    PROJECT_DROPPED = "PROJECT_DROPPED"
    PROJECT_COMPLETED = "PROJECT_COMPLETED"

    # Task errors
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_ALREADY_COMPLETED = "TASK_ALREADY_COMPLETED"

    # Validation errors
    INVALID_PROJECT_ID = "INVALID_PROJECT_ID"
    INVALID_DATE_FORMAT = "INVALID_DATE_FORMAT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"

    # System errors
    OMNIFOCUS_NOT_RUNNING = "OMNIFOCUS_NOT_RUNNING"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    APPLESCRIPT_ERROR = "APPLESCRIPT_ERROR"

    # Generic
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
```

### 6.2 Error Response Structure

```python
def create_error_response(
    code: str,
    message: str,
    details: dict = None,
    suggestions: list[str] = None
) -> list[TextContent]:
    """Create a standardized error response."""

    structured_data = {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "suggestions": suggestions or []
        }
    }

    # Build human-readable text
    text = f"Error: {message}"
    if suggestions:
        text += "\n\nSuggestions:\n" + "\n".join(f"- {s}" for s in suggestions)

    return [TextContent(
        type="text",
        text=text,
        structured_data=structured_data
    )]
```

### 6.3 Validation Helper

```python
def validate_project_exists(project_id: str) -> tuple[bool, Optional[str]]:
    """Validate that a project exists and is accessible.

    Returns: (is_valid, error_message)
    """
    try:
        projects = client.get_projects()
        project_ids = [p['id'] for p in projects]

        if project_id not in project_ids:
            return False, f"Project '{project_id}' not found"

        return True, None

    except Exception as e:
        return False, f"Error validating project: {str(e)}"
```

---

## 7. Backward Compatibility Strategy

### 7.1 Versioning Approach

**Option 1: Additive Changes Only**
- Add new optional fields to existing tools
- Add new tools without modifying existing ones
- Maintain text-based responses alongside structured data
- **Recommended for current stage**

**Option 2: Explicit Versioning**
- Add version field to tool names (e.g., `get_projects_v2`)
- Maintain both versions temporarily
- Deprecate old versions with warnings
- **Only if breaking changes needed**

### 7.2 Implementation Plan

**Phase 1: Add Output Schemas (Non-Breaking)**
1. Add `outputSchema` to all existing tools
2. Return both text and `structured_data` in responses
3. Existing clients continue to work (use text)
4. New clients can use structured data

**Phase 2: Enhance Input Schemas (Non-Breaking)**
1. Add new optional parameters to existing tools
2. Maintain default behavior when parameters not provided
3. Document new parameters clearly

**Phase 3: Add New Tools**
1. Implement new tools for missing functionality
2. Don't modify existing tool behavior
3. Cross-reference tools in descriptions

**Phase 4: Deprecation (If Needed)**
1. Announce deprecation with 3-month notice
2. Add deprecation warnings to tool descriptions
3. Provide migration guide
4. Remove after deprecation period

---

## 8. Documentation Improvements

### 8.1 Enhanced Tool Descriptions

**Current:**
```python
description="Get all active projects from OmniFocus with their folder hierarchy, names, notes, and status"
```

**Improved:**
```python
description="""Get projects from OmniFocus with detailed information and filtering.

This tool retrieves projects with their complete metadata including:
- Project hierarchy (folder paths)
- Status and dates (due, defer, review, completion)
- Task counts (total, completed, available)
- Tags and flags

Use the 'status' parameter to filter by project state (active, on-hold, completed, dropped).
Use 'folder_path' to narrow results to a specific folder.
Results can be sorted by name, due date, or modification date.

Examples:
- Get all active projects: {}
- Get projects in Work folder: {"folder_path": "Work"}
- Get recently modified: {"sort_by": "modification_date", "limit": 10}
- Include completed projects: {"include_completed": true}
"""
```

### 8.2 Input Parameter Documentation

Add examples and constraints to all parameters:

```python
"due_date": {
    "type": "string",
    "format": "date-time",
    "description": "Due date in ISO 8601 format. Examples: '2025-10-15T17:00:00Z' (UTC), '2025-10-15T09:00:00-08:00' (with timezone). Use null to clear existing due date."
}
```

### 8.3 Error Documentation

Document possible errors in tool descriptions:

```python
description="""...

Possible Errors:
- PROJECT_NOT_FOUND: The specified project_id doesn't exist
- OMNIFOCUS_NOT_RUNNING: OmniFocus application is not running
- PERMISSION_DENIED: Insufficient permissions to access OmniFocus
- INVALID_DATE_FORMAT: Date string is not in valid ISO 8601 format
"""
```

---

## 9. Client Code Updates Required

### 9.1 Enhanced `get_projects` Implementation

```python
def get_projects_enhanced(
    self,
    status: str = "active",
    folder_path: Optional[str] = None,
    include_completed: bool = False,
    include_tasks: bool = True
) -> list[dict[str, Any]]:
    """Get projects with enhanced data and filtering."""

    script = f'''
    use AppleScript version "2.4"
    use scripting additions
    use framework "Foundation"

    set output to ""

    tell application "OmniFocus"
        tell front document
            set allProjects to flattened projects

            repeat with proj in allProjects
                try
                    -- Get basic properties
                    set projId to id of proj
                    set projName to name of proj
                    set projNote to note of proj
                    set projStatus to status of proj as text

                    -- Apply status filter
                    set includeProject to false
                    if "{status}" is "all" then
                        set includeProject to true
                    else if "{status}" is "active" and projStatus is "active" then
                        set includeProject to true
                    else if projStatus is "{status}" then
                        set includeProject to true
                    end if

                    if not includeProject then error "skip"

                    -- Get dates
                    set creationDate to creation date of proj
                    set modificationDate to modification date of proj
                    set dueDate to due date of proj
                    set deferDate to defer date of proj
                    set completionDate to completion date of proj
                    set nextReviewDate to next review date of proj

                    -- Get flags
                    set isFlagged to flagged of proj
                    set isSequential to sequential of proj
                    set isCompleted to completed of proj
                    set isDropped to dropped of proj

                    -- Get folder path
                    set folderPath to ""
                    try
                        set parentFolder to container of proj
                        if class of parentFolder is folder then
                            set folderPath to name of parentFolder
                            set currentFolder to parentFolder
                            repeat
                                try
                                    set parentOfFolder to container of currentFolder
                                    if class of parentOfFolder is folder then
                                        set folderPath to (name of parentOfFolder) & " > " & folderPath
                                        set currentFolder to parentOfFolder
                                    else
                                        exit repeat
                                    end if
                                on error
                                    exit repeat
                                end try
                            end repeat
                        end if
                    end try

                    -- Apply folder filter
                    if "{folder_path}" is not "" and folderPath does not contain "{folder_path}" then
                        error "skip folder"
                    end if

                    -- Get task counts
                    set taskCount to 0
                    set completedCount to 0
                    set availableCount to 0

                    {'
                    if include_tasks:
                        script += '''
                    try
                        set rootTask to root task of proj
                        set allTasks to flattened tasks of rootTask
                        set taskCount to count of allTasks

                        repeat with t in allTasks
                            if completed of t then
                                set completedCount to completedCount + 1
                            end if
                            -- Task is available if not deferred
                            try
                                set taskDefer to defer date of t
                                if taskDefer is missing value or taskDefer < (current date) then
                                    if not completed of t then
                                        set availableCount to availableCount + 1
                                    end if
                                end if
                            on error
                                if not completed of t then
                                    set availableCount to availableCount + 1
                                end if
                            end try
                        end repeat
                    end try
                        '''
                    }

                    -- Get tags
                    set tagList to ""
                    try
                        set projectTags to tags of proj
                        repeat with t in projectTags
                            if tagList is not "" then set tagList to tagList & ","
                            set tagList to tagList & name of t
                        end repeat
                    end try

                    -- Build JSON
                    set jsonLine to "{{" & ¬
                        "\\"id\\": \\"" & projId & "\\", " & ¬
                        "\\"name\\": \\"" & my escapeJSON(projName) & "\\", " & ¬
                        "\\"note\\": \\"" & my escapeJSON(projNote) & "\\", " & ¬
                        "\\"status\\": \\"" & projStatus & "\\", " & ¬
                        "\\"folder_path\\": \\"" & my escapeJSON(folderPath) & "\\", " & ¬
                        "\\"dates\\": {{" & ¬
                        "\\"created\\": " & my dateToISO(creationDate) & ", " & ¬
                        "\\"modified\\": " & my dateToISO(modificationDate) & ", " & ¬
                        "\\"due\\": " & my dateToISO(dueDate) & ", " & ¬
                        "\\"defer\\": " & my dateToISO(deferDate) & ", " & ¬
                        "\\"completed\\": " & my dateToISO(completionDate) & ", " & ¬
                        "\\"next_review\\": " & my dateToISO(nextReviewDate) & ¬
                        "}}, " & ¬
                        "\\"task_counts\\": {{" & ¬
                        "\\"total\\": " & taskCount & ", " & ¬
                        "\\"completed\\": " & completedCount & ", " & ¬
                        "\\"available\\": " & availableCount & ", " & ¬
                        "\\"remaining\\": " & (taskCount - completedCount) & ¬
                        "}}, " & ¬
                        "\\"flags\\": {{" & ¬
                        "\\"flagged\\": " & (isFlagged as text) & ", " & ¬
                        "\\"sequential\\": " & (isSequential as text) & ", " & ¬
                        "\\"completed\\": " & (isCompleted as text) & ", " & ¬
                        "\\"dropped\\": " & (isDropped as text) & ¬
                        "}}, " & ¬
                        "\\"tags\\": [" & my jsonArrayFromCSV(tagList) & "]" & ¬
                        "}}"

                    if output is not "" then
                        set output to output & "," & linefeed
                    end if
                    set output to output & jsonLine
                end try
            end repeat
        end tell
    end tell

    return "[" & linefeed & output & linefeed & "]"

    -- Helper: Convert AppleScript date to ISO 8601 string
    on dateToISO(theDate)
        if theDate is missing value then
            return "null"
        end if

        set theYear to year of theDate as string
        set theMonth to text -2 thru -1 of ("0" & (month of theDate as integer))
        set theDay to text -2 thru -1 of ("0" & (day of theDate as integer))
        set theHour to text -2 thru -1 of ("0" & (hours of theDate))
        set theMinute to text -2 thru -1 of ("0" & (minutes of theDate))
        set theSecond to text -2 thru -1 of ("0" & (seconds of theDate))

        return "\\"" & theYear & "-" & theMonth & "-" & theDay & "T" & ¬
               theHour & ":" & theMinute & ":" & theSecond & "Z\\""
    end dateToISO

    -- Helper: Convert CSV to JSON array
    on jsonArrayFromCSV(csvString)
        if csvString is "" then return ""

        set AppleScript's text item delimiters to ","
        set items to text items of csvString
        set AppleScript's text item delimiters to ""

        set result to ""
        repeat with i in items
            if result is not "" then set result to result & ", "
            set result to result & "\\"" & i & "\\""
        end repeat

        return result
    end jsonArrayFromCSV

    -- Helper to escape JSON strings
    on escapeJSON(txt)
        set txt to my replaceText(txt, "\\\\", "\\\\\\\\")
        set txt to my replaceText(txt, "\\"", "\\\\\\"")
        set txt to my replaceText(txt, linefeed, "\\\\n")
        set txt to my replaceText(txt, return, "\\\\r")
        set txt to my replaceText(txt, tab, "\\\\t")
        return txt
    end escapeJSON

    -- Helper to replace text
    on replaceText(sourceText, oldText, newText)
        set AppleScript's text item delimiters to oldText
        set textItems to text items of sourceText
        set AppleScript's text item delimiters to newText
        set resultText to textItems as text
        set AppleScript's text item delimiters to ""
        return resultText
    end replaceText
    '''

    try:
        result = run_applescript(script)
        if result:
            return json.loads(result)
        else:
            return []
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error querying OmniFocus: {e.stderr}")
    except json.JSONDecodeError as e:
        raise Exception(f"Error parsing OmniFocus output: {e}")
```

---

## 10. Testing Implications

### 10.1 Schema Validation Tests

Add tests for schema compliance:

```python
def test_get_projects_output_schema():
    """Test that get_projects response matches output schema."""
    result = await call_tool("get_projects", {})

    # Extract structured data
    structured = result[0].structured_data

    # Validate against schema
    assert "projects" in structured
    assert "count" in structured
    assert isinstance(structured["projects"], list)
    assert isinstance(structured["count"], int)

    # Validate project structure
    if structured["projects"]:
        project = structured["projects"][0]
        assert "id" in project
        assert "name" in project
        assert "status" in project
        assert "dates" in project
        assert "task_counts" in project
        assert "flags" in project
```

### 10.2 Backward Compatibility Tests

```python
def test_get_projects_text_format_maintained():
    """Test that text response format is maintained for backward compatibility."""
    result = await call_tool("get_projects", {})

    # Verify text response exists
    assert result[0].type == "text"
    assert result[0].text.startswith("Found")

    # Verify it contains project information
    assert "ID:" in result[0].text
    assert "Folder:" in result[0].text
    assert "Status:" in result[0].text
```

### 10.3 Error Handling Tests

```python
def test_add_task_invalid_project():
    """Test error handling for invalid project ID."""
    result = await call_tool("add_task", {
        "project_id": "invalid-id",
        "task_name": "Test Task"
    })

    # Check error structure
    assert result[0].structured_data["error"]["code"] == "PROJECT_NOT_FOUND"
    assert "suggestions" in result[0].structured_data["error"]
    assert len(result[0].structured_data["error"]["suggestions"]) > 0
```

---

## 11. Implementation Priority

### Priority 1: Critical (Implement First)
1. ✅ Add output schemas to all existing tools
2. ✅ Return structured_data in all responses
3. ✅ Implement standardized error handling
4. ✅ Add error codes and suggestions

### Priority 2: High Value (Next Sprint)
1. ⚠️ Enhance `get_projects` with filtering and sorting
2. ⚠️ Enhance `get_projects` with complete OmniFocus data
3. ⚠️ Enhance `add_task` with dates, tags, and flags
4. ⚠️ Add validation helpers

### Priority 3: New Functionality (Future)
1. 🔲 Implement `get_tasks` tool
2. 🔲 Implement `update_project` tool
3. 🔲 Implement `complete_task` tool
4. 🔲 Implement `update_task` tool

### Priority 4: Nice to Have
1. 🔲 Add `get_contexts` tool
2. 🔲 Add `get_perspectives` tool
3. 🔲 Add `create_project` tool
4. 🔲 Add pagination support for large result sets

---

## 12. Code Change Summary

### Files to Modify

1. **`server.py`**
   - Add output schemas to all tool definitions
   - Update `call_tool()` to return structured_data
   - Implement error code constants
   - Add standardized error handling
   - Enhance tool descriptions

2. **`omnifocus_client.py`**
   - Add `get_projects_enhanced()` method
   - Add `add_task_enhanced()` method
   - Add validation helper methods
   - Enhance AppleScript to capture more data
   - Add date formatting utilities

3. **New file: `error_codes.py`**
   - Define all error codes
   - Error response builder
   - Validation helpers

4. **Test files**
   - Add schema validation tests
   - Add backward compatibility tests
   - Add error handling tests
   - Update existing tests for new structured data

---

## 13. Migration Guide for Clients

### For Existing Clients (No Changes Required)

Existing clients will continue to work without modification:
- Text responses remain unchanged
- Same tool names and required parameters
- Same behavior when optional parameters not provided

### For New Clients (Recommended)

New clients should use structured data:

```python
# Old way (still works)
result = call_tool("get_projects", {})
text = result[0].text
# Parse text manually...

# New way (recommended)
result = call_tool("get_projects", {})
data = result[0].structured_data
projects = data["projects"]
for project in projects:
    print(f"{project['name']}: {project['task_counts']['available']} available tasks")
```

---

## 14. Best Practices Summary

### Schema Design Principles

1. ✅ **Completeness**: Include all relevant OmniFocus data
2. ✅ **Extensibility**: Design for future additions
3. ✅ **Documentation**: Clear descriptions and examples
4. ✅ **Validation**: JSON Schema validation for inputs and outputs
5. ✅ **Consistency**: Uniform patterns across all tools
6. ✅ **Backward Compatibility**: Maintain text responses
7. ✅ **Error Handling**: Structured errors with codes and suggestions
8. ✅ **Discoverability**: Self-documenting API

### API Design Principles

1. ✅ **Higher-Level Functions**: Group related operations
2. ✅ **Sensible Defaults**: Optional parameters with good defaults
3. ✅ **Clear Naming**: verb_noun pattern
4. ✅ **Filtering**: Let users narrow results
5. ✅ **Sorting**: Provide sort options where relevant
6. ✅ **Limiting**: Prevent overwhelming responses
7. ✅ **Structured Output**: Both text and structured data
8. ✅ **Validation**: Check inputs before execution

---

## 15. Conclusion

The current OmniFocus MCP server provides functional basic operations but has significant room for improvement in schema design, data completeness, error handling, and extensibility.

### Key Recommendations

1. **Immediate**: Add output schemas and structured_data to all responses
2. **Short-term**: Enhance existing tools with filters, dates, and complete OmniFocus data
3. **Medium-term**: Add new tools for task management and updates
4. **Long-term**: Consider advanced features like perspectives and batch operations

### Expected Benefits

- Better client integration (structured data)
- More powerful filtering and searching
- Complete access to OmniFocus functionality
- Consistent error handling
- Future-proof extensibility
- Improved developer experience

### Next Steps

1. Review this document with team
2. Prioritize implementation phases
3. Update schema definitions
4. Enhance client code
5. Update tests
6. Update documentation
7. Release with migration guide

---

## Appendix A: Complete Example Tool Definition

This example shows a fully-documented, schema-complete tool:

```python
Tool(
    name="get_projects",
    description="""Get projects from OmniFocus with comprehensive filtering and detailed information.

    **Purpose:**
    Retrieve OmniFocus projects with complete metadata including hierarchy, dates, status,
    task counts, tags, and flags. Supports filtering and sorting for precise queries.

    **What it returns:**
    - Project core data (id, name, note, status)
    - Folder hierarchy and full path
    - All dates (created, modified, due, defer, completed, review)
    - Task statistics (total, completed, available, remaining)
    - Flags (flagged, sequential, completed, dropped)
    - Tags/contexts
    - Metadata about filters applied

    **Use cases:**
    - List all active projects: No parameters needed
    - Review project: {"folder_path": "Personal > Review"}
    - Find overdue: {"status": "active"} then check due dates
    - Project dashboard: {"include_tasks": true, "sort_by": "due_date"}

    **Filtering:**
    - status: Filter by project status (active/on-hold/completed/dropped/all)
    - folder_path: Filter to specific folder or hierarchy
    - include_completed: Include completed projects (default: false)
    - limit: Limit number of results

    **Sorting:**
    - name: Alphabetical by project name (default)
    - due_date: By due date (soonest first, nulls last)
    - modification_date: Recently modified first
    - folder_path: By folder hierarchy

    **Performance:**
    - Fast for <100 projects
    - Use 'limit' parameter for large databases
    - Set include_tasks=false for faster response if task counts not needed

    **Possible Errors:**
    - OMNIFOCUS_NOT_RUNNING: OmniFocus app must be running
    - PERMISSION_DENIED: Grant automation permissions in System Settings
    - APPLESCRIPT_ERROR: Check OmniFocus version compatibility

    **Related Tools:**
    - search_projects: Search projects by query string
    - get_tasks: Get tasks within projects
    - update_project: Modify project properties

    **Version:** 2.0 (enhanced schema with structured output)
    """,
    inputSchema={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["active", "on-hold", "completed", "dropped", "all"],
                "description": "Filter by project status. Default: 'active'",
                "default": "active",
                "examples": ["active", "on-hold"]
            },
            "folder_path": {
                "type": "string",
                "description": "Filter to projects in specific folder. Matches partial paths. Example: 'Work > Projects'",
                "examples": ["Work", "Personal > Review", "Archive"]
            },
            "include_completed": {
                "type": "boolean",
                "description": "Include completed projects in results. Default: false",
                "default": False
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of projects to return. No limit if not specified.",
                "minimum": 1,
                "examples": [10, 50, 100]
            },
            "sort_by": {
                "type": "string",
                "enum": ["name", "due_date", "modification_date", "folder_path"],
                "description": "Sort order for results. Default: 'name'",
                "default": "name"
            },
            "include_tasks": {
                "type": "boolean",
                "description": "Calculate and include task counts. Set false for faster response. Default: true",
                "default": True
            }
        },
        "required": [],
        "additionalProperties": False
    },
    outputSchema={
        "type": "object",
        "properties": {
            "projects": {
                "type": "array",
                "description": "Array of project objects matching the filters",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "string",
                            "description": "Unique OmniFocus project identifier"
                        },
                        "name": {
                            "type": "string",
                            "description": "Project name/title"
                        },
                        "note": {
                            "type": "string",
                            "description": "Project notes (markdown supported)"
                        },
                        "status": {
                            "type": "string",
                            "enum": ["active", "on-hold", "completed", "dropped"],
                            "description": "Current project status"
                        },
                        "folder_path": {
                            "type": ["string", "null"],
                            "description": "Full folder hierarchy path (e.g., 'Work > Projects > Client A'). Null if at root."
                        },
                        "dates": {
                            "type": "object",
                            "description": "All project dates in ISO 8601 format",
                            "properties": {
                                "created": {
                                    "type": ["string", "null"],
                                    "format": "date-time",
                                    "description": "Project creation date"
                                },
                                "modified": {
                                    "type": ["string", "null"],
                                    "format": "date-time",
                                    "description": "Last modification date"
                                },
                                "due": {
                                    "type": ["string", "null"],
                                    "format": "date-time",
                                    "description": "Project due date"
                                },
                                "defer": {
                                    "type": ["string", "null"],
                                    "format": "date-time",
                                    "description": "Project defer/start date"
                                },
                                "completed": {
                                    "type": ["string", "null"],
                                    "format": "date-time",
                                    "description": "Completion date (if completed)"
                                },
                                "next_review": {
                                    "type": ["string", "null"],
                                    "format": "date-time",
                                    "description": "Next scheduled review date"
                                },
                                "last_review": {
                                    "type": ["string", "null"],
                                    "format": "date-time",
                                    "description": "Last review date"
                                }
                            }
                        },
                        "task_counts": {
                            "type": "object",
                            "description": "Task statistics for this project (only if include_tasks=true)",
                            "properties": {
                                "total": {
                                    "type": "integer",
                                    "description": "Total number of tasks"
                                },
                                "completed": {
                                    "type": "integer",
                                    "description": "Number of completed tasks"
                                },
                                "available": {
                                    "type": "integer",
                                    "description": "Number of available (not blocked) tasks"
                                },
                                "remaining": {
                                    "type": "integer",
                                    "description": "Number of incomplete tasks"
                                }
                            },
                            "required": ["total", "completed", "available", "remaining"]
                        },
                        "flags": {
                            "type": "object",
                            "description": "Boolean flags indicating project state",
                            "properties": {
                                "flagged": {
                                    "type": "boolean",
                                    "description": "Project is flagged for attention"
                                },
                                "sequential": {
                                    "type": "boolean",
                                    "description": "Tasks must be completed in order (vs parallel)"
                                },
                                "completed": {
                                    "type": "boolean",
                                    "description": "Project is completed"
                                },
                                "dropped": {
                                    "type": "boolean",
                                    "description": "Project is dropped/abandoned"
                                }
                            },
                            "required": ["flagged", "sequential", "completed", "dropped"]
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of tag names assigned to this project"
                        }
                    },
                    "required": ["id", "name", "status"],
                    "additionalProperties": False
                }
            },
            "count": {
                "type": "integer",
                "description": "Number of projects returned (length of projects array)"
            },
            "filters_applied": {
                "type": "object",
                "description": "Summary of filters that were applied to this query",
                "properties": {
                    "status": {"type": "string"},
                    "folder_path": {"type": ["string", "null"]},
                    "include_completed": {"type": "boolean"},
                    "limit": {"type": ["integer", "null"]},
                    "sort_by": {"type": "string"}
                }
            }
        },
        "required": ["projects", "count", "filters_applied"],
        "additionalProperties": False
    }
)
```

---

**Document Version:** 1.0
**Date:** October 7, 2025
**Author:** Schema Review Team
**Status:** Ready for Review
