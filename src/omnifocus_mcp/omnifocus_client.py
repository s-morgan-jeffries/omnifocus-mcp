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
        note: Optional[str] = None
    ) -> bool:
        """Add a task to a specific project using AppleScript."""
        # Escape quotes and backslashes for AppleScript
        def escape_applescript(text: str) -> str:
            if not text:
                return ""
            text = text.replace("\\", "\\\\")
            text = text.replace('"', '\\"')
            return text

        task_name_escaped = escape_applescript(task_name)
        note_escaped = escape_applescript(note or "")

        script = f'''
        tell application "OmniFocus"
            tell front document
                try
                    -- Find project by ID
                    set targetProject to first flattened project whose id is "{project_id}"

                    -- Create new task in the project
                    tell targetProject
                        set newTask to make new task with properties {{name:"{task_name_escaped}", note:"{note_escaped}"}}
                    end tell

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
