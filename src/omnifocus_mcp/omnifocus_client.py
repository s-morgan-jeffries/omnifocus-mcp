"""Client for interacting with OmniFocus app."""
import subprocess
import json
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


class OmniFocusClient:
    """Client for OmniFocus app operations using AppleScript."""

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
        # Escape quotes and backslashes for AppleScript
        def escape_applescript(text: str) -> str:
            if not text:
                return ""
            text = text.replace("\\", "\\\\")
            text = text.replace('"', '\\"')
            return text

        task_name_escaped = escape_applescript(task_name)
        note_escaped = escape_applescript(note or "")

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
                tag_escaped = escape_applescript(tag)
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
        # Escape quotes and backslashes for AppleScript
        def escape_applescript(text: str) -> str:
            if not text:
                return ""
            text = text.replace("\\", "\\\\")
            text = text.replace('"', '\\"')
            return text

        note_escaped = escape_applescript(note_text)

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
        flagged_only: bool = False
    ) -> list[dict[str, Any]]:
        """Get tasks from OmniFocus with optional filtering.

        Args:
            project_id: Optional project ID to filter tasks. If None, returns all tasks.
            include_completed: Whether to include completed tasks (default: False)
            flagged_only: Only return flagged tasks (default: False)

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
