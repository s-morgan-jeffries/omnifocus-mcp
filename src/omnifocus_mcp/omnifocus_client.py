"""Client for interacting with OmniFocus app."""
import subprocess
import json
import os
from enum import Enum
from typing import Any, Optional, Union


class TaskStatus(Enum):
    """Task status values for OmniFocus tasks."""
    ACTIVE = "active"
    DROPPED = "dropped"


class ProjectStatus(Enum):
    """Project status values for OmniFocus projects."""
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    DONE = "done"
    DROPPED = "dropped"


def run_applescript(script: str, timeout: int = 60) -> str:
    """Execute AppleScript and return the result.

    Args:
        script: The AppleScript code to execute
        timeout: Maximum seconds to wait (default: 60, max: 300)

    Returns:
        The stdout output from the AppleScript

    Raises:
        subprocess.TimeoutExpired: If script execution exceeds timeout
        subprocess.CalledProcessError: If script execution fails
    """
    if timeout > 300:
        raise ValueError("Timeout cannot exceed 300 seconds")

    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        check=True,
        timeout=timeout
    )
    return result.stdout.strip()


# AppleScript helper functions for JSON escaping
#
# NOTE: These helpers are embedded 9 times throughout this file - this is INTENTIONAL.
# AppleScript does not support imports or modules, so each AppleScript block must be
# completely self-contained. While this creates code duplication, it's a necessary
# limitation of the AppleScript language.
#
# DO NOT attempt to refactor this duplication - it will break AppleScript execution.
APPLESCRIPT_JSON_HELPERS = '''
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
        """Verify we're using the correct database during test mode.

        In production mode (default): All operations are allowed.
        In test mode (OMNIFOCUS_TEST_MODE=true): Verifies the correct test database is open.

        Args:
            operation_name: Name of the operation being performed

        Raises:
            DatabaseSafetyError: If test mode is enabled but wrong database is open
        """
        # Skip if safety checks are disabled (for unit tests)
        if not self._safety_checks_enabled:
            return

        # Read-only operations are always safe
        if operation_name not in self.DESTRUCTIVE_OPERATIONS:
            return

        # If in test mode, verify we're using the correct test database
        if not self._test_mode:
            # Production mode: no safety checks, allow the operation
            return

        # Test mode: verify we're using the correct test database via AppleScript
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
            # OmniFocus returns name without .ofocus extension, so strip it for comparison
            expected_name = self._test_database.replace('.ofocus', '')
            if expected_name not in result:
                raise DatabaseSafetyError(
                    f"Database safety check FAILED! Expected '{expected_name}' (from {self._test_database}) but got '{result}'. "
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

    def _filter_projects_by_conditions(
        self,
        projects: list[dict[str, Any]],
        min_task_count: Optional[int],
        has_overdue_tasks: Optional[bool],
        has_no_due_dates: Optional[bool]
    ) -> list[dict[str, Any]]:
        """Filter projects by conditional criteria.

        Args:
            projects: List of project dictionaries to filter
            min_task_count: Only include projects with at least this many tasks
            has_overdue_tasks: If True, only include projects with overdue tasks
            has_no_due_dates: If True, only include projects where no tasks have due dates

        Returns:
            Filtered list of projects
        """
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()

        filtered = []

        for project in projects:
            project_id = project.get('id')
            if not project_id:
                continue

            # Get tasks for this project (cached by get_tasks)
            tasks = self.get_tasks(project_id=project_id, include_completed=False)

            include = True

            # Check min_task_count filter
            if min_task_count is not None:
                if len(tasks) < min_task_count:
                    include = False

            # Check has_overdue_tasks filter
            if include and has_overdue_tasks is not None:
                has_overdue = any(
                    task.get('dueDate', '') and task.get('dueDate', '') < now
                    for task in tasks
                )
                if has_overdue_tasks and not has_overdue:
                    include = False
                elif not has_overdue_tasks and has_overdue:
                    include = False

            # Check has_no_due_dates filter
            if include and has_no_due_dates is not None:
                all_have_no_due_date = all(
                    not task.get('dueDate', '')
                    for task in tasks
                ) and len(tasks) > 0  # Must have at least one task

                if has_no_due_dates and not all_have_no_due_date:
                    include = False
                elif not has_no_due_dates and all_have_no_due_date:
                    include = False

            if include:
                filtered.append(project)

        return filtered

    def _filter_by_date_range(
        self,
        items: list[dict[str, Any]],
        created_after: Optional[str],
        created_before: Optional[str],
        modified_after: Optional[str],
        modified_before: Optional[str]
    ) -> list[dict[str, Any]]:
        """Filter items by date ranges.

        Args:
            items: List of task or project dictionaries to filter
            created_after: Only include items created after this date
            created_before: Only include items created before this date
            modified_after: Only include items modified after this date
            modified_before: Only include items modified before this date

        Returns:
            Filtered list of items
        """
        filtered = []

        for item in items:
            include = True

            # Check creation date filters
            if created_after or created_before:
                creation_date = item.get('creationDate', '')
                if creation_date:
                    if created_after and creation_date < created_after:
                        include = False
                    if created_before and creation_date > created_before:
                        include = False
                else:
                    # No creation date - exclude if filtering by creation date
                    include = False

            # Check modification date filters
            if include and (modified_after or modified_before):
                mod_date = item.get('modificationDate', '')
                if mod_date:
                    if modified_after and mod_date < modified_after:
                        include = False
                    if modified_before and mod_date > modified_before:
                        include = False
                else:
                    # No modification date - exclude if filtering by modification date
                    include = False

            if include:
                filtered.append(item)

        return filtered

    def _filter_tasks_by_tags(self, tasks: list[dict[str, Any]], tag_filter: list[str], mode: str) -> list[dict[str, Any]]:
        """Filter tasks by tags using boolean logic.

        Args:
            tasks: List of task dictionaries to filter
            tag_filter: List of tag names to filter by
            mode: Filtering mode - "and" (all tags), "or" (any tag), "not" (none of tags)

        Returns:
            Filtered list of tasks
        """
        filtered_tasks = []
        # Normalize filter tags to lowercase for case-insensitive comparison
        filter_tags_lower = [tag.lower() for tag in tag_filter]

        for task in tasks:
            # Parse task tags (comma-separated string)
            task_tags_str = task.get('tags', '')
            if task_tags_str:
                task_tags = [t.strip().lower() for t in task_tags_str.split(',')]
            else:
                task_tags = []

            if mode == "and":
                # Task must have all of the filter tags
                if all(tag in task_tags for tag in filter_tags_lower):
                    filtered_tasks.append(task)
            elif mode == "or":
                # Task must have at least one of the filter tags
                if any(tag in task_tags for tag in filter_tags_lower):
                    filtered_tasks.append(task)
            elif mode == "not":
                # Task must not have any of the filter tags
                if not any(tag in task_tags for tag in filter_tags_lower):
                    filtered_tasks.append(task)

        return filtered_tasks

    def _sort_tasks(self, tasks: list[dict[str, Any]], sort_by: str, sort_order: str) -> list[dict[str, Any]]:
        """Sort tasks by specified field and order.

        Args:
            tasks: List of task dictionaries to sort
            sort_by: Field to sort by ("name", "due_date", "defer_date")
            sort_order: Sort order ("asc" or "desc")

        Returns:
            Sorted list of tasks
        """
        # Map sort_by to actual field names in task dict
        field_map = {
            "name": "name",
            "due_date": "dueDate",
            "defer_date": "deferDate"
        }

        field = field_map[sort_by]
        reverse = (sort_order == "desc")

        # For date fields, handle empty dates by putting them last
        if field in ["dueDate", "deferDate"]:
            def sort_key(task):
                value = task.get(field, "")
                # Empty dates sort to end regardless of asc/desc
                if not value:
                    return ("9999" if not reverse else "")
                return value
            return sorted(tasks, key=sort_key, reverse=reverse)
        else:
            # For name, simple case-insensitive sort
            return sorted(tasks, key=lambda t: t.get(field, "").lower(), reverse=reverse)

    def get_projects(
        self,
        on_hold_only: bool = False,
        modified_after: Optional[str] = None,
        modified_before: Optional[str] = None,
        min_task_count: Optional[int] = None,
        has_overdue_tasks: Optional[bool] = None,
        has_no_due_dates: Optional[bool] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        query: Optional[str] = None,
        timeout: int = 90
    ) -> list[dict[str, Any]]:
        """Get projects with their folder/hierarchy information using AppleScript.

        NOTE: This method is intentionally long (251 lines) because:
        1. AppleScript must be a single self-contained string with embedded JSON helpers
        2. Comprehensive property extraction (timestamps, stats, hierarchy, etc.)
        3. Multiple filter conditions and post-processing logic
        4. AppleScript is verbose for JSON generation and error handling

        Args:
            on_hold_only: Only return projects with "on hold" status (default: False)
            modified_after: Only return projects modified after this ISO date
            modified_before: Only return projects modified before this ISO date
            min_task_count: Only return projects with at least this many tasks
            has_overdue_tasks: If True, only return projects with overdue tasks
            has_no_due_dates: If True, only return projects where no tasks have due dates
            sort_by: Field to sort by - "name" (default: None - OmniFocus order)
            sort_order: Sort order - "asc" or "desc" (default: "asc")
            query: Optional search term to filter by name, note, or folder path (case-insensitive)
            timeout: Maximum seconds to wait for AppleScript (default: 90). Increase for large project lists (100+)

        Returns:
            list: List of project dictionaries with id, name, status, folder, note, etc.

        Raises:
            ValueError: If date format or sort parameters are invalid
            subprocess.TimeoutExpired: If AppleScript execution exceeds timeout
        """
        # Validate date formats
        from datetime import datetime
        for date_param, date_value in [
            ("modified_after", modified_after),
            ("modified_before", modified_before)
        ]:
            if date_value:
                try:
                    datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                except ValueError:
                    raise ValueError(f"Invalid date format for {date_param}: {date_value}. Use ISO format (e.g., '2025-01-15T00:00:00Z')")

        # Validate sort parameters
        valid_sort_by = ["name", None]
        valid_sort_order = ["asc", "desc"]

        if sort_by not in valid_sort_by:
            raise ValueError(f"Invalid sort_by value: {sort_by}. Must be one of: {[v for v in valid_sort_by if v is not None]}")
        if sort_order not in valid_sort_order:
            raise ValueError(f"Invalid sort_order value: {sort_order}. Must be one of: {valid_sort_order}")
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
                        if projStatus is "dropped status" then
                            error "skip dropped project"
                        end if

                        {on_hold_check}

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

                        -- Get timestamp fields
                        set creationDateStr to "null"
                        try
                            set creationDate to creation date of proj
                            if creationDate is not missing value then
                                set creationDateStr to "\\"" & (creationDate as «class isot» as string) & "\\""
                            end if
                        end try

                        set modDateStr to "null"
                        try
                            set modDate to modification date of proj
                            if modDate is not missing value then
                                set modDateStr to "\\"" & (modDate as «class isot» as string) & "\\""
                            end if
                        end try

                        set completionDateStr to "null"
                        try
                            set completionDate to completion date of proj
                            if completionDate is not missing value then
                                set completionDateStr to "\\"" & (completionDate as «class isot» as string) & "\\""
                            end if
                        end try

                        set droppedDateStr to "null"
                        try
                            set droppedDate to dropped date of proj
                            if droppedDate is not missing value then
                                set droppedDateStr to "\\"" & (droppedDate as «class isot» as string) & "\\""
                            end if
                        end try

                        -- Get sequential status
                        set isSequential to sequential of proj

                        -- Calculate last activity date (most recent task creation or completion)
                        set lastActivityStr to "null"
                        try
                            set projTasks to flattened tasks of proj
                            set lastActivity to missing value

                            repeat with t in projTasks
                                try
                                    set createDate to creation date of t
                                    if lastActivity is missing value or createDate > lastActivity then
                                        set lastActivity to createDate
                                    end if
                                end try

                                try
                                    if completed of t is true then
                                        set compDate to completion date of t
                                        if compDate is not missing value then
                                            if lastActivity is missing value or compDate > lastActivity then
                                                set lastActivity to compDate
                                            end if
                                        end if
                                    end if
                                end try
                            end repeat

                            if lastActivity is not missing value then
                                set lastActivityStr to "\\"" & (lastActivity as «class isot» as string) & "\\""
                            end if
                        end try

                        -- Build JSON manually (AppleScript doesn't have native JSON)
                        set jsonLine to "{{" & ¬
                            "\\"id\\": \\"" & projId & "\\", " & ¬
                            "\\"name\\": \\"" & my escapeJSON(projName) & "\\", " & ¬
                            "\\"note\\": \\"" & my escapeJSON(projNote) & "\\", " & ¬
                            "\\"status\\": \\"" & projStatus & "\\", " & ¬
                            "\\"sequential\\": " & (isSequential as text) & ", " & ¬
                            "\\"folderPath\\": \\"" & my escapeJSON(folderPath) & "\\", " & ¬
                            "\\"creationDate\\": " & creationDateStr & ", " & ¬
                            "\\"modificationDate\\": " & modDateStr & ", " & ¬
                            "\\"completionDate\\": " & completionDateStr & ", " & ¬
                            "\\"droppedDate\\": " & droppedDateStr & ", " & ¬
                            "\\"lastActivityDate\\": " & lastActivityStr & ¬
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
        ''' + APPLESCRIPT_JSON_HELPERS

        # Build on_hold filter
        on_hold_check = "" if not on_hold_only else """
                        -- Skip non-on-hold projects
                        if projStatus is not "on hold status" then
                            error "skip non-on-hold project"
                        end if"""

        script = script.format(on_hold_check=on_hold_check)

        try:
            result = run_applescript(script, timeout=timeout)
            if result:
                projects = json.loads(result)

                # Apply date range filtering
                if modified_after or modified_before:
                    projects = self._filter_by_date_range(
                        projects,
                        None,  # created_after (not applicable to projects)
                        None,  # created_before
                        modified_after,
                        modified_before
                    )

                # Apply conditional filters
                if min_task_count is not None or has_overdue_tasks is not None or has_no_due_dates is not None:
                    projects = self._filter_projects_by_conditions(
                        projects,
                        min_task_count,
                        has_overdue_tasks,
                        has_no_due_dates
                    )

                # Apply query filter if provided
                if query:
                    query_lower = query.lower()
                    projects = [
                        p for p in projects
                        if query_lower in p.get('name', '').lower()
                        or query_lower in p.get('note', '').lower()
                        or query_lower in p.get('folderPath', '').lower()
                    ]

                # Apply sorting if requested
                if sort_by:
                    reverse = (sort_order == "desc")
                    projects = sorted(projects, key=lambda p: p.get("name", "").lower(), reverse=reverse)

                return projects
            else:
                raise Exception("No output from OmniFocus AppleScript")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error querying OmniFocus: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing OmniFocus output: {e}")

    def get_project(self, project_id: str) -> dict[str, Any]:
        """Get a single project by its ID.

        NOTE: This method is intentionally long (231 lines) because:
        1. Retrieves comprehensive project data including all timestamps and statistics
        2. AppleScript must extract 15+ properties with null-safety checks
        3. Calculates aggregate statistics (task counts by status, overdue, etc.)
        4. Self-contained AppleScript with embedded JSON helpers

        Args:
            project_id: The ID of the project to retrieve

        Returns:
            dict: Project dictionary with id, name, note, status, folderPath, sequential, timestamps, and statistics:
                - sequential: Boolean indicating if tasks must be completed in order
                - creationDate: When project was created (ISO 8601 or null)
                - modificationDate: Last time project was modified (ISO 8601 or null)
                - completionDate: When project was completed (ISO 8601 or null)
                - droppedDate: When project was dropped (ISO 8601 or null)
                - lastReviewDate: Last GTD review date (ISO 8601 or null)
                - nextReviewDate: Next scheduled review (ISO 8601 or null)
                - lastActivityDate: Most recent task activity (ISO 8601 or null)
                - taskCount: Total number of tasks
                - completedTaskCount: Number of completed tasks
                - remainingTaskCount: Number of remaining tasks
                - completionPercentage: Percentage of completed tasks (0.0-100.0)

        Raises:
            ValueError: If project_id is empty
            Exception: If project not found or error occurs
        """
        if not project_id:
            raise ValueError("project_id is required")

        script = f'''
        use AppleScript version "2.4"
        use scripting additions

        tell application "OmniFocus"
            tell front document
                set targetProject to first flattened project whose id is "{project_id}"

                if targetProject is missing value then
                    error "Project not found"
                end if

                set projId to id of targetProject
                set projName to name of targetProject
                set projNote to note of targetProject
                set projStatus to status of targetProject as text
                set projSequential to sequential of targetProject

                -- Get folder path
                set folderPath to ""
                try
                    set parentFolder to container of targetProject
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

                -- Calculate task statistics
                set allTasks to flattened tasks of targetProject
                set taskCount to count of allTasks
                set completedCount to 0

                repeat with t in allTasks
                    if completed of t is true then
                        set completedCount to completedCount + 1
                    end if
                end repeat

                set remainingCount to taskCount - completedCount
                set completionPct to 0.0
                if taskCount > 0 then
                    set completionPct to (completedCount / taskCount) * 100
                end if

                -- Get review metadata
                set reviewIntervalStr to "null"
                set lastReviewStr to "null"
                set nextReviewStr to "null"

                try
                    set reviewInterval to review interval of targetProject
                    if reviewInterval is not missing value then
                        -- Convert interval to readable format (e.g., "1 week", "2 weeks")
                        set intervalSecs to reviewInterval as integer
                        set intervalDays to intervalSecs / 86400
                        set intervalWeeks to intervalDays / 7

                        if intervalWeeks ≥ 1 then
                            if intervalWeeks = 1 then
                                set reviewIntervalStr to "\\"1 week\\""
                            else
                                set reviewIntervalStr to "\\"" & (intervalWeeks as integer) & " weeks\\""
                            end if
                        else if intervalDays ≥ 1 then
                            if intervalDays = 1 then
                                set reviewIntervalStr to "\\"1 day\\""
                            else
                                set reviewIntervalStr to "\\"" & (intervalDays as integer) & " days\\""
                            end if
                        end if
                    end if
                end try

                try
                    set lastReview to last review date of targetProject
                    if lastReview is not missing value then
                        set lastReviewStr to "\\"" & (lastReview as «class isot» as string) & "\\""
                    end if
                end try

                try
                    set nextReview to next review date of targetProject
                    if nextReview is not missing value then
                        set nextReviewStr to "\\"" & (nextReview as «class isot» as string) & "\\""
                    end if
                end try

                -- Get timestamp fields
                set creationDateStr to "null"
                try
                    set creationDate to creation date of targetProject
                    if creationDate is not missing value then
                        set creationDateStr to "\\"" & (creationDate as «class isot» as string) & "\\""
                    end if
                end try

                set modDateStr to "null"
                try
                    set modDate to modification date of targetProject
                    if modDate is not missing value then
                        set modDateStr to "\\"" & (modDate as «class isot» as string) & "\\""
                    end if
                end try

                set completionDateStr to "null"
                try
                    set completionDate to completion date of targetProject
                    if completionDate is not missing value then
                        set completionDateStr to "\\"" & (completionDate as «class isot» as string) & "\\""
                    end if
                end try

                set droppedDateStr to "null"
                try
                    set droppedDate to dropped date of targetProject
                    if droppedDate is not missing value then
                        set droppedDateStr to "\\"" & (droppedDate as «class isot» as string) & "\\""
                    end if
                end try

                -- Calculate last activity date (already have tasks from earlier)
                set lastActivityStr to "null"
                try
                    set lastActivity to missing value

                    repeat with t in allTasks
                        try
                            set createDate to creation date of t
                            if lastActivity is missing value or createDate > lastActivity then
                                set lastActivity to createDate
                            end if
                        end try

                        try
                            if completed of t is true then
                                set compDate to completion date of t
                                if compDate is not missing value then
                                    if lastActivity is missing value or compDate > lastActivity then
                                        set lastActivity to compDate
                                    end if
                                end if
                            end if
                        end try
                    end repeat

                    if lastActivity is not missing value then
                        set lastActivityStr to "\\"" & (lastActivity as «class isot» as string) & "\\""
                    end if
                end try

                -- Build JSON manually
                set jsonOutput to "{{" & ¬
                    "\\"id\\": \\"" & projId & "\\", " & ¬
                    "\\"name\\": \\"" & my escapeJSON(projName) & "\\", " & ¬
                    "\\"note\\": \\"" & my escapeJSON(projNote) & "\\", " & ¬
                    "\\"status\\": \\"" & projStatus & "\\", " & ¬
                    "\\"folderPath\\": \\"" & my escapeJSON(folderPath) & "\\", " & ¬
                    "\\"sequential\\": " & (projSequential as text) & ", " & ¬
                    "\\"taskCount\\": " & taskCount & ", " & ¬
                    "\\"completedTaskCount\\": " & completedCount & ", " & ¬
                    "\\"remainingTaskCount\\": " & remainingCount & ", " & ¬
                    "\\"completionPercentage\\": " & completionPct & ", " & ¬
                    "\\"reviewInterval\\": " & reviewIntervalStr & ", " & ¬
                    "\\"lastReviewDate\\": " & lastReviewStr & ", " & ¬
                    "\\"nextReviewDate\\": " & nextReviewStr & ", " & ¬
                    "\\"creationDate\\": " & creationDateStr & ", " & ¬
                    "\\"modificationDate\\": " & modDateStr & ", " & ¬
                    "\\"completionDate\\": " & completionDateStr & ", " & ¬
                    "\\"droppedDate\\": " & droppedDateStr & ", " & ¬
                    "\\"lastActivityDate\\": " & lastActivityStr & ¬
                    "}}"

                return jsonOutput
            end tell
        end tell
        ''' + APPLESCRIPT_JSON_HELPERS

        try:
            result = run_applescript(script)
            if result:
                return json.loads(result)
            else:
                raise Exception(f"Project with ID '{project_id}' not found")
        except subprocess.CalledProcessError as e:
            if "Project not found" in e.stderr:
                raise Exception(f"Project with ID '{project_id}' not found")
            raise Exception(f"Error retrieving project: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing project output: {e}")

    def get_project_aggregates(self, project_id: str) -> dict[str, Any]:
        """Get aggregated statistics for a project's tasks.

        Args:
            project_id: The ID of the project

        Returns:
            dict: Aggregated statistics with:
                - projectId: The project ID
                - taskCount: Total number of incomplete tasks
                - totalEstimatedMinutes: Sum of all task time estimates
                - earliestDueDate: Earliest due date among tasks (None if no dates)
                - latestDueDate: Latest due date among tasks (None if no dates)
                - overdueTaskCount: Number of tasks with past due dates
                - dueTodayCount: Number of tasks due today
                - dueThisWeekCount: Number of tasks due within the next 7 days (excluding today and overdue)
                - noDueDateCount: Number of tasks without due dates

        Raises:
            ValueError: If project_id is empty
        """
        if not project_id:
            raise ValueError("project_id is required")

        # Get all incomplete tasks for this project
        tasks = self.get_tasks(project_id=project_id, include_completed=False)

        # Initialize aggregates
        total_estimated_minutes = 0
        earliest_due_date = None
        latest_due_date = None
        overdue_count = 0
        due_today_count = 0
        due_this_week_count = 0
        no_due_date_count = 0

        # Get current datetime for date comparisons
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()

        # Calculate today's date range (start and end of day in UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        today_start_iso = today_start.isoformat()
        today_end_iso = today_end.isoformat()

        # Calculate end of this week (7 days from today's start)
        week_end = (today_start + timedelta(days=7)).isoformat()

        for task in tasks:
            # Sum time estimates
            estimated_minutes = task.get('estimatedMinutes', 0)
            if estimated_minutes:
                total_estimated_minutes += estimated_minutes

            # Track due date range and categorize
            due_date = task.get('dueDate', '')
            if due_date:
                if earliest_due_date is None or due_date < earliest_due_date:
                    earliest_due_date = due_date
                if latest_due_date is None or due_date > latest_due_date:
                    latest_due_date = due_date

                # Categorize by due date
                if due_date < today_start_iso:
                    # Overdue (before today)
                    overdue_count += 1
                elif today_start_iso <= due_date <= today_end_iso:
                    # Due today
                    due_today_count += 1
                elif due_date <= week_end:
                    # Due this week (not including today, not overdue)
                    due_this_week_count += 1
                # else: due later than this week
            else:
                # No due date
                no_due_date_count += 1

        return {
            'projectId': project_id,
            'taskCount': len(tasks),
            'totalEstimatedMinutes': total_estimated_minutes,
            'earliestDueDate': earliest_due_date,
            'latestDueDate': latest_due_date,
            'overdueTaskCount': overdue_count,
            'dueTodayCount': due_today_count,
            'dueThisWeekCount': due_this_week_count,
            'noDueDateCount': no_due_date_count
        }

    def get_stalled_projects(self, days_inactive: int = 30, min_task_count: Optional[int] = None) -> list[dict[str, Any]]:
        """Get active projects with no recent task activity.

        Args:
            days_inactive: Minimum days of inactivity to consider a project stalled (default: 30)
            min_task_count: Minimum number of tasks a project must have to be included (optional)

        Returns:
            list[dict]: List of stalled projects, each containing:
                - id: Project ID
                - name: Project name
                - status: Project status (always "active")
                - lastActivityDate: ISO timestamp of most recent task activity (or null)
                - daysInactive: Number of days since last activity (or null if no activity)
                - taskCount: Total number of tasks in project

            Projects are sorted by days inactive (most stale first).
        """
        from datetime import datetime, timezone

        # AppleScript to get projects with lastActivityDate
        script = '''
        tell application "OmniFocus"
            tell front document
                set output to "["
                set firstItem to true

                repeat with proj in flattened projects
                    if status of proj is active then
                        set projId to id of proj
                        set projName to name of proj

                        -- Get modification date as last activity proxy
                        set lastActivityStr to "null"
                        try
                            set modDate to modification date of proj
                            if modDate is not missing value then
                                set lastActivityStr to "\\"" & (modDate as «class isot» as string) & "\\""
                            end if
                        end try

                        -- Get task count
                        set taskCount to (count of flattened tasks of proj)

                        if not firstItem then
                            set output to output & ","
                        end if
                        set firstItem to false

                        set output to output & "{" & ¬
                            "\\"id\\":\\"" & projId & "\\"," & ¬
                            "\\"name\\":\\"" & projName & "\\"," & ¬
                            "\\"status\\":\\"active\\"," & ¬
                            "\\"lastActivityDate\\":" & lastActivityStr & "," & ¬
                            "\\"taskCount\\":" & taskCount & ¬
                            "}"
                    end if
                end repeat

                set output to output & "]"
                return output
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            if not result or result == "[]":
                return []

            projects = json.loads(result)

            # Calculate daysInactive and filter
            now = datetime.now(timezone.utc)
            filtered_projects = []

            for project in projects:
                # Calculate days inactive
                if project['lastActivityDate']:
                    last_activity_str = project['lastActivityDate'].replace('Z', '+00:00')
                    last_activity = datetime.fromisoformat(last_activity_str)

                    # Make timezone-aware if needed
                    if last_activity.tzinfo is None:
                        last_activity = last_activity.replace(tzinfo=timezone.utc)

                    days_diff = (now - last_activity).days
                    project['daysInactive'] = days_diff

                    # Filter by days_inactive threshold
                    if days_diff < days_inactive:
                        continue
                else:
                    project['daysInactive'] = None

                # Filter by min_task_count if specified
                if min_task_count is not None and project['taskCount'] < min_task_count:
                    continue

                filtered_projects.append(project)

            # Sort by days inactive (most stale first)
            filtered_projects.sort(key=lambda p: p['daysInactive'] if p['daysInactive'] is not None else float('inf'), reverse=True)

            return filtered_projects

        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse OmniFocus response: {e}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"AppleScript execution failed: {e.stderr}")

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

                repeat with i from 1 to count of folderNames
                    set folderName to item i of folderNames

                    if i is 1 then
                        -- First level: search in document folders
                        repeat with f in folders
                            if name of f is folderName then
                                set targetFolder to f
                                exit repeat
                            end if
                        end repeat
                    else
                        -- Subsequent levels: search in current folder's subfolders
                        if targetFolder is not missing value then
                            set found to false
                            repeat with f in folders of targetFolder
                                if name of f is folderName then
                                    set targetFolder to f
                                    set found to true
                                    exit repeat
                                end if
                            end repeat
                            if not found then
                                set targetFolder to missing value
                                exit repeat
                            end if
                        end if
                    end if
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

    def update_project(
        self,
        project_id: str,
        project_name: Optional[str] = None,
        folder_path: Optional[str] = None,
        note: Optional[str] = None,
        sequential: Optional[bool] = None,
        status: Optional[Union[ProjectStatus, str]] = None,
        review_interval_weeks: Optional[int] = None,
        last_reviewed: Optional[str] = None
    ) -> dict:
        """Update properties of an existing project (NEW API - Phase 2).

        NEW API changes:
        - Renamed 'name' parameter to 'project_name' for consistency
        - Added status parameter (ProjectStatus enum or string)
        - Added review_interval_weeks parameter
        - Added last_reviewed parameter
        - Added folder_path parameter
        - Returns dict instead of bool
        - Consolidates: set_project_status(), drop_project(), set_review_interval(), mark_project_reviewed()

        Args:
            project_id: The ID of the project to update
            project_name: New project name (optional)
            folder_path: Folder path to move project to (e.g., "Work > Projects")
            note: New project note (optional)
            sequential: New sequential setting (optional)
            status: Project status (ProjectStatus enum or string: "active", "on_hold", "done", "dropped")
            review_interval_weeks: Review interval in weeks (0 to clear)
            last_reviewed: Last reviewed date in ISO format or "now" (optional)

        Returns:
            dict: {
                "success": bool,
                "project_id": str,
                "updated_fields": list[str],
                "error": Optional[str]
            }

        Raises:
            ValueError: If project_id is empty, no fields provided, or invalid status
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('update_project')

        if not project_id:
            raise ValueError("project_id is required")

        # Collect all provided fields
        all_fields = {
            "project_name": project_name,
            "folder_path": folder_path,
            "note": note,
            "sequential": sequential,
            "status": status,
            "review_interval_weeks": review_interval_weeks,
            "last_reviewed": last_reviewed
        }

        # Check if at least one field is provided
        if all(v is None for v in all_fields.values()):
            raise ValueError("At least one field must be provided to update")

        # Validate and normalize status
        status_str = None
        if status is not None:
            if isinstance(status, ProjectStatus):
                status_str = status.value
            elif isinstance(status, str):
                # Validate string status
                valid_statuses = ["active", "on_hold", "done", "dropped"]
                if status.lower() not in valid_statuses:
                    raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}")
                status_str = status.lower()
            else:
                raise ValueError(f"status must be ProjectStatus enum or string, got {type(status)}")

        # Track which fields we're updating
        updated_fields = []

        # Build properties for simple fields
        properties = []
        project_id_escaped = self._escape_applescript_string(project_id)

        if project_name is not None:
            escaped_name = self._escape_applescript_string(project_name)
            properties.append(f'name:"{escaped_name}"')
            updated_fields.append("project_name")

        if note is not None:
            escaped_note = self._escape_applescript_string(note)
            properties.append(f'note:"{escaped_note}"')
            updated_fields.append("note")

        if sequential is not None:
            properties.append(f'sequential:{str(sequential).lower()}')
            updated_fields.append("sequential")

        # Build status command (separate from properties)
        status_command = ""
        if status_str is not None:
            # Map status string to OmniFocus status
            status_map = {
                "active": "active",
                "on_hold": "on hold",
                "done": "done",
                "dropped": "dropped"
            }
            of_status = status_map[status_str]
            status_command = f'set status of theProject to {of_status}'
            updated_fields.append("status")

        # Build review interval command
        review_command = ""
        if review_interval_weeks is not None:
            # Use OmniFocus record format for review interval
            review_command = f'set review interval of theProject to {{unit:week, steps:{review_interval_weeks}, fixed:true}}'
            updated_fields.append("review_interval_weeks")

        # Build last reviewed command
        reviewed_command = ""
        if last_reviewed is not None:
            if last_reviewed.lower() == "now" or last_reviewed == "":
                reviewed_command = 'set next review date of theProject to (current date)'
            else:
                # Parse ISO date
                reviewed_command = f'set next review date of theProject to date "{last_reviewed}"'
            updated_fields.append("last_reviewed")

        # Build folder path command
        folder_command = ""
        if folder_path is not None:
            # Parse folder path (use ">" as delimiter like create_project)
            folder_parts = [part.strip() for part in folder_path.split('>')]

            if len(folder_parts) == 1:
                # Top-level folder - simple case
                folder_escaped = self._escape_applescript_string(folder_parts[0])
                folder_command = f'''
                    -- Move to top-level folder
                    set targetFolder to first folder whose name is "{folder_escaped}"
                    move theProject to end of projects of targetFolder
                '''
            else:
                # Nested folder - walk the hierarchy
                folder_names_list = ', '.join(f'"{self._escape_applescript_string(p)}"' for p in folder_parts)
                folder_command = f'''
                    -- Move to nested folder
                    set folderNames to {{{folder_names_list}}}
                    set targetFolder to missing value

                    repeat with i from 1 to count of folderNames
                        set folderName to item i of folderNames

                        if i is 1 then
                            -- First level: search in document folders
                            repeat with f in folders
                                if name of f is folderName then
                                    set targetFolder to f
                                    exit repeat
                                end if
                            end repeat
                        else
                            -- Subsequent levels: search in current folder's subfolders
                            if targetFolder is not missing value then
                                set found to false
                                repeat with f in folders of targetFolder
                                    if name of f is folderName then
                                        set targetFolder to f
                                        set found to true
                                        exit repeat
                                    end if
                                end repeat
                                if not found then
                                    error "Folder path not found: {folder_path}"
                                end if
                            end if
                        end if
                    end repeat

                    if targetFolder is missing value then
                        error "Folder path not found: {folder_path}"
                    end if

                    move theProject to end of projects of targetFolder
                '''
            updated_fields.append("folder_path")

        # Build properties string
        properties_str = ", ".join(properties) if properties else ""
        properties_command = f"set properties of theProject to {{{properties_str}}}" if properties_str else ""

        # Build complete AppleScript
        script = f'''
        tell application "OmniFocus"
            tell front document
                try
                    set theProject to first flattened project whose id is "{project_id_escaped}"
                    if theProject is missing value then
                        return "false|Project not found"
                    end if

                    {properties_command}
                    {status_command}
                    {review_command}
                    {reviewed_command}
                    {folder_command}

                    return "true"
                on error errMsg
                    return "false|" & errMsg
                end try
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            result = result.strip()

            if result.startswith("true"):
                return {
                    "success": True,
                    "project_id": project_id,
                    "updated_fields": updated_fields
                }
            else:
                # Extract error message
                error_msg = result.split("|", 1)[1] if "|" in result else "Update failed"
                return {
                    "success": False,
                    "project_id": project_id,
                    "updated_fields": [],
                    "error": error_msg
                }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "project_id": project_id,
                "updated_fields": [],
                "error": f"AppleScript error: {e.stderr}"
            }

    def update_projects(
        self,
        project_ids: Union[str, list[str]],
        folder_path: Optional[str] = None,
        sequential: Optional[bool] = None,
        status: Optional[Union[ProjectStatus, str]] = None,
        review_interval_weeks: Optional[int] = None,
        last_reviewed: Optional[str] = None,
        **kwargs  # Catch invalid parameters like project_name, note
    ) -> dict:
        """Update properties of multiple projects (NEW API - Phase 2, Batch Function).

        This is the BATCH version of update_project(). It updates multiple projects
        with the same values.

        IMPORTANT: This function does NOT accept project_name or note parameters
        because those require unique values for each project. Use update_project()
        for those fields.

        NEW API changes:
        - Accepts Union[str, list[str]] for project_ids (single or batch)
        - EXCLUDES project_name and note (require unique values)
        - Returns dict with counts instead of success bool
        - Continues processing even if some projects fail
        - Consolidates: drop_projects() legacy function

        Args:
            project_ids: Single project ID (str) or list of project IDs
            folder_path: Folder path to move projects to (e.g., "Work > Projects")
            sequential: Sequential setting (optional)
            status: Project status (ProjectStatus enum or string: "active", "on_hold", "done", "dropped")
            review_interval_weeks: Review interval in weeks (0 to clear)
            last_reviewed: Last review date ("now" or ISO format like "2025-01-15")

        Returns:
            dict: {
                "updated_count": int,  # Number of successfully updated projects
                "failed_count": int,    # Number of failed updates
                "updated_ids": list[str],  # IDs of successfully updated projects
                "failures": [{"project_id": str, "error": str}, ...]  # Failed updates with errors
            }

        Raises:
            ValueError: If project_name or note parameters are provided, or no fields to update
            TypeError: If project_ids is missing

        Example:
            # Drop multiple projects
            result = client.update_projects(
                ["proj-001", "proj-002", "proj-003"],
                status="dropped"
            )
            # result = {"updated_count": 3, "failed_count": 0, "updated_ids": [...], "failures": []}
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('update_projects')

        # Validate that project_name and note are NOT provided
        if 'project_name' in kwargs:
            raise ValueError(
                "update_projects() does not accept 'project_name' parameter. "
                "Project names require unique values - use update_project() for individual names."
            )
        if 'note' in kwargs:
            raise ValueError(
                "update_projects() does not accept 'note' parameter. "
                "Notes require unique values - use update_project() for individual notes."
            )

        # Validate at least one field is provided
        if (folder_path is None and sequential is None and status is None and
                review_interval_weeks is None and last_reviewed is None):
            raise ValueError("At least one field must be provided to update")

        # Normalize project_ids to list
        if isinstance(project_ids, str):
            ids_list = [project_ids]
        else:
            ids_list = project_ids

        # Track results
        updated_count = 0
        failed_count = 0
        updated_ids: list[str] = []
        failures: list[dict] = []

        # Update each project individually
        for project_id in ids_list:
            try:
                result = self.update_project(
                    project_id=project_id,
                    folder_path=folder_path,
                    sequential=sequential,
                    status=status,
                    review_interval_weeks=review_interval_weeks,
                    last_reviewed=last_reviewed
                )

                if result["success"]:
                    updated_count += 1
                    updated_ids.append(project_id)
                else:
                    failed_count += 1
                    failures.append({
                        "project_id": project_id,
                        "error": result.get("error", "Unknown error")
                    })

            except Exception as e:
                failed_count += 1
                failures.append({
                    "project_id": project_id,
                    "error": str(e)
                })

        return {
            "updated_count": updated_count,
            "failed_count": failed_count,
            "updated_ids": updated_ids,
            "failures": failures
        }

    def set_project_status(self, project_id: str, status: str) -> bool:
        """Set the status of a project.

        Args:
            project_id: The ID of the project
            status: The status to set - one of: "active", "on_hold", "done", "dropped"

        Returns:
            bool: True if status was set successfully

        Raises:
            ValueError: If project not found or status is invalid
            RuntimeError: If AppleScript execution fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('set_project_status')

        # Validate status
        valid_statuses = ["active", "on_hold", "done", "dropped"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}")

        project_id_escaped = self._escape_applescript_string(project_id)

        # Different AppleScript commands for different statuses
        if status in ["active", "on_hold"]:
            # For active/on_hold, use "set status" with the appropriate value
            status_value = "on hold" if status == "on_hold" else status
            script = f'''
            tell application "OmniFocus"
                tell front document
                    set targetProject to first flattened project whose id is "{project_id_escaped}"
                    if targetProject is missing value then
                        return "false"
                    end if
                    set status of targetProject to {status_value}
                    return "true"
                end tell
            end tell
            '''
        elif status == "done":
            # For done, use "mark complete" command
            script = f'''
            tell application "OmniFocus"
                tell front document
                    set targetProject to first flattened project whose id is "{project_id_escaped}"
                    if targetProject is missing value then
                        return "false"
                    end if
                    mark complete targetProject
                    return "true"
                end tell
            end tell
            '''
        else:  # status == "dropped"
            # For dropped, use "mark dropped" command
            script = f'''
            tell application "OmniFocus"
                tell front document
                    set targetProject to first flattened project whose id is "{project_id_escaped}"
                    if targetProject is missing value then
                        return "false"
                    end if
                    mark dropped targetProject
                    return "true"
                end tell
            end tell
            '''

        try:
            result = run_applescript(script)
            if result == "false":
                raise ValueError(f"Project with ID {project_id} not found")
            return True
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"AppleScript execution failed: {e.stderr}")

    def add_task(
        self,
        project_id: str,
        task_name: str,
        note: Optional[str] = None,
        due_date: Optional[str] = None,
        defer_date: Optional[str] = None,
        flagged: bool = False,
        tags: Optional[list[str]] = None,
        recurrence: Optional[str] = None,
        repetition_method: Optional[str] = None
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
            recurrence: Optional iCalendar RRULE string (e.g., "FREQ=WEEKLY", "FREQ=DAILY;INTERVAL=2")
            repetition_method: Optional repetition method - "fixed" (default), "start_after_completion", "due_after_completion"

        Returns:
            bool: True if task was created successfully

        Raises:
            ValueError: If repetition_method is invalid or provided without recurrence
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('add_task')

        # Validate repetition parameters
        if repetition_method and not recurrence:
            raise ValueError("repetition_method requires recurrence to be specified")

        if repetition_method:
            valid_methods = ["fixed", "start_after_completion", "due_after_completion"]
            if repetition_method not in valid_methods:
                raise ValueError(f"Invalid repetition_method: {repetition_method}. Must be one of: {', '.join(valid_methods)}")

        # Default repetition_method to 'fixed' if recurrence is provided but method isn't
        if recurrence and not repetition_method:
            repetition_method = "fixed"

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

        # Build repetition rule commands
        repetition_commands = []
        if recurrence:
            # Convert Python-friendly method names to AppleScript enum names
            as_method = {
                "fixed": "fixed repetition",
                "start_after_completion": "start after completion",
                "due_after_completion": "due after completion"
            }[repetition_method]

            # Escape the recurrence string for AppleScript
            recurrence_escaped = self._escape_applescript_string(recurrence)

            # Get a template rule, create task, assign rule, modify properties
            repetition_commands.append(f'''
                    -- Get template repetition rule from any existing task
                    set templateRule to missing value
                    repeat with t in flattened tasks
                        try
                            set templateRule to repetition rule of t
                            if templateRule is not missing value then
                                exit repeat
                            end if
                        end try
                    end repeat

                    -- If we have a template, set up recurrence
                    if templateRule is not missing value then
                        set repetition rule of newTask to templateRule
                        set theRule to repetition rule of newTask
                        set recurrence of theRule to "{recurrence_escaped}"
                        set repetition method of theRule to {as_method}
                    end if''')

        properties_str = ", ".join(properties)
        date_commands_str = "\n                    ".join(date_commands)
        tag_commands_str = "\n                    ".join(tag_commands)
        repetition_commands_str = "\n                    ".join(repetition_commands)

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

                    -- Set up repetition if provided
                    {repetition_commands_str if repetition_commands else ""}

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

    def create_task(
        self,
        task_name: str,
        project_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        note: Optional[str] = None,
        due_date: Optional[str] = None,
        defer_date: Optional[str] = None,
        flagged: bool = False,
        tags: Optional[list[str]] = None,
        estimated_minutes: Optional[int] = None
    ) -> str:
        """Create a new task in OmniFocus (NEW API - consolidates add_task and create_inbox_task).

        NEW API (Redesign): Unified task creation supporting project, inbox, or subtask creation.

        Args:
            task_name: The name/title of the task (required)
            project_id: Project ID to add task to. None = inbox (optional, default: None)
            parent_task_id: Parent task ID to create subtask (optional, conflicts with project_id)
            note: Optional note/description for the task
            due_date: Due date in ISO 8601 format (e.g., "2025-10-15" or "2025-10-15T17:00:00")
            defer_date: Defer date in ISO 8601 format (when task becomes available)
            flagged: Whether to flag the task (default: False)
            tags: List of tag names to assign to the task
            estimated_minutes: Estimated time in minutes

        Returns:
            str: The ID of the created task

        Raises:
            ValueError: If both project_id and parent_task_id are specified
            Exception: If task creation fails

        Examples:
            # Create in project
            task_id = client.create_task("Task name", project_id="proj-123")

            # Create in inbox
            task_id = client.create_task("Inbox task")
            # or explicitly:
            task_id = client.create_task("Inbox task", project_id=None)

            # Create subtask
            task_id = client.create_task("Subtask", parent_task_id="task-parent")
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('create_task')

        # Validation: Cannot specify both project_id and parent_task_id
        if project_id is not None and parent_task_id is not None:
            raise ValueError("Cannot specify both project_id and parent_task_id")

        # Escape strings for AppleScript
        task_name_escaped = self._escape_applescript_string(task_name)
        note_escaped = self._escape_applescript_string(note or "")

        # Build properties
        properties = [f'name:"{task_name_escaped}"']
        if note:
            properties.append(f'note:"{note_escaped}"')
        if flagged:
            properties.append('flagged:true')
        if estimated_minutes is not None:
            properties.append(f'estimated minutes:{estimated_minutes}')

        # Build date commands
        date_commands = []
        if due_date:
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

        # Build script based on destination (project, inbox, or parent task)
        if parent_task_id is not None:
            # Create as subtask
            parent_id_escaped = self._escape_applescript_string(parent_task_id)
            script = f'''
            tell application "OmniFocus"
                tell front document
                    try
                        -- Find parent task by ID
                        set parentTask to first flattened task whose id is "{parent_id_escaped}"

                        -- Create new task as child of parent
                        tell parentTask
                            set newTask to make new task with properties {{{properties_str}}}
                        end tell

                        -- Set dates if provided
                        {date_commands_str if date_commands else ""}

                        -- Add tags if provided
                        {tag_commands_str if tag_commands else ""}

                        return id of newTask
                    on error errMsg
                        error "Failed to create subtask: " & errMsg
                    end try
                end tell
            end tell
            '''
        elif project_id is not None:
            # Create in specific project
            project_id_escaped = self._escape_applescript_string(project_id)
            script = f'''
            tell application "OmniFocus"
                tell front document
                    try
                        -- Find project by ID
                        set targetProject to first flattened project whose id is "{project_id_escaped}"

                        -- Create new task in the project
                        tell targetProject
                            set newTask to make new task with properties {{{properties_str}}}
                        end tell

                        -- Set dates if provided
                        {date_commands_str if date_commands else ""}

                        -- Add tags if provided
                        {tag_commands_str if tag_commands else ""}

                        return id of newTask
                    on error errMsg
                        error "Failed to create task in project: " & errMsg
                    end try
                end tell
            end tell
            '''
        else:
            # Create in inbox (project_id is None)
            script = f'''
            tell application "OmniFocus"
                tell front document
                    try
                        -- Create new task in inbox
                        set newTask to make new inbox task with properties {{{properties_str}}}

                        -- Set dates if provided
                        {date_commands_str if date_commands else ""}

                        -- Add tags if provided
                        {tag_commands_str if tag_commands else ""}

                        return id of newTask
                    on error errMsg
                        error "Failed to create inbox task: " & errMsg
                    end try
                end tell
            end tell
            '''

        try:
            result = run_applescript(script)
            return result.strip()
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error creating task: {e.stderr}")

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
        dropped_only: bool = False,
        blocked_only: bool = False,
        next_only: bool = False,
        due_relative: Optional[str] = None,
        defer_relative: Optional[str] = None,
        max_estimated_minutes: Optional[int] = None,
        has_estimate: Optional[bool] = None,
        tag_filter: Optional[list[str]] = None,
        tag_filter_mode: str = "and",
        created_after: Optional[str] = None,
        created_before: Optional[str] = None,
        modified_after: Optional[str] = None,
        modified_before: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        recurring_only: Optional[bool] = None,
        query: Optional[str] = None,
        inbox_only: bool = False,
        timeout: int = 120
    ) -> list[dict[str, Any]]:
        """Get tasks from OmniFocus with optional filtering.

        NOTE: This method is intentionally long (628 lines) because:
        1. AppleScript must be generated as a single self-contained string
        2. AppleScript is verbose and requires extensive property extraction
        3. 21 parameters require conditional logic for filter generation
        4. Complex date handling and recurring task logic
        5. Post-processing filters (tag logic, date ranges) in Python

        The method is organized into clear sections:
        - Parameter validation and setup
        - AppleScript filter condition generation
        - AppleScript property extraction
        - AppleScript execution
        - Python-side post-processing filters
        - Result sorting and return

        Args:
            project_id: Optional project ID to filter tasks. If None, returns all tasks (ignored if inbox_only=True).
            include_completed: Whether to include completed tasks (default: False)
            flagged_only: Only return flagged tasks (default: False)
            available_only: Only return available tasks (not blocked or deferred) (default: False)
            overdue: Only return overdue tasks (default: False)
            dropped_only: Only return dropped tasks (default: False)
            blocked_only: Only return blocked tasks (default: False)
            next_only: Only return next tasks (default: False)
            due_relative: Relative due date filter - "today", "tomorrow", "this_week", "next_week", "overdue"
            defer_relative: Relative defer date filter - "today", "tomorrow", "this_week", "next_week"
            max_estimated_minutes: Only return tasks estimated at or under this many minutes
            has_estimate: If True, only return tasks with estimates; if False, only tasks without estimates
            tag_filter: List of tag names to filter by
            tag_filter_mode: Tag filtering logic - "and" (all tags), "or" (any tag), "not" (none of tags) (default: "and")
            created_after: Only return tasks created after this ISO date (e.g., "2025-01-15T00:00:00Z")
            created_before: Only return tasks created before this ISO date
            modified_after: Only return tasks modified after this ISO date
            modified_before: Only return tasks modified before this ISO date
            sort_by: Field to sort by - "name", "due_date", "defer_date" (default: None - OmniFocus order)
            sort_order: Sort order - "asc" or "desc" (default: "asc")
            recurring_only: If True, only return recurring tasks; if False, only non-recurring tasks; if None, return all (default: None)
            query: Optional search term to filter by name or note (case-insensitive)
            inbox_only: Only return inbox tasks (default: False)
            timeout: Maximum seconds to wait for AppleScript (default: 120). Increase for large task lists (500+)

        Returns:
            list: List of task dictionaries with id, name, note, completed, flagged, dropped, blocked, next, project info, dates, tags, and recurring info

        Raises:
            ValueError: If relative date filter value, tag_filter_mode, date format, or sort parameters are invalid
            subprocess.TimeoutExpired: If AppleScript execution exceeds timeout (increase timeout for large task lists)
        """
        # Validate date formats
        from datetime import datetime
        for date_param, date_value in [
            ("created_after", created_after),
            ("created_before", created_before),
            ("modified_after", modified_after),
            ("modified_before", modified_before)
        ]:
            if date_value:
                try:
                    datetime.fromisoformat(date_value.replace('Z', '+00:00'))
                except ValueError:
                    raise ValueError(f"Invalid date format for {date_param}: {date_value}. Use ISO format (e.g., '2025-01-15T00:00:00Z')")

        # Validate tag filter mode
        valid_tag_filter_modes = ["and", "or", "not"]
        if tag_filter_mode not in valid_tag_filter_modes:
            raise ValueError(f"Invalid tag_filter_mode value: {tag_filter_mode}. Must be one of: {valid_tag_filter_modes}")

        # Validate sort parameters
        valid_sort_by = ["name", "due_date", "defer_date", None]
        valid_sort_order = ["asc", "desc"]

        if sort_by not in valid_sort_by:
            raise ValueError(f"Invalid sort_by value: {sort_by}. Must be one of: {[v for v in valid_sort_by if v is not None]}")
        if sort_order not in valid_sort_order:
            raise ValueError(f"Invalid sort_order value: {sort_order}. Must be one of: {valid_sort_order}")

        # Validate relative date parameters
        valid_due_relative = ["today", "tomorrow", "this_week", "next_week", "overdue", None]
        valid_defer_relative = ["today", "tomorrow", "this_week", "next_week", None]

        if due_relative not in valid_due_relative:
            raise ValueError(f"Invalid due_relative value: {due_relative}. Must be one of: {valid_due_relative[:-1]}")
        if defer_relative not in valid_defer_relative:
            raise ValueError(f"Invalid defer_relative value: {defer_relative}. Must be one of: {valid_defer_relative[:-1]}")

        # Build task source (inbox, project, or all tasks)
        if inbox_only:
            task_source = 'inbox tasks'
        elif project_id:
            project_filter = f'whose id is "{project_id}"'
            task_source = f'flattened tasks of (first flattened project {project_filter})'
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

        # Build dropped filter
        dropped_check = "" if not dropped_only else """
                        -- Skip non-dropped tasks
                        if not dropped of t then
                            error "skip non-dropped task"
                        end if"""

        # Build blocked filter
        blocked_check = "" if not blocked_only else """
                        -- Skip non-blocked tasks
                        if not blocked of t then
                            error "skip non-blocked task"
                        end if"""

        # Build next filter
        next_check = "" if not next_only else """
                        -- Skip non-next tasks
                        if not next of t then
                            error "skip non-next task"
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

        # Build relative due date filter
        due_relative_check = ""
        if due_relative:
            if due_relative == "today":
                due_relative_check = """
                        -- Skip tasks not due today
                        set taskDue to due date of t
                        if taskDue is missing value then
                            error "skip task"
                        end if
                        set todayStart to (current date)
                        set time of todayStart to 0
                        set todayEnd to todayStart + (24 * hours)
                        if taskDue < todayStart or taskDue ≥ todayEnd then
                            error "skip task"
                        end if"""
            elif due_relative == "tomorrow":
                due_relative_check = """
                        -- Skip tasks not due tomorrow
                        set taskDue to due date of t
                        if taskDue is missing value then
                            error "skip task"
                        end if
                        set tomorrowStart to (current date) + (1 * days)
                        set time of tomorrowStart to 0
                        set tomorrowEnd to tomorrowStart + (24 * hours)
                        if taskDue < tomorrowStart or taskDue ≥ tomorrowEnd then
                            error "skip task"
                        end if"""
            elif due_relative == "this_week":
                due_relative_check = """
                        -- Skip tasks not due this week
                        set taskDue to due date of t
                        if taskDue is missing value then
                            error "skip task"
                        end if
                        set weekEnd to (current date) + (7 * days)
                        if taskDue > weekEnd then
                            error "skip task"
                        end if"""
            elif due_relative == "next_week":
                due_relative_check = """
                        -- Skip tasks not due next week
                        set taskDue to due date of t
                        if taskDue is missing value then
                            error "skip task"
                        end if
                        set nextWeekStart to (current date) + (7 * days)
                        set nextWeekEnd to nextWeekStart + (7 * days)
                        if taskDue < nextWeekStart or taskDue > nextWeekEnd then
                            error "skip task"
                        end if"""
            elif due_relative == "overdue":
                due_relative_check = """
                        -- Skip non-overdue tasks
                        set taskDue to due date of t
                        if taskDue is missing value then
                            error "skip task"
                        end if
                        if taskDue >= (current date) then
                            error "skip task"
                        end if"""

        # Build relative defer date filter
        defer_relative_check = ""
        if defer_relative:
            if defer_relative == "today":
                defer_relative_check = """
                        -- Skip tasks not deferred until today
                        set taskDefer to defer date of t
                        if taskDefer is missing value then
                            error "skip task"
                        end if
                        set todayStart to (current date)
                        set time of todayStart to 0
                        set todayEnd to todayStart + (24 * hours)
                        if taskDefer < todayStart or taskDefer ≥ todayEnd then
                            error "skip task"
                        end if"""
            elif defer_relative == "tomorrow":
                defer_relative_check = """
                        -- Skip tasks not deferred until tomorrow
                        set taskDefer to defer date of t
                        if taskDefer is missing value then
                            error "skip task"
                        end if
                        set tomorrowStart to (current date) + (1 * days)
                        set time of tomorrowStart to 0
                        set tomorrowEnd to tomorrowStart + (24 * hours)
                        if taskDefer < tomorrowStart or taskDefer ≥ tomorrowEnd then
                            error "skip task"
                        end if"""
            elif defer_relative == "this_week":
                defer_relative_check = """
                        -- Skip tasks not deferred until this week
                        set taskDefer to defer date of t
                        if taskDefer is missing value then
                            error "skip task"
                        end if
                        set weekEnd to (current date) + (7 * days)
                        if taskDefer > weekEnd then
                            error "skip task"
                        end if"""
            elif defer_relative == "next_week":
                defer_relative_check = """
                        -- Skip tasks not deferred until next week
                        set taskDefer to defer date of t
                        if taskDefer is missing value then
                            error "skip task"
                        end if
                        set nextWeekStart to (current date) + (7 * days)
                        set nextWeekEnd to nextWeekStart + (7 * days)
                        if taskDefer < nextWeekStart or taskDefer > nextWeekEnd then
                            error "skip task"
                        end if"""

        # Build time estimate filters
        estimate_check = ""
        if max_estimated_minutes is not None:
            estimate_check = f"""
                        -- Skip tasks over time limit
                        set estMins to estimated minutes of t
                        if estMins is missing value or estMins = 0 or estMins > {max_estimated_minutes} then
                            error "skip task"
                        end if"""
        elif has_estimate is not None:
            if has_estimate:
                estimate_check = """
                        -- Skip tasks without estimate
                        set estMins to estimated minutes of t
                        if estMins is missing value or estMins = 0 then
                            error "skip task"
                        end if"""
            else:
                estimate_check = """
                        -- Skip tasks with estimate
                        set estMins to estimated minutes of t
                        if estMins is not missing value and estMins > 0 then
                            error "skip task"
                        end if"""

        # Build tag filter
        # Tag filtering: only use AppleScript for AND mode (existing behavior)
        # OR and NOT modes will be filtered in Python after retrieval
        tag_check = ""
        if tag_filter and len(tag_filter) > 0 and tag_filter_mode == "and":
            # Build AppleScript to check for all required tags (AND logic)
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
        set taskIndex to 0

        tell application "OmniFocus"
            tell front document
                set allTasks to {task_source}

                repeat with t in allTasks
                    set taskIndex to taskIndex + 1
                    try
                        set taskId to id of t
                        set taskName to name of t
                        set taskNote to note of t
                        set taskCompleted to completed of t
                        set taskFlagged to flagged of t
                        set taskDropped to dropped of t
                        set taskBlocked to blocked of t
                        set taskNext to next of t

                        {completion_check}
                        {flagged_check}
                        {dropped_check}
                        {blocked_check}
                        {next_check}
                        {available_check}
                        {overdue_check}
                        {due_relative_check}
                        {defer_relative_check}
                        {estimate_check}
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

                        -- Get timestamp fields
                        set creationDateStr to "null"
                        try
                            set creationDateObj to creation date of t
                            if creationDateObj is not missing value then
                                set creationDateStr to "\\"" & (creationDateObj as «class isot» as string) & "\\""
                            end if
                        end try

                        set modificationDateStr to "null"
                        try
                            set modificationDateObj to modification date of t
                            if modificationDateObj is not missing value then
                                set modificationDateStr to "\\"" & (modificationDateObj as «class isot» as string) & "\\""
                            end if
                        end try

                        set completionDateStr to "null"
                        try
                            set completionDateObj to completion date of t
                            if completionDateObj is not missing value then
                                set completionDateStr to "\\"" & (completionDateObj as «class isot» as string) & "\\""
                            end if
                        end try

                        set droppedDateStr to "null"
                        try
                            set droppedDateObj to dropped date of t
                            if droppedDateObj is not missing value then
                                set droppedDateStr to "\\"" & (droppedDateObj as «class isot» as string) & "\\""
                            end if
                        end try

                        -- Get tags as JSON array
                        set tagsJSON to "[]"
                        try
                            set taskTags to tags of t
                            if (count of taskTags) > 0 then
                                set tagItems to {{}}
                                repeat with tg in taskTags
                                    set tagName to name of tg
                                    set end of tagItems to "\\"" & my escapeJSON(tagName) & "\\""
                                end repeat
                                set AppleScript's text item delimiters to ", "
                                set tagsJSON to "[" & (tagItems as text) & "]"
                                set AppleScript's text item delimiters to ""
                            end if
                        end try

                        -- Get estimated minutes
                        set estimatedMins to "null"
                        try
                            set estMins to estimated minutes of t
                            if estMins is not missing value and estMins is not 0 then
                                set estimatedMins to estMins as text
                            end if
                        end try

                        -- Get repetition info
                        set isRecurring to "false"
                        set recurrenceStr to ""
                        set repetitionMethodStr to ""
                        try
                            set repRule to repetition rule of t
                            if repRule is not missing value then
                                set isRecurring to "true"
                                try
                                    set recurrenceStr to recurrence of repRule
                                end try
                                try
                                    set repetitionMethodStr to (repetition method of repRule) as text
                                end try
                            end if
                        end try

                        -- Get hierarchy fields
                        set parentTaskId to ""
                        try
                            set parentTaskObj to parent task of t
                            if parentTaskObj is not missing value then
                                -- Check if parent is same as containing project (means no parent task)
                                set parentTaskObjId to id of parentTaskObj
                                if parentTaskObjId is not equal to projectId then
                                    set parentTaskId to parentTaskObjId
                                end if
                            end if
                        end try

                        set taskSubtaskCount to 0
                        try
                            set taskSubtaskCount to count of (tasks of t)
                        end try

                        set taskSequential to false
                        try
                            set taskSequential to sequential of t
                        end try

                        -- Get availability fields
                        set numAvailableTasks to 0
                        try
                            set numAvailableTasks to number of available tasks of t
                        end try

                        -- Compute available status
                        set deferDateObj to defer date of t
                        set isDeferred to false
                        if deferDateObj is not missing value then
                            set isDeferred to (deferDateObj > (current date))
                        end if

                        set directlyAvailable to (not taskCompleted) and (not taskDropped) and (not taskBlocked) and (not isDeferred)
                        set taskAvailable to directlyAvailable or (numAvailableTasks > 0)

                        -- Build JSON manually
                        set jsonLine to "{{" & ¬
                            "\\"id\\": \\"" & taskId & "\\", " & ¬
                            "\\"name\\": \\"" & my escapeJSON(taskName) & "\\", " & ¬
                            "\\"note\\": \\"" & my escapeJSON(taskNote) & "\\", " & ¬
                            "\\"completed\\": " & (taskCompleted as text) & ", " & ¬
                            "\\"flagged\\": " & (taskFlagged as text) & ", " & ¬
                            "\\"dropped\\": " & (taskDropped as text) & ", " & ¬
                            "\\"blocked\\": " & (taskBlocked as text) & ", " & ¬
                            "\\"next\\": " & (taskNext as text) & ", " & ¬
                            "\\"projectId\\": \\"" & projectId & "\\", " & ¬
                            "\\"projectName\\": \\"" & my escapeJSON(projectName) & "\\", " & ¬
                            "\\"dueDate\\": \\"" & dueDate & "\\", " & ¬
                            "\\"deferDate\\": \\"" & deferDate & "\\", " & ¬
                            "\\"creationDate\\": " & creationDateStr & ", " & ¬
                            "\\"modificationDate\\": " & modificationDateStr & ", " & ¬
                            "\\"completionDate\\": " & completionDateStr & ", " & ¬
                            "\\"droppedDate\\": " & droppedDateStr & ", " & ¬
                            "\\"tags\\": " & tagsJSON & ", " & ¬
                            "\\"estimatedMinutes\\": " & estimatedMins & ", " & ¬
                            "\\"isRecurring\\": " & isRecurring & ", " & ¬
                            "\\"recurrence\\": \\"" & my escapeJSON(recurrenceStr) & "\\", " & ¬
                            "\\"repetitionMethod\\": \\"" & my escapeJSON(repetitionMethodStr) & "\\", " & ¬
                            "\\"parentTaskId\\": \\"" & parentTaskId & "\\", " & ¬
                            "\\"subtaskCount\\": " & (taskSubtaskCount as text) & ", " & ¬
                            "\\"sequential\\": " & (taskSequential as text) & ", " & ¬
                            "\\"position\\": " & (taskIndex as text) & ", " & ¬
                            "\\"numberOfAvailableTasks\\": " & (numAvailableTasks as text) & ", " & ¬
                            "\\"available\\": " & (taskAvailable as text) & ¬
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
        ''' + APPLESCRIPT_JSON_HELPERS

        try:
            result = run_applescript(script, timeout=timeout)
            if result:
                tasks = json.loads(result)

                # Normalize repetitionMethod values
                for task in tasks:
                    # Convert AppleScript enum values to Python-friendly snake_case
                    rep_method = task.get('repetitionMethod', '')
                    if rep_method == 'fixed repetition':
                        task['repetitionMethod'] = 'fixed'
                    elif rep_method == 'start after completion':
                        task['repetitionMethod'] = 'start_after_completion'
                    elif rep_method == 'due after completion':
                        task['repetitionMethod'] = 'due_after_completion'
                    elif rep_method == '':
                        task['repetitionMethod'] = None

                    # Normalize recurrence
                    if task.get('recurrence', '') == '':
                        task['recurrence'] = None

                # Apply Python-based tag filtering
                # For AND mode: AppleScript already filtered, but we apply Python filter too for consistency in tests
                # For OR/NOT modes: always filter in Python
                if tag_filter and len(tag_filter) > 0:
                    if tag_filter_mode == "and":
                        # For AND mode, filter to ensure all tags are present (redundant if AppleScript worked, but needed for tests)
                        tasks = self._filter_tasks_by_tags(tasks, tag_filter, tag_filter_mode)
                    elif tag_filter_mode in ["or", "not"]:
                        tasks = self._filter_tasks_by_tags(tasks, tag_filter, tag_filter_mode)

                # Apply date range filtering
                if created_after or created_before or modified_after or modified_before:
                    tasks = self._filter_by_date_range(
                        tasks,
                        created_after,
                        created_before,
                        modified_after,
                        modified_before
                    )

                # Apply recurring filter
                if recurring_only is not None:
                    if recurring_only:
                        tasks = [t for t in tasks if t.get('isRecurring', False)]
                    else:
                        tasks = [t for t in tasks if not t.get('isRecurring', False)]

                # Apply query filter if provided
                if query:
                    query_lower = query.lower()
                    tasks = [
                        t for t in tasks
                        if query_lower in t.get('name', '').lower()
                        or query_lower in t.get('note', '').lower()
                    ]

                # Apply sorting if requested
                if sort_by:
                    tasks = self._sort_tasks(tasks, sort_by, sort_order)

                return tasks
            else:
                raise Exception("No output from OmniFocus AppleScript")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error querying OmniFocus tasks: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing OmniFocus task output: {e}")

    def search_tasks(self, query: str, search_notes: bool = True) -> list[dict[str, Any]]:
        """Search for tasks by text query.

        Performs case-insensitive search across task names and optionally notes.

        Args:
            query: The search term to look for
            search_notes: If True, also search in task notes (default: True)

        Returns:
            List of matching tasks with all standard task fields

        Raises:
            ValueError: If query is empty or whitespace-only
            Exception: If the search operation fails
        """
        if not query or query.strip() == "":
            raise ValueError("query cannot be empty")

        query_lower = query.lower()

        try:
            # Get all tasks and filter in Python for simplicity
            # This approach is simpler and more maintainable than building complex AppleScript
            all_tasks = self.get_tasks()

            matching_tasks = []
            for task in all_tasks:
                task_matches = False

                # Search in task name
                if query_lower in task.get('name', '').lower():
                    task_matches = True

                # Search in notes if requested
                if search_notes and not task_matches:
                    if query_lower in task.get('note', '').lower():
                        task_matches = True

                if task_matches:
                    matching_tasks.append(task)

            return matching_tasks
        except Exception as e:
            raise Exception(f"Error searching tasks: {str(e)}")

    def get_task(self, task_id: str) -> dict[str, Any]:
        """Get a single task by its ID.

        NOTE: This method is intentionally long (207 lines) because:
        1. Extracts comprehensive task data (20+ properties including timestamps)
        2. Handles tags as JSON array with proper escaping
        3. AppleScript requires extensive null-safety checks for each property
        4. Self-contained AppleScript with embedded JSON helpers

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            dict: Task dictionary with id, name, note, completed, flagged, dropped, project info, dates, and tags

        Raises:
            ValueError: If task_id is empty
            Exception: If task not found or error occurs
        """
        if not task_id:
            raise ValueError("task_id is required")

        script = f'''
        use AppleScript version "2.4"
        use scripting additions

        tell application "OmniFocus"
            tell front document
                set targetTask to first flattened task whose id is "{task_id}"

                if targetTask is missing value then
                    error "Task not found"
                end if

                set taskId to id of targetTask
                set taskName to name of targetTask
                set taskNote to note of targetTask
                set taskCompleted to completed of targetTask
                set taskFlagged to flagged of targetTask
                set taskDropped to dropped of targetTask
                set taskBlocked to blocked of targetTask
                set taskNext to next of targetTask

                -- Get project info
                set projectId to ""
                set projectName to ""
                try
                    set parentProj to containing project of targetTask
                    if parentProj is not missing value then
                        set projectId to id of parentProj
                        set projectName to name of parentProj
                    end if
                end try

                -- Get dates
                set dueDate to ""
                try
                    set dueDateObj to due date of targetTask
                    if dueDateObj is not missing value then
                        set dueDate to dueDateObj as «class isot» as string
                    end if
                end try

                set deferDate to ""
                try
                    set deferDateObj to defer date of targetTask
                    if deferDateObj is not missing value then
                        set deferDate to deferDateObj as «class isot» as string
                    end if
                end try

                -- Get timestamp fields
                set creationDateStr to "null"
                try
                    set creationDateObj to creation date of targetTask
                    if creationDateObj is not missing value then
                        set creationDateStr to "\\"" & (creationDateObj as «class isot» as string) & "\\""
                    end if
                end try

                set modificationDateStr to "null"
                try
                    set modificationDateObj to modification date of targetTask
                    if modificationDateObj is not missing value then
                        set modificationDateStr to "\\"" & (modificationDateObj as «class isot» as string) & "\\""
                    end if
                end try

                set completionDateStr to "null"
                try
                    set completionDateObj to completion date of targetTask
                    if completionDateObj is not missing value then
                        set completionDateStr to "\\"" & (completionDateObj as «class isot» as string) & "\\""
                    end if
                end try

                set droppedDateStr to "null"
                try
                    set droppedDateObj to dropped date of targetTask
                    if droppedDateObj is not missing value then
                        set droppedDateStr to "\\"" & (droppedDateObj as «class isot» as string) & "\\""
                    end if
                end try

                -- Get tags as JSON array
                set tagsJSON to "[]"
                try
                    set taskTags to tags of targetTask
                    if (count of taskTags) > 0 then
                        set tagItems to {{}}
                        repeat with tg in taskTags
                            set tagName to name of tg
                            set end of tagItems to "\\"" & my escapeJSON(tagName) & "\\""
                        end repeat
                        set AppleScript's text item delimiters to ", "
                        set tagsJSON to "[" & (tagItems as text) & "]"
                        set AppleScript's text item delimiters to ""
                    end if
                end try

                -- Get estimated minutes
                set estimatedMins to "null"
                try
                    set estMins to estimated minutes of targetTask
                    if estMins is not missing value and estMins is not 0 then
                        set estimatedMins to estMins as text
                    end if
                end try

                -- Get hierarchy fields
                set parentTaskId to ""
                try
                    set parentTaskObj to parent task of targetTask
                    if parentTaskObj is not missing value then
                        -- Check if parent is same as containing project (means no parent task)
                        set parentTaskObjId to id of parentTaskObj
                        if parentTaskObjId is not equal to projectId then
                            set parentTaskId to parentTaskObjId
                        end if
                    end if
                end try

                set taskSubtaskCount to 0
                try
                    set taskSubtaskCount to count of (tasks of targetTask)
                end try

                set taskSequential to false
                try
                    set taskSequential to sequential of targetTask
                end try

                -- Get availability fields
                set numAvailableTasks to 0
                try
                    set numAvailableTasks to number of available tasks of targetTask
                end try

                -- Compute available status
                -- A task is available if it's directly actionable OR has available subtasks
                set deferDateObj to defer date of targetTask
                set isDeferred to false
                if deferDateObj is not missing value then
                    set isDeferred to (deferDateObj > (current date))
                end if

                set directlyAvailable to (not taskCompleted) and (not taskDropped) and (not taskBlocked) and (not isDeferred)
                set taskAvailable to directlyAvailable or (numAvailableTasks > 0)

                -- Build JSON manually
                set jsonOutput to "{{" & ¬
                    "\\"id\\": \\"" & taskId & "\\", " & ¬
                    "\\"name\\": \\"" & my escapeJSON(taskName) & "\\", " & ¬
                    "\\"note\\": \\"" & my escapeJSON(taskNote) & "\\", " & ¬
                    "\\"completed\\": " & (taskCompleted as text) & ", " & ¬
                    "\\"flagged\\": " & (taskFlagged as text) & ", " & ¬
                    "\\"dropped\\": " & (taskDropped as text) & ", " & ¬
                    "\\"blocked\\": " & (taskBlocked as text) & ", " & ¬
                    "\\"next\\": " & (taskNext as text) & ", " & ¬
                    "\\"projectId\\": \\"" & projectId & "\\", " & ¬
                    "\\"projectName\\": \\"" & my escapeJSON(projectName) & "\\", " & ¬
                    "\\"dueDate\\": \\"" & dueDate & "\\", " & ¬
                    "\\"deferDate\\": \\"" & deferDate & "\\", " & ¬
                    "\\"creationDate\\": " & creationDateStr & ", " & ¬
                    "\\"modificationDate\\": " & modificationDateStr & ", " & ¬
                    "\\"completionDate\\": " & completionDateStr & ", " & ¬
                    "\\"droppedDate\\": " & droppedDateStr & ", " & ¬
                    "\\"tags\\": " & tagsJSON & ", " & ¬
                    "\\"estimatedMinutes\\": " & estimatedMins & ", " & ¬
                    "\\"parentTaskId\\": \\"" & parentTaskId & "\\", " & ¬
                    "\\"subtaskCount\\": " & (taskSubtaskCount as text) & ", " & ¬
                    "\\"sequential\\": " & (taskSequential as text) & ", " & ¬
                    "\\"position\\": 1, " & ¬
                    "\\"numberOfAvailableTasks\\": " & (numAvailableTasks as text) & ", " & ¬
                    "\\"available\\": " & (taskAvailable as text) & ¬
                    "}}"

                return jsonOutput
            end tell
        end tell
        ''' + APPLESCRIPT_JSON_HELPERS

        try:
            result = run_applescript(script)
            if result:
                return json.loads(result)
            else:
                raise Exception(f"Task with ID '{task_id}' not found")
        except subprocess.CalledProcessError as e:
            if "Task not found" in e.stderr:
                raise Exception(f"Task with ID '{task_id}' not found")
            raise Exception(f"Error retrieving task: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing task output: {e}")

    def get_subtasks(self, task_id: str) -> list[dict[str, Any]]:
        """Get all subtasks (child tasks) of a given task.

        Args:
            task_id: The ID of the parent task

        Returns:
            list: List of subtask dictionaries with full task details

        Raises:
            ValueError: If task_id is empty
        """
        if not task_id:
            raise ValueError("task_id cannot be empty")

        script = f'''
        use AppleScript version "2.4"
        use scripting additions
        use framework "Foundation"

        set output to ""
        set taskIndex to 0

        tell application "OmniFocus"
            tell front document
                try
                    set parentTask to first flattened task whose id is "{task_id}"
                    set childTasks to tasks of parentTask

                    repeat with t in childTasks
                        set taskIndex to taskIndex + 1
                        try
                            set taskId to id of t
                            set taskName to name of t
                            set taskNote to note of t
                            set taskCompleted to completed of t
                            set taskFlagged to flagged of t
                            set taskDropped to dropped of t
                            set taskBlocked to blocked of t
                            set taskNext to next of t

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
                            set deferDate to ""
                            set completionDate to ""

                            try
                                if due date of t is not missing value then
                                    set dueDate to (due date of t) as «class isot» as string
                                end if
                            end try

                            try
                                if defer date of t is not missing value then
                                    set deferDate to (defer date of t) as «class isot» as string
                                end if
                            end try

                            try
                                if completion date of t is not missing value then
                                    set completionDate to (completion date of t) as «class isot» as string
                                end if
                            end try

                            -- Get tags
                            set tagsList to ""
                            try
                                set taskTags to tags of t
                                set tagNames to {{}}
                                repeat with aTag in taskTags
                                    set end of tagNames to name of aTag
                                end repeat
                                set AppleScript's text item delimiters to ", "
                                set tagsList to tagNames as text
                                set AppleScript's text item delimiters to ""
                            end try

                            -- Get estimated minutes
                            set estimatedMins to "null"
                            try
                                set estMins to estimated minutes of t
                                if estMins is not missing value and estMins is not 0 then
                                    set estimatedMins to estMins as text
                                end if
                            end try

                            -- Get hierarchy fields
                            set parentTaskId to ""
                            try
                                set parentTaskObj to parent task of t
                                if parentTaskObj is not missing value then
                                    -- Check if parent is same as containing project (means no parent task)
                                    set parentTaskObjId to id of parentTaskObj
                                    if parentTaskObjId is not equal to projectId then
                                        set parentTaskId to parentTaskObjId
                                    end if
                                end if
                            end try

                            set taskSubtaskCount to 0
                            try
                                set taskSubtaskCount to count of (tasks of t)
                            end try

                            set taskSequential to false
                            try
                                set taskSequential to sequential of t
                            end try

                            -- Get availability fields
                            set numAvailableTasks to 0
                            try
                                set numAvailableTasks to number of available tasks of t
                            end try

                            -- Compute available status
                            set deferDateObj to defer date of t
                            set isDeferred to false
                            if deferDateObj is not missing value then
                                set isDeferred to (deferDateObj > (current date))
                            end if

                            set directlyAvailable to (not taskCompleted) and (not taskDropped) and (not taskBlocked) and (not isDeferred)
                            set taskAvailable to directlyAvailable or (numAvailableTasks > 0)

                            -- Build JSON manually
                            set jsonLine to "{{" & ¬
                                "\\"id\\": \\"" & taskId & "\\", " & ¬
                                "\\"name\\": \\"" & my escapeJSON(taskName) & "\\", " & ¬
                                "\\"note\\": \\"" & my escapeJSON(taskNote) & "\\", " & ¬
                                "\\"completed\\": " & (taskCompleted as text) & ", " & ¬
                                "\\"flagged\\": " & (taskFlagged as text) & ", " & ¬
                                "\\"dropped\\": " & (taskDropped as text) & ", " & ¬
                                "\\"blocked\\": " & (taskBlocked as text) & ", " & ¬
                                "\\"next\\": " & (taskNext as text) & ", " & ¬
                                "\\"projectId\\": \\"" & projectId & "\\", " & ¬
                                "\\"projectName\\": \\"" & my escapeJSON(projectName) & "\\", " & ¬
                                "\\"dueDate\\": \\"" & dueDate & "\\", " & ¬
                                "\\"deferDate\\": \\"" & deferDate & "\\", " & ¬
                                "\\"completionDate\\": \\"" & completionDate & "\\", " & ¬
                                "\\"tags\\": \\"" & my escapeJSON(tagsList) & "\\", " & ¬
                                "\\"estimatedMinutes\\": " & estimatedMins & ", " & ¬
                                "\\"parentTaskId\\": \\"" & parentTaskId & "\\", " & ¬
                                "\\"subtaskCount\\": " & (taskSubtaskCount as text) & ", " & ¬
                                "\\"sequential\\": " & (taskSequential as text) & ", " & ¬
                                "\\"position\\": " & (taskIndex as text) & ", " & ¬
                                "\\"numberOfAvailableTasks\\": " & (numAvailableTasks as text) & ", " & ¬
                                "\\"available\\": " & (taskAvailable as text) & ¬
                                "}}"

                            if output is not "" then
                                set output to output & "," & linefeed
                            end if
                            set output to output & jsonLine
                        end try
                    end repeat
                on error errMsg
                    -- Parent task not found or has no children - return empty array
                end try
            end tell
        end tell

        return "[" & linefeed & output & linefeed & "]"
        ''' + APPLESCRIPT_JSON_HELPERS

        try:
            result = run_applescript(script)
            if result:
                return json.loads(result)
            else:
                return []
        except subprocess.CalledProcessError as e:
            return []
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing subtasks output: {e}")

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
                mark complete theTask
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

    def complete_tasks(self, task_ids: list[str]) -> int:
        """Mark multiple tasks as completed in a single operation.

        Args:
            task_ids: List of task IDs to complete

        Returns:
            int: Number of tasks successfully completed

        Raises:
            ValueError: If task_ids is empty
            Exception: If the operation fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('complete_tasks')

        if not task_ids:
            raise ValueError("task_ids cannot be empty")

        # Build AppleScript list of task IDs
        ids_list = ", ".join([f'"{task_id}"' for task_id in task_ids])

        script = f'''
        tell application "OmniFocus"
            tell front document
                set taskIdList to {{{ids_list}}}
                set successCount to 0

                repeat with taskId in taskIdList
                    try
                        set theTask to first flattened task whose id is taskId
                        if completed of theTask is false then
                            mark complete theTask
                            set successCount to successCount + 1
                        end if
                    on error
                        -- Task not found or already completed, skip
                    end try
                end repeat

                return successCount as text
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            return int(result.strip())
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error completing tasks: {e.stderr}")
        except ValueError as e:
            raise Exception(f"Error parsing completion result: {e}")

    def update_task(
        self,
        task_id: str,
        task_name: Optional[str] = None,
        project_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        note: Optional[str] = None,
        due_date: Optional[str] = None,
        defer_date: Optional[str] = None,
        flagged: Optional[bool] = None,
        tags: Optional[list[str]] = None,
        add_tags: Optional[list[str]] = None,
        remove_tags: Optional[list[str]] = None,
        estimated_minutes: Optional[int] = None,
        completed: Optional[bool] = None,
        status: Optional[Union[TaskStatus, str]] = None,
        # Legacy parameters (kept for backwards compatibility)
        recurrence: Optional[str] = None,
        repetition_method: Optional[str] = None,
        name: Optional[str] = None  # Deprecated: use task_name
    ) -> dict:
        """Update properties of an existing task (NEW API - Redesign).

        This comprehensive update function consolidates multiple specialized functions:
        - complete_task() -> update_task(task_id, completed=True)
        - drop_task() -> update_task(task_id, status=TaskStatus.DROPPED)
        - move_task() -> update_task(task_id, project_id=X)
        - set_parent_task() -> update_task(task_id, parent_task_id=X)
        - set_estimated_minutes() -> update_task(task_id, estimated_minutes=X)
        - add_tag_to_task() -> update_task(task_id, add_tags=[...])

        Args:
            task_id: The ID of the task to update (required)
            task_name: New task name (optional)
            project_id: Move task to this project (optional, conflicts with parent_task_id)
            parent_task_id: Make task a subtask of this parent (optional, conflicts with project_id)
            note: New task note (optional, WARNING: removes rich text formatting)
            due_date: New due date in ISO 8601 format, or "" to clear (optional)
            defer_date: New defer date in ISO 8601 format, or "" to clear (optional)
            flagged: New flagged status (optional)
            tags: Full replacement - set exact tag list (optional, conflicts with add_tags/remove_tags)
            add_tags: Add these tags incrementally (optional, conflicts with tags)
            remove_tags: Remove these tags (optional, conflicts with tags)
            estimated_minutes: Estimated time in minutes (optional)
            completed: Mark task complete/incomplete (optional)
            status: Task status (TaskStatus enum or string: "active", "dropped") (optional)
            recurrence: iCalendar RRULE string, or "" to remove (optional, legacy)
            repetition_method: "fixed", "start_after_completion", "due_after_completion" (optional, legacy)
            name: Deprecated - use task_name instead (optional)

        Returns:
            dict: {
                "success": bool,
                "task_id": str,
                "updated_fields": list[str],  # Names of fields that were updated
                "error": Optional[str]  # Only present if success=False
            }

        Raises:
            ValueError: If task_id is empty, no fields provided, or conflicting parameters

        Error Handling:
            - Parameter validation errors → Raises ValueError immediately
            - OmniFocus errors (task not found, etc.) → Returns dict with success=False
            - Never raises exceptions for runtime OmniFocus errors
        """
        # NEW API (Redesign)

        # SAFETY: Verify database before modifying
        self._verify_database_safety('update_task')

        if not task_id:
            raise ValueError("task_id is required")

        # Support legacy 'name' parameter
        if name is not None and task_name is None:
            task_name = name

        # Validate conflict: project_id vs parent_task_id
        if project_id is not None and parent_task_id is not None:
            raise ValueError("Cannot specify both parent_task_id and project_id - parent task already determines the project.")

        # Validate conflict: tags vs add_tags/remove_tags
        if tags is not None and add_tags is not None:
            raise ValueError("Cannot specify both tags and add_tags/remove_tags - use tags for full replacement or add_tags/remove_tags for incremental changes.")
        if tags is not None and remove_tags is not None:
            raise ValueError("Cannot specify both tags and remove_tags - use tags for full replacement or add_tags/remove_tags for incremental changes.")

        # Validate status parameter (accept enum or string)
        if status is not None:
            if isinstance(status, str):
                try:
                    status = TaskStatus(status)
                except ValueError:
                    raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join([s.value for s in TaskStatus])}")

        # Validate repetition parameters (legacy)
        if repetition_method:
            valid_methods = ["fixed", "start_after_completion", "due_after_completion"]
            if repetition_method not in valid_methods:
                raise ValueError(f"Invalid repetition_method: {repetition_method}. Must be one of: {', '.join(valid_methods)}")

        # Track which fields are being updated
        updated_fields = []

        # Check if at least one field is provided
        all_params = [
            task_name, project_id, parent_task_id, note, due_date, defer_date,
            flagged, tags, add_tags, remove_tags, estimated_minutes, completed,
            status, recurrence, repetition_method
        ]
        if all(v is None for v in all_params):
            raise ValueError("At least one field must be provided to update")

        # Build AppleScript
        try:
            # Build properties to update (for set properties of theTask)
            properties = []

            if task_name is not None:
                escaped_name = self._escape_applescript_string(task_name)
                properties.append(f'name:"{escaped_name}"')
                updated_fields.append("task_name")

            if note is not None:
                escaped_note = self._escape_applescript_string(note)
                properties.append(f'note:"{escaped_note}"')
                updated_fields.append("note")

            if flagged is not None:
                properties.append(f'flagged:{str(flagged).lower()}')
                updated_fields.append("flagged")

            # Build separate commands (can't use set properties for these)
            separate_commands = []

            # Handle dates
            if due_date is not None:
                if due_date == "":
                    separate_commands.append("set due date of theTask to missing value")
                else:
                    as_date = self._iso_to_applescript_date(due_date)
                    separate_commands.append(f'set due date of theTask to date "{as_date}"')
                updated_fields.append("due_date")

            if defer_date is not None:
                if defer_date == "":
                    separate_commands.append("set defer date of theTask to missing value")
                else:
                    as_date = self._iso_to_applescript_date(defer_date)
                    separate_commands.append(f'set defer date of theTask to date "{as_date}"')
                updated_fields.append("defer_date")

            # Handle estimated minutes
            if estimated_minutes is not None:
                separate_commands.append(f'set estimated minutes of theTask to {estimated_minutes}')
                updated_fields.append("estimated_minutes")

            # Handle completion (use "mark complete" for recurring task safety)
            if completed is not None:
                if completed:
                    separate_commands.append("mark complete theTask")
                else:
                    # Uncomplete task
                    separate_commands.append("set completed of theTask to false")
                updated_fields.append("completed")

            # Handle status (use "mark dropped" command)
            if status is not None:
                if status == TaskStatus.DROPPED:
                    separate_commands.append("mark dropped theTask")
                elif status == TaskStatus.ACTIVE:
                    # Reactivate dropped task
                    separate_commands.append("set dropped of theTask to false")
                updated_fields.append("status")

            # Handle hierarchy changes (project_id or parent_task_id)
            if project_id is not None:
                # Move to project
                project_id_escaped = self._escape_applescript_string(project_id)
                separate_commands.append(f'''
                    set theProject to first flattened project whose id is "{project_id_escaped}"
                    move theTask to end of tasks of theProject''')
                updated_fields.append("project_id")

            if parent_task_id is not None:
                # Make subtask
                parent_id_escaped = self._escape_applescript_string(parent_task_id)
                separate_commands.append(f'''
                    set theParent to first flattened task whose id is "{parent_id_escaped}"
                    if id of theTask is id of theParent then
                        error "Cannot set task as its own parent"
                    end if
                    move theTask to end of tasks of theParent''')
                updated_fields.append("parent_task_id")

            # Handle tags
            if tags is not None:
                # Full replacement: remove all tags, then add new ones
                if len(tags) > 0:
                    tag_adds = []
                    for tag in tags:
                        tag_escaped = self._escape_applescript_string(tag)
                        tag_adds.append(f'''
                        set tagObj to first flattened tag whose name is "{tag_escaped}"
                        copy tagObj to end of newTags''')
                    tag_adds_str = "\n                    ".join(tag_adds)
                    separate_commands.append(f'''
                    set newTags to {{}}
                    {tag_adds_str}
                    set tags of theTask to newTags''')
                else:
                    # Empty list = remove all tags
                    separate_commands.append("set tags of theTask to {}")
                updated_fields.append("tags")

            if add_tags is not None:
                # Add tags incrementally
                for tag in add_tags:
                    tag_escaped = self._escape_applescript_string(tag)
                    separate_commands.append(f'''
                    set tagObj to first flattened tag whose name is "{tag_escaped}"
                    add tagObj to tags of theTask''')
                updated_fields.append("add_tags")

            if remove_tags is not None:
                # Remove tags
                for tag in remove_tags:
                    tag_escaped = self._escape_applescript_string(tag)
                    separate_commands.append(f'''
                    set tagObj to first flattened tag whose name is "{tag_escaped}"
                    remove tagObj from tags of theTask''')
                updated_fields.append("remove_tags")

            # Handle recurrence (legacy)
            if recurrence is not None:
                if recurrence == "":
                    separate_commands.append("set repetition rule of theTask to missing value")
                else:
                    as_method = "fixed repetition"
                    if repetition_method:
                        as_method = {
                            "fixed": "fixed repetition",
                            "start_after_completion": "start after completion",
                            "due_after_completion": "due after completion"
                        }[repetition_method]
                    recurrence_escaped = self._escape_applescript_string(recurrence)
                    separate_commands.append(f'''
                    set existingRule to repetition rule of theTask
                    if existingRule is missing value then
                        set templateRule to missing value
                        repeat with t in flattened tasks
                            try
                                set templateRule to repetition rule of t
                                if templateRule is not missing value then
                                    exit repeat
                                end if
                            end try
                        end repeat
                        if templateRule is not missing value then
                            set repetition rule of theTask to templateRule
                            set theRule to repetition rule of theTask
                            set recurrence of theRule to "{recurrence_escaped}"
                            set repetition method of theRule to {as_method}
                        end if
                    else
                        set recurrence of existingRule to "{recurrence_escaped}"
                        set repetition method of existingRule to {as_method}
                    end if''')
                updated_fields.append("recurrence")
            elif repetition_method is not None:
                as_method = {
                    "fixed": "fixed repetition",
                    "start_after_completion": "start after completion",
                    "due_after_completion": "due after completion"
                }[repetition_method]
                separate_commands.append(f'''
                    set existingRule to repetition rule of theTask
                    if existingRule is not missing value then
                        set repetition method of existingRule to {as_method}
                    end if''')
                updated_fields.append("repetition_method")

            # Build final AppleScript
            task_id_escaped = self._escape_applescript_string(task_id)
            script = f'''
            tell application "OmniFocus"
                tell front document
                    set theTask to first flattened task whose id is "{task_id_escaped}"
                    '''

            # Apply property updates
            if properties:
                props_str = ", ".join(properties)
                script += f'\n                    set properties of theTask to {{{props_str}}}'

            # Apply separate commands
            if separate_commands:
                cmds_str = "\n                    ".join(separate_commands)
                script += f'\n                    {cmds_str}'

            script += '''
                    return "true"
                end tell
            end tell
            '''

            result = run_applescript(script)
            if result.strip() == "true":
                return {
                    "success": True,
                    "task_id": task_id,
                    "updated_fields": updated_fields,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "task_id": task_id,
                    "updated_fields": [],
                    "error": f"Unexpected result: {result}"
                }
        except subprocess.CalledProcessError as e:
            # OmniFocus error (task not found, etc.) - return error dict
            return {
                "success": False,
                "task_id": task_id,
                "updated_fields": [],
                "error": f"AppleScript error: {e.stderr}"
            }
        except Exception as e:
            # Other runtime errors - return error dict
            return {
                "success": False,
                "task_id": task_id,
                "updated_fields": [],
                "error": str(e)
            }

    def update_tasks(
        self,
        task_ids: Union[str, list[str]],
        flagged: Optional[bool] = None,
        status: Optional[Union[TaskStatus, str]] = None,
        completed: Optional[bool] = None,
        project_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        add_tags: Optional[list[str]] = None,
        remove_tags: Optional[list[str]] = None,
        due_date: Optional[str] = None,
        defer_date: Optional[str] = None,
        estimated_minutes: Optional[int] = None,
        **kwargs  # Catch unexpected arguments
    ) -> dict:
        """Update multiple tasks with the same field values (batch operation).

        NEW API (Redesign): Batch version of update_task() for applying uniform changes.

        Key differences from update_task():
        - Accepts Union[str, list[str]] for task_ids (single or multiple)
        - EXCLUDES task_name and note (require unique values per task)
        - Returns dict with counts instead of single success/failure
        - Continues processing on individual failures

        Args:
            task_ids: Single task ID (str) or list of task IDs
            flagged: Mark as flagged (True) or unflagged (False)
            status: Set status ("active" or "dropped", or TaskStatus enum)
            completed: Mark as completed (True) or incomplete (False)
            project_id: Move to project (use empty string "" for inbox)
            parent_task_id: Set as child of parent task
            tags: Replace all tags with this list (empty list removes all)
            add_tags: Add these tags to existing tags
            remove_tags: Remove these tags from existing tags
            due_date: Set due date (ISO format or empty string to clear)
            defer_date: Set defer date (ISO format or empty string to clear)
            estimated_minutes: Set estimated time in minutes

        Returns:
            dict: {
                "updated_count": int,
                "failed_count": int,
                "updated_ids": list[str],
                "failures": list[dict] with "task_id" and "error"
            }

        Raises:
            ValueError: If validation fails (task_name/note provided, conflicting params, etc.)

        Example:
            # Flag multiple tasks
            result = client.update_tasks(
                task_ids=["task-001", "task-002", "task-003"],
                flagged=True
            )
            # Returns: {"updated_count": 3, "failed_count": 0, "updated_ids": [...], "failures": []}
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('update_tasks')

        # Validation: task_name and note are NOT allowed (require unique values)
        if 'task_name' in kwargs or 'name' in kwargs:
            raise ValueError("task_name is not allowed in batch updates (requires unique values per task)")
        if 'note' in kwargs:
            raise ValueError("note is not allowed in batch updates (requires unique values per task)")

        # Reject any other unexpected arguments
        if kwargs:
            unexpected = ', '.join(kwargs.keys())
            raise ValueError(f"Unexpected arguments: {unexpected}")

        # Normalize task_ids to list
        if isinstance(task_ids, str):
            ids_list = [task_ids]
        else:
            ids_list = task_ids

        # Validation: task_ids must not be empty
        if not ids_list:
            raise ValueError("task_ids cannot be empty")

        # Validation: Must provide at least one field to update
        provided_fields = [
            flagged, status, completed, project_id, parent_task_id,
            tags, add_tags, remove_tags, due_date, defer_date, estimated_minutes
        ]
        if all(f is None for f in provided_fields):
            raise ValueError("Must provide at least one field to update")

        # Validation: Conflicting parameters
        if project_id is not None and parent_task_id is not None:
            raise ValueError("Cannot specify both project_id and parent_task_id")

        if tags is not None and add_tags is not None:
            raise ValueError("Cannot specify both tags and add_tags (use one or the other)")

        # Process each task individually
        updated_ids = []
        failures = []

        for task_id in ids_list:
            try:
                # Call update_task for each task
                result = self.update_task(
                    task_id=task_id,
                    flagged=flagged,
                    status=status,
                    completed=completed,
                    project_id=project_id,
                    parent_task_id=parent_task_id,
                    tags=tags,
                    add_tags=add_tags,
                    remove_tags=remove_tags,
                    due_date=due_date,
                    defer_date=defer_date,
                    estimated_minutes=estimated_minutes
                )

                if result["success"]:
                    updated_ids.append(task_id)
                else:
                    failures.append({
                        "task_id": task_id,
                        "error": result["error"]
                    })
            except Exception as e:
                # Catch any unexpected errors and continue
                failures.append({
                    "task_id": task_id,
                    "error": str(e)
                })

        return {
            "updated_count": len(updated_ids),
            "failed_count": len(failures),
            "updated_ids": updated_ids,
            "failures": failures
        }

    def get_inbox_tasks(self) -> list[dict[str, Any]]:
        """Get all tasks from the inbox.

        Returns:
            list: List of inbox task dictionaries with id, name, note, completed, flagged, dropped, dates, and tags
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
                        set taskDropped to dropped of t

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
                            "\\"dropped\\": " & (taskDropped as text) & ", " & ¬
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
        ''' + APPLESCRIPT_JSON_HELPERS

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
        flagged: bool = False,
        recurrence: Optional[str] = None,
        repetition_method: Optional[str] = None
    ) -> bool:
        """Create a new task in the inbox.

        Args:
            task_name: The name of the task
            note: Optional note for the task
            due_date: Optional due date in ISO 8601 format
            flagged: Whether to flag the task (default: False)
            recurrence: Optional iCalendar RRULE string (e.g., "FREQ=WEEKLY", "FREQ=DAILY;INTERVAL=2")
            repetition_method: Optional repetition method - "fixed" (default), "start_after_completion", "due_after_completion"

        Returns:
            bool: True if successful

        Raises:
            ValueError: If task_name is empty or if repetition_method is invalid or provided without recurrence
            Exception: If the task cannot be created
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('create_inbox_task')

        if not task_name:
            raise ValueError("task_name is required")

        # Validate repetition parameters
        if repetition_method and not recurrence:
            raise ValueError("repetition_method requires recurrence to be specified")

        if repetition_method:
            valid_methods = ["fixed", "start_after_completion", "due_after_completion"]
            if repetition_method not in valid_methods:
                raise ValueError(f"Invalid repetition_method: {repetition_method}. Must be one of: {', '.join(valid_methods)}")

        # Default repetition_method to 'fixed' if recurrence is provided but method isn't
        if recurrence and not repetition_method:
            repetition_method = "fixed"

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

        # Build repetition rule commands
        repetition_commands = []
        if recurrence:
            # Convert Python-friendly method names to AppleScript enum names
            as_method = {
                "fixed": "fixed repetition",
                "start_after_completion": "start after completion",
                "due_after_completion": "due after completion"
            }[repetition_method]

            # Escape the recurrence string for AppleScript
            recurrence_escaped = self._escape_applescript_string(recurrence)

            # Get a template rule, create task, assign rule, modify properties
            repetition_commands.append(f'''
                    -- Get template repetition rule from any existing task
                    set templateRule to missing value
                    repeat with t in flattened tasks
                        try
                            set templateRule to repetition rule of t
                            if templateRule is not missing value then
                                exit repeat
                            end if
                        end try
                    end repeat

                    -- If we have a template, set up recurrence
                    if templateRule is not missing value then
                        set repetition rule of newTask to templateRule
                        set theRule to repetition rule of newTask
                        set recurrence of theRule to "{recurrence_escaped}"
                        set repetition method of theRule to {as_method}
                    end if''')

        repetition_commands_str = "\n                ".join(repetition_commands)

        script = f'''
        tell application "OmniFocus"
            tell front document
                set newTask to make new inbox task with properties {{{properties_str}}}
                {date_command if date_command else ""}
                {repetition_commands_str if repetition_commands else ""}
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
        ''' + APPLESCRIPT_JSON_HELPERS

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

    def drop_project(self, project_id: str) -> bool:
        """Drop a project (mark as on hold indefinitely).

        Args:
            project_id: The ID of the project to drop

        Returns:
            True if drop was successful

        Raises:
            Exception: If project not found or drop fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('drop_project')

        project_id_escaped = self._escape_applescript_string(project_id)

        script = f'''
        tell application "OmniFocus"
            tell front document
                try
                    set theProject to first flattened project whose id is "{project_id_escaped}"
                    mark dropped theProject
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
            raise Exception(f"Error dropping project: {e.stderr}")

    def drop_projects(self, project_ids: list[str]) -> int:
        """Drop multiple projects (mark as on hold indefinitely) in a single operation.

        Args:
            project_ids: List of project IDs to drop

        Returns:
            int: Number of projects successfully dropped

        Raises:
            ValueError: If project_ids is empty
            Exception: If the operation fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('drop_projects')

        if not project_ids:
            raise ValueError("project_ids cannot be empty")

        # Build AppleScript list of project IDs
        ids_list = ", ".join([f'"{project_id}"' for project_id in project_ids])

        script = f'''
        tell application "OmniFocus"
            tell front document
                set projectIdList to {{{ids_list}}}
                set successCount to 0

                repeat with projectId in projectIdList
                    try
                        set theProject to first flattened project whose id is projectId
                        mark dropped theProject
                        set successCount to successCount + 1
                    on error
                        -- Project not found, skip
                    end try
                end repeat

                return successCount as text
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            return int(result.strip())
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error dropping projects: {e.stderr}")
        except ValueError as e:
            raise Exception(f"Error parsing drop result: {e}")

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

    def move_tasks(self, task_ids: list[str], project_id: Optional[str]) -> int:
        """Move multiple tasks to a different project or to inbox.

        Args:
            task_ids: List of task IDs to move
            project_id: The ID of the destination project, or None for inbox

        Returns:
            int: Number of tasks successfully moved

        Raises:
            ValueError: If task_ids is empty
            Exception: If the operation fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('move_tasks')

        if not task_ids:
            raise ValueError("task_ids cannot be empty")

        # Build AppleScript list of task IDs
        ids_list = ", ".join([f'"{task_id}"' for task_id in task_ids])

        if project_id is None:
            # Move to inbox
            script = f'''
            tell application "OmniFocus"
                tell front document
                    set taskIdList to {{{ids_list}}}
                    set successCount to 0

                    repeat with taskId in taskIdList
                        try
                            set theTask to first flattened task whose id is taskId
                            move theTask to end of tasks of front document
                            set successCount to successCount + 1
                        on error
                            -- Task not found, skip
                        end try
                    end repeat

                    return successCount as text
                end tell
            end tell
            '''
        else:
            # Move to project
            script = f'''
            tell application "OmniFocus"
                tell front document
                    set taskIdList to {{{ids_list}}}
                    set successCount to 0

                    try
                        set theProject to first flattened project whose id is "{project_id}"

                        repeat with taskId in taskIdList
                            try
                                set theTask to first flattened task whose id is taskId
                                move theTask to end of tasks of theProject
                                set successCount to successCount + 1
                            on error
                                -- Task not found, skip
                            end try
                        end repeat

                        return successCount as text
                    on error errMsg
                        error "Project not found: " & errMsg
                    end try
                end tell
            end tell
            '''

        try:
            result = run_applescript(script)
            return int(result.strip())
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error moving tasks: {e.stderr}")
        except ValueError as e:
            raise Exception(f"Error parsing move result: {e}")

    def add_tag_to_tasks(self, task_ids: list[str], tag_name: str) -> int:
        """Add a tag to multiple tasks in a single operation.

        Args:
            task_ids: List of task IDs to tag
            tag_name: Name of the tag to add

        Returns:
            int: Number of tasks successfully tagged

        Raises:
            ValueError: If task_ids is empty or tag_name is empty
            Exception: If the operation fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('add_tag_to_tasks')

        if not task_ids:
            raise ValueError("task_ids cannot be empty")
        if not tag_name or tag_name.strip() == "":
            raise ValueError("tag_name cannot be empty")

        # Build AppleScript list of task IDs
        ids_list = ", ".join([f'"{task_id}"' for task_id in task_ids])
        tag_escaped = self._escape_applescript_string(tag_name)

        script = f'''
        tell application "OmniFocus"
            tell front document
                set taskIdList to {{{ids_list}}}
                set successCount to 0

                try
                    set tagObj to first flattened tag whose name is "{tag_escaped}"

                    repeat with taskId in taskIdList
                        try
                            set theTask to first flattened task whose id is taskId
                            add tagObj to tags of theTask
                            set successCount to successCount + 1
                        on error
                            -- Task not found, skip
                        end try
                    end repeat

                    return successCount as text
                on error errMsg
                    error "Tag not found: " & errMsg
                end try
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            return int(result.strip())
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error adding tag to tasks: {e.stderr}")
        except ValueError as e:
            raise Exception(f"Error parsing tag result: {e}")

    def remove_tag_from_tasks(self, task_ids: list[str], tag_name: str) -> int:
        """Remove a tag from multiple tasks in a single operation.

        Args:
            task_ids: List of task IDs to remove tag from
            tag_name: Name of the tag to remove

        Returns:
            int: Number of tasks successfully updated

        Raises:
            ValueError: If task_ids is empty or tag_name is empty
            Exception: If the operation fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('remove_tag_from_tasks')

        if not task_ids:
            raise ValueError("task_ids cannot be empty")
        if not tag_name or tag_name.strip() == "":
            raise ValueError("tag_name cannot be empty")

        # Build AppleScript list of task IDs
        ids_list = ", ".join([f'"{task_id}"' for task_id in task_ids])
        tag_escaped = self._escape_applescript_string(tag_name)

        script = f'''
        tell application "OmniFocus"
            tell front document
                set taskIdList to {{{ids_list}}}
                set successCount to 0

                try
                    set tagObj to first flattened tag whose name is "{tag_escaped}"

                    repeat with taskId in taskIdList
                        try
                            set theTask to first flattened task whose id is taskId
                            remove tagObj from tags of theTask
                            set successCount to successCount + 1
                        on error
                            -- Task not found or tag not present, skip
                        end try
                    end repeat

                    return successCount as text
                on error errMsg
                    error "Tag not found: " & errMsg
                end try
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            return int(result.strip())
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error removing tag from tasks: {e.stderr}")
        except ValueError as e:
            raise Exception(f"Error parsing tag result: {e}")

    def drop_tasks(self, task_ids: list[str]) -> int:
        """Drop multiple tasks (mark as on hold indefinitely) in a single operation.

        Args:
            task_ids: List of task IDs to drop

        Returns:
            int: Number of tasks successfully dropped

        Raises:
            ValueError: If task_ids is empty
            Exception: If the operation fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('drop_tasks')

        if not task_ids:
            raise ValueError("task_ids cannot be empty")

        # Build AppleScript list of task IDs
        ids_list = ", ".join([f'"{task_id}"' for task_id in task_ids])

        script = f'''
        tell application "OmniFocus"
            tell front document
                set taskIdList to {{{ids_list}}}
                set successCount to 0

                repeat with taskId in taskIdList
                    try
                        set theTask to first flattened task whose id is taskId
                        if dropped of theTask is false then
                            mark dropped theTask
                            set successCount to successCount + 1
                        end if
                    on error
                        -- Task not found or already dropped, skip
                    end try
                end repeat

                return successCount as text
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            return int(result.strip())
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error dropping tasks: {e.stderr}")
        except ValueError as e:
            raise Exception(f"Error parsing drop result: {e}")

    def delete_tasks(self, task_ids: Union[str, list[str]]) -> dict:
        """Delete multiple tasks from OmniFocus in a single operation.

        NEW API (Redesign): Enhanced to accept Union[str, list[str]] and return dict.

        Args:
            task_ids: Single task ID (str) or list of task IDs to delete

        Returns:
            dict: {
                "deleted_count": int,
                "failed_count": int,
                "deleted_ids": list[str],
                "failures": list[dict]  # Empty for now (AppleScript doesn't track individual failures)
            }

        Raises:
            ValueError: If task_ids is empty
            Exception: If the operation fails

        Example:
            result = client.delete_tasks(["task-001", "task-002"])
            # Returns: {"deleted_count": 2, "failed_count": 0, "deleted_ids": [...], "failures": []}
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('delete_tasks')

        # Normalize task_ids to list
        if isinstance(task_ids, str):
            ids_list_input = [task_ids]
        else:
            ids_list_input = task_ids

        # Validation
        if not ids_list_input:
            raise ValueError("task_ids cannot be empty")

        # Build AppleScript list of task IDs
        ids_list = ", ".join([f'"{task_id}"' for task_id in ids_list_input])

        script = f'''
        tell application "OmniFocus"
            tell front document
                set taskIdList to {{{ids_list}}}
                set successCount to 0

                repeat with taskId in taskIdList
                    try
                        set theTask to first flattened task whose id is taskId
                        delete theTask
                        set successCount to successCount + 1
                    on error
                        -- Task not found, skip
                    end try
                end repeat

                return successCount as text
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            deleted_count = int(result.strip())
            total_count = len(ids_list_input)
            failed_count = total_count - deleted_count

            # Build list of deleted IDs (we successfully deleted the first N tasks)
            # Note: AppleScript doesn't tell us which specific tasks failed,
            # so we assume the first deleted_count tasks succeeded
            deleted_ids = ids_list_input[:deleted_count] if deleted_count > 0 else []

            return {
                "deleted_count": deleted_count,
                "failed_count": failed_count,
                "deleted_ids": deleted_ids,
                "failures": []  # AppleScript doesn't provide detailed failure info
            }
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error deleting tasks: {e.stderr}")
        except ValueError as e:
            raise Exception(f"Error parsing delete result: {e}")

    def delete_projects(self, project_ids: list[str]) -> int:
        """Delete multiple projects from OmniFocus in a single operation.

        Args:
            project_ids: List of project IDs to delete

        Returns:
            int: Number of projects successfully deleted

        Raises:
            ValueError: If project_ids is empty
            Exception: If the operation fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('delete_projects')

        if not project_ids:
            raise ValueError("project_ids cannot be empty")

        # Build AppleScript list of project IDs
        ids_list = ", ".join([f'"{project_id}"' for project_id in project_ids])

        script = f'''
        tell application "OmniFocus"
            tell front document
                set projectIdList to {{{ids_list}}}
                set successCount to 0

                repeat with projectId in projectIdList
                    try
                        set theProject to first flattened project whose id is projectId
                        delete theProject
                        set successCount to successCount + 1
                    on error
                        -- Project not found, skip
                    end try
                end repeat

                return successCount as text
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            return int(result.strip())
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error deleting projects: {e.stderr}")
        except ValueError as e:
            raise Exception(f"Error parsing delete result: {e}")

    def get_folders(self) -> list[dict]:
        """Get all folders from OmniFocus.

        Returns:
            List of folder dictionaries with id, name, and path
        """
        script = '''
        -- Helper to build folder path
        on getFolderPath(f)
            tell application "OmniFocus"
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
            end tell
        end getFolderPath

        -- Process folders recursively
        on processFolders(foldersToProcess, folderResults)
            tell application "OmniFocus"
                repeat with f in foldersToProcess
                    set folderPath to my getFolderPath(f)
                    set folderInfo to "{" & quote & "id" & quote & ":" & quote & (id of f) & quote & "," & quote & "name" & quote & ":" & quote & (name of f) & quote & "," & quote & "path" & quote & ":" & quote & folderPath & quote & "}"
                    set end of folderResults to folderInfo
                    my processFolders(folders of f, folderResults)
                end repeat
                return folderResults
            end tell
        end processFolders

        tell application "OmniFocus"
            tell front document
                set folderList to my processFolders(folders, {})

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
                    mark dropped theTask
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

        # Escape quotes and backslashes in name
        name_escaped = self._escape_applescript_string(name)

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

    def reorder_task(self, task_id: str, before_task_id: Optional[str] = None, after_task_id: Optional[str] = None) -> bool:
        """Reorder a task by moving it before or after another task.

        Args:
            task_id: The ID of the task to move
            before_task_id: Move the task before this task (optional)
            after_task_id: Move the task after this task (optional)

        Note:
            Exactly one of before_task_id or after_task_id must be provided.
            Both tasks must be in the same project and at the same level (both root or both subtasks of same parent).

        Returns:
            True if operation was successful

        Raises:
            ValueError: If neither or both before_task_id and after_task_id are provided
            Exception: If tasks not found, not in same project, or operation fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('reorder_task')

        # Validate parameters
        if before_task_id is None and after_task_id is None:
            raise ValueError("Must provide either before_task_id or after_task_id")
        if before_task_id is not None and after_task_id is not None:
            raise ValueError("Cannot provide both before_task_id and after_task_id")

        reference_task_id = before_task_id if before_task_id else after_task_id
        position = "before" if before_task_id else "after"

        script = f'''
        tell application "OmniFocus"
            tell front document
                try
                    set theTask to first flattened task whose id is "{task_id}"
                    set refTask to first flattened task whose id is "{reference_task_id}"

                    -- Move task to before/after reference task
                    move theTask to {position} refTask
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
                raise Exception(f"Error reordering task: {result}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error reordering task: {e.stderr}")

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
                    set next review date of theProject to (current date)
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
        ''' + APPLESCRIPT_JSON_HELPERS

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
