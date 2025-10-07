"""Client for interacting with OmniFocus app."""
import subprocess
import json
import os
from typing import Any, Optional


def run_applescript(script: str) -> str:
    """Execute AppleScript and return the result."""
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


class DatabaseSafetyError(Exception):
    """Raised when database safety checks fail."""
    pass


class OmniFocusClient:
    """Client for OmniFocus app operations using AppleScript.

    SAFETY: For integration testing with real OmniFocus, set environment variables:
        OMNIFOCUS_TEST_MODE=true
        OMNIFOCUS_TEST_DATABASE=OmniFocus-TEST.ofocus

    Without these, destructive operations will be blocked to protect your production database.
    """

    # Allowed test database names
    ALLOWED_TEST_DATABASES = {
        "OmniFocus-TEST.ofocus",
        "OmniFocus-Dev.ofocus",
        "OmniFocus-Staging.ofocus",
    }

    # Operations that modify data (require safety checks)
    DESTRUCTIVE_OPERATIONS = {
        'add_task', 'add_note', 'complete_task', 'update_task',
        'create_inbox_task', 'add_tag_to_task', 'create_project',
        'delete_task', 'delete_project', 'move_task', 'drop_task',
        'create_folder', 'set_parent_task', 'set_review_interval',
        'mark_project_reviewed', 'set_estimated_minutes'
    }

    def __init__(self, enable_safety_checks: bool = True):
        """Initialize the OmniFocus client.

        Args:
            enable_safety_checks: If True (default), verify database before destructive operations.
                                 Set to False only for unit tests with mocked AppleScript.
        """
        self._safety_checks_enabled = enable_safety_checks
        self._test_mode = os.environ.get('OMNIFOCUS_TEST_MODE', '').lower() == 'true'
        self._test_database = os.environ.get('OMNIFOCUS_TEST_DATABASE', '')

        # If safety checks are enabled and we're in test mode, verify configuration
        if self._safety_checks_enabled and self._test_mode:
            if not self._test_database:
                raise DatabaseSafetyError(
                    "OMNIFOCUS_TEST_MODE is enabled but OMNIFOCUS_TEST_DATABASE is not set. "
                    "Set OMNIFOCUS_TEST_DATABASE to one of: " +
                    ", ".join(self.ALLOWED_TEST_DATABASES)
                )
            if self._test_database not in self.ALLOWED_TEST_DATABASES:
                raise DatabaseSafetyError(
                    f"Database '{self._test_database}' is not in the allowed test databases list. "
                    "Allowed: " + ", ".join(self.ALLOWED_TEST_DATABASES)
                )

    def _verify_database_safety(self, operation_name: str) -> None:
        """Verify we're not accidentally modifying production database.

        Args:
            operation_name: Name of the operation being performed

        Raises:
            DatabaseSafetyError: If safety checks fail
        """
        # Skip if safety checks are disabled (for unit tests)
        if not self._safety_checks_enabled:
            return

        # Read-only operations are always safe
        if operation_name not in self.DESTRUCTIVE_OPERATIONS:
            return

        # For destructive operations, test mode must be enabled
        if not self._test_mode:
            raise DatabaseSafetyError(
                f"Cannot perform destructive operation '{operation_name}' without test mode. "
                "Set OMNIFOCUS_TEST_MODE=true to enable testing with OmniFocus. "
                "WARNING: Only use with a test database!"
            )

        # Verify we're using the correct test database via AppleScript
        try:
            script = '''
            tell application "OmniFocus"
                tell front document
                    return name of it
                end tell
            end tell
            '''
            result = run_applescript(script)

            # Check if the database name matches what we expect
            if self._test_database not in result:
                raise DatabaseSafetyError(
                    f"Database safety check FAILED! Expected '{self._test_database}' but got '{result}'. "
                    "This could mean you're about to modify your PRODUCTION database! "
                    "Operation blocked for safety."
                )
        except subprocess.CalledProcessError as e:
            raise DatabaseSafetyError(
                f"Could not verify database name before operation '{operation_name}'. "
                f"Blocking operation for safety. Error: {e.stderr}"
            )

    def _escape_applescript_string(self, text: str) -> str:
        """Escape quotes and backslashes for AppleScript strings."""
        if not text:
            return ""
        text = text.replace("\\", "\\\\")
        text = text.replace('"', '\\"')
        return text

    def get_projects(self) -> list[dict[str, Any]]:
        """Get projects with their folder/hierarchy information using AppleScript."""
        script = '''
        use AppleScript version "2.4"
        use scripting additions
        use framework "Foundation"

        set output to ""

        tell application "OmniFocus"
            tell front document
                set allProjects to flattened projects

                repeat with proj in allProjects
                    try
                        set projId to id of proj
                        set projName to name of proj
                        set projNote to note of proj
                        set projStatus to status of proj as text

                        -- Skip dropped projects
                        if projStatus is "dropped" then
                            error "skip dropped project"
                        end if

                        -- Get folder path
                        set folderPath to ""
                        try
                            set parentFolder to container of proj
                            if class of parentFolder is folder then
                                set folderPath to name of parentFolder
                                -- Walk up the folder hierarchy
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

                        -- Build JSON manually (AppleScript doesn't have native JSON)
                        set jsonLine to "{" & ¬
                            "\\"id\\": \\"" & projId & "\\", " & ¬
                            "\\"name\\": \\"" & my escapeJSON(projName) & "\\", " & ¬
                            "\\"note\\": \\"" & my escapeJSON(projNote) & "\\", " & ¬
                            "\\"status\\": \\"" & projStatus & "\\", " & ¬
                            "\\"folderPath\\": \\"" & my escapeJSON(folderPath) & "\\"" & ¬
                            "}"

                        if output is not "" then
                            set output to output & "," & linefeed
                        end if
                        set output to output & jsonLine
                    end try
                end repeat
            end tell
        end tell

        return "[" & linefeed & output & linefeed & "]"

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
                raise Exception("No output from OmniFocus AppleScript")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error querying OmniFocus: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing OmniFocus output: {e}")

    def create_project(
        self,
        name: str,
        note: Optional[str] = None,
        folder_path: Optional[str] = None,
        sequential: bool = False
    ) -> str:
        """Create a new project in OmniFocus.

        Args:
            name: The name of the project
            note: Optional note/description for the project
            folder_path: Optional folder path (e.g., "Work > Clients") - folder must exist
            sequential: If True, tasks must be completed in order (default: False, parallel)

        Returns:
            str: The ID of the created project

        Raises:
            Exception: If project creation fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('create_project')

        # Escape strings for AppleScript
        name_escaped = self._escape_applescript_string(name)
        note_escaped = self._escape_applescript_string(note or "")

        # Build properties
        properties = [f'name:"{name_escaped}"']
        if note:
            properties.append(f'note:"{note_escaped}"')
        if sequential:
            properties.append('sequential:true')
        else:
            properties.append('sequential:false')

        properties_str = ", ".join(properties)

        # Build script with optional folder placement
        if folder_path:
            # Parse folder path and find folder
            folder_parts = [part.strip() for part in folder_path.split('>')]
            folder_escaped = self._escape_applescript_string(folder_parts[-1])

            # Build folder finding logic
            if len(folder_parts) == 1:
                # Top-level folder
                folder_finder = f'''
                set targetFolder to first folder whose name is "{folder_escaped}"
                '''
            else:
                # Nested folder - need to walk the hierarchy
                folder_finder = f'''
                -- Find folder by walking hierarchy
                set folderNames to {{{', '.join(f'"{self._escape_applescript_string(p)}"' for p in folder_parts)}}}
                set targetFolder to missing value
                set currentContainers to folders of front document

                repeat with folderName in folderNames
                    repeat with possibleFolder in currentContainers
                        if name of possibleFolder is folderName then
                            set targetFolder to possibleFolder
                            set currentContainers to folders of targetFolder
                            exit repeat
                        end if
                    end repeat
                end repeat

                if targetFolder is missing value then
                    error "Folder path not found: {folder_path}"
                end if
                '''

            script = f'''
            tell application "OmniFocus"
                tell front document
                    {folder_finder}
                    set newProject to make new project at end of projects of targetFolder with properties {{{properties_str}}}
                    return id of newProject
                end tell
            end tell
            '''
        else:
            # Create at root level
            script = f'''
            tell application "OmniFocus"
                tell front document
                    set newProject to make new project with properties {{{properties_str}}}
                    return id of newProject
                end tell
            end tell
            '''

        try:
            result = run_applescript(script)
            if result and result.strip():
                return result.strip()
            else:
                raise Exception("No project ID returned from OmniFocus")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error creating project: {e.stderr}")

    def add_task(
        self,
        project_id: str,
        task_name: str,
        note: Optional[str] = None,
        due_date: Optional[str] = None,
        defer_date: Optional[str] = None,
        flagged: bool = False,
        tags: Optional[list[str]] = None
    ) -> bool:
        """Add a task to a specific project using AppleScript.

        Args:
            project_id: The ID of the project to add the task to
            task_name: The name/title of the task
            note: Optional note/description for the task
            due_date: Due date in ISO 8601 format (e.g., "2025-10-15" or "2025-10-15T17:00:00")
            defer_date: Defer date in ISO 8601 format (when task becomes available)
            flagged: Whether to flag the task
            tags: List of tag names to assign to the task

        Returns:
            bool: True if task was created successfully
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('add_task')

        # Escape quotes and backslashes for AppleScript
        task_name_escaped = self._escape_applescript_string(task_name)
        note_escaped = self._escape_applescript_string(note or "")

        # Build properties dictionary
        properties = [f'name:"{task_name_escaped}"']
        if note:
            properties.append(f'note:"{note_escaped}"')
        if flagged:
            properties.append('flagged:true')

        # Build script with optional date settings
        date_commands = []
        if due_date:
            # Convert ISO date to AppleScript date
            date_commands.append(f'set due date of newTask to date "{self._iso_to_applescript_date(due_date)}"')
        if defer_date:
            date_commands.append(f'set defer date of newTask to date "{self._iso_to_applescript_date(defer_date)}"')

        # Build tag assignment commands
        tag_commands = []
        if tags:
            for tag in tags:
                tag_escaped = self._escape_applescript_string(tag)
                tag_commands.append(f'''
                    try
                        set tagObj to first flattened tag whose name is "{tag_escaped}"
                        add tagObj to tags of newTask
                    on error
                        -- Tag doesn't exist, skip it
                    end try''')

        properties_str = ", ".join(properties)
        date_commands_str = "\n                    ".join(date_commands)
        tag_commands_str = "\n                    ".join(tag_commands)

        script = f'''
        tell application "OmniFocus"
            tell front document
                try
                    -- Find project by ID
                    set targetProject to first flattened project whose id is "{project_id}"

                    -- Create new task in the project
                    tell targetProject
                        set newTask to make new task with properties {{{properties_str}}}
                    end tell

                    -- Set dates if provided
                    {date_commands_str if date_commands else ""}

                    -- Add tags if provided
                    {tag_commands_str if tag_commands else ""}

                    return "true"
                on error errMsg
                    return "false: " & errMsg
                end try
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            if result.startswith("false:"):
                raise Exception(f"Error adding task: {result}")
            return result.strip() == "true"
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error adding task: {e.stderr}")

    def _iso_to_applescript_date(self, iso_date: str) -> str:
        """Convert ISO 8601 date to AppleScript date format.

        Args:
            iso_date: Date in ISO 8601 format (e.g., "2025-10-15" or "2025-10-15T17:00:00")

        Returns:
            str: Date in AppleScript format (e.g., "October 15, 2025 5:00:00 PM")
        """
        from datetime import datetime

        # Parse ISO date (handle both with and without time)
        try:
            if 'T' in iso_date:
                dt = datetime.fromisoformat(iso_date.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(iso_date + 'T00:00:00')
        except ValueError as e:
            raise ValueError(f"Invalid date format '{iso_date}'. Expected ISO 8601 format like '2025-10-15' or '2025-10-15T17:00:00'") from e

        # Format for AppleScript: "October 15, 2025 5:00:00 PM"
        return dt.strftime("%B %d, %Y %I:%M:%S %p")

    def add_note(self, project_id: str, note_text: str) -> bool:
        """Append a note to a project's existing notes using AppleScript."""
        # SAFETY: Verify database before modifying
        self._verify_database_safety('add_note')

        # Escape quotes and backslashes for AppleScript
        note_escaped = self._escape_applescript_string(note_text)

        script = f'''
        tell application "OmniFocus"
            tell front document
                try
                    -- Find project by ID
                    set targetProject to first flattened project whose id is "{project_id}"

                    -- Get current note and append new note
                    set currentNote to note of targetProject
                    if currentNote is "" then
                        set note of targetProject to "{note_escaped}"
                    else
                        set note of targetProject to currentNote & linefeed & linefeed & "{note_escaped}"
                    end if

                    return "true"
                on error errMsg
                    return "false: " & errMsg
                end try
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            if result.startswith("false:"):
                raise Exception(f"Error adding note: {result}")
            return result.strip() == "true"
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error adding note: {e.stderr}")

    def get_note(self, item_id: str, item_type: str = "project") -> str:
        """Get the full note content from a project or task.

        Args:
            item_id: The ID of the project or task
            item_type: Either "project" or "task" (default: "project")

        Returns:
            The full note content as a string (empty string if no note exists)

        Raises:
            ValueError: If item_type is not "project" or "task"
            Exception: If the item is not found or AppleScript fails
        """
        if item_type not in ["project", "task"]:
            raise ValueError(f"item_type must be 'project' or 'task', got: {item_type}")

        if item_type == "project":
            script = f'''
            tell application "OmniFocus"
                tell front document
                    try
                        set targetProject to first flattened project whose id is "{item_id}"
                        set noteContent to note of targetProject
                        if noteContent is missing value then
                            return ""
                        else
                            return noteContent
                        end if
                    on error errMsg
                        error "Project not found: " & errMsg
                    end try
                end tell
            end tell
            '''
        else:  # task
            script = f'''
            tell application "OmniFocus"
                tell front document
                    try
                        set targetTask to first flattened task whose id is "{item_id}"
                        set noteContent to note of targetTask
                        if noteContent is missing value then
                            return ""
                        else
                            return noteContent
                        end if
                    on error errMsg
                        error "Task not found: " & errMsg
                    end try
                end tell
            end tell
            '''

        try:
            result = run_applescript(script)
            return result.strip()
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error getting note: {e.stderr}")

    def search_projects(self, query: str) -> list[dict[str, Any]]:
        """Search projects by name or note content."""
        all_projects = self.get_projects()
        query_lower = query.lower()

        matches = []
        for project in all_projects:
            if (query_lower in project['name'].lower() or
                query_lower in project['note'].lower() or
                query_lower in project['folderPath'].lower()):
                matches.append(project)

        return matches

    def get_tasks(
        self,
        project_id: Optional[str] = None,
        include_completed: bool = False,
        flagged_only: bool = False,
        available_only: bool = False,
        overdue: bool = False,
        tag_filter: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """Get tasks from OmniFocus with optional filtering.

        Args:
            project_id: Optional project ID to filter tasks. If None, returns all tasks.
            include_completed: Whether to include completed tasks (default: False)
            flagged_only: Only return flagged tasks (default: False)
            available_only: Only return available tasks (not blocked or deferred) (default: False)
            overdue: Only return overdue tasks (default: False)
            tag_filter: List of tag names to filter by (AND logic - task must have all tags)

        Returns:
            list: List of task dictionaries with id, name, note, status, project info, dates, flagged status, and tags
        """
        # Build project filter
        if project_id:
            project_filter = f'whose id is "{project_id}"'
            task_source = f'tasks of (first flattened project {project_filter})'
        else:
            task_source = 'flattened tasks'

        # Build completion filter
        completion_check = "" if include_completed else """
                        -- Skip completed tasks
                        if completed of t then
                            error "skip completed task"
                        end if"""

        # Build flagged filter
        flagged_check = "" if not flagged_only else """
                        -- Skip non-flagged tasks
                        if not flagged of t then
                            error "skip non-flagged task"
                        end if"""

        # Build available filter (not dropped, not blocked, not deferred)
        available_check = "" if not available_only else """
                        -- Skip unavailable tasks
                        if dropped of t then
                            error "skip unavailable task"
                        end if
                        if blocked of t then
                            error "skip unavailable task"
                        end if
                        -- Check if deferred
                        try
                            set taskDeferDate to defer date of t
                            if taskDeferDate is not missing value then
                                if taskDeferDate > (current date) then
                                    error "skip unavailable task"
                                end if
                            end if
                        end try"""

        # Build overdue filter
        overdue_check = "" if not overdue else """
                        -- Skip non-overdue tasks
                        try
                            set taskDueDate to due date of t
                            if taskDueDate is missing value then
                                error "skip non-overdue task"
                            else if taskDueDate >= (current date) then
                                error "skip non-overdue task"
                            end if
                        on error
                            error "skip non-overdue task"
                        end try"""

        # Build tag filter
        tag_check = ""
        if tag_filter and len(tag_filter) > 0:
            # Build AppleScript to check for all required tags
            tag_checks = []
            for tag_name in tag_filter:
                tag_escaped = tag_name.replace('"', '\\"')
                tag_checks.append(f'''
                        -- Check for tag: {tag_escaped}
                        set hasTag to false
                        repeat with tg in tags of t
                            if name of tg is "{tag_escaped}" then
                                set hasTag to true
                                exit repeat
                            end if
                        end repeat
                        if not hasTag then
                            error "skip task without required tag"
                        end if''')
            tag_check = "".join(tag_checks)

        script = f'''
        use AppleScript version "2.4"
        use scripting additions

        set output to ""

        tell application "OmniFocus"
            tell front document
                set allTasks to {task_source}

                repeat with t in allTasks
                    try
                        set taskId to id of t
                        set taskName to name of t
                        set taskNote to note of t
                        set taskCompleted to completed of t
                        set taskFlagged to flagged of t

                        {completion_check}
                        {flagged_check}
                        {available_check}
                        {overdue_check}
                        {tag_check}

                        -- Get project info
                        set projectId to ""
                        set projectName to ""
                        try
                            set parentProj to containing project of t
                            if parentProj is not missing value then
                                set projectId to id of parentProj
                                set projectName to name of parentProj
                            end if
                        end try

                        -- Get dates
                        set dueDate to ""
                        try
                            set dueDateObj to due date of t
                            if dueDateObj is not missing value then
                                set dueDate to dueDateObj as «class isot» as string
                            end if
                        end try

                        set deferDate to ""
                        try
                            set deferDateObj to defer date of t
                            if deferDateObj is not missing value then
                                set deferDate to deferDateObj as «class isot» as string
                            end if
                        end try

                        set completionDate to ""
                        try
                            set completionDateObj to completion date of t
                            if completionDateObj is not missing value then
                                set completionDate to completionDateObj as «class isot» as string
                            end if
                        end try

                        -- Get tags
                        set tagsList to ""
                        try
                            set taskTags to tags of t
                            set tagNames to {{}}
                            repeat with tg in taskTags
                                set end of tagNames to name of tg
                            end repeat
                            set AppleScript's text item delimiters to ", "
                            set tagsList to tagNames as text
                            set AppleScript's text item delimiters to ""
                        end try

                        -- Build JSON manually
                        set jsonLine to "{{" & ¬
                            "\\"id\\": \\"" & taskId & "\\", " & ¬
                            "\\"name\\": \\"" & my escapeJSON(taskName) & "\\", " & ¬
                            "\\"note\\": \\"" & my escapeJSON(taskNote) & "\\", " & ¬
                            "\\"completed\\": " & (taskCompleted as text) & ", " & ¬
                            "\\"flagged\\": " & (taskFlagged as text) & ", " & ¬
                            "\\"projectId\\": \\"" & projectId & "\\", " & ¬
                            "\\"projectName\\": \\"" & my escapeJSON(projectName) & "\\", " & ¬
                            "\\"dueDate\\": \\"" & dueDate & "\\", " & ¬
                            "\\"deferDate\\": \\"" & deferDate & "\\", " & ¬
                            "\\"completionDate\\": \\"" & completionDate & "\\", " & ¬
                            "\\"tags\\": \\"" & my escapeJSON(tagsList) & "\\"" & ¬
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
                raise Exception("No output from OmniFocus AppleScript")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error querying OmniFocus tasks: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing OmniFocus task output: {e}")

    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed.

        Args:
            task_id: The ID of the task to complete

        Returns:
            bool: True if successful

        Raises:
            ValueError: If task_id is empty
            Exception: If the task cannot be completed
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('complete_task')

        if not task_id:
            raise ValueError("task_id is required")

        script = f'''
        tell application "OmniFocus"
            tell front document
                set theTask to first flattened task whose id is "{task_id}"
                set completed of theTask to true
                return "true"
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            if result.strip() == "true":
                return True
            else:
                raise Exception(f"Error completing task: {result}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error completing task: {e.stderr}")

    def update_task(
        self,
        task_id: str,
        name: Optional[str] = None,
        note: Optional[str] = None,
        due_date: Optional[str] = None,
        defer_date: Optional[str] = None,
        flagged: Optional[bool] = None
    ) -> bool:
        """Update properties of an existing task.

        Args:
            task_id: The ID of the task to update
            name: New task name (optional)
            note: New task note (optional)
            due_date: New due date in ISO 8601 format, or None to clear (optional)
            defer_date: New defer date in ISO 8601 format, or None to clear (optional)
            flagged: New flagged status (optional)

        Returns:
            bool: True if successful

        Raises:
            ValueError: If task_id is empty or no fields are provided
            Exception: If the task cannot be updated
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('update_task')

        if not task_id:
            raise ValueError("task_id is required")

        # Check if at least one field is provided
        if all(v is None for v in [name, note, due_date, flagged]) and defer_date is None:
            raise ValueError("At least one field must be provided to update")

        # Build properties to update
        properties = []

        if name is not None:
            escaped_name = self._escape_applescript_string(name)
            properties.append(f'name:"{escaped_name}"')

        if note is not None:
            escaped_note = self._escape_applescript_string(note)
            properties.append(f'note:"{escaped_note}"')

        if flagged is not None:
            properties.append(f'flagged:{str(flagged).lower()}')

        # Build date update commands
        date_commands = []

        if due_date is not None:
            if due_date == "":
                date_commands.append("set due date of theTask to missing value")
            else:
                as_date = self._iso_to_applescript_date(due_date)
                date_commands.append(f'set due date of theTask to date "{as_date}"')

        if defer_date is not None:
            if defer_date == "":
                date_commands.append("set defer date of theTask to missing value")
            else:
                as_date = self._iso_to_applescript_date(defer_date)
                date_commands.append(f'set defer date of theTask to date "{as_date}"')

        # Build properties string
        props_str = ", ".join(properties) if properties else ""
        date_cmds_str = "\n                ".join(date_commands) if date_commands else ""

        script = f'''
        tell application "OmniFocus"
            tell front document
                set theTask to first flattened task whose id is "{task_id}"
                '''

        if props_str:
            script += f'\n                set properties of theTask to {{{props_str}}}'

        if date_cmds_str:
            script += f'\n                {date_cmds_str}'

        script += '''
                return "true"
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            if result.strip() == "true":
                return True
            else:
                raise Exception(f"Error updating task: {result}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error updating task: {e.stderr}")

    def get_inbox_tasks(self) -> list[dict[str, Any]]:
        """Get all tasks from the inbox.

        Returns:
            list: List of inbox task dictionaries with id, name, note, dates, flagged status, and tags
        """
        script = '''
        use AppleScript version "2.4"
        use scripting additions

        set output to ""

        tell application "OmniFocus"
            tell front document
                set allInboxTasks to inbox tasks

                repeat with t in allInboxTasks
                    try
                        set taskId to id of t
                        set taskName to name of t
                        set taskNote to note of t
                        set taskCompleted to completed of t
                        set taskFlagged to flagged of t

                        -- Get dates
                        set dueDate to ""
                        try
                            set dueDateObj to due date of t
                            if dueDateObj is not missing value then
                                set dueDate to dueDateObj as «class isot» as string
                            end if
                        end try

                        set deferDate to ""
                        try
                            set deferDateObj to defer date of t
                            if deferDateObj is not missing value then
                                set deferDate to deferDateObj as «class isot» as string
                            end if
                        end try

                        -- Get tags
                        set tagsList to ""
                        try
                            set taskTags to tags of t
                            set tagNames to {}
                            repeat with tg in taskTags
                                set end of tagNames to name of tg
                            end repeat
                            set AppleScript's text item delimiters to ", "
                            set tagsList to tagNames as text
                            set AppleScript's text item delimiters to ""
                        end try

                        -- Build JSON manually
                        set jsonLine to "{" & ¬
                            "\\"id\\": \\"" & taskId & "\\", " & ¬
                            "\\"name\\": \\"" & my escapeJSON(taskName) & "\\", " & ¬
                            "\\"note\\": \\"" & my escapeJSON(taskNote) & "\\", " & ¬
                            "\\"completed\\": " & (taskCompleted as text) & ", " & ¬
                            "\\"flagged\\": " & (taskFlagged as text) & ", " & ¬
                            "\\"dueDate\\": \\"" & dueDate & "\\", " & ¬
                            "\\"deferDate\\": \\"" & deferDate & "\\", " & ¬
                            "\\"tags\\": \\"" & my escapeJSON(tagsList) & "\\"" & ¬
                            "}"

                        if output is not "" then
                            set output to output & "," & linefeed
                        end if
                        set output to output & jsonLine
                    end try
                end repeat
            end tell
        end tell

        return "[" & linefeed & output & linefeed & "]"

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
            raise Exception(f"Error querying inbox tasks: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing inbox task output: {e}")

    def create_inbox_task(
        self,
        task_name: str,
        note: Optional[str] = None,
        due_date: Optional[str] = None,
        flagged: bool = False
    ) -> bool:
        """Create a new task in the inbox.

        Args:
            task_name: The name of the task
            note: Optional note for the task
            due_date: Optional due date in ISO 8601 format
            flagged: Whether to flag the task (default: False)

        Returns:
            bool: True if successful

        Raises:
            ValueError: If task_name is empty
            Exception: If the task cannot be created
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('create_inbox_task')

        if not task_name:
            raise ValueError("task_name is required")

        # Build properties
        task_name_escaped = self._escape_applescript_string(task_name)
        properties = [f'name:"{task_name_escaped}"']

        if note:
            note_escaped = self._escape_applescript_string(note)
            properties.append(f'note:"{note_escaped}"')

        if flagged:
            properties.append('flagged:true')

        properties_str = ", ".join(properties)

        # Build date command
        date_command = ""
        if due_date:
            as_date = self._iso_to_applescript_date(due_date)
            date_command = f'set due date of newTask to date "{as_date}"'

        script = f'''
        tell application "OmniFocus"
            tell front document
                tell inbox
                    set newTask to make new task with properties {{{properties_str}}}
                end tell
                {date_command if date_command else ""}
                return "true"
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            if result.strip() == "true":
                return True
            else:
                raise Exception(f"Error creating inbox task: {result}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error creating inbox task: {e.stderr}")

    def get_tags(self) -> list[dict[str, Any]]:
        """Get all tags from OmniFocus.

        Returns:
            list: List of tag dictionaries with id, name, and status
        """
        script = '''
        use AppleScript version "2.4"
        use scripting additions

        set output to ""

        tell application "OmniFocus"
            tell front document
                set allTags to flattened tags

                repeat with t in allTags
                    try
                        set tagId to id of t
                        set tagName to name of t
                        set tagStatus to "active"

                        -- Build JSON manually
                        set jsonLine to "{" & ¬
                            "\\"id\\": \\"" & tagId & "\\", " & ¬
                            "\\"name\\": \\"" & my escapeJSON(tagName) & "\\", " & ¬
                            "\\"status\\": \\"" & tagStatus & "\\"" & ¬
                            "}"

                        if output is not "" then
                            set output to output & "," & linefeed
                        end if
                        set output to output & jsonLine
                    end try
                end repeat
            end tell
        end tell

        return "[" & linefeed & output & linefeed & "]"

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
            raise Exception(f"Error querying tags: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing tags output: {e}")

    def add_tag_to_task(self, task_id: str, tag_name: str) -> bool:
        """Add an existing tag to a task.

        Args:
            task_id: The ID of the task
            tag_name: The name of the tag to add

        Returns:
            bool: True if successful

        Raises:
            ValueError: If task_id or tag_name is empty
            Exception: If the tag cannot be added
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('add_tag_to_task')

        if not task_id:
            raise ValueError("task_id is required")
        if not tag_name:
            raise ValueError("tag_name is required")

        tag_escaped = self._escape_applescript_string(tag_name)

        script = f'''
        tell application "OmniFocus"
            tell front document
                set theTask to first flattened task whose id is "{task_id}"
                set tagObj to first flattened tag whose name is "{tag_escaped}"
                add tagObj to tags of theTask
                return "true"
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            if result.strip() == "true":
                return True
            else:
                raise Exception(f"Error adding tag to task: {result}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error adding tag to task: {e.stderr}")

    def delete_task(self, task_id: str) -> bool:
        """Delete a task from OmniFocus.

        Args:
            task_id: The ID of the task to delete

        Returns:
            True if deletion was successful

        Raises:
            Exception: If task not found or deletion fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('delete_task')

        script = f'''
        tell application "OmniFocus"
            tell front document
                try
                    set theTask to first flattened task whose id is "{task_id}"
                    delete theTask
                    return "true"
                on error
                    return "false"
                end try
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            if result.strip() == "true":
                return True
            else:
                raise Exception(f"Task not found: {task_id}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error deleting task: {e.stderr}")

    def delete_project(self, project_id: str) -> bool:
        """Delete a project from OmniFocus.

        Args:
            project_id: The ID of the project to delete

        Returns:
            True if deletion was successful

        Raises:
            Exception: If project not found or deletion fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('delete_project')

        script = f'''
        tell application "OmniFocus"
            tell front document
                try
                    set theProject to first flattened project whose id is "{project_id}"
                    delete theProject
                    return "true"
                on error
                    return "false"
                end try
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            if result.strip() == "true":
                return True
            else:
                raise Exception(f"Project not found: {project_id}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error deleting project: {e.stderr}")

    def move_task(self, task_id: str, project_id: Optional[str]) -> bool:
        """Move a task to a different project or to inbox.

        Args:
            task_id: The ID of the task to move
            project_id: The ID of the destination project, or None for inbox

        Returns:
            True if move was successful

        Raises:
            Exception: If task or project not found, or move fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('move_task')

        if project_id is None:
            # Move to inbox
            script = f'''
            tell application "OmniFocus"
                tell front document
                    try
                        set theTask to first flattened task whose id is "{task_id}"
                        move theTask to end of tasks of front document
                        return "true"
                    on error errMsg
                        return "false: " & errMsg
                    end try
                end tell
            end tell
            '''
        else:
            # Move to project
            script = f'''
            tell application "OmniFocus"
                tell front document
                    try
                        set theTask to first flattened task whose id is "{task_id}"
                        set theProject to first flattened project whose id is "{project_id}"
                        move theTask to end of tasks of theProject
                        return "true"
                    on error errMsg
                        return "false: " & errMsg
                    end try
                end tell
            end tell
            '''

        try:
            result = run_applescript(script)
            if result.strip() == "true":
                return True
            else:
                raise Exception(f"Error moving task: {result}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error moving task: {e.stderr}")

    def get_folders(self) -> list[dict]:
        """Get all folders from OmniFocus.

        Returns:
            List of folder dictionaries with id, name, and path
        """
        script = '''
        tell application "OmniFocus"
            tell front document
                set folderList to {}

                -- Helper function to build folder path
                on getFolderPath(f)
                    set pathParts to {name of f}
                    set currentFolder to f
                    repeat
                        try
                            set parentFolder to container of currentFolder
                            if class of parentFolder is folder then
                                set pathParts to {name of parentFolder} & pathParts
                                set currentFolder to parentFolder
                            else
                                exit repeat
                            end if
                        on error
                            exit repeat
                        end try
                    end repeat

                    set AppleScript's text item delimiters to " > "
                    set folderPath to pathParts as text
                    set AppleScript's text item delimiters to ""
                    return folderPath
                end getFolderPath

                -- Get all folders recursively
                on processFolders(folderContainer, folderResults)
                    repeat with f in folders of folderContainer
                        set folderPath to my getFolderPath(f)
                        set folderInfo to "{" & quote & "id" & quote & ":" & quote & (id of f) & quote & "," & quote & "name" & quote & ":" & quote & (name of f) & quote & "," & quote & "path" & quote & ":" & quote & folderPath & quote & "}"
                        set end of folderResults to folderInfo
                        my processFolders(f, folderResults)
                    end repeat
                    return folderResults
                end processFolders

                set folderList to my processFolders(front document, {})

                set AppleScript's text item delimiters to ","
                return "[" & (folderList as text) & "]"
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            return json.loads(result)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error retrieving folders: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing folder data: {e}")

    def drop_task(self, task_id: str) -> bool:
        """Drop a task (mark as on hold indefinitely).

        Args:
            task_id: The ID of the task to drop

        Returns:
            True if drop was successful

        Raises:
            Exception: If task not found or drop fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('drop_task')

        script = f'''
        tell application "OmniFocus"
            tell front document
                try
                    set theTask to first flattened task whose id is "{task_id}"
                    set dropped of theTask to true
                    return "true"
                on error
                    return "false"
                end try
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            if result.strip() == "true":
                return True
            else:
                raise Exception(f"Task not found: {task_id}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error dropping task: {e.stderr}")

    def create_folder(self, name: str, parent_path: Optional[str] = None) -> str:
        """Create a new folder in OmniFocus.

        Args:
            name: The name of the folder to create
            parent_path: Optional parent folder path (e.g., "Work" or "Work > Clients")

        Returns:
            The ID of the created folder

        Raises:
            Exception: If parent folder not found or creation fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('create_folder')

        # Escape quotes in name
        name_escaped = name.replace('"', '\\"')

        if parent_path is None:
            # Create at root level
            script = f'''
            tell application "OmniFocus"
                tell front document
                    try
                        set newFolder to make new folder with properties {{name:"{name_escaped}"}}
                        return id of newFolder
                    on error errMsg
                        return "false: " & errMsg
                    end try
                end tell
            end tell
            '''
        else:
            # Create in parent folder - need to find the parent first
            parts = [p.strip() for p in parent_path.split('>')]

            # Build AppleScript to navigate folder hierarchy
            if len(parts) == 1:
                # Single level parent
                script = f'''
                tell application "OmniFocus"
                    tell front document
                        try
                            set parentFolder to first folder whose name is "{parts[0]}"
                            set newFolder to make new folder at end of folders of parentFolder with properties {{name:"{name_escaped}"}}
                            return id of newFolder
                        on error errMsg
                            return "false: " & errMsg
                        end try
                    end tell
                end tell
                '''
            else:
                # Nested parent path
                folder_navigation = f'first folder whose name is "{parts[0]}"'
                for part in parts[1:]:
                    folder_navigation = f'first folder of ({folder_navigation}) whose name is "{part}"'

                script = f'''
                tell application "OmniFocus"
                    tell front document
                        try
                            set parentFolder to {folder_navigation}
                            set newFolder to make new folder at end of folders of parentFolder with properties {{name:"{name_escaped}"}}
                            return id of newFolder
                        on error errMsg
                            return "false: " & errMsg
                        end try
                    end tell
                end tell
                '''

        try:
            result = run_applescript(script)
            if result.startswith("false:"):
                raise Exception(f"Error creating folder: {result}")
            return result.strip()
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error creating folder: {e.stderr}")

    def set_parent_task(self, task_id: str, parent_task_id: Optional[str]) -> bool:
        """Set the parent task of a task (make it a subtask) or make it root-level.

        Args:
            task_id: The ID of the task to modify
            parent_task_id: The ID of the parent task, or None to make it root-level

        Returns:
            True if operation was successful

        Raises:
            Exception: If task or parent not found, or operation fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('set_parent_task')

        if parent_task_id is None:
            # Make task root-level (remove parent)
            script = f'''
            tell application "OmniFocus"
                tell front document
                    try
                        set theTask to first flattened task whose id is "{task_id}"
                        -- Get the task's containing project
                        set taskProject to containing project of theTask
                        if taskProject is not missing value then
                            -- Move to root of project
                            move theTask to end of tasks of taskProject
                        else
                            -- Move to inbox
                            move theTask to end of tasks of front document
                        end if
                        return "true"
                    on error errMsg
                        return "false: " & errMsg
                    end try
                end tell
            end tell
            '''
        else:
            # Set parent task
            script = f'''
            tell application "OmniFocus"
                tell front document
                    try
                        set theTask to first flattened task whose id is "{task_id}"
                        set theParent to first flattened task whose id is "{parent_task_id}"

                        -- Check for circular reference
                        if id of theTask is id of theParent then
                            return "false: Cannot set task as its own parent"
                        end if

                        -- Move task to be child of parent
                        move theTask to end of tasks of theParent
                        return "true"
                    on error errMsg
                        return "false: " & errMsg
                    end try
                end tell
            end tell
            '''

        try:
            result = run_applescript(script)
            if result.strip() == "true":
                return True
            else:
                raise Exception(f"Error setting parent task: {result}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error setting parent task: {e.stderr}")

    def set_review_interval(self, project_id: str, interval_weeks: int) -> bool:
        """Set the review interval for a project.

        Args:
            project_id: The ID of the project
            interval_weeks: Review interval in weeks (e.g., 1 for weekly, 4 for monthly)

        Returns:
            True if operation was successful

        Raises:
            Exception: If project not found or operation fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('set_review_interval')

        script = f'''
        tell application "OmniFocus"
            tell front document
                try
                    set theProject to first flattened project whose id is "{project_id}"
                    set review interval of theProject to {{unit:week, steps:{interval_weeks}, fixed:true}}
                    return "true"
                on error
                    return "false"
                end try
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            if result.strip() == "true":
                return True
            else:
                raise Exception(f"Project not found: {project_id}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error setting review interval: {e.stderr}")

    def mark_project_reviewed(self, project_id: str) -> bool:
        """Mark a project as reviewed (updates last review date and calculates next review date).

        Args:
            project_id: The ID of the project

        Returns:
            True if operation was successful

        Raises:
            Exception: If project not found or operation fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('mark_project_reviewed')

        script = f'''
        tell application "OmniFocus"
            tell front document
                try
                    set theProject to first flattened project whose id is "{project_id}"
                    mark theProject reviewed
                    return "true"
                on error
                    return "false"
                end try
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            if result.strip() == "true":
                return True
            else:
                raise Exception(f"Project not found: {project_id}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error marking project as reviewed: {e.stderr}")

    def get_projects_due_for_review(self) -> list[dict]:
        """Get all projects that are due for review.

        Returns:
            List of project dictionaries with id, name, nextReviewDate, lastReviewDate
        """
        script = '''
        tell application "OmniFocus"
            tell front document
                set output to ""
                set projectList to flattened projects

                repeat with p in projectList
                    try
                        set nextDate to next review date of p
                        if nextDate is not missing value then
                            -- Check if due for review (next review date is in the past or today)
                            if nextDate <= (current date) then
                                set projId to id of p
                                set projName to name of p

                                -- Format next review date
                                set nextDateStr to ""
                                try
                                    set nextDateStr to nextDate as «class isot» as string
                                end try

                                -- Format last review date
                                set lastDateStr to ""
                                try
                                    set lastDate to last review date of p
                                    if lastDate is not missing value then
                                        set lastDateStr to lastDate as «class isot» as string
                                    end if
                                end try

                                -- Build JSON manually
                                set jsonLine to "{" & quote & "id" & quote & ":" & quote & projId & quote & "," & quote & "name" & quote & ":" & quote & my escapeJSON(projName) & quote & "," & quote & "nextReviewDate" & quote & ":" & quote & nextDateStr & quote & "," & quote & "lastReviewDate" & quote & ":" & quote & lastDateStr & quote & "}"

                                if output is not "" then
                                    set output to output & "," & linefeed
                                end if
                                set output to output & jsonLine
                            end if
                        end if
                    end try
                end repeat

                return "[" & linefeed & output & linefeed & "]"
            end tell
        end tell

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
            return json.loads(result)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error retrieving projects due for review: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing review project data: {e}")

    def set_estimated_minutes(self, task_id: str, minutes: int) -> bool:
        """Set the estimated time for a task.

        Args:
            task_id: The ID of the task
            minutes: Estimated time in minutes (0 to clear estimate)

        Returns:
            True if operation was successful

        Raises:
            Exception: If task not found or operation fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('set_estimated_minutes')

        script = f'''
        tell application "OmniFocus"
            tell front document
                try
                    set theTask to first flattened task whose id is "{task_id}"
                    set estimated minutes of theTask to {minutes}
                    return "true"
                on error
                    return "false"
                end try
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            if result.strip() == "true":
                return True
            else:
                raise Exception(f"Task not found: {task_id}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error setting estimated minutes: {e.stderr}")

    def get_perspectives(self) -> list[str]:
        """Get all perspective names from OmniFocus.

        Returns:
            List of perspective names (both built-in and custom)
        """
        script = '''
        tell application "OmniFocus"
            tell default document
                get perspective names
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            # Result is comma-separated list like "Inbox, Projects, Tags, ..."
            perspectives = [p.strip() for p in result.split(',') if p.strip()]
            return perspectives
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error retrieving perspectives: {e.stderr}")

    def switch_perspective(self, perspective_name: str) -> str:
        """Switch the front window to a different perspective.

        Args:
            perspective_name: Name of the perspective to switch to

        Returns:
            The name of the perspective that was switched to

        Raises:
            Exception: If perspective not found or switch fails
        """
        # Escape quotes in perspective name
        perspective_escaped = perspective_name.replace('"', '\\"')

        script = f'''
        tell application "OmniFocus"
            tell default document
                tell front document window
                    set perspective name to "{perspective_escaped}"
                    return perspective name
                end tell
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            return result.strip()
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error switching perspective: {e.stderr}")
