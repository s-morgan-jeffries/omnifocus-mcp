"""Tests for git hooks.

These tests verify the git hook logic without requiring actual git operations.
"""

import subprocess
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
GIT_HOOKS_DIR = PROJECT_ROOT / "scripts" / "git-hooks"


class TestPreCommitHook:
    """Tests for pre-commit git hook."""

    def test_hook_exists(self):
        """Pre-commit hook script should exist."""
        hook_path = GIT_HOOKS_DIR / "pre-commit"
        assert hook_path.exists(), "pre-commit hook should exist"

    def test_hook_executable(self):
        """Pre-commit hook should be executable."""
        hook_path = GIT_HOOKS_DIR / "pre-commit"
        assert hook_path.stat().st_mode & 0o111, "pre-commit hook should be executable"

    def test_allows_commits_on_feature_branch(self, tmp_path):
        """Commits should be allowed on non-main branches."""
        # Create a temporary git repo on a feature branch
        repo = tmp_path / "test_repo"
        repo.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "-b", "feature/test"], cwd=repo, check=True, capture_output=True)

        # Create a test file and stage it
        (repo / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)

        # Run pre-commit hook
        result = subprocess.run(
            [str(GIT_HOOKS_DIR / "pre-commit")],
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

        # Try to make another commit
        (repo / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)

        # Run pre-commit hook
        result = subprocess.run(
            [str(GIT_HOOKS_DIR / "pre-commit")],
            capture_output=True,
            cwd=repo,
        )

        assert result.returncode == 1, "Commits should be blocked on main branch"
        output = result.stderr + result.stdout
        assert b"Direct commits to" in output and (b"main" in output or b"master" in output)

    def test_blocks_commits_on_master_branch(self, tmp_path):
        """Commits should be blocked on master branch (except hotfixes)."""
        # Create a temporary git repo on master
        repo = tmp_path / "test_repo"
        repo.mkdir()

        # Initialize git repo with master as default branch
        subprocess.run(["git", "init", "-b", "master"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        # Create initial commit
        (repo / "README.md").write_text("test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

        # Try to make another commit
        (repo / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)

        # Run pre-commit hook
        result = subprocess.run(
            [str(GIT_HOOKS_DIR / "pre-commit")],
            capture_output=True,
            cwd=repo,
        )

        assert result.returncode == 1, "Commits should be blocked on master branch"

    def test_allows_hotfix_commits_on_main(self, tmp_path):
        """Hotfix commits should be allowed on main branch."""
        # Create a temporary git repo on main
        repo = tmp_path / "test_repo"
        repo.mkdir()

        # Initialize git repo on main
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        # Create initial commit with hotfix message
        (repo / "README.md").write_text("test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "hotfix: initial setup"], cwd=repo, check=True, capture_output=True)

        # Stage a change for another hotfix commit
        (repo / "test.txt").write_text("hotfix")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)

        # Write commit message to COMMIT_EDITMSG (simulates git commit -m)
        commit_msg_file = repo / ".git" / "COMMIT_EDITMSG"
        commit_msg_file.write_text("hotfix: critical bug fix")

        # Run pre-commit hook
        result = subprocess.run(
            [str(GIT_HOOKS_DIR / "pre-commit")],
            capture_output=True,
            cwd=repo,
        )

        assert result.returncode == 0, f"Hotfix commits should be allowed on main. stderr: {result.stderr.decode()}"

    def test_allows_emergency_commits_on_main(self, tmp_path):
        """Emergency commits should be allowed on main branch."""
        # Create a temporary git repo on main
        repo = tmp_path / "test_repo"
        repo.mkdir()

        # Initialize git repo on main
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        # Create initial commit with emergency message
        (repo / "README.md").write_text("test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "emergency: initial setup"], cwd=repo, check=True, capture_output=True)

        # Stage a change for another emergency commit
        (repo / "test.txt").write_text("emergency")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)

        # Write commit message to COMMIT_EDITMSG (simulates git commit -m)
        commit_msg_file = repo / ".git" / "COMMIT_EDITMSG"
        commit_msg_file.write_text("emergency: production down")

        # Run pre-commit hook
        result = subprocess.run(
            [str(GIT_HOOKS_DIR / "pre-commit")],
            capture_output=True,
            cwd=repo,
        )

        assert result.returncode == 0, f"Emergency commits should be allowed on main. stderr: {result.stderr.decode()}"

    def test_allows_commits_on_release_branch(self, tmp_path):
        """Commits should be allowed on release branches."""
        # Create a temporary git repo on release branch
        repo = tmp_path / "test_repo"
        repo.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True, capture_output=True)

        # Create initial commit
        (repo / "README.md").write_text("test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)

        # Create release branch
        subprocess.run(["git", "checkout", "-b", "release/v0.7.0"], cwd=repo, check=True, capture_output=True)

        # Try to make a commit
        (repo / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)

        # Run pre-commit hook
        result = subprocess.run(
            [str(GIT_HOOKS_DIR / "pre-commit")],
            capture_output=True,
            cwd=repo,
        )

        assert result.returncode == 0, f"Commits should be allowed on release branches. stderr: {result.stderr.decode()}"
