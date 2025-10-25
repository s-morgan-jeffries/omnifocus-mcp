#!/bin/bash
# Run all test suites (unit, integration, e2e)
# Returns 0 if all pass, 1 if any fail

set -e

FAILED=0

echo "Running all test suites..."
echo ""

# Unit tests
echo "1. Running unit tests..."
if make test > /tmp/unit_tests.log 2>&1; then
    echo "   ✅ Unit tests passed"
else
    echo "   ❌ Unit tests failed"
    echo "   See /tmp/unit_tests.log for details"
    FAILED=1
fi

# Integration tests
echo "2. Running integration tests..."
if make test-integration > /tmp/integration_tests.log 2>&1; then
    echo "   ✅ Integration tests passed"
else
    echo "   ❌ Integration tests failed"
    echo "   See /tmp/integration_tests.log for details"
    FAILED=1
fi

# E2E tests
echo "3. Running e2e tests..."
if make test-e2e > /tmp/e2e_tests.log 2>&1; then
    echo "   ✅ E2E tests passed"
else
    echo "   ❌ E2E tests failed"
    echo "   See /tmp/e2e_tests.log for details"
    FAILED=1
fi

echo ""
if [ $FAILED -eq 0 ]; then
    echo "✅ All test suites passed"
    exit 0
else
    echo "❌ Some test suites failed"
    exit 1
fi
