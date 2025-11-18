#!/bin/bash
# Check if all documentation files have synchronized test counts
# Addresses MISTAKE-002 root cause and issue #169

echo "🧪 Checking test count synchronization..."

# Determine pytest command (venv or system)
if [ -f "./venv/bin/pytest" ]; then
    PYTEST_CMD="./venv/bin/pytest"
elif command -v pytest &> /dev/null; then
    PYTEST_CMD="pytest"
else
    echo "❌ pytest not found (checked ./venv/bin/pytest and system PATH)"
    echo "   Run: python3 -m venv venv && ./venv/bin/pip install -e ."
    exit 1
fi

# Get actual test count from pytest
# Exclude integration tests since those require OmniFocus setup
ACTUAL_COUNT=$($PYTEST_CMD tests/ -m "not integration" --collect-only -q 2>&1 | tail -1 | grep -o "[0-9]\+ test" | grep -o "[0-9]\+")

if [ -z "$ACTUAL_COUNT" ]; then
    echo "❌ Could not determine actual test count"
    echo "   Run: $PYTEST_CMD tests/ -m 'not integration' --collect-only -q"
    exit 1
fi

echo "   Actual test count (pytest): $ACTUAL_COUNT"
echo ""

# Files to check (TESTING.md is canonical source)
# Format: "file_path"
DOC_FILES=(
    "docs/guides/TESTING.md"
    "README.md"
    ".claude/CLAUDE.md"
    "docs/reference/API_REFERENCE.md"
    "docs/project/ROADMAP.md"
    "docs/guides/CONTRIBUTING.md"
    "docs/guides/README.md"
    ".claude/commands/test-coverage.md"
)

MISMATCH_COUNT=0
MISMATCHED_FILES=()

# Check each file
for FILE in "${DOC_FILES[@]}"; do
    if [ ! -f "$FILE" ]; then
        echo "⚠️  $FILE not found (skipping)"
        continue
    fi

    # Extract test count from file (look for patterns like "333 tests" or "333 passing tests")
    # Use head -1 to get the first occurrence which should be the main count
    DOCUMENTED_COUNT=$(grep -oE "[0-9]+ (passing )?tests?" "$FILE" | grep -oE "[0-9]+" | head -1)

    if [ -z "$DOCUMENTED_COUNT" ]; then
        echo "⚠️  No test count found in $FILE"
        continue
    fi

    # Compare with actual count
    if [ "$DOCUMENTED_COUNT" -eq "$ACTUAL_COUNT" ]; then
        echo "✅ $FILE: $DOCUMENTED_COUNT tests (match)"
    else
        DIFF=$((ACTUAL_COUNT - DOCUMENTED_COUNT))
        if [ $DIFF -gt 0 ]; then
            DIRECTION="↑"
        else
            DIRECTION="↓"
            DIFF=$((-DIFF))
        fi
        echo "❌ $FILE: $DOCUMENTED_COUNT tests (should be $ACTUAL_COUNT, $DIRECTION$DIFF)"
        MISMATCH_COUNT=$((MISMATCH_COUNT + 1))
        MISMATCHED_FILES+=("$FILE")
    fi
done

echo ""

# Summary
if [ $MISMATCH_COUNT -eq 0 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ All documentation files have synchronized test counts!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ Test count mismatch in $MISMATCH_COUNT file(s)!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   Actual test count: $ACTUAL_COUNT"
    echo ""
    echo "📝 Files needing updates:"
    for FILE in "${MISMATCHED_FILES[@]}"; do
        echo "   - $FILE"
    done
    echo ""
    echo "💡 Action required:"
    echo "   1. Update each file above with correct count: $ACTUAL_COUNT"
    echo "   2. Ensure docs/guides/TESTING.md is the canonical source"
    echo "   3. Run this script again to verify: ./scripts/check_test_count_sync.sh"
    echo ""
    echo "💡 Prevention (issue #169):"
    echo "   - This check runs in pre-tag hook (blocks RC creation)"
    echo "   - Warning in pre-commit hook (alerts early)"
    echo "   - TESTING.md is single source of truth"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    exit 1
fi
