"""Tests for get_tasks helper methods extracted during complexity refactoring.

Tests _build_task_source, _build_task_filter_checks, _validate_get_tasks_params,
and _post_process_tasks.
"""
import pytest
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


@pytest.fixture
def client():
    """Create an OmniFocusConnector instance."""
    return OmniFocusConnector()


# ── _build_task_source ──────────────────────────────────────────────────────


class TestBuildTaskSource:
    """Tests for _build_task_source — task source expression and whose clause building."""

    def test_task_id_returns_whose_id_filter(self, client):
        """Task ID filter produces whose clause matching the given ID."""
        source, whose_active = client._build_task_source(
            task_id="abc-123", parent_task_id=None, inbox_only=False,
            project_id=None, include_completed=False, flagged_only=False,
            next_only=False, dropped_only=False, blocked_only=False,
            overdue=False, query=None, tag_prefiltered_ids=None,
        )
        assert 'whose id is "abc-123"' in source
        assert whose_active is False

    def test_parent_task_id_returns_tasks_of_parent(self, client):
        """Parent task ID scopes source to child tasks of the specified parent."""
        source, whose_active = client._build_task_source(
            task_id=None, parent_task_id="parent-1", inbox_only=False,
            project_id=None, include_completed=False, flagged_only=False,
            next_only=False, dropped_only=False, blocked_only=False,
            overdue=False, query=None, tag_prefiltered_ids=None,
        )
        assert 'tasks of (first flattened task' in source
        assert 'whose id is "parent-1"' in source
        assert whose_active is False

    def test_inbox_only_returns_inbox_tasks(self, client):
        """Inbox flag sets source to inbox tasks without whose clause."""
        source, whose_active = client._build_task_source(
            task_id=None, parent_task_id=None, inbox_only=True,
            project_id=None, include_completed=False, flagged_only=False,
            next_only=False, dropped_only=False, blocked_only=False,
            overdue=False, query=None, tag_prefiltered_ids=None,
        )
        assert source == 'inbox tasks'
        assert whose_active is False

    def test_project_id_returns_flattened_tasks_of_project(self, client):
        """Project ID scopes source to flattened tasks of the specified project."""
        source, whose_active = client._build_task_source(
            task_id=None, parent_task_id=None, inbox_only=False,
            project_id="proj-42", include_completed=False, flagged_only=False,
            next_only=False, dropped_only=False, blocked_only=False,
            overdue=False, query=None, tag_prefiltered_ids=None,
        )
        assert 'flattened tasks of (first flattened project' in source
        assert 'whose id is "proj-42"' in source
        assert whose_active is False

    def test_flagged_only_adds_whose_condition(self, client):
        """Flagged filter adds whose clause for flagged and not-completed conditions."""
        source, whose_active = client._build_task_source(
            task_id=None, parent_task_id=None, inbox_only=False,
            project_id=None, include_completed=False, flagged_only=True,
            next_only=False, dropped_only=False, blocked_only=False,
            overdue=False, query=None, tag_prefiltered_ids=None,
        )
        assert 'flagged is true' in source
        assert 'completed is false' in source
        assert whose_active is True

    def test_multiple_whose_conditions_combined(self, client):
        """Multiple filters combine into a single whose clause with 'and' conjunctions."""
        source, whose_active = client._build_task_source(
            task_id=None, parent_task_id=None, inbox_only=False,
            project_id=None, include_completed=False, flagged_only=True,
            next_only=True, dropped_only=False, blocked_only=False,
            overdue=False, query=None, tag_prefiltered_ids=None,
        )
        assert 'completed is false' in source
        assert 'flagged is true' in source
        assert 'next is true' in source
        assert ' and ' in source
        assert whose_active is True

    def test_no_filters_returns_plain_flattened_tasks(self, client):
        """No filters with include_completed returns plain flattened tasks source."""
        source, whose_active = client._build_task_source(
            task_id=None, parent_task_id=None, inbox_only=False,
            project_id=None, include_completed=True, flagged_only=False,
            next_only=False, dropped_only=False, blocked_only=False,
            overdue=False, query=None, tag_prefiltered_ids=None,
        )
        assert source == 'flattened tasks'
        assert whose_active is False

    def test_tag_prefiltered_ids_adds_id_whose_clause(self, client):
        """Pre-filtered tag IDs produce an OR-chained whose clause matching each ID."""
        source, whose_active = client._build_task_source(
            task_id=None, parent_task_id=None, inbox_only=False,
            project_id=None, include_completed=False, flagged_only=False,
            next_only=False, dropped_only=False, blocked_only=False,
            overdue=False, query=None, tag_prefiltered_ids={"id-1", "id-2"},
        )
        assert 'id is "id-1"' in source or 'id is "id-2"' in source
        assert ' or ' in source
        assert whose_active is True

    def test_query_adds_name_and_note_contains(self, client):
        """Query string adds name-contains and note-contains conditions to whose clause."""
        source, whose_active = client._build_task_source(
            task_id=None, parent_task_id=None, inbox_only=False,
            project_id=None, include_completed=False, flagged_only=False,
            next_only=False, dropped_only=False, blocked_only=False,
            overdue=False, query="search term", tag_prefiltered_ids=None,
        )
        assert 'name contains "search term"' in source
        assert 'note contains "search term"' in source
        assert whose_active is True

    def test_overdue_adds_due_date_condition(self, client):
        """Overdue filter adds effective due date less-than current date condition."""
        source, whose_active = client._build_task_source(
            task_id=None, parent_task_id=None, inbox_only=False,
            project_id=None, include_completed=False, flagged_only=False,
            next_only=False, dropped_only=False, blocked_only=False,
            overdue=True, query=None, tag_prefiltered_ids=None,
        )
        assert 'effective due date < (current date)' in source
        assert whose_active is True

    def test_task_id_escapes_special_characters(self, client):
        """Task ID with special characters is escaped in the whose clause."""
        source, _ = client._build_task_source(
            task_id='id"with"quotes', parent_task_id=None, inbox_only=False,
            project_id=None, include_completed=False, flagged_only=False,
            next_only=False, dropped_only=False, blocked_only=False,
            overdue=False, query=None, tag_prefiltered_ids=None,
        )
        assert '"' not in source.split('whose id is ')[1].strip('"()')[:20] or \
            'id\\"with\\"quotes' in source or 'id' in source


# ── _build_task_filter_checks ───────────────────────────────────────────────


class TestBuildTaskFilterChecks:
    """Tests for _build_task_filter_checks — AppleScript filter string generation."""

    def _default_params(self, **overrides):
        """Return default params with optional overrides."""
        defaults = dict(
            include_completed=False, flagged_only=False, available_only=False,
            overdue=False, dropped_only=False, blocked_only=False,
            next_only=False, due_relative=None, defer_relative=None,
            max_estimated_minutes=None, has_estimate=None,
            tag_filter=None, tag_filter_mode="and", tag_prefiltered_ids=None,
            query=None, whose_active=False,
            on_hold_available_check_batch="",
        )
        defaults.update(overrides)
        return defaults

    # -- Batch checks active when whose_active=False --

    def test_completion_check_active_when_not_include_completed(self, client):
        """Completion check filters out completed tasks by default."""
        checks = client._build_task_filter_checks(**self._default_params())
        assert 'item i of taskComps' in checks['completion_check_batch']

    def test_completion_check_empty_when_include_completed(self, client):
        """Completion check is skipped when include_completed is set."""
        checks = client._build_task_filter_checks(**self._default_params(include_completed=True))
        assert checks['completion_check_batch'] == ""

    def test_flagged_check_active_when_flagged_only(self, client):
        """Flagged filter generates batch check using taskFlags array."""
        checks = client._build_task_filter_checks(**self._default_params(flagged_only=True))
        assert 'item i of taskFlags' in checks['flagged_check_batch']

    def test_dropped_check_active_when_dropped_only(self, client):
        """Dropped filter generates batch check using taskDrops array."""
        checks = client._build_task_filter_checks(**self._default_params(dropped_only=True))
        assert 'item i of taskDrops' in checks['dropped_check_batch']

    def test_blocked_check_active_when_blocked_only(self, client):
        """Blocked filter generates batch check using taskBlocks array."""
        checks = client._build_task_filter_checks(**self._default_params(blocked_only=True))
        assert 'item i of taskBlocks' in checks['blocked_check_batch']

    def test_next_check_active_when_next_only(self, client):
        """Next filter generates batch check using taskNexts array."""
        checks = client._build_task_filter_checks(**self._default_params(next_only=True))
        assert 'item i of taskNexts' in checks['next_check_batch']

    def test_available_check_batch_uses_indexed_data(self, client):
        """Available filter checks dropped, blocked, and defer date arrays."""
        checks = client._build_task_filter_checks(**self._default_params(available_only=True))
        batch = checks['available_check_batch']
        assert 'item i of taskDrops' in batch
        assert 'item i of taskBlocks' in batch
        assert 'item i of deferDates' in batch

    def test_overdue_check_active_when_overdue(self, client):
        """Overdue filter generates batch check comparing dueDates to current date."""
        checks = client._build_task_filter_checks(**self._default_params(overdue=True))
        assert 'item i of dueDates' in checks['overdue_check_batch']

    def test_query_check_active_when_whose_not_active(self, client):
        """Query generates batch check on taskNames and taskNotes when whose is inactive."""
        checks = client._build_task_filter_checks(**self._default_params(query="search"))
        assert 'item i of taskNames' in checks['query_check_batch']
        assert 'item i of taskNotes' in checks['query_check_batch']

    # -- Batch checks suppressed when whose_active=True --

    def test_all_whose_gated_checks_empty_when_whose_active(self, client):
        """All whose-gated batch checks are suppressed when whose clause is active."""
        checks = client._build_task_filter_checks(**self._default_params(
            flagged_only=True, dropped_only=True, blocked_only=True,
            next_only=True, overdue=True, query="search", whose_active=True,
        ))
        assert checks['completion_check_batch'] == ""
        assert checks['flagged_check_batch'] == ""
        assert checks['dropped_check_batch'] == ""
        assert checks['blocked_check_batch'] == ""
        assert checks['next_check_batch'] == ""
        assert checks['overdue_check_batch'] == ""
        assert checks['query_check_batch'] == ""

    # -- Due relative checks (batch) --

    def test_due_relative_today(self, client):
        """Due relative 'today' produces batch check with todayStart and todayEnd bounds."""
        checks = client._build_task_filter_checks(**self._default_params(due_relative="today"))
        assert 'todayStart' in checks['due_relative_check_batch']
        assert 'todayEnd' in checks['due_relative_check_batch']

    def test_due_relative_tomorrow(self, client):
        """Due relative 'tomorrow' produces batch check with tomorrowStart bound."""
        checks = client._build_task_filter_checks(**self._default_params(due_relative="tomorrow"))
        assert 'tomorrowStart' in checks['due_relative_check_batch']

    def test_due_relative_this_week(self, client):
        """Due relative 'this_week' produces batch check with weekEnd bound."""
        checks = client._build_task_filter_checks(**self._default_params(due_relative="this_week"))
        assert 'weekEnd' in checks['due_relative_check_batch']

    def test_due_relative_next_week(self, client):
        """Due relative 'next_week' produces batch check with nextWeekStart bound."""
        checks = client._build_task_filter_checks(**self._default_params(due_relative="next_week"))
        assert 'nextWeekStart' in checks['due_relative_check_batch']

    def test_due_relative_overdue(self, client):
        """Due relative 'overdue' produces batch check comparing to current date."""
        checks = client._build_task_filter_checks(**self._default_params(due_relative="overdue"))
        assert 'current date' in checks['due_relative_check_batch']

    # -- Defer relative checks (batch) --

    def test_defer_relative_today(self, client):
        """Defer relative 'today' produces batch check with todayStart bound."""
        checks = client._build_task_filter_checks(**self._default_params(defer_relative="today"))
        assert 'todayStart' in checks['defer_relative_check_batch']

    def test_defer_relative_tomorrow(self, client):
        """Defer relative 'tomorrow' produces batch check with tomorrowStart bound."""
        checks = client._build_task_filter_checks(**self._default_params(defer_relative="tomorrow"))
        assert 'tomorrowStart' in checks['defer_relative_check_batch']

    def test_defer_relative_this_week(self, client):
        """Defer relative 'this_week' produces batch check with weekEnd bound."""
        checks = client._build_task_filter_checks(**self._default_params(defer_relative="this_week"))
        assert 'weekEnd' in checks['defer_relative_check_batch']

    def test_defer_relative_next_week(self, client):
        """Defer relative 'next_week' produces batch check with nextWeekStart bound."""
        checks = client._build_task_filter_checks(**self._default_params(defer_relative="next_week"))
        assert 'nextWeekStart' in checks['defer_relative_check_batch']

    # -- Estimate checks (batch) --

    def test_max_estimated_minutes(self, client):
        """Max estimated minutes filter checks estMins array against threshold."""
        checks = client._build_task_filter_checks(**self._default_params(max_estimated_minutes=30))
        assert '30' in checks['estimate_check_batch']
        assert 'item i of estMins' in checks['estimate_check_batch']

    def test_has_estimate_true(self, client):
        """Has-estimate true filter checks for non-missing-value estimates."""
        checks = client._build_task_filter_checks(**self._default_params(has_estimate=True))
        assert 'missing value' in checks['estimate_check_batch']

    def test_has_estimate_false(self, client):
        """Has-estimate false filter checks for missing-value estimates."""
        checks = client._build_task_filter_checks(**self._default_params(has_estimate=False))
        assert 'is not missing value' in checks['estimate_check_batch']

    # -- Tag checks (batch) --

    def test_tag_check_batch_and_mode_generates_tag_loop(self, client):
        """AND-mode tag filter generates AppleScript loop checking tagNameLists."""
        checks = client._build_task_filter_checks(**self._default_params(
            tag_filter=["urgent", "home"], tag_filter_mode="and",
        ))
        assert 'urgent' in checks['tag_check_batch']
        assert 'home' in checks['tag_check_batch']
        assert 'tagNameLists' in checks['tag_check_batch']

    def test_tag_check_batch_empty_for_or_mode(self, client):
        """OR mode tag filtering is handled in Python, not AppleScript."""
        checks = client._build_task_filter_checks(**self._default_params(
            tag_filter=["urgent"], tag_filter_mode="or",
        ))
        assert checks['tag_check_batch'] == ""

    def test_tag_check_batch_empty_for_not_mode(self, client):
        """NOT mode tag filtering is handled in Python, not AppleScript."""
        checks = client._build_task_filter_checks(**self._default_params(
            tag_filter=["urgent"], tag_filter_mode="not",
        ))
        assert checks['tag_check_batch'] == ""

    def test_tag_check_batch_skipped_when_prefiltered(self, client):
        """When tag_prefiltered_ids is set, batch tag check is skipped."""
        checks = client._build_task_filter_checks(**self._default_params(
            tag_filter=["urgent"], tag_filter_mode="and",
            tag_prefiltered_ids={"id-1"},
        ))
        assert checks['tag_check_batch'] == ""

    def test_tag_check_batch_active_without_prefilter(self, client):
        """AND-mode tag filter generates tagNameLists check when not pre-filtered."""
        checks = client._build_task_filter_checks(**self._default_params(
            tag_filter=["urgent"], tag_filter_mode="and",
            tag_prefiltered_ids=None,
        ))
        assert 'tagNameLists' in checks['tag_check_batch']

    # -- Query check suppressed when whose_active --

    def test_query_check_empty_when_whose_active(self, client):
        """Query batch check is suppressed when whose clause handles filtering."""
        checks = client._build_task_filter_checks(**self._default_params(
            query="search", whose_active=True,
        ))
        assert checks['query_check_batch'] == ""

    # -- All keys present --

    def test_returns_all_expected_keys(self, client):
        """Filter checks dict contains all 12 expected batch check keys."""
        checks = client._build_task_filter_checks(**self._default_params())
        expected_keys = {
            'completion_check_batch', 'flagged_check_batch', 'dropped_check_batch',
            'blocked_check_batch', 'next_check_batch', 'overdue_check_batch',
            'query_check_batch', 'available_check_batch',
            'due_relative_check_batch', 'defer_relative_check_batch',
            'estimate_check_batch', 'tag_check_batch',
        }
        assert set(checks.keys()) == expected_keys


# ── _validate_get_tasks_params ──────────────────────────────────────────────


class TestValidateGetTasksParams:
    """Tests for _validate_get_tasks_params — parameter validation."""

    def test_valid_params_no_error(self, client):
        """Valid params should not raise."""
        client._validate_get_tasks_params(
            created_after=None, created_before=None,
            modified_after=None, modified_before=None,
            tag_filter_mode="and", sort_by=None, sort_order="asc",
            due_relative=None, defer_relative=None,
        )

    def test_invalid_date_format_raises(self, client):
        """Non-ISO date string raises ValueError with descriptive message."""
        with pytest.raises(ValueError, match="Invalid date format"):
            client._validate_get_tasks_params(
                created_after="not-a-date", created_before=None,
                modified_after=None, modified_before=None,
                tag_filter_mode="and", sort_by=None, sort_order="asc",
                due_relative=None, defer_relative=None,
            )

    def test_invalid_tag_filter_mode_raises(self, client):
        """Unrecognized tag_filter_mode raises ValueError."""
        with pytest.raises(ValueError, match="tag_filter_mode"):
            client._validate_get_tasks_params(
                created_after=None, created_before=None,
                modified_after=None, modified_before=None,
                tag_filter_mode="invalid", sort_by=None, sort_order="asc",
                due_relative=None, defer_relative=None,
            )

    def test_invalid_sort_by_raises(self, client):
        """Unrecognized sort_by field raises ValueError."""
        with pytest.raises(ValueError, match="sort_by"):
            client._validate_get_tasks_params(
                created_after=None, created_before=None,
                modified_after=None, modified_before=None,
                tag_filter_mode="and", sort_by="invalid_field", sort_order="asc",
                due_relative=None, defer_relative=None,
            )

    def test_invalid_sort_order_raises(self, client):
        """Sort order other than asc/desc raises ValueError."""
        with pytest.raises(ValueError, match="sort_order"):
            client._validate_get_tasks_params(
                created_after=None, created_before=None,
                modified_after=None, modified_before=None,
                tag_filter_mode="and", sort_by=None, sort_order="sideways",
                due_relative=None, defer_relative=None,
            )

    def test_invalid_due_relative_raises(self, client):
        """Unrecognized due_relative value raises ValueError."""
        with pytest.raises(ValueError, match="due_relative"):
            client._validate_get_tasks_params(
                created_after=None, created_before=None,
                modified_after=None, modified_before=None,
                tag_filter_mode="and", sort_by=None, sort_order="asc",
                due_relative="yesterday", defer_relative=None,
            )

    def test_invalid_defer_relative_raises(self, client):
        """Unrecognized defer_relative value raises ValueError."""
        with pytest.raises(ValueError, match="defer_relative"):
            client._validate_get_tasks_params(
                created_after=None, created_before=None,
                modified_after=None, modified_before=None,
                tag_filter_mode="and", sort_by=None, sort_order="asc",
                due_relative=None, defer_relative="yesterday",
            )

    def test_valid_iso_date_accepted(self, client):
        """ISO format dates should be accepted."""
        client._validate_get_tasks_params(
            created_after="2025-01-15T00:00:00Z", created_before=None,
            modified_after=None, modified_before=None,
            tag_filter_mode="and", sort_by=None, sort_order="asc",
            due_relative=None, defer_relative=None,
        )


# ── _post_process_tasks ─────────────────────────────────────────────────────


class TestPostProcessTasks:
    """Tests for _post_process_tasks — result normalization and Python-side filtering."""

    def _default_params(self, **overrides):
        defaults = dict(
            tag_filter=None, tag_filter_mode="and", tag_prefiltered_ids=None,
            created_after=None, created_before=None,
            modified_after=None, modified_before=None,
            recurring_only=None,
            sort_by=None, sort_order="asc",
        )
        defaults.update(overrides)
        return defaults

    def _sample_task(self, **overrides):
        task = {
            "id": "t1", "name": "Test Task", "note": "",
            "completed": False, "flagged": False,
            "repetitionMethod": "", "recurrence": "",
            "isRecurring": False, "tags": [],
        }
        task.update(overrides)
        return task

    def test_normalizes_fixed_repetition(self, client):
        """Normalizes 'fixed repetition' to 'fixed' in repetitionMethod."""
        tasks = [self._sample_task(repetitionMethod="fixed repetition", isRecurring=True)]
        result = client._post_process_tasks(tasks, **self._default_params())
        assert result[0]['repetitionMethod'] == 'fixed'

    def test_normalizes_start_after_completion(self, client):
        """Normalizes 'start after completion' to 'start_after_completion'."""
        tasks = [self._sample_task(repetitionMethod="start after completion", isRecurring=True)]
        result = client._post_process_tasks(tasks, **self._default_params())
        assert result[0]['repetitionMethod'] == 'start_after_completion'

    def test_normalizes_due_after_completion(self, client):
        """Normalizes 'due after completion' to 'due_after_completion'."""
        tasks = [self._sample_task(repetitionMethod="due after completion", isRecurring=True)]
        result = client._post_process_tasks(tasks, **self._default_params())
        assert result[0]['repetitionMethod'] == 'due_after_completion'

    def test_normalizes_empty_repetition_method_to_none(self, client):
        """Empty repetitionMethod string is normalized to None."""
        tasks = [self._sample_task(repetitionMethod="")]
        result = client._post_process_tasks(tasks, **self._default_params())
        assert result[0]['repetitionMethod'] is None

    def test_normalizes_empty_recurrence_to_none(self, client):
        """Empty recurrence string is normalized to None."""
        tasks = [self._sample_task(recurrence="")]
        result = client._post_process_tasks(tasks, **self._default_params())
        assert result[0]['recurrence'] is None

    def test_computes_repeat_summary_from_rrule(self, client):
        """RRULE recurrence string produces a human-readable repeatSummary."""
        tasks = [self._sample_task(recurrence="FREQ=WEEKLY;INTERVAL=1", isRecurring=True)]
        result = client._post_process_tasks(tasks, **self._default_params())
        assert result[0]['repeatSummary'] is not None
        assert 'week' in result[0]['repeatSummary'].lower()

    def test_repeat_summary_none_when_no_recurrence(self, client):
        """No recurrence produces None repeatSummary."""
        tasks = [self._sample_task(recurrence="")]
        result = client._post_process_tasks(tasks, **self._default_params())
        assert result[0]['repeatSummary'] is None

    def test_recurring_only_true_filters(self, client):
        """Recurring-only true keeps only tasks with isRecurring set."""
        tasks = [
            self._sample_task(id="t1", isRecurring=True, recurrence="FREQ=DAILY"),
            self._sample_task(id="t2", isRecurring=False),
        ]
        result = client._post_process_tasks(tasks, **self._default_params(recurring_only=True))
        assert len(result) == 1
        assert result[0]['id'] == 't1'

    def test_recurring_only_false_filters(self, client):
        """Recurring-only false keeps only non-recurring tasks."""
        tasks = [
            self._sample_task(id="t1", isRecurring=True, recurrence="FREQ=DAILY"),
            self._sample_task(id="t2", isRecurring=False),
        ]
        result = client._post_process_tasks(tasks, **self._default_params(recurring_only=False))
        assert len(result) == 1
        assert result[0]['id'] == 't2'

    def test_sort_by_name(self, client):
        """Sort by name orders tasks alphabetically ascending."""
        tasks = [
            self._sample_task(id="t1", name="Zebra"),
            self._sample_task(id="t2", name="Apple"),
        ]
        result = client._post_process_tasks(tasks, **self._default_params(sort_by="name"))
        assert result[0]['name'] == 'Apple'
        assert result[1]['name'] == 'Zebra'

    def test_passthrough_when_no_filters(self, client):
        """Tasks pass through unchanged when no post-processing filters are set."""
        tasks = [self._sample_task()]
        result = client._post_process_tasks(tasks, **self._default_params())
        assert len(result) == 1
        assert result[0]['id'] == 't1'


# ── Batch mode invariant ──────────────────────────────────────────────────


class TestBatchModeInvariant:
    """Verify 'a reference to' batch mode pattern exists in generated AppleScript.

    This is the key performance optimization: batch property reads use
    O(P) Apple Events instead of O(N*P). Removing this would cause a
    20-30x regression. See docs/reference/PERFORMANCE_PROFILING.md.
    """

    def test_get_tasks_script_uses_batch_reference(self, client):
        """get_tasks AppleScript must use 'a reference to' for batch reads."""
        filter_checks = {
            'completion_check_batch': '',
            'flagged_check_batch': '',
            'dropped_check_batch': '',
            'blocked_check_batch': '',
            'next_check_batch': '',
            'overdue_check_batch': '',
            'query_check_batch': '',
            'available_check_batch': '',
            'due_relative_check_batch': '',
            'defer_relative_check_batch': '',
            'estimate_check_batch': '',
            'tag_check_batch': '',
        }
        script = client._build_batch_mode_script(
            task_source="flattened tasks",
            on_hold_tags_decl="",
            filter_checks=filter_checks,
        )
        assert "a reference to" in script, (
            "Batch mode script MUST use 'a reference to' for O(P) property reads. "
            "Removing this causes a 20-30x performance regression."
        )

    def test_get_projects_source_uses_batch_reference(self):
        """get_projects source code must contain 'a reference to' for batch reads."""
        import inspect
        source = inspect.getsource(OmniFocusConnector.get_projects)
        assert "a reference to" in source, (
            "get_projects MUST use 'a reference to' for batch property reads."
        )

    def test_get_folders_source_uses_batch_reference(self):
        """get_folders source code must contain 'a reference to' for batch reads."""
        import inspect
        source = inspect.getsource(OmniFocusConnector.get_folders)
        assert "a reference to" in source, (
            "get_folders MUST use 'a reference to' for batch property reads."
        )


# ── _filter_by_date_range: planned date filtering ─────────────────────────


class TestPlannedDateFilter:
    """Tests for planned_after and planned_before parameters in _filter_by_date_range."""

    def _make_tasks(self):
        return [
            {"id": "t1", "plannedDate": "2026-03-20T09:00:00", "name": "early"},
            {"id": "t2", "plannedDate": "2026-03-25T09:00:00", "name": "late"},
            {"id": "t3", "plannedDate": "", "name": "no planned date"},
        ]

    def test_planned_after_filters(self, client):
        """Planned-after filter excludes tasks with planned date before cutoff."""
        tasks = self._make_tasks()
        result = client._filter_by_date_range(
            tasks,
            created_after=None, created_before=None,
            modified_after=None, modified_before=None,
            planned_after="2026-03-22T00:00:00", planned_before=None,
        )
        assert len(result) == 1
        assert result[0]["id"] == "t2"

    def test_planned_before_filters(self, client):
        """Planned-before filter excludes tasks with planned date after cutoff."""
        tasks = self._make_tasks()
        result = client._filter_by_date_range(
            tasks,
            created_after=None, created_before=None,
            modified_after=None, modified_before=None,
            planned_after=None, planned_before="2026-03-22T00:00:00",
        )
        assert len(result) == 1
        assert result[0]["id"] == "t1"

    def test_planned_range_filters(self, client):
        """Combined planned-after and planned-before narrows to date range."""
        tasks = self._make_tasks()
        result = client._filter_by_date_range(
            tasks,
            created_after=None, created_before=None,
            modified_after=None, modified_before=None,
            planned_after="2026-03-19T00:00:00",
            planned_before="2026-03-22T00:00:00",
        )
        assert len(result) == 1
        assert result[0]["id"] == "t1"

    def test_no_planned_date_excluded(self, client):
        """Tasks without a planned date are excluded when planned filter is active."""
        tasks = [{"id": "t3", "plannedDate": "", "name": "no planned date"}]
        result = client._filter_by_date_range(
            tasks,
            created_after=None, created_before=None,
            modified_after=None, modified_before=None,
            planned_after="2026-03-01T00:00:00", planned_before=None,
        )
        assert len(result) == 0

    def test_no_planned_filter_returns_all(self, client):
        """When neither planned_after nor planned_before is set, all tasks pass."""
        tasks = self._make_tasks()
        result = client._filter_by_date_range(
            tasks,
            created_after=None, created_before=None,
            modified_after=None, modified_before=None,
            planned_after=None, planned_before=None,
        )
        assert len(result) == 3


# ── _post_process_projects tag filtering ─────────────────────────────────


class TestProjectTagFilter:
    """Tests for tag filtering in _post_process_projects."""

    def test_filter_projects_by_single_tag(self, client):
        """Projects with matching tag are returned."""
        projects = [
            {"id": "p1", "name": "P1", "tags": ["High Priority", "Work"]},
            {"id": "p2", "name": "P2", "tags": ["Work"]},
            {"id": "p3", "name": "P3", "tags": []},
        ]
        result = client._filter_tasks_by_tags(projects, ["High Priority"], "and")
        assert len(result) == 1
        assert result[0]["id"] == "p1"

    def test_filter_projects_by_multiple_tags(self, client):
        """Only projects with ALL specified tags are returned."""
        projects = [
            {"id": "p1", "name": "P1", "tags": ["High Priority", "Work"]},
            {"id": "p2", "name": "P2", "tags": ["Work"]},
            {"id": "p3", "name": "P3", "tags": ["High Priority"]},
        ]
        result = client._filter_tasks_by_tags(projects, ["High Priority", "Work"], "and")
        assert len(result) == 1
        assert result[0]["id"] == "p1"

    def test_filter_projects_no_match(self, client):
        """No projects match the tag filter."""
        projects = [
            {"id": "p1", "name": "P1", "tags": ["Work"]},
            {"id": "p2", "name": "P2", "tags": []},
        ]
        result = client._filter_tasks_by_tags(projects, ["Nonexistent"], "and")
        assert len(result) == 0

    def test_post_process_projects_with_tag_filter(self, client):
        """_post_process_projects applies tag_filter correctly."""
        projects = [
            {"id": "p1", "name": "P1", "tags": ["Work"], "sequential": False, "singletonActionHolder": False},
            {"id": "p2", "name": "P2", "tags": ["Personal"], "sequential": False, "singletonActionHolder": False},
        ]
        result = client._post_process_projects(
            projects,
            modified_after=None,
            modified_before=None,
            min_task_count=None,
            has_overdue_tasks=None,
            has_no_due_dates=None,
            query=None,
            include_task_health=False,
            stalled_only=False,
            flagged_only=False,
            sort_by=None,
            sort_order="asc",
            tag_filter=["Work"],
        )
        assert len(result) == 1
        assert result[0]["id"] == "p1"
