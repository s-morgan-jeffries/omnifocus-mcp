"""Tests for delete_tags MCP tool and connector method.

Tests both the server layer (MCP tool) and the connector layer (AppleScript client).
"""
from unittest import mock

import pytest

import omnifocus_mcp.server_fastmcp as server
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector

delete_tags = server.delete_tags


class TestDeleteTagsServer:
    """Tests for delete_tags() MCP tool."""

    def test_delete_single_tag(self):
        """Server deletes single tag and returns success message."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.delete_tags.return_value = {
                "deleted_count": 1,
                "failed_count": 0,
                "deleted_ids": ["tag-001"],
                "failures": [],
            }
            mock_get_client.return_value = mock_client

            result = delete_tags(tag_ids="tag-001")

            mock_client.delete_tags.assert_called_once_with("tag-001")
            assert "Successfully deleted 1 tag" in result

    def test_delete_multiple_tags(self):
        """Server deletes multiple tags and returns count."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.delete_tags.return_value = {
                "deleted_count": 3,
                "failed_count": 0,
                "deleted_ids": ["tag-001", "tag-002", "tag-003"],
                "failures": [],
            }
            mock_get_client.return_value = mock_client

            result = delete_tags(tag_ids=["tag-001", "tag-002", "tag-003"])

            assert "Successfully deleted 3 tags" in result

    def test_delete_partial_failure(self):
        """Server reports partial success when some tags not found."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.delete_tags.return_value = {
                "deleted_count": 1,
                "failed_count": 1,
                "deleted_ids": ["tag-001"],
                "failures": [],
            }
            mock_get_client.return_value = mock_client

            result = delete_tags(tag_ids=["tag-001", "tag-bad"])

            assert "1" in result
            assert "failed" in result.lower()

    def test_delete_empty_list_error(self):
        """Server returns error for empty tag list."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.delete_tags.side_effect = ValueError(
                "tag_ids cannot be empty"
            )
            mock_get_client.return_value = mock_client

            result = delete_tags(tag_ids=[])

            assert "Error" in result


class TestDeleteTagsConnector:
    """Tests for delete_tags() connector method (AppleScript layer)."""

    def test_delete_single_tag_calls_applescript(self):
        """Connector builds correct AppleScript for single tag deletion."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "1"

            client = OmniFocusConnector()
            result = client.delete_tags("tag-001")

            assert result["deleted_count"] == 1
            assert result["failed_count"] == 0
            call_args = mock_run.call_args[0][0]
            assert "delete" in call_args
            assert "tag-001" in call_args

    def test_delete_multiple_tags_calls_applescript(self):
        """Connector builds correct AppleScript for batch tag deletion."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "2"

            client = OmniFocusConnector()
            result = client.delete_tags(["tag-001", "tag-002"])

            assert result["deleted_count"] == 2
            call_args = mock_run.call_args[0][0]
            assert "tag-001" in call_args
            assert "tag-002" in call_args

    def test_delete_empty_list_raises_valueerror(self):
        """Connector raises ValueError for empty list."""
        client = OmniFocusConnector()
        with pytest.raises(ValueError, match="tag_ids cannot be empty"):
            client.delete_tags([])

    def test_delete_applescript_error_raises_exception(self):
        """Connector raises Exception on AppleScript failure."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = Exception("AppleScript error")

            client = OmniFocusConnector()
            with pytest.raises(Exception):
                client.delete_tags("tag-001")

    def test_delete_string_input_normalized_to_list(self):
        """Connector normalizes string input to list internally."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "1"

            client = OmniFocusConnector()
            result = client.delete_tags("tag-single")

            assert result["deleted_count"] == 1
            assert result["deleted_ids"] == ["tag-single"]
