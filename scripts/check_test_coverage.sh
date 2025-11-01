#!/bin/bash
# Check for test coverage gaps (Critical check - blocking)
# Enforces minimum 85% test coverage threshold
# Returns 0 if coverage >= 85%, 1 if below threshold

echo "Checking test coverage..."

ISSUES_FOUND=0

# Check for TODO markers indicating missing tests
echo "1. Checking for TODO test markers in source code..."
TODO_TESTS=$(grep -r "TODO.*test" src/ 2>/dev/null || echo "")
if [ -n "$TODO_TESTS" ]; then
    echo "   ⚠️  Found TODO test markers:"
    echo "$TODO_TESTS" | sed 's/^/      /'
    ISSUES_FOUND=1
else
    echo "   ✅ No TODO test markers found"
fi

# Check for functions without corresponding tests
echo "2. Checking for untested public functions..."
# Get all public function definitions from omnifocus_connector.py
FUNCTIONS=$(grep -E "^    def [a-z_]+\(" src/omnifocus_mcp/omnifocus_connector.py | sed 's/.*def \([a-z_]*\).*/\1/' || echo "")

UNTESTED=()
for func in $FUNCTIONS; do
    # Skip private functions and __init__
    if [[ "$func" == _* ]] || [[ "$func" == "__init__" ]]; then
        continue
    fi

    # Check if function has tests in any test file
    if ! grep -rq "test.*$func\|$func.*test" tests/ 2>/dev/null; then
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
# Use venv python if available, otherwise system python
if [ -f ./venv/bin/python ]; then
    PYTHON=./venv/bin/python
else
    PYTHON=python3
fi

if $PYTHON -c "import pytest_cov" 2>/dev/null; then
    # Run coverage on omnifocus_connector.py with all unit tests
    COVERAGE=$($PYTHON -m pytest tests/ -m "not integration" --cov=src/omnifocus_mcp/omnifocus_connector --cov-report=term-missing 2>/dev/null | grep "TOTAL" | awk '{print $NF}' | sed 's/%//' || echo "0")

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
    echo "❌ Test coverage check failed"
    echo ""
    echo "Required action:"
    echo "  - Add tests to reach 85% coverage minimum"
    echo "  - Or document exceptions if coverage gaps are intentional"
    exit 1
fi
