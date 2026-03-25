"""Tests for Unicode/emoji handling across all layers.

Verifies that non-ASCII characters survive escaping, AppleScript generation,
and round-trip through real OmniFocus.
"""
import os
import re

import pytest

from omnifocus_mcp.omnifocus_connector import OmniFocusConnector
import omnifocus_mcp.server_fastmcp as server

# ============================================================================
# Unit tests: escaper functions
# ============================================================================

UNICODE_SAMPLES = [
    ("accented", "Café résumé naïve"),
    ("emoji", "Review docs 📋🎯"),
    ("cjk", "日本語テスト"),
    ("cyrillic", "Проверка задач"),
    ("mixed", "Meeting with José 🤝 about naïve Bayes"),
    ("special_symbols", "Budget: £500 → €450 ≈ ¥70000"),
    ("quotes_and_unicode", 'Say "hello" to Aimée'),
]


class TestEscapeAppleScriptUnicode:
    """Verify _escape_applescript_string preserves Unicode."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector()

    @pytest.mark.parametrize("name,text", UNICODE_SAMPLES)
    def test_unicode_preserved(self, client, name, text):
        """Unicode characters survive AppleScript escaping unchanged."""
        escaped = client._escape_applescript_string(text)
        # Unicode chars should pass through — only quotes/backslashes are escaped
        for char in text:
            if char not in ('"', '\\'):
                assert char in escaped, f"Unicode char {repr(char)} lost in escaping"

    def test_accented_chars_unchanged(self, client):
        """Accented Latin characters pass through AppleScript escaping unchanged."""
        result = client._escape_applescript_string("Café résumé")
        assert result == "Café résumé"

    def test_emoji_unchanged(self, client):
        """Emoji characters pass through AppleScript escaping unchanged."""
        result = client._escape_applescript_string("Task 🎯")
        assert result == "Task 🎯"

    def test_quotes_in_unicode_escaped(self, client):
        """Double quotes are escaped while surrounding Unicode is preserved."""
        result = client._escape_applescript_string('Say "bonjour" à Aimée')
        assert '\\"' in result
        assert "Aimée" in result


class TestEscapeJsStringUnicode:
    """Verify _escape_js_string preserves Unicode."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector()

    @pytest.mark.parametrize("name,text", UNICODE_SAMPLES)
    def test_unicode_preserved(self, client, name, text):
        """Unicode characters survive JS string escaping unchanged."""
        escaped = client._escape_js_string(text)
        for char in text:
            if char not in ("'", '"', '\\'):
                assert char in escaped, f"Unicode char {repr(char)} lost in JS escaping"


# ============================================================================
# Unit tests: generated AppleScript contains Unicode
# ============================================================================


class TestAppleScriptGenerationUnicode:
    """Verify Unicode survives into generated AppleScript strings."""

    def test_create_task_unicode_in_script(self):
        """create_task with Unicode name produces AppleScript containing that name."""
        from unittest import mock

        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "task-123"
            client = OmniFocusConnector()
            client.create_task(task_name="Café meeting 🎯")

            call_args = mock_run.call_args[0][0]
            assert "Café meeting 🎯" in call_args

    def test_create_task_unicode_note_in_script(self):
        """create_task with Unicode note produces AppleScript containing that note."""
        from unittest import mock

        with mock.patch('omnifocus_mcp.omnifocus_connector.run_applescript') as mock_run:
            mock_run.return_value = "task-123"
            client = OmniFocusConnector()
            client.create_task(task_name="Test", note="Notes: résumé → review")

            call_args = mock_run.call_args[0][0]
            assert "résumé → review" in call_args


# ============================================================================
# Integration tests: round-trip through real OmniFocus
# ============================================================================

pytestmark_integration = pytest.mark.skipif(
    os.environ.get('OMNIFOCUS_TEST_MODE', '').lower() != 'true',
    reason="Integration tests require OMNIFOCUS_TEST_MODE=true"
)


@pytestmark_integration
class TestUnicodeIntegration:
    """Round-trip Unicode through real OmniFocus."""

    @pytest.fixture
    def client(self):
        return OmniFocusConnector(enable_safety_checks=True)

    def test_task_unicode_roundtrip(self, client):
        """Create task with Unicode name and note, read back, verify."""
        task_name = "Café meeting 🎯 with José"
        task_note = "Discuss résumé → budget ≈ £500"
        task_id = client.create_task(task_name=task_name, note=task_note)
        try:
            tasks = client.get_tasks(query="Café meeting")
            matching = [t for t in tasks if t["id"] == task_id]
            assert len(matching) == 1
            assert matching[0]["name"] == task_name
            assert task_note in matching[0].get("note", "")
        finally:
            client.delete_tasks(task_id)

    def test_project_unicode_roundtrip(self, client):
        """Create project with Unicode name, read back, verify."""
        proj_name = "Проект тестирования 📋"
        proj_id = client.create_project(name=proj_name)
        try:
            projects = client.get_projects()
            matching = [p for p in projects if p["id"] == proj_id]
            assert len(matching) == 1
            assert matching[0]["name"] == proj_name
        finally:
            client.delete_projects(proj_id)

    def test_tag_unicode_roundtrip(self, client):
        """Create tag with Unicode name, read back, verify."""
        tag_name = "Énergie élevée ⚡"
        tag_id = client.create_tag(name=tag_name)
        try:
            tags = client.get_tags()
            matching = [t for t in tags if t["id"] == tag_id]
            assert len(matching) == 1
            assert matching[0]["name"] == tag_name
        finally:
            client.delete_tags(tag_id)

    def test_mcp_server_unicode_roundtrip(self, client):
        """Full MCP stack: create task with Unicode via server tool, verify."""
        result = server.create_task(task_name="E2E Unicode 日本語 🎯")
        assert isinstance(result, str)
        assert "Successfully created" in result
        assert "E2E Unicode" in result

        # Extract task ID and clean up
        match = re.search(r'Task ID: (\S+)', result)
        if match:
            client.delete_tasks(match.group(1))
