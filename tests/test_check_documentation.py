"""
Unit tests for scripts/check_documentation.sh

Tests the documentation completeness check script that runs during release hygiene checks.
"""

import subprocess
import tempfile
import shutil
from pathlib import Path
import pytest


@pytest.fixture
def temp_repo():
    """Create a temporary directory with minimal files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)

        # Create minimal directory structure
        (repo_path / ".claude").mkdir()
        (repo_path / "docs" / "guides").mkdir(parents=True)
        (repo_path / "docs" / "reference").mkdir(parents=True)
        (repo_path / "docs" / "project").mkdir(parents=True)

        # Copy the check script
        script_src = Path("scripts/check_documentation.sh")
        script_dest = repo_path / "scripts" / "check_documentation.sh"
        script_dest.parent.mkdir(parents=True)
        shutil.copy(script_src, script_dest)
        script_dest.chmod(0o755)

        yield repo_path


def run_check(repo_path, version):
    """Run the documentation check script and return result."""
    result = subprocess.run(
        ["./scripts/check_documentation.sh", version],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    return result.returncode, result.stdout, result.stderr


def test_check_requires_version_argument():
    """Test that script requires version argument."""
    result = subprocess.run(
        ["./scripts/check_documentation.sh"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 1
    assert "Usage:" in result.stdout


def test_changelog_check_passes(temp_repo):
    """Test CHANGELOG check passes when entry exists."""
    # Create CHANGELOG with entry
    changelog = temp_repo / "CHANGELOG.md"
    changelog.write_text("""
# Changelog

## [0.7.0] - 2025-11-12
- New feature

## [0.6.7] - 2025-11-11
- Old feature
""")

    # Create minimal other files to avoid failures
    (temp_repo / ".claude/CLAUDE.md").write_text("Current Version: v0.7.0")
    (temp_repo / "README.md").write_text("""
v0.7.0 API
Key Changes in v0.7.0:
git checkout v0.7.0
""")

    # Create key doc files
    for doc in ["TESTING.md", "CONTRIBUTING.md", "INTEGRATION_TESTING.md"]:
        (temp_repo / "docs" / "guides" / doc).touch()
    for doc in ["ARCHITECTURE.md", "CODE_QUALITY.md", "APPLESCRIPT_GOTCHAS.md"]:
        (temp_repo / "docs" / "reference" / doc).touch()
    (temp_repo / "docs" / "project" / "ROADMAP.md").touch()

    returncode, stdout, stderr = run_check(temp_repo, "v0.7.0")
    assert returncode == 0
    assert "✅ CHANGELOG.md has entry for v0.7.0" in stdout


def test_changelog_check_fails(temp_repo):
    """Test CHANGELOG check fails when entry missing."""
    changelog = temp_repo / "CHANGELOG.md"
    changelog.write_text("""
# Changelog

## [0.6.7] - 2025-11-11
- Old feature
""")

    (temp_repo / ".claude/CLAUDE.md").write_text("Current Version: v0.6.7")
    (temp_repo / "README.md").write_text("v0.6.7 API")

    returncode, stdout, stderr = run_check(temp_repo, "v0.7.0")
    assert returncode == 1
    assert "❌ CHANGELOG.md missing entry for v0.7.0" in stdout


def test_readme_installation_example_check(temp_repo):
    """Test README installation example must reference current version."""
    (temp_repo / "CHANGELOG.md").write_text("## [0.7.0] - 2025-11-12")
    (temp_repo / ".claude/CLAUDE.md").write_text("Current Version: v0.7.0")

    # README has wrong version in installation example
    readme = temp_repo / "README.md"
    readme.write_text("""
v0.7.0 API

Key Changes in v0.7.0:
- New stuff

git checkout v0.6.7  # Old version!
""")

    returncode, stdout, stderr = run_check(temp_repo, "v0.7.0")
    assert returncode == 1
    assert "❌ Installation example should reference 'v0.7.0'" in stdout


def test_readme_key_changes_check(temp_repo):
    """Test README 'Key Changes' section must mention current version."""
    (temp_repo / "CHANGELOG.md").write_text("## [0.7.0] - 2025-11-12")
    (temp_repo / ".claude/CLAUDE.md").write_text("Current Version: v0.7.0")

    # README has old version in Key Changes
    readme = temp_repo / "README.md"
    readme.write_text("""
v0.7.0 API

Key Changes in v0.6.7:
- Old stuff

git checkout v0.7.0
""")

    returncode, stdout, stderr = run_check(temp_repo, "v0.7.0")
    assert returncode == 1
    assert "❌ 'Key Changes' section should include v0.7.0" in stdout


def test_readme_comprehensive_checks_pass(temp_repo):
    """Test all README checks pass with correct content."""
    (temp_repo / "CHANGELOG.md").write_text("## [0.7.0] - 2025-11-12")
    (temp_repo / ".claude/CLAUDE.md").write_text("Current Version: v0.7.0")

    # README with all correct version references
    readme = temp_repo / "README.md"
    readme.write_text("""
This is the v0.7.0 API documentation.

Key Changes in v0.7.0:
- New feature added

Installation:
git checkout v0.7.0
""")

    # Create key doc files
    for doc in ["TESTING.md", "CONTRIBUTING.md", "INTEGRATION_TESTING.md"]:
        (temp_repo / "docs" / "guides" / doc).touch()
    for doc in ["ARCHITECTURE.md", "CODE_QUALITY.md", "APPLESCRIPT_GOTCHAS.md"]:
        (temp_repo / "docs" / "reference" / doc).touch()
    (temp_repo / "docs" / "project" / "ROADMAP.md").touch()

    returncode, stdout, stderr = run_check(temp_repo, "v0.7.0")
    assert returncode == 0
    assert "✅ Installation example references v0.7.0" in stdout
    assert "✅ 'Key Changes' section mentions v0.7.0" in stdout
    assert "✅ API version header mentions v0.7.0" in stdout


def test_breaking_changes_require_migration_guide(temp_repo):
    """Test that breaking changes in CHANGELOG require migration guide."""
    changelog = temp_repo / "CHANGELOG.md"
    changelog.write_text("""
## [0.7.0] - 2025-11-12

### BREAKING CHANGES
- API changed significantly

## [0.6.7] - 2025-11-11
""")

    (temp_repo / ".claude/CLAUDE.md").write_text("Current Version: v0.7.0")
    (temp_repo / "README.md").write_text("v0.7.0 API\nKey Changes in v0.7.0:\ngit checkout v0.7.0")

    # No migration guide exists
    returncode, stdout, stderr = run_check(temp_repo, "v0.7.0")
    assert returncode == 1
    assert "⚠️  CHANGELOG mentions breaking changes" in stdout
    assert "❌ Migration guide missing" in stdout


def test_missing_key_documentation_files(temp_repo):
    """Test that missing key documentation files are detected."""
    (temp_repo / "CHANGELOG.md").write_text("## [0.7.0] - 2025-11-12")
    (temp_repo / ".claude/CLAUDE.md").write_text("Current Version: v0.7.0")
    (temp_repo / "README.md").write_text("v0.7.0 API\nKey Changes in v0.7.0:\ngit checkout v0.7.0")

    # Create only some doc files, not all
    (temp_repo / "docs" / "guides" / "TESTING.md").touch()

    returncode, stdout, stderr = run_check(temp_repo, "v0.7.0")
    assert returncode == 1
    assert "❌ Missing key documentation files:" in stdout
    assert "docs/guides/CONTRIBUTING.md" in stdout


def test_v070_rc1_scenario_would_have_failed(temp_repo):
    """
    Test that the enhanced script would have caught the v0.7.0-rc1 issue.

    At v0.7.0-rc1, README had:
    - Line 1: "v0.7.0 API" (correct)
    - Key Changes: "v0.6.7" (wrong)
    - Installation: "git checkout v0.6.7" (wrong)

    The old script passed because it only checked if v0.7.0 appeared anywhere.
    The enhanced script should fail.
    """
    (temp_repo / "CHANGELOG.md").write_text("## [0.7.0] - 2025-11-12")
    (temp_repo / ".claude/CLAUDE.md").write_text("Current Version: v0.7.0")

    # Simulate the problematic v0.7.0-rc1 README
    readme = temp_repo / "README.md"
    readme.write_text("""
This server provides **17 comprehensive tools** for managing OmniFocus (v0.7.0 API):

**Key Changes in v0.6.7:**
- v0.6.7: Fixed unit test timeout issue

Installation:
git checkout v0.6.7  # Or latest version
""")

    returncode, stdout, stderr = run_check(temp_repo, "v0.7.0")

    # Should fail because installation and key changes reference wrong version
    assert returncode == 1
    assert "❌ Installation example should reference 'v0.7.0'" in stdout
    assert "❌ 'Key Changes' section should include v0.7.0" in stdout
    # But API header should pass
    assert "✅ API version header mentions v0.7.0" in stdout
