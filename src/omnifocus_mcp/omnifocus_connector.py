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


class OmniFocusConnector:
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
        'create_task', 'update_task', 'update_tasks',
        'create_project', 'update_project', 'update_projects',
        'create_folder', 'create_tag', 'update_tag', 'delete_tasks',
        'delete_projects', 'delete_tags', 'reorder_task',
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

    def _escape_js_string(self, text: str) -> str:
        """Escape a string for use in a JS single-quoted literal inside AppleScript.

        Handles the double-context: JS '...' inside AppleScript "..." via
        `evaluate javascript "..."`. Order matters — backslashes first.
        """
        if not text:
            return ""
        text = text.replace("\\", "\\\\")   # \ → \\ (must be first)
        text = text.replace("'", "\\'")      # ' → \' (JS string delimiter)
        text = text.replace('"', '\\"')      # " → \" (AppleScript string delimiter)
        text = text.replace("\n", "\\n")     # newline → \n
        text = text.replace("\r", "\\r")     # carriage return → \r
        text = text.replace("\t", "\\t")     # tab → \t
        return text

    def _build_whose_or_chain(self, ids_list: list[str], entity_type: str) -> str:
        """Build a 'whose' or-chain clause for targeting multiple items by ID.

        Returns: 'every <entity_type> whose id is "X" or id is "Y" or ...'
        """
        clauses = " or ".join(
            f'id is "{self._escape_applescript_string(tid)}"' for tid in ids_list
        )
        return f"every {entity_type} whose {clauses}"

    def _get_tasks_batch_for_filtering(
        self,
        project_ids: list[str]
    ) -> dict[str, list[dict[str, Any]]]:
        """Batch fetch tasks for multiple projects in a single AppleScript call.

        This method is optimized for project filtering and only returns minimal
        task information needed for filtering: id, project_id, due_date, completed.

        This eliminates the N+1 query pattern where each project triggers a separate
        get_tasks() call, reducing ~30 AppleScript roundtrips to just 1.

        Args:
            project_ids: List of project IDs to fetch tasks for

        Returns:
            Dictionary mapping project_id -> list of task dictionaries
            Each task dict contains: {id, projectId, dueDate}
        """
        if not project_ids:
            return {}

        # Build AppleScript to fetch all tasks for all projects in one call
        # Handlers must be at script level, not inside tell blocks
        script = '''
        -- Helper to format ISO date
        on formatDate(d)
            if d is missing value then
                return ""
            end if
            try
                set y to year of d as string
                set m to month of d as integer
                if m < 10 then set m to "0" & m
                set dy to day of d as integer
                if dy < 10 then set dy to "0" & dy
                set h to hours of d as integer
                if h < 10 then set h to "0" & h
                set min to minutes of d as integer
                if min < 10 then set min to "0" & min
                set s to seconds of d as integer
                if s < 10 then set s to "0" & s
                return y & "-" & m & "-" & dy & "T" & h & ":" & min & ":" & s & "Z"
            on error
                return ""
            end try
        end formatDate

        -- Helper to join list with delimiter
        on joinList(theList, theDelimiter)
            set oldDelimiters to AppleScript's text item delimiters
            set AppleScript's text item delimiters to theDelimiter
            set theString to theList as string
            set AppleScript's text item delimiters to oldDelimiters
            return theString
        end joinList

        tell application "OmniFocus"
            tell front document
                set tasksByProject to {}

                -- Iterate through all projects and collect tasks
                repeat with proj in flattened projects
                    set projId to id of proj
'''

        # Add project ID checks
        for i, project_id in enumerate(project_ids):
            escaped_id = self._escape_applescript_string(project_id)
            if i == 0:
                script += f'''
                    if projId is "{escaped_id}"'''
            else:
                script += f''' or projId is "{escaped_id}"'''

        script += ''' then
                        set projectTasks to {}

                        -- Get all incomplete tasks for this project
                        repeat with t in flattened tasks of proj
                            if not (completed of t) then
                                set taskId to id of t
                                set taskDue to my formatDate(effective due date of t)
                                set taskJson to "{\\"id\\":\\"" & taskId & "\\",\\"projectId\\":\\"" & projId & "\\",\\"dueDate\\":\\"" & taskDue & "\\"}"
                                set end of projectTasks to taskJson
                            end if
                        end repeat

                        -- Add to results
                        set projectJson to "{\\"projectId\\":\\"" & projId & "\\",\\"tasks\\":[" & my joinList(projectTasks, ",") & "]}"
                        set end of tasksByProject to projectJson
                    end if
                end repeat

                return "[" & my joinList(tasksByProject, ",") & "]"
            end tell
        end tell
        '''

        # Execute AppleScript
        result = run_applescript(script, timeout=60)

        # Parse JSON result
        import json
        projects_data = json.loads(result)

        # Convert to dict[project_id -> list[task]]
        tasks_by_project = {}
        for project_data in projects_data:
            project_id = project_data['projectId']
            tasks_by_project[project_id] = project_data['tasks']

        return tasks_by_project

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

        # OPTIMIZATION: Batch fetch all tasks for all projects in one AppleScript call
        # This eliminates the N+1 query pattern (one get_tasks() call per project)
        project_ids = [p.get('id') for p in projects if p.get('id')]
        tasks_by_project = self._get_tasks_batch_for_filtering(project_ids)

        for project in projects:
            project_id = project.get('id')
            if not project_id:
                continue

            # Get tasks for this project from batch results
            tasks = tasks_by_project.get(project_id, [])

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
            task_tags_raw = task.get('tags', [])
            if isinstance(task_tags_raw, list):
                task_tags = [t.lower() for t in task_tags_raw if isinstance(t, str)]
            elif task_tags_raw:
                task_tags = [t.strip().lower() for t in task_tags_raw.split(',')]
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

    def _get_on_hold_tag_names(self) -> list[str]:
        """Pre-fetch names of all On Hold or Dropped tags.

        Used by get_tasks(available_only=True) to exclude tasks with On Hold
        or Dropped tags, matching OmniFocus's native Available perspective
        behavior.

        Returns:
            List of tag names where allows next action is false or hidden
            is true. Empty list if no such tags exist or on error.
        """
        script = '''
        tell application "OmniFocus"
            tell front document
                try
                    return name of (flattened tags whose allows next action is false or hidden is true)
                on error
                    return {}
                end try
            end tell
        end tell
        '''
        try:
            result = run_applescript(script)
            if not result or not result.strip():
                return []
            return [name.strip() for name in result.split(", ") if name.strip()]
        except Exception:
            return []

    def _get_task_ids_for_tags(
        self,
        tag_names: list[str],
        mode: str,
        include_completed: bool = False
    ) -> set[str] | None:
        """Query task IDs from the tag side for pre-filtering.

        Instead of scanning all tasks and checking their tags (O(N) with full
        property extraction), this queries OmniFocus for tasks belonging to
        each tag directly. Returns task IDs for use in a 'whose' clause.

        Args:
            tag_names: List of tag names to query
            mode: "and" (intersection) or "or" (union)
            include_completed: Whether to include completed tasks

        Returns:
            set of task IDs, empty set if no matches, or None if a tag was not found
        """
        # Build AppleScript that queries tasks for each tag
        escaped_names = [self._escape_applescript_string(name) for name in tag_names]
        tag_list_items = ", ".join(f'"{name}"' for name in escaped_names)

        completed_filter = ""
        if not include_completed:
            completed_filter = " whose completed is false"

        script = f'''
        tell application "OmniFocus"
            tell front document
                set output to ""
                set tagNames to {{{tag_list_items}}}
                repeat with tagName in tagNames
                    try
                        set tagObj to first flattened tag whose name is tagName
                        set tIds to id of (tasks of tagObj{completed_filter})
                        set AppleScript's text item delimiters to ","
                        set output to output & (tIds as string) & "|"
                    on error
                        set output to output & "TAG_NOT_FOUND|"
                    end try
                end repeat
                return output
            end tell
        end tell
        '''

        result = run_applescript(script)

        # Parse pipe-delimited groups (one per tag)
        groups = result.rstrip("|").split("|") if result.strip() else []

        id_sets = []
        for group in groups:
            group = group.strip()
            if group == "TAG_NOT_FOUND":
                return None  # Signal fallback to caller
            if group == "":
                id_sets.append(set())
            else:
                id_sets.append(set(group.split(",")))

        if not id_sets:
            return set()

        if mode == "and":
            # Intersection: task must be in ALL tag sets
            result_ids = id_sets[0]
            for s in id_sets[1:]:
                result_ids = result_ids & s
            return result_ids
        elif mode == "or":
            # Union: task must be in ANY tag set
            result_ids: set[str] = set()
            for s in id_sets:
                result_ids = result_ids | s
            return result_ids
        else:
            return None  # NOT mode not supported here

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

    def _build_task_ops_blocks(
        self,
        include_task_health: bool,
        include_last_activity: bool
    ) -> tuple[str, str, str, str]:
        """Build AppleScript blocks for global task batch reads.

        Returns (task_ops_preamble, task_ops_block, health_init, task_health_json_fields).
        Uses global batch reads + parallel counter lists instead of per-project IPC.
        """
        if not include_task_health and not include_last_activity:
            return "", "", "", ""

        # Global batch reads (~8 Apple Events total for ALL tasks)
        batch_reads = [
            "set ft to a reference to flattened tasks",
            "set taskCount to count of ft",
            "set allTaskProjIds to id of (containing project of ft)",
        ]
        if include_task_health:
            batch_reads += [
                "set allCompleted to completed of ft",
                "set allDropped to dropped of ft",
                "set allBlocked to blocked of ft",
                "set allDeferDates to effective defer date of ft",
                "set allDueDates to effective due date of ft",
            ]
        if include_last_activity:
            batch_reads += [
                "set allCreateDates to creation date of ft",
                "set allCompDates to completion date of ft",
            ]

        # Initialize parallel counter lists (one entry per project)
        init_lines = []
        if include_task_health:
            init_lines += [
                "set remainingCounts to {}",
                "set availableCounts to {}",
                "set overdueCounts to {}",
                "set deferredCounts to {}",
            ]
        if include_last_activity:
            init_lines.append("set latestActivityDates to {}")
        init_lines.append("repeat with idx from 1 to projCount")
        if include_task_health:
            init_lines += [
                "    set end of remainingCounts to 0",
                "    set end of availableCounts to 0",
                "    set end of overdueCounts to 0",
                "    set end of deferredCounts to 0",
            ]
        if include_last_activity:
            init_lines.append("    set end of latestActivityDates to missing value")
        init_lines.append("end repeat")

        # Single-pass accumulation: find project index, accumulate counters
        accum_lines = [
            "set todayDate to current date",
            "repeat with j from 1 to taskCount",
            "    set projIdx to 0",
            "    try",
            "        set taskProjId to item j of allTaskProjIds",
            "        repeat with k from 1 to projCount",
            "            if item k of ids is taskProjId then",
            "                set projIdx to k",
            "                exit repeat",
            "            end if",
            "        end repeat",
            "    end try",
            "    if projIdx > 0 then",
        ]
        if include_task_health:
            accum_lines += [
                "        try",
                "            set taskCompleted to item j of allCompleted",
                "            set taskDropped to item j of allDropped",
                "            if taskCompleted is false and taskDropped is false then",
                "                set item projIdx of remainingCounts to (item projIdx of remainingCounts) + 1",
                "                set taskBlocked to item j of allBlocked",
                "                set taskDeferred to false",
                "                try",
                "                    set deferDateVal to item j of allDeferDates",
                "                    if deferDateVal is not missing value and deferDateVal > todayDate then",
                "                        set taskDeferred to true",
                "                    end if",
                "                end try",
                "                if taskDeferred then",
                "                    set item projIdx of deferredCounts to (item projIdx of deferredCounts) + 1",
                "                else if taskBlocked is false then",
                "                    set item projIdx of availableCounts to (item projIdx of availableCounts) + 1",
                "                end if",
                "                try",
                "                    set dueDateVal to item j of allDueDates",
                "                    if dueDateVal is not missing value and dueDateVal < todayDate then",
                "                        set item projIdx of overdueCounts to (item projIdx of overdueCounts) + 1",
                "                    end if",
                "                end try",
                "            end if",
                "        end try",
            ]
        if include_last_activity:
            accum_lines += [
                "        try",
                "            set cDate to item j of allCreateDates",
                "            if cDate is not missing value then",
                "                set curMax to item projIdx of latestActivityDates",
                "                if curMax is missing value or cDate > curMax then",
                "                    set item projIdx of latestActivityDates to cDate",
                "                end if",
                "            end if",
                "        end try",
                "        try",
                "            set dDate to item j of allCompDates",
                "            if dDate is not missing value then",
                "                set curMax to item projIdx of latestActivityDates",
                "                if curMax is missing value or dDate > curMax then",
                "                    set item projIdx of latestActivityDates to dDate",
                "                end if",
                "            end if",
                "        end try",
            ]
        accum_lines += ["    end if", "end repeat"]

        # Join with indentation
        indent = "\n                "
        task_ops_preamble = indent.join(batch_reads)
        task_ops_preamble += indent + indent.join(init_lines)
        task_ops_preamble += indent + indent.join(accum_lines)

        # Per-project reads from counter lists (inside the project JSON loop)
        health_init = ""
        if include_task_health:
            health_init = """set remainingCount to item i of remainingCounts
                            set availableCount to item i of availableCounts
                            set overdueCount to item i of overdueCounts
                            set deferredCount to item i of deferredCounts
                            set hasDeferredOnly to (remainingCount > 0 and availableCount = 0)"""

        task_ops_block = ""
        if include_last_activity:
            task_ops_block = """try
                                set activityDate to item i of latestActivityDates
                                if activityDate is not missing value then
                                    set lastActivityStr to "\\"" & (activityDate as «class isot» as string) & "\\""
                                end if
                            end try"""

        task_health_json_fields = ""
        if include_task_health:
            task_health_json_fields = (' & ", " & ¬\n'
                '                            "\\"remainingCount\\": " & remainingCount & ", " & ¬\n'
                '                            "\\"availableCount\\": " & availableCount & ", " & ¬\n'
                '                            "\\"overdueCount\\": " & overdueCount & ", " & ¬\n'
                '                            "\\"deferredCount\\": " & deferredCount & ", " & ¬\n'
                '                            "\\"hasDeferredOnly\\": " & hasDeferredOnly')

        return task_ops_preamble, task_ops_block, health_init, task_health_json_fields

    def _validate_get_projects_params(
        self,
        *,
        modified_after: Optional[str],
        modified_before: Optional[str],
        sort_by: Optional[str],
        sort_order: str,
    ) -> None:
        """Validate get_projects parameters, raising ValueError for invalid values."""
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

        valid_sort_by = ["name", None]
        valid_sort_order = ["asc", "desc"]
        if sort_by not in valid_sort_by:
            raise ValueError(f"Invalid sort_by value: {sort_by}. Must be one of: {[v for v in valid_sort_by if v is not None]}")
        if sort_order not in valid_sort_order:
            raise ValueError(f"Invalid sort_order value: {sort_order}. Must be one of: {valid_sort_order}")

    def _post_process_projects(
        self,
        projects: list[dict[str, Any]],
        *,
        modified_after: Optional[str],
        modified_before: Optional[str],
        min_task_count: Optional[int],
        has_overdue_tasks: Optional[bool],
        has_no_due_dates: Optional[bool],
        query: Optional[str],
        include_task_health: bool,
        stalled_only: bool,
        sort_by: Optional[str],
        sort_order: str,
    ) -> list[dict[str, Any]]:
        """Post-process projects: compute types, apply filters, sort."""
        # Compute projectType from singleton and sequential flags
        for p in projects:
            if p.get("singletonActionHolder"):
                p["projectType"] = "single_actions"
            elif p.get("sequential"):
                p["projectType"] = "sequential"
            else:
                p["projectType"] = "parallel"

        # Apply date range filtering
        if modified_after or modified_before:
            projects = self._filter_by_date_range(
                projects, None, None, modified_after, modified_before
            )

        # Apply conditional filters
        if min_task_count is not None or has_overdue_tasks is not None or has_no_due_dates is not None:
            projects = self._filter_projects_by_conditions(
                projects, min_task_count, has_overdue_tasks, has_no_due_dates
            )

        # Apply query filter
        if query:
            query_lower = query.lower()
            projects = [
                p for p in projects
                if query_lower in p.get('name', '').lower()
                or query_lower in p.get('note', '').lower()
                or query_lower in p.get('folderPath', '').lower()
            ]

        # Compute stalled field when task health is available
        if include_task_health:
            for p in projects:
                p["stalled"] = (
                    p.get("status") == "active status"
                    and p.get("availableCount", 1) == 0
                    and not p.get("hasDeferredOnly", False)
                )

        # Filter to stalled projects only
        if stalled_only:
            projects = [p for p in projects if p.get("stalled", False)]

        # Apply sorting
        if sort_by:
            reverse = (sort_order == "desc")
            projects = sorted(projects, key=lambda p: p.get("name", "").lower(), reverse=reverse)

        return projects

    def get_projects(
        self,
        project_id: Optional[str] = None,  # NEW (Phase 3.2): Filter to specific project
        include_full_notes: bool = False,  # NEW (Phase 3.2): Return full notes
        on_hold_only: bool = False,
        modified_after: Optional[str] = None,
        modified_before: Optional[str] = None,
        min_task_count: Optional[int] = None,
        has_overdue_tasks: Optional[bool] = None,
        has_no_due_dates: Optional[bool] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        query: Optional[str] = None,
        include_task_health: bool = False,
        include_last_activity: bool = False,
        stalled_only: bool = False,
        timeout: int = 90
    ) -> list[dict[str, Any]]:
        """Get projects with their folder/hierarchy information using AppleScript.

        Args:
            project_id: NEW (Phase 3.2) - Filter to specific project by ID (consolidates get_project())
            include_full_notes: NEW (Phase 3.2) - Return full note content (consolidates get_note())
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
        self._validate_get_projects_params(
            modified_after=modified_after, modified_before=modified_before,
            sort_by=sort_by, sort_order=sort_order,
        )

        # Build project source (specific project or all projects)
        # NEW (Phase 3.2): project_id parameter
        if project_id:
            project_id_escaped = self._escape_applescript_string(project_id)
            project_source = f'(flattened projects whose id is "{project_id_escaped}")'
        else:
            project_source = 'flattened projects'

        # stalled_only requires task health data
        if stalled_only:
            include_task_health = True

        # Build task ops AppleScript blocks via helper
        task_ops_preamble, task_ops_block, health_init, task_health_json_fields = \
            self._build_task_ops_blocks(include_task_health, include_last_activity)

        # Build on_hold filter condition
        on_hold_condition = ""
        if on_hold_only:
            on_hold_condition = ' or projStatus is not "on hold status"'

        script = '''
        use AppleScript version "2.4"
        use scripting additions
        use framework "Foundation"

        set output to ""

        tell application "OmniFocus"
            tell front document
                -- Pre-build folder path cache (folders are few, typically <50)
                set ff to a reference to flattened folders
                set folderCount to count of ff
                set folderIds to id of ff
                set folderNames to name of ff
                set folderContainerIds to id of (container of ff)
                set folderContainerClasses to class of (container of ff)

                set folderPaths to {{}}
                repeat with i from 1 to folderCount
                    if item i of folderContainerClasses is folder then
                        set parentId to item i of folderContainerIds
                        set parentPath to ""
                        repeat with j from 1 to (i - 1)
                            if item j of folderIds is parentId then
                                set parentPath to item j of folderPaths
                                exit repeat
                            end if
                        end repeat
                        if parentPath is "" then
                            set end of folderPaths to item i of folderNames
                        else
                            set end of folderPaths to parentPath & " > " & (item i of folderNames)
                        end if
                    else
                        set end of folderPaths to item i of folderNames
                    end if
                end repeat

                -- Batch read all project properties (one Apple Event per property type)
                set fp to a reference to {project_source}
                set projCount to count of fp
                set ids to id of fp
                set names to name of fp
                set notes to note of fp
                set statuses to status of fp
                set seqs to sequential of fp
                set singletons to singleton action holder of fp
                set completionsByChildren to completed by children of fp
                set createDates to creation date of fp
                set modDates to modification date of fp
                set compDates to completion date of fp
                set dropDates to dropped date of fp
                set lastRevDates to last review date of fp
                set nextRevDates to next review date of fp
                set projDueDates to due date of fp
                set projDeferDates to defer date of fp
                set projPlannedDates to planned date of fp
                set containerIds to id of (container of fp)
                set containerClasses to class of (container of fp)

                {task_ops_preamble}

                -- Iterate by index (all reads are local — no per-project IPC)
                repeat with i from 1 to projCount
                    try
                        set projStatus to item i of statuses as text

                        -- Skip dropped projects (and on_hold filter)
                        if projStatus is "dropped status"{on_hold_condition} then
                            error "skip project"
                        end if

                        -- Look up folder path from cache
                        set folderPath to ""
                        if item i of containerClasses is folder then
                            set projContainerId to item i of containerIds
                            repeat with j from 1 to folderCount
                                if item j of folderIds is projContainerId then
                                    set folderPath to item j of folderPaths
                                    exit repeat
                                end if
                            end repeat
                        end if

                        -- Format dates (local conversion, no IPC)
                        set creationDateStr to "null"
                        try
                            set createVal to item i of createDates
                            if createVal is not missing value then
                                set creationDateStr to "\\"" & (createVal as «class isot» as string) & "\\""
                            end if
                        end try

                        set modDateStr to "null"
                        try
                            set modVal to item i of modDates
                            if modVal is not missing value then
                                set modDateStr to "\\"" & (modVal as «class isot» as string) & "\\""
                            end if
                        end try

                        set completionDateStr to "null"
                        try
                            set compVal to item i of compDates
                            if compVal is not missing value then
                                set completionDateStr to "\\"" & (compVal as «class isot» as string) & "\\""
                            end if
                        end try

                        set droppedDateStr to "null"
                        try
                            set dropVal to item i of dropDates
                            if dropVal is not missing value then
                                set droppedDateStr to "\\"" & (dropVal as «class isot» as string) & "\\""
                            end if
                        end try

                        set lastActivityStr to "null"

                        set lastReviewDateStr to "null"
                        try
                            set lastRevVal to item i of lastRevDates
                            if lastRevVal is not missing value then
                                set lastReviewDateStr to "\\"" & (lastRevVal as «class isot» as string) & "\\""
                            end if
                        end try

                        set nextReviewDateStr to "null"
                        try
                            set nextRevVal to item i of nextRevDates
                            if nextRevVal is not missing value then
                                set nextReviewDateStr to "\\"" & (nextRevVal as «class isot» as string) & "\\""
                            end if
                        end try

                        set dueDateStr to ""
                        set dVal to item i of projDueDates
                        if dVal is not missing value then
                            set dueDateStr to (dVal as «class isot» as string)
                        end if

                        set deferDateStr to ""
                        set dVal to item i of projDeferDates
                        if dVal is not missing value then
                            set deferDateStr to (dVal as «class isot» as string)
                        end if

                        set plannedDateStr to ""
                        set pVal to item i of projPlannedDates
                        if pVal is not missing value then
                            set plannedDateStr to (pVal as «class isot» as string)
                        end if

                        -- Per-project task operations (only when task_health/last_activity requested)
                        {health_init}
                        {task_ops_block}

                        -- Build JSON
                        set jsonLine to "{{" & ¬
                            "\\"id\\": \\"" & (item i of ids) & "\\", " & ¬
                            "\\"name\\": \\"" & my escapeJSON(item i of names) & "\\", " & ¬
                            "\\"note\\": \\"" & my escapeJSON(item i of notes) & "\\", " & ¬
                            "\\"status\\": \\"" & projStatus & "\\", " & ¬
                            "\\"sequential\\": " & ((item i of seqs) as text) & ", " & ¬
                            "\\"singletonActionHolder\\": " & ((item i of singletons) as text) & ", " & ¬
                            "\\"completedByChildren\\": " & ((item i of completionsByChildren) as text) & ", " & ¬
                            "\\"folderPath\\": \\"" & my escapeJSON(folderPath) & "\\", " & ¬
                            "\\"creationDate\\": " & creationDateStr & ", " & ¬
                            "\\"modificationDate\\": " & modDateStr & ", " & ¬
                            "\\"completionDate\\": " & completionDateStr & ", " & ¬
                            "\\"droppedDate\\": " & droppedDateStr & ", " & ¬
                            "\\"lastActivityDate\\": " & lastActivityStr & ", " & ¬
                            "\\"lastReviewDate\\": " & lastReviewDateStr & ", " & ¬
                            "\\"dueDate\\": \\"" & dueDateStr & "\\", " & ¬
                            "\\"deferDate\\": \\"" & deferDateStr & "\\", " & ¬
                            "\\"plannedDate\\": \\"" & plannedDateStr & "\\", " & ¬
                            "\\"nextReviewDate\\": " & nextReviewDateStr{task_health_json_fields} & ¬
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

        script = script.format(
            project_source=project_source,
            on_hold_condition=on_hold_condition,
            task_ops_preamble=task_ops_preamble,
            health_init=health_init,
            task_ops_block=task_ops_block,
            task_health_json_fields=task_health_json_fields,
        )

        try:
            result = run_applescript(script, timeout=timeout)
            if result:
                projects = json.loads(result)

                return self._post_process_projects(
                    projects,
                    modified_after=modified_after,
                    modified_before=modified_before,
                    min_task_count=min_task_count,
                    has_overdue_tasks=has_overdue_tasks,
                    has_no_due_dates=has_no_due_dates,
                    query=query,
                    include_task_health=include_task_health,
                    stalled_only=stalled_only,
                    sort_by=sort_by,
                    sort_order=sort_order,
                )
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
        sequential: bool = False,
        project_type: Optional[str] = None,
        review_interval_weeks: Optional[int] = None,
        completed_by_children: Optional[bool] = None,
        due_date: Optional[str] = None,
        defer_date: Optional[str] = None,
        planned_date: Optional[str] = None,
    ) -> str:
        """Create a new project in OmniFocus.

        Args:
            name: The name of the project
            note: Optional note/description for the project
            folder_path: Optional folder path (e.g., "Work > Clients") - folder must exist
            sequential: If True, tasks must be completed in order (default: False, parallel).
                Ignored when project_type is provided.
            project_type: Project type: "parallel", "sequential", or "single_actions".
                Overrides sequential when provided.
            review_interval_weeks: Optional review interval in weeks for GTD review cycle
            due_date: Due date in ISO 8601 format (e.g., "2025-10-15" or "2025-10-15T17:00:00")
            defer_date: Defer date in ISO 8601 format (when project becomes available)
            planned_date: Planned date in ISO 8601 format (when you plan to work on the project)

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

        # Resolve effective type from project_type (takes precedence) or sequential flag
        if project_type is not None:
            effective_type = project_type
        elif sequential:
            effective_type = "sequential"
        else:
            effective_type = "parallel"

        # Build properties
        properties = [f'name:"{name_escaped}"']
        if note:
            properties.append(f'note:"{note_escaped}"')
        if effective_type == "single_actions":
            properties.append('singleton action holder:true')
            properties.append('sequential:false')
        elif effective_type == "sequential":
            properties.append('sequential:true')
        else:
            properties.append('sequential:false')
        if review_interval_weeks is not None:
            # Convert weeks to days for OmniFocus review interval
            review_days = review_interval_weeks * 7
            properties.append(f'review interval:{review_days}')
        if completed_by_children is not None:
            properties.append(f'completed by children:{str(completed_by_children).lower()}')

        properties_str = ", ".join(properties)

        # Build date commands (set after creation, like create_task)
        date_commands = []
        if due_date:
            date_commands.append(f'set due date of newProject to date "{self._iso_to_applescript_date(due_date)}"')
        if defer_date:
            date_commands.append(f'set defer date of newProject to date "{self._iso_to_applescript_date(defer_date)}"')
        if planned_date:
            date_commands.append(f'set planned date of newProject to date "{self._iso_to_applescript_date(planned_date)}"')
        date_commands_str = "\n                    ".join(date_commands) if date_commands else ""

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
                    {date_commands_str}
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
                    {date_commands_str}
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
        project_type: Optional[str] = None,
        status: Optional[Union[ProjectStatus, str]] = None,
        review_interval_weeks: Optional[int] = None,
        last_reviewed: Optional[str] = None,
        next_review_date: Optional[str] = None,
        completed_by_children: Optional[bool] = None,
        due_date: Optional[str] = None,
        defer_date: Optional[str] = None,
        planned_date: Optional[str] = None,
    ) -> dict:
        """Update properties of an existing project (NEW API - Phase 2).

        Args:
            project_id: The ID of the project to update
            project_name: New project name (optional)
            folder_path: Folder path to move project to (e.g., "Work > Projects")
            note: New project note (optional)
            sequential: New sequential setting (optional)
            status: Project status (ProjectStatus enum or string: "active", "on_hold", "done", "dropped")
            review_interval_weeks: Review interval in weeks (0 to clear)
            last_reviewed: Last reviewed date in ISO format or "now" - OmniFocus calculates next review automatically (optional)
            next_review_date: Next review date in ISO format - Explicit override of calculated date (optional)
            due_date: Due date in ISO 8601 format, or "" to clear (optional)
            defer_date: Defer date in ISO 8601 format, or "" to clear (optional)
            planned_date: Planned date in ISO 8601 format, or "" to clear (optional)

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
            "project_type": project_type,
            "status": status,
            "review_interval_weeks": review_interval_weeks,
            "last_reviewed": last_reviewed,
            "next_review_date": next_review_date,
            "completed_by_children": completed_by_children,
            "due_date": due_date,
            "defer_date": defer_date,
            "planned_date": planned_date,
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

        if project_type is not None:
            valid_types = ["parallel", "sequential", "single_actions"]
            if project_type not in valid_types:
                raise ValueError(f"Invalid project_type: {project_type}. Must be one of: {', '.join(valid_types)}")
            if project_type == "single_actions":
                properties.append('singleton action holder:true')
                properties.append('sequential:false')
            elif project_type == "sequential":
                properties.append('singleton action holder:false')
                properties.append('sequential:true')
            else:  # parallel
                properties.append('singleton action holder:false')
                properties.append('sequential:false')
            updated_fields.append("project_type")

        # Build status command (separate from properties)
        status_command = ""
        if status_str is not None:
            # OmniFocus projects use enum values for status (e.g. 'active status')
            # and 'mark complete'/'mark dropped' verbs for done/dropped.
            # Using 'set dropped of theProject to true/false' fails for projects.
            if status_str == "done":
                status_command = 'mark complete theProject'
            elif status_str == "dropped":
                status_command = 'mark dropped theProject'
            elif status_str == "active":
                status_command = 'set status of theProject to active status'
            elif status_str == "on_hold":
                status_command = 'set status of theProject to on hold'
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
                reviewed_command = 'set last review date of theProject to (current date)'
            else:
                # Parse ISO date
                as_date = self._iso_to_applescript_date(last_reviewed)
                reviewed_command = f'set last review date of theProject to date "{as_date}"'
            updated_fields.append("last_reviewed")

        # Build next review date command
        next_review_command = ""
        if next_review_date is not None:
            as_date = self._iso_to_applescript_date(next_review_date)
            next_review_command = f'set next review date of theProject to date "{as_date}"'
            updated_fields.append("next_review_date")

        # Build date commands (due, defer, planned)
        date_commands_list = []
        for field_name, field_val, field_key in [
            ("due date", due_date, "due_date"),
            ("defer date", defer_date, "defer_date"),
            ("planned date", planned_date, "planned_date"),
        ]:
            if field_val is not None:
                if field_val == "":
                    date_commands_list.append(f"set {field_name} of theProject to missing value")
                else:
                    as_date = self._iso_to_applescript_date(field_val)
                    date_commands_list.append(f'set {field_name} of theProject to date "{as_date}"')
                updated_fields.append(field_key)
        date_commands_str = "\n                    ".join(date_commands_list) if date_commands_list else ""

        # Build completed by children command
        completed_by_children_command = ""
        if completed_by_children is not None:
            completed_by_children_command = f'set completed by children of theProject to {str(completed_by_children).lower()}'
            updated_fields.append("completed_by_children")

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
                    {next_review_command}
                    {date_commands_str}
                    {completed_by_children_command}
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
        next_review_date: Optional[str] = None,
        due_date: Optional[str] = None,
        defer_date: Optional[str] = None,
        planned_date: Optional[str] = None,
        **kwargs  # Catch invalid parameters like project_name, note
    ) -> dict:
        """Update properties of multiple projects (NEW API - Phase 2, Batch Function).

        This is the BATCH version of update_project(). It updates multiple projects
        with the same values.

        IMPORTANT: This function does NOT accept project_name or note parameters
        because those require unique values for each project. Use update_project()
        for those fields.

        Args:
            project_ids: Single project ID (str) or list of project IDs
            folder_path: Folder path to move projects to (e.g., "Work > Projects")
            sequential: Sequential setting (optional)
            status: Project status (ProjectStatus enum or string: "active", "on_hold", "done", "dropped")
            review_interval_weeks: Review interval in weeks (0 to clear)
            last_reviewed: Last reviewed date in ISO format or "now" - OmniFocus calculates next review automatically (optional)
            next_review_date: Next review date in ISO format - Explicit override of calculated date (optional)
            due_date: Due date in ISO 8601 format, or "" to clear (optional)
            defer_date: Defer date in ISO 8601 format, or "" to clear (optional)
            planned_date: Planned date in ISO 8601 format, or "" to clear (optional)

        Returns:
            dict: {
                "updated_count": int,  # Number of successfully updated projects
                "failed_count": int,    # Number of failed updates
                "updated_ids": list[str],  # IDs of successfully updated projects
                "failures": [{"project_id": str, "error": str}, ...]  # Failed updates with errors
            }

        Note:
            ``updated_ids`` is approximate on partial failure — it lists
            the first N IDs from the input, not necessarily the ones that
            succeeded.

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
                review_interval_weeks is None and last_reviewed is None and
                next_review_date is None and due_date is None and
                defer_date is None and planned_date is None):
            raise ValueError("At least one field must be provided to update")

        # Normalize project_ids to list
        if isinstance(project_ids, str):
            ids_list = [project_ids]
        else:
            ids_list = project_ids

        # Classify fields into bulk-settable (or-chain) vs per-project (repeat loop)
        # Bulk: sequential, status, review_interval_weeks, last_reviewed, next_review_date
        # Per-project: folder_path (move operation)
        has_bulk = False
        has_per_project = False

        bulk_commands = []
        or_chain_target = self._build_whose_or_chain(ids_list, "flattened project")

        # --- Bulk-settable fields ---

        if sequential is not None:
            bulk_commands.append(
                f"set sequential of ({or_chain_target}) to {str(sequential).lower()}"
            )
            has_bulk = True

        if status is not None:
            if isinstance(status, ProjectStatus):
                status_str = status.value
            elif isinstance(status, str):
                valid_statuses = ["active", "on_hold", "done", "dropped"]
                if status.lower() not in valid_statuses:
                    raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}")
                status_str = status.lower()
            else:
                raise ValueError(f"status must be ProjectStatus enum or string, got {type(status)}")

            if status_str == "done":
                bulk_commands.append(f"mark complete ({or_chain_target})")
            elif status_str == "dropped":
                bulk_commands.append(f"mark dropped ({or_chain_target})")
            elif status_str == "active":
                bulk_commands.append(f"set status of ({or_chain_target}) to active status")
            elif status_str == "on_hold":
                bulk_commands.append(f"set status of ({or_chain_target}) to on hold")
            has_bulk = True

        if review_interval_weeks is not None:
            bulk_commands.append(
                f"set review interval of ({or_chain_target}) to {{unit:week, steps:{review_interval_weeks}, fixed:true}}"
            )
            has_bulk = True

        if last_reviewed is not None:
            if last_reviewed.lower() == "now" or last_reviewed == "":
                bulk_commands.append(
                    f"set last review date of ({or_chain_target}) to (current date)"
                )
            else:
                as_date = self._iso_to_applescript_date(last_reviewed)
                bulk_commands.append(
                    f'set last review date of ({or_chain_target}) to date "{as_date}"'
                )
            has_bulk = True

        if next_review_date is not None:
            as_date = self._iso_to_applescript_date(next_review_date)
            bulk_commands.append(
                f'set next review date of ({or_chain_target}) to date "{as_date}"'
            )
            has_bulk = True

        for field_name, field_val in [("due date", due_date), ("defer date", defer_date), ("planned date", planned_date)]:
            if field_val is not None:
                if field_val == "":
                    bulk_commands.append(
                        f"set {field_name} of ({or_chain_target}) to missing value"
                    )
                else:
                    as_date = self._iso_to_applescript_date(field_val)
                    bulk_commands.append(
                        f'set {field_name} of ({or_chain_target}) to date "{as_date}"'
                    )
                has_bulk = True

        # --- Per-project fields (need repeat loop) ---

        per_project_commands = []

        if folder_path is not None:
            # Build folder navigation commands (reuse existing logic)
            folder_parts = [part.strip() for part in folder_path.split('>')]
            if len(folder_parts) == 1:
                folder_escaped = self._escape_applescript_string(folder_parts[0])
                per_project_commands.append(f'''
                    set targetFolder to first folder whose name is "{folder_escaped}"
                    move theProject to end of projects of targetFolder''')
            else:
                folder_names_list = ', '.join(f'"{self._escape_applescript_string(p)}"' for p in folder_parts)
                per_project_commands.append(f'''
                    set folderNames to {{{folder_names_list}}}
                    set targetFolder to missing value
                    repeat with i from 1 to count of folderNames
                        set folderName to item i of folderNames
                        if i is 1 then
                            repeat with f in folders
                                if name of f is folderName then
                                    set targetFolder to f
                                    exit repeat
                                end if
                            end repeat
                        else
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
                    move theProject to end of projects of targetFolder''')
            has_per_project = True

        # --- Build AppleScript ---

        bulk_block = ""
        if has_bulk:
            bulk_block = "\n                ".join(bulk_commands)

        per_project_block = ""
        if has_per_project:
            ids_applescript = ", ".join(
                [f'"{self._escape_applescript_string(pid)}"' for pid in ids_list]
            )
            per_project_cmds_str = "\n                        ".join(per_project_commands)
            per_project_block = f'''
                set projectIdList to {{{ids_applescript}}}
                set successCount to 0

                repeat with projectId in projectIdList
                    try
                        set theProject to first flattened project whose id is projectId
                        {per_project_cmds_str}
                        set successCount to successCount + 1
                    on error
                        -- Project not found or update failed, skip
                    end try
                end repeat'''

        if has_bulk and not has_per_project:
            count_expr = f"count of ({or_chain_target})"
            script = f'''
        tell application "OmniFocus"
            tell front document
                set preCount to ({count_expr})
                {bulk_block}
                return preCount as text
            end tell
        end tell
        '''
        elif has_per_project and not has_bulk:
            script = f'''
        tell application "OmniFocus"
            tell front document
                {per_project_block}
                return successCount as text
            end tell
        end tell
        '''
        else:
            # Hybrid: bulk commands first, then repeat loop
            script = f'''
        tell application "OmniFocus"
            tell front document
                {bulk_block}
                {per_project_block}
                return successCount as text
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            updated_count = int(result.strip())
            total_count = len(ids_list)
            failed_count = total_count - updated_count

            updated_ids = ids_list[:updated_count] if updated_count > 0 else []

            return {
                "updated_count": updated_count,
                "failed_count": failed_count,
                "updated_ids": updated_ids,
                "failures": []  # Batch AppleScript doesn't provide per-project failure detail
            }
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error batch updating projects: {e.stderr}")



    def create_task(
        self,
        task_name: str,
        project_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        note: Optional[str] = None,
        due_date: Optional[str] = None,
        defer_date: Optional[str] = None,
        planned_date: Optional[str] = None,
        flagged: bool = False,
        tags: Optional[list[str]] = None,
        estimated_minutes: Optional[int] = None,
        sequential: bool = False,
        completed_by_children: bool = False
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
            planned_date: Planned date in ISO 8601 format (when you plan to work on the task)
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
        if sequential:
            properties.append('sequential:true')
        if completed_by_children:
            properties.append('completed by children:true')
        if estimated_minutes is not None:
            properties.append(f'estimated minutes:{estimated_minutes}')

        # Build date commands
        date_commands = []
        if due_date:
            date_commands.append(f'set due date of newTask to date "{self._iso_to_applescript_date(due_date)}"')
        if defer_date:
            date_commands.append(f'set defer date of newTask to date "{self._iso_to_applescript_date(defer_date)}"')
        if planned_date:
            date_commands.append(f'set planned date of newTask to date "{self._iso_to_applescript_date(planned_date)}"')

        # Build tag assignment commands
        tag_commands = []
        if tags:
            for tag in tags:
                tag_escaped = self._escape_applescript_string(tag)
                tag_commands.append(f'''
                    set tagObj to first flattened tag whose name is "{tag_escaped}"
                    add tagObj to tags of newTask''')

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

    @staticmethod
    def _rrule_to_summary(rrule: str) -> str:
        """Convert an iCalendar RRULE string to a human-readable summary.

        Handles common OmniFocus recurrence patterns (DAILY, WEEKLY, MONTHLY,
        YEARLY with INTERVAL and BYDAY). Falls back to the raw RRULE string
        for anything unparseable.

        Args:
            rrule: Raw RRULE string (e.g., "FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,WE,FR")

        Returns:
            Human-readable summary (e.g., "Every 2 weeks on Mon, Wed, Fri")
        """
        if not rrule:
            return ""

        # Parse RRULE parts into dict
        parts = {}
        try:
            for part in rrule.split(";"):
                if "=" in part:
                    key, value = part.split("=", 1)
                    parts[key] = value
        except (ValueError, AttributeError):
            return rrule

        freq = parts.get("FREQ")
        if not freq:
            return rrule

        freq_map = {
            "DAILY": ("day", "days"),
            "WEEKLY": ("week", "weeks"),
            "MONTHLY": ("month", "months"),
            "YEARLY": ("year", "years"),
        }

        if freq not in freq_map:
            return rrule

        singular, plural = freq_map[freq]
        interval = int(parts.get("INTERVAL", "1"))

        if interval == 1:
            summary = f"Every {singular}"
        else:
            summary = f"Every {interval} {plural}"

        # Append day names for weekly rules
        byday = parts.get("BYDAY")
        if byday and freq == "WEEKLY":
            day_map = {
                "MO": "Mon", "TU": "Tue", "WE": "Wed", "TH": "Thu",
                "FR": "Fri", "SA": "Sat", "SU": "Sun",
            }
            day_names = [day_map.get(d, d) for d in byday.split(",")]
            summary += f" on {', '.join(day_names)}"

        return summary

    def _post_process_tasks(
        self,
        tasks: list[dict[str, Any]],
        *,
        tag_filter: Optional[list[str]],
        tag_filter_mode: str,
        tag_prefiltered_ids: Optional[set],
        created_after: Optional[str],
        created_before: Optional[str],
        modified_after: Optional[str],
        modified_before: Optional[str],
        recurring_only: Optional[bool],
        query: Optional[str],
        sort_by: Optional[str],
        sort_order: str,
    ) -> list[dict[str, Any]]:
        """Post-process tasks returned from AppleScript: normalize and filter.

        Handles repetition normalization, Python-side tag/date/recurring/query
        filtering, and sorting.
        """
        # Normalize repetitionMethod values
        for task in tasks:
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

            # Compute repeatSummary from RRULE
            rrule = task.get('recurrence')
            if rrule:
                task['repeatSummary'] = OmniFocusConnector._rrule_to_summary(rrule)
            else:
                task['repeatSummary'] = None

        # Apply Python-based tag filtering
        # Skip when tag pre-filter already narrowed the task set via whose ID clause
        if tag_filter and len(tag_filter) > 0 and tag_prefiltered_ids is None:
            if tag_filter_mode == "and":
                tasks = self._filter_tasks_by_tags(tasks, tag_filter, tag_filter_mode)
            elif tag_filter_mode in ["or", "not"]:
                tasks = self._filter_tasks_by_tags(tasks, tag_filter, tag_filter_mode)

        # Apply date range filtering
        if created_after or created_before or modified_after or modified_before:
            tasks = self._filter_by_date_range(
                tasks, created_after, created_before,
                modified_after, modified_before
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

    def _validate_get_tasks_params(
        self,
        *,
        created_after: Optional[str],
        created_before: Optional[str],
        modified_after: Optional[str],
        modified_before: Optional[str],
        tag_filter_mode: str,
        sort_by: Optional[str],
        sort_order: str,
        due_relative: Optional[str],
        defer_relative: Optional[str],
    ) -> None:
        """Validate get_tasks parameters, raising ValueError for invalid values."""
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

        valid_tag_filter_modes = ["and", "or", "not"]
        if tag_filter_mode not in valid_tag_filter_modes:
            raise ValueError(f"Invalid tag_filter_mode value: {tag_filter_mode}. Must be one of: {valid_tag_filter_modes}")

        valid_sort_by = ["name", "due_date", "defer_date", None]
        valid_sort_order = ["asc", "desc"]
        if sort_by not in valid_sort_by:
            raise ValueError(f"Invalid sort_by value: {sort_by}. Must be one of: {[v for v in valid_sort_by if v is not None]}")
        if sort_order not in valid_sort_order:
            raise ValueError(f"Invalid sort_order value: {sort_order}. Must be one of: {valid_sort_order}")

        valid_due_relative = ["today", "tomorrow", "this_week", "next_week", "overdue", None]
        valid_defer_relative = ["today", "tomorrow", "this_week", "next_week", None]
        if due_relative not in valid_due_relative:
            raise ValueError(f"Invalid due_relative value: {due_relative}. Must be one of: {valid_due_relative[:-1]}")
        if defer_relative not in valid_defer_relative:
            raise ValueError(f"Invalid defer_relative value: {defer_relative}. Must be one of: {valid_defer_relative[:-1]}")

    def _build_task_source(
        self,
        *,
        task_id: Optional[str],
        parent_task_id: Optional[str],
        inbox_only: bool,
        project_id: Optional[str],
        include_completed: bool,
        flagged_only: bool,
        next_only: bool,
        dropped_only: bool,
        blocked_only: bool,
        overdue: bool,
        query: Optional[str],
        tag_prefiltered_ids: Optional[set],
    ) -> tuple[str, bool]:
        """Build AppleScript task source expression and whose conditions.

        Returns (task_source, whose_active) where task_source is the AppleScript
        expression to get tasks and whose_active indicates if whose filtering is used.
        """
        if task_id:
            task_id_escaped = self._escape_applescript_string(task_id)
            return f'(flattened tasks whose id is "{task_id_escaped}")', False
        elif parent_task_id:
            parent_id_escaped = self._escape_applescript_string(parent_task_id)
            parent_filter = f'whose id is "{parent_id_escaped}"'
            return f'tasks of (first flattened task {parent_filter})', False
        elif inbox_only:
            return 'inbox tasks', False
        elif project_id:
            project_id_escaped = self._escape_applescript_string(project_id)
            project_filter = f'whose id is "{project_id_escaped}"'
            return f'flattened tasks of (first flattened project {project_filter})', False
        else:
            # Build whose conditions for filters that OmniFocus can evaluate natively
            whose_conditions: list[str] = []
            if not include_completed:
                whose_conditions.append("completed is false")
            if flagged_only:
                whose_conditions.append("flagged is true")
            if next_only:
                whose_conditions.append("next is true")
            if dropped_only:
                whose_conditions.append("dropped is true")
            if blocked_only:
                whose_conditions.append("blocked is true")
            if overdue:
                whose_conditions.append("effective due date < (current date)")
            if query:
                query_escaped = self._escape_applescript_string(query)
                whose_conditions.append(f'(name contains "{query_escaped}" or note contains "{query_escaped}")')

            # Tag pre-filter: add ID-based whose condition from tag-side query
            if tag_prefiltered_ids is not None and len(tag_prefiltered_ids) > 0:
                id_conditions = " or ".join(
                    f'id is "{self._escape_applescript_string(tid)}"'
                    for tid in tag_prefiltered_ids
                )
                whose_conditions.append(f'({id_conditions})')

            if whose_conditions:
                return f'(flattened tasks whose {" and ".join(whose_conditions)})', True
            else:
                return 'flattened tasks', False

    def _build_task_filter_checks(
        self,
        *,
        include_completed: bool,
        flagged_only: bool,
        available_only: bool,
        overdue: bool,
        dropped_only: bool,
        blocked_only: bool,
        next_only: bool,
        due_relative: Optional[str],
        defer_relative: Optional[str],
        max_estimated_minutes: Optional[int],
        has_estimate: Optional[bool],
        tag_filter: Optional[list[str]],
        tag_filter_mode: str,
        tag_prefiltered_ids: Optional[set],
        query: Optional[str],
        whose_active: bool,
        on_hold_available_check_batch: str,
    ) -> dict[str, str]:
        """Generate batch-mode AppleScript filter check strings for get_tasks.

        All checks use indexed batch data (e.g. 'item i of taskComps') instead
        of per-task property reads. Checks gated on 'whose_active' are skipped
        when whose clauses already handle that filter natively.
        """
        checks: dict[str, str] = {}

        # --- Filters that whose handles when active (skip if whose_active) ---

        completion_check_batch = ""
        if not include_completed and not whose_active:
            completion_check_batch = """
                        if item i of taskComps then error "skip completed task"
                        """
        checks['completion_check_batch'] = completion_check_batch

        flagged_check_batch = ""
        if flagged_only and not whose_active:
            flagged_check_batch = """
                        if not (item i of taskFlags) then error "skip non-flagged task"
                        """
        checks['flagged_check_batch'] = flagged_check_batch

        dropped_check_batch = ""
        if dropped_only and not whose_active:
            dropped_check_batch = """
                        if not (item i of taskDrops) then error "skip non-dropped task"
                        """
        checks['dropped_check_batch'] = dropped_check_batch

        blocked_check_batch = ""
        if blocked_only and not whose_active:
            blocked_check_batch = """
                        if not (item i of taskBlocks) then error "skip non-blocked task"
                        """
        checks['blocked_check_batch'] = blocked_check_batch

        next_check_batch = ""
        if next_only and not whose_active:
            next_check_batch = """
                        if not (item i of taskNexts) then error "skip non-next task"
                        """
        checks['next_check_batch'] = next_check_batch

        overdue_check_batch = ""
        if overdue and not whose_active:
            overdue_check_batch = """
                        set taskDue to contents of (item i of dueDates)
                        if taskDue is missing value then error "skip non-overdue task"
                        if taskDue ≥ (current date) then error "skip non-overdue task"
                        """
        checks['overdue_check_batch'] = overdue_check_batch

        query_check_batch = ""
        if query and not whose_active:
            query_escaped = self._escape_applescript_string(query)
            query_check_batch = f"""
                        set queryCheck to false
                        if (item i of taskNames) contains "{query_escaped}" then set queryCheck to true
                        if (item i of taskNotes) contains "{query_escaped}" then set queryCheck to true
                        if not queryCheck then error "skip non-matching task"
                        """
        checks['query_check_batch'] = query_check_batch

        # --- Filters always applied in batch mode (not handled by whose) ---

        available_check_batch = ""
        if available_only:
            available_check_batch = f"""
                        -- Skip unavailable tasks (using batch-read data)
                        if item i of taskDrops then error "skip unavailable"
                        if item i of taskBlocks then error "skip unavailable"
                        if item i of effComps then error "skip unavailable"
                        if item i of effDrops then error "skip unavailable"
                        set dVal to contents of (item i of deferDates)
                        if dVal is not missing value then
                            if dVal > (current date) then error "skip unavailable"
                        end if{on_hold_available_check_batch}"""
        checks['available_check_batch'] = available_check_batch

        due_relative_check_batch = ""
        if due_relative:
            if due_relative == "today":
                due_relative_check_batch = """
                        set taskDue to contents of (item i of dueDates)
                        if taskDue is missing value then error "skip task"
                        set todayStart to (current date)
                        set time of todayStart to 0
                        set todayEnd to todayStart + (24 * hours)
                        if taskDue < todayStart or taskDue ≥ todayEnd then error "skip task"
                        """
            elif due_relative == "tomorrow":
                due_relative_check_batch = """
                        set taskDue to contents of (item i of dueDates)
                        if taskDue is missing value then error "skip task"
                        set tomorrowStart to (current date) + (1 * days)
                        set time of tomorrowStart to 0
                        set tomorrowEnd to tomorrowStart + (24 * hours)
                        if taskDue < tomorrowStart or taskDue ≥ tomorrowEnd then error "skip task"
                        """
            elif due_relative == "this_week":
                due_relative_check_batch = """
                        set taskDue to contents of (item i of dueDates)
                        if taskDue is missing value then error "skip task"
                        set weekEnd to (current date) + (7 * days)
                        if taskDue > weekEnd then error "skip task"
                        """
            elif due_relative == "next_week":
                due_relative_check_batch = """
                        set taskDue to contents of (item i of dueDates)
                        if taskDue is missing value then error "skip task"
                        set nextWeekStart to (current date) + (7 * days)
                        set nextWeekEnd to nextWeekStart + (7 * days)
                        if taskDue < nextWeekStart or taskDue > nextWeekEnd then error "skip task"
                        """
            elif due_relative == "overdue":
                due_relative_check_batch = """
                        set taskDue to contents of (item i of dueDates)
                        if taskDue is missing value then error "skip task"
                        if taskDue >= (current date) then error "skip task"
                        """
        checks['due_relative_check_batch'] = due_relative_check_batch

        defer_relative_check_batch = ""
        if defer_relative:
            if defer_relative == "today":
                defer_relative_check_batch = """
                        set taskDefer to contents of (item i of deferDates)
                        if taskDefer is missing value then error "skip task"
                        set todayStart to (current date)
                        set time of todayStart to 0
                        set todayEnd to todayStart + (24 * hours)
                        if taskDefer < todayStart or taskDefer ≥ todayEnd then error "skip task"
                        """
            elif defer_relative == "tomorrow":
                defer_relative_check_batch = """
                        set taskDefer to contents of (item i of deferDates)
                        if taskDefer is missing value then error "skip task"
                        set tomorrowStart to (current date) + (1 * days)
                        set time of tomorrowStart to 0
                        set tomorrowEnd to tomorrowStart + (24 * hours)
                        if taskDefer < tomorrowStart or taskDefer ≥ tomorrowEnd then error "skip task"
                        """
            elif defer_relative == "this_week":
                defer_relative_check_batch = """
                        set taskDefer to contents of (item i of deferDates)
                        if taskDefer is missing value then error "skip task"
                        set weekEnd to (current date) + (7 * days)
                        if taskDefer > weekEnd then error "skip task"
                        """
            elif defer_relative == "next_week":
                defer_relative_check_batch = """
                        set taskDefer to contents of (item i of deferDates)
                        if taskDefer is missing value then error "skip task"
                        set nextWeekStart to (current date) + (7 * days)
                        set nextWeekEnd to nextWeekStart + (7 * days)
                        if taskDefer < nextWeekStart or taskDefer > nextWeekEnd then error "skip task"
                        """
        checks['defer_relative_check_batch'] = defer_relative_check_batch

        estimate_check_batch = ""
        if max_estimated_minutes is not None:
            estimate_check_batch = f"""
                        set emVal to contents of (item i of estMins)
                        if emVal is missing value or emVal = 0 or emVal > {max_estimated_minutes} then error "skip task"
                        """
        elif has_estimate is not None:
            if has_estimate:
                estimate_check_batch = """
                        set emVal to contents of (item i of estMins)
                        if emVal is missing value or emVal = 0 then error "skip task"
                        """
            else:
                estimate_check_batch = """
                        set emVal to contents of (item i of estMins)
                        if emVal is not missing value and emVal > 0 then error "skip task"
                        """
        checks['estimate_check_batch'] = estimate_check_batch

        tag_check_batch = ""
        if tag_filter and len(tag_filter) > 0 and tag_filter_mode == "and" and tag_prefiltered_ids is None:
            tag_checks_batch = []
            for tag_name in tag_filter:
                tag_escaped = self._escape_applescript_string(tag_name)
                tag_checks_batch.append(f'''
                        set hasTag to false
                        set taskTagNames to contents of (item i of tagNameLists)
                        repeat with tn in taskTagNames
                            if tn is "{tag_escaped}" then
                                set hasTag to true
                                exit repeat
                            end if
                        end repeat
                        if not hasTag then error "skip task without required tag"
                        ''')
            tag_check_batch = "".join(tag_checks_batch)
        checks['tag_check_batch'] = tag_check_batch

        return checks

    def _build_batch_mode_script(
        self,
        task_source: str,
        on_hold_tags_decl: str,
        filter_checks: dict[str, str],
    ) -> str:
        """Build the BATCH mode AppleScript for get_tasks.

        Uses 'a reference to' for O(P) batch property reads.
        Returns the complete AppleScript string.
        """
        completion_check_batch = filter_checks['completion_check_batch']
        flagged_check_batch = filter_checks['flagged_check_batch']
        dropped_check_batch = filter_checks['dropped_check_batch']
        blocked_check_batch = filter_checks['blocked_check_batch']
        next_check_batch = filter_checks['next_check_batch']
        overdue_check_batch = filter_checks['overdue_check_batch']
        query_check_batch = filter_checks['query_check_batch']
        available_check_batch = filter_checks['available_check_batch']
        due_relative_check_batch = filter_checks['due_relative_check_batch']
        defer_relative_check_batch = filter_checks['defer_relative_check_batch']
        estimate_check_batch = filter_checks['estimate_check_batch']
        tag_check_batch = filter_checks['tag_check_batch']

        return f'''
        use AppleScript version "2.4"
        use scripting additions

        set output to ""

        tell application "OmniFocus"
            tell front document
                set ft to a reference to {task_source}

                -- Batch read all properties (one Apple Event each)
                set ids to id of ft
                set taskNames to name of ft
                set taskNotes to note of ft
                set taskFlags to flagged of ft
                set taskComps to completed of ft
                set taskDrops to dropped of ft
                set taskBlocks to blocked of ft
                set taskNexts to next of ft
                set taskSeqs to sequential of ft
                set taskCompByChildren to completed by children of ft
                set dueDates to effective due date of ft
                set deferDates to effective defer date of ft
                set plannedDates to effective planned date of ft
                set creationDates to creation date of ft
                set modDates to modification date of ft
                set compDates to completion date of ft
                set dropDates to dropped date of ft
                set estMins to estimated minutes of ft
                set repRules to repetition rule of ft
                set nextDueDates to next due date of ft
                set nextDeferDates to next defer date of ft
                set nextPlannedDates to next planned date of ft
                set availCounts to number of available tasks of ft
                set subtaskCounts to number of tasks of ft
                set effComps to effectively completed of ft
                set effDrops to effectively dropped of ft
                set taskInInbox to in inbox of ft

                -- Nested batch reads (project, parent, tags)
                set projIds to id of (containing project of ft)
                set projNames to name of (containing project of ft)
                set parentIds to id of (parent task of ft)
                set tagNameLists to name of (tags of ft)

                set taskCount to count of ids
                {on_hold_tags_decl}

                -- Build JSON from parallel lists (local loop, minimal IPC)
                repeat with i from 1 to taskCount
                    try
                        -- Apply all filters using batch-read data
                        {completion_check_batch}
                        {flagged_check_batch}
                        {dropped_check_batch}
                        {blocked_check_batch}
                        {next_check_batch}
                        {overdue_check_batch}
                        {query_check_batch}
                        {available_check_batch}
                        {due_relative_check_batch}
                        {defer_relative_check_batch}
                        {estimate_check_batch}
                        {tag_check_batch}

                        -- Date coercion (local, no IPC)
                        set dueDateStr to ""
                        set dVal to contents of (item i of dueDates)
                        if dVal is not missing value then
                            set dueDateStr to (dVal as «class isot» as string)
                        end if

                        set deferDateStr to ""
                        set dVal to contents of (item i of deferDates)
                        if dVal is not missing value then
                            set deferDateStr to (dVal as «class isot» as string)
                        end if

                        set plannedDateStr to ""
                        set pVal to contents of (item i of plannedDates)
                        if pVal is not missing value then
                            set plannedDateStr to (pVal as «class isot» as string)
                        end if

                        set nextDueDateStr to ""
                        set dVal to contents of (item i of nextDueDates)
                        if dVal is not missing value then
                            set nextDueDateStr to (dVal as «class isot» as string)
                        end if

                        set nextDeferDateStr to ""
                        set dVal to contents of (item i of nextDeferDates)
                        if dVal is not missing value then
                            set nextDeferDateStr to (dVal as «class isot» as string)
                        end if

                        set nextPlannedDateStr to ""
                        set dVal to contents of (item i of nextPlannedDates)
                        if dVal is not missing value then
                            set nextPlannedDateStr to (dVal as «class isot» as string)
                        end if

                        set creationDateStr to "null"
                        set dVal to contents of (item i of creationDates)
                        if dVal is not missing value then
                            set creationDateStr to "\\"" & (dVal as «class isot» as string) & "\\""
                        end if

                        set modificationDateStr to "null"
                        set dVal to contents of (item i of modDates)
                        if dVal is not missing value then
                            set modificationDateStr to "\\"" & (dVal as «class isot» as string) & "\\""
                        end if

                        set completionDateStr to "null"
                        set dVal to contents of (item i of compDates)
                        if dVal is not missing value then
                            set completionDateStr to "\\"" & (dVal as «class isot» as string) & "\\""
                        end if

                        set droppedDateStr to "null"
                        set dVal to contents of (item i of dropDates)
                        if dVal is not missing value then
                            set droppedDateStr to "\\"" & (dVal as «class isot» as string) & "\\""
                        end if

                        -- Project info (batch-read)
                        set projectId to ""
                        set projIdVal to contents of (item i of projIds)
                        if projIdVal is not missing value then set projectId to projIdVal

                        set projectName to ""
                        set projNameVal to contents of (item i of projNames)
                        if projNameVal is not missing value then set projectName to projNameVal

                        -- Estimated minutes
                        set estimatedMins to "null"
                        set emVal to contents of (item i of estMins)
                        if emVal is not missing value and emVal is not 0 then
                            set estimatedMins to emVal as text
                        end if

                        -- Tags (batch-read as list of name-lists)
                        set tagsJSON to "[]"
                        set taskTagNames to contents of (item i of tagNameLists)
                        if (count of taskTagNames) > 0 then
                            set tagItems to {{}}
                            repeat with tn in taskTagNames
                                set end of tagItems to "\\"" & my escapeJSON(tn) & "\\""
                            end repeat
                            set AppleScript's text item delimiters to ", "
                            set tagsJSON to "[" & (tagItems as text) & "]"
                            set AppleScript's text item delimiters to ""
                        end if

                        -- Parent task (batch-read, exclude project-level parents)
                        set parentTaskId to ""
                        set parentIdVal to contents of (item i of parentIds)
                        if parentIdVal is not missing value then
                            if parentIdVal is not equal to projectId then
                                set parentTaskId to parentIdVal
                            end if
                        end if

                        -- Repetition info (per-task IPC — most tasks have no rules)
                        set isRecurring to "false"
                        set recurrenceStr to ""
                        set repetitionMethodStr to ""
                        set catchUpAutoStr to "null"
                        set repRuleVal to contents of (item i of repRules)
                        if repRuleVal is not missing value then
                            set isRecurring to "true"
                            try
                                set recurrenceStr to recurrence of repRuleVal
                            end try
                            try
                                set repetitionMethodStr to (repetition method of repRuleVal) as text
                            end try
                            try
                                set catchUpAutoStr to (catch up automatically of repRuleVal) as text
                            end try
                        end if

                        -- Subtask count (batch-read)
                        set taskSubtaskCount to item i of subtaskCounts

                        -- Availability (computed from batch-read data)
                        set numAvailableTasks to item i of availCounts
                        set isDeferred to false
                        set deferVal to contents of (item i of deferDates)
                        if deferVal is not missing value then
                            set isDeferred to (deferVal > (current date))
                        end if
                        set taskCompleted to item i of taskComps
                        set taskDropped to item i of taskDrops
                        set taskBlocked to item i of taskBlocks
                        set directlyAvailable to (not taskCompleted) and (not taskDropped) and (not taskBlocked) and (not isDeferred)
                        set effComp to item i of effComps
                        set effDrop to item i of effDrops
                        set containerActive to (not effComp) and (not effDrop)
                        set taskAvailable to (directlyAvailable or (numAvailableTasks > 0)) and containerActive

                        -- Build JSON
                        set jsonLine to "{{" & ¬
                            "\\"id\\": \\"" & item i of ids & "\\", " & ¬
                            "\\"name\\": \\"" & my escapeJSON(item i of taskNames) & "\\", " & ¬
                            "\\"note\\": \\"" & my escapeJSON(item i of taskNotes) & "\\", " & ¬
                            "\\"completed\\": " & (taskCompleted as text) & ", " & ¬
                            "\\"flagged\\": " & (item i of taskFlags as text) & ", " & ¬
                            "\\"dropped\\": " & (taskDropped as text) & ", " & ¬
                            "\\"blocked\\": " & (taskBlocked as text) & ", " & ¬
                            "\\"next\\": " & (item i of taskNexts as text) & ", " & ¬
                            "\\"projectId\\": \\"" & projectId & "\\", " & ¬
                            "\\"projectName\\": \\"" & my escapeJSON(projectName) & "\\", " & ¬
                            "\\"dueDate\\": \\"" & dueDateStr & "\\", " & ¬
                            "\\"deferDate\\": \\"" & deferDateStr & "\\", " & ¬
                            "\\"plannedDate\\": \\"" & plannedDateStr & "\\", " & ¬
                            "\\"nextDueDate\\": \\"" & nextDueDateStr & "\\", " & ¬
                            "\\"nextDeferDate\\": \\"" & nextDeferDateStr & "\\", " & ¬
                            "\\"nextPlannedDate\\": \\"" & nextPlannedDateStr & "\\", " & ¬
                            "\\"creationDate\\": " & creationDateStr & ", " & ¬
                            "\\"modificationDate\\": " & modificationDateStr & ", " & ¬
                            "\\"completionDate\\": " & completionDateStr & ", " & ¬
                            "\\"droppedDate\\": " & droppedDateStr & ", " & ¬
                            "\\"tags\\": " & tagsJSON & ", " & ¬
                            "\\"estimatedMinutes\\": " & estimatedMins & ", " & ¬
                            "\\"isRecurring\\": " & isRecurring & ", " & ¬
                            "\\"recurrence\\": \\"" & my escapeJSON(recurrenceStr) & "\\", " & ¬
                            "\\"repetitionMethod\\": \\"" & my escapeJSON(repetitionMethodStr) & "\\", " & ¬
                            "\\"catchUpAutomatically\\": " & catchUpAutoStr & ", " & ¬
                            "\\"parentTaskId\\": \\"" & parentTaskId & "\\", " & ¬
                            "\\"subtaskCount\\": " & (taskSubtaskCount as text) & ", " & ¬
                            "\\"sequential\\": " & (item i of taskSeqs as text) & ", " & ¬
                            "\\"completedByChildren\\": " & ((item i of taskCompByChildren) as text) & ", " & ¬
                            "\\"position\\": " & (i as text) & ", " & ¬
                            "\\"numberOfAvailableTasks\\": " & (numAvailableTasks as text) & ", " & ¬
                            "\\"inInbox\\": " & (item i of taskInInbox as text) & ", " & ¬
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



    def get_tasks(
        self,
        task_id: Optional[str] = None,  # NEW (Phase 3.1): Filter to specific task
        parent_task_id: Optional[str] = None,  # NEW (Phase 3.1): Filter by parent
        include_full_notes: bool = False,  # NEW (Phase 3.1): Return full notes
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

        Orchestrator that delegates to helper methods:
        - _validate_get_tasks_params() — parameter validation
        - _build_task_source() — AppleScript task source + whose clauses
        - _build_task_filter_checks() — batch filter strings
        - _build_batch_mode_script() — AppleScript generation
        - _post_process_tasks() — normalization, Python-side filtering, sorting

        Args:
            task_id: NEW (Phase 3.1): Filter to specific task by ID (consolidates get_task())
            parent_task_id: NEW (Phase 3.1): Filter to subtasks of specific parent (consolidates get_subtasks())
            include_full_notes: NEW (Phase 3.1): Return full note content instead of truncated (consolidates get_note())
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
        self._validate_get_tasks_params(
            created_after=created_after, created_before=created_before,
            modified_after=modified_after, modified_before=modified_before,
            tag_filter_mode=tag_filter_mode, sort_by=sort_by,
            sort_order=sort_order, due_relative=due_relative,
            defer_relative=defer_relative,
        )

        # Tag-side pre-filter: query task IDs from tag objects instead of
        # scanning all tasks. This reverses the lookup direction for massive
        # speedup (from 120s+ to ~1-2s). Only for AND/OR modes — NOT mode
        # is inherently a full scan and uses the fallback path.
        tag_prefiltered_ids = None
        if (tag_filter and len(tag_filter) > 0
                and tag_filter_mode != "not"
                and not task_id and not parent_task_id and not inbox_only):
            tag_prefiltered_ids = self._get_task_ids_for_tags(
                tag_filter, tag_filter_mode, include_completed
            )
            if tag_prefiltered_ids is not None and len(tag_prefiltered_ids) == 0:
                return []  # No tasks match — early return

        # Pre-fetch On Hold tag names for available_only filtering.
        # OmniFocus's Available perspective excludes tasks with On Hold tags.
        on_hold_tag_names: list[str] = []
        on_hold_tags_decl = ""
        on_hold_available_check_batch = ""
        if available_only:
            on_hold_tag_names = self._get_on_hold_tag_names()
            if on_hold_tag_names:
                escaped = [f'"{self._escape_applescript_string(n)}"' for n in on_hold_tag_names]
                on_hold_tags_decl = f"set onHoldTags to {{{', '.join(escaped)}}}"
                on_hold_available_check_batch = """
                        -- Skip tasks with On Hold tags (batch data)
                        set taskTagNms to contents of (item i of tagNameLists)
                        repeat with tn in taskTagNms
                            if tn is in onHoldTags then error "skip unavailable"
                        end repeat"""

        # Build task source with native 'whose' pre-filtering where possible.
        # OmniFocus evaluates 'whose' clauses natively (~20-30x faster than
        # manual iteration with per-task property checks). See PERFORMANCE_PROFILING.md.
        task_source, whose_active = self._build_task_source(
            task_id=task_id,
            parent_task_id=parent_task_id,
            inbox_only=inbox_only,
            project_id=project_id,
            include_completed=include_completed,
            flagged_only=flagged_only,
            next_only=next_only,
            dropped_only=dropped_only,
            blocked_only=blocked_only,
            overdue=overdue,
            query=query,
            tag_prefiltered_ids=tag_prefiltered_ids,
        )

        # Generate batch filter check strings
        filter_checks = self._build_task_filter_checks(
            include_completed=include_completed,
            flagged_only=flagged_only,
            available_only=available_only,
            overdue=overdue,
            dropped_only=dropped_only,
            blocked_only=blocked_only,
            next_only=next_only,
            due_relative=due_relative,
            defer_relative=defer_relative,
            max_estimated_minutes=max_estimated_minutes,
            has_estimate=has_estimate,
            tag_filter=tag_filter,
            tag_filter_mode=tag_filter_mode,
            tag_prefiltered_ids=tag_prefiltered_ids,
            query=query,
            whose_active=whose_active,
            on_hold_available_check_batch=on_hold_available_check_batch,
        )

        # Always use batch mode — 'a reference to' works with all source types
        script = self._build_batch_mode_script(
            task_source, on_hold_tags_decl, filter_checks
        )

        try:
            result = run_applescript(script, timeout=timeout)
            if result:
                tasks = json.loads(result)

                return self._post_process_tasks(
                    tasks,
                    tag_filter=tag_filter,
                    tag_filter_mode=tag_filter_mode,
                    tag_prefiltered_ids=tag_prefiltered_ids,
                    created_after=created_after,
                    created_before=created_before,
                    modified_after=modified_after,
                    modified_before=modified_before,
                    recurring_only=recurring_only,
                    query=query,
                    sort_by=sort_by,
                    sort_order=sort_order,
                )
            else:
                raise Exception("No output from OmniFocus AppleScript")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error querying OmniFocus tasks: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing OmniFocus task output: {e}")


    def _validate_update_task_params(
        self,
        *,
        task_id: str,
        task_name: Optional[str],
        name: Optional[str],
        project_id: Optional[str],
        parent_task_id: Optional[str],
        tags: Optional[list[str]],
        add_tags: Optional[list[str]],
        remove_tags: Optional[list[str]],
        status: Optional[Union[TaskStatus, str]],
        repetition_method: Optional[str],
        note: Optional[str],
        due_date: Optional[str],
        defer_date: Optional[str],
        planned_date: Optional[str],
        flagged: Optional[bool],
        sequential: Optional[bool],
        completed_by_children: Optional[bool],
        estimated_minutes: Optional[int],
        completed: Optional[bool],
        recurrence: Optional[str],
    ) -> tuple[Optional[str], Optional[TaskStatus]]:
        """Validate update_task parameters, raising ValueError for invalid values.

        Returns (resolved_task_name, resolved_status) after legacy name support
        and status enum normalization.
        """
        if not task_id:
            raise ValueError("task_id is required")

        # Support legacy 'name' parameter
        if name is not None and task_name is None:
            task_name = name

        if project_id is not None and parent_task_id is not None:
            raise ValueError("Cannot specify both parent_task_id and project_id - parent task already determines the project.")

        if tags is not None and add_tags is not None:
            raise ValueError("Cannot specify both tags and add_tags/remove_tags - use tags for full replacement or add_tags/remove_tags for incremental changes.")
        if tags is not None and remove_tags is not None:
            raise ValueError("Cannot specify both tags and remove_tags - use tags for full replacement or add_tags/remove_tags for incremental changes.")

        if status is not None:
            if isinstance(status, str):
                try:
                    status = TaskStatus(status)
                except ValueError:
                    raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join([s.value for s in TaskStatus])}")

        if repetition_method:
            valid_methods = ["fixed", "start_after_completion", "due_after_completion"]
            if repetition_method not in valid_methods:
                raise ValueError(f"Invalid repetition_method: {repetition_method}. Must be one of: {', '.join(valid_methods)}")

        all_params = [
            task_name, project_id, parent_task_id, note, due_date, defer_date,
            planned_date, flagged, sequential, completed_by_children, tags,
            add_tags, remove_tags, estimated_minutes, completed, status,
            recurrence, repetition_method
        ]
        if all(v is None for v in all_params):
            raise ValueError("At least one field must be provided to update")

        return task_name, status

    def _build_update_task_commands(
        self,
        *,
        task_name: Optional[str],
        note: Optional[str],
        flagged: Optional[bool],
        sequential: Optional[bool],
        due_date: Optional[str],
        defer_date: Optional[str],
        planned_date: Optional[str],
        estimated_minutes: Optional[int],
        completed: Optional[bool],
        status: Optional[TaskStatus],
        project_id: Optional[str],
        parent_task_id: Optional[str],
        tags: Optional[list[str]],
        add_tags: Optional[list[str]],
        remove_tags: Optional[list[str]],
        recurrence: Optional[str],
        repetition_method: Optional[str],
        completed_by_children: Optional[bool],
    ) -> tuple[list[str], list[str], list[str], bool]:
        """Build AppleScript property and command strings for update_task.

        Returns (properties, separate_commands, updated_fields, recurrence_js_needed).
        """
        properties: list[str] = []
        separate_commands: list[str] = []
        updated_fields: list[str] = []

        # Simple properties (set via 'set properties of theTask')
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

        if sequential is not None:
            properties.append(f'sequential:{str(sequential).lower()}')
            updated_fields.append("sequential")

        if completed_by_children is not None:
            properties.append(f'completed by children:{str(completed_by_children).lower()}')
            updated_fields.append("completed_by_children")

        # Dates (clear vs set)
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

        if planned_date is not None:
            if planned_date == "":
                separate_commands.append("set planned date of theTask to missing value")
            else:
                as_date = self._iso_to_applescript_date(planned_date)
                separate_commands.append(f'set planned date of theTask to date "{as_date}"')
            updated_fields.append("planned_date")

        # Estimated minutes
        if estimated_minutes is not None:
            separate_commands.append(f'set estimated minutes of theTask to {estimated_minutes}')
            updated_fields.append("estimated_minutes")

        # Completion (use "mark complete" for recurring task safety)
        if completed is not None:
            if completed:
                separate_commands.append("mark complete theTask")
            else:
                separate_commands.append("set completed of theTask to false")
            updated_fields.append("completed")

        # Status (use "mark dropped" command)
        if status is not None:
            if status == TaskStatus.DROPPED:
                separate_commands.append("mark dropped theTask")
            elif status == TaskStatus.ACTIVE:
                raise ValueError(
                    "Cannot undrop a task via automation. "
                    "OmniFocus does not support restoring dropped tasks "
                    "through AppleScript or OmniAutomation. "
                    "Use the OmniFocus UI to restore dropped tasks."
                )
            updated_fields.append("status")

        # Hierarchy changes
        if project_id is not None:
            project_id_escaped = self._escape_applescript_string(project_id)
            separate_commands.append(f'''
                    set theProject to first flattened project whose id is "{project_id_escaped}"
                    move theTask to end of tasks of theProject''')
            updated_fields.append("project_id")

        if parent_task_id is not None:
            parent_id_escaped = self._escape_applescript_string(parent_task_id)
            separate_commands.append(f'''
                    set theParent to first flattened task whose id is "{parent_id_escaped}"
                    if id of theTask is id of theParent then
                        error "Cannot set task as its own parent"
                    end if
                    move theTask to end of tasks of theParent''')
            updated_fields.append("parent_task_id")

        # Tags
        if tags is not None:
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
                separate_commands.append("set tags of theTask to {}")
            updated_fields.append("tags")

        if add_tags is not None:
            for tag in add_tags:
                tag_escaped = self._escape_applescript_string(tag)
                separate_commands.append(f'''
                    set tagObj to first flattened tag whose name is "{tag_escaped}"
                    add tagObj to tags of theTask''')
            updated_fields.append("add_tags")

        if remove_tags is not None:
            for tag in remove_tags:
                tag_escaped = self._escape_applescript_string(tag)
                separate_commands.append(f'''
                    set tagObj to first flattened tag whose name is "{tag_escaped}"
                    remove tagObj from tags of theTask''')
            updated_fields.append("remove_tags")

        # Recurrence
        _recurrence_js_needed = False
        if recurrence is not None:
            if recurrence == "":
                separate_commands.append("set repetition rule of theTask to missing value")
            else:
                _recurrence_js_needed = True
            updated_fields.append("recurrence")
        elif repetition_method is not None:
            _recurrence_js_needed = True
            updated_fields.append("repetition_method")

        return properties, separate_commands, updated_fields, _recurrence_js_needed

    def _execute_recurrence_update(
        self,
        task_id: str,
        recurrence: Optional[str],
        repetition_method: Optional[str],
    ) -> None:
        """Execute OmniAutomation recurrence update (post-AppleScript).

        Skipped in test mode — OmniAutomation crashes on headless test databases (#324).
        """
        if self._test_mode:
            return

        js_method_map = {
            "fixed": "Task.RepetitionMethod.Fixed",
            "due_after_completion": "Task.RepetitionMethod.DueDate",
            "start_after_completion": "Task.RepetitionMethod.DeferUntilDate",
        }
        js_method = js_method_map.get(
            repetition_method or "fixed",
            "Task.RepetitionMethod.Fixed"
        )
        task_id_js = self._escape_js_string(task_id)

        if recurrence is not None:
            recurrence_js = self._escape_js_string(recurrence)
            js_code = (
                f"var t = Task.byIdentifier('{task_id_js}');"
                f" if (t) {{ t.repetitionRule = new Task.RepetitionRule("
                f"'{recurrence_js}', {js_method}); 'ok'; }}"
                f" else {{ 'not found'; }}"
            )
        else:
            js_code = (
                f"var t = Task.byIdentifier('{task_id_js}');"
                f" if (t && t.repetitionRule) {{"
                f" var rr = t.repetitionRule.ruleString;"
                f" t.repetitionRule = new Task.RepetitionRule("
                f"rr, {js_method}); 'ok'; }}"
                f" else {{ 'no rule'; }}"
            )

        js_script = (
            'tell application "OmniFocus"\n'
            f'    evaluate javascript "{js_code}"\n'
            'end tell'
        )
        run_applescript(js_script)

    def update_task(
        self,
        task_id: str,
        task_name: Optional[str] = None,
        project_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        note: Optional[str] = None,
        due_date: Optional[str] = None,
        defer_date: Optional[str] = None,
        planned_date: Optional[str] = None,
        flagged: Optional[bool] = None,
        sequential: Optional[bool] = None,
        completed_by_children: Optional[bool] = None,
        tags: Optional[list[str]] = None,
        add_tags: Optional[list[str]] = None,
        remove_tags: Optional[list[str]] = None,
        estimated_minutes: Optional[int] = None,
        completed: Optional[bool] = None,
        status: Optional[Union[TaskStatus, str]] = None,
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
            recurrence: iCalendar RRULE string (e.g., "FREQ=WEEKLY;BYDAY=MO,WE,FR"),
                or "" to remove recurrence (optional). Uses OmniAutomation internally.
            repetition_method: "fixed", "start_after_completion", or
                "due_after_completion" (optional)
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
        # SAFETY: Verify database before modifying
        self._verify_database_safety('update_task')

        # Validate parameters
        task_name, status = self._validate_update_task_params(
            task_id=task_id, task_name=task_name, name=name,
            project_id=project_id, parent_task_id=parent_task_id,
            tags=tags, add_tags=add_tags, remove_tags=remove_tags,
            status=status, repetition_method=repetition_method,
            note=note, due_date=due_date, defer_date=defer_date,
            planned_date=planned_date, flagged=flagged, sequential=sequential,
            completed_by_children=completed_by_children,
            estimated_minutes=estimated_minutes, completed=completed,
            recurrence=recurrence,
        )

        # Build AppleScript properties and commands
        properties, separate_commands, updated_fields, _recurrence_js_needed = \
            self._build_update_task_commands(
                task_name=task_name, note=note, flagged=flagged,
                sequential=sequential, due_date=due_date, defer_date=defer_date,
                planned_date=planned_date, estimated_minutes=estimated_minutes,
                completed=completed, status=status, project_id=project_id,
                parent_task_id=parent_task_id, tags=tags, add_tags=add_tags,
                remove_tags=remove_tags, recurrence=recurrence,
                repetition_method=repetition_method,
                completed_by_children=completed_by_children,
            )

        # Build and execute AppleScript
        try:
            task_id_escaped = self._escape_applescript_string(task_id)
            script = f'''
            tell application "OmniFocus"
                tell front document
                    set theTask to first flattened task whose id is "{task_id_escaped}"
                    '''

            if properties:
                props_str = ", ".join(properties)
                script += f'\n                    set properties of theTask to {{{props_str}}}'

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
                if _recurrence_js_needed:
                    self._execute_recurrence_update(
                        task_id, recurrence, repetition_method
                    )
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
            error_msg = f"AppleScript error: {e.stderr}"
            # Type coercion error on tag operations typically means the task
            # is dropped or in a state that prevents modification
            if "(-1700)" in (e.stderr or "") and "type tag" in (e.stderr or ""):
                error_msg = (
                    f"Cannot modify tags on task '{task_id}': the task may be "
                    f"dropped or completed. Change the task's status to active "
                    f"first, or create a new task. "
                    f"(Original error: {e.stderr})"
                )
            return {
                "success": False,
                "task_id": task_id,
                "updated_fields": [],
                "error": error_msg
            }
        except Exception as e:
            return {
                "success": False,
                "task_id": task_id,
                "updated_fields": [],
                "error": str(e)
            }

    def _validate_update_tasks_params(
        self,
        *,
        task_ids: Union[str, list[str]],
        flagged: Optional[bool],
        sequential: Optional[bool],
        status: Optional[Union[TaskStatus, str]],
        completed: Optional[bool],
        project_id: Optional[str],
        parent_task_id: Optional[str],
        tags: Optional[list[str]],
        add_tags: Optional[list[str]],
        remove_tags: Optional[list[str]],
        due_date: Optional[str],
        defer_date: Optional[str],
        planned_date: Optional[str],
        estimated_minutes: Optional[int],
        kwargs: dict,
    ) -> list[str]:
        """Validate update_tasks parameters. Returns normalized ids_list."""
        if 'task_name' in kwargs or 'name' in kwargs:
            raise ValueError("task_name is not allowed in batch updates (requires unique values per task)")
        if 'note' in kwargs:
            raise ValueError("note is not allowed in batch updates (requires unique values per task)")
        if kwargs:
            unexpected = ', '.join(kwargs.keys())
            raise ValueError(f"Unexpected arguments: {unexpected}")

        ids_list = [task_ids] if isinstance(task_ids, str) else task_ids
        if not ids_list:
            raise ValueError("task_ids cannot be empty")

        provided_fields = [
            flagged, sequential, status, completed, project_id, parent_task_id,
            tags, add_tags, remove_tags, due_date, defer_date, planned_date,
            estimated_minutes
        ]
        if all(f is None for f in provided_fields):
            raise ValueError("Must provide at least one field to update")

        if project_id is not None and parent_task_id is not None:
            raise ValueError("Cannot specify both project_id and parent_task_id")
        if tags is not None and add_tags is not None:
            raise ValueError("Cannot specify both tags and add_tags (use one or the other)")

        # Validate status string
        if status is not None and isinstance(status, str):
            try:
                TaskStatus(status)
            except ValueError:
                raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join([s.value for s in TaskStatus])}")

        return ids_list

    def _build_bulk_update_commands(
        self,
        *,
        or_chain_target: str,
        flagged: Optional[bool],
        sequential: Optional[bool],
        due_date: Optional[str],
        defer_date: Optional[str],
        planned_date: Optional[str],
        estimated_minutes: Optional[int],
        completed: Optional[bool],
    ) -> tuple[list[str], bool]:
        """Build bulk-settable OR-chain commands for update_tasks.

        Returns (bulk_commands, has_bulk).
        """
        bulk_commands: list[str] = []

        if flagged is not None:
            bulk_commands.append(
                f"set flagged of ({or_chain_target}) to {str(flagged).lower()}"
            )
        if sequential is not None:
            bulk_commands.append(
                f"set sequential of ({or_chain_target}) to {str(sequential).lower()}"
            )
        if estimated_minutes is not None:
            bulk_commands.append(
                f"set estimated minutes of ({or_chain_target}) to {estimated_minutes}"
            )

        for field_name, field_val in [("due date", due_date), ("defer date", defer_date), ("planned date", planned_date)]:
            if field_val is not None:
                if field_val == "":
                    bulk_commands.append(
                        f"set {field_name} of ({or_chain_target}) to missing value"
                    )
                else:
                    as_date = self._iso_to_applescript_date(field_val)
                    bulk_commands.append(
                        f'set {field_name} of ({or_chain_target}) to date "{as_date}"'
                    )

        if completed is True:
            bulk_commands.append(f"mark complete ({or_chain_target})")

        return bulk_commands, len(bulk_commands) > 0

    def _build_per_task_update_commands(
        self,
        *,
        completed: Optional[bool],
        status: Optional[Union[TaskStatus, str]],
        project_id: Optional[str],
        parent_task_id: Optional[str],
        tags: Optional[list[str]],
        add_tags: Optional[list[str]],
        remove_tags: Optional[list[str]],
    ) -> tuple[list[str], bool]:
        """Build per-task repeat-loop commands for update_tasks.

        Returns (per_task_commands, has_per_task).
        """
        per_task_commands: list[str] = []

        if completed is False:
            per_task_commands.append("set completed of theTask to false")

        if status is not None:
            if isinstance(status, str):
                status = TaskStatus(status)
            if status == TaskStatus.DROPPED:
                per_task_commands.append("mark dropped theTask")
            elif status == TaskStatus.ACTIVE:
                raise ValueError(
                    "Cannot undrop a task via automation. "
                    "OmniFocus does not support restoring dropped tasks "
                    "through AppleScript or OmniAutomation. "
                    "Use the OmniFocus UI to restore dropped tasks."
                )

        if project_id is not None:
            project_id_escaped = self._escape_applescript_string(project_id)
            per_task_commands.append(f'''
                    set theProject to first flattened project whose id is "{project_id_escaped}"
                    move theTask to end of tasks of theProject''')

        if parent_task_id is not None:
            parent_id_escaped = self._escape_applescript_string(parent_task_id)
            per_task_commands.append(f'''
                    set theParent to first flattened task whose id is "{parent_id_escaped}"
                    if id of theTask is id of theParent then
                        error "Cannot set task as its own parent"
                    end if
                    move theTask to end of tasks of theParent''')

        if tags is not None:
            if len(tags) > 0:
                tag_adds = []
                for tag in tags:
                    tag_escaped = self._escape_applescript_string(tag)
                    tag_adds.append(f'''
                        set tagObj to first flattened tag whose name is "{tag_escaped}"
                        copy tagObj to end of newTags''')
                tag_adds_str = "\n                    ".join(tag_adds)
                per_task_commands.append(f'''
                    set newTags to {{}}
                    {tag_adds_str}
                    set tags of theTask to newTags''')
            else:
                per_task_commands.append("set tags of theTask to {}")

        if add_tags is not None:
            for tag in add_tags:
                tag_escaped = self._escape_applescript_string(tag)
                per_task_commands.append(f'''
                    set tagObj to first flattened tag whose name is "{tag_escaped}"
                    add tagObj to tags of theTask''')

        if remove_tags is not None:
            for tag in remove_tags:
                tag_escaped = self._escape_applescript_string(tag)
                per_task_commands.append(f'''
                    set tagObj to first flattened tag whose name is "{tag_escaped}"
                    remove tagObj from tags of theTask''')

        return per_task_commands, len(per_task_commands) > 0

    def update_tasks(
        self,
        task_ids: Union[str, list[str]],
        flagged: Optional[bool] = None,
        sequential: Optional[bool] = None,
        status: Optional[Union[TaskStatus, str]] = None,
        completed: Optional[bool] = None,
        project_id: Optional[str] = None,
        parent_task_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        add_tags: Optional[list[str]] = None,
        remove_tags: Optional[list[str]] = None,
        due_date: Optional[str] = None,
        defer_date: Optional[str] = None,
        planned_date: Optional[str] = None,
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

        Note:
            ``updated_ids`` is approximate on partial failure — it lists
            the first N IDs from the input, not necessarily the ones that
            succeeded.

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

        # Validate and normalize parameters
        ids_list = self._validate_update_tasks_params(
            task_ids=task_ids, flagged=flagged, sequential=sequential,
            status=status, completed=completed, project_id=project_id,
            parent_task_id=parent_task_id, tags=tags, add_tags=add_tags,
            remove_tags=remove_tags, due_date=due_date, defer_date=defer_date,
            planned_date=planned_date, estimated_minutes=estimated_minutes,
            kwargs=kwargs,
        )

        or_chain_target = self._build_whose_or_chain(ids_list, "flattened task")

        # Build bulk-settable and per-task commands
        bulk_commands, has_bulk = self._build_bulk_update_commands(
            or_chain_target=or_chain_target, flagged=flagged,
            sequential=sequential, due_date=due_date, defer_date=defer_date,
            planned_date=planned_date, estimated_minutes=estimated_minutes,
            completed=completed,
        )

        per_task_commands, has_per_task = self._build_per_task_update_commands(
            completed=completed, status=status, project_id=project_id,
            parent_task_id=parent_task_id, tags=tags, add_tags=add_tags,
            remove_tags=remove_tags,
        )

        # --- Build AppleScript ---

        bulk_block = ""
        if has_bulk:
            bulk_block = "\n                ".join(bulk_commands)

        per_task_block = ""
        if has_per_task:
            ids_applescript = ", ".join(
                [f'"{self._escape_applescript_string(tid)}"' for tid in ids_list]
            )
            per_task_cmds_str = "\n                        ".join(per_task_commands)
            per_task_block = f'''
                set taskIdList to {{{ids_applescript}}}
                set successCount to 0

                repeat with taskId in taskIdList
                    try
                        set theTask to first flattened task whose id is taskId
                        {per_task_cmds_str}
                        set successCount to successCount + 1
                    on error
                        -- Task not found or update failed, skip
                    end try
                end repeat'''

        # Count: bulk uses pre-counted value, per-task uses successCount
        if has_bulk and not has_per_task:
            count_expr = f"count of ({or_chain_target})"
            script = f'''
        tell application "OmniFocus"
            tell front document
                set preCount to ({count_expr})
                {bulk_block}
                return preCount as text
            end tell
        end tell
        '''
        elif has_per_task and not has_bulk:
            script = f'''
        tell application "OmniFocus"
            tell front document
                {per_task_block}
                return successCount as text
            end tell
        end tell
        '''
        else:
            # Hybrid: bulk commands first, then repeat loop
            count_expr = f"count of ({or_chain_target})"
            script = f'''
        tell application "OmniFocus"
            tell front document
                {bulk_block}
                {per_task_block}
                return successCount as text
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            updated_count = int(result.strip())
            total_count = len(ids_list)
            failed_count = total_count - updated_count

            # Build list of updated IDs (AppleScript doesn't track which specific ones failed)
            updated_ids = ids_list[:updated_count] if updated_count > 0 else []

            return {
                "updated_count": updated_count,
                "failed_count": failed_count,
                "updated_ids": updated_ids,
                "failures": []  # Batch AppleScript doesn't provide per-task failure detail
            }
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error batch updating tasks: {e.stderr}")


    def _get_tag_exclusivity_map(self) -> dict[str, bool]:
        """Read childrenAreMutuallyExclusive for all tags via OmniAutomation.

        Returns:
            dict: {tag_id: bool} mapping tag IDs to exclusivity status

        Raises:
            Exception: If OmniAutomation is unavailable (headless test DB)
        """
        js_code = (
            "var result = {};"
            " flattenedTags.forEach(function(t) {"
            " result[t.id.primaryKey] = t.childrenAreMutuallyExclusive;"
            " });"
            " JSON.stringify(result);"
        )
        js_script = (
            'tell application "OmniFocus"\n'
            f'    evaluate javascript "{js_code}"\n'
            'end tell'
        )
        result = run_applescript(js_script)
        return json.loads(result)

    def _set_tag_exclusivity(self, tag_id: str, value: bool) -> None:
        """Set childrenAreMutuallyExclusive on a tag via OmniAutomation.

        Args:
            tag_id: The tag ID
            value: True to make children mutually exclusive, False otherwise
        """
        tag_id_js = self._escape_js_string(tag_id)
        value_js = "true" if value else "false"
        js_code = (
            f"var tag = Tag.byIdentifier('{tag_id_js}');"
            f" if (tag) {{ tag.childrenAreMutuallyExclusive = {value_js}; 'ok'; }}"
            f" else {{ 'not found'; }}"
        )
        js_script = (
            'tell application "OmniFocus"\n'
            f'    evaluate javascript "{js_code}"\n'
            'end tell'
        )
        result = run_applescript(js_script)
        if 'not found' in result:
            raise Exception(f"Tag not found: {tag_id}")

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
                        set tagHidden to hidden of t
                        set tagAllows to allows next action of t
                        if tagHidden then
                            set tagStatus to "dropped"
                        else if tagAllows then
                            set tagStatus to "active"
                        else
                            set tagStatus to "on hold"
                        end if

                        -- Get parent tag ID (empty string if top-level)
                        set parentTagId to ""
                        set tagContainer to container of t
                        if class of tagContainer is tag then
                            set parentTagId to id of tagContainer
                        end if

                        -- Build JSON manually
                        set jsonLine to "{" & ¬
                            "\\"id\\": \\"" & tagId & "\\", " & ¬
                            "\\"name\\": \\"" & my escapeJSON(tagName) & "\\", " & ¬
                            "\\"status\\": \\"" & tagStatus & "\\", " & ¬
                            "\\"parentTagId\\": \\"" & parentTagId & "\\"" & ¬
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
                tags = json.loads(result)
            else:
                tags = []

            # Enrich with OmniAutomation-only property (graceful fallback)
            if self._test_mode:
                # OmniAutomation crashes on headless test databases (#324)
                for tag in tags:
                    tag['childrenAreMutuallyExclusive'] = False
            else:
                try:
                    exclusivity_map = self._get_tag_exclusivity_map()
                    for tag in tags:
                        tag['childrenAreMutuallyExclusive'] = exclusivity_map.get(
                            tag['id'], False
                        )
                except Exception:
                    for tag in tags:
                        tag['childrenAreMutuallyExclusive'] = False

            return tags
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error querying tags: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing tags output: {e}")

    def create_tag(
        self,
        name: str,
        parent_tag: Optional[str] = None,
        children_are_mutually_exclusive: bool = False
    ) -> str:
        """Create a new tag in OmniFocus.

        Args:
            name: The name of the tag to create
            parent_tag: Optional parent tag name for nesting (e.g., "Energy" to create "Energy : High")
            children_are_mutually_exclusive: If True, child tags will be
                mutually exclusive (assigning one removes others). Set via
                OmniAutomation after creation.

        Returns:
            The ID of the created tag

        Raises:
            ValueError: If a tag with the same name already exists at the target level
            Exception: If parent tag not found or creation fails
        """
        self._verify_database_safety('create_tag')

        name_escaped = self._escape_applescript_string(name)

        if parent_tag is None:
            script = f'''
            tell application "OmniFocus"
                tell front document
                    try
                        set existingTag to first flattened tag whose name is "{name_escaped}"
                        return "EXISTS: " & id of existingTag
                    on error
                        -- Tag doesn't exist, create it
                    end try
                    try
                        set newTag to make new tag with properties {{name:"{name_escaped}"}}
                        return id of newTag
                    on error errMsg
                        return "ERROR: " & errMsg
                    end try
                end tell
            end tell
            '''
        else:
            parent_escaped = self._escape_applescript_string(parent_tag)
            script = f'''
            tell application "OmniFocus"
                tell front document
                    try
                        set parentTag to first flattened tag whose name is "{parent_escaped}"
                    on error
                        return "ERROR: Parent tag '{parent_escaped}' not found"
                    end try
                    -- Check if child tag already exists under parent
                    try
                        set existingChild to first tag of parentTag whose name is "{name_escaped}"
                        return "EXISTS: " & id of existingChild
                    on error
                        -- Child doesn't exist, create it
                    end try
                    try
                        set newTag to make new tag at end of tags of parentTag with properties {{name:"{name_escaped}"}}
                        return id of newTag
                    on error errMsg
                        return "ERROR: " & errMsg
                    end try
                end tell
            end tell
            '''

        try:
            result = run_applescript(script)
            result = result.strip()
            if result.startswith("EXISTS:"):
                tag_id = result[len("EXISTS:"):].strip()
                raise ValueError(f"Tag '{name}' already exists (ID: {tag_id})")
            if result.startswith("ERROR:"):
                raise Exception(f"Error creating tag: {result[len('ERROR:'):]}")

            # Post-create: set exclusivity via OmniAutomation (if requested)
            # OmniAutomation crashes on headless test databases (#324)
            if children_are_mutually_exclusive and not self._test_mode:
                self._set_tag_exclusivity(result, True)

            return result
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error creating tag: {e.stderr}")

    def update_tag(
        self,
        tag_id: str,
        name: Optional[str] = None,
        status: Optional[str] = None,
        children_are_mutually_exclusive: Optional[bool] = None
    ) -> dict:
        """Update properties of an existing tag.

        Args:
            tag_id: The ID of the tag to update
            name: New tag name (optional)
            status: Tag status (optional). Values: "active", "on_hold",
                "dropped". Active tags allow next actions. On-hold tags
                exclude tasks from available queries. Dropped tags are
                hidden from most views.
            children_are_mutually_exclusive: If True, child tags of this
                tag are mutually exclusive (assigning one removes others).
                Set via OmniAutomation. (optional)

        Returns:
            dict: {
                "success": bool,
                "tag_id": str,
                "updated_fields": list[str],
                "error": Optional[str]
            }

        Raises:
            ValueError: If tag_id is empty, no fields provided, or
                invalid status
            Exception: If tag not found or update fails
        """
        self._verify_database_safety('update_tag')

        if not tag_id:
            raise ValueError("tag_id is required")

        valid_statuses = {"active", "on_hold", "dropped"}
        if status is not None and status not in valid_statuses:
            raise ValueError(
                f"Invalid status '{status}'. "
                f"Must be one of: {', '.join(sorted(valid_statuses))}"
            )

        all_fields = {
            "name": name,
            "status": status,
            "children_are_mutually_exclusive": children_are_mutually_exclusive,
        }
        if all(v is None for v in all_fields.values()):
            raise ValueError("At least one field must be provided to update")

        tag_id_escaped = self._escape_applescript_string(tag_id)
        updated_fields = []
        set_lines = []

        if name is not None:
            name_escaped = self._escape_applescript_string(name)
            set_lines.append(f'set name of theTag to "{name_escaped}"')
            updated_fields.append("name")

        if status is not None:
            if status == "active":
                set_lines.append('set hidden of theTag to false')
                set_lines.append('set allows next action of theTag to true')
            elif status == "on_hold":
                set_lines.append('set hidden of theTag to false')
                set_lines.append('set allows next action of theTag to false')
            elif status == "dropped":
                set_lines.append('set hidden of theTag to true')
            updated_fields.append("status")

        # Run AppleScript for name/status changes (if any)
        if set_lines:
            set_block = "\n                        ".join(set_lines)
            fields_json = ", ".join(f'\\"{f}\\"' for f in updated_fields)

            script = f'''
            tell application "OmniFocus"
                tell front document
                    try
                        set theTag to first flattened tag whose id is "{tag_id_escaped}"
                    on error
                        return "ERROR: Tag not found"
                    end try
                    try
                        {set_block}
                        return "{{\\"success\\": true, \\"updated_fields\\": [{fields_json}]}}"
                    on error errMsg
                        return "ERROR: " & errMsg
                    end try
                end tell
            end tell
            '''

            try:
                result = run_applescript(script)
                result = result.strip()
                if result.startswith("ERROR:"):
                    raise Exception(
                        f"Error updating tag: {result[len('ERROR:'):]}"
                    )
                parsed = json.loads(result)
            except json.JSONDecodeError:
                raise Exception(
                    f"Error parsing update tag result: {result}"
                )
            except subprocess.CalledProcessError as e:
                raise Exception(f"Error updating tag: {e.stderr}")
        else:
            parsed = {"success": True, "updated_fields": []}

        # Post-update: set exclusivity via OmniAutomation (if requested)
        # OmniAutomation crashes on headless test databases (#324)
        if children_are_mutually_exclusive is not None and not self._test_mode:
            self._set_tag_exclusivity(tag_id, children_are_mutually_exclusive)
            parsed["updated_fields"].append(
                "children_are_mutually_exclusive"
            )

        parsed["tag_id"] = tag_id
        parsed["error"] = None
        return parsed

    def delete_tags(self, tag_ids: Union[str, list[str]]) -> dict:
        """Delete one or more tags from OmniFocus.

        Args:
            tag_ids: Single tag ID (str) or list of tag IDs to delete

        Returns:
            dict: {
                "deleted_count": int,
                "failed_count": int,
                "deleted_ids": list[str],
                "failures": list[dict]
            }

        Raises:
            ValueError: If tag_ids is empty
            Exception: If the operation fails
        """
        self._verify_database_safety('delete_tags')

        if isinstance(tag_ids, str):
            ids_list_input = [tag_ids]
        else:
            ids_list_input = tag_ids

        if not ids_list_input:
            raise ValueError("tag_ids cannot be empty")

        ids_list = ", ".join([f'"{self._escape_applescript_string(tid)}"' for tid in ids_list_input])

        script = f'''
        tell application "OmniFocus"
            tell front document
                set tagIdList to {{{ids_list}}}
                set successCount to 0

                repeat with tagId in tagIdList
                    try
                        set theTag to first flattened tag whose id is tagId
                        delete theTag
                        set successCount to successCount + 1
                    on error
                        -- Tag not found, skip
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
            deleted_ids = ids_list_input[:deleted_count] if deleted_count > 0 else []

            return {
                "deleted_count": deleted_count,
                "failed_count": failed_count,
                "deleted_ids": deleted_ids,
                "failures": []
            }
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error deleting tags: {e.stderr}")
        except ValueError as e:
            raise Exception(f"Error parsing delete result: {e}")

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
        ids_list = ", ".join([f'"{self._escape_applescript_string(task_id)}"' for task_id in ids_list_input])

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

    def delete_projects(self, project_ids: Union[str, list[str]]) -> dict:
        """Delete one or more projects from OmniFocus (NEW API - Enhanced with Union type).

        NEW API changes:
        - Accepts Union[str, list[str]] for project_ids (single or multiple)
        - Returns dict instead of int for consistency with update_projects()
        - Consolidates delete_project() functionality

        Args:
            project_ids: Single project ID (str) or list of project IDs to delete

        Returns:
            dict: {
                "deleted_count": int,     # Number of successfully deleted projects
                "failed_count": int,      # Number of failed deletions
                "deleted_ids": list[str], # IDs of successfully deleted projects
                "failures": list[dict]    # Failed deletions with errors
            }

        Raises:
            ValueError: If project_ids is empty
            Exception: If the operation fails completely
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('delete_projects')

        # Normalize project_ids to list
        if isinstance(project_ids, str):
            ids_list_data = [project_ids]
        else:
            ids_list_data = project_ids

        if not ids_list_data:
            raise ValueError("project_ids cannot be empty")

        # Build AppleScript list of project IDs
        ids_list = ", ".join([f'"{self._escape_applescript_string(project_id)}"' for project_id in ids_list_data])

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
            deleted_count = int(result.strip())
            failed_count = len(ids_list_data) - deleted_count

            # Return dict format for consistency with update_projects()
            return {
                "deleted_count": deleted_count,
                "failed_count": failed_count,
                "deleted_ids": ids_list_data[:deleted_count],  # Assume first N succeeded
                "failures": []  # AppleScript doesn't track individual failures
            }
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
                    set folderHidden to hidden of f
                    set folderInfo to "{" & quote & "id" & quote & ":" & quote & (id of f) & quote & "," & quote & "name" & quote & ":" & quote & (name of f) & quote & "," & quote & "path" & quote & ":" & quote & folderPath & quote & "," & quote & "hidden" & quote & ":" & (folderHidden as text) & "}"
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
            folders = json.loads(result)
            for folder in folders:
                folder["status"] = "dropped" if folder.get("hidden") else "active"
            return folders
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error retrieving folders: {e.stderr}")
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing folder data: {e}")


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
                            set parentFolder to first folder whose name is "{self._escape_applescript_string(parts[0])}"
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
                folder_navigation = f'first folder whose name is "{self._escape_applescript_string(parts[0])}"'
                for part in parts[1:]:
                    folder_navigation = f'first folder of ({folder_navigation}) whose name is "{self._escape_applescript_string(part)}"'

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


    def update_folder(
        self,
        folder_id: str,
        name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict:
        """Update properties of an existing folder.

        Args:
            folder_id: The ID of the folder to update
            name: New folder name (optional)
            status: Folder status — "active" or "dropped" (optional).
                Dropping a folder hides it and drops all contained projects.

        Returns:
            dict: {"success": bool, "folder_id": str, "updated_fields": list[str]}

        Raises:
            ValueError: If no fields provided or invalid status
        """
        self._verify_database_safety('update_folder')

        if not folder_id:
            raise ValueError("folder_id is required")

        if name is None and status is None:
            raise ValueError("At least one field must be provided to update")

        valid_statuses = ["active", "dropped"]
        if status is not None and status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of: {', '.join(valid_statuses)}")

        folder_id_escaped = self._escape_applescript_string(folder_id)
        set_lines = []
        updated_fields = []

        if name is not None:
            name_escaped = self._escape_applescript_string(name)
            set_lines.append(f'set name of theFolder to "{name_escaped}"')
            updated_fields.append("name")

        if status is not None:
            if status == "active":
                set_lines.append('set hidden of theFolder to false')
            else:  # dropped
                set_lines.append('set hidden of theFolder to true')
            updated_fields.append("status")

        set_block = "\n                ".join(set_lines)

        script = f'''
        tell application "OmniFocus"
            tell front document
                try
                    set theFolder to first flattened folder whose id is "{folder_id_escaped}"
                    {set_block}
                    return "true"
                on error errMsg
                    return "ERROR: " & errMsg
                end try
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            if result.startswith("ERROR:"):
                return {"success": False, "folder_id": folder_id, "updated_fields": [], "error": result}
            return {"success": True, "folder_id": folder_id, "updated_fields": updated_fields}
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error updating folder: {e.stderr}")

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
                    set theTask to first flattened task whose id is "{self._escape_applescript_string(task_id)}"
                    set refTask to first flattened task whose id is "{self._escape_applescript_string(reference_task_id)}"

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

    def reorder_project(self, project_id: str, before_project_id: Optional[str] = None, after_project_id: Optional[str] = None) -> bool:
        """Reorder a project by moving it before or after another project.

        Args:
            project_id: The ID of the project to move
            before_project_id: Move the project before this project (optional)
            after_project_id: Move the project after this project (optional)

        Note:
            Exactly one of before_project_id or after_project_id must be provided.
            Both projects must be in the same folder.

        Returns:
            True if operation was successful

        Raises:
            ValueError: If project_id is empty, or neither/both reference IDs provided
            Exception: If projects not found, not in same folder, or operation fails
        """
        # SAFETY: Verify database before modifying
        self._verify_database_safety('reorder_project')

        if not project_id:
            raise ValueError("project_id is required")

        # Validate parameters
        if before_project_id is None and after_project_id is None:
            raise ValueError("Must provide either before_project_id or after_project_id")
        if before_project_id is not None and after_project_id is not None:
            raise ValueError("Cannot provide both before_project_id and after_project_id")

        reference_project_id = before_project_id if before_project_id else after_project_id
        position = "before" if before_project_id else "after"

        script = f'''
        tell application "OmniFocus"
            tell front document
                try
                    set theProject to first flattened project whose id is "{self._escape_applescript_string(project_id)}"
                    set refProject to first flattened project whose id is "{self._escape_applescript_string(reference_project_id)}"

                    -- Move project to before/after reference project
                    move theProject to {position} refProject
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
                raise Exception(f"Error reordering project: {result}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error reordering project: {e.stderr}")




    def get_perspectives(self) -> list[dict]:
        """Get all perspectives from OmniFocus with name, id, and type.

        Returns:
            List of dicts with name, id (None for some built-ins), and
            type ("built-in" or "custom") for each perspective.
        """
        script = '''
        on escapeJSON(theText)
            set resultText to ""
            repeat with i from 1 to count of theText
                set c to character i of theText
                if c is "\\"" then
                    set resultText to resultText & "\\\\\\""
                else if c is "\\\\" then
                    set resultText to resultText & "\\\\\\\\"
                else
                    set resultText to resultText & c
                end if
            end repeat
            return resultText
        end escapeJSON

        tell application "OmniFocus"
            tell default document
                -- Build lookup of custom perspective names and IDs
                -- Built-in perspectives error on name/id access, so we
                -- catch errors to identify them.
                set customNames to {}
                set customIds to {}
                repeat with p in every perspective
                    try
                        set pName to name of p
                        set pId to id of p
                        set end of customNames to pName
                        set end of customIds to pId
                    end try
                end repeat

                -- Iterate all perspective names (includes built-in + custom)
                set perspNames to perspective names
                set jsonResult to "["
                set isFirst to true

                repeat with pName in perspNames
                    if not isFirst then
                        set jsonResult to jsonResult & ","
                    end if
                    set isFirst to false

                    -- Check if this name is in our custom lookup
                    set pId to missing value
                    set pType to "built-in"
                    repeat with idx from 1 to count of customNames
                        if item idx of customNames is (pName as text) then
                            set pId to item idx of customIds
                            set pType to "custom"
                            exit repeat
                        end if
                    end repeat

                    set nameText to my escapeJSON(pName as text)

                    set jsonResult to jsonResult & "{"
                    set jsonResult to jsonResult & "\\"name\\":\\"" & nameText & "\\""

                    if pId is missing value then
                        set jsonResult to jsonResult & ",\\"id\\":null"
                    else
                        set jsonResult to jsonResult & ",\\"id\\":\\"" & pId & "\\""
                    end if

                    set jsonResult to jsonResult & ",\\"type\\":\\"" & pType & "\\""
                    set jsonResult to jsonResult & "}"
                end repeat
                set jsonResult to jsonResult & "]"
                return jsonResult
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            return json.loads(result)
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

    def set_focus(
        self,
        item_ids: Union[str, list[str]] = None,
        item_types: Union[str, list[str]] = None,
    ) -> dict:
        """Set focus on one or more items, or clear focus.

        OmniFocus supports focusing on projects and folders only.
        Call with no arguments (or empty lists) to clear focus.

        Args:
            item_ids: Single ID or list of IDs to focus on. None or [] to clear.
            item_types: Matching type(s) - each must be "project" or "folder".

        Returns:
            dict with success, action ("set" or "cleared"), and focused_items

        Raises:
            ValueError: If types are invalid or lengths don't match
            Exception: If focus operation fails
        """
        # Normalize to lists
        if item_ids is None:
            ids_list = []
        elif isinstance(item_ids, str):
            ids_list = [item_ids]
        else:
            ids_list = list(item_ids)

        if item_types is None:
            types_list = []
        elif isinstance(item_types, str):
            types_list = [item_types]
        else:
            types_list = list(item_types)

        # Clear focus path
        if not ids_list and not types_list:
            script = '''
            tell application "OmniFocus"
                tell front document
                    tell front document window
                        set focus to {}
                        return "CLEARED"
                    end tell
                end tell
            end tell
            '''
            try:
                run_applescript(script)
                return {
                    "success": True,
                    "action": "cleared",
                    "focused_items": [],
                }
            except subprocess.CalledProcessError as e:
                raise Exception(f"Error clearing focus: {e.stderr}")

        # Validate lengths match
        if len(ids_list) != len(types_list):
            raise ValueError(
                f"item_ids and item_types must have the same length. "
                f"Got {len(ids_list)} IDs and {len(types_list)} types."
            )

        # Validate each type
        valid_types = ["project", "folder"]
        for item_type in types_list:
            if item_type not in valid_types:
                if item_type in ["task", "tag"]:
                    raise ValueError(
                        f"OmniFocus only supports setting focus on projects and folders. "
                        f"Cannot set focus on {item_type}s via AppleScript."
                    )
                else:
                    raise ValueError(
                        f"item_type must be one of {valid_types}, got: {item_type}"
                    )

        # Build AppleScript to find each item and set focus
        lookup_lines = []
        for i, (item_id, item_type) in enumerate(zip(ids_list, types_list)):
            id_escaped = self._escape_applescript_string(item_id)
            if item_type == "project":
                collection = f'flattened projects whose id is "{id_escaped}"'
            else:
                collection = f'flattened folders whose id is "{id_escaped}"'
            lookup_lines.append(
                f'set matchingItems{i} to {collection}\n'
                f'                if (count of matchingItems{i}) = 0 then\n'
                f'                    error "{item_type} with id {id_escaped} not found"\n'
                f'                end if\n'
                f'                set end of focusList to item 1 of matchingItems{i}'
            )

        lookups = "\n                ".join(lookup_lines)

        script = f'''
        tell application "OmniFocus"
            tell front document
                set focusList to {{}}
                {lookups}
                tell front document window
                    set focus to focusList
                    return "SUCCESS"
                end tell
            end tell
        end tell
        '''

        try:
            run_applescript(script)
            focused_items = [
                {"id": item_id, "type": item_type}
                for item_id, item_type in zip(ids_list, types_list)
            ]
            return {
                "success": True,
                "action": "set",
                "focused_items": focused_items,
            }
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error setting focus: {e.stderr}")

    def get_focus(self) -> list[dict]:
        """Get the currently focused items in the OmniFocus window.

        Returns:
            List of dicts with id, name, and type for each focused item.
            Empty list when no focus is set.
        """
        script = '''
        tell application "OmniFocus"
            tell front document
                tell front document window
                    set focusItems to every item of focus
                    set itemCount to count of focusItems
                    if itemCount = 0 then
                        return "[]"
                    end if

                    set jsonResult to "["
                    set isFirst to true
                    repeat with fi in focusItems
                        if not isFirst then
                            set jsonResult to jsonResult & ","
                        end if
                        set isFirst to false

                        if class of fi is project then
                            set fiType to "project"
                        else
                            set fiType to "folder"
                        end if

                        set fiName to name of fi as text
                        set nameText to ""
                        repeat with charIdx from 1 to count of fiName
                            set charVal to character charIdx of fiName
                            if charVal is "\\"" then
                                set nameText to nameText & "\\\\\\""
                            else if charVal is "\\\\" then
                                set nameText to nameText & "\\\\\\\\"
                            else
                                set nameText to nameText & charVal
                            end if
                        end repeat

                        set fiId to id of fi as text

                        set jsonResult to jsonResult & "{"
                        set jsonResult to jsonResult & "\\"id\\":\\"" & fiId & "\\""
                        set jsonResult to jsonResult & ",\\"name\\":\\"" & nameText & "\\""
                        set jsonResult to jsonResult & ",\\"type\\":\\"" & fiType & "\\""
                        set jsonResult to jsonResult & "}"
                    end repeat
                    set jsonResult to jsonResult & "]"
                    return jsonResult
                end tell
            end tell
        end tell
        '''

        try:
            result = run_applescript(script)
            return json.loads(result)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Error getting focus: {e.stderr}")
