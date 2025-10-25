#!/bin/bash
# PreToolUse hook for Bash commands
# Runs multiple checks before Bash tool execution
#
# To add new checks:
# 1. Create a new check_* function below
# 2. Add function name to CHECKS array
# 3. Function should return 0 (allow) or 2 (block with error on stderr)

# Read JSON input from stdin
INPUT=$(cat)

# Extract command from tool input
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')

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
