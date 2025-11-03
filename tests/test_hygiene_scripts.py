"""Smoke tests for hygiene check scripts.

These tests verify that hygiene check scripts run without crashing.
They do NOT test detailed logic correctness - only basic execution.
"""

import subprocess
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


class TestComplexityCheck:
    """Smoke tests for check_complexity.sh."""

    def test_script_exists(self):
        """Script should exist."""
        script_path = SCRIPTS_DIR / "check_complexity.sh"
        assert script_path.exists(), "check_complexity.sh should exist"

    def test_script_executable(self):
        """Script should be executable."""
        script_path = SCRIPTS_DIR / "check_complexity.sh"
        assert script_path.stat().st_mode & 0o111, "check_complexity.sh should be executable"

    def test_runs_without_crashing(self):
        """Script should run without crashing (exit 0 or 1)."""
        result = subprocess.run(
            [str(SCRIPTS_DIR / "check_complexity.sh")],
            capture_output=True,
            cwd=PROJECT_ROOT,
        )
        # Exit 0 = all good, exit 1 = complexity issues found
        # Both are acceptable - script should not crash
        assert result.returncode in [0, 1], (
            f"Script should exit with 0 or 1, got {result.returncode}. "
            f"stderr: {result.stderr.decode()}"
        )


class TestTestCoverageCheck:
    """Smoke tests for check_test_coverage.sh."""

    def test_script_exists(self):
        """Script should exist."""
        script_path = SCRIPTS_DIR / "check_test_coverage.sh"
        assert script_path.exists(), "check_test_coverage.sh should exist"

    def test_script_executable(self):
        """Script should be executable."""
        script_path = SCRIPTS_DIR / "check_test_coverage.sh"
        assert script_path.stat().st_mode & 0o111, "check_test_coverage.sh should be executable"

    def test_runs_without_crashing(self):
        """Script should run without crashing (exit 0 or 1)."""
        result = subprocess.run(
            [str(SCRIPTS_DIR / "check_test_coverage.sh")],
            capture_output=True,
            cwd=PROJECT_ROOT,
        )
        # Exit 0 = coverage OK, exit 1 = coverage below threshold
        assert result.returncode in [0, 1], (
            f"Script should exit with 0 or 1, got {result.returncode}. "
            f"stderr: {result.stderr.decode()}"
        )


class TestCodeQualityCheck:
    """Smoke tests for check_code_quality.sh."""

    def test_script_exists(self):
        """Script should exist."""
        script_path = SCRIPTS_DIR / "check_code_quality.sh"
        assert script_path.exists(), "check_code_quality.sh should exist"

    def test_script_executable(self):
        """Script should be executable."""
        script_path = SCRIPTS_DIR / "check_code_quality.sh"
        assert script_path.stat().st_mode & 0o111, "check_code_quality.sh should be executable"

    def test_runs_without_crashing(self):
        """Script should run without crashing (exit 0 or 1)."""
        result = subprocess.run(
            [str(SCRIPTS_DIR / "check_code_quality.sh")],
            capture_output=True,
            cwd=PROJECT_ROOT,
        )
        # Exit 0 = no quality issues, exit 1 = quality issues found
        assert result.returncode in [0, 1], (
            f"Script should exit with 0 or 1, got {result.returncode}. "
            f"stderr: {result.stderr.decode()}"
        )


class TestDirectoryOrganizationCheck:
    """Smoke tests for check_directory_organization.sh."""

    def test_script_exists(self):
        """Script should exist."""
        script_path = SCRIPTS_DIR / "check_directory_organization.sh"
        assert script_path.exists(), "check_directory_organization.sh should exist"

    def test_script_executable(self):
        """Script should be executable."""
        script_path = SCRIPTS_DIR / "check_directory_organization.sh"
        assert script_path.stat().st_mode & 0o111, "check_directory_organization.sh should be executable"

    def test_runs_without_crashing(self):
        """Script should run without crashing (exit 0 or 1)."""
        result = subprocess.run(
            [str(SCRIPTS_DIR / "check_directory_organization.sh")],
            capture_output=True,
            cwd=PROJECT_ROOT,
        )
        # Exit 0 = organization OK, exit 1 = issues found
        assert result.returncode in [0, 1], (
            f"Script should exit with 0 or 1, got {result.returncode}. "
            f"stderr: {result.stderr.decode()}"
        )


class TestApproveHygieneChecks:
    """Smoke tests for approve_hygiene_checks.sh."""

    def test_script_exists(self):
        """Script should exist."""
        script_path = SCRIPTS_DIR / "approve_hygiene_checks.sh"
        assert script_path.exists(), "approve_hygiene_checks.sh should exist"

    def test_script_executable(self):
        """Script should be executable."""
        script_path = SCRIPTS_DIR / "approve_hygiene_checks.sh"
        assert script_path.stat().st_mode & 0o111, "approve_hygiene_checks.sh should be executable"

    def test_requires_tag_argument(self):
        """Script should error when no tag provided."""
        result = subprocess.run(
            [str(SCRIPTS_DIR / "approve_hygiene_checks.sh")],
            capture_output=True,
            cwd=PROJECT_ROOT,
        )
        # Should exit with error
        assert result.returncode != 0, "Script should error when no tag provided"
        # Should mention tag requirement
        output = result.stderr.decode() + result.stdout.decode()
        assert "tag" in output.lower(), "Error message should mention tag requirement"

    def test_accepts_tag_argument(self):
        """Script should accept tag argument without crashing."""
        # Use a fake tag name - script should accept it
        # (May create approval file which we'll clean up)
        result = subprocess.run(
            [str(SCRIPTS_DIR / "approve_hygiene_checks.sh"), "v0.0.0-test"],
            capture_output=True,
            cwd=PROJECT_ROOT,
        )
        # Clean up any approval file created
        approval_file = PROJECT_ROOT / ".hygiene-approved-v0.0.0-test"
        if approval_file.exists():
            approval_file.unlink()

        # Script should run without crashing
        # Exit code may be 0 (created file) or 1 (file existed)
        assert result.returncode in [0, 1], (
            f"Script should not crash with valid tag. "
            f"stderr: {result.stderr.decode()}"
        )


class TestVersionSyncCheck:
    """Smoke tests for check_version_sync.sh."""

    def test_script_exists(self):
        """Script should exist."""
        script_path = SCRIPTS_DIR / "check_version_sync.sh"
        assert script_path.exists(), "check_version_sync.sh should exist"

    def test_script_executable(self):
        """Script should be executable."""
        script_path = SCRIPTS_DIR / "check_version_sync.sh"
        assert script_path.stat().st_mode & 0o111, "check_version_sync.sh should be executable"

    def test_runs_without_crashing(self):
        """Script should run without crashing (exit 0 or 1)."""
        result = subprocess.run(
            [str(SCRIPTS_DIR / "check_version_sync.sh")],
            capture_output=True,
            cwd=PROJECT_ROOT,
        )
        # Exit 0 = versions synced, exit 1 = sync issues
        assert result.returncode in [0, 1], (
            f"Script should exit with 0 or 1, got {result.returncode}. "
            f"stderr: {result.stderr.decode()}"
        )


class TestTestCountSyncCheck:
    """Smoke tests for check_test_count_sync.sh."""

    def test_script_exists(self):
        """Script should exist."""
        script_path = SCRIPTS_DIR / "check_test_count_sync.sh"
        assert script_path.exists(), "check_test_count_sync.sh should exist"

    def test_script_executable(self):
        """Script should be executable."""
        script_path = SCRIPTS_DIR / "check_test_count_sync.sh"
        assert script_path.stat().st_mode & 0o111, "check_test_count_sync.sh should be executable"

    def test_runs_without_crashing(self):
        """Script should run without crashing (exit 0 or 1)."""
        result = subprocess.run(
            [str(SCRIPTS_DIR / "check_test_count_sync.sh")],
            capture_output=True,
            cwd=PROJECT_ROOT,
        )
        # Exit 0 = count synced, exit 1 = sync issues
        assert result.returncode in [0, 1], (
            f"Script should exit with 0 or 1, got {result.returncode}. "
            f"stderr: {result.stderr.decode()}"
        )


class TestRoadmapSyncCheck:
    """Smoke tests for check_roadmap_sync.sh."""

    def test_script_exists(self):
        """Script should exist."""
        script_path = SCRIPTS_DIR / "check_roadmap_sync.sh"
        assert script_path.exists(), "check_roadmap_sync.sh should exist"

    def test_script_executable(self):
        """Script should be executable."""
        script_path = SCRIPTS_DIR / "check_roadmap_sync.sh"
        assert script_path.stat().st_mode & 0o111, "check_roadmap_sync.sh should be executable"

    def test_runs_without_crashing(self):
        """Script should run without crashing (exit 0 or 1)."""
        result = subprocess.run(
            [str(SCRIPTS_DIR / "check_roadmap_sync.sh")],
            capture_output=True,
            cwd=PROJECT_ROOT,
        )
        # Exit 0 = roadmap synced, exit 1 = sync issues
        assert result.returncode in [0, 1], (
            f"Script should exit with 0 or 1, got {result.returncode}. "
            f"stderr: {result.stderr.decode()}"
        )


class TestDocumentationCheck:
    """Smoke tests for check_documentation.sh."""

    def test_script_exists(self):
        """Script should exist."""
        script_path = SCRIPTS_DIR / "check_documentation.sh"
        assert script_path.exists(), "check_documentation.sh should exist"

    def test_script_executable(self):
        """Script should be executable."""
        script_path = SCRIPTS_DIR / "check_documentation.sh"
        assert script_path.stat().st_mode & 0o111, "check_documentation.sh should be executable"

    def test_runs_without_crashing(self):
        """Script should run without crashing (exit 0 or 1)."""
        result = subprocess.run(
            [str(SCRIPTS_DIR / "check_documentation.sh")],
            capture_output=True,
            cwd=PROJECT_ROOT,
        )
        # Exit 0 = docs OK, exit 1 = doc issues
        assert result.returncode in [0, 1], (
            f"Script should exit with 0 or 1, got {result.returncode}. "
            f"stderr: {result.stderr.decode()}"
        )


class TestClientServerParityCheck:
    """Smoke tests for check_client_server_parity.sh."""

    def test_script_exists(self):
        """Script should exist."""
        script_path = SCRIPTS_DIR / "check_client_server_parity.sh"
        assert script_path.exists(), "check_client_server_parity.sh should exist"

    def test_script_executable(self):
        """Script should be executable."""
        script_path = SCRIPTS_DIR / "check_client_server_parity.sh"
        assert script_path.stat().st_mode & 0o111, "check_client_server_parity.sh should be executable"

    def test_runs_without_crashing(self):
        """Script should run without crashing (exit 0 or 1)."""
        result = subprocess.run(
            [str(SCRIPTS_DIR / "check_client_server_parity.sh")],
            capture_output=True,
            cwd=PROJECT_ROOT,
        )
        # Exit 0 = parity OK, exit 1 = parity issues
        assert result.returncode in [0, 1], (
            f"Script should exit with 0 or 1, got {result.returncode}. "
            f"stderr: {result.stderr.decode()}"
        )
