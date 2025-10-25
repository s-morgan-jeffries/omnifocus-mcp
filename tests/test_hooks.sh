#!/bin/bash
# Test suite for Claude Code hooks
#
# Tests all hooks to ensure they work correctly before enabling in production

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "========================================="
echo "Testing Claude Code Hooks"
echo "========================================="
echo ""

# Save current branch
ORIGINAL_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
pass() {
    echo "✅ PASS: $1"
    ((TESTS_PASSED++))
    ((TESTS_RUN++))
}

fail() {
    echo "❌ FAIL: $1"
    ((TESTS_FAILED++))
    ((TESTS_RUN++))
}

# ===========================================
# Test 1: pre_bash.sh blocks commits on main
# ===========================================
echo "Test 1: pre_bash.sh blocks commits on main branch"

# Switch to main
git checkout main 2>/dev/null || git checkout master 2>/dev/null

# Test blocking
RESULT=$(echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "git commit -m \"test\""}
}' | ./scripts/hooks/pre_bash.sh 2>&1)

EXIT_CODE=$?

if [ $EXIT_CODE -eq 2 ] && echo "$RESULT" | grep -q "Cannot commit directly to main"; then
    pass "Commit blocked on main branch"
else
    fail "Commit should be blocked on main branch (exit code: $EXIT_CODE)"
fi

# ===========================================
# Test 2: pre_bash.sh allows hotfix commits on main
# ===========================================
echo "Test 2: pre_bash.sh allows hotfix commits on main"

RESULT=$(echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "git commit -m \"hotfix: critical bug\""}
}' | ./scripts/hooks/pre_bash.sh 2>&1)

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    pass "Hotfix commit allowed on main branch"
else
    fail "Hotfix commit should be allowed on main branch (exit code: $EXIT_CODE)"
fi

# ===========================================
# Test 3: pre_bash.sh allows commits on feature branch
# ===========================================
echo "Test 3: pre_bash.sh allows commits on feature branch"

# Create and switch to test branch
git checkout -b test-hooks-branch 2>/dev/null || git checkout test-hooks-branch 2>/dev/null

RESULT=$(echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "git commit -m \"test\""}
}' | ./scripts/hooks/pre_bash.sh 2>&1)

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    pass "Commit allowed on feature branch"
else
    fail "Commit should be allowed on feature branch (exit code: $EXIT_CODE)"
fi

# ===========================================
# Test 4: pre_bash.sh allows non-commit commands
# ===========================================
echo "Test 4: pre_bash.sh allows non-commit commands"

RESULT=$(echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "ls -la"}
}' | ./scripts/hooks/pre_bash.sh 2>&1)

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    pass "Non-commit command allowed"
else
    fail "Non-commit commands should always be allowed (exit code: $EXIT_CODE)"
fi

# ===========================================
# Test 5: post_bash.sh allows non-push commands
# ===========================================
echo "Test 5: post_bash.sh allows non-push commands"

RESULT=$(echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "git status"},
  "tool_response": {"exit_code": 0}
}' | ./scripts/hooks/post_bash.sh 2>&1)

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    pass "Non-push command allowed"
else
    fail "Non-push commands should always be allowed (exit code: $EXIT_CODE)"
fi

# ===========================================
# Test 6: post_bash.sh detects git push
# ===========================================
echo "Test 6: post_bash.sh detects git push (dry run)"

# Note: This test doesn't actually push, just checks detection
# We can't test full CI monitoring without actually pushing
# MacOS doesn't have timeout, so we just test failed push (which skips monitoring)
RESULT=$(echo '{
  "tool_name": "Bash",
  "tool_input": {"command": "git push origin test-branch"},
  "tool_response": {"exit_code": 1}
}' | ./scripts/hooks/post_bash.sh 2>&1)

EXIT_CODE=$?

# Should exit 0 because push failed (exit_code: 1), so hook doesn't monitor
if [ $EXIT_CODE -eq 0 ]; then
    pass "Hook correctly ignores failed git push"
else
    fail "Hook should ignore failed git push (exit code: $EXIT_CODE)"
fi

# ===========================================
# Test 7: session_start.sh returns valid JSON
# ===========================================
echo "Test 7: session_start.sh returns valid JSON"

RESULT=$(echo '{
  "hook_event_name": "SessionStart",
  "source": "startup",
  "cwd": "'$(pwd)'"
}' | ./scripts/hooks/session_start.sh 2>/dev/null)

EXIT_CODE=$?

# Check if valid JSON
if [ $EXIT_CODE -eq 0 ] && echo "$RESULT" | jq -e . >/dev/null 2>&1; then
    # Check if has additionalContext field
    if echo "$RESULT" | jq -e '.additionalContext' >/dev/null 2>&1; then
        pass "session_start.sh returns valid JSON with additionalContext"
    else
        fail "session_start.sh JSON missing additionalContext field"
    fi
else
    fail "session_start.sh should return valid JSON (exit code: $EXIT_CODE)"
fi

# ===========================================
# Test 8: session_start.sh warns if on main
# ===========================================
echo "Test 8: session_start.sh warns if on main branch"

git checkout main 2>/dev/null || git checkout master 2>/dev/null

RESULT=$(echo '{
  "hook_event_name": "SessionStart",
  "source": "startup"
}' | ./scripts/hooks/session_start.sh 2>/dev/null)

if echo "$RESULT" | jq -r '.additionalContext' | grep -q "WARNING.*main"; then
    pass "session_start.sh warns when on main branch"
else
    fail "session_start.sh should warn when on main branch"
fi

# ===========================================
# Cleanup
# ===========================================
echo ""
echo "Cleaning up..."

# Return to original branch
git checkout "$ORIGINAL_BRANCH" 2>/dev/null || true

# Delete test branch if it exists
git branch -D test-hooks-branch 2>/dev/null || true

# ===========================================
# Summary
# ===========================================
echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo "Tests run:    $TESTS_RUN"
echo "Tests passed: $TESTS_PASSED"
echo "Tests failed: $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "✅ All tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi
