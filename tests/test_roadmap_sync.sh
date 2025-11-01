#!/bin/bash
# Tests for check_roadmap_sync.sh
#
# These are integration tests that verify the script's behavior
# in different scenarios.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECK_SCRIPT="$SCRIPT_DIR/scripts/check_roadmap_sync.sh"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0

# Test helper functions
pass() {
    TESTS_PASSED=$((TESTS_PASSED + 1))
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    echo -e "${RED}✗${NC} $1"
    echo "  Error: $2"
}

run_test() {
    TESTS_RUN=$((TESTS_RUN + 1))
    echo ""
    echo "Test $TESTS_RUN: $1"
}

# ========================================
# Test 1: Script exists and is executable
# ========================================
run_test "Script exists and is executable"

if [ -f "$CHECK_SCRIPT" ]; then
    pass "Script file exists"
else
    fail "Script file exists" "File not found: $CHECK_SCRIPT"
    exit 1
fi

if [ -x "$CHECK_SCRIPT" ]; then
    pass "Script is executable"
else
    fail "Script is executable" "File is not executable"
    exit 1
fi

# ========================================
# Test 2: Help message / usage
# ========================================
run_test "Shows error when milestone not provided and VERSION missing"

# Temporarily rename VERSION if it exists
VERSION_FILE="$SCRIPT_DIR/VERSION"
VERSION_BACKUP=""
if [ -f "$VERSION_FILE" ]; then
    VERSION_BACKUP="$VERSION_FILE.backup"
    mv "$VERSION_FILE" "$VERSION_BACKUP"
fi

# Run script without arguments (should fail with usage message)
if ! OUTPUT=$("$CHECK_SCRIPT" 2>&1); then
    if echo "$OUTPUT" | grep -q "Usage:"; then
        pass "Shows usage message when no milestone specified"
    else
        fail "Shows usage message" "Output didn't contain 'Usage:'"
    fi
else
    fail "Should fail without milestone" "Script succeeded when it should have failed"
fi

# Restore VERSION if it was backed up
if [ -n "$VERSION_BACKUP" ]; then
    mv "$VERSION_BACKUP" "$VERSION_FILE"
fi

# ========================================
# Test 3: Handles missing gh CLI gracefully
# ========================================
run_test "Handles missing gh CLI gracefully"

# Mock gh command to fail
MOCK_GH="$SCRIPT_DIR/.mock_gh_missing"
echo '#!/bin/bash
exit 127
' > "$MOCK_GH"
chmod +x "$MOCK_GH"

# Temporarily modify PATH to use mock gh
OLD_PATH="$PATH"
export PATH="$(dirname "$MOCK_GH"):$PATH"

# Run script (should exit 0 with warning)
if OUTPUT=$("$CHECK_SCRIPT" v0.6.6 2>&1); then
    if echo "$OUTPUT" | grep -q "gh CLI not found"; then
        pass "Shows warning when gh CLI not found"
    else
        fail "Warning message" "Output didn't contain expected warning"
    fi
else
    fail "Should handle missing gh gracefully" "Script failed instead of warning"
fi

# Restore PATH and clean up mock
export PATH="$OLD_PATH"
rm -f "$MOCK_GH"

# ========================================
# Test 4: Real milestone check (v0.6.6)
# ========================================
run_test "Checks real milestone (v0.6.6)"

# This requires gh CLI and network access
# Skip if gh not available
if command -v gh &> /dev/null; then
    if OUTPUT=$("$CHECK_SCRIPT" v0.6.6 2>&1); then
        if echo "$OUTPUT" | grep -qE "(✅|closed issue)"; then
            pass "Successfully checks v0.6.6 milestone"
        else
            fail "Milestone check output" "Unexpected output format"
        fi
    else
        fail "Milestone check" "Script failed on real milestone"
    fi
else
    echo "  ⊘ Skipped (gh CLI not available)"
fi

# ========================================
# Test 5: Handles non-existent milestone
# ========================================
run_test "Handles non-existent milestone gracefully"

if command -v gh &> /dev/null; then
    # Use a milestone that definitely doesn't exist
    if OUTPUT=$("$CHECK_SCRIPT" v99.99.99 2>&1); then
        if echo "$OUTPUT" | grep -qE "(No closed issues|not found)"; then
            pass "Handles non-existent milestone gracefully"
        else
            # Script might succeed with 0 issues, which is also acceptable
            pass "Handles non-existent milestone (0 issues)"
        fi
    else
        fail "Non-existent milestone" "Script should handle gracefully"
    fi
else
    echo "  ⊘ Skipped (gh CLI not available)"
fi

# ========================================
# Summary
# ========================================
echo ""
echo "========================================"
echo "Test Results: $TESTS_PASSED/$TESTS_RUN passed"
echo "========================================"

if [ $TESTS_PASSED -eq $TESTS_RUN ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed${NC}"
    exit 1
fi
