"""Tests for create_tag MCP tool and connector method.

Tests both the server layer (MCP tool) and the connector layer (AppleScript client).
"""
from unittest import mock

import pytest

import omnifocus_mcp.server_fastmcp as server
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector

create_tag = server.create_tag


class TestCreateTagServer:
    """Tests for create_tag() MCP tool."""

    def test_create_tag_success(self):
        """Server creates tag and returns human-readable response."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_tag.return_value = "tag-new-001"
            mock_get_client.return_value = mock_client

            result = create_tag(name="Automation")

            mock_client.create_tag.assert_called_once_with(
                name="Automation", parent_tag=None
            )
            assert "tag-new-001" in result
            assert "Automation" in result
            assert "Successfully created tag" in result

    def test_create_tag_with_parent(self):
        """Server creates nested tag under parent."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_tag.return_value = "tag-new-002"
            mock_get_client.return_value = mock_client

            result = create_tag(name="High", parent_tag="Energy")

            mock_client.create_tag.assert_called_once_with(
                name="High", parent_tag="Energy"
            )
            assert "tag-new-002" in result
            assert "High" in result
            assert "Energy" in result

    def test_create_tag_already_exists(self):
        """Server returns error when tag already exists."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_tag.side_effect = ValueError(
                "Tag 'Work' already exists (ID: tag-existing-001)"
            )
            mock_get_client.return_value = mock_client

            result = create_tag(name="Work")

            assert "Error" in result
            assert "already exists" in result


class TestCreateTagConnector:
    """Tests for create_tag() connector method (AppleScript layer)."""

    def test_create_tag_calls_applescript(self):
        """Connector builds correct AppleScript for root-level tag creation."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "tag-abc-123"

            client = OmniFocusConnector()
            result = client.create_tag("Automation")

            assert result == "tag-abc-123"
            # Verify AppleScript was called
            call_args = mock_run.call_args[0][0]
            assert "make new tag" in call_args
            assert "Automation" in call_args

    def test_create_tag_with_parent_calls_applescript(self):
        """Connector builds correct AppleScript for nested tag creation."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "tag-child-456"

            client = OmniFocusConnector()
            result = client.create_tag("High", parent_tag="Energy")

            assert result == "tag-child-456"
            call_args = mock_run.call_args[0][0]
            assert "make new tag" in call_args
            assert "Energy" in call_args
            assert "High" in call_args

    def test_create_tag_already_exists_raises_valueerror(self):
        """Connector raises ValueError when tag already exists."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "EXISTS: tag-existing-001"

            client = OmniFocusConnector()
            with pytest.raises(ValueError, match="already exists"):
                client.create_tag("Work")

    def test_create_tag_error_raises_exception(self):
        """Connector raises Exception on AppleScript error."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "ERROR: Some AppleScript error"

            client = OmniFocusConnector()
            with pytest.raises(Exception, match="Error creating tag"):
                client.create_tag("BadTag")

    def test_create_tag_escapes_special_characters(self):
        """Connector escapes quotes in tag name."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "tag-escaped-789"

            client = OmniFocusConnector()
            result = client.create_tag('Tag with "quotes"')

            assert result == "tag-escaped-789"
            call_args = mock_run.call_args[0][0]
            # Should contain escaped quotes
            assert '\\"' in call_args or 'quotes' in call_args

    def test_create_tag_parent_not_found(self):
        """Connector raises Exception when parent tag doesn't exist."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "ERROR: Parent tag 'NonExistent' not found"

            client = OmniFocusConnector()
            with pytest.raises(Exception, match="Parent tag"):
                client.create_tag("Child", parent_tag="NonExistent")
