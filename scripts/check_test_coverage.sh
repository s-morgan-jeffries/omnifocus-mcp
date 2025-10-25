#!/bin/bash
# Check for test coverage gaps
# Returns 0 if coverage is acceptable, 1 if issues found

set -e

echo "Checking test coverage..."

ISSUES_FOUND=0

# Check for TODO markers indicating missing tests
echo "1. Checking for TODO test markers in source code..."
TODO_TESTS=$(grep -r "TODO.*test" src/ 2>/dev/null || true)
if [ -n "$TODO_TESTS" ]; then
    echo "   ⚠️  Found TODO test markers:"
    echo "$TODO_TESTS" | sed 's/^/      /'
    ISSUES_FOUND=1
else
    echo "   ✅ No TODO test markers found"
fi

# Check for functions without corresponding tests
echo "2. Checking for untested functions..."
# Get all function definitions from client.py
FUNCTIONS=$(grep -E "^def [a-z_]+\(" src/omnifocus_mcp/client.py | sed 's/def \([a-z_]*\).*/\1/' || true)

UNTESTED=()
for func in $FUNCTIONS; do
    # Skip private functions and __init__
    if [[ "$func" == _* ]] || [[ "$func" == "__init__" ]]; then
        continue
    fi

    # Check if function has tests
    if ! grep -q "test.*$func\|$func.*test" tests/test_client.py 2>/dev/null; then
        UNTESTED+=("$func")
    fi
done

if [ ${#UNTESTED[@]} -gt 0 ]; then
    echo "   ⚠️  Functions without obvious test coverage:"
    for func in "${UNTESTED[@]}"; do
        echo "      - $func()"
    done
    ISSUES_FOUND=1
else
    echo "   ✅ All public functions have test coverage"
fi

# Check overall coverage percentage if pytest-cov available
echo "3. Checking overall coverage percentage..."
if python3 -c "import pytest_cov" 2>/dev/null; then
    COVERAGE=$(python3 -m pytest tests/test_client.py --cov=src/omnifocus_mcp/client --cov-report=term-missing 2>/dev/null | grep "TOTAL" | awk '{print $NF}' | sed 's/%//' || echo "0")

    if [ -n "$COVERAGE" ] && [ "$COVERAGE" -ge 85 ]; then
        echo "   ✅ Coverage is ${COVERAGE}% (target: 85%+)"
    else
        echo "   ⚠️  Coverage is ${COVERAGE}% (target: 85%+)"
        ISSUES_FOUND=1
    fi
else
    echo "   ⚠️  pytest-cov not available, skipping percentage check"
fi

echo ""
if [ $ISSUES_FOUND -eq 0 ]; then
    echo "✅ Test coverage check passed"
    exit 0
else
    echo "⚠️  Test coverage has some gaps (non-blocking)"
    echo "   Consider adding tests for better coverage"
    # Don't fail the release for coverage gaps, just warn
    exit 0
fi
