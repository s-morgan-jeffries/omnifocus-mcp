---
name: release
description: Use when the user wants to release a new version, says "time to release", "let's release", "cut a release", "version bump", or similar. Orchestrates the full release workflow including milestone check, version bump, changelog generation, validation, tagging, and PR creation. Also invocable as /release.
---

# Release Workflow

This skill orchestrates a complete release. Follow each phase in order. Stop and report if any phase fails.

## Phase 1: Milestone Check

Before creating a release branch, verify the milestone is ready.

1. Determine the target milestone. Look at open milestones:
   ```bash
   gh api "repos/{owner}/{repo}/milestones?state=open&sort=due_on" --jq '.[] | "\(.number) \(.title) open:\(.open_issues) closed:\(.closed_issues)"'
   ```

2. If there are multiple open milestones, ask the user which one to release.

3. If the target milestone has open issues, **stop and ask the user**:
   - List the open issues: `gh api "repos/{owner}/{repo}/milestones/{number}/issues?state=open" --jq ...` (or use `gh issue list --milestone`)
   - Present options:
     a. Move open issues to the next milestone (specify or create it)
     b. Pause to work on the open issues first
     c. Close the issues if they're no longer relevant
   - Do NOT proceed until all issues in the target milestone are closed or moved.

4. Once the milestone is clean (0 open issues), proceed.

## Phase 2: Version Number

1. Read the current version from `pyproject.toml` (authoritative source).
2. The milestone title tells you the target version (e.g., `v0.7.3` means version `0.7.3`).
3. Validate it's a valid semver bump from the current version.
4. Present the version to the user for confirmation: "Release version X.Y.Z? (current: A.B.C)"
5. Wait for confirmation before proceeding.

## Phase 3: Create Release Branch

```bash
git checkout main
git pull origin main
git checkout -b release/vX.Y.Z
```

## Phase 4: Bump Version

Update version in ALL of these files (pyproject.toml is authoritative):

1. **pyproject.toml** - `version = "X.Y.Z"`
2. **src/omnifocus_mcp/__init__.py** - `__version__ = "X.Y.Z"`
3. **CLAUDE.md** (.claude/CLAUDE.md) - `**Version:** vX.Y.Z` in the header line
4. **README.md** - All references to the old version (check with grep for old version string)

Use the Edit tool for each file. Be precise about what to change.

## Phase 5: Generate CHANGELOG

1. Get all commits since the last release:
   ```bash
   git log v{previous_version}..HEAD --oneline
   ```
   Use the previous version tag directly (e.g., `v0.8.1`). Do NOT use `git describe --tags --abbrev=0` — it walks commit ancestry and may not find tags that were created before a squash/rebase merge.

2. Get merged PRs since the last release:
   ```bash
   gh pr list --state merged --base main --search "merged:>YYYY-MM-DD" --json number,title,labels
   ```
   (Use the date of the last tag)

3. Generate a CHANGELOG entry following the existing format in CHANGELOG.md:
   - Use Keep a Changelog format: `## [X.Y.Z] - YYYY-MM-DD`
   - Categorize changes: Added, Changed, Fixed, Removed
   - Reference PR/issue numbers with (#N)
   - Be concise but descriptive
   - Include today's date

4. Insert the new entry at the top of CHANGELOG.md (after the header, before the previous version).

## Phase 6: Test Coverage Review

1. Run coverage report:
   ```bash
   pytest --cov=omnifocus_mcp --cov-report=term-missing tests/ -q
   ```

2. Compare overall coverage against the `fail_under` threshold in `pyproject.toml`. If coverage dropped below the threshold, **stop and report** — new code likely needs tests.

3. Get the cumulative diff to identify changed files:
   ```bash
   git diff v{previous}..HEAD --stat
   ```

4. Audit changed `src/` files for adequate test coverage:
   - New code paths without unit tests
   - Modified AppleScript strings without integration tests (per CLAUDE.md hard rule: "If you wrote or modified an AppleScript string, integration tests must cover it before merge")
   - New parameters or return fields without test assertions

5. Flag any gaps. If coverage dropped or critical paths are untested, stop and fix before proceeding.

## Phase 7: Code Review

1. Get the cumulative diff since the last release:
   ```bash
   git diff v{previous}..HEAD
   ```

2. Launch the `superpowers:code-reviewer` agent to review the full diff. Provide context about the release scope (PRs included, features added/changed).

3. The reviewer will report issues by severity:
   - **Critical** — security issues, data loss risks, correctness bugs → blocks the release
   - **Important** — code quality, missed edge cases → fix or document in PR
   - **Minor** — style, naming, suggestions → note in PR description

4. If Critical issues are found, **stop and fix** before proceeding.

5. Include Important/Minor findings in the release PR description under a "Code Review Notes" section.

## Phase 8: Documentation Review

1. Enumerate documentation to check:
   - `README.md` — feature descriptions, installation, usage examples
   - `.claude/CLAUDE.md` — version, test counts, coverage %, API surface count, performance baselines
   - `CHANGELOG.md` — new entry completeness
   - `docs/**` — architecture, profiling, AppleScript gotchas, automation notes
   - Tool docstrings in `src/omnifocus_mcp/server_fastmcp.py`
   - Skill files in `.claude/skills/`

2. Verify accuracy against changes in this release:
   - Stale version numbers (should still be old version — Phase 4 bumped them)
   - Outdated performance baselines if perf-related changes were made
   - Missing feature documentation for new capabilities
   - Incorrect cross-references between docs
   - Test count / coverage stats in CLAUDE.md header
   - README coverage badge (`coverage-XX%25-brightgreen`) matches actual coverage

3. Flag discrepancies and fix them on the release branch before proceeding.

## Phase 9: Validation

Run ALL validation checks. Stop on any failure.

1. **Version sync check:**
   ```bash
   ./scripts/check_version_sync.sh
   ```

2. **Client-server parity:**
   ```bash
   ./scripts/check_client_server_parity.sh
   ```

3. **Complexity check:**
   ```bash
   ./scripts/check_complexity.sh
   ```

4. **Unit tests:**
   ```bash
   make test
   ```

5. **Dependency audit:**
   ```bash
   ./scripts/check_dependencies.sh
   ```

6. **AppleScript safety audit:**
   ```bash
   ./scripts/check_applescript_safety.sh
   ```

If any check fails, fix the issue and re-run. Do not proceed with failures.

## Phase 10: Commit, Push, and PR

1. **Commit** the version bump and changelog:
   ```bash
   git add -A
   git commit -m "release: vX.Y.Z"
   ```

2. **Push** the branch:
   ```bash
   git push -u origin release/vX.Y.Z
   ```

3. **Create the PR** to main:
   ```bash
   gh pr create --title "release: vX.Y.Z" --body "..."
   ```
   Include any Code Review Notes from Phase 7 in the PR body.

4. Tell the user the PR is ready for review. Do NOT merge it automatically.

## Phase 11: Merge, Tag, and Push Tag

After the user approves the PR:

1. **Merge** using rebase merge:
   ```bash
   gh pr merge NNN --rebase --delete-branch
   ```

2. **Switch to main and pull:**
   ```bash
   git checkout main
   git pull origin main
   ```

3. **Create the tag on main** (where it will be reachable via `git describe`):
   ```bash
   ./scripts/create_tag.sh vX.Y.Z
   ```

4. **Push the tag:**
   ```bash
   git push origin vX.Y.Z
   ```

5. **Verify** tag reachability:
   ```bash
   git describe --tags --abbrev=0  # Should return vX.Y.Z
   ```

## Phase 12: Close Milestone

After the tag is pushed, close the milestone:

```bash
gh api -X PATCH "repos/{owner}/{repo}/milestones/{number}" -f state=closed
```

## Notes

- CHANGELOG is only updated on release branches, never on feature branches.
- Tags are created on main **after** the PR merge. This ensures they are reachable via `git describe`, which walks commit ancestry. Squash/rebase merges create new commits, so tags on the release branch would become orphaned.
- Use **rebase merge** for release PRs. Merge commits are blocked by `required_linear_history` on main.
- Integration tests (`make test-integration`, `make test-e2e`) require a real OmniFocus test database. Ask the user if they want to run them — they're optional for the release validation.
