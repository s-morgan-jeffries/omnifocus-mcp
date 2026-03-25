"""Tests for _escape_js_string — JavaScript escaping for OmniAutomation.

The escaper handles the double-context problem: JS single-quoted strings
embedded inside AppleScript double-quoted strings via `evaluate javascript "..."`.

See #318.
"""
import pytest
from omnifocus_mcp.omnifocus_connector import OmniFocusConnector


@pytest.fixture
def client():
    return OmniFocusConnector()


class TestEscapeJsString:

    def test_plain_string_unchanged(self, client):
        """Plain ASCII string passes through without modification."""
        assert client._escape_js_string("hello") == "hello"

    def test_empty_string(self, client):
        """Empty string passes through without modification."""
        assert client._escape_js_string("") == ""

    def test_single_quote_escaped(self, client):
        """Single quotes are backslash-escaped for JS string context."""
        assert client._escape_js_string("it's") == "it\\'s"

    def test_backslash_escaped(self, client):
        """Backslashes are doubled to prevent escape sequence injection."""
        assert client._escape_js_string("a\\b") == "a\\\\b"

    def test_double_quote_escaped_for_applescript(self, client):
        """Double quotes must be escaped because the JS lives inside AppleScript \"...\"."""
        assert client._escape_js_string('say "hi"') == 'say \\"hi\\"'

    def test_newline_escaped(self, client):
        """Newlines are replaced with literal \\n for JS string context."""
        assert client._escape_js_string("line1\nline2") == "line1\\nline2"

    def test_carriage_return_escaped(self, client):
        """Carriage returns are replaced with literal \\r for JS string context."""
        assert client._escape_js_string("a\rb") == "a\\rb"

    def test_tab_escaped(self, client):
        """Tabs are replaced with literal \\t for JS string context."""
        assert client._escape_js_string("a\tb") == "a\\tb"

    def test_combined_special_chars(self, client):
        """Multiple special characters are all escaped independently."""
        result = client._escape_js_string("it's a \"test\"\nwith\\stuff")
        assert "\\'" in result      # single quote
        assert '\\"' in result      # double quote
        assert "\\n" in result      # newline
        assert "\\\\" in result     # backslash

    def test_rrule_string_safe(self, client):
        """Typical RRULE strings should pass through safely."""
        rrule = "FREQ=WEEKLY;INTERVAL=2;BYDAY=MO,WE,FR"
        assert client._escape_js_string(rrule) == rrule

    def test_backslash_before_quote(self, client):
        """Backslash before quote: both must be escaped independently."""
        result = client._escape_js_string("\\'")
        assert result == "\\\\\\'"
