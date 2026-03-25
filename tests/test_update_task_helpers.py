"""Tests for update_task and update_tasks helper methods.

Tests _validate_update_task_params, _build_update_task_commands,
_execute_recurrence_update, _validate_update_tasks_params,
_build_bulk_update_commands, and _build_per_task_update_commands.
"""
import pytest
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector, TaskStatus


@pytest.fixture
def client():
    return OmniFocusConnector()


# ── _validate_update_task_params ────────────────────────────────────────────


class TestValidateUpdateTaskParams:
    """Tests for _validate_update_task_params — single task update validation."""

    def _call(self, client, **overrides):
        defaults = dict(
            task_id="t1", task_name=None,
            project_id=None, parent_task_id=None,
            tags=None, add_tags=None, remove_tags=None,
            status=None, repetition_method=None,
            note=None, due_date=None, defer_date=None,
            planned_date=None, flagged=None, sequential=None,
            completed_by_children=None,
            estimated_minutes=None, completed=None, recurrence=None,
        )
        defaults.update(overrides)
        return client._validate_update_task_params(**defaults)

    def test_empty_task_id_raises(self, client):
        """Empty task_id string raises ValueError."""
        with pytest.raises(ValueError, match="task_id is required"):
            self._call(client, task_id="", flagged=True)

    def test_project_and_parent_conflict(self, client):
        """Specifying both project_id and parent_task_id raises ValueError."""
        with pytest.raises(ValueError, match="Cannot specify both"):
            self._call(client, project_id="p1", parent_task_id="t2", flagged=True)

    def test_tags_and_add_tags_conflict(self, client):
        """Specifying both tags and add_tags raises ValueError."""
        with pytest.raises(ValueError, match="Cannot specify both tags"):
            self._call(client, tags=["a"], add_tags=["b"])

    def test_tags_and_remove_tags_conflict(self, client):
        """Specifying both tags and remove_tags raises ValueError."""
        with pytest.raises(ValueError, match="Cannot specify both tags"):
            self._call(client, tags=["a"], remove_tags=["b"])

    def test_invalid_status_string_raises(self, client):
        """Unrecognized status string raises ValueError."""
        with pytest.raises(ValueError, match="Invalid status"):
            self._call(client, status="invalid")

    def test_valid_status_string_normalized(self, client):
        """Valid status string is normalized to TaskStatus enum value."""
        _, status = self._call(client, status="dropped")
        assert status == TaskStatus.DROPPED

    def test_invalid_repetition_method_raises(self, client):
        """Unrecognized repetition_method raises ValueError."""
        with pytest.raises(ValueError, match="Invalid repetition_method"):
            self._call(client, repetition_method="bogus", recurrence="FREQ=DAILY")

    def test_no_fields_raises(self, client):
        """No update fields provided raises ValueError."""
        with pytest.raises(ValueError, match="At least one field"):
            self._call(client)


# ── _build_update_task_commands ─────────────────────────────────────────────


class TestBuildUpdateTaskCommands:
    """Tests for _build_update_task_commands — AppleScript command generation for single task updates."""

    def _call(self, client, **overrides):
        defaults = dict(
            task_name=None, note=None, flagged=None, sequential=None,
            completed_by_children=None,
            due_date=None, defer_date=None, planned_date=None,
            estimated_minutes=None, completed=None, status=None,
            project_id=None, parent_task_id=None,
            tags=None, add_tags=None, remove_tags=None,
            recurrence=None, repetition_method=None,
        )
        defaults.update(overrides)
        return client._build_update_task_commands(**defaults)

    def test_task_name_adds_property(self, client):
        """Task name generates a name property and tracks it in updated fields."""
        props, cmds, fields, _ = self._call(client, task_name="New Name")
        assert any('name:' in p for p in props)
        assert "task_name" in fields

    def test_flagged_adds_property(self, client):
        """Flagged true generates a flagged property set to true."""
        props, _, fields, _ = self._call(client, flagged=True)
        assert any('flagged:true' in p for p in props)
        assert "flagged" in fields

    def test_due_date_set(self, client):
        """Due date string generates a set due date command."""
        _, cmds, fields, _ = self._call(client, due_date="2026-04-01")
        assert any('due date' in c for c in cmds)
        assert "due_date" in fields

    def test_due_date_clear(self, client):
        """Empty due date string generates a missing value command to clear it."""
        _, cmds, _, _ = self._call(client, due_date="")
        assert any('missing value' in c for c in cmds)

    def test_completed_true_uses_mark_complete(self, client):
        """Completed true uses mark complete command for recurring task support."""
        _, cmds, _, _ = self._call(client, completed=True)
        assert any('mark complete' in c for c in cmds)

    def test_completed_false_uses_set(self, client):
        """Completed false uses set completed property to uncomplete a task."""
        _, cmds, _, _ = self._call(client, completed=False)
        assert any('set completed' in c for c in cmds)

    def test_status_dropped(self, client):
        """Dropped status generates mark dropped command."""
        _, cmds, _, _ = self._call(client, status=TaskStatus.DROPPED)
        assert any('mark dropped' in c for c in cmds)

    def test_tags_full_replacement(self, client):
        """Full tag replacement removes existing tags then adds new ones."""
        _, cmds, fields, _ = self._call(client, tags=["urgent", "home"])
        # Should remove all existing tags then add each new one
        cmds_str = "\n".join(cmds)
        assert "repeat while" in cmds_str and "remove" in cmds_str
        assert "add tagObj to tags of theTask" in cmds_str
        assert "tags" in fields

    def test_tags_empty_clears(self, client):
        """Empty tags list removes all existing tags without adding new ones."""
        _, cmds, _, _ = self._call(client, tags=[])
        # Should remove all existing tags (no adds)
        cmds_str = "\n".join(cmds)
        assert "repeat while" in cmds_str and "remove" in cmds_str
        assert "add tagObj" not in cmds_str

    def test_add_tags(self, client):
        """Add tags generates commands to append tags without removing existing ones."""
        _, cmds, fields, _ = self._call(client, add_tags=["urgent"])
        assert any('add tagObj' in c for c in cmds)
        assert "add_tags" in fields

    def test_recurrence_set_flags_js(self, client):
        """Setting recurrence flags JavaScript execution as needed."""
        _, _, _, js_needed = self._call(client, recurrence="FREQ=DAILY")
        assert js_needed is True

    def test_recurrence_clear_no_js(self, client):
        """Clearing recurrence uses missing value without JavaScript."""
        _, cmds, _, js_needed = self._call(client, recurrence="")
        assert js_needed is False
        assert any('missing value' in c for c in cmds)

    def test_repetition_method_only_flags_js(self, client):
        """Setting repetition method alone flags JavaScript execution as needed."""
        _, _, _, js_needed = self._call(client, repetition_method="fixed")
        assert js_needed is True

    def test_recurrence_clear_before_drop_in_command_order(self, client):
        """Recurrence removal must precede mark dropped to prevent next occurrence."""
        _, cmds, fields, _ = self._call(
            client, recurrence="", status=TaskStatus.DROPPED
        )
        recurrence_idx = next(
            i for i, c in enumerate(cmds) if 'missing value' in c
        )
        drop_idx = next(
            i for i, c in enumerate(cmds) if 'mark dropped' in c
        )
        assert recurrence_idx < drop_idx, (
            f"Recurrence removal (index {recurrence_idx}) must come before "
            f"mark dropped (index {drop_idx})"
        )
        assert "recurrence" in fields
        assert "status" in fields


# ── _execute_recurrence_update ──────────────────────────────────────────────


class TestExecuteRecurrenceUpdate:
    """Tests for _execute_recurrence_update — OmniAutomation JavaScript execution."""

    def test_skipped_in_test_mode(self, client):
        """In test mode, should not call run_applescript."""
        import os
        from unittest import mock
        os.environ['OMNIFOCUS_TEST_MODE'] = 'true'
        os.environ['OMNIFOCUS_TEST_DATABASE'] = 'OmniFocus-TEST.ofocus'
        test_client = OmniFocusConnector(enable_safety_checks=True)
        try:
            with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_as:
                test_client._execute_recurrence_update("task-1", "FREQ=DAILY", "fixed")
                mock_as.assert_not_called()
        finally:
            os.environ.pop('OMNIFOCUS_TEST_MODE', None)
            os.environ.pop('OMNIFOCUS_TEST_DATABASE', None)


# ── _validate_update_tasks_params ───────────────────────────────────────────


class TestValidateUpdateTasksParams:
    """Tests for _validate_update_tasks_params — batch update validation."""

    def _call(self, client, **overrides):
        defaults = dict(
            task_ids=["t1"], flagged=None, sequential=None, status=None,
            completed=None, project_id=None, parent_task_id=None,
            tags=None, add_tags=None, remove_tags=None,
            due_date=None, defer_date=None, planned_date=None,
            estimated_minutes=None, kwargs={},
        )
        defaults.update(overrides)
        return client._validate_update_tasks_params(**defaults)

    def test_task_name_rejected(self, client):
        """Batch update rejects task_name since it requires unique values per task."""
        with pytest.raises(ValueError, match="task_name is not allowed"):
            self._call(client, kwargs={"task_name": "x"}, flagged=True)

    def test_note_rejected(self, client):
        """Batch update rejects note since it requires unique values per task."""
        with pytest.raises(ValueError, match="note is not allowed"):
            self._call(client, kwargs={"note": "x"}, flagged=True)

    def test_unexpected_kwargs_rejected(self, client):
        """Unknown keyword arguments raise ValueError."""
        with pytest.raises(ValueError, match="Unexpected"):
            self._call(client, kwargs={"foo": "bar"}, flagged=True)

    def test_empty_ids_raises(self, client):
        """Empty task_ids list raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            self._call(client, task_ids=[], flagged=True)

    def test_no_fields_raises(self, client):
        """No update fields provided raises ValueError."""
        with pytest.raises(ValueError, match="Must provide"):
            self._call(client)

    def test_string_id_normalized(self, client):
        """Single string task_id is normalized to a one-element list."""
        ids = self._call(client, task_ids="single-id", flagged=True)
        assert ids == ["single-id"]

    def test_conflict_project_parent(self, client):
        """Specifying both project_id and parent_task_id raises ValueError."""
        with pytest.raises(ValueError, match="Cannot specify both"):
            self._call(client, project_id="p1", parent_task_id="t2", flagged=True)


# ── _build_bulk_update_commands ─────────────────────────────────────────────


class TestBuildBulkUpdateCommands:
    """Tests for _build_bulk_update_commands — batch AppleScript command generation."""

    def _call(self, client, **overrides):
        defaults = dict(
            or_chain_target="(flattened task whose id is \"t1\")",
            flagged=None, sequential=None, due_date=None,
            defer_date=None, planned_date=None,
            estimated_minutes=None, completed=None,
        )
        defaults.update(overrides)
        return client._build_bulk_update_commands(**defaults)

    def test_flagged(self, client):
        """Flagged generates a bulk flagged property command."""
        cmds, has_bulk = self._call(client, flagged=True)
        assert has_bulk is True
        assert any('flagged' in c for c in cmds)

    def test_due_date_set(self, client):
        """Due date generates a bulk set due date command."""
        cmds, has_bulk = self._call(client, due_date="2026-04-01")
        assert has_bulk is True
        assert any('due date' in c for c in cmds)

    def test_due_date_clear(self, client):
        """Empty due date generates a bulk missing value command."""
        cmds, _ = self._call(client, due_date="")
        assert any('missing value' in c for c in cmds)

    def test_completed_true(self, client):
        """Completed true generates a bulk mark complete command."""
        cmds, _ = self._call(client, completed=True)
        assert any('mark complete' in c for c in cmds)

    def test_no_fields_empty(self, client):
        """No fields returns empty commands list and no-bulk flag."""
        cmds, has_bulk = self._call(client)
        assert cmds == []
        assert has_bulk is False


# ── _build_per_task_update_commands ─────────────────────────────────────────


class TestBuildPerTaskUpdateCommands:
    """Tests for _build_per_task_update_commands — per-task loop command generation."""

    def _call(self, client, **overrides):
        defaults = dict(
            completed=None, status=None, project_id=None,
            parent_task_id=None, tags=None, add_tags=None,
            remove_tags=None,
        )
        defaults.update(overrides)
        return client._build_per_task_update_commands(**defaults)

    def test_completed_false(self, client):
        """Completed false generates per-task set completed command."""
        cmds, has = self._call(client, completed=False)
        assert has is True
        assert any('set completed' in c for c in cmds)

    def test_status_dropped(self, client):
        """Dropped status generates per-task mark dropped command."""
        cmds, _ = self._call(client, status="dropped")
        assert any('mark dropped' in c for c in cmds)

    def test_tags_replacement(self, client):
        """Full tag replacement generates per-task newTags command block."""
        cmds, _ = self._call(client, tags=["work"])
        assert any('newTags' in c for c in cmds)

    def test_add_tags(self, client):
        """Add tags generates per-task add tagObj commands."""
        cmds, _ = self._call(client, add_tags=["urgent"])
        assert any('add tagObj' in c for c in cmds)

    def test_remove_tags(self, client):
        """Remove tags generates per-task remove tagObj commands."""
        cmds, _ = self._call(client, remove_tags=["old"])
        assert any('remove tagObj' in c for c in cmds)

    def test_no_fields_empty(self, client):
        """No fields returns empty commands list and no-per-task flag."""
        cmds, has = self._call(client)
        assert cmds == []
        assert has is False
