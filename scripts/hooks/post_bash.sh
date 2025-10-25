#!/bin/bash
# PostToolUse hook for Bash commands
# Runs multiple checks after Bash tool execution
#
# To add new checks:
# 1. Create a new check_* function below
# 2. Add function name to CHECKS array
# 3. Function should return 0 (allow) or 2 (block with error on stderr)

# Read JSON input from stdin
INPUT=$(cat)

# Extract command and exit code
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command')
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // 0')

# ===================================================
# CHECK: Monitor CI after git push
# Related issues: #36, #39, #42
# ===================================================
check_monitor_ci_after_push() {
    # Only check successful git push commands
    if ! echo "$COMMAND" | grep -qE "^git push" || [ "$EXIT_CODE" != "0" ]; then
        return 0
    fi

    echo "🔍 Git push detected. Monitoring GitHub Actions..." >&2

    # Wait for CI to start
    sleep 5

    # Check if gh CLI is available
    if ! command -v gh &> /dev/null; then
        echo "⚠️  gh CLI not found. Skipping GitHub Actions monitoring." >&2
        echo "Install: brew install gh" >&2
        return 0
    fi

    # Get latest run ID
    RUN_ID=$(gh run list --limit 1 --json databaseId -q '.[0].databaseId' 2>/dev/null)

    if [ -n "$RUN_ID" ]; then
        echo "Watching run #$RUN_ID..." >&2

        # Watch the run (gh run watch has built-in timeout)
        if ! gh run watch "$RUN_ID" --exit-status 2>&1; then
            # CI failed
            RUN_URL=$(gh run view "$RUN_ID" --json url -q .url 2>/dev/null || echo "Unable to get URL")

            cat >&2 <<EOF
{
  "decision": "block",
  "reason": "GitHub Actions CI failed after your push",
  "additionalContext": "View failure details: $RUN_URL\n\nFetch logs with: gh run view $RUN_ID --log-failed\n\nYou must fix CI failures before continuing."
}
EOF
            return 2
        else
            echo "✅ GitHub Actions passed successfully" >&2
        fi
    else
        echo "⚠️  No GitHub Actions run found. CI may not have triggered." >&2
        REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[:/]\(.*\)\.git/\1/')
        echo "Check manually: https://github.com/$REPO/actions" >&2
    fi

    return 0
}

# ===================================================
# Add new checks here as functions
# ===================================================

# Future checks (add as needed):
# check_test_output() - Parse test results and warn about failures
# check_lint_output() - Parse linter output
# check_build_output() - Parse build output
# etc.

# ===================================================
# Run all checks
# ===================================================

# Array of check functions to run
CHECKS=(
    check_monitor_ci_after_push
    # Add more checks here
)

# Run each check in order
for check in "${CHECKS[@]}"; do
    $check
    CHECK_EXIT=$?

    if [ $CHECK_EXIT -ne 0 ]; then
        # Check failed - exit with its exit code
        exit $CHECK_EXIT
    fi
done

# All checks passed
exit 0
