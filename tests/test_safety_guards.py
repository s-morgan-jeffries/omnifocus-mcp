"""Tests for database safety guards.

These tests verify that the safety system correctly verifies the test database
when test mode is enabled.
"""
import os
import pytest
from unittest import mock

from omnifocus_mcp.omnifocus_client import OmniFocusClient, DatabaseSafetyError


class TestSafetyGuardsWithTestMode:
    """Test safety guards when test mode is enabled."""

    @pytest.fixture
    def client_with_test_mode(self):
        """Create a client with test mode configured."""
        # Set environment variables
        os.environ['OMNIFOCUS_TEST_MODE'] = 'true'
        os.environ['OMNIFOCUS_TEST_DATABASE'] = 'OmniFocus-TEST.ofocus'

        client = OmniFocusClient(enable_safety_checks=True)

        yield client

        # Cleanup
        os.environ.pop('OMNIFOCUS_TEST_MODE', None)
        os.environ.pop('OMNIFOCUS_TEST_DATABASE', None)

    def test_add_task_verifies_database_name(self, client_with_test_mode):
        """Test that add_task verifies database name before proceeding."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # First call: database name verification (returns test database name)
            # Second call: actual add_task operation
            mock_run.side_effect = ["OmniFocus-TEST.ofocus", "true"]

            result = client_with_test_mode.add_task("proj-001", "Task")
            assert result is True

            # Verify database name was checked
            assert mock_run.call_count == 2
            first_call_script = mock_run.call_args_list[0][0][0]
            assert "name of it" in first_call_script  # Database name check

    def test_add_task_blocked_if_wrong_database(self, client_with_test_mode):
        """Test that add_task is blocked if database name doesn't match."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # Return production database name instead of test database
            mock_run.return_value = "OmniFocus.ofocus"

            with pytest.raises(DatabaseSafetyError) as exc_info:
                client_with_test_mode.add_task("proj-001", "Task")

            assert "Database safety check FAILED" in str(exc_info.value)
            assert "PRODUCTION database" in str(exc_info.value)


class TestSafetyGuardsConfiguration:
    """Test safety guard configuration validation."""

    def test_init_requires_test_database_when_test_mode_enabled(self):
        """Test that initialization fails if test mode is set without database name."""
        os.environ['OMNIFOCUS_TEST_MODE'] = 'true'
        os.environ.pop('OMNIFOCUS_TEST_DATABASE', None)  # Remove database name

        try:
            with pytest.raises(DatabaseSafetyError) as exc_info:
                OmniFocusClient(enable_safety_checks=True)

            assert "OMNIFOCUS_TEST_DATABASE is not set" in str(exc_info.value)
        finally:
            os.environ.pop('OMNIFOCUS_TEST_MODE', None)

    def test_init_validates_test_database_name(self):
        """Test that initialization fails if test database name is not in allowed list."""
        os.environ['OMNIFOCUS_TEST_MODE'] = 'true'
        os.environ['OMNIFOCUS_TEST_DATABASE'] = 'OmniFocus.ofocus'  # Not allowed!

        try:
            with pytest.raises(DatabaseSafetyError) as exc_info:
                OmniFocusClient(enable_safety_checks=True)

            assert "not in the allowed test databases list" in str(exc_info.value)
        finally:
            os.environ.pop('OMNIFOCUS_TEST_MODE', None)
            os.environ.pop('OMNIFOCUS_TEST_DATABASE', None)

    def test_allowed_test_database_names(self):
        """Test that all allowed test database names work."""
        allowed_names = [
            "OmniFocus-TEST.ofocus",
            "OmniFocus-Dev.ofocus",
            "OmniFocus-Staging.ofocus",
        ]

        for db_name in allowed_names:
            os.environ['OMNIFOCUS_TEST_MODE'] = 'true'
            os.environ['OMNIFOCUS_TEST_DATABASE'] = db_name

            try:
                # Should not raise an error
                client = OmniFocusClient(enable_safety_checks=True)
                assert client is not None
            finally:
                os.environ.pop('OMNIFOCUS_TEST_MODE', None)
                os.environ.pop('OMNIFOCUS_TEST_DATABASE', None)


class TestSafetyGuardsDisabled:
    """Test that safety guards can be disabled for unit tests."""

    @pytest.fixture
    def client_without_safety(self):
        """Create a client with safety checks disabled."""
        return OmniFocusClient(enable_safety_checks=False)

    def test_destructive_operations_allowed_when_disabled(self, client_without_safety):
        """Test that destructive operations work when safety is disabled."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            # All of these should work without test mode
            result = client_without_safety.add_task("proj-001", "Task")
            assert result is True

            result = client_without_safety.add_note("proj-001", "Note")
            assert result is True

            result = client_without_safety.complete_task("task-001")
            assert result is True

            result = client_without_safety.update_task("task-001", name="New")
            assert result is True

            result = client_without_safety.create_inbox_task("Task")
            assert result is True

            result = client_without_safety.add_tag_to_task("task-001", "tag")
            assert result is True

            result = client_without_safety.delete_task("task-001")
            assert result is True

            result = client_without_safety.delete_project("proj-001")
            assert result is True

            result = client_without_safety.move_task("task-001", "proj-002")
            assert result is True

            result = client_without_safety.drop_task("task-001")
            assert result is True

            client_without_safety.create_folder("Test Folder")

            result = client_without_safety.set_parent_task("task-001", "task-002")
            assert result is True

            result = client_without_safety.set_review_interval("proj-001", interval_weeks=1)
            assert result is True

            result = client_without_safety.mark_project_reviewed("proj-001")
            assert result is True

            result = client_without_safety.set_estimated_minutes("task-001", 60)
            assert result is True
