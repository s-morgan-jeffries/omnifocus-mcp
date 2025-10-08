"""Tests for task search functionality."""
import pytest
from unittest import mock

from omnifocus_mcp.omnifocus_client import OmniFocusClient


@pytest.fixture
def client():
    """Create a client with safety checks disabled."""
    return OmniFocusClient(enable_safety_checks=False)


class TestSearchTasks:
    """Tests for search_tasks method."""

    def test_search_tasks_name_only(self, client):
        """Test searching task names only."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {
                    "id": "task-001",
                    "name": "Budget review meeting",
                    "completed": false
                },
                {
                    "id": "task-002",
                    "name": "Review budget report",
                    "completed": false
                }
            ]'''

            results = client.search_tasks("budget", search_notes=False)

            assert len(results) == 2
            assert results[0]['name'] == "Budget review meeting"
            assert results[1]['name'] == "Review budget report"

    def test_search_tasks_with_notes(self, client):
        """Test searching both names and notes."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {
                    "id": "task-001",
                    "name": "Meeting",
                    "note": "Discuss budget for Q4",
                    "completed": false
                }
            ]'''

            results = client.search_tasks("budget", search_notes=True)

            assert len(results) == 1
            assert "budget" in results[0]['note'].lower()

    def test_search_tasks_case_insensitive(self, client):
        """Test that search is case-insensitive."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {
                    "id": "task-001",
                    "name": "BUDGET Review",
                    "completed": false
                }
            ]'''

            results = client.search_tasks("budget", search_notes=False)

            assert len(results) == 1

    def test_search_tasks_no_results(self, client):
        """Test search with no matches."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = '[]'

            results = client.search_tasks("nonexistent", search_notes=False)

            assert len(results) == 0

    def test_search_tasks_empty_query(self, client):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="query cannot be empty"):
            client.search_tasks("", search_notes=False)

    def test_search_tasks_whitespace_query(self, client):
        """Test that whitespace-only query raises ValueError."""
        with pytest.raises(ValueError, match="query cannot be empty"):
            client.search_tasks("   ", search_notes=False)

    def test_search_tasks_error(self, client):
        """Test error handling in search."""
        import subprocess
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            error = subprocess.CalledProcessError(1, 'osascript')
            error.stderr = "Search error"
            mock_run.side_effect = error

            with pytest.raises(Exception, match="Error searching tasks"):
                client.search_tasks("budget", search_notes=False)
