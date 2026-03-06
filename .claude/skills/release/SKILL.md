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

1. Get all commits since the last tag:
   ```bash
   git log $(git describe --tags --abbrev=0)..HEAD --oneline
   ```

2. Get merged PRs since the last tag:
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

## Phase 6: Validation

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

If any check fails, fix the issue and re-run. Do not proceed with failures.

## Phase 7: Commit, Tag, Push, and PR

1. **Commit** the version bump and changelog:
   ```bash
   git add -A
   git commit -m "release: vX.Y.Z"
   ```

2. **Create the tag** on the release branch:
   ```bash
   ./scripts/create_tag.sh vX.Y.Z
   ```

3. **Push** the branch and tag:
   ```bash
   git push -u origin release/vX.Y.Z
   git push origin vX.Y.Z
   ```

4. **Create the PR** to main:
   ```bash
   gh pr create --title "release: vX.Y.Z" --body "..."
   ```
   Use a merge commit (not squash) for release PRs — the individual commits are meaningful.

5. Tell the user the PR is ready for review. Do NOT merge it automatically.

## Phase 8: Close Milestone

After the PR is created (not merged), close the milestone:

```bash
gh api -X PATCH "repos/{owner}/{repo}/milestones/{number}" -f state=closed
```

## Notes

- CHANGELOG is only updated on release branches, never on feature branches.
- The pre-tag hook validates that final release tags are on main and that CHANGELOG dates are set. Since we tag on the release branch and merge to main, the tag is created here before merging.
- If `create_tag.sh` fails due to the pre-tag hook requiring main branch, create the tag after the PR is merged instead. Adjust the workflow accordingly and inform the user.
- Integration tests (`make test-integration`, `make test-e2e`) require a real OmniFocus test database. Ask the user if they want to run them — they're optional for the release validation.
