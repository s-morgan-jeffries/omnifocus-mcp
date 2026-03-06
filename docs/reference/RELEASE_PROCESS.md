# Release Process

The release process is automated via the `/release` skill (`.claude/skills/release/SKILL.md`).

## Quick Reference

```bash
# Tell Claude Code to run the release workflow
/release
```

The skill handles all 8 phases:

1. **Milestone check** — Verify all issues closed, ask about open ones
2. **Version number** — Read from pyproject.toml, confirm with user
3. **Create release branch** — `release/vX.Y.Z` from main
4. **Bump version** — pyproject.toml, __init__.py, CLAUDE.md, README.md
5. **Generate CHANGELOG** — From commits and merged PRs since last tag
6. **Validation** — Version sync, client-server parity, complexity, unit tests
7. **Commit, tag, push, PR** — Tag on release branch, push, create PR
8. **Close milestone** — After PR is created

## Validation Scripts

These run during Phase 6:

| Script | Purpose |
|--------|---------|
| `scripts/check_version_sync.sh` | Version consistency across files |
| `scripts/check_client_server_parity.sh` | All connector functions exposed as MCP tools |
| `scripts/check_complexity.sh` | Cyclomatic complexity thresholds |
| `scripts/check_changelog_date.sh` | CHANGELOG date is set (not TBD) |

## Conventions

- **Merge strategy:** Squash merge for all PRs (merge commits blocked on this repo)
- **Tag format:** `vX.Y.Z` (no RC tags)
- **Branch format:** `release/vX.Y.Z`
- **CHANGELOG:** Only updated on release branches, never on feature branches
- **Version authority:** `pyproject.toml` is the single source of truth
