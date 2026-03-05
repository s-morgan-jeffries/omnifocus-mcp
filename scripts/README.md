# Scripts

Utility scripts for development, testing, and release of the OmniFocus MCP server.

## Validation

| Script | Purpose |
|--------|---------|
| `check_version_sync.sh` | Version consistency across pyproject.toml, CLAUDE.md, CHANGELOG, README |
| `check_client_server_parity.sh` | Verify all connector functions are exposed as MCP tools |
| `check_complexity.sh` | Cyclomatic complexity check via Radon |
| `check_changelog_date.sh` | Verify CHANGELOG date is set (not TBD) before final release |

## Testing

| Script | Purpose |
|--------|---------|
| `run_all_tests.sh` | Run unit + integration + E2E tests |
| `run_integration_tests.sh` | Run integration test workflow |
| `check_test_coverage.sh` | Verify coverage meets 85% threshold |
| `setup_test_database.sh` | Create OmniFocus test database |
| `setup_comprehensive_test_data.sh` | Populate test database with fixtures |
| `cleanup_test_data.sh` | Remove test data |
| `cleanup_comprehensive_test_data.sh` | Remove comprehensive test data |

## Release

| Script | Purpose |
|--------|---------|
| `create_tag.sh` | Create version tags (RC and final) |
| `sync_version.sh` | Bump version across all files |
| `check_code_quality.sh` | Code quality scan (TODOs, print statements, bare excepts) |
| `check_directory_organization.sh` | Directory structure check |

## Git Hooks

| Hook | Purpose |
|------|---------|
| `git-hooks/pre-commit` | Block direct commits to main, version sync warning |
| `git-hooks/pre-tag` | Validate tag format, branch requirements, CHANGELOG date |
| `git-hooks/pre-push` | Push protection |

Install with: `./scripts/install-git-hooks.sh`

## Claude Code Hooks

| Hook | Purpose |
|------|---------|
| `hooks/session_start.sh` | Load project context (branch, milestone, recent commits) |
| `hooks/pre_bash.sh` | Branch protection, tag creation enforcement |
| `hooks/post_bash.sh` | CI monitoring after push |

## Local Development

| Script | Purpose |
|--------|---------|
| `local/switch_to_test_db.sh` | Switch to test database |
| `local/switch_to_prod_db.sh` | Switch to production database |
| `local/setup_profiling_data.sh` | Create profiling test data |
