"""Tests for AppleScript-side query filtering optimization.

Currently, get_tasks(query="...") fetches all tasks and filters in Python.
The optimization moves name/note matching into AppleScript so non-matching
tasks skip property extraction (27 properties × ~0.43ms each).

This is a transparent optimization — same API, same results, just faster.
"""
import json
import pytest
from unittest.mock import patch
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


@pytest.fixture
def client():
    return OmniFocusConnector(enable_safety_checks=False)


class TestQueryAppleScriptFilter:
    """Test that query parameter generates AppleScript-side filtering."""

    def test_query_generates_applescript_name_check(self, client):
        """When query is provided, AppleScript should check task name."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(query="meeting")
            script = mock_run.call_args[0][0]
            # AppleScript should contain a name-matching check
            assert 'meeting' in script.lower()

    def test_query_generates_applescript_note_check(self, client):
        """When query is provided, AppleScript should also check task note."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(query="meeting")
            script = mock_run.call_args[0][0]
            # Should check note field too, not just name
            assert 'note' in script.lower()

    def test_no_query_no_name_filter_in_applescript(self, client):
        """Without query, AppleScript should not contain query-specific matching."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks()
            script = mock_run.call_args[0][0]
            # Should not have a query-specific check variable
            assert 'queryCheck' not in script

    def test_query_results_still_filtered_correctly(self, client):
        """Query should still filter results (whether in AppleScript or Python)."""
        mock_json = json.dumps([
            {"id": "t1", "name": "Team meeting", "note": "", "projectName": "Work",
             "status": "active", "flagged": False},
        ])
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = mock_json
            tasks = client.get_tasks(query="meeting")
            assert len(tasks) == 1
            assert "meeting" in tasks[0]['name'].lower()

    def test_query_with_selective_filter_includes_query_check(self, client):
        """When query is combined with selective filters, query should also filter in AppleScript."""
        with patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '[]'
            client.get_tasks(query="meeting", flagged_only=True)
            script = mock_run.call_args[0][0]
            # Both flagged and query checks should be in the AppleScript
            assert 'meeting' in script.lower()
