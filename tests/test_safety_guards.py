"""Tests for database safety guards.

These tests verify that the safety system correctly blocks destructive operations
when test mode is not properly configured.
"""
import os
import pytest
from unittest import mock

from omnifocus_mcp.omnifocus_client import OmniFocusClient, DatabaseSafetyError


class TestSafetyGuardsEnabled:
    """Test that safety guards block operations when not in test mode."""

    @pytest.fixture
    def client_with_safety(self):
        """Create a client with safety checks enabled."""
        return OmniFocusClient(enable_safety_checks=True)

    def test_add_task_blocked_without_test_mode(self, client_with_safety):
        """Test that add_task is blocked without test mode."""
        with pytest.raises(DatabaseSafetyError) as exc_info:
            client_with_safety.add_task("proj-001", "Task Name")

        assert "Cannot perform destructive operation 'add_task'" in str(exc_info.value)
        assert "OMNIFOCUS_TEST_MODE=true" in str(exc_info.value)

    def test_add_note_blocked_without_test_mode(self, client_with_safety):
        """Test that add_note is blocked without test mode."""
        with pytest.raises(DatabaseSafetyError) as exc_info:
            client_with_safety.add_note("proj-001", "Note text")

        assert "Cannot perform destructive operation 'add_note'" in str(exc_info.value)

    def test_complete_task_blocked_without_test_mode(self, client_with_safety):
        """Test that complete_task is blocked without test mode."""
        with pytest.raises(DatabaseSafetyError) as exc_info:
            client_with_safety.complete_task("task-001")

        assert "Cannot perform destructive operation 'complete_task'" in str(exc_info.value)

    def test_update_task_blocked_without_test_mode(self, client_with_safety):
        """Test that update_task is blocked without test mode."""
        with pytest.raises(DatabaseSafetyError) as exc_info:
            client_with_safety.update_task("task-001", name="New Name")

        assert "Cannot perform destructive operation 'update_task'" in str(exc_info.value)

    def test_create_inbox_task_blocked_without_test_mode(self, client_with_safety):
        """Test that create_inbox_task is blocked without test mode."""
        with pytest.raises(DatabaseSafetyError) as exc_info:
            client_with_safety.create_inbox_task("Task Name")

        assert "Cannot perform destructive operation 'create_inbox_task'" in str(exc_info.value)

    def test_add_tag_to_task_blocked_without_test_mode(self, client_with_safety):
        """Test that add_tag_to_task is blocked without test mode."""
        with pytest.raises(DatabaseSafetyError) as exc_info:
            client_with_safety.add_tag_to_task("task-001", "urgent")

        assert "Cannot perform destructive operation 'add_tag_to_task'" in str(exc_info.value)

    def test_read_operations_allowed_without_test_mode(self, client_with_safety):
        """Test that read operations are allowed without test mode."""
        with mock.patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            # These should NOT raise DatabaseSafetyError
            mock_run.return_value = "[]"

            # All of these are read-only operations
            try:
                client_with_safety.get_projects()
                client_with_safety.search_projects("test")
                client_with_safety.get_tasks()
                client_with_safety.get_inbox_tasks()
                client_with_safety.get_tags()
            except DatabaseSafetyError:
                pytest.fail("Read-only operations should not be blocked by safety guards")


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
