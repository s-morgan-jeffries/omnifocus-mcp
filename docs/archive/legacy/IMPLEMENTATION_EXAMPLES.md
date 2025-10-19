# Implementation Examples

This document provides concrete code examples for implementing the schema improvements.

## Table of Contents
1. [Output Schema Implementation](#output-schema-implementation)
2. [Structured Data Responses](#structured-data-responses)
3. [Error Handling](#error-handling)
4. [Enhanced Client Methods](#enhanced-client-methods)
5. [Testing Examples](#testing-examples)

---

## Output Schema Implementation

### Example 1: Adding Output Schema to `get_projects`

**File: `server.py`**

```python
# BEFORE
Tool(
    name="get_projects",
    description="Get all active projects from OmniFocus with their folder hierarchy, names, notes, and status",
    inputSchema={
        "type": "object",
        "properties": {},
        "required": []
    }
)

# AFTER
Tool(
    name="get_projects",
    description="Get all active projects from OmniFocus with their folder hierarchy, names, notes, and status",
    inputSchema={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["active", "on-hold", "completed", "dropped", "all"],
                "description": "Filter projects by status (default: active)",
                "default": "active"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of projects to return",
                "minimum": 1
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
                        "status": {"type": "string"},
                        "folder_path": {"type": ["string", "null"]},
                        "dates": {
                            "type": "object",
                            "properties": {
                                "created": {"type": ["string", "null"], "format": "date-time"},
                                "modified": {"type": ["string", "null"], "format": "date-time"},
                                "due": {"type": ["string", "null"], "format": "date-time"},
                                "defer": {"type": ["string", "null"], "format": "date-time"}
                            }
                        },
                        "task_counts": {
                            "type": "object",
                            "properties": {
                                "total": {"type": "integer"},
                                "completed": {"type": "integer"},
                                "available": {"type": "integer"}
                            }
                        }
                    },
                    "required": ["id", "name", "status"]
                }
            },
            "count": {"type": "integer"}
        },
        "required": ["projects", "count"]
    }
)
```

---

## Structured Data Responses

### Example 2: Returning Structured Data from `get_projects`

**File: `server.py`**

```python
# BEFORE
@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    if name == "get_projects":
        projects = client.get_projects()
        return [TextContent(
            type="text",
            text=f"Found {len(projects)} active projects:\n\n" +
                 "\n\n".join([
                     f"**{p['name']}**\n"
                     f"ID: {p['id']}\n"
                     f"Folder: {p['folderPath'] or '(root)'}\n"
                     f"Status: {p['status']}\n"
                     f"Note: {p['note'][:100] + '...' if len(p['note']) > 100 else p['note']}"
                     for p in projects
                 ])
        )]

# AFTER
@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    if name == "get_projects":
        # Parse arguments
        status_filter = arguments.get("status", "active")
        limit = arguments.get("limit")

        # Get projects (enhanced)
        projects = client.get_projects_enhanced(status=status_filter)

        # Apply limit
        if limit:
            projects = projects[:limit]

        # Build structured data
        structured_data = {
            "projects": projects,
            "count": len(projects),
            "filters_applied": {
                "status": status_filter,
                "limit": limit
            }
        }

        # Build text response (backward compatibility)
        text = f"Found {len(projects)} projects"
        if status_filter != "all":
            text += f" (status: {status_filter})"
        text += ":\n\n"

        text += "\n\n".join([
            format_project_text(p) for p in projects
        ])

        # Return both formats
        return [TextContent(
            type="text",
            text=text,
            structured_data=structured_data
        )]


def format_project_text(project: dict) -> str:
    """Format a single project as text for display."""
    lines = [f"**{project['name']}**"]
    lines.append(f"ID: {project['id']}")
    lines.append(f"Folder: {project.get('folder_path') or '(root)'}")
    lines.append(f"Status: {project['status']}")

    # Add dates if available
    if project.get('dates'):
        dates = project['dates']
        if dates.get('due'):
            lines.append(f"Due: {dates['due']}")

    # Add task counts if available
    if project.get('task_counts'):
        counts = project['task_counts']
        lines.append(f"Tasks: {counts['available']}/{counts['total']} available")

    # Add note (truncated)
    note = project.get('note', '')
    if note:
        note_preview = note[:100] + '...' if len(note) > 100 else note
        lines.append(f"Note: {note_preview}")

    return "\n".join(lines)
```

### Example 3: Structured Response for `add_task`

**File: `server.py`**

```python
# BEFORE
elif name == "add_task":
    project_id = arguments.get("project_id")
    task_name = arguments.get("task_name")
    note = arguments.get("note")

    if not project_id or not task_name:
        return [TextContent(
            type="text",
            text="Error: project_id and task_name are required"
        )]

    success = client.add_task(project_id, task_name, note)
    if success:
        return [TextContent(
            type="text",
            text=f"Successfully added task '{task_name}' to project {project_id}"
        )]
    else:
        return [TextContent(
            type="text",
            text=f"Failed to add task '{task_name}' to project {project_id}"
        )]

# AFTER
elif name == "add_task":
    project_id = arguments.get("project_id")
    task_name = arguments.get("task_name")
    note = arguments.get("note")
    due_date = arguments.get("due_date")
    defer_date = arguments.get("defer_date")
    flagged = arguments.get("flagged", False)
    tags = arguments.get("tags", [])

    # Validation
    if not project_id or not task_name:
        return create_error_response(
            code="MISSING_REQUIRED_FIELD",
            message="project_id and task_name are required",
            details={
                "provided": {
                    "project_id": project_id,
                    "task_name": task_name
                }
            },
            suggestions=[
                "Provide both project_id and task_name parameters",
                "Use get_projects to find available project IDs"
            ]
        )

    # Validate project exists
    is_valid, error_msg = validate_project_exists(project_id)
    if not is_valid:
        return create_error_response(
            code="PROJECT_NOT_FOUND",
            message=error_msg,
            details={"project_id": project_id},
            suggestions=[
                "Use get_projects to list available projects",
                "Check that the project ID is correct"
            ]
        )

    try:
        # Add task with enhanced properties
        result = client.add_task_enhanced(
            project_id=project_id,
            task_name=task_name,
            note=note,
            due_date=due_date,
            defer_date=defer_date,
            flagged=flagged,
            tags=tags
        )

        # result includes task_id and other details
        structured_data = {
            "success": True,
            "task": {
                "id": result["task_id"],
                "name": task_name,
                "project_id": project_id,
                "created_date": result["created_date"]
            },
            "message": f"Successfully added task '{task_name}'"
        }

        text = f"✓ Successfully added task '{task_name}' to project {project_id}\n"
        text += f"Task ID: {result['task_id']}"

        return [TextContent(
            type="text",
            text=text,
            structured_data=structured_data
        )]

    except Exception as e:
        logger.error(f"Error adding task: {e}", exc_info=True)
        return create_error_response(
            code="ADD_TASK_FAILED",
            message=f"Failed to add task: {str(e)}",
            details={
                "project_id": project_id,
                "task_name": task_name,
                "error": str(e)
            },
            suggestions=[
                "Check that OmniFocus is running",
                "Verify you have permission to control OmniFocus",
                "Check the error details for more information"
            ]
        )
```

---

## Error Handling

### Example 4: Error Codes Module

**File: `error_codes.py` (new file)**

```python
"""Error codes and standardized error handling for OmniFocus MCP server."""
from typing import Optional
from mcp.types import TextContent


class ErrorCode:
    """Standard error codes for OmniFocus MCP server."""

    # Project errors
    PROJECT_NOT_FOUND = "PROJECT_NOT_FOUND"
    PROJECT_DROPPED = "PROJECT_DROPPED"
    PROJECT_COMPLETED = "PROJECT_COMPLETED"
    INVALID_PROJECT_STATUS = "INVALID_PROJECT_STATUS"

    # Task errors
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    TASK_ALREADY_COMPLETED = "TASK_ALREADY_COMPLETED"
    INVALID_TASK_ID = "INVALID_TASK_ID"

    # Validation errors
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_DATE_FORMAT = "INVALID_DATE_FORMAT"
    INVALID_PARAMETER_VALUE = "INVALID_PARAMETER_VALUE"
    INVALID_TAG_NAME = "INVALID_TAG_NAME"

    # System errors
    OMNIFOCUS_NOT_RUNNING = "OMNIFOCUS_NOT_RUNNING"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    APPLESCRIPT_ERROR = "APPLESCRIPT_ERROR"
    APPLESCRIPT_TIMEOUT = "APPLESCRIPT_TIMEOUT"

    # Operation errors
    ADD_TASK_FAILED = "ADD_TASK_FAILED"
    UPDATE_PROJECT_FAILED = "UPDATE_PROJECT_FAILED"
    GET_PROJECTS_FAILED = "GET_PROJECTS_FAILED"

    # Generic
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


def create_error_response(
    code: str,
    message: str,
    details: Optional[dict] = None,
    suggestions: Optional[list[str]] = None
) -> list[TextContent]:
    """
    Create a standardized error response.

    Args:
        code: Error code from ErrorCode class
        message: Human-readable error message
        details: Additional context about the error
        suggestions: List of suggestions for fixing the error

    Returns:
        List containing a TextContent with error information
    """
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

    if details:
        text += "\n\nDetails:"
        for key, value in details.items():
            text += f"\n  {key}: {value}"

    if suggestions:
        text += "\n\nSuggestions:"
        for suggestion in suggestions:
            text += f"\n  • {suggestion}"

    return [TextContent(
        type="text",
        text=text,
        structured_data=structured_data
    )]


def validate_project_exists(client, project_id: str) -> tuple[bool, Optional[str]]:
    """
    Validate that a project exists and is accessible.

    Args:
        client: OmniFocusClient instance
        project_id: Project ID to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        projects = client.get_projects()
        project_ids = [p['id'] for p in projects]

        if project_id not in project_ids:
            return False, f"Project with ID '{project_id}' not found"

        return True, None

    except Exception as e:
        return False, f"Error validating project: {str(e)}"


def validate_date_format(date_string: str) -> tuple[bool, Optional[str]]:
    """
    Validate ISO 8601 date format.

    Args:
        date_string: Date string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    from datetime import datetime

    if not date_string:
        return True, None

    try:
        datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return True, None
    except ValueError:
        return False, (
            f"Invalid date format: '{date_string}'. "
            "Expected ISO 8601 format (e.g., '2025-10-15T17:00:00Z')"
        )


def validate_status(status: str) -> tuple[bool, Optional[str]]:
    """
    Validate project status value.

    Args:
        status: Status string to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    valid_statuses = ["active", "on-hold", "completed", "dropped", "all"]

    if status not in valid_statuses:
        return False, (
            f"Invalid status: '{status}'. "
            f"Must be one of: {', '.join(valid_statuses)}"
        )

    return True, None
```

### Example 5: Using Error Handling in Server

**File: `server.py`**

```python
from error_codes import (
    ErrorCode,
    create_error_response,
    validate_project_exists,
    validate_date_format,
    validate_status
)

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls with standardized error handling."""

    try:
        if name == "get_projects":
            # Validate status parameter
            status = arguments.get("status", "active")
            is_valid, error_msg = validate_status(status)
            if not is_valid:
                return create_error_response(
                    code=ErrorCode.INVALID_PARAMETER_VALUE,
                    message=error_msg,
                    details={"parameter": "status", "value": status}
                )

            # ... rest of implementation

        elif name == "add_task":
            # Validate required fields
            project_id = arguments.get("project_id")
            task_name = arguments.get("task_name")

            if not project_id or not task_name:
                return create_error_response(
                    code=ErrorCode.MISSING_REQUIRED_FIELD,
                    message="project_id and task_name are required",
                    suggestions=[
                        "Provide both project_id and task_name",
                        "Use get_projects to find project IDs"
                    ]
                )

            # Validate project exists
            is_valid, error_msg = validate_project_exists(client, project_id)
            if not is_valid:
                return create_error_response(
                    code=ErrorCode.PROJECT_NOT_FOUND,
                    message=error_msg,
                    details={"project_id": project_id},
                    suggestions=[
                        "Use get_projects to list available projects",
                        "Check that OmniFocus is running"
                    ]
                )

            # Validate dates if provided
            due_date = arguments.get("due_date")
            if due_date:
                is_valid, error_msg = validate_date_format(due_date)
                if not is_valid:
                    return create_error_response(
                        code=ErrorCode.INVALID_DATE_FORMAT,
                        message=error_msg,
                        details={"due_date": due_date},
                        suggestions=[
                            "Use ISO 8601 format: '2025-10-15T17:00:00Z'",
                            "Include timezone or use 'Z' for UTC"
                        ]
                    )

            # ... rest of implementation

    except subprocess.CalledProcessError as e:
        # AppleScript execution failed
        return create_error_response(
            code=ErrorCode.APPLESCRIPT_ERROR,
            message="Failed to execute AppleScript",
            details={
                "command": name,
                "error": e.stderr
            },
            suggestions=[
                "Check that OmniFocus is running",
                "Verify automation permissions in System Settings",
                "Try restarting OmniFocus"
            ]
        )

    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error in {name}: {e}", exc_info=True)
        return create_error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"An unexpected error occurred: {str(e)}",
            details={"tool": name, "arguments": arguments}
        )
```

---

## Enhanced Client Methods

### Example 6: Enhanced `get_projects` in Client

**File: `omnifocus_client.py`**

```python
from datetime import datetime
from typing import Any, Optional

def get_projects_enhanced(
    self,
    status: str = "active",
    folder_path: Optional[str] = None,
    include_tasks: bool = True
) -> list[dict[str, Any]]:
    """
    Get projects with enhanced data and filtering.

    Args:
        status: Filter by status (active/on-hold/completed/dropped/all)
        folder_path: Filter to projects in specific folder
        include_tasks: Calculate task counts (slower if false)

    Returns:
        List of project dictionaries with complete data
    """

    # Build AppleScript with conditional logic
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
                    else if projStatus is "{status}" then
                        set includeProject to true
                    end if

                    if not includeProject then error "skip"

                    -- Get dates (with null handling)
                    set creationDate to creation date of proj
                    set modificationDate to modification date of proj

                    set dueDate to missing value
                    try
                        set dueDate to due date of proj
                    end try

                    set deferDate to missing value
                    try
                        set deferDate to defer date of proj
                    end try

                    set completionDate to missing value
                    try
                        set completionDate to completion date of proj
                    end try

                    set nextReviewDate to missing value
                    try
                        set nextReviewDate to next review date of proj
                    end try

                    set lastReviewDate to missing value
                    try
                        set lastReviewDate to last review date of proj
                    end try

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
                    {"if folder_path:" if folder_path else ""}
                    {"if folderPath does not contain \\\"" + folder_path + "\\\" then error \\"skip folder\\"" if folder_path else ""}

                    -- Get task counts (optional for performance)
                    set taskCount to 0
                    set completedCount to 0
                    set availableCount to 0
                    set remainingCount to 0

                    {"if include_tasks:" if include_tasks else ""}
                    {'''
                    try
                        set rootTask to root task of proj
                        set allTasks to flattened tasks of rootTask
                        set taskCount to count of allTasks

                        repeat with t in allTasks
                            if completed of t then
                                set completedCount to completedCount + 1
                            else
                                set remainingCount to remainingCount + 1
                                -- Task is available if not deferred
                                try
                                    set taskDefer to defer date of t
                                    if taskDefer is missing value or taskDefer ≤ (current date) then
                                        set availableCount to availableCount + 1
                                    end if
                                on error
                                    set availableCount to availableCount + 1
                                end try
                            end if
                        end repeat
                    end try
                    ''' if include_tasks else ""}

                    -- Get tags
                    set tagList to ""
                    try
                        set projectTags to tags of proj
                        repeat with t in projectTags
                            if tagList is not "" then set tagList to tagList & ","
                            set tagList to tagList & name of t
                        end repeat
                    end try

                    -- Build JSON object
                    set jsonLine to "{{" & ¬
                        "\\"id\\": \\"" & projId & "\\", " & ¬
                        "\\"name\\": \\"" & my escapeJSON(projName) & "\\", " & ¬
                        "\\"note\\": \\"" & my escapeJSON(projNote) & "\\", " & ¬
                        "\\"status\\": \\"" & projStatus & "\\", " & ¬
                        "\\"folder_path\\": " & my stringToJSON(folderPath) & ", " & ¬
                        "\\"dates\\": {{" & ¬
                        "\\"created\\": " & my dateToJSON(creationDate) & ", " & ¬
                        "\\"modified\\": " & my dateToJSON(modificationDate) & ", " & ¬
                        "\\"due\\": " & my dateToJSON(dueDate) & ", " & ¬
                        "\\"defer\\": " & my dateToJSON(deferDate) & ", " & ¬
                        "\\"completed\\": " & my dateToJSON(completionDate) & ", " & ¬
                        "\\"next_review\\": " & my dateToJSON(nextReviewDate) & ", " & ¬
                        "\\"last_review\\": " & my dateToJSON(lastReviewDate) & ¬
                        "}}, " & ¬
                        "\\"task_counts\\": {{" & ¬
                        "\\"total\\": " & taskCount & ", " & ¬
                        "\\"completed\\": " & completedCount & ", " & ¬
                        "\\"available\\": " & availableCount & ", " & ¬
                        "\\"remaining\\": " & remainingCount & ¬
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

                on error errMsg
                    -- Skip this project (filtered out or error)
                end try
            end repeat
        end tell
    end tell

    return "[" & linefeed & output & linefeed & "]"

    -- Helper: Convert string to JSON (with null handling)
    on stringToJSON(txt)
        if txt is "" or txt is missing value then
            return "null"
        end if
        return "\\"" & my escapeJSON(txt) & "\\""
    end stringToJSON

    -- Helper: Convert date to JSON (ISO 8601)
    on dateToJSON(theDate)
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
    end dateToJSON

    -- Helper: Convert CSV to JSON array
    on jsonArrayFromCSV(csvString)
        if csvString is "" then return ""

        set AppleScript's text item delimiters to ","
        set items to text items of csvString
        set AppleScript's text item delimiters to ""

        set result to ""
        repeat with i in items
            if result is not "" then set result to result & ", "
            set result to result & "\\"" & my escapeJSON(i) & "\\""
        end repeat

        return result
    end jsonArrayFromCSV

    -- Helper: Escape JSON strings
    on escapeJSON(txt)
        if txt is missing value then return ""
        set txt to my replaceText(txt, "\\\\", "\\\\\\\\")
        set txt to my replaceText(txt, "\\"", "\\\\\\"")
        set txt to my replaceText(txt, linefeed, "\\\\n")
        set txt to my replaceText(txt, return, "\\\\r")
        set txt to my replaceText(txt, tab, "\\\\t")
        return txt
    end escapeJSON

    -- Helper: Replace text
    on replaceText(sourceText, oldText, newText)
        if sourceText is missing value then return ""
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
            projects = json.loads(result)
            return projects
        else:
            return []
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error querying OmniFocus: {e.stderr}")
    except json.JSONDecodeError as e:
        raise Exception(f"Error parsing OmniFocus output: {e}")
```

### Example 7: Enhanced `add_task` Method

**File: `omnifocus_client.py`**

```python
def add_task_enhanced(
    self,
    project_id: str,
    task_name: str,
    note: Optional[str] = None,
    due_date: Optional[str] = None,
    defer_date: Optional[str] = None,
    flagged: bool = False,
    estimated_minutes: Optional[int] = None,
    tags: Optional[list[str]] = None
) -> dict[str, Any]:
    """
    Add a task with enhanced properties.

    Args:
        project_id: Project ID to add task to
        task_name: Task name
        note: Optional task note
        due_date: Due date in ISO 8601 format
        defer_date: Defer date in ISO 8601 format
        flagged: Whether to flag the task
        estimated_minutes: Estimated duration
        tags: List of tag names to apply

    Returns:
        Dictionary with task_id and created_date
    """

    # Escape strings for AppleScript
    def escape(text: str) -> str:
        if not text:
            return ""
        text = text.replace("\\", "\\\\")
        text = text.replace('"', '\\"')
        return text

    task_name_escaped = escape(task_name)
    note_escaped = escape(note or "")

    # Convert ISO dates to AppleScript dates
    def iso_to_applescript_date(iso_date: Optional[str]) -> str:
        if not iso_date:
            return "missing value"

        # Parse ISO 8601
        dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))

        # Format for AppleScript
        return (
            f'date \\"{dt.strftime("%A, %B %d, %Y at %I:%M:%S %p")}\\"'
        )

    due_date_script = iso_to_applescript_date(due_date)
    defer_date_script = iso_to_applescript_date(defer_date)

    # Build tags list
    tags_list = ""
    if tags:
        tags_escaped = [escape(tag) for tag in tags]
        tags_list = ", ".join(f'\\"{tag}\\"' for tag in tags_escaped)

    script = f'''
    tell application "OmniFocus"
        tell front document
            try
                -- Find project by ID
                set targetProject to first flattened project whose id is "{project_id}"

                -- Create task with properties
                tell targetProject
                    set newTask to make new task with properties {{¬
                        name:"{task_name_escaped}", ¬
                        note:"{note_escaped}", ¬
                        flagged:{str(flagged).lower()}}}

                    -- Set dates if provided
                    if {due_date_script} is not missing value then
                        set due date of newTask to {due_date_script}
                    end if

                    if {defer_date_script} is not missing value then
                        set defer date of newTask to {defer_date_script}
                    end if

                    -- Set estimated time if provided
                    {f'set estimated minutes of newTask to {estimated_minutes}' if estimated_minutes else ''}

                    -- Apply tags if provided
                    {f'''
                    set tagNames to {{{tags_list}}}
                    repeat with tagName in tagNames
                        try
                            set theTag to first tag whose name is tagName
                            set tags of newTask to tags of newTask & {{theTag}}
                        on error
                            -- Tag doesn't exist, skip it
                        end try
                    end repeat
                    ''' if tags else ''}

                    -- Get task ID and creation date
                    set taskId to id of newTask
                    set taskCreated to creation date of newTask

                    -- Format creation date as ISO 8601
                    set theYear to year of taskCreated as string
                    set theMonth to text -2 thru -1 of ("0" & (month of taskCreated as integer))
                    set theDay to text -2 thru -1 of ("0" & (day of taskCreated as integer))
                    set theHour to text -2 thru -1 of ("0" & (hours of taskCreated))
                    set theMinute to text -2 thru -1 of ("0" & (minutes of taskCreated))
                    set theSecond to text -2 thru -1 of ("0" & (seconds of taskCreated))

                    set isoDate to theYear & "-" & theMonth & "-" & theDay & "T" & ¬
                                   theHour & ":" & theMinute & ":" & theSecond & "Z"

                    return "{{" & ¬
                        "\\"task_id\\": \\"" & taskId & "\\", " & ¬
                        "\\"created_date\\": \\"" & isoDate & "\\"" & ¬
                        "}}"
                end tell

            on error errMsg
                error "Failed to add task: " & errMsg
            end try
        end tell
    end tell
    '''

    try:
        result = run_applescript(script)
        return json.loads(result)
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error adding task: {e.stderr}")
    except json.JSONDecodeError as e:
        raise Exception(f"Error parsing task result: {e}")
```

---

## Testing Examples

### Example 8: Testing Output Schema Compliance

**File: `test_server.py`**

```python
import pytest
from jsonschema import validate, ValidationError

def test_get_projects_output_schema_compliance():
    """Test that get_projects response matches its output schema."""

    # Get the tool definition
    tools = await list_tools()
    get_projects_tool = next(t for t in tools if t.name == "get_projects")

    # Call the tool
    with mock.patch.object(server.client, 'get_projects_enhanced', return_value=[
        {
            "id": "proj-001",
            "name": "Test Project",
            "note": "Test note",
            "status": "active",
            "folder_path": "Work",
            "dates": {
                "created": "2025-01-01T10:00:00Z",
                "modified": "2025-10-01T14:00:00Z",
                "due": "2025-10-15T17:00:00Z",
                "defer": None,
                "completed": None,
                "next_review": None,
                "last_review": None
            },
            "task_counts": {
                "total": 5,
                "completed": 2,
                "available": 3,
                "remaining": 3
            },
            "flags": {
                "flagged": True,
                "sequential": False,
                "completed": False,
                "dropped": False
            },
            "tags": ["urgent", "client"]
        }
    ]):
        result = await call_tool("get_projects", {})

    # Extract structured data
    structured_data = result[0].structured_data

    # Validate against output schema
    try:
        validate(instance=structured_data, schema=get_projects_tool.outputSchema)
    except ValidationError as e:
        pytest.fail(f"Output schema validation failed: {e.message}")

    # Additional assertions
    assert "projects" in structured_data
    assert "count" in structured_data
    assert isinstance(structured_data["projects"], list)
    assert len(structured_data["projects"]) == 1
    assert structured_data["count"] == 1


def test_add_task_output_schema_compliance():
    """Test that add_task response matches its output schema."""

    tools = await list_tools()
    add_task_tool = next(t for t in tools if t.name == "add_task")

    with mock.patch.object(server.client, 'add_task_enhanced', return_value={
        "task_id": "task-001",
        "created_date": "2025-10-07T10:30:00Z"
    }):
        result = await call_tool("add_task", {
            "project_id": "proj-001",
            "task_name": "Test Task"
        })

    structured_data = result[0].structured_data

    try:
        validate(instance=structured_data, schema=add_task_tool.outputSchema)
    except ValidationError as e:
        pytest.fail(f"Output schema validation failed: {e.message}")

    assert structured_data["success"] is True
    assert "task" in structured_data
    assert structured_data["task"]["id"] == "task-001"
```

### Example 9: Testing Error Responses

**File: `test_error_handling.py`**

```python
import pytest
from error_codes import ErrorCode

@pytest.mark.asyncio
async def test_project_not_found_error():
    """Test error response when project doesn't exist."""

    with mock.patch.object(server.client, 'get_projects', return_value=[]):
        result = await call_tool("add_task", {
            "project_id": "invalid-id",
            "task_name": "Test Task"
        })

    # Check structured error
    assert "error" in result[0].structured_data
    error = result[0].structured_data["error"]

    assert error["code"] == ErrorCode.PROJECT_NOT_FOUND
    assert "invalid-id" in error["message"]
    assert "details" in error
    assert "suggestions" in error
    assert len(error["suggestions"]) > 0

    # Check text contains error info
    assert "Error:" in result[0].text
    assert "Suggestions:" in result[0].text


@pytest.mark.asyncio
async def test_invalid_date_format_error():
    """Test error response for invalid date format."""

    with mock.patch.object(server.client, 'get_projects', return_value=[
        {"id": "proj-001", "name": "Test"}
    ]):
        result = await call_tool("add_task", {
            "project_id": "proj-001",
            "task_name": "Test Task",
            "due_date": "not-a-date"
        })

    error = result[0].structured_data["error"]

    assert error["code"] == ErrorCode.INVALID_DATE_FORMAT
    assert "ISO 8601" in error["message"]
    assert "suggestions" in error


@pytest.mark.asyncio
async def test_missing_required_field_error():
    """Test error response for missing required fields."""

    result = await call_tool("add_task", {
        "project_id": "proj-001"
        # missing task_name
    })

    error = result[0].structured_data["error"]

    assert error["code"] == ErrorCode.MISSING_REQUIRED_FIELD
    assert "task_name" in error["message"].lower()
    assert len(error["suggestions"]) > 0
```

### Example 10: Testing Backward Compatibility

**File: `test_backward_compatibility.py`**

```python
@pytest.mark.asyncio
async def test_get_projects_text_format_maintained():
    """Test that text response format is maintained for old clients."""

    with mock.patch.object(server.client, 'get_projects_enhanced', return_value=[
        {
            "id": "proj-001",
            "name": "Test Project",
            "status": "active",
            "folder_path": "Work",
            "note": "Test note",
            # ... other fields
        }
    ]):
        result = await call_tool("get_projects", {})

    # Verify text response exists and has expected format
    assert result[0].type == "text"
    text = result[0].text

    # Check for expected text format
    assert "Found" in text
    assert "projects" in text.lower()
    assert "Test Project" in text
    assert "ID: proj-001" in text
    assert "Folder: Work" in text
    assert "Status: active" in text


@pytest.mark.asyncio
async def test_get_projects_no_arguments_still_works():
    """Test that get_projects works without any arguments (backward compatibility)."""

    with mock.patch.object(server.client, 'get_projects_enhanced', return_value=[]):
        # Call without any arguments (old behavior)
        result = await call_tool("get_projects", {})

    # Should not error
    assert len(result) == 1
    assert result[0].type == "text"
    assert "structured_data" in result[0].__dict__


@pytest.mark.asyncio
async def test_add_task_basic_usage_still_works():
    """Test that basic add_task usage (without new fields) still works."""

    with mock.patch.object(server.client, 'add_task_enhanced', return_value={
        "task_id": "task-001",
        "created_date": "2025-10-07T10:30:00Z"
    }):
        # Call with only original required fields
        result = await call_tool("add_task", {
            "project_id": "proj-001",
            "task_name": "Test Task",
            "note": "Optional note"
        })

    # Should work as before
    assert result[0].type == "text"
    assert "Successfully added" in result[0].text
```

---

## Summary

These examples demonstrate:

1. **Output Schemas**: Complete JSON Schema definitions
2. **Structured Responses**: Both text and structured_data
3. **Error Handling**: Standardized error codes and responses
4. **Enhanced Client**: AppleScript to capture all OmniFocus data
5. **Testing**: Validation, error checking, backward compatibility

All changes are **backward compatible** and follow **MCP 2025 best practices**.

---

**Next Steps:**

1. Review these examples
2. Implement Phase 1 (output schemas)
3. Test with existing clients
4. Roll out remaining phases
5. Update documentation

**Files to Create/Modify:**
- `error_codes.py` (new)
- `server.py` (enhance)
- `omnifocus_client.py` (enhance)
- `test_*.py` (update)
