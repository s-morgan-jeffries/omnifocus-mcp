#!/bin/bash
# PreToolUse hook for Bash commands
# Runs multiple checks before Bash tool execution
#
# IMPORTANT: Hook configuration is loaded at session start.
# After modifying this script or .claude/settings.json, restart Claude Code
# for changes to take effect. Changes won't apply to current session.
#
# To add new checks:
# 1. Create a new check_* function below
# 2. Add function name to CHECKS array
# 3. Function should return 0 (allow) or 2 (block with error on stderr)
# 4. Test manually: echo '{"tool_input":{"command":"test"}}' | ./scripts/hooks/pre_bash.sh
# 5. Restart Claude Code session to activate

# Read JSON input from stdin
INPUT=$(cat)

# Extract command from tool input
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')

# DEBUG: Log all hook invocations
echo "=== Hook invoked at $(date) ===" >> /tmp/pre_bash_hook.log
echo "Command: $COMMAND" >> /tmp/pre_bash_hook.log

# ===================================================
# CHECK: Prevent commits to main branch
# Related issues: #37, #41
# ===================================================
check_no_commits_to_main() {
    # Only check git commit commands
    if ! echo "$COMMAND" | grep -qE "^git commit"; then
        return 0
    fi

    # Get current branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

    # Allow commits to release/* branches (for release preparation)
    if [[ "$CURRENT_BRANCH" =~ ^release/ ]]; then
        return 0
    fi

    # Block commits to main/master unless it's a hotfix
    if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
        # Check if commit message contains "hotfix" or "emergency"
        if ! echo "$COMMAND" | grep -qiE "hotfix|emergency"; then
            # Block the commit
            cat >&2 <<'EOF'
{
  "permissionDecision": "deny",
  "permissionDecisionReason": "❌ Cannot commit directly to main branch.\n\nPlease create a feature branch first:\n  git checkout -b feature/description  # For features\n  git checkout -b fix/description      # For bug fixes\n  git checkout -b docs/description     # For documentation\n  git checkout -b release/v0.6.x       # For release preparation\n\nOnly commit to main for:\n  - Hotfixes (include 'hotfix' in commit message)\n  - Emergency rollbacks (include 'emergency' in message)\n\nSee .claude/CLAUDE.md 'Before Starting Work' section."
}
EOF
            return 2
        fi
    fi

    return 0
}

# ===================================================
# CHECK: Enforce release hygiene for RC tags
# Related issues: #46, #29
# ===================================================
check_rc_tag_hygiene() {
    # Only check git tag commands
    if ! echo "$COMMAND" | grep -qE "^git tag"; then
        return 0
    fi

    # Extract tag name from command
    TAG_NAME=$(echo "$COMMAND" | sed -n 's/^git tag \([^ ]*\).*/\1/p')

    # Check if it's an RC tag (v0.6.3-rc1, etc.)
    if ! echo "$TAG_NAME" | grep -qE "^v[0-9]+\.[0-9]+\.[0-9]+-rc[0-9]+$"; then
        # Not an RC tag, allow it
        return 0
    fi

    cat >&2 <<EOF
{
  "permissionDecision": "deny",
  "permissionDecisionReason": "🔍 RC tag detected: $TAG_NAME\n\n❌ Cannot create RC tag directly.\n\nUse the git pre-tag hook instead:\n  1. Install git hooks: ./scripts/install-git-hooks.sh\n  2. Create tag: git tag $TAG_NAME\n\nThe git pre-tag hook will:\n  ✅ Run all automated checks (tests, version sync, complexity, milestone)\n  ⚠️  Remind you to verify manual review items\n  🚀 Allow tag creation after confirmation\n\nWhy? Git hooks can run expensive checks (tests, CI verification) without\nblocking Claude Code. Claude Code hooks are for quick validations only.\n\nAlternatively, if you've already run the checks manually:\n  git tag $TAG_NAME  # Run in terminal, not through Claude Code"
}
EOF
    return 2
}

# ===================================================
# CHECK: Verify acceptance criteria before closing issues
# Related issues: #63, #66
# ===================================================
check_issue_close_criteria() {
    # Only check gh issue close commands
    if ! echo "$COMMAND" | grep -qE "gh issue close"; then
        return 0
    fi

    # Allow bypass with CLAUDE_VERIFIED=1 environment variable
    if echo "$COMMAND" | grep -qE "^CLAUDE_VERIFIED=1 "; then
        return 0
    fi

    # Extract issue number from command
    ISSUE_NUM=$(echo "$COMMAND" | sed -n 's/.*gh issue close \([0-9]*\).*/\1/p')

    # Block and prompt Claude to verify with user
    cat >&2 <<EOF
{
  "permissionDecision": "deny",
  "permissionDecisionReason": "🔍 Attempting to close issue #${ISSUE_NUM}\n\n**BLOCKED: Acceptance criteria verification required**\n\nBefore closing this issue, you MUST:\n\n1. ✅ Check the issue's acceptance criteria on GitHub\n2. ✅ Verify ALL criteria are complete (not 'deferred' or 'partial')\n3. ✅ Create tracking issues for any incomplete criteria\n4. ✅ Include verification in closing comment\n\n**Required closing comment format:**\n\`\`\`\nCompleted all acceptance criteria:\n- ✅ Criterion 1: Description (commit abc123)\n- ✅ Criterion 2: Description (commit def456)\n- ⏳ Criterion 3: Deferred to #XX (reason)\n\`\`\`\n\n**Next steps:**\n1. Fetch issue #${ISSUE_NUM} to review acceptance criteria\n2. Verify each criterion is addressed\n3. Create tracking issues for incomplete items (if any)\n4. Ask user: 'I've verified all acceptance criteria for #${ISSUE_NUM}. The closing comment includes verification. Proceed with closing?'\n5. **After user approval**, retry with: CLAUDE_VERIFIED=1 gh issue close ${ISSUE_NUM} --comment \"...\"\n\nSee .claude/CLAUDE.md 'Before Closing Issues' section."
}
EOF
    # Return code 2 = blocking error (Claude must address)
    return 2
}

# ===================================================
# Add new checks here as functions
# ===================================================

# Future checks (add as needed):
# check_dangerous_commands() - Block rm -rf, etc.
# check_permission_files() - Warn about .env, credentials.json
# etc.

# ===================================================
# Run all checks
# ===================================================

# Array of check functions to run
CHECKS=(
    check_no_commits_to_main
    check_rc_tag_hygiene
    check_issue_close_criteria
    # Add more checks here
)

# Run each check in order
for check in "${CHECKS[@]}"; do
    $check
    EXIT_CODE=$?

    if [ $EXIT_CODE -ne 0 ]; then
        # Check failed - exit with its exit code
        exit $EXIT_CODE
    fi
done

# All checks passed
exit 0
