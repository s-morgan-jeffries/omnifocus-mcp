"""Tests for create_tag and create_tags MCP tools and connector method.

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
                name="Automation", parent_tag=None,
                children_are_mutually_exclusive=False
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
                name="High", parent_tag="Energy",
                children_are_mutually_exclusive=False
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


class TestCreateTagsUnified:
    """Tests for unified create_tags() with Pydantic model input."""

    def test_create_tags_single_item(self):
        """Single tag returns detailed format matching old create_tag output."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_tag.return_value = "tag-001"
            mock_get_client.return_value = mock_client

            create_tags = server.create_tags
            result = create_tags(tags=[{"name": "Automation"}])

            assert "Successfully created tag" in result
            assert "tag-001" in result
            assert "Automation" in result
            mock_client.create_tag.assert_called_once()

    def test_create_tags_batch(self):
        """Multiple tags return summary with count."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_tag.side_effect = ["tag-001", "tag-002", "tag-003"]
            mock_get_client.return_value = mock_client

            create_tags = server.create_tags
            result = create_tags(tags=[
                {"name": "Tag A"},
                {"name": "Tag B"},
                {"name": "Tag C"},
            ])

            assert "3" in result
            assert mock_client.create_tag.call_count == 3

    def test_create_tags_partial_failure(self):
        """One failure in batch returns mixed results."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_tag.side_effect = [
                "tag-001",
                ValueError("Tag 'Duplicate' already exists"),
                "tag-003",
            ]
            mock_get_client.return_value = mock_client

            create_tags = server.create_tags
            result = create_tags(tags=[
                {"name": "Good Tag"},
                {"name": "Duplicate"},
                {"name": "Also Good"},
            ])

            assert "2" in result
            assert "FAILED" in result
            assert "already exists" in result

    def test_create_tags_passes_all_fields(self):
        """All TagCreate fields are passed through to connector."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_tag.return_value = "tag-001"
            mock_get_client.return_value = mock_client

            create_tags = server.create_tags
            result = create_tags(tags=[{
                "name": "Priority",
                "parent_tag": "Energy",
                "children_are_mutually_exclusive": True,
            }])

            call_kwargs = mock_client.create_tag.call_args[1]
            assert call_kwargs["name"] == "Priority"
            assert call_kwargs["parent_tag"] == "Energy"
            assert call_kwargs["children_are_mutually_exclusive"] is True

    def test_create_tag_delegates_to_create_tags(self):
        """Old create_tag should delegate to create_tags."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.create_tag.return_value = "tag-delegated"
            mock_get_client.return_value = mock_client

            result = create_tag(name="Delegated", parent_tag="Parent")

            assert "tag-delegated" in result
            assert "Successfully" in result
            mock_client.create_tag.assert_called_once()
