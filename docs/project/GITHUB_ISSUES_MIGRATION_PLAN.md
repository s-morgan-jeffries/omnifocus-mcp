# GitHub Issues Migration Plan

**Created:** 2025-10-21
**Status:** Planning
**Estimated Time:** 5-6 hours
**Target Completion:** TBD

## Table of Contents
1. [Overview](#overview)
2. [Versioning & Issue Workflow](#versioning--issue-workflow)
3. [Label Structure](#label-structure)
4. [GitHub Project Setup](#github-project-setup)
5. [Issue Templates](#issue-templates)
6. [Migration Implementation](#migration-implementation)
7. [Documentation Updates](#documentation-updates)
8. [Testing & Verification](#testing--verification)
9. [Rollout Plan](#rollout-plan)

---

## Overview

### Goal
Migrate from file-based mistake tracking (`.claude/mistakes/MISTAKES.md`) to GitHub Issues for all issue tracking: bugs, features, documentation, and AI process failures.

### Why GitHub Issues?
- **Visibility:** User can see issues without asking Claude
- **Organization:** Labels, milestones, projects for grouping
- **Standard workflow:** Everyone knows GitHub
- **Automation:** GitHub Actions, CLI, native tooling
- **Collaboration:** Comments, mentions, assignees

### Scope
- Migrate all 12 existing AI process failures from MISTAKES.md to GitHub Issues
- Set up label taxonomy for all issue types
- Create GitHub Project for tracking and visualization
- Create issue template for AI process failures
- Update all documentation to reference GitHub Issues
- Rebuild recurrence checking for GitHub Issues
- Update CLAUDE.md with issue filing instructions

### Out of Scope
- GitHub Actions automation (defer to future iteration)
- Advanced GitHub Projects automation (defer to future iteration)
- Migration of ROADMAP.md items (these become issues during version planning)

---

## Versioning & Issue Workflow

### Issue Lifecycle

```
┌─────────────┐
│ Issue Filed │ (Bug, feature, ai-process, etc.)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Backlog   │ (No milestone assigned)
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│ Version Planning    │ (Review issues, decide what goes in next version)
│ - Review all issues │
│ - Assign milestone  │
│ - Update ROADMAP.md │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Development Sprint  │ (Work on milestone issues)
│ - Issues → In Prog  │
│ - Fix/implement     │
│ - Issues → Done     │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Pre-Release Check   │ (Before version bump)
│ - All milestone     │
│   issues closed?    │
│ - ROADMAP updated?  │
│ - CHANGELOG updated?│
└──────┬──────────────┘
       │
       ▼
┌─────────────┐
│   Release   │ (Close milestone, tag version)
└─────────────┘
```

### When Issues Are Created

**During Development:**
- **Bugs discovered** → File immediately with `bug` label
- **AI process failures** → File immediately with `ai-process` label
- **Feature ideas** → File immediately with `enhancement` label
- **Documentation gaps** → File immediately with `documentation` label

**All issues start in Backlog (no milestone assigned).**

### Version Planning Session

**Timing:** Before starting work on next version (e.g., v0.7.0)

**Process:**
1. **Review all open issues** in Backlog
2. **Decide scope for next version** (what issues to address)
3. **Create milestone** (e.g., "v0.7.0")
4. **Assign issues to milestone** (only issues planned for this version)
5. **Update ROADMAP.md** with milestone goals
6. **Start development sprint**

**Example:**
```bash
# During planning for v0.7.0
gh issue list --label bug --no-milestone
# Review, decide which bugs to fix in v0.7.0
gh issue edit 15 --milestone "v0.7.0"
gh issue edit 22 --milestone "v0.7.0"

# Update ROADMAP.md to reflect v0.7.0 scope
```

### Pre-Release Checklist

**Before bumping version to v0.7.0:**
```bash
# 1. Check all milestone issues are closed
gh issue list --milestone "v0.7.0" --state open
# Should return empty

# 2. Verify ROADMAP.md is updated
# 3. Verify CHANGELOG.md has v0.7.0 section
# 4. All tests passing
# 5. Documentation updated
```

### AI Process Failure Recurrence Handling

**When AI process failure occurs:**

**Standard practice: File new issue every time** (don't search first)

```bash
# File issue immediately when failure occurs
gh issue create \
  --template ai-process-failure.md \
  --title "[AI-PROCESS] Description of what went wrong" \
  --label "ai-process,missing-tests,high"
```

**During triage/review:**
- Human reviews issues and marks duplicates
- When duplicate found:
  - Add comment on new issue: "Duplicate of #X"
  - Add label `duplicate` to new issue
  - Close new issue
  - Original issue stays open (or reopen if closed)
  - This indicates recurrence (prevention failed)

**Why this approach:**
- Standard GitHub workflow (everyone knows it)
- Simpler for AI (no searching required)
- Natural audit trail (each issue = one occurrence)
- Easy to see recurrence pattern (multiple duplicates = recurring problem)
- Recurrence count = number of duplicate issues linked to original

**During version planning:**
- Review all `ai-process` issues
- Prioritize issues with many duplicates (indicates recurring problem)
- Assign to milestone if prevention measures need improvement

---

## Label Structure

### Type Labels (Mutually Exclusive - Pick One)
```yaml
- name: bug
  color: d73a4a  # Red
  description: Something isn't working

- name: enhancement
  color: a2eeef  # Light blue
  description: New feature or request

- name: documentation
  color: 0075ca  # Blue
  description: Improvements or additions to documentation

- name: ai-process
  color: 7057ff  # Purple
  description: AI process failure (mistake in workflow/architecture)

- name: question
  color: d876e3  # Pink
  description: Further information is requested
```

### AI Process Categories (Use with `ai-process` label)
```yaml
- name: missing-docs
  color: fef2c0  # Light yellow
  description: Documentation not updated

- name: missing-tests
  color: fbca04  # Yellow
  description: Tests not written or updated

- name: missing-automation
  color: f9d0c4  # Light orange
  description: Automation opportunity missed

- name: architecture-violation
  color: e99695  # Light red
  description: Violated architectural principles

- name: tdd-violation
  color: d93f0b  # Orange
  description: Did not follow TDD workflow
```

### Severity Labels (Optional, use for bugs and ai-process)
```yaml
- name: critical
  color: b60205  # Dark red
  description: Critical priority

- name: high
  color: d93f0b  # Orange
  description: High priority

- name: medium
  color: fbca04  # Yellow
  description: Medium priority

- name: low
  color: 0e8a16  # Green
  description: Low priority
```

### Additional Standard Labels
```yaml
- name: duplicate
  color: cfd3d7  # Gray
  description: This issue is a duplicate of another issue
```

**Label Creation Script:**
```bash
# scripts/setup_github_labels.sh
# Creates all labels listed above
```

**Note:** GitHub provides the `duplicate` label by default, but we include it here for completeness.

---

## GitHub Project Setup

### Project: "OmniFocus MCP Development"

**Type:** Board (with table view available)

### Custom Fields

**No custom fields needed.** We keep it simple using:
- **Labels:** Type, category, severity
- **Issue state:** Open (needs work) vs Closed (resolved)
- **Issue body:** All details (commits, dates, prevention measures)
- **Comments:** Updates and discussions
- **Milestones:** Version planning
- **Duplicates:** Recurrence tracking (number of duplicates = recurrence count)

### Views

**View 1: Sprint Board** (Default)
```
Columns: Backlog | Todo | In Progress | Done
Filter: Current milestone OR no milestone
Group by: Label (type)
```

**View 2: AI Process Dashboard**
```
Type: Table
Filter: label:ai-process
Columns: Title, Labels (category/severity), State, Created, Updated
Sort: Updated DESC
```

**View 3: Next Release**
```
Type: Board
Filter: Current milestone (e.g., v0.7.0)
Group by: Label (type)
Columns: Todo | In Progress | Done
```

**View 4: All Issues Table**
```
Type: Table
Filter: None (all issues)
Columns: Title, Type, Milestone, Created, Updated
Sort: Updated DESC
```

**Project Creation:**
- Create manually in GitHub UI (easier than scripting)
- Set up 4 views as described above
- No custom fields needed

---

## Issue Templates

### AI Process Failure Template

**File:** `.github/ISSUE_TEMPLATE/ai-process-failure.md`

```yaml
---
name: AI Process Failure
about: Log an AI workflow or architectural mistake
title: '[AI-PROCESS] '
labels: ['ai-process']
assignees: []
---

## What Happened

[Clear description of what went wrong]

## Context

- **File(s):**
- **Function(s):**
- **Commit:**
- **Discovery Date:** YYYY-MM-DD

## Impact

[How this affected the project or user]

## Root Cause

[Why this happened - what process/check was missing?]

## Prevention Measures

### Immediate Fix
[What was done to resolve this specific instance]

- **Resolved in commit:** [hash]

### Long-term Prevention
[How to prevent this class of mistakes]

- [ ] Prevention measure 1
- [ ] Prevention measure 2

## Related Issues

[Links to related issues, if any - especially duplicates indicating recurrence]
```

### Default Template (Bugs, Features)

**File:** `.github/ISSUE_TEMPLATE/default.md`

Standard GitHub template - keep minimal:
```yaml
---
name: Bug Report or Feature Request
about: Report a bug or request a feature
title: ''
labels: []
assignees: []
---

## Description

[Clear description]

## Expected Behavior (for bugs)

[What should happen]

## Actual Behavior (for bugs)

[What actually happens]

## Steps to Reproduce (for bugs)

1.
2.
3.

## Proposed Solution (for features)

[How you envision this working]
```

---

## Migration Implementation

### Phase 1: Setup (30 minutes)

**1.1 Create Labels**
```bash
./scripts/setup_github_labels.sh
```

**1.2 Create Issue Templates**
- Create `.github/ISSUE_TEMPLATE/` directory
- Add `ai-process-failure.md`
- Add `default.md`

**1.3 Create GitHub Project**
- Create manually in GitHub UI (simpler without custom fields)
- Set up 4 views as specified in plan

### Phase 2: Migration Script (2 hours)

**2.1 Write Migration Script**

**File:** `scripts/migrate_mistakes_to_issues.sh`

```bash
#!/bin/bash
# Migrates MISTAKES.md to GitHub Issues

set -e

MISTAKES_FILE=".claude/mistakes/MISTAKES.md"
DRY_RUN=${1:-false}  # Pass "true" to test without creating issues

echo "Starting MISTAKES.md migration..."
echo "Dry run: $DRY_RUN"

# Parse MISTAKES.md and create issues
# (Implementation details below)
```

**Migration Logic:**
1. Parse each `## [MISTAKE-XXX]` section
2. Extract:
   - Title
   - Status → determines issue state (monitoring = open, resolved/verified = closed)
   - Category → becomes label (`missing-docs`, etc.)
   - Severity → becomes label (`critical`, `high`, `medium`)
   - Discovery Date → in issue body
   - All other fields → in issue body (preserve markdown)
3. Create issue:
   ```bash
   gh issue create \
     --title "MISTAKE-001: Missing MIGRATION_v0.6.md" \
     --body "$(cat /tmp/mistake-001-body.md)" \
     --label "ai-process,missing-docs,high"
   ```
4. If status was "resolved" or "verified", close the issue:
   ```bash
   gh issue close <issue-number>
   ```

**2.2 Test Migration (Dry Run)**
```bash
# Test on first 2 mistakes
./scripts/migrate_mistakes_to_issues.sh true
# Review output, verify format
```

**2.3 Full Migration**
```bash
# Create all issues
./scripts/migrate_mistakes_to_issues.sh false

# Verify count
gh issue list --label ai-process | wc -l
# Should show 12
```

### Phase 3: Recurrence Checking (2 hours)

**3.1 Rebuild check_recurrence.sh**

**File:** `scripts/check_recurrence.sh`

**New Implementation:**
```bash
#!/bin/bash
# Check for AI process failure recurrences using GitHub Issues

set -e

echo "Checking for AI process recurrences..."

# Get all open ai-process issues (closed ones are considered resolved)
ISSUES=$(gh issue list --label ai-process --state open --json number,title,body)

RECURRENCE_FOUND=false

for row in $(echo "$ISSUES" | jq -r '.[] | @base64'); do
    _jq() {
        echo "$row" | base64 --decode | jq -r "${1}"
    }

    ISSUE_NUM=$(_jq '.number')
    ISSUE_TITLE=$(_jq '.title')
    ISSUE_BODY=$(_jq '.body')

    # Extract prevention script from issue body
    # Look for section: ## Prevention Script
    # (Between ## Prevention Script and next ##)

    PREVENTION_SCRIPT=$(echo "$ISSUE_BODY" | sed -n '/## Prevention Script/,/^##/p' | sed '1d;$d' | sed '/^```bash/,/^```/!d;//d')

    if [ -n "$PREVENTION_SCRIPT" ]; then
        echo "Checking issue #$ISSUE_NUM: $ISSUE_TITLE"

        if ! eval "$PREVENTION_SCRIPT" > /dev/null 2>&1; then
            echo "❌ RECURRENCE DETECTED: Issue #$ISSUE_NUM"

            # File new issue as duplicate (standard GitHub workflow)
            # This will be done manually - script just reports

            RECURRENCE_FOUND=true
        else
            echo "✅ Prevention holding for issue #$ISSUE_NUM"
        fi
    else
        echo "⚠️  No prevention script found for issue #$ISSUE_NUM"
    fi
done

if [ "$RECURRENCE_FOUND" = true ]; then
    echo ""
    echo "❌ Recurrences detected. Review issues above."
    echo "Action required: File new issues for recurrences, mark as duplicates during triage."
    exit 1
else
    echo ""
    echo "✅ No recurrences detected. All preventions holding."
    exit 0
fi
```

**3.2 Update GitHub Actions**

Update `.github/workflows/validate-prevention-measures.yml` to use new script:
```yaml
- name: Check for recurrences
  run: ./scripts/check_recurrence.sh
```

### Phase 4: Documentation Updates (1 hour)

**4.1 Update CLAUDE.md**

Add section on issue filing:

```markdown
## Issue Tracking

This project uses GitHub Issues for all tracking: bugs, features, documentation, and AI process failures.

### When to File Issues

**File immediately when you encounter:**
- **Bug:** Something not working as expected → label: `bug`
- **AI Process Failure:** Violated TDD, forgot tests, missed docs, etc. → label: `ai-process`
- **Feature Idea:** New functionality to consider → label: `enhancement`
- **Documentation Gap:** Missing or outdated docs → label: `documentation`

**All issues start in Backlog (no milestone assigned). They will be reviewed during version planning.**

### Filing AI Process Failures

Use the "AI Process Failure" issue template (`.github/ISSUE_TEMPLATE/ai-process-failure.md`):

1. Clear description of what went wrong
2. Context (files, functions, commits)
3. Impact on project/user
4. Root cause analysis
5. Prevention measures (immediate fix + long-term prevention)

**Required labels:**
- `ai-process` (type)
- Category: `missing-docs`, `missing-tests`, `missing-automation`, `architecture-violation`, or `tdd-violation`
- Severity: `critical`, `high`, `medium`, or `low`

**Example:**
```bash
gh issue create \
  --template ai-process-failure.md \
  --title "[AI-PROCESS] Forgot to update test count in TESTING.md" \
  --label "ai-process,missing-docs,medium"
```

### Recurrence Handling (Standard GitHub Practice)

**File new issue every time** - Don't search first, just file it:

```bash
gh issue create \
  --template ai-process-failure.md \
  --title "[AI-PROCESS] Description of failure" \
  --label "ai-process,category,severity"
```

**During triage (human reviews):**
- Search for duplicates
- Mark as duplicate if found: Add `duplicate` label, comment "Duplicate of #X", close
- Original issue tracks the recurrences via linked duplicates

### Automatic Recurrence Detection

The `check_recurrence.sh` script runs in CI and locally to verify prevention measures are working:

```bash
./scripts/check_recurrence.sh
```

If a prevention measure fails, the script:
- Reports which issue prevention failed
- Exits with error code 1 (fails CI)
- Human then files new issue, marks as duplicate during triage

**Prevention measures must be verifiable bash scripts** embedded in issue body under "## Prevention Script" section.
```

**4.2 Update Other Docs**

Files to update:
- `README.md` - Link to GitHub Issues
- `docs/guides/CONTRIBUTING.md` - Issue filing workflow
- `docs/project/ROADMAP.md` - Reference GitHub Issues migration completion
- `.claude/mistakes/README.md` - Archive notice, point to GitHub Issues

**4.3 Create Archive Notice**

**File:** `.claude/mistakes/ARCHIVE_NOTICE.md`

```markdown
# MISTAKES.md Archive Notice

**Date Archived:** 2025-10-21
**Migrated To:** GitHub Issues

This file-based mistake tracking system has been migrated to GitHub Issues.

**All historical mistakes (MISTAKE-001 through MISTAKE-012) have been migrated to:**
https://github.com/s-morgan-jeffries/omnifocus-mcp/issues?q=label%3Aai-process

**Going forward:**
- File new issues using GitHub Issues
- Use label: `ai-process` for process failures
- Use issue template: `.github/ISSUE_TEMPLATE/ai-process-failure.md`

**Why we migrated:**
- Better visibility for user (native GitHub UI)
- Standard workflow (everyone knows GitHub)
- Native automation (GitHub Actions, CLI)
- Better organization (labels, milestones, projects)

**Old System Preserved:**
The `MISTAKES.md` file has been preserved in git history for reference:
```bash
git show HEAD~1:.claude/mistakes/MISTAKES.md
```

**New Workflow:**
See `.claude/CLAUDE.md` section "Issue Tracking" for complete workflow.
```

---

## Testing & Verification

### Verification Checklist

**Before considering migration complete:**

- [ ] All 12 mistakes migrated to GitHub Issues
- [ ] All issues have correct labels
- [ ] All issues have complete bodies (all fields preserved)
- [ ] GitHub Project created with 4 views
- [ ] Issue templates created and working
- [ ] `check_recurrence.sh` runs successfully
- [ ] `check_recurrence.sh` detects intentional failure (test)
- [ ] GitHub Actions workflow updated and passing
- [ ] CLAUDE.md updated with issue filing instructions
- [ ] All documentation references updated
- [ ] Archive notice created
- [ ] MISTAKES.md can be safely deleted

### Testing Procedure

**1. Verify Migration Accuracy**
```bash
# Check count
gh issue list --label ai-process | wc -l  # Should be 12

# Spot check: Compare MISTAKE-001 in MISTAKES.md vs GitHub Issue
gh issue view 1  # (or whatever number MISTAKE-001 got)
# Verify all fields present and correct
```

**2. Test Issue Templates**
```bash
# Create test issue using template
gh issue create --template ai-process-failure.md
# Verify template loads correctly, fields are there
# Close and delete test issue
```

**3. Test Recurrence Checking**
```bash
# Run check (should pass)
./scripts/check_recurrence.sh

# Intentionally break a prevention measure
# Run check again (should fail and comment on issue)
./scripts/check_recurrence.sh

# Verify comment added and issue reopened
# Fix prevention measure
```

**4. Test Versioning Workflow**
```bash
# Create test milestone
gh milestone create "v0.7.0-test" --due "2025-12-01"

# Assign test issue to milestone
gh issue edit <test-issue> --milestone "v0.7.0-test"

# Verify shows up in milestone
gh issue list --milestone "v0.7.0-test"

# Clean up
gh milestone delete "v0.7.0-test"
```

---

## Rollout Plan

### Pre-Migration

- [ ] Review this plan with user
- [ ] Get approval to proceed
- [ ] Create backup branch: `git checkout -b backup-before-github-issues-migration`
- [ ] Set aside 5-6 hour block for migration

### Migration Day - Step by Step

**Hour 1: Setup**
- [ ] Create all labels (`setup_github_labels.sh`)
- [ ] Create issue templates (`.github/ISSUE_TEMPLATE/`)
- [ ] Create GitHub Project (manual in UI)
- [ ] Create 4 project views (no custom fields needed)

**Hour 2-3: Migration Script**
- [ ] Write `migrate_mistakes_to_issues.sh`
- [ ] Test on MISTAKE-001 only (dry run)
- [ ] Verify issue body format, labels correct
- [ ] If good, run on MISTAKE-001 and MISTAKE-002
- [ ] Verify both issues
- [ ] If good, run full migration (all 12)

**Hour 3-4: Recurrence Script**
- [ ] Rewrite `check_recurrence.sh` for GitHub Issues
- [ ] Test on existing issues
- [ ] Intentionally break a prevention, verify detection
- [ ] Update GitHub Actions workflow
- [ ] Push and verify CI runs correctly

**Hour 4-5: Documentation**
- [ ] Update CLAUDE.md (issue tracking section)
- [ ] Update CONTRIBUTING.md
- [ ] Update README.md
- [ ] Update ROADMAP.md
- [ ] Create ARCHIVE_NOTICE.md
- [ ] Archive `.claude/mistakes/README.md`

**Hour 5-6: Testing & Cleanup**
- [ ] Run full verification checklist
- [ ] Create test issue, verify workflow
- [ ] Delete MISTAKES.md
- [ ] Commit all changes
- [ ] Create PR for review
- [ ] Merge PR
- [ ] Create GitHub release noting migration

### Post-Migration

- [ ] Monitor for 1 week (any issues with new workflow?)
- [ ] File first "real" AI process failure using new system
- [ ] Verify recurrence checking runs in CI
- [ ] Update ROADMAP.md marking migration complete

---

## Rollback Plan

If migration fails or issues discovered:

**Before deleting MISTAKES.md:**
- All data still in git, easy rollback: `git checkout HEAD -- .claude/mistakes/MISTAKES.md`

**After deleting MISTAKES.md:**
- Data preserved in git history: `git show HEAD~1:.claude/mistakes/MISTAKES.md > .claude/mistakes/MISTAKES.md`
- Can delete migrated GitHub Issues if needed: `gh issue delete <num>`

**No data loss risk** - everything in git history and GitHub Issues.

---

## Success Criteria

Migration is successful when:
1. ✅ All 12 historical mistakes migrated to GitHub Issues
2. ✅ Recurrence checking works with GitHub Issues
3. ✅ Documentation updated and accurate
4. ✅ User can view all issues in GitHub without asking Claude
5. ✅ New issues can be filed easily
6. ✅ Version planning workflow documented and understood
7. ✅ Claude knows how to file issues and check for recurrences

---

## Appendix: Example Issue Body

**Example of migrated MISTAKE-001:**

```markdown
# MISTAKE-001: Missing MIGRATION_v0.6.md

**Original ID:** MISTAKE-001
**Discovery Date:** 2025-10-15
**Severity:** High
**Category:** missing-docs

*This issue was migrated from `.claude/mistakes/MISTAKES.md` on 2025-10-21. Original status was "monitoring" - now tracked via GitHub issue state (open = monitoring, closed = resolved).*

## What Happened

When implementing v0.6.0 API redesign, created detailed CHANGELOG.md but forgot to create MIGRATION_v0.6.md guide for users upgrading from v0.5.x. User had to piece together migration steps from CHANGELOG.

## Context

- **File(s):** CHANGELOG.md (created), MIGRATION_v0.6.md (missing)
- **Commit:** e4c28fb (added CHANGELOG), no migration guide commit
- **Discovery Date:** 2025-10-15

## Impact

- User confusion during upgrade
- Higher support burden
- Unprofessional release (incomplete documentation)

## Root Cause

1. CLAUDE.md checklist had "Update CHANGELOG.md" but not "Create MIGRATION_vX.Y.md if breaking changes"
2. Focused on technical accuracy (CHANGELOG) but not user experience (migration guide)
3. No checklist item for "breaking changes need migration guide"

## Prevention Measures

### Immediate Fix
Created MIGRATION_v0.6.md with complete upgrade guide.

- **Resolved in commit:** abc123

### Long-term Prevention
- [x] Added to CLAUDE.md "Before Every Commit" checklist: "Breaking changes need migration guide (MIGRATION_vX.Y.md pattern)"
- [x] Updated CONTRIBUTING.md with documentation requirements for breaking changes

## Prevention Script

```bash
# Check if CHANGELOG has breaking changes without migration guide
if grep -q "BREAKING" CHANGELOG.md && ! ls docs/migration/MIGRATION_v*.md > /dev/null 2>&1; then
    exit 1
fi
exit 0
```

## Recurrence History

- 2025-10-15: Initial occurrence
- No recurrences detected

*If this issue recurs, file new issue and mark as duplicate of this one during triage.*
```

---

**End of Migration Plan**
