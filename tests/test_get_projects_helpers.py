"""Tests for get_projects helper methods.

Tests _validate_get_projects_params and _post_process_projects.
"""
import pytest
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


@pytest.fixture
def client():
    return OmniFocusConnector()


# ── _validate_get_projects_params ───────────────────────────────────────────


class TestValidateGetProjectsParams:

    def test_valid_params_no_error(self, client):
        """Valid parameters accepted without raising."""
        client._validate_get_projects_params(
            modified_after=None, modified_before=None,
            sort_by=None, sort_order="asc",
        )

    def test_invalid_date_raises(self, client):
        """Invalid date format raises ValueError."""
        with pytest.raises(ValueError, match="Invalid date format"):
            client._validate_get_projects_params(
                modified_after="not-a-date", modified_before=None,
                sort_by=None, sort_order="asc",
            )

    def test_invalid_sort_by_raises(self, client):
        """Unrecognized sort_by value raises ValueError."""
        with pytest.raises(ValueError, match="sort_by"):
            client._validate_get_projects_params(
                modified_after=None, modified_before=None,
                sort_by="date", sort_order="asc",
            )

    def test_invalid_sort_order_raises(self, client):
        """Unrecognized sort_order value raises ValueError."""
        with pytest.raises(ValueError, match="sort_order"):
            client._validate_get_projects_params(
                modified_after=None, modified_before=None,
                sort_by=None, sort_order="sideways",
            )

    def test_valid_iso_date_accepted(self, client):
        """ISO 8601 date format accepted without raising."""
        client._validate_get_projects_params(
            modified_after="2025-01-15T00:00:00Z", modified_before=None,
            sort_by=None, sort_order="asc",
        )


# ── _post_process_projects ──────────────────────────────────────────────────


class TestPostProcessProjects:

    def _default_params(self, **overrides):
        defaults = dict(
            modified_after=None, modified_before=None,
            min_task_count=None, has_overdue_tasks=None,
            has_no_due_dates=None, query=None,
            include_task_health=False, stalled_only=False,
            flagged_only=False, sort_by=None, sort_order="asc",
            planned_after=None, planned_before=None,
        )
        defaults.update(overrides)
        return defaults

    def _sample_project(self, **overrides):
        p = {
            "id": "p1", "name": "Project", "note": "",
            "status": "active status", "singletonActionHolder": False,
            "sequential": False, "folderPath": "Work",
        }
        p.update(overrides)
        return p

    def test_computes_parallel_project_type(self, client):
        """Non-sequential non-singleton project typed as parallel."""
        projects = [self._sample_project()]
        result = client._post_process_projects(projects, **self._default_params())
        assert result[0]["projectType"] == "parallel"

    def test_computes_sequential_project_type(self, client):
        """Sequential project typed as sequential."""
        projects = [self._sample_project(sequential=True)]
        result = client._post_process_projects(projects, **self._default_params())
        assert result[0]["projectType"] == "sequential"

    def test_computes_single_actions_project_type(self, client):
        """Singleton action holder project typed as single_actions."""
        projects = [self._sample_project(singletonActionHolder=True)]
        result = client._post_process_projects(projects, **self._default_params())
        assert result[0]["projectType"] == "single_actions"

    def test_query_filters_by_name(self, client):
        """Query matches project name case-insensitively."""
        projects = [
            self._sample_project(id="p1", name="Marketing Plan"),
            self._sample_project(id="p2", name="Engineering"),
        ]
        result = client._post_process_projects(projects, **self._default_params(query="marketing"))
        assert len(result) == 1
        assert result[0]["id"] == "p1"

    def test_query_filters_by_folder_path(self, client):
        """Query matches folder path case-insensitively."""
        projects = [
            self._sample_project(id="p1", folderPath="Work/Marketing"),
            self._sample_project(id="p2", folderPath="Personal"),
        ]
        result = client._post_process_projects(projects, **self._default_params(query="marketing"))
        assert len(result) == 1

    def test_sort_by_name(self, client):
        """Projects sorted alphabetically by name ascending."""
        projects = [
            self._sample_project(name="Zebra"),
            self._sample_project(name="Apple"),
        ]
        result = client._post_process_projects(projects, **self._default_params(sort_by="name"))
        assert result[0]["name"] == "Apple"

    def test_sort_by_name_desc(self, client):
        """Projects sorted alphabetically by name descending."""
        projects = [
            self._sample_project(name="Apple"),
            self._sample_project(name="Zebra"),
        ]
        result = client._post_process_projects(projects, **self._default_params(sort_by="name", sort_order="desc"))
        assert result[0]["name"] == "Zebra"

    def test_stalled_computed_when_task_health(self, client):
        """Stalled flag set when active project has no available tasks."""
        projects = [
            self._sample_project(status="active status", availableCount=0, hasDeferredOnly=False),
        ]
        result = client._post_process_projects(projects, **self._default_params(include_task_health=True))
        assert result[0]["stalled"] is True

    def test_not_stalled_when_has_available(self, client):
        """Stalled flag false when project has available tasks."""
        projects = [
            self._sample_project(status="active status", availableCount=5, hasDeferredOnly=False),
        ]
        result = client._post_process_projects(projects, **self._default_params(include_task_health=True))
        assert result[0]["stalled"] is False

    def test_stalled_only_filters(self, client):
        """Stalled-only filter excludes non-stalled projects."""
        projects = [
            self._sample_project(id="p1", status="active status", availableCount=0, hasDeferredOnly=False),
            self._sample_project(id="p2", status="active status", availableCount=5, hasDeferredOnly=False),
        ]
        result = client._post_process_projects(projects, **self._default_params(
            include_task_health=True, stalled_only=True
        ))
        assert len(result) == 1
        assert result[0]["id"] == "p1"

    def test_flagged_only_filters(self, client):
        """Flagged-only filter excludes unflagged projects."""
        projects = [
            self._sample_project(id="p1", name="P1", flagged=True),
            self._sample_project(id="p2", name="P2", flagged=False),
        ]
        result = client._post_process_projects(projects, **self._default_params(flagged_only=True))
        assert len(result) == 1
        assert result[0]["id"] == "p1"

    def test_flagged_only_false_returns_all(self, client):
        """Flagged-only false returns both flagged and unflagged projects."""
        projects = [
            self._sample_project(id="p1", flagged=True),
            self._sample_project(id="p2", flagged=False),
        ]
        result = client._post_process_projects(projects, **self._default_params(flagged_only=False))
        assert len(result) == 2

    def test_planned_after_filters_projects(self, client):
        """Planned-after filter excludes projects with earlier or no planned date."""
        projects = [
            self._sample_project(id="p1", plannedDate="2026-03-25T10:00:00"),
            self._sample_project(id="p2", plannedDate="2026-03-20T10:00:00"),
            self._sample_project(id="p3"),  # no planned date
        ]
        result = client._post_process_projects(
            projects, **self._default_params(planned_after="2026-03-23")
        )
        assert len(result) == 1
        assert result[0]["id"] == "p1"

    def test_planned_before_filters_projects(self, client):
        """Planned-before filter excludes projects with later planned date."""
        projects = [
            self._sample_project(id="p1", plannedDate="2026-03-25T10:00:00"),
            self._sample_project(id="p2", plannedDate="2026-03-20T10:00:00"),
        ]
        result = client._post_process_projects(
            projects, **self._default_params(planned_before="2026-03-23")
        )
        assert len(result) == 1
        assert result[0]["id"] == "p2"

    def test_passthrough_when_no_filters(self, client):
        """All projects returned unchanged when no filters applied."""
        projects = [self._sample_project()]
        result = client._post_process_projects(projects, **self._default_params())
        assert len(result) == 1


# ── Extracted helpers ─────────────────────────────────────────────────────


class TestComputeProjectTypes:

    def test_parallel_default(self):
        """Default project type is parallel when not sequential or singleton."""
        projects = [{"singletonActionHolder": False, "sequential": False}]
        OmniFocusConnector._compute_project_types(projects)
        assert projects[0]["projectType"] == "parallel"

    def test_sequential(self):
        """Sequential flag produces sequential project type."""
        projects = [{"singletonActionHolder": False, "sequential": True}]
        OmniFocusConnector._compute_project_types(projects)
        assert projects[0]["projectType"] == "sequential"

    def test_single_actions(self):
        """Singleton action holder produces single_actions project type."""
        projects = [{"singletonActionHolder": True, "sequential": False}]
        OmniFocusConnector._compute_project_types(projects)
        assert projects[0]["projectType"] == "single_actions"

    def test_singleton_takes_precedence(self):
        """singletonActionHolder checked first, even if sequential is also True."""
        projects = [{"singletonActionHolder": True, "sequential": True}]
        OmniFocusConnector._compute_project_types(projects)
        assert projects[0]["projectType"] == "single_actions"


class TestFilterProjectsByQuery:

    def test_matches_name(self):
        """Query matches against project name."""
        projects = [{"name": "Marketing Plan", "note": "", "folderPath": ""}]
        result = OmniFocusConnector._filter_projects_by_query(projects, "marketing")
        assert len(result) == 1

    def test_matches_note(self):
        """Query matches against project note."""
        projects = [{"name": "P1", "note": "Review marketing budget", "folderPath": ""}]
        result = OmniFocusConnector._filter_projects_by_query(projects, "marketing")
        assert len(result) == 1

    def test_matches_folder_path(self):
        """Query matches against folder path."""
        projects = [{"name": "P1", "note": "", "folderPath": "Work/Marketing"}]
        result = OmniFocusConnector._filter_projects_by_query(projects, "marketing")
        assert len(result) == 1

    def test_no_match(self):
        """Non-matching query returns empty list."""
        projects = [{"name": "Engineering", "note": "Code review", "folderPath": "Work"}]
        result = OmniFocusConnector._filter_projects_by_query(projects, "marketing")
        assert len(result) == 0

    def test_case_insensitive(self):
        """Query matching is case-insensitive."""
        projects = [{"name": "MARKETING", "note": "", "folderPath": ""}]
        result = OmniFocusConnector._filter_projects_by_query(projects, "marketing")
        assert len(result) == 1


class TestComputeStalledStatus:

    def test_stalled_when_active_no_available(self):
        """Active project with no available tasks marked stalled."""
        projects = [{"status": "active status", "availableCount": 0, "hasDeferredOnly": False}]
        OmniFocusConnector._compute_stalled_status(projects)
        assert projects[0]["stalled"] is True

    def test_not_stalled_when_has_available(self):
        """Active project with available tasks not marked stalled."""
        projects = [{"status": "active status", "availableCount": 3, "hasDeferredOnly": False}]
        OmniFocusConnector._compute_stalled_status(projects)
        assert projects[0]["stalled"] is False

    def test_not_stalled_when_on_hold(self):
        """On-hold project not marked stalled regardless of available count."""
        projects = [{"status": "on hold status", "availableCount": 0, "hasDeferredOnly": False}]
        OmniFocusConnector._compute_stalled_status(projects)
        assert projects[0]["stalled"] is False

    def test_not_stalled_when_deferred_only(self):
        """Active project with only deferred tasks not marked stalled."""
        projects = [{"status": "active status", "availableCount": 0, "hasDeferredOnly": True}]
        OmniFocusConnector._compute_stalled_status(projects)
        assert projects[0]["stalled"] is False
