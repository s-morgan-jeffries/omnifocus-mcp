"""Tests that OmniAutomation calls are skipped in test mode.

OmniAutomation (`evaluate javascript`) crashes on headless test databases.
These tests verify that all OmniAutomation call sites are properly guarded
when OMNIFOCUS_TEST_MODE=true.

See: docs/reference/OMNIFOCUS_AUTOMATION_NOTES.md (lines 96-112)
See: #324 — OmniFocus crashes during integration test suite
"""
import json
import os
import pytest
from unittest import mock

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


@pytest.fixture
def client_test_mode():
    """Create a client with test mode enabled."""
    os.environ['OMNIFOCUS_TEST_MODE'] = 'true'
    os.environ['OMNIFOCUS_TEST_DATABASE'] = 'OmniFocus-TEST.ofocus'
    client = OmniFocusConnector(enable_safety_checks=True)
    yield client
    os.environ.pop('OMNIFOCUS_TEST_MODE', None)
    os.environ.pop('OMNIFOCUS_TEST_DATABASE', None)


@pytest.fixture
def client_prod_mode():
    """Create a client without test mode (production)."""
    os.environ.pop('OMNIFOCUS_TEST_MODE', None)
    os.environ.pop('OMNIFOCUS_TEST_DATABASE', None)
    client = OmniFocusConnector()
    yield client


class TestGetTagsSkipsOmniAutomationInTestMode:
    """get_tags() must not call _get_tag_exclusivity_map() in test mode."""

    def test_get_tags_skips_exclusivity_in_test_mode(self, client_test_mode):
        """In test mode, get_tags should default exclusivity to False without OmniAutomation."""
        tags_json = json.dumps([
            {"id": "tag-1", "name": "Home", "status": "active", "hidden": False}
        ])
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript', return_value=tags_json):
            with mock.patch.object(client_test_mode, '_get_tag_exclusivity_map') as mock_exclusivity:
                tags = client_test_mode.get_tags()
                mock_exclusivity.assert_not_called()
                assert tags[0]['childrenAreMutuallyExclusive'] is False

    def test_get_tags_calls_exclusivity_in_prod_mode(self, client_prod_mode):
        """In production mode, get_tags should call _get_tag_exclusivity_map()."""
        tags_json = json.dumps([
            {"id": "tag-1", "name": "Home", "status": "active", "hidden": False}
        ])
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript', return_value=tags_json):
            with mock.patch.object(client_prod_mode, '_get_tag_exclusivity_map', return_value={"tag-1": True}) as mock_exclusivity:
                tags = client_prod_mode.get_tags()
                mock_exclusivity.assert_called_once()
                assert tags[0]['childrenAreMutuallyExclusive'] is True


class TestCreateTagSkipsOmniAutomationInTestMode:
    """create_tag() must not call _set_tag_exclusivity() in test mode."""

    def test_create_tag_skips_exclusivity_in_test_mode(self, client_test_mode):
        """In test mode, create_tag with exclusivity=True should skip OmniAutomation."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_as:
            # First call: safety check, second call: create tag
            mock_as.side_effect = ["OmniFocus-TEST", "tag-new-id"]
            with mock.patch.object(client_test_mode, '_set_tag_exclusivity') as mock_set:
                result = client_test_mode.create_tag("TestTag", children_are_mutually_exclusive=True)
                mock_set.assert_not_called()
                assert result == "tag-new-id"

    def test_create_tag_calls_exclusivity_in_prod_mode(self, client_prod_mode):
        """In production mode, create_tag with exclusivity=True should call OmniAutomation."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript', return_value="tag-new-id"):
            with mock.patch.object(client_prod_mode, '_set_tag_exclusivity') as mock_set:
                client_prod_mode.create_tag("TestTag", children_are_mutually_exclusive=True)
                mock_set.assert_called_once_with("tag-new-id", True)


class TestUpdateTagSkipsOmniAutomationInTestMode:
    """update_tag() must not call _set_tag_exclusivity() in test mode."""

    def test_update_tag_skips_exclusivity_in_test_mode(self, client_test_mode):
        """In test mode, update_tag with exclusivity should skip OmniAutomation."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_as:
            # First call: safety check, second call: update tag
            mock_as.side_effect = ["OmniFocus-TEST", "true"]
            with mock.patch.object(client_test_mode, '_set_tag_exclusivity') as mock_set:
                result = client_test_mode.update_tag("tag-1", children_are_mutually_exclusive=True)
                mock_set.assert_not_called()

    def test_update_tag_calls_exclusivity_in_prod_mode(self, client_prod_mode):
        """In production mode, update_tag with exclusivity should call OmniAutomation."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript', return_value="true"):
            with mock.patch.object(client_prod_mode, '_set_tag_exclusivity') as mock_set:
                client_prod_mode.update_tag("tag-1", children_are_mutually_exclusive=False)
                mock_set.assert_called_once_with("tag-1", False)


class TestUpdateTaskSkipsOmniAutomationInTestMode:
    """update_task() recurrence OmniAutomation must be skipped in test mode."""

    def test_update_task_recurrence_skips_js_in_test_mode(self, client_test_mode):
        """In test mode, update_task with recurrence should skip evaluate javascript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_as:
            # First call: safety check, second call: update task AppleScript
            mock_as.side_effect = ["OmniFocus-TEST", "true"]
            result = client_test_mode.update_task("task-1", recurrence="FREQ=DAILY;INTERVAL=1")
            # Should only be called twice (safety + update), NOT a third time for JS
            assert mock_as.call_count == 2
            # Verify no call contains "evaluate javascript"
            for call in mock_as.call_args_list:
                script = call[0][0] if call[0] else call[1].get('script', '')
                assert 'evaluate javascript' not in script
