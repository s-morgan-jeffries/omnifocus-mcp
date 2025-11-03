# MISTAKES.md Archive Notice

**Date Archived:** 2025-10-21
**Migrated To:** GitHub Issues

This file-based mistake tracking system has been migrated to GitHub Issues.

## Migrated Issues

**All historical AI process failures (MISTAKE-001 through MISTAKE-012) have been migrated to:**

https://github.com/s-morgan-jeffries/omnifocus-mcp/issues?q=label%3Aai-process

**Current status:**
- 6 open issues (MISTAKE-002, 003, 007, 008, 011, 012)
- 4 closed issues (MISTAKE-001, 004, 009, 010)

## Going Forward

**File new issues using GitHub Issues:**
```bash
gh issue create \
  --title "[AI-PROCESS] Description of failure" \
  --label "ai-process,category,severity"
```

**Use the issue template:** `.github/ISSUE_TEMPLATE/ai-process-failure.md`

**View all AI process issues:**
```bash
gh issue list --label ai-process
```

## Why We Migrated

- **Better visibility:** User can see issues in native GitHub UI without asking Claude
- **Standard workflow:** Everyone knows GitHub Issues
- **Native automation:** GitHub Actions, CLI, notifications
- **Better organization:** Labels, milestones, projects for grouping
- **Version planning:** Use milestones to group issues by version

## Old System Preserved

The `MISTAKES.md` file has been preserved in git history for reference:

```bash
# View the last version before migration
git show 762f0c7:.claude/mistakes/MISTAKES.md

# Or view at a specific commit
git log --all --full-history -- .claude/mistakes/MISTAKES.md
```

## New Workflow

**See `.claude/CLAUDE.md` section "Issue Tracking" for complete workflow:**
1. File issues immediately when they occur
2. Issues start in Backlog (no milestone)
3. During version planning, assign issues to milestones
4. Work on milestone issues during sprint
5. Close issues when resolved
6. File duplicates for recurrences (marked during triage)

**Recurrence checking:**
```bash
./scripts/check_recurrence.sh
```

This script fetches open `ai-process` issues from GitHub and runs their prevention scripts to detect recurrences automatically.

## Migration Details

**Migration completed:** 2025-10-21
**Migration plan:** `docs/project/GITHUB_ISSUES_MIGRATION_PLAN.md`
**Migration script:** `scripts/migrate_mistakes_to_issues.sh`

All 10 mistakes successfully migrated with proper formatting, labels, and issue state (open/closed) matching original status (monitoring/resolved).
