"""Production database integration tests.

These tests require OmniAutomation (evaluate javascript) which crashes on
headless test databases. They run against the production OmniFocus database
with all operations scoped to a persistent "MCP Test Sandbox" folder.

Safety:
- All entities are created inside the sandbox folder
- Automatic cleanup on teardown (even on failure)
- UUID-based naming prevents conflicts
- Gated by OMNIFOCUS_PROD_TEST=true environment variable

Run with: make test-prod
"""

import os
import uuid
import warnings

import pytest

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


pytestmark = pytest.mark.skipif(
    not os.environ.get("OMNIFOCUS_PROD_TEST"),
    reason="Set OMNIFOCUS_PROD_TEST=true to run (requires production DB)"
)

SANDBOX_FOLDER = "MCP Test Sandbox"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def prod_sandbox_folder():
    """Ensure the MCP Test Sandbox folder exists in production OmniFocus.

    This folder is persistent — folders cannot be deleted via AppleScript.
    Created once, reused forever. All prod test entities live inside it.

    Returns:
        str: Folder ID of the sandbox folder
    """
    client = OmniFocusConnector(enable_safety_checks=False)
    folders = client.get_folders()
    existing = [f for f in folders if f["name"] == SANDBOX_FOLDER]

    if existing:
        return existing[0]["id"]

    # First run: create the sandbox folder
    folder_id = client.create_folder(SANDBOX_FOLDER)
    return folder_id


@pytest.fixture(scope="session")
def prod_client():
    """Connector for production database tests.

    Safety checks are disabled because we're intentionally operating on the
    production database. Safety is enforced by the fixtures, which only create
    entities inside the sandbox folder.

    Scope: session — shared across all prod tests for performance.
    """
    return OmniFocusConnector(enable_safety_checks=False)


@pytest.fixture(scope="function")
def prod_project(prod_client, prod_sandbox_folder):
    """Create a test project inside the sandbox folder, clean up after.

    Yields:
        str: Project ID
    """
    project_name = f"test-Project {uuid.uuid4()}"
    project_id = prod_client.create_project(
        project_name, folder_path=SANDBOX_FOLDER
    )
    yield project_id
    try:
        prod_client.delete_projects(project_id)
    except Exception as e:
        warnings.warn(f"Cleanup failed for project {project_id}: {e}")


@pytest.fixture(scope="function")
def prod_task(prod_client, prod_project):
    """Create a test task in the sandbox project, clean up after.

    Yields:
        str: Task ID
    """
    task_name = f"test-Task {uuid.uuid4()}"
    task_id = prod_client.create_task(task_name, project_id=prod_project)
    yield task_id
    try:
        prod_client.delete_tasks(task_id)
    except Exception as e:
        warnings.warn(f"Cleanup failed for task {task_id}: {e}")


# ============================================================================
# Recurrence Write Tests (migrated from test_integration_real.py)
# ============================================================================

class TestRecurrenceWriteIntegration:
    """Test recurrence write operations via OmniAutomation (production DB only).

    These tests exercise the evaluate javascript path for setting/modifying
    repetition rules, which crashes on headless test databases.
    """

    def test_add_recurrence_to_non_recurring(self, prod_client, prod_task):
        """Test adding recurrence to a non-recurring task via OmniAutomation."""
        result = prod_client.update_task(
            prod_task,
            recurrence="FREQ=WEEKLY",
            repetition_method="fixed"
        )
        assert result["success"] is True

        tasks = prod_client.get_tasks(task_id=prod_task)
        task = tasks[0]
        assert task["isRecurring"] is True
        assert "FREQ=WEEKLY" in task["recurrence"]
        assert task["repetitionMethod"] == "fixed"
        assert task["repeatSummary"] == "Every week"

    def test_modify_existing_recurrence(self, prod_client, prod_task):
        """Test modifying recurrence on an already-recurring task."""
        # First add recurrence
        prod_client.update_task(
            prod_task, recurrence="FREQ=DAILY", repetition_method="fixed"
        )

        # Now modify it
        result = prod_client.update_task(
            prod_task,
            recurrence="FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,WE,FR",
            repetition_method="start_after_completion"
        )
        assert result["success"] is True

        tasks = prod_client.get_tasks(task_id=prod_task)
        task = tasks[0]
        assert task["isRecurring"] is True
        assert "FREQ=WEEKLY" in task["recurrence"]
        assert "INTERVAL=2" in task["recurrence"]
        assert task["repetitionMethod"] == "start_after_completion"
        assert task["repeatSummary"] == "Every 2 weeks on Mon, Wed, Fri"

    def test_change_repetition_method_only(self, prod_client, prod_task):
        """Test changing only the repetition method without changing the RRULE."""
        # First add recurrence
        prod_client.update_task(
            prod_task, recurrence="FREQ=DAILY", repetition_method="fixed"
        )

        # Change method only
        result = prod_client.update_task(
            prod_task, repetition_method="due_after_completion"
        )
        assert result["success"] is True

        tasks = prod_client.get_tasks(task_id=prod_task)
        task = tasks[0]
        assert task["isRecurring"] is True
        assert task["repetitionMethod"] == "due_after_completion"
        # RRULE should be preserved
        assert "FREQ=DAILY" in task["recurrence"]

    def test_remove_recurrence(self, prod_client, prod_task):
        """Test removing recurrence from a recurring task."""
        # First add recurrence
        prod_client.update_task(
            prod_task, recurrence="FREQ=DAILY", repetition_method="fixed"
        )

        # Remove it
        result = prod_client.update_task(prod_task, recurrence="")
        assert result["success"] is True

        tasks = prod_client.get_tasks(task_id=prod_task)
        task = tasks[0]
        assert task["isRecurring"] is False
        assert task["repeatSummary"] is None


# ============================================================================
# Sequential Flag Tests (#307)
# ============================================================================

class TestSequentialFlag:
    """Test sequential flag on action groups (production DB only).

    These tests verify that the sequential property can be set on tasks
    (action groups) via both create_task and update_task.
    """

    def test_create_task_sequential(self, prod_client, prod_project):
        """Test creating a task with sequential=True."""
        task_name = f"test-Sequential {uuid.uuid4()}"
        task_id = prod_client.create_task(
            task_name, project_id=prod_project, sequential=True
        )
        try:
            tasks = prod_client.get_tasks(task_id=task_id)
            task = tasks[0]
            assert task["sequential"] is True
        finally:
            prod_client.delete_tasks(task_id)

    def test_update_task_sequential(self, prod_client, prod_task):
        """Test toggling sequential via update_task."""
        # Default should be parallel (False)
        tasks = prod_client.get_tasks(task_id=prod_task)
        assert tasks[0]["sequential"] is False

        # Set to sequential
        result = prod_client.update_task(prod_task, sequential=True)
        assert result["success"] is True

        tasks = prod_client.get_tasks(task_id=prod_task)
        assert tasks[0]["sequential"] is True

        # Set back to parallel
        result = prod_client.update_task(prod_task, sequential=False)
        assert result["success"] is True

        tasks = prod_client.get_tasks(task_id=prod_task)
        assert tasks[0]["sequential"] is False


# ============================================================================
# Next Occurrence Date Tests (#294)
# ============================================================================

class TestNextOccurrenceDates:
    """Test next occurrence date fields on recurring tasks (production DB only).

    These fields (nextDueDate, nextDeferDate, nextPlannedDate) are read-only,
    computed by OmniFocus from the repetition rule.
    """

    def test_recurring_task_has_next_due_date(self, prod_client, prod_project):
        """A recurring task with a due date should have a populated nextDueDate."""
        task_name = f"test-NextDue {uuid.uuid4()}"
        task_id = prod_client.create_task(
            task_name,
            project_id=prod_project,
            due_date="2026-04-15T17:00:00",
        )
        try:
            # Add recurrence
            prod_client.update_task(
                task_id,
                recurrence="FREQ=WEEKLY",
                repetition_method="fixed"
            )

            tasks = prod_client.get_tasks(task_id=task_id)
            task = tasks[0]
            assert task["isRecurring"] is True
            assert task["nextDueDate"] != "", "nextDueDate should be populated for recurring task"
        finally:
            prod_client.delete_tasks(task_id)

    def test_non_recurring_task_has_empty_next_dates(self, prod_client, prod_task):
        """A non-recurring task should have empty next occurrence dates."""
        tasks = prod_client.get_tasks(task_id=prod_task)
        task = tasks[0]
        assert task["nextDueDate"] == ""
        assert task["nextDeferDate"] == ""
        assert task["nextPlannedDate"] == ""
