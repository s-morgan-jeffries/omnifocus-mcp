"""Client for interacting with OmniFocus app."""
import subprocess
import json
import os
from typing import Any, Optional


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
# These are duplicated in each AppleScript block since AppleScript doesn't support imports
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
                        if projStatus is "dropped" then
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

                        -- Get modification date
                        set modDateStr to "null"
                        try
                            set modDate to modification date of proj
                            if modDate is not missing value then
                                set modDateStr to "\\"" & (modDate as «class isot» as string) & "\\""
                            end if
                        end try

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
                            "\\"folderPath\\": \\"" & my escapeJSON(folderPath) & "\\", " & ¬
                            "\\"modificationDate\\": " & modDateStr & ", " & ¬
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
                        if projStatus is not "on hold" then
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

        Args:
            project_id: The ID of the project to retrieve

        Returns:
            dict: Project dictionary with id, name, note, status, folderPath, and statistics:
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

                -- Get modification date
                set modDateStr to "null"
                try
                    set modDate to modification date of targetProject
                    if modDate is not missing value then
                        set modDateStr to "\\"" & (modDate as «class isot» as string) & "\\""
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
                    "\\"taskCount\\": " & taskCount & ", " & ¬
                    "\\"completedTaskCount\\": " & completedCount & ", " & ¬
                    "\\"remainingTaskCount\\": " & remainingCount & ", " & ¬
                    "\\"completionPercentage\\": " & completionPct & ", " & ¬
                    "\\"reviewInterval\\": " & reviewIntervalStr & ", " & ¬
                    "\\"lastReviewDate\\": " & lastReviewStr & ", " & ¬
                    "\\"nextReviewDate\\": " & nextReviewStr & ", " & ¬
                    "\\"modificationDate\\": " & modDateStr & ", " & ¬
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

    def get_stalled_projects(self, days_inactive: int = 30) -> list[dict[str, Any]]:
        """Get active projects with no recent task activity.

        Args:
            days_inactive: Minimum days of inactivity to consider a project stalled (default: 30)

        Returns:
            list[dict]: List of stalled projects, each containing:
                - id: Project ID
                - name: Project name
                - status: Project status (always "active")
                - lastActivityDate: ISO timestamp of most recent task activity (or null)
                - daysInactive: Number of days since last activity (or null if no activity)

            Projects are sorted by days inactive (most stale first).
        """
        from datetime import datetime, timezone, timedelta

        # Calculate the cutoff date
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_inactive)
        cutoff_iso = cutoff_date.isoformat()

        # Simplified implementation: just return all active projects
        # The caller can filter by activity in Python
        script = '''
        tell application "OmniFocus"
            tell front document
                set output to "["
                set firstItem to true

                repeat with proj in flattened projects
                    if status of proj is active then
                        set projId to id of proj
                        set projName to name of proj

                        if not firstItem then
                            set output to output & ","
                        end if
                        set firstItem to false

                        set output to output & "{" & quote & "id" & quote & ":" & quote & projId & quote & "," & quote & "name" & quote & ":" & quote & projName & quote & "," & quote & "status" & quote & ":" & quote & "active" & quote & "}"
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

            # For now, return all active projects
            # TODO: Implement proper stalled project detection
            # Would need to query tasks for each project to determine activity
            return projects

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

    def set_project_status(self, project_id: str, status: str) -> bool:
        """Set the status of a project.

        Args:
            project_id: The ID of the project
            status: The status to set - one of: "active", "on_hold", "done"
                   Note: "dropped" status is not supported by AppleScript

        Returns:
            bool: True if status was set successfully

        Raises:
            ValueError: If project not found, status is invalid, or "dropped" is requested
            RuntimeError: If AppleScript execution fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('set_project_status')

        # Validate status
        valid_statuses = ["active", "on_hold", "done"]
        if status not in valid_statuses:
            if status == "dropped":
                raise ValueError("Status 'dropped' is not supported by AppleScript API. Only 'active', 'on_hold', and 'done' are supported.")
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
        else:  # status == "done"
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
                            "\\"isRecurring\\": " & isRecurring & ", " & ¬
                            "\\"recurrence\\": \\"" & my escapeJSON(recurrenceStr) & "\\", " & ¬
                            "\\"repetitionMethod\\": \\"" & my escapeJSON(repetitionMethodStr) & "\\" " & ¬
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

                set completionDate to ""
                try
                    set completionDateObj to completion date of targetTask
                    if completionDateObj is not missing value then
                        set completionDate to completionDateObj as «class isot» as string
                    end if
                end try

                -- Get tags
                set tagsList to ""
                try
                    set taskTags to tags of targetTask
                    set tagNames to {{}}
                    repeat with tg in taskTags
                        set end of tagNames to name of tg
                    end repeat
                    set AppleScript's text item delimiters to ", "
                    set tagsList to tagNames as text
                    set AppleScript's text item delimiters to ""
                end try

                -- Get estimated minutes
                set estimatedMins to "null"
                try
                    set estMins to estimated minutes of targetTask
                    if estMins is not missing value and estMins is not 0 then
                        set estimatedMins to estMins as text
                    end if
                end try

                -- Build JSON manually
                set jsonOutput to "{{" & ¬
                    "\\"id\\": \\"" & taskId & "\\", " & ¬
                    "\\"name\\": \\"" & my escapeJSON(taskName) & "\\", " & ¬
                    "\\"note\\": \\"" & my escapeJSON(taskNote) & "\\", " & ¬
                    "\\"completed\\": " & (taskCompleted as text) & ", " & ¬
                    "\\"flagged\\": " & (taskFlagged as text) & ", " & ¬
                    "\\"dropped\\": " & (taskDropped as text) & ", " & ¬
                    "\\"projectId\\": \\"" & projectId & "\\", " & ¬
                    "\\"projectName\\": \\"" & my escapeJSON(projectName) & "\\", " & ¬
                    "\\"dueDate\\": \\"" & dueDate & "\\", " & ¬
                    "\\"deferDate\\": \\"" & deferDate & "\\", " & ¬
                    "\\"completionDate\\": \\"" & completionDate & "\\", " & ¬
                    "\\"tags\\": \\"" & my escapeJSON(tagsList) & "\\", " & ¬
                    "\\"estimatedMinutes\\": " & estimatedMins & ¬
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

        tell application "OmniFocus"
            tell front document
                try
                    set parentTask to first flattened task whose id is "{task_id}"
                    set childTasks to tasks of parentTask

                    repeat with t in childTasks
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
                                "\\"estimatedMinutes\\": " & estimatedMins & ¬
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
        name: Optional[str] = None,
        task_name: Optional[str] = None,
        note: Optional[str] = None,
        due_date: Optional[str] = None,
        defer_date: Optional[str] = None,
        flagged: Optional[bool] = None,
        recurrence: Optional[str] = None,
        repetition_method: Optional[str] = None
    ) -> bool:
        """Update properties of an existing task.

        Args:
            task_id: The ID of the task to update
            name: New task name (optional) - deprecated, use task_name
            task_name: New task name (optional)
            note: New task note (optional)
            due_date: New due date in ISO 8601 format, or None to clear (optional)
            defer_date: New defer date in ISO 8601 format, or None to clear (optional)
            flagged: New flagged status (optional)
            recurrence: iCalendar RRULE string to set, or "" to remove recurrence (optional)
            repetition_method: Repetition method - "fixed", "start_after_completion", "due_after_completion" (optional)

        Returns:
            bool: True if successful

        Raises:
            ValueError: If task_id is empty, no fields are provided, or repetition_method is invalid
            Exception: If the task cannot be updated
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('update_task')

        if not task_id:
            raise ValueError("task_id is required")

        # Support both name and task_name for backwards compatibility
        if task_name is not None:
            name = task_name

        # Validate repetition parameters
        if repetition_method:
            valid_methods = ["fixed", "start_after_completion", "due_after_completion"]
            if repetition_method not in valid_methods:
                raise ValueError(f"Invalid repetition_method: {repetition_method}. Must be one of: {', '.join(valid_methods)}")

        # Check if at least one field is provided
        if all(v is None for v in [name, note, due_date, flagged, recurrence, repetition_method]) and defer_date is None:
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

        # Build repetition update commands
        repetition_commands = []
        if recurrence is not None:
            if recurrence == "":
                # Remove recurrence
                repetition_commands.append("set repetition rule of theTask to missing value")
            else:
                # Add or update recurrence
                as_method = "fixed repetition"  # default
                if repetition_method:
                    as_method = {
                        "fixed": "fixed repetition",
                        "start_after_completion": "start after completion",
                        "due_after_completion": "due after completion"
                    }[repetition_method]

                recurrence_escaped = self._escape_applescript_string(recurrence)

                # Check if task already has a rule; if not, get template
                repetition_commands.append(f'''
                    set existingRule to repetition rule of theTask
                    if existingRule is missing value then
                        -- Need to get a template rule
                        set templateRule to missing value
                        repeat with t in flattened tasks
                            try
                                set templateRule to repetition rule of t
                                if templateRule is not missing value then
                                    exit repeat
                                end if
                            end try
                        end repeat

                        -- Set up new rule from template
                        if templateRule is not missing value then
                            set repetition rule of theTask to templateRule
                            set theRule to repetition rule of theTask
                            set recurrence of theRule to "{recurrence_escaped}"
                            set repetition method of theRule to {as_method}
                        end if
                    else
                        -- Modify existing rule
                        set recurrence of existingRule to "{recurrence_escaped}"
                        set repetition method of existingRule to {as_method}
                    end if''')
        elif repetition_method is not None:
            # Only updating the method, not the recurrence string
            as_method = {
                "fixed": "fixed repetition",
                "start_after_completion": "start after completion",
                "due_after_completion": "due after completion"
            }[repetition_method]

            repetition_commands.append(f'''
                    set existingRule to repetition rule of theTask
                    if existingRule is not missing value then
                        set repetition method of existingRule to {as_method}
                    end if''')

        # Build properties string
        props_str = ", ".join(properties) if properties else ""
        date_cmds_str = "\n                ".join(date_commands) if date_commands else ""
        repetition_cmds_str = "\n                ".join(repetition_commands) if repetition_commands else ""

        script = f'''
        tell application "OmniFocus"
            tell front document
                set theTask to first flattened task whose id is "{task_id}"
                '''

        if props_str:
            script += f'\n                set properties of theTask to {{{props_str}}}'

        if date_cmds_str:
            script += f'\n                {date_cmds_str}'

        if repetition_cmds_str:
            script += f'\n                {repetition_cmds_str}'

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

    def delete_tasks(self, task_ids: list[str]) -> int:
        """Delete multiple tasks from OmniFocus in a single operation.

        Args:
            task_ids: List of task IDs to delete

        Returns:
            int: Number of tasks successfully deleted

        Raises:
            ValueError: If task_ids is empty
            Exception: If the operation fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('delete_tasks')

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
            return int(result.strip())
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
