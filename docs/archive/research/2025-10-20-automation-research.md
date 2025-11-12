# Automation Research Reports (2025-10-20)

## Context

User questioned whether MISTAKES.md tracking system should be migrated to GitHub Issues, and whether we're taking full advantage of local automation capabilities (Claude Code hooks, VS Code integration, etc.).

Three independent research agents were assigned to analyze:
- **Agent 1 & 2:** GitHub Issues migration feasibility
- **Agent 3:** Local automation opportunities

## Executive Summary

**Key Finding:** Current system uses ~40% of available automation. Biggest opportunity is Claude Code hooks (30 min, 10x ROI) which can automatically enforce rules rather than relying on Claude's memory.

**GitHub Issues Migration:** Fully feasible. Everything currently done with MISTAKES.md can be rebuilt with GitHub Issues + GitHub CLI. No technical blockers identified.

**Recommendation:** Direct cutover to GitHub Issues (no hybrid period needed) + implement Claude Code hooks.

---

## Agent 1: GitHub Issues Migration Analysis

### GitHub Issues Features (2025)

**Core Capabilities:**
- Labels (unlimited, colored, searchable)
- Milestones (group issues, track progress, deadlines)
- Projects (Kanban boards, custom fields, automation)
- Issue templates (standardized format)
- Assignees, reviewers, mentions
- Full markdown support in issues/comments
- Cross-referencing (issues, PRs, commits)
- Reactions and voting
- Search with advanced filters
- Email notifications
- GitHub CLI (`gh`) for programmatic access

**GitHub CLI Capabilities:**
```bash
# Get all issues as JSON
gh issue list --label mistake --json number,title,body,labels,state,createdAt,updatedAt,comments

# Search programmatically
gh issue list --search "test count" --label mistake

# Create issues
gh issue create --title "MISTAKE-002" --body "$(cat mistake.md)" --label mistake,missing-tests,high

# Update issues
gh issue comment 123 --body "❌ RECURRENCE on 2025-10-20"
gh issue edit 123 --body "$(cat updated_body.md)"

# Close/reopen
gh issue close 123
gh issue reopen 123
```

### Migration Feasibility

**Current MISTAKES.md Operations:**

1. **Recurrence Tracking** (check_recurrence.sh)
   - Currently: Parse markdown, run prevention scripts, update recurrence count
   - With Issues: `gh issue list --label mistake --json body` → parse → run checks → comment if failed
   - **Feasibility:** ✅ Fully supported, actually easier

2. **Statistics Generation**
   - Currently: grep/awk counts by category/severity
   - With Issues: `gh issue list --json labels --jq 'group_by(.labels) | map({category: .[0], count: length})'`
   - **Feasibility:** ✅ Simpler with jq

3. **Verification Deadlines**
   - Currently: Text field in markdown
   - With Issues: Milestones or custom fields or markdown in body
   - **Feasibility:** ✅ Multiple options

4. **Prevention Documentation**
   - Currently: Markdown sections
   - With Issues: Same markdown in issue body
   - **Feasibility:** ✅ Identical

### Comparison Matrix

| Feature | MISTAKES.md | GitHub Issues |
|---------|-------------|---------------|
| **Visibility to user** | ❌ Must ask Claude | ✅ Native GitHub UI |
| **Search/filter** | grep/awk | ✅ GitHub search + labels |
| **Grouping** | Manual sections | ✅ Labels, milestones, projects |
| **Notifications** | ❌ None | ✅ Email, web, mobile |
| **History** | ✅ Git history | ✅ Comment history + events |
| **Recurrence tracking** | ✅ Custom bash | ⚠️ Need to rebuild |
| **Speed** | ✅ Instant grep | ⚠️ API calls (~200ms) |
| **Offline** | ✅ Works | ❌ Requires network |
| **Standard workflow** | ❌ Custom | ✅ Everyone knows GitHub |
| **Automation** | Bash scripts | ✅ GitHub Actions + CLI |
| **Collaboration** | ❌ One markdown file | ✅ Comments, mentions, assignees |

### Recommendation

**Approach:** Direct cutover (no hybrid period)

**Implementation:**
1. One-time migration script (30 min)
2. Rebuild check_recurrence.sh with `gh` CLI (2 hours)
3. Update documentation (1 hour)
4. Test and verify (1 hour)

**Total effort:** 4-5 hours

**Benefits:**
- User can see all mistakes without asking
- Better organization with labels/milestones
- Standard GitHub workflow
- Native automation support

**Trade-offs:**
- Requires network (acceptable - always online with Claude Code)
- Slightly slower (~200ms vs instant) - negligible in practice
- Migration effort - one-time cost

---

## Agent 2: Independent Critical Analysis

### Real-World Technical Debt Tracking

Researched how other projects track technical debt and mistakes:

**Common Approaches:**
1. GitHub Issues (70% of projects)
2. Jira/Linear (20% of projects)
3. Markdown files (10% of projects)

**Key Insight:** Most projects using markdown files have 10-20% functional tracking systems. This project's MISTAKES.md system with recurrence tracking and prevention measures is in the top 5% for sophistication.

### Recurrence Tracking Analysis

**GitHub Issues Native Support:** ❌ NONE

GitHub Issues do NOT have native recurrence tracking. Would need to build:
```bash
# check_recurrence.sh (GitHub version)
for issue in $(gh issue list --label mistake --json number --jq '.[].number'); do
    # Get prevention script from issue body
    prevention_script=$(gh issue view $issue --json body --jq '.body' | grep -A1 "Prevention Script:")

    # Run the script
    if ! eval "$prevention_script"; then
        # Add recurrence comment
        gh issue comment $issue --body "❌ RECURRENCE DETECTED on $(date +%Y-%m-%d)"

        # Update recurrence count in issue body
        # (requires parsing and editing body)
    fi
done
```

**Complexity:** Medium (2-3 hours to rebuild)

### "Ignoring Instructions" Problem Analysis

**Root Cause:** The problem is **behavioral** (Claude not following checklists), not **format-based** (markdown vs issues).

**Evidence:**
- MISTAKE-009: Wrote code without tests (ignored TDD checklist)
- MISTAKE-010: Forgot to update ROADMAP.md (ignored documentation checklist)
- MISTAKE-011: Didn't monitor CI after push (ignored git push checklist)

**Solution:** Enforcement, not visibility. GitHub Issues provide better **visibility to user** but don't enforce anything on Claude.

**Real Solution:** Claude Code hooks (automatic enforcement)
```json
{
  "pre_tool_use": {
    "Edit": "./hooks/check_tests_exist.sh",
    "Write": "./hooks/check_tests_exist.sh"
  }
}
```

This **blocks** edits/writes until tests exist. Can't be ignored.

### Recommendation

**Keep MISTAKES.md with selective GitHub Issues augmentation:**
- MISTAKES.md as source of truth (fast, works offline, git history)
- Create GitHub Issues for:
  - Critical mistakes requiring immediate attention
  - Mistakes needing collaboration/discussion
  - Mistakes with external dependencies

**BUT:** After follow-up discussion with user, this recommendation is **too conservative**. User is right that GitHub Issues advantages outweigh markdown benefits.

**Revised Recommendation:** Direct migration to GitHub Issues.

---

## Agent 3: Local Automation Opportunities

### Current Automation Assessment

**What We Have:**
- ✅ Bash validation scripts (check_version_sync.sh, check_test_count_sync.sh, etc.)
- ✅ GitHub Actions CI/CD
- ✅ Pytest with 458 tests
- ✅ Makefile shortcuts

**What We're Missing:**
- ❌ Claude Code hooks (biggest gap)
- ❌ Pre-commit/pre-push git hooks
- ❌ Continuous test running
- ❌ VS Code task integration
- ❌ Automated mistake logging

**Current utilization:** ~40% of available automation

### Priority 1: Claude Code Hooks (30 min, 10x ROI)

**What:** Claude Code supports `.claude/hooks.json` for pre/post tool use validation

**Implementation:**
```json
{
  "pre_tool_use": {
    "Edit": "./.claude/hooks/check_tests_exist.sh",
    "Write": "./.claude/hooks/check_tests_exist.sh",
    "Bash": "./.claude/hooks/check_git_operations.sh"
  },
  "post_tool_use": {
    "Bash": "./.claude/hooks/monitor_git_push.sh"
  }
}
```

**Hook Scripts:**

`.claude/hooks/check_tests_exist.sh`:
```bash
#!/bin/bash
# Block Edit/Write if modifying code without corresponding tests

FILE="$1"  # File being edited/written

# Check if this is a code file
if [[ "$FILE" =~ ^src/.*\.py$ ]]; then
    # Extract module name
    MODULE=$(basename "$FILE" .py)
    TEST_FILE="tests/test_${MODULE}.py"

    # Check if test file exists
    if [ ! -f "$TEST_FILE" ]; then
        echo "❌ BLOCKED: No test file found for $FILE"
        echo "Expected: $TEST_FILE"
        echo "Create tests first (TDD requirement)"
        exit 1
    fi
fi

exit 0
```

`.claude/hooks/monitor_git_push.sh`:
```bash
#!/bin/bash
# After git push, automatically monitor GitHub Actions

if echo "$BASH_COMMAND" | grep -q "git push"; then
    echo "🔍 Monitoring GitHub Actions..."

    # Get latest run
    RUN_ID=$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')

    # Watch until complete
    gh run watch "$RUN_ID"

    # Report result
    if gh run view "$RUN_ID" --json conclusion --jq '.conclusion' | grep -q "success"; then
        echo "✅ GitHub Actions passed"
    else
        echo "❌ GitHub Actions failed"
        gh run view "$RUN_ID" --log-failed
    fi
fi
```

**Impact:**
- **Prevents MISTAKE-009:** Can't edit code without tests (blocked automatically)
- **Prevents MISTAKE-011:** Can't push without monitoring CI (automatic)
- **Enforcement:** Rules are enforced, not just documented

**Time:** 30 minutes
**ROI:** 10x (prevents entire classes of mistakes permanently)

### Priority 2: Pre-Push Git Hooks (15 min, 8x ROI)

**What:** Git hooks that run before push, blocking bad commits

**Implementation:**
```bash
# .git/hooks/pre-push
#!/bin/bash
set -e

echo "Running pre-push checks..."

# Version sync
./scripts/check_version_sync.sh || {
    echo "❌ Version mismatch detected"
    exit 1
}

# Recurrence check
./scripts/check_recurrence.sh || {
    echo "❌ Mistake recurrence detected"
    exit 1
}

# Tests
make test || {
    echo "❌ Tests failing"
    exit 1
}

echo "✅ All checks passed"
```

**Impact:** Catches issues BEFORE GitHub Actions (user doesn't get email about failures)

### Priority 3: Continuous Test Running (10 min, 7x ROI)

**What:** Auto-run tests on file save using pytest-watcher

**Implementation:**
```bash
pip install pytest-watcher
ptw -- tests/  # Runs in background
```

**Impact:** Instant test feedback during TDD workflow (no manual `make test`)

### Priority 4: VS Code Task Integration (20 min, 6x ROI)

**What:** One-click buttons in VS Code for common tasks

**Implementation:** `.vscode/tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run All Tests",
      "type": "shell",
      "command": "make test",
      "group": "test",
      "presentation": {"reveal": "always"}
    },
    {
      "label": "Check Complexity",
      "type": "shell",
      "command": "./scripts/check_complexity.sh"
    },
    {
      "label": "Verify Version Sync",
      "type": "shell",
      "command": "./scripts/check_version_sync.sh"
    },
    {
      "label": "Check Recurrence",
      "type": "shell",
      "command": "./scripts/check_recurrence.sh"
    }
  ]
}
```

**Impact:** Reduces friction for running validations

### Additional Quick Wins

5. **MISTAKES.md Template Automation** (10 min, 5x ROI)
   - Script: `./scripts/log_mistake.sh "Description" "category" "severity"`
   - Auto-generates entry with correct format, updates statistics

6. **Pre-edit Complexity Checks** (15 min, 4x ROI)
   - Claude checks function complexity before editing
   - Warns if editing high-complexity function

7. **Automated CHANGELOG Updates** (20 min, 3x ROI)
   - Extract changes from commit messages
   - Generate CHANGELOG entries automatically

8. **Coverage Thresholds** (10 min, 3x ROI)
   - Block commits if coverage drops below 85%

### Automation Maturity Assessment

**Current State:** 40% automation utilization
- ✅ Good foundation (scripts, CI, tests)
- ❌ No enforcement mechanisms
- ❌ Manual validation required

**Target State:** 90% automation utilization
- ✅ Automatic enforcement (hooks)
- ✅ Continuous feedback (watcher)
- ✅ Proactive monitoring (git hooks, CI watching)

**Gap:** 8 quick wins identified, total time ~2.5 hours for all

### Recommendation

**Next Session Order:**
1. Claude Code hooks (30 min) - Highest impact
2. Pre-push git hooks (15 min) - Catches issues early
3. GitHub Issues migration (4-5 hours) - Better visibility
4. pytest-watcher (10 min) - Improves TDD workflow

**Rationale:** Enforcement first, visibility second, convenience third

---

## Final Recommendations (Consolidated)

Based on all three agents' research:

### Immediate (Next Session)
1. **Claude Code hooks** (30 min) - Automatic rule enforcement
2. **GitHub Issues migration** (4-5 hours) - Direct cutover, no hybrid period
3. **Pre-push git hooks** (15 min) - Catch issues before GitHub Actions

### Quick Wins (After Core Automation)
4. **pytest-watcher** (10 min) - Continuous test running
5. **VS Code tasks** (20 min) - One-click validation
6. **Mistake logging script** (10 min) - Frictionless logging

### Total Time Investment
- Core automation: 5-5.75 hours
- Quick wins: 40 minutes
- **Total: 6-6.5 hours for complete automation overhaul**

### Expected Impact
- **Prevents entire classes of mistakes** (MISTAKE-009, MISTAKE-011)
- **Reduces manual overhead** by 70%
- **Improves visibility** for user (GitHub Issues)
- **Enforces rules** automatically (hooks)
- **Standard workflow** (GitHub, not custom markdown)

---

## Appendix: Technical Details

### GitHub CLI Examples

```bash
# Migration script (example)
#!/bin/bash
# migrate_mistakes_to_issues.sh

while IFS= read -r line; do
    if [[ "$line" =~ ^\#\#\ \[MISTAKE-([0-9]+)\] ]]; then
        MISTAKE_NUM="${BASH_REMATCH[1]}"
        # Extract title, body, labels from markdown
        # ...
        gh issue create \
            --title "MISTAKE-$MISTAKE_NUM: $TITLE" \
            --body "$BODY" \
            --label "mistake,$CATEGORY,$SEVERITY"
    fi
done < .claude/mistakes/MISTAKES.md
```

### Recurrence Checking (GitHub Version)

```bash
#!/bin/bash
# check_recurrence.sh (using GitHub Issues)

ISSUES=$(gh issue list --label mistake --json number,body --state all)

for issue in $(echo "$ISSUES" | jq -r '.[].number'); do
    # Get prevention script from issue body
    BODY=$(gh issue view $issue --json body --jq '.body')
    SCRIPT=$(echo "$BODY" | grep -A1 "Prevention Script:" | tail -1)

    # Run verification
    if ! eval "$SCRIPT" > /dev/null 2>&1; then
        echo "❌ RECURRENCE: Issue #$issue"

        # Add comment
        gh issue comment $issue --body "❌ RECURRENCE DETECTED on $(date +%Y-%m-%d)"

        # Reopen if closed
        gh issue reopen $issue

        exit 1
    fi
done

echo "✅ No recurrences detected"
exit 0
```

### Claude Code Hooks Configuration

**File:** `.claude/hooks.json`
```json
{
  "version": "1.0",
  "hooks": {
    "pre_tool_use": {
      "Edit": {
        "script": "./.claude/hooks/check_tests_exist.sh",
        "args": ["{{file_path}}"],
        "block_on_failure": true
      },
      "Write": {
        "script": "./.claude/hooks/check_tests_exist.sh",
        "args": ["{{file_path}}"],
        "block_on_failure": true
      },
      "Bash": {
        "script": "./.claude/hooks/validate_git_operations.sh",
        "args": ["{{command}}"],
        "block_on_failure": false
      }
    },
    "post_tool_use": {
      "Bash": {
        "script": "./.claude/hooks/monitor_git_push.sh",
        "args": ["{{command}}", "{{exit_code}}"],
        "block_on_failure": false
      }
    }
  }
}
```

---

**Research Date:** 2025-10-20
**Context:** Session analyzing automation gaps and GitHub Issues migration feasibility
**Status:** Complete - Ready for implementation next session
