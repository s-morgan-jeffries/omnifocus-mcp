"""Tests for database safety guards.

These tests verify that the safety system correctly verifies the test database
when test mode is enabled.
"""
import os
import pytest
from unittest import mock

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector, DatabaseSafetyError


class TestSafetyGuardsWithTestMode:
    """Test safety guards when test mode is enabled."""

    @pytest.fixture
    def client_with_test_mode(self):
        """Create a client with test mode configured."""
        # Set environment variables
        os.environ['OMNIFOCUS_TEST_MODE'] = 'true'
        os.environ['OMNIFOCUS_TEST_DATABASE'] = 'OmniFocus-TEST.ofocus'

        client = OmniFocusConnector(enable_safety_checks=True)

        yield client

        # Cleanup
        os.environ.pop('OMNIFOCUS_TEST_MODE', None)
        os.environ.pop('OMNIFOCUS_TEST_DATABASE', None)

    def test_add_task_verifies_database_name(self, client_with_test_mode):
        """Test that create_task verifies database name before proceeding."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # Use a function to return different values based on the script content
            def mock_applescript(script):
                if "return name of it" in script:
                    # Database name verification - return test database name
                    return "OmniFocus-TEST"
                else:
                    # Actual task creation - return task ID
                    return "task-123"

            mock_run.side_effect = mock_applescript

            # NEW API signature: task_name first, then project_id
            result = client_with_test_mode.create_task("Task", project_id="proj-001")
            # create_task returns task ID string, not boolean
            assert result == "task-123"

            # Verify database name was checked
            assert mock_run.call_count == 2
            first_call_script = mock_run.call_args_list[0][0][0]
            assert "name of it" in first_call_script  # Database name check

    def test_add_task_blocked_if_wrong_database(self, client_with_test_mode):
        """Test that create_task is blocked if database name doesn't match."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # Return production database name instead of test database (without .ofocus extension)
            # The safety check looks for "OmniFocus-TEST" in the result, so return "OmniFocus" to fail the check
            mock_run.return_value = "OmniFocus"

            with pytest.raises(DatabaseSafetyError) as exc_info:
                # NEW API signature: task_name first, then project_id
                client_with_test_mode.create_task("Task", project_id="proj-001")

            assert "Database safety check FAILED" in str(exc_info.value)
            # Check that expected database name is mentioned in error
            assert "OmniFocus-TEST" in str(exc_info.value)


class TestSafetyGuardsConfiguration:
    """Test safety guard configuration validation."""

    def test_init_requires_test_database_when_test_mode_enabled(self):
        """Test that initialization fails if test mode is set without database name."""
        os.environ['OMNIFOCUS_TEST_MODE'] = 'true'
        os.environ.pop('OMNIFOCUS_TEST_DATABASE', None)  # Remove database name

        try:
            with pytest.raises(DatabaseSafetyError) as exc_info:
                OmniFocusConnector(enable_safety_checks=True)

            assert "OMNIFOCUS_TEST_DATABASE is not set" in str(exc_info.value)
        finally:
            os.environ.pop('OMNIFOCUS_TEST_MODE', None)

    def test_init_validates_test_database_name(self):
        """Test that initialization fails if test database name is not in allowed list."""
        os.environ['OMNIFOCUS_TEST_MODE'] = 'true'
        os.environ['OMNIFOCUS_TEST_DATABASE'] = 'OmniFocus.ofocus'  # Not allowed!

        try:
            with pytest.raises(DatabaseSafetyError) as exc_info:
                OmniFocusConnector(enable_safety_checks=True)

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
                client = OmniFocusConnector(enable_safety_checks=True)
                assert client is not None
            finally:
                os.environ.pop('OMNIFOCUS_TEST_MODE', None)
                os.environ.pop('OMNIFOCUS_TEST_DATABASE', None)


class TestSafetyGuardsDisabled:
    """Test that safety guards can be disabled for unit tests."""

    @pytest.fixture
    def client_without_safety(self):
        """Create a client with safety checks disabled."""
        return OmniFocusConnector(enable_safety_checks=False)

    def test_destructive_operations_allowed_when_disabled(self, client_without_safety):
        """Test that operations work when safety is disabled (NEW API)."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # Test create_task - returns task ID
            mock_run.return_value = "task-123"
            result = client_without_safety.create_task("Task", project_id="proj-001")
            assert result == "task-123"

            # Test update_task - AppleScript returns "true", update_task returns dict
            mock_run.return_value = "true"
            result = client_without_safety.update_task("task-001", task_name="New")
            assert result["success"] is True
            assert result["task_id"] == "task-001"

            # Test create_task for inbox (no project_id)
            mock_run.return_value = "task-456"
            result = client_without_safety.create_task("Inbox Task")
            assert result == "task-456"

            # All operations work without safety checks - no DatabaseSafetyError raised
            # Test passed - safety checks are disabled, operations succeed
