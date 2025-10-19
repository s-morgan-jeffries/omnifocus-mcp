#!/bin/bash
# Test that prevention measures actually detect their target mistakes
# Addresses MISTAKE-007: No validation that prevention measures work
#
# This script creates test scenarios for each prevention measure and verifies
# that the prevention script correctly detects the mistake pattern.

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🧪 Testing Prevention Measures"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

TESTS_PASSED=0
TESTS_FAILED=0
TEST_RESULTS=()

# Test helper functions
test_prevention() {
    local test_name="$1"
    local test_func="$2"

    echo "Testing: $test_name"
    if $test_func; then
        echo "  ✅ PASS"
        ((TESTS_PASSED++))
        TEST_RESULTS+=("✅ $test_name")
    else
        echo "  ❌ FAIL"
        ((TESTS_FAILED++))
        TEST_RESULTS+=("❌ $test_name")
    fi
    echo ""
}

cleanup_test_dir() {
    local dir="$1"
    if [ -d "$dir" ]; then
        rm -rf "$dir"
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MISTAKE-001 Prevention: Version Sync Detection
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

test_version_sync_detects_mismatch() {
    local test_dir="/tmp/mistake_001_test_$$"
    cleanup_test_dir "$test_dir"

    # Create test directory with mismatched versions
    mkdir -p "$test_dir"
    echo 'version = "1.0.0"' > "$test_dir/pyproject.toml"
    echo '**Current Version:** v1.0.1' > "$test_dir/CLAUDE.md"
    echo '## [1.0.2]' > "$test_dir/CHANGELOG.md"
    echo 'v1.0.3' > "$test_dir/README.md"

    # Run check_version_sync.sh in test directory
    cd "$test_dir"
    cp "$PROJECT_ROOT/scripts/check_version_sync.sh" .

    # Script should FAIL (exit 1) because versions don't match
    if ./check_version_sync.sh > /dev/null 2>&1; then
        # Script passed when it should have failed
        cleanup_test_dir "$test_dir"
        return 1
    else
        # Script correctly detected mismatch
        cleanup_test_dir "$test_dir"
        return 0
    fi
}

test_version_sync_allows_matching_versions() {
    local test_dir="/tmp/mistake_001_test_match_$$"
    cleanup_test_dir "$test_dir"

    # Create test directory with MATCHING versions
    mkdir -p "$test_dir"
    echo 'version = "1.0.0"' > "$test_dir/pyproject.toml"
    echo '**Current Version:** v1.0.0' > "$test_dir/CLAUDE.md"
    echo '## [1.0.0]' > "$test_dir/CHANGELOG.md"
    echo 'v1.0.0' > "$test_dir/README.md"

    cd "$test_dir"
    cp "$PROJECT_ROOT/scripts/check_version_sync.sh" .

    # Script should PASS (exit 0) because all versions match
    if ./check_version_sync.sh > /dev/null 2>&1; then
        # Script correctly allowed matching versions
        cleanup_test_dir "$test_dir"
        return 0
    else
        # Script failed when it should have passed
        cleanup_test_dir "$test_dir"
        return 1
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MISTAKE-002 Prevention: Test Count Sync Detection
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

test_test_count_sync_detects_mismatch() {
    local test_dir="/tmp/mistake_002_test_$$"
    cleanup_test_dir "$test_dir"

    # Create test directory structure
    mkdir -p "$test_dir/docs/guides"

    # Create TESTING.md with WRONG test count
    echo '**Total Test Coverage**: 100 tests (v0.6.0)' > "$test_dir/docs/guides/TESTING.md"

    # Create Makefile that returns different count
    cat > "$test_dir/Makefile" << 'EOF'
test:
	@echo "collecting ... collected 456 items"
EOF

    cd "$test_dir"
    cp "$PROJECT_ROOT/scripts/check_test_count_sync.sh" .

    # Script should FAIL because counts don't match (100 vs 456)
    if ./check_test_count_sync.sh > /dev/null 2>&1; then
        cleanup_test_dir "$test_dir"
        return 1
    else
        cleanup_test_dir "$test_dir"
        return 0
    fi
}

test_test_count_sync_allows_matching_counts() {
    local test_dir="/tmp/mistake_002_test_match_$$"
    cleanup_test_dir "$test_dir"

    mkdir -p "$test_dir/docs/guides"

    # Create TESTING.md with CORRECT test count
    echo '**Total Test Coverage**: 456 tests (v0.6.0)' > "$test_dir/docs/guides/TESTING.md"

    # Create Makefile that returns same count
    cat > "$test_dir/Makefile" << 'EOF'
test:
	@echo "collecting ... collected 456 items"
EOF

    cd "$test_dir"
    cp "$PROJECT_ROOT/scripts/check_test_count_sync.sh" .

    # Script should PASS because counts match
    if ./check_test_count_sync.sh > /dev/null 2>&1; then
        cleanup_test_dir "$test_dir"
        return 0
    else
        cleanup_test_dir "$test_dir"
        return 1
    fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Run All Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "MISTAKE-001 Prevention Tests (check_version_sync.sh)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_prevention "Version sync detects mismatch (positive case)" test_version_sync_detects_mismatch
test_prevention "Version sync allows matching versions (negative case)" test_version_sync_allows_matching_versions

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "MISTAKE-002 Prevention Tests (check_test_count_sync.sh)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

test_prevention "Test count sync detects mismatch (positive case)" test_test_count_sync_detects_mismatch
test_prevention "Test count sync allows matching counts (negative case)" test_test_count_sync_allows_matching_counts

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Test Results Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

for result in "${TEST_RESULTS[@]}"; do
    echo "$result"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Total: $((TESTS_PASSED + TESTS_FAILED)) tests"
echo "Passed: $TESTS_PASSED ✅"
echo "Failed: $TESTS_FAILED ❌"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "🎉 All prevention validation tests passed!"
    echo ""
    echo "This proves that prevention measures actually detect their target mistakes."
    echo "Prevention for MISTAKE-001 and MISTAKE-002 is validated."
    exit 0
else
    echo "⚠️  Some prevention validation tests failed!"
    echo ""
    echo "This indicates that prevention measures may not be working correctly."
    echo "Review failed tests and fix prevention scripts before marking them as validated."
    exit 1
fi
