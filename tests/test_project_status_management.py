"""Tests for project status management."""

import json
import pytest
from unittest.mock import patch, MagicMock
from omnifocus_mcp.omnifocus_client import OmniFocusClient


@pytest.fixture
def client():
    """Create an OmniFocusClient instance."""
    return OmniFocusClient(enable_safety_checks=False)


class TestSetProjectStatus:
    """Test setting project status to different values."""

    def test_set_status_to_active(self, client):
        """Should set project status to active."""
        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.set_project_status("proj-123", "active")

        assert result is True
        # Verify AppleScript uses "set status" for active
        call_args = mock_run.call_args[0][0]
        assert 'set status of targetProject to active' in call_args
        assert 'mark complete' not in call_args

    def test_set_status_to_on_hold(self, client):
        """Should set project status to on hold."""
        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.set_project_status("proj-123", "on_hold")

        assert result is True
        # Verify AppleScript uses "set status" for on hold
        call_args = mock_run.call_args[0][0]
        assert 'set status of targetProject to on hold' in call_args
        assert 'mark complete' not in call_args

    def test_set_status_to_done(self, client):
        """Should mark project complete when setting status to done."""
        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"
            result = client.set_project_status("proj-123", "done")

        assert result is True
        # Verify AppleScript uses "mark complete" for done
        call_args = mock_run.call_args[0][0]
        assert 'mark complete targetProject' in call_args
        assert 'set status' not in call_args

    def test_set_status_to_dropped(self, client):
        """Test setting project status to dropped."""
        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "true"

            result = client.set_project_status("proj-123", "dropped")

            assert result is True
            # Verify it called AppleScript with "mark dropped"
            call_args = mock_run.call_args[0][0]
            assert "mark dropped" in call_args.lower()
            assert "proj-123" in call_args

    def test_set_status_invalid_status(self, client):
        """Should raise ValueError for invalid status values."""
        with pytest.raises(ValueError, match="Invalid status"):
            client.set_project_status("proj-123", "invalid_status")

    def test_set_status_project_not_found(self, client):
        """Should raise ValueError when project not found."""
        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.return_value = "false"

            with pytest.raises(ValueError, match="Project.*not found"):
                client.set_project_status("nonexistent", "active")

    def test_set_status_handles_applescript_error(self, client):
        """Should raise RuntimeError when AppleScript fails."""
        with patch('omnifocus_mcp.omnifocus_client.run_applescript') as mock_run:
            mock_run.side_effect = RuntimeError("AppleScript execution failed")

            with pytest.raises(RuntimeError, match="AppleScript execution failed"):
                client.set_project_status("proj-123", "active")
