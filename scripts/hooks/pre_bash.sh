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

    # Block commits to main/master unless it's a hotfix
    if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
        # Check if commit message contains "hotfix" or "emergency"
        if ! echo "$COMMAND" | grep -qiE "hotfix|emergency"; then
            # Block the commit
            cat >&2 <<'EOF'
{
  "permissionDecision": "deny",
  "permissionDecisionReason": "❌ Cannot commit directly to main branch.\n\nPlease create a feature branch first:\n  git checkout -b feature/description  # For features\n  git checkout -b fix/description      # For bug fixes\n  git checkout -b docs/description     # For documentation\n\nOnly commit to main for:\n  - Hotfixes (include 'hotfix' in commit message)\n  - Emergency rollbacks (include 'emergency' in message)\n\nSee .claude/CLAUDE.md 'Before Starting Work' section."
}
EOF
            return 2
        fi
    fi

    return 0
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
