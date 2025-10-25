#!/bin/bash
# Test suite for Claude Code hooks
#
# Tests hook logic without switching branches (which would make hooks disappear)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "========================================="
echo "Testing Claude Code Hooks"
echo "========================================="
echo ""

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
    if [ -n "$2" ]; then
        echo "   Details: $2"
    fi
    ((TESTS_FAILED++))
    ((TESTS_RUN++))
}

# Get current branch for context
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
echo "Current branch: $CURRENT_BRANCH"
echo ""

# ===========================================
# Test 1: pre_bash.sh allows non-commit commands
# ===========================================
echo "Test 1: pre_bash.sh allows non-commit commands"

RESULT=$(echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | ./scripts/hooks/pre_bash.sh 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    pass "Non-commit command allowed"
else
    fail "Non-commit commands should always be allowed" "Exit code: $EXIT_CODE"
fi

# ===========================================
# Test 2: pre_bash.sh allows commits on current branch
# ===========================================
echo "Test 2: pre_bash.sh allows commits on current branch ($CURRENT_BRANCH)"

RESULT=$(echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"test\""}}' | ./scripts/hooks/pre_bash.sh 2>&1)
EXIT_CODE=$?

# Should allow on feature/non-main branch
if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
    if [ $EXIT_CODE -eq 0 ]; then
        pass "Commit allowed on feature branch"
    else
        fail "Commits should be allowed on feature branches" "Exit code: $EXIT_CODE"
    fi
else
    # If on main, should block
    if [ $EXIT_CODE -eq 2 ]; then
        pass "Commit blocked on main branch (as expected)"
    else
        fail "Commits should be blocked on main" "Exit code: $EXIT_CODE"
    fi
fi

# ===========================================
# Test 3: pre_bash.sh parses git commit commands correctly
# ===========================================
echo "Test 3: pre_bash.sh parses various commit command formats"

for cmd in 'git commit -m "test"' 'git commit -am "test"' 'git commit --amend'; do
    RESULT=$(echo "{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"$cmd\"}}" | ./scripts/hooks/pre_bash.sh 2>&1)
    EXIT_CODE=$?

    # On feature branch, all should pass
    if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ] && [ $EXIT_CODE -ne 0 ]; then
        fail "Hook should parse: $cmd" "Exit code: $EXIT_CODE"
        break
    fi
done

if [ "$CURRENT_BRANCH" != "main" ] && [ "$CURRENT_BRANCH" != "master" ]; then
    pass "All commit command formats parsed correctly"
fi

# ===========================================
# Test 4: post_bash.sh allows non-push commands
# ===========================================
echo "Test 4: post_bash.sh allows non-push commands"

RESULT=$(echo '{"tool_name":"Bash","tool_input":{"command":"git status"},"tool_response":{"exit_code":0}}' | ./scripts/hooks/post_bash.sh 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    pass "Non-push command allowed"
else
    fail "Non-push commands should always be allowed" "Exit code: $EXIT_CODE"
fi

# ===========================================
# Test 5: post_bash.sh ignores failed pushes
# ===========================================
echo "Test 5: post_bash.sh ignores failed git push"

# A failed push (exit_code: 1) should not trigger monitoring
RESULT=$(echo '{"tool_name":"Bash","tool_input":{"command":"git push origin test"},"tool_response":{"exit_code":1}}' | ./scripts/hooks/post_bash.sh 2>&1)
EXIT_CODE=$?

# Should exit 0 because push failed, no monitoring needed
if [ $EXIT_CODE -eq 0 ]; then
    pass "Hook correctly ignores failed git push"
else
    fail "Hook should ignore failed git push" "Exit code: $EXIT_CODE"
fi

# ===========================================
# Test 6: session_start.sh returns valid JSON
# ===========================================
echo "Test 6: session_start.sh returns valid JSON"

RESULT=$(echo '{"hook_event_name":"SessionStart","source":"startup","cwd":"'$(pwd)'"}' | ./scripts/hooks/session_start.sh 2>/dev/null)
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
    fail "session_start.sh should return valid JSON" "Exit code: $EXIT_CODE"
fi

# ===========================================
# Test 7: session_start.sh includes current branch
# ===========================================
echo "Test 7: session_start.sh includes current branch info"

RESULT=$(echo '{"hook_event_name":"SessionStart","source":"startup"}' | ./scripts/hooks/session_start.sh 2>/dev/null)

if echo "$RESULT" | jq -r '.additionalContext' | grep -q "$CURRENT_BRANCH"; then
    pass "session_start.sh includes current branch ($CURRENT_BRANCH)"
else
    fail "session_start.sh should include current branch"
fi

# ===========================================
# Test 8: All hook scripts are executable
# ===========================================
echo "Test 8: All hook scripts are executable"

HOOKS_EXECUTABLE=true
for hook in scripts/hooks/*.sh; do
    if [ ! -x "$hook" ]; then
        fail "Hook not executable: $hook"
        HOOKS_EXECUTABLE=false
    fi
done

if [ "$HOOKS_EXECUTABLE" = true ]; then
    pass "All hook scripts are executable"
fi

# ===========================================
# Test 9: .claude/settings.json is valid
# ===========================================
echo "Test 9: .claude/settings.json is valid JSON"

if jq -e . .claude/settings.json >/dev/null 2>&1; then
    # Check if has hooks configuration
    if jq -e '.hooks' .claude/settings.json >/dev/null 2>&1; then
        pass ".claude/settings.json is valid and has hooks config"
    else
        fail ".claude/settings.json missing hooks configuration"
    fi
else
    fail ".claude/settings.json is not valid JSON"
fi

# ===========================================
# Test 10: All configured hooks exist
# ===========================================
echo "Test 10: All hooks referenced in settings.json exist"

ALL_HOOKS_EXIST=true

# Check PreToolUse hooks
PRE_HOOKS=$(jq -r '.hooks.PreToolUse[]?.hooks[]?.command // empty' .claude/settings.json 2>/dev/null)
for hook_cmd in $PRE_HOOKS; do
    if [ ! -f "$hook_cmd" ]; then
        fail "Hook referenced in settings.json doesn't exist: $hook_cmd"
        ALL_HOOKS_EXIST=false
    fi
done

# Check PostToolUse hooks
POST_HOOKS=$(jq -r '.hooks.PostToolUse[]?.hooks[]?.command // empty' .claude/settings.json 2>/dev/null)
for hook_cmd in $POST_HOOKS; do
    if [ ! -f "$hook_cmd" ]; then
        fail "Hook referenced in settings.json doesn't exist: $hook_cmd"
        ALL_HOOKS_EXIST=false
    fi
done

# Check SessionStart hooks
SESSION_HOOKS=$(jq -r '.hooks.SessionStart[]?.hooks[]?.command // empty' .claude/settings.json 2>/dev/null)
for hook_cmd in $SESSION_HOOKS; do
    if [ ! -f "$hook_cmd" ]; then
        fail "Hook referenced in settings.json doesn't exist: $hook_cmd"
        ALL_HOOKS_EXIST=false
    fi
done

if [ "$ALL_HOOKS_EXIST" = true ]; then
    pass "All hooks referenced in settings.json exist"
fi

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
    echo ""
    echo "Note: To fully test branch blocking, commit to main would be blocked"
    echo "by the hook. This test suite runs on the feature branch where commits"
    echo "are allowed."
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi
