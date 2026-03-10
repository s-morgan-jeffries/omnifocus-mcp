"""Tests for update_tag MCP tool and connector method.

Tests both the server layer (MCP tool) and the connector layer (AppleScript client).
"""
from unittest import mock

import pytest

import omnifocus_mcp.server_fastmcp as server
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector

update_tag = server.update_tag


class TestUpdateTagServer:
    """Tests for update_tag() MCP tool."""

    def test_update_tag_name(self):
        """Server updates tag name and returns human-readable response."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_tag.return_value = {
                "success": True,
                "tag_id": "tag-001",
                "updated_fields": ["name"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tag(tag_id="tag-001", name="Renamed")

            mock_client.update_tag.assert_called_once_with(
                tag_id="tag-001", name="Renamed", active=None
            )
            assert "tag-001" in result
            assert "Successfully" in result

    def test_update_tag_active_status(self):
        """Server updates tag active status."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_tag.return_value = {
                "success": True,
                "tag_id": "tag-002",
                "updated_fields": ["active"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tag(tag_id="tag-002", active=False)

            mock_client.update_tag.assert_called_once_with(
                tag_id="tag-002", name=None, active=False
            )
            assert "tag-002" in result
            assert "Successfully" in result

    def test_update_tag_multiple_fields(self):
        """Server updates multiple tag fields at once."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_tag.return_value = {
                "success": True,
                "tag_id": "tag-003",
                "updated_fields": ["name", "active"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tag(tag_id="tag-003", name="New Name", active=True)

            assert "tag-003" in result
            assert "Successfully" in result

    def test_update_tag_not_found(self):
        """Server returns error when tag not found."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_tag.side_effect = Exception(
                "Error updating tag: Tag not found"
            )
            mock_get_client.return_value = mock_client

            result = update_tag(tag_id="tag-nonexistent", name="Foo")

            assert "Error" in result

    def test_update_tag_no_fields(self):
        """Server returns error when no fields provided."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_tag.side_effect = ValueError(
                "At least one field must be provided to update"
            )
            mock_get_client.return_value = mock_client

            result = update_tag(tag_id="tag-001")

            assert "Error" in result


class TestUpdateTagConnector:
    """Tests for update_tag() connector method (AppleScript layer)."""

    def test_update_tag_name_calls_applescript(self):
        """Connector builds correct AppleScript for tag rename."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '{"success": true, "updated_fields": ["name"]}'

            client = OmniFocusConnector()
            result = client.update_tag("tag-001", name="Renamed")

            assert result["success"] is True
            assert "name" in result["updated_fields"]
            call_args = mock_run.call_args[0][0]
            assert "Renamed" in call_args
            assert "tag-001" in call_args

    def test_update_tag_active_calls_applescript(self):
        """Connector builds correct AppleScript for active status change."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '{"success": true, "updated_fields": ["active"]}'

            client = OmniFocusConnector()
            result = client.update_tag("tag-002", active=False)

            assert result["success"] is True
            call_args = mock_run.call_args[0][0]
            assert "tag-002" in call_args
            assert "allows next action" in call_args

    def test_update_tag_no_fields_raises_valueerror(self):
        """Connector raises ValueError when no fields provided."""
        client = OmniFocusConnector()
        with pytest.raises(ValueError, match="At least one field"):
            client.update_tag("tag-001")

    def test_update_tag_empty_id_raises_valueerror(self):
        """Connector raises ValueError when tag_id is empty."""
        client = OmniFocusConnector()
        with pytest.raises(ValueError, match="tag_id is required"):
            client.update_tag("")

    def test_update_tag_error_raises_exception(self):
        """Connector raises Exception on AppleScript error."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "ERROR: Tag not found"

            client = OmniFocusConnector()
            with pytest.raises(Exception, match="Error updating tag"):
                client.update_tag("tag-bad", name="Foo")

    def test_update_tag_escapes_special_characters(self):
        """Connector escapes quotes in tag name."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '{"success": true, "updated_fields": ["name"]}'

            client = OmniFocusConnector()
            client.update_tag("tag-001", name='Tag "quoted"')

            call_args = mock_run.call_args[0][0]
            assert '\\"' in call_args or 'quoted' in call_args
