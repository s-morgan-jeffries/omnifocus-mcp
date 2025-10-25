# Claude Code Hook Solutions for All AI Process Issues

**Purpose:** Comprehensive analysis of how to prevent recurrence of all ai-process issues (both open and closed) using Claude Code hooks.

**Last Updated:** 2025-10-25

**Strategy:** When Claude makes a mistake, Claude Code hooks should be our go-to tool for prevention.

---

## Summary Table

| Issue # | Status | Category | Hook Type | Implementation Priority |
|---------|--------|----------|-----------|------------------------|
| #27 | CLOSED | missing-docs | Stop | 🟡 Medium |
| #28 | OPEN | missing-docs | PostToolUse(Edit) | 🟢 Low (automation better) |
| #29 | OPEN | missing-docs | PostToolUse(Edit) | 🟢 Low (automation better) |
| #30 | CLOSED | other | N/A | ✅ Already automated |
| #31 | OPEN | missing-tests | Stop | 🟡 Medium |
| #32 | OPEN | missing-docs | N/A | ✅ Already automated (CI) |
| #33 | CLOSED | other | UserPromptSubmit | 🟡 Medium |
| #34 | OPEN | missing-docs | PostToolUse(Edit) | 🟡 Medium |
| #35 | CLOSED | missing-docs | N/A | ✅ Documented pattern |
| #36 | OPEN | missing-automation | PostToolUse(Bash) | 🔴 High |
| #37 | CLOSED | architecture-violation | PreToolUse(Bash) | 🔴 High |
| #39 | OPEN | missing-automation | PostToolUse(Bash) | 🔴 High (dup of #36) |

**Priority Legend:**
- 🔴 High: Implement in v0.6.2 (immediate fixes for workflow violations)
- 🟡 Medium: Implement in v0.6.3 (process improvements)
- 🟢 Low: Better solved with automation scripts than hooks

---

## Issue #27: Missing MIGRATION_v0.6.md despite CHANGELOG reference

**Category:** missing-docs
**Status:** CLOSED
**Severity:** high

### What Happened
Referenced `MIGRATION_v0.6.md` in CHANGELOG.md but never created the file.

### Hook Solution: Stop Hook

**Hook Type:** `Stop`
**Purpose:** Verify all cross-references exist before completion

```bash
#!/bin/bash
# scripts/hooks/pre_stop.sh (partial)

# Check for broken documentation cross-references
for file in $(git diff --cached --name-only | grep -E '\.(md|txt)$'); do
    # Find all markdown links
    grep -oE '\[.*\]\([^)]+\)' "$file" | while read -r link; do
        # Extract path from [text](path)
        path=$(echo "$link" | sed 's/.*(\([^)]*\)).*/\1/')

        # Skip external URLs
        if [[ "$path" =~ ^https?:// ]]; then
            continue
        fi

        # Check if referenced file exists
        if [ ! -f "$path" ] && [ ! -f "$(dirname "$file")/$path" ]; then
            cat >&2 <<EOF
{
  "decision": "block",
  "reason": "Broken cross-reference detected: $file references $path which doesn't exist",
  "additionalContext": "Create the referenced file or remove the reference before committing."
}
EOF
            exit 2
        fi
    done
done

exit 0
```

**Priority:** 🟡 Medium (catches pattern of broken doc links)

---

## Issue #28: TESTING.md test counts get out of sync

**Category:** missing-docs
**Status:** OPEN
**Severity:** medium

### What Happened
Hardcoded test counts in TESTING.md become stale as tests are added/removed.

### Hook Solution: PostToolUse(Edit) + Automation

**Better solution: Automation script**

Test counts should be generated, not maintained manually. Hook can remind but shouldn't block.

```bash
#!/bin/bash
# scripts/hooks/post_edit.sh (partial)

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Check if editing test files
if [[ "$FILE_PATH" =~ ^tests/.*\.py$ ]]; then
    cat <<EOF
{
  "systemMessage": "⚠️  Test file modified. If adding/removing tests, remember to:\n1. Run: pytest --collect-only -q | tail -1\n2. Update count in docs/guides/TESTING.md if changed\n3. Better: Use ./scripts/generate_test_stats.sh (TODO: create this)"
}
EOF
fi

exit 0
```

**Priority:** 🟢 Low (create `scripts/generate_test_stats.sh` instead)

**Recommended approach:** Automate test count generation rather than using hooks.

---

## Issue #29: Version numbers get out of sync

**Category:** missing-docs
**Status:** OPEN
**Severity:** high

### What Happened
Version in `pyproject.toml` doesn't match version in CHANGELOG.md, CLAUDE.md, README.md.

### Hook Solution: PostToolUse(Edit) + Automation

**Better solution: bump2version or similar**

```bash
#!/bin/bash
# scripts/hooks/post_edit.sh (partial)

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Check if editing pyproject.toml version
if [ "$FILE_PATH" = "pyproject.toml" ]; then
    OLD_STRING=$(echo "$INPUT" | jq -r '.tool_input.old_string // empty')
    NEW_STRING=$(echo "$INPUT" | jq -r '.tool_input.new_string // empty')

    if echo "$OLD_STRING" | grep -q "^version = " || echo "$NEW_STRING" | grep -q "^version = "; then
        # Version changed
        NEW_VERSION=$(echo "$NEW_STRING" | grep '^version = ' | cut -d'"' -f2)

        cat <<EOF
{
  "systemMessage": "⚠️  Version changed to $NEW_VERSION. Remember to update:\n- CHANGELOG.md (add new version section)\n- .claude/CLAUDE.md (Current Version line)\n- README.md (if version appears)\n\nBetter: Use ./scripts/bump_version.sh $NEW_VERSION (TODO: create this)"
}
EOF
    fi
fi

exit 0
```

**Priority:** 🟢 Low (create version management script instead)

**Recommended approach:** Implement `bump2version` or custom script.

---

## Issue #30: Automation script exists but never runs

**Category:** other
**Status:** CLOSED
**Severity:** high

### What Happened
Created `update_metrics.sh` but never integrated it into any automated workflow.

### Hook Solution: N/A - Already Fixed

**Resolution:** Script now runs automatically in git hooks.

**Lesson learned:** All automation scripts must be actually called automatically, not just exist.

**Prevention:** When creating automation scripts, always integrate them into workflow (hooks, CI, cron).

---

## Issue #31: No validation that prevention measures work

**Category:** missing-tests
**Status:** OPEN
**Severity:** critical

### What Happened
Created prevention scripts but never tested that they actually detect mistakes.

### Hook Solution: Stop Hook

**Hook Type:** `Stop`
**Purpose:** Ensure prevention scripts have tests before completion

```bash
#!/bin/bash
# scripts/hooks/pre_stop.sh (partial)

# Check if new prevention scripts have tests
NEW_SCRIPTS=$(git diff --cached --name-only --diff-filter=A | grep -E 'scripts/(check_|verify_)')

if [ -n "$NEW_SCRIPTS" ]; then
    for script in $NEW_SCRIPTS; do
        script_name=$(basename "$script" .sh)

        # Check if test exists
        if [ ! -f "tests/test_$script_name.sh" ]; then
            cat >&2 <<EOF
{
  "decision": "block",
  "reason": "Prevention script $script created without tests",
  "additionalContext": "Create tests/test_$script_name.sh that validates:\n1. Script detects mistake (positive case)\n2. Script allows valid code (negative case)\n\nSee docs/reference/CLAUDE_CODE_HOOKS.md for testing examples."
}
EOF
            exit 2
        fi
    done
fi

exit 0
```

**Priority:** 🟡 Medium (ensures prevention measures are tested)

---

## Issue #32: No recurrence tracking

**Category:** missing-docs
**Status:** OPEN
**Severity:** critical

### What Happened
No mechanism to detect when prevented mistakes recur.

### Hook Solution: N/A - Already Automated

**Resolution:** `scripts/check_recurrence.sh` runs in CI and detects recurrences by executing prevention scripts from issue bodies.

**No hook needed:** CI already handles this automatically.

---

## Issue #33: Started implementation without planning

**Category:** other
**Status:** CLOSED
**Severity:** medium

### What Happened
Started rename implementation without asking about version bump, documentation strategy, or planning full scope.

### Hook Solution: UserPromptSubmit Hook

**Hook Type:** `UserPromptSubmit`
**Purpose:** Inject planning reminder for breaking changes

```bash
#!/bin/bash
# scripts/hooks/user_prompt_submit.sh

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt')

# Check if user requesting breaking change or rename
if echo "$PROMPT" | grep -qiE "rename|breaking change|remove.*function|change.*signature"; then
    cat <<EOF
{
  "additionalContext": "🔔 PLANNING CHECKLIST for Breaking Changes:\n\n1. **Version bump:** Should this be v0.X.0 (breaking) or v0.X.Y (patch)?\n2. **Documentation:** What's the documentation strategy?\n   - Update ROADMAP.md (remove from upcoming, note in current state?)\n   - CHANGELOG.md entry\n   - MIGRATION guide if major version\n3. **Full scope:** List all affected files/docs before starting\n4. **Tests:** Plan test updates along with code changes\n\nSee .claude/CLAUDE.md section 'Common Development Tasks' for full workflow."
}
EOF
fi

exit 0
```

**Priority:** 🟡 Medium (prevents jumping into implementation)

---

## Issue #34: Failed to update ROADMAP.md after fixing bug

**Category:** missing-docs
**Status:** OPEN
**Severity:** medium

### What Happened
Fixed critical bug documented in ROADMAP.md but never removed it from "Upcoming Work".

### Hook Solution: PostToolUse(Edit) Hook

**Hook Type:** `PostToolUse(Edit)` on CHANGELOG.md
**Purpose:** Remind to update ROADMAP.md when documenting bug fixes

```bash
#!/bin/bash
# scripts/hooks/post_edit.sh (partial)

FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Check if editing CHANGELOG.md
if [ "$FILE_PATH" = "CHANGELOG.md" ]; then
    NEW_STRING=$(echo "$INPUT" | jq -r '.tool_input.new_string // empty')

    # Check if adding bug fix entry
    if echo "$NEW_STRING" | grep -qiE "### (fixed|bug)"; then
        cat <<EOF
{
  "systemMessage": "⚠️  Bug fix added to CHANGELOG.md. Remember to:\n1. Check if bug is listed in docs/project/ROADMAP.md\n2. If yes, remove it from 'Upcoming Work' section\n3. Cross-reference: CHANGELOG should match ROADMAP status\n\nSee .claude/CLAUDE.md 'Before Every Commit' checklist."
}
EOF
    fi
fi

exit 0
```

**Priority:** 🟡 Medium (catches ROADMAP drift)

---

## Issue #35: No documented pattern for completed roadmap items

**Category:** missing-docs
**Status:** CLOSED
**Severity:** medium

### What Happened
Unclear where completed "Upcoming Work" items should go in ROADMAP.md.

### Hook Solution: N/A - Documented Pattern

**Resolution:** Pattern now documented in CONTRIBUTING.md:
- Small items: Remove from "Upcoming Work", note in "Current State", document in CHANGELOG
- Major features: Add to "Completed Phases"

**No hook needed:** Clear documentation sufficient.

---

## Issue #36: No proactive GitHub Actions monitoring

**Category:** missing-automation
**Status:** OPEN
**Severity:** medium

### What Happened
Pushed code without monitoring GitHub Actions CI runs. User had to notify me of failures.

### Hook Solution: PostToolUse(Bash) Hook

**Hook Type:** `PostToolUse(Bash)`
**Purpose:** Monitor CI after every `git push`

```bash
#!/bin/bash
# scripts/hooks/post_bash.sh

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // 0')

# Check if this was a successful git push
if echo "$COMMAND" | grep -qE "^git push" && [ "$EXIT_CODE" = "0" ]; then
    echo "🔍 Git push detected. Monitoring GitHub Actions..." >&2

    # Wait for CI to start
    sleep 5

    # Get latest run ID
    RUN_ID=$(gh run list --limit 1 --json databaseId -q '.[0].databaseId')

    if [ -n "$RUN_ID" ]; then
        echo "Watching run #$RUN_ID..." >&2

        # Watch the run with timeout (5 minutes max)
        if ! timeout 300 gh run watch "$RUN_ID" --exit-status 2>&1; then
            # CI failed
            RUN_URL=$(gh run view "$RUN_ID" --json url -q .url)

            cat >&2 <<EOF
{
  "decision": "block",
  "reason": "GitHub Actions CI failed after your push",
  "additionalContext": "View failure details: $RUN_URL\n\nFetch logs with: gh run view $RUN_ID --log-failed\n\nYou must fix CI failures before continuing."
}
EOF
            exit 2
        else
            echo "✅ GitHub Actions passed successfully" >&2
        fi
    else
        echo "⚠️  No GitHub Actions run found. CI may not have triggered." >&2
    fi
fi

exit 0
```

**Priority:** 🔴 High (prevents CI failures going unnoticed)

**Note:** This is the most important hook to prevent user interruptions.

---

## Issue #37: Worked directly on main branch

**Category:** architecture-violation
**Status:** CLOSED
**Severity:** medium

### What Happened
Started work on main branch instead of creating feature branch.

### Hook Solution: PreToolUse(Bash) Hook

**Hook Type:** `PreToolUse(Bash)`
**Purpose:** Block commits to main branch (except hotfixes)

```bash
#!/bin/bash
# scripts/hooks/pre_bash.sh

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')

# Check if this is a git commit command
if echo "$COMMAND" | grep -qE "^git commit"; then
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

    # Block commits to main/master unless it's a hotfix
    if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
        # Check if commit message contains "hotfix" or "emergency"
        if ! echo "$COMMAND" | grep -qiE "hotfix|emergency"; then
            cat >&2 <<EOF
{
  "permissionDecision": "deny",
  "permissionDecisionReason": "❌ Cannot commit directly to $CURRENT_BRANCH branch.\n\nPlease create a feature branch first:\n  git checkout -b feature/description  # For features\n  git checkout -b fix/description      # For bug fixes\n  git checkout -b docs/description     # For documentation\n\nOnly commit to main for:\n  - Hotfixes (include 'hotfix' in commit message)\n  - Emergency rollbacks (include 'emergency' in message)\n\nSee .claude/CLAUDE.md 'Before Starting Work' section."
}
EOF
            exit 2
        fi
    fi
fi

exit 0
```

**Priority:** 🔴 High (enforces workflow discipline)

---

## Issue #39: Did not monitor GitHub Actions after git push

**Category:** missing-automation
**Status:** OPEN
**Severity:** medium

### What Happened
Pushed code but didn't monitor CI run. This is a recurrence of #36.

### Hook Solution: Same as Issue #36

**This is a duplicate of #36.** The PostToolUse(Bash) hook for monitoring CI after `git push` prevents both issues.

**Priority:** 🔴 High (same as #36)

---

## Implementation Plan by Version

### v0.6.2: Hook Infrastructure + Immediate Fixes

**Goal:** Prevent workflow violations (branch management, CI monitoring)

| Hook | Event | Prevents Issue(s) | Priority |
|------|-------|-------------------|----------|
| `pre_bash.sh` | PreToolUse(Bash) | #37: Commits to main | 🔴 High |
| `post_bash.sh` | PostToolUse(Bash) | #36, #39: CI monitoring | 🔴 High |
| `session_start.sh` | SessionStart | N/A: Load context, warn if on main | 🟡 Medium |

**Deliverables:**
1. Create `scripts/hooks/` directory
2. Implement 3 core hooks (above)
3. Configure `.claude/settings.json`
4. Test in informational mode
5. Switch to blocking mode
6. Update issue #37, #36, #39 prevention scripts to check for hooks

### v0.6.3: Process Enforcement

**Goal:** Enforce planning, testing, and documentation workflows

| Hook | Event | Prevents Issue(s) | Priority |
|------|-------|-------------------|----------|
| `user_prompt_submit.sh` | UserPromptSubmit | #33: Planning before implementation | 🟡 Medium |
| `pre_stop.sh` | Stop | #27: Broken cross-refs, #31: Untested prevention | 🟡 Medium |
| `post_edit.sh` | PostToolUse(Edit) | #34: ROADMAP drift, #29: Version sync | 🟡 Medium |

**Deliverables:**
1. Implement 3 process hooks (above)
2. Create hook test suite
3. Update CLAUDE.md with hook expectations
4. Document hook patterns in CONTRIBUTING.md

### Future: Automation Over Hooks

**Issues better solved with automation:**

| Issue | Why Automation > Hooks | Script to Create |
|-------|----------------------|------------------|
| #28 | Test counts should be generated | `scripts/generate_test_stats.sh` |
| #29 | Version bumping should be atomic | `scripts/bump_version.sh` or `bump2version` |
| #32 | Already automated via CI | N/A (done) |
| #30 | Already automated | N/A (done) |

---

## Hook Development Workflow

### Phase 1: Informational (Week 1)
1. Implement hooks with **warnings only** (exit 0, systemMessage)
2. Monitor Claude's behavior and hook output
3. Identify false positives and edge cases
4. Refine hook logic

### Phase 2: Enforcement (Week 2)
1. Switch to **blocking mode** (exit 2, decision: "block")
2. Document any issues Claude encounters
3. Adjust error messages for clarity
4. Verify CI detects missing hooks

### Phase 3: Validation (Week 3)
1. Update issue prevention scripts to check for hooks
2. Verify CI fails if hooks are missing
3. Monitor for recurrences
4. Document lessons learned

---

## Testing Strategy for Hooks

### Manual Testing

```bash
# Test PreToolUse hook (branch validation)
echo '{
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {"command": "git commit -m \"test\""},
  "cwd": "'$(pwd)'"
}' | ./scripts/hooks/pre_bash.sh

# Test PostToolUse hook (CI monitoring)
echo '{
  "hook_event_name": "PostToolUse",
  "tool_name": "Bash",
  "tool_input": {"command": "git push origin main"},
  "tool_response": {"exit_code": 0},
  "cwd": "'$(pwd)'"
}' | ./scripts/hooks/post_bash.sh

# Test UserPromptSubmit hook (planning reminder)
echo '{
  "hook_event_name": "UserPromptSubmit",
  "prompt": "Rename the client module to connector",
  "cwd": "'$(pwd)'"
}' | ./scripts/hooks/user_prompt_submit.sh
```

### Automated Testing

Create `tests/test_hooks.sh`:

```bash
#!/bin/bash
set -e

echo "Testing Claude Code hooks..."

# Test 1: Branch validation blocks commits on main
echo "Test: Block commit on main branch"
git checkout main
RESULT=$(echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"test\""}}' | \
  ./scripts/hooks/pre_bash.sh 2>&1)
if [ $? -eq 2 ]; then
    echo "✅ PASS: Commit blocked on main branch"
else
    echo "❌ FAIL: Commit should be blocked on main branch"
    exit 1
fi

# Test 2: Branch validation allows commits on feature branch
echo "Test: Allow commit on feature branch"
git checkout -b test-branch 2>/dev/null || git checkout test-branch
RESULT=$(echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"test\""}}' | \
  ./scripts/hooks/pre_bash.sh 2>&1)
if [ $? -eq 0 ]; then
    echo "✅ PASS: Commit allowed on feature branch"
else
    echo "❌ FAIL: Commit should be allowed on feature branch"
    exit 1
fi

git checkout main
git branch -D test-branch 2>/dev/null || true

echo "All hook tests passed!"
```

---

## Prevention Script Updates

After implementing hooks, update issue prevention scripts:

### Issue #37 Prevention Script

```bash
# Check if pre_bash.sh hook exists and is enabled
if [ -f "scripts/hooks/pre_bash.sh" ] && \
   grep -q "pre_bash.sh" .claude/settings.json; then
    # Verify it actually blocks commits to main
    echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"test\""}}' | \
      ./scripts/hooks/pre_bash.sh &>/dev/null
    if [ $? -eq 2 ]; then
        exit 0  # Hook working correctly
    fi
fi
exit 1  # Hook missing or not working
```

### Issue #36/#39 Prevention Script

```bash
# Check if post_bash.sh hook exists and monitors CI
if [ -f "scripts/hooks/post_bash.sh" ] && \
   grep -q "post_bash.sh" .claude/settings.json; then
    # Verify it monitors git push
    if grep -q "gh run watch" scripts/hooks/post_bash.sh; then
        exit 0  # Hook configured correctly
    fi
fi
exit 1  # Hook missing or not configured
```

---

## Success Metrics

**v0.6.2 Success Criteria:**
- [ ] Claude blocked from committing to main (issue #37 prevention working)
- [ ] Claude monitors CI after every push (issues #36, #39 prevention working)
- [ ] CI detects if hooks are missing (prevention scripts updated)
- [ ] Zero user interruptions for CI failures (1 week observation)
- [ ] Zero commits to main without feature branch (1 week observation)

**v0.6.3 Success Criteria:**
- [ ] Claude asks about planning before breaking changes (issue #33 prevention)
- [ ] Claude reminded about ROADMAP updates when editing CHANGELOG (issue #34 prevention)
- [ ] Claude blocked from completing with broken cross-references (issue #27 prevention)
- [ ] All prevention scripts have automated tests (issue #31 prevention)

---

## Key Insights

### 1. Hook Priority Ranking

**Highest value hooks (implement first):**
1. **PostToolUse(Bash) for CI monitoring** - Prevents user interruptions (issues #36, #39)
2. **PreToolUse(Bash) for branch validation** - Enforces workflow discipline (issue #37)
3. **UserPromptSubmit for planning** - Prevents premature implementation (issue #33)

**Medium value hooks (implement second):**
4. **Stop for validation** - Catches incomplete work before completion (issues #27, #31)
5. **PostToolUse(Edit) for doc sync** - Reminds about cross-references (issue #34)

**Lower value (automation better):**
6. Issues #28, #29 - Better solved with generation scripts than hooks

### 2. Hooks vs Automation Decision Tree

**Use hooks when:**
- ✅ Need to enforce workflow during Claude Code session
- ✅ Decision requires context from current work
- ✅ Want to block Claude from continuing until fixed

**Use automation when:**
- ✅ Information can be generated from source of truth
- ✅ Same check applies to all contributors (human and AI)
- ✅ Can run in CI or git hooks universally

### 3. Closed Issues Still Need Hooks

**Critical insight:** Closed issues (#27, #30, #33, #35, #37) still need hook prevention to prevent recurrence in future sessions. Claude doesn't remember past mistakes across sessions.

**Pattern:** Closed issue = successful one-time fix. Hook = permanent prevention.

---

## Next Steps

1. **Create issues for v0.6.2:**
   - "Implement PreToolUse(Bash) hook for branch validation (#37)"
   - "Implement PostToolUse(Bash) hook for CI monitoring (#36, #39)"
   - "Implement SessionStart hook for project context loading"

2. **Create issues for v0.6.3:**
   - "Implement UserPromptSubmit hook for planning reminders (#33)"
   - "Implement Stop hook for completion validation (#27, #31)"
   - "Implement PostToolUse(Edit) hook for documentation sync (#34)"

3. **Assign to milestones:**
   - v0.6.2: High priority hooks (branch, CI)
   - v0.6.3: Process enforcement hooks (planning, validation, docs)

4. **Begin implementation:**
   - Start with informational mode
   - Test thoroughly
   - Switch to blocking mode
   - Update prevention scripts in issues
