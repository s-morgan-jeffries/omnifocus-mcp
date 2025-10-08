"""Tests for boolean tag filtering logic."""
import pytest
from unittest import mock

from omnifocus_mcp.omnifocus_client import OmniFocusClient


@pytest.fixture
def client():
    """Create a client with safety checks disabled."""
    return OmniFocusClient(enable_safety_checks=False)


class TestBooleanTagLogic:
    """Tests for AND/OR/NOT tag filtering."""

    def test_tag_filter_and_mode(self, client):
        """Test AND mode - task must have all tags."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Task 1", "completed": false, "tags": "work,urgent"},
                {"id": "t2", "name": "Task 2", "completed": false, "tags": "work"},
                {"id": "t3", "name": "Task 3", "completed": false, "tags": "urgent"}
            ]'''

            # Should only return tasks with BOTH work AND urgent
            tasks = client.get_tasks(tag_filter=["work", "urgent"], tag_filter_mode="and")

            assert len(tasks) == 1
            assert tasks[0]['id'] == "t1"

    def test_tag_filter_or_mode(self, client):
        """Test OR mode - task must have at least one tag."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Task 1", "completed": false, "tags": "work,urgent"},
                {"id": "t2", "name": "Task 2", "completed": false, "tags": "work"},
                {"id": "t3", "name": "Task 3", "completed": false, "tags": "home"}
            ]'''

            # Should return tasks with work OR urgent
            tasks = client.get_tasks(tag_filter=["work", "urgent"], tag_filter_mode="or")

            assert len(tasks) == 2
            assert tasks[0]['id'] == "t1"
            assert tasks[1]['id'] == "t2"

    def test_tag_filter_not_mode(self, client):
        """Test NOT mode - task must NOT have any of these tags."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Task 1", "completed": false, "tags": "work"},
                {"id": "t2", "name": "Task 2", "completed": false, "tags": "home"},
                {"id": "t3", "name": "Task 3", "completed": false, "tags": "personal"}
            ]'''

            # Should return tasks without work or home tags
            tasks = client.get_tasks(tag_filter=["work", "home"], tag_filter_mode="not")

            assert len(tasks) == 1
            assert tasks[0]['id'] == "t3"

    def test_tag_filter_default_and_mode(self, client):
        """Test that default mode is AND (backward compatible)."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Task 1", "completed": false, "tags": "work,urgent"},
                {"id": "t2", "name": "Task 2", "completed": false, "tags": "work"}
            ]'''

            # Without specifying mode, should default to AND
            tasks = client.get_tasks(tag_filter=["work", "urgent"])

            assert len(tasks) == 1
            assert tasks[0]['id'] == "t1"

    def test_tag_filter_invalid_mode(self, client):
        """Test that invalid mode raises ValueError."""
        with pytest.raises(ValueError, match="Invalid tag_filter_mode"):
            client.get_tasks(tag_filter=["work"], tag_filter_mode="invalid")

    def test_tag_filter_empty_tags(self, client):
        """Test filtering with no tags."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Task 1", "completed": false, "tags": "work"},
                {"id": "t2", "name": "Task 2", "completed": false, "tags": ""}
            ]'''

            tasks = client.get_tasks(tag_filter=["work"], tag_filter_mode="not")

            # Should return task with no tags
            assert len(tasks) == 1
            assert tasks[0]['id'] == "t2"

    def test_tag_filter_case_insensitive(self, client):
        """Test that tag filtering is case-insensitive."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Task 1", "completed": false, "tags": "Work,URGENT"}
            ]'''

            # Should match regardless of case
            tasks = client.get_tasks(tag_filter=["work", "urgent"], tag_filter_mode="and")

            assert len(tasks) == 1

    def test_tag_filter_single_tag_or_mode(self, client):
        """Test OR mode with single tag."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = '''[
                {"id": "t1", "name": "Task 1", "completed": false, "tags": "work"}
            ]'''

            tasks = client.get_tasks(tag_filter=["work"], tag_filter_mode="or")

            assert len(tasks) == 1
