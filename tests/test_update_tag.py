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
                tag_id="tag-001", name="Renamed"
            )
            assert "tag-001" in result
            assert "Successfully" in result

    def test_update_tag_on_hold_status(self):
        """Server updates tag to on_hold status."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_tag.return_value = {
                "success": True,
                "tag_id": "tag-002",
                "updated_fields": ["status"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tag(tag_id="tag-002", status="on_hold")

            mock_client.update_tag.assert_called_once_with(
                tag_id="tag-002", status="on_hold",
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
                "updated_fields": ["name", "status"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tag(tag_id="tag-003", name="New Name", status="active")

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


class TestUpdateTagReparenting:
    """Tests for update_tag() parent_tag parameter (tag reparenting)."""

    def test_server_passes_parent_tag_to_connector(self):
        """Server passes parent_tag parameter to connector."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_tag.return_value = {
                "success": True,
                "tag_id": "tag-001",
                "updated_fields": ["parent_tag"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tag(tag_id="tag-001", parent_tag="People")

            mock_client.update_tag.assert_called_once_with(
                tag_id="tag-001", parent_tag="People"
            )
            assert "Successfully" in result

    def test_connector_move_under_parent(self):
        """Connector builds move command to reparent tag under another tag."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '{"success": true, "updated_fields": ["parent_tag"]}'

            client = OmniFocusConnector()
            result = client.update_tag("tag-child", parent_tag="People")

            assert result["success"] is True
            assert "parent_tag" in result["updated_fields"]
            call_args = mock_run.call_args[0][0]
            assert "move theTag" in call_args
            assert "People" in call_args

    def test_connector_move_to_top_level(self):
        """Connector builds move command to make tag top-level (parent_tag='')."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '{"success": true, "updated_fields": ["parent_tag"]}'

            client = OmniFocusConnector()
            result = client.update_tag("tag-child", parent_tag="")

            assert result["success"] is True
            call_args = mock_run.call_args[0][0]
            assert "move theTag" in call_args
            # Should move to document level, not under a parent
            assert "tags of it" in call_args


class TestGetTagsDroppedStatus:
    """Tests for get_tags() returning dropped status."""

    def test_get_tags_returns_dropped_status(self):
        """get_tags should return status='dropped' for hidden tags."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # Simulate a tag with hidden=true (dropped in OmniFocus UI)
            mock_run.return_value = '[{"id": "tag-001", "name": "Archived", "status": "dropped"}]'

            client = OmniFocusConnector()
            tags = client.get_tags()

            assert len(tags) == 1
            assert tags[0]["status"] == "dropped"

    def test_get_tags_three_states(self):
        """get_tags should distinguish active, on hold, and dropped."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = (
                '[{"id": "tag-1", "name": "Active Tag", "status": "active"}, '
                '{"id": "tag-2", "name": "Paused Tag", "status": "on hold"}, '
                '{"id": "tag-3", "name": "Dropped Tag", "status": "dropped"}]'
            )

            client = OmniFocusConnector()
            tags = client.get_tags()

            statuses = {t["name"]: t["status"] for t in tags}
            assert statuses["Active Tag"] == "active"
            assert statuses["Paused Tag"] == "on hold"
            assert statuses["Dropped Tag"] == "dropped"

    def test_get_tags_applescript_reads_hidden_property(self):
        """get_tags AppleScript should read 'hidden' to determine dropped status."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.side_effect = ['[]', '{}']

            client = OmniFocusConnector()
            client.get_tags()

            call_args = mock_run.call_args_list[0][0][0]
            assert "hidden" in call_args


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

    def test_update_tag_status_calls_applescript(self):
        """Connector builds correct AppleScript for status change."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '{"success": true, "updated_fields": ["status"]}'

            client = OmniFocusConnector()
            result = client.update_tag("tag-002", status="on_hold")

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


class TestUpdateTagStatus:
    """Tests for update_tag() with new status parameter."""

    def test_update_tag_status_dropped(self):
        """Connector sets hidden=true for status='dropped'."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '{"success": true, "updated_fields": ["status"]}'

            client = OmniFocusConnector()
            result = client.update_tag("tag-001", status="dropped")

            assert result["success"] is True
            call_args = mock_run.call_args[0][0]
            assert "hidden of theTag to true" in call_args

    def test_update_tag_status_active(self):
        """Connector sets hidden=false and allows next action=true for status='active'."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '{"success": true, "updated_fields": ["status"]}'

            client = OmniFocusConnector()
            result = client.update_tag("tag-001", status="active")

            assert result["success"] is True
            call_args = mock_run.call_args[0][0]
            assert "hidden of theTag to false" in call_args
            assert "allows next action of theTag to true" in call_args

    def test_update_tag_status_on_hold(self):
        """Connector sets hidden=false and allows next action=false for status='on_hold'."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = '{"success": true, "updated_fields": ["status"]}'

            client = OmniFocusConnector()
            result = client.update_tag("tag-001", status="on_hold")

            assert result["success"] is True
            call_args = mock_run.call_args[0][0]
            assert "hidden of theTag to false" in call_args
            assert "allows next action of theTag to false" in call_args

    def test_update_tag_status_invalid(self):
        """Connector raises ValueError for invalid status."""
        client = OmniFocusConnector()
        with pytest.raises(ValueError, match="Invalid status"):
            client.update_tag("tag-001", status="invalid")

    def test_update_tag_server_status_param(self):
        """Server passes status parameter to connector."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_tag.return_value = {
                "success": True,
                "tag_id": "tag-001",
                "updated_fields": ["status"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tag(tag_id="tag-001", status="dropped")

            mock_client.update_tag.assert_called_once_with(
                tag_id="tag-001", status="dropped",
            )
            assert "Successfully" in result


class TestTagExclusivity:
    """Tests for childrenAreMutuallyExclusive via OmniAutomation."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=False)

    def test_get_tags_includes_exclusivity_field(self, client):
        """get_tags should include childrenAreMutuallyExclusive from OmniAutomation."""
        tags_json = '[{"id": "tag-1", "name": "Priority", "status": "active"}]'
        exclusivity_json = '{"tag-1": true}'

        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # First call: AppleScript get_tags, Second call: OmniAutomation exclusivity
            mock_run.side_effect = [tags_json, exclusivity_json]
            tags = client.get_tags()

        assert len(tags) == 1
        assert tags[0]['childrenAreMutuallyExclusive'] is True

    def test_get_tags_exclusivity_fallback_on_error(self, client):
        """get_tags should default to False when OmniAutomation fails."""
        tags_json = '[{"id": "tag-1", "name": "Work", "status": "active"}]'

        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # First call succeeds, second call (OmniAutomation) fails
            mock_run.side_effect = [tags_json, Exception("evaluate javascript crashed")]
            tags = client.get_tags()

        assert len(tags) == 1
        assert tags[0]['childrenAreMutuallyExclusive'] is False

    def test_update_tag_exclusivity_calls_omniautomation(self, client):
        """update_tag with children_are_mutually_exclusive should call evaluate javascript."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # Only exclusivity — no AppleScript call, just OmniAutomation
            mock_run.return_value = 'ok'
            result = client.update_tag("tag-001", children_are_mutually_exclusive=True)

        assert result["success"] is True
        assert "children_are_mutually_exclusive" in result["updated_fields"]
        assert mock_run.call_count == 1
        js_call = mock_run.call_args[0][0]
        assert "evaluate javascript" in js_call
        assert "childrenAreMutuallyExclusive" in js_call
        assert "true" in js_call

    def test_update_tag_exclusivity_false(self, client):
        """update_tag with children_are_mutually_exclusive=False should set to false."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = 'ok'
            result = client.update_tag("tag-001", children_are_mutually_exclusive=False)

        assert result["success"] is True
        js_call = mock_run.call_args[0][0]
        assert "false" in js_call

    def test_create_tag_exclusivity_calls_omniautomation(self, client):
        """create_tag with children_are_mutually_exclusive=True should call OmniAutomation."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            # First call: AppleScript create tag, Second call: OmniAutomation
            mock_run.side_effect = ['tag-new-123', 'ok']
            result = client.create_tag("Exclusive Group", children_are_mutually_exclusive=True)

        assert result == 'tag-new-123'
        assert mock_run.call_count == 2
        js_call = mock_run.call_args_list[1][0][0]
        assert "evaluate javascript" in js_call
        assert "childrenAreMutuallyExclusive" in js_call

    def test_create_tag_no_exclusivity_no_omniautomation(self, client):
        """create_tag without exclusivity should not call OmniAutomation."""
        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = 'tag-new-456'
            result = client.create_tag("Regular Tag")

        assert result == 'tag-new-456'
        assert mock_run.call_count == 1  # Only AppleScript, no OmniAutomation


class TestUpdateTagsUnified:
    """Tests for unified update_tags() with Pydantic model input."""

    def test_update_tags_single_item(self):
        """Single tag update returns detailed format."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_tag.return_value = {
                "success": True,
                "tag_id": "tag-001",
                "updated_fields": ["name"],
                "error": None,
            }
            mock_get_client.return_value = mock_client

            update_tags = server.update_tags
            result = update_tags(tags=[{"id": "tag-001", "name": "Renamed"}])

            assert "Successfully updated tag tag-001" in result
            assert "name" in result
            mock_client.update_tag.assert_called_once()

    def test_update_tags_batch_different_fields(self):
        """Multiple tags with different fields per item."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_tag.side_effect = [
                {"success": True, "tag_id": "tag-001", "updated_fields": ["name"], "error": None},
                {"success": True, "tag_id": "tag-002", "updated_fields": ["status"], "error": None},
            ]
            mock_get_client.return_value = mock_client

            update_tags = server.update_tags
            result = update_tags(tags=[
                {"id": "tag-001", "name": "Renamed"},
                {"id": "tag-002", "status": "on_hold"},
            ])

            assert "Updated 2 of 2 tags" in result
            assert mock_client.update_tag.call_count == 2

    def test_update_tags_partial_failure(self):
        """One failure in batch returns mixed results."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_tag.side_effect = [
                {"success": True, "tag_id": "tag-001", "updated_fields": ["name"], "error": None},
                ValueError("Tag not found"),
            ]
            mock_get_client.return_value = mock_client

            update_tags = server.update_tags
            result = update_tags(tags=[
                {"id": "tag-001", "name": "Good"},
                {"id": "tag-bad", "name": "Bad"},
            ])

            assert "Updated 1 of 2 tags" in result
            assert "FAILED" in result

    def test_update_tags_excludes_none_fields(self):
        """Only set fields are passed to connector."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_tag.return_value = {
                "success": True, "tag_id": "tag-001",
                "updated_fields": ["status"], "error": None,
            }
            mock_get_client.return_value = mock_client

            update_tags = server.update_tags
            result = update_tags(tags=[{"id": "tag-001", "status": "on_hold"}])

            call_kwargs = mock_client.update_tag.call_args[1]
            assert call_kwargs["tag_id"] == "tag-001"
            assert call_kwargs["status"] == "on_hold"
            assert "name" not in call_kwargs

    def test_update_tag_delegates_to_update_tags(self):
        """Old update_tag should delegate to update_tags."""
        with mock.patch('omnifocus_mcp.server_fastmcp.get_client') as mock_get_client:
            mock_client = mock.Mock()
            mock_client.update_tag.return_value = {
                "success": True, "tag_id": "tag-001",
                "updated_fields": ["name"], "error": None,
            }
            mock_get_client.return_value = mock_client

            result = update_tag(tag_id="tag-001", name="Renamed")

            assert "Successfully updated tag tag-001" in result
            mock_client.update_tag.assert_called_once()
