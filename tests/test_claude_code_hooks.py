"""Tests for Claude Code hooks.

These tests verify the hook logic without requiring actual git operations.
"""

import json
import subprocess
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
HOOKS_DIR = PROJECT_ROOT / "scripts" / "hooks"


class TestPreBashHook:
    """Tests for pre_bash.sh hook."""

    def test_allows_non_commit_commands(self, monkeypatch):
        """Non-commit commands should always be allowed."""
        # Mock git to return a feature branch
        monkeypatch.setattr(
            "subprocess.run",
            lambda *args, **kwargs: subprocess.CompletedProcess(
                args=args, returncode=0, stdout=b"feature/test-branch"
            )
            if "rev-parse" in str(args)
            else subprocess.CompletedProcess(args=args, returncode=0),
        )

        hook_input = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"}
        })

        result = subprocess.run(
            [str(HOOKS_DIR / "pre_bash.sh")],
            input=hook_input.encode(),
            capture_output=True,
        )

        assert result.returncode == 0, f"Non-commit command should be allowed. stderr: {result.stderr.decode()}"

    def test_allows_commits_on_feature_branch(self, tmp_path, monkeypatch):
        """Commits should be allowed on non-main branches."""
        # Create a temporary git repo on a feature branch
        repo = tmp_path / "test_repo"
        repo.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "-b", "feature/test"], cwd=repo, check=True, capture_output=True)

        hook_input = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": 'git commit -m "test"'}
        })

        result = subprocess.run(
            [str(HOOKS_DIR / "pre_bash.sh")],
            input=hook_input.encode(),
            capture_output=True,
            cwd=repo,
        )

        assert result.returncode == 0, f"Commits should be allowed on feature branches. stderr: {result.stderr.decode()}"

    def test_blocks_commits_on_main_branch(self, tmp_path):
        """Commits should be blocked on main branch (except hotfixes)."""
        # Create a temporary git repo on main
        repo = tmp_path / "test_repo"
        repo.mkdir()

        # Initialize git repo on main
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        # Create initial commit so we're on main
        (repo / "README.md").write_text("test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

        hook_input = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": 'git commit -m "regular commit"'}
        })

        result = subprocess.run(
            [str(HOOKS_DIR / "pre_bash.sh")],
            input=hook_input.encode(),
            capture_output=True,
            cwd=repo,
        )

        assert result.returncode == 2, "Commits should be blocked on main branch"
        assert b"Cannot commit directly to main" in result.stderr

    def test_allows_hotfix_commits_on_main(self, tmp_path):
        """Hotfix commits should be allowed on main branch."""
        # Create a temporary git repo on main
        repo = tmp_path / "test_repo"
        repo.mkdir()

        # Initialize git repo on main
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        # Create initial commit
        (repo / "README.md").write_text("test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

        hook_input = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": 'git commit -m "hotfix: critical bug"'}
        })

        result = subprocess.run(
            [str(HOOKS_DIR / "pre_bash.sh")],
            input=hook_input.encode(),
            capture_output=True,
            cwd=repo,
        )

        assert result.returncode == 0, f"Hotfix commits should be allowed on main. stderr: {result.stderr.decode()}"


class TestPostBashHook:
    """Tests for post_bash.sh hook."""

    def test_allows_non_push_commands(self):
        """Non-push commands should always be allowed."""
        hook_input = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": "git status"},
            "tool_response": {"exit_code": 0}
        })

        result = subprocess.run(
            [str(HOOKS_DIR / "post_bash.sh")],
            input=hook_input.encode(),
            capture_output=True,
        )

        assert result.returncode == 0, "Non-push commands should be allowed"

    def test_ignores_failed_pushes(self):
        """Failed git pushes should not trigger monitoring."""
        hook_input = json.dumps({
            "tool_name": "Bash",
            "tool_input": {"command": "git push origin test"},
            "tool_response": {"exit_code": 1}  # Failed push
        })

        result = subprocess.run(
            [str(HOOKS_DIR / "post_bash.sh")],
            input=hook_input.encode(),
            capture_output=True,
        )

        assert result.returncode == 0, "Failed pushes should not trigger monitoring"


class TestSessionStartHook:
    """Tests for session_start.sh hook."""

    def test_returns_valid_json(self, tmp_path):
        """session_start.sh should return valid JSON."""
        # Create a temporary git repo for testing
        repo = tmp_path / "test_repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        hook_input = json.dumps({
            "hook_event_name": "SessionStart",
            "source": "startup",
            "cwd": str(repo)
        })

        result = subprocess.run(
            [str(HOOKS_DIR / "session_start.sh")],
            input=hook_input.encode(),
            capture_output=True,
            cwd=repo,
        )

        assert result.returncode == 0, f"session_start.sh should succeed. stderr: {result.stderr.decode()}"

        # Parse JSON output
        try:
            output = json.loads(result.stdout.decode())
            assert "additionalContext" in output, "Output should have additionalContext field"
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}\nOutput: {result.stdout.decode()}")

    def test_includes_branch_info(self, tmp_path):
        """session_start.sh should include current branch information."""
        # Create a temporary git repo on a feature branch
        repo = tmp_path / "test_repo"
        repo.mkdir()
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        # Create an initial commit so we have a proper branch
        (repo / "README.md").write_text("test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "-b", "feature/test-branch"], cwd=repo, check=True, capture_output=True)

        hook_input = json.dumps({
            "hook_event_name": "SessionStart",
            "source": "startup",
            "cwd": str(repo)
        })

        result = subprocess.run(
            [str(HOOKS_DIR / "session_start.sh")],
            input=hook_input.encode(),
            capture_output=True,
            cwd=repo,
        )

        output = json.loads(result.stdout.decode())
        context = output["additionalContext"]

        assert "feature/test-branch" in context, "Output should include current branch name"


class TestHookConfiguration:
    """Tests for hook configuration and setup."""

    def test_all_hooks_executable(self):
        """All hook scripts should be executable."""
        hooks = list(HOOKS_DIR.glob("*.sh"))
        assert len(hooks) > 0, "Should have at least one hook script"

        for hook in hooks:
            assert hook.stat().st_mode & 0o111, f"Hook should be executable: {hook.name}"

    def test_settings_json_valid(self):
        """settings.json should be valid JSON with hooks config."""
        settings_file = PROJECT_ROOT / ".claude" / "settings.json"
        assert settings_file.exists(), "settings.json should exist"

        with open(settings_file) as f:
            settings = json.load(f)

        assert "hooks" in settings, "settings.json should have hooks configuration"

    def test_all_configured_hooks_exist(self):
        """All hooks referenced in settings.json should exist."""
        settings_file = PROJECT_ROOT / ".claude" / "settings.json"

        with open(settings_file) as f:
            settings = json.load(f)

        hooks_config = settings.get("hooks", {})

        # Check all hook types
        for hook_type in ["PreToolUse", "PostToolUse", "SessionStart"]:
            if hook_type not in hooks_config:
                continue

            for matcher_config in hooks_config[hook_type]:
                if "hooks" not in matcher_config:
                    continue

                for hook in matcher_config["hooks"]:
                    if "command" not in hook:
                        continue

                    hook_path = PROJECT_ROOT / hook["command"]
                    assert hook_path.exists(), f"Hook referenced in settings.json doesn't exist: {hook['command']}"
