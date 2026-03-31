"""Tests for AppleScript error message sanitization."""
import pytest

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


class TestSanitizeError:
    """Test _sanitize_error strips sensitive info while keeping useful messages."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return OmniFocusConnector(enable_safety_checks=False)

    def test_strips_user_home_paths(self, client):
        """File paths under /Users/ are replaced."""
        raw = "Can't open file /Users/morgan/Library/Containers/com.omnigroup.OmniFocus4/OmniFocus.ofocus"
        result = client._sanitize_error(raw)
        assert "/Users/" not in result
        assert "Can't open file" in result

    def test_strips_library_paths(self, client):
        """Library paths are replaced."""
        raw = "Error at /Library/Scripts/OmniFocus/helper.scpt"
        result = client._sanitize_error(raw)
        assert "/Library/" not in result

    def test_strips_ofocus_database_names(self, client):
        """Database filenames are replaced."""
        raw = "Can't access document OmniFocus-TEST.ofocus"
        result = client._sanitize_error(raw)
        assert ".ofocus" not in result

    def test_strips_applescript_class_references(self, client):
        """AppleScript class notation is stripped."""
        raw = "Can't make «class isot» into type string"
        result = client._sanitize_error(raw)
        assert "«class" not in result

    def test_preserves_useful_error_text(self, client):
        """Core error messages are kept."""
        raw = "Can't get task id \"abc-123\" of document 1"
        result = client._sanitize_error(raw)
        assert "Can't get task" in result

    def test_truncates_long_messages(self, client):
        """Messages over 500 chars are truncated."""
        raw = "Error: " + "x" * 600
        result = client._sanitize_error(raw)
        assert len(result) <= 503  # 500 + "..."

    def test_handles_empty_string(self, client):
        """Empty stderr returns empty string."""
        assert client._sanitize_error("") == ""

    def test_handles_none(self, client):
        """None stderr returns empty string."""
        assert client._sanitize_error(None) == ""

    def test_clean_message_unchanged(self, client):
        """Messages without sensitive info pass through."""
        raw = "Can't get project: no matching project found"
        result = client._sanitize_error(raw)
        assert result == raw
