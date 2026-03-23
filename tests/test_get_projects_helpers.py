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
        client._validate_get_projects_params(
            modified_after=None, modified_before=None,
            sort_by=None, sort_order="asc",
        )

    def test_invalid_date_raises(self, client):
        with pytest.raises(ValueError, match="Invalid date format"):
            client._validate_get_projects_params(
                modified_after="not-a-date", modified_before=None,
                sort_by=None, sort_order="asc",
            )

    def test_invalid_sort_by_raises(self, client):
        with pytest.raises(ValueError, match="sort_by"):
            client._validate_get_projects_params(
                modified_after=None, modified_before=None,
                sort_by="date", sort_order="asc",
            )

    def test_invalid_sort_order_raises(self, client):
        with pytest.raises(ValueError, match="sort_order"):
            client._validate_get_projects_params(
                modified_after=None, modified_before=None,
                sort_by=None, sort_order="sideways",
            )

    def test_valid_iso_date_accepted(self, client):
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
        projects = [self._sample_project()]
        result = client._post_process_projects(projects, **self._default_params())
        assert result[0]["projectType"] == "parallel"

    def test_computes_sequential_project_type(self, client):
        projects = [self._sample_project(sequential=True)]
        result = client._post_process_projects(projects, **self._default_params())
        assert result[0]["projectType"] == "sequential"

    def test_computes_single_actions_project_type(self, client):
        projects = [self._sample_project(singletonActionHolder=True)]
        result = client._post_process_projects(projects, **self._default_params())
        assert result[0]["projectType"] == "single_actions"

    def test_query_filters_by_name(self, client):
        projects = [
            self._sample_project(id="p1", name="Marketing Plan"),
            self._sample_project(id="p2", name="Engineering"),
        ]
        result = client._post_process_projects(projects, **self._default_params(query="marketing"))
        assert len(result) == 1
        assert result[0]["id"] == "p1"

    def test_query_filters_by_folder_path(self, client):
        projects = [
            self._sample_project(id="p1", folderPath="Work/Marketing"),
            self._sample_project(id="p2", folderPath="Personal"),
        ]
        result = client._post_process_projects(projects, **self._default_params(query="marketing"))
        assert len(result) == 1

    def test_sort_by_name(self, client):
        projects = [
            self._sample_project(name="Zebra"),
            self._sample_project(name="Apple"),
        ]
        result = client._post_process_projects(projects, **self._default_params(sort_by="name"))
        assert result[0]["name"] == "Apple"

    def test_sort_by_name_desc(self, client):
        projects = [
            self._sample_project(name="Apple"),
            self._sample_project(name="Zebra"),
        ]
        result = client._post_process_projects(projects, **self._default_params(sort_by="name", sort_order="desc"))
        assert result[0]["name"] == "Zebra"

    def test_stalled_computed_when_task_health(self, client):
        projects = [
            self._sample_project(status="active status", availableCount=0, hasDeferredOnly=False),
        ]
        result = client._post_process_projects(projects, **self._default_params(include_task_health=True))
        assert result[0]["stalled"] is True

    def test_not_stalled_when_has_available(self, client):
        projects = [
            self._sample_project(status="active status", availableCount=5, hasDeferredOnly=False),
        ]
        result = client._post_process_projects(projects, **self._default_params(include_task_health=True))
        assert result[0]["stalled"] is False

    def test_stalled_only_filters(self, client):
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
        projects = [
            self._sample_project(id="p1", name="P1", flagged=True),
            self._sample_project(id="p2", name="P2", flagged=False),
        ]
        result = client._post_process_projects(projects, **self._default_params(flagged_only=True))
        assert len(result) == 1
        assert result[0]["id"] == "p1"

    def test_flagged_only_false_returns_all(self, client):
        projects = [
            self._sample_project(id="p1", flagged=True),
            self._sample_project(id="p2", flagged=False),
        ]
        result = client._post_process_projects(projects, **self._default_params(flagged_only=False))
        assert len(result) == 2

    def test_planned_after_filters_projects(self, client):
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
        projects = [self._sample_project()]
        result = client._post_process_projects(projects, **self._default_params())
        assert len(result) == 1
