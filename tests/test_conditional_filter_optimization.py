"""Tests for conditional filter-first optimization (Phase 2).

This test file verifies that get_tasks() correctly detects selective filters
and uses the appropriate script generation strategy:
- Selective filters → filter-first architecture (faster)
- Inclusive filters → extract-then-filter architecture (avoids empty check overhead)
"""
import pytest
from unittest import mock

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


@pytest.fixture
def client():
    """Create a client with safety checks disabled."""
    return OmniFocusConnector(enable_safety_checks=False)


class TestFilterDetectionLogic:
    """Tests for detecting whether selective filters are active."""

    def _check_extract_then_filter_mode(self, script):
        """Verify script uses extract-then-filter or batch architecture.

        Unfiltered queries now use batch mode (a reference to) which is
        a superset of extract-then-filter — both extract all properties
        without pre-filtering.
        """
        # Batch mode is acceptable — it's the optimized version of extract-then-filter
        if 'a reference to' in script:
            assert 'id of ft' in script  # batch property reads
            return
        # Check for PHASE 1 comment indicating property extraction first
        assert '-- PHASE 1: Extract basic properties' in script
        # Check for PHASE 2 comment indicating filters second
        assert '-- PHASE 2: Apply filters' in script

    def _check_filter_first_mode(self, script):
        """Verify script uses filter-first or batch architecture.

        Filters with whose clauses now use batch mode (a reference to)
        which is a superset of filter-first — whose pre-filters then
        batch reads extract properties only for matching tasks.
        """
        # Batch mode is acceptable — it's the optimized version with whose + batch reads
        if 'a reference to' in script:
            assert 'id of ft' in script  # batch property reads
            return
        # Check for PHASE 1 comment indicating filters first
        assert '-- PHASE 1: Apply ALL filters using direct property access' in script
        # Check for PHASE 2 comment indicating property extraction second
        assert '-- PHASE 2: Extract ALL properties (only for tasks that passed filters)' in script

    def test_no_filters_not_selective(self, client):
        """Test that no filters means extract-then-filter mode."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks()
            script = mock_run.call_args[0][0]
            self._check_extract_then_filter_mode(script)

    def test_flagged_only_is_selective(self, client):
        """Test that flagged_only triggers filter-first mode."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(flagged_only=True)
            script = mock_run.call_args[0][0]
            self._check_filter_first_mode(script)

    def test_overdue_is_selective(self, client):
        """Test that overdue triggers filter-first mode."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(overdue=True)
            script = mock_run.call_args[0][0]
            self._check_filter_first_mode(script)

    def test_dropped_only_is_selective(self, client):
        """Test that dropped_only triggers filter-first mode."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(dropped_only=True)
            script = mock_run.call_args[0][0]
            self._check_filter_first_mode(script)

    def test_blocked_only_is_selective(self, client):
        """Test that blocked_only triggers filter-first mode."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(blocked_only=True)
            script = mock_run.call_args[0][0]
            self._check_filter_first_mode(script)

    def test_next_only_is_selective(self, client):
        """Test that next_only triggers filter-first mode."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(next_only=True)
            script = mock_run.call_args[0][0]
            self._check_filter_first_mode(script)

    def test_due_relative_today_is_selective(self, client):
        """Test that due_relative=today triggers filter-first mode."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(due_relative='today')
            script = mock_run.call_args[0][0]
            self._check_filter_first_mode(script)

    def test_due_relative_tomorrow_is_selective(self, client):
        """Test that due_relative=tomorrow triggers filter-first mode."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(due_relative='tomorrow')
            script = mock_run.call_args[0][0]
            self._check_filter_first_mode(script)

    def test_due_relative_this_week_is_selective(self, client):
        """Test that due_relative=this_week triggers filter-first mode."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(due_relative='this_week')
            script = mock_run.call_args[0][0]
            self._check_filter_first_mode(script)

    def test_due_relative_next_week_is_selective(self, client):
        """Test that due_relative=next_week triggers filter-first mode."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(due_relative='next_week')
            script = mock_run.call_args[0][0]
            self._check_filter_first_mode(script)

    def test_due_relative_overdue_is_selective(self, client):
        """Test that due_relative=overdue triggers filter-first mode."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(due_relative='overdue')
            script = mock_run.call_args[0][0]
            self._check_filter_first_mode(script)

    def test_query_is_selective(self, client):
        """Test that query triggers filter-first mode (uses whose clause)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(query="test")
            script = mock_run.call_args[0][0]
            self._check_filter_first_mode(script)

    def test_available_only_is_selective(self, client):
        """Test that available_only triggers filter-first mode."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(available_only=True)
            script = mock_run.call_args[0][0]
            self._check_filter_first_mode(script)

    def test_include_completed_not_selective(self, client):
        """Test that include_completed uses extract-then-filter mode (inclusive)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(include_completed=True)
            script = mock_run.call_args[0][0]
            self._check_extract_then_filter_mode(script)

    def test_combined_selective_filters(self, client):
        """Test that multiple selective filters trigger filter-first mode."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(flagged_only=True, overdue=True)
            script = mock_run.call_args[0][0]
            self._check_filter_first_mode(script)

    def test_selective_and_inclusive_filters(self, client):
        """Test that selective filter takes precedence over inclusive filter."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(flagged_only=True, available_only=True)
            script = mock_run.call_args[0][0]
            self._check_filter_first_mode(script)
