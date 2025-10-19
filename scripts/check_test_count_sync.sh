#!/bin/bash
# Check if TESTING.md test count matches actual pytest output
# Addresses MISTAKE-002 root cause

echo "🧪 Checking test count synchronization..."

# Get actual test count from pytest
ACTUAL_COUNT=$(pytest --collect-only -q 2>/dev/null | tail -1 | grep -o "[0-9]\+ tests\?" | grep -o "[0-9]\+")

if [ -z "$ACTUAL_COUNT" ]; then
    echo "❌ Could not determine actual test count"
    echo "   Run: pytest --collect-only -q"
    exit 1
fi

echo "   Actual test count (pytest): $ACTUAL_COUNT"

# Get documented count from TESTING.md
TESTING_FILE="docs/guides/TESTING.md"
if [ ! -f "$TESTING_FILE" ]; then
    echo "❌ $TESTING_FILE not found"
    exit 1
fi

# Look for test count patterns in TESTING.md
DOCUMENTED_COUNT=$(grep -oE "[0-9]+ (passing )?tests?" "$TESTING_FILE" | grep -oE "[0-9]+" | head -1)

if [ -z "$DOCUMENTED_COUNT" ]; then
    echo "⚠️  Could not find test count in $TESTING_FILE"
    echo "   Search pattern: 'XXX tests' or 'XXX passing tests'"
    exit 0
fi

echo "   Documented count (TESTING.md): $DOCUMENTED_COUNT"

# Compare
if [ "$ACTUAL_COUNT" -eq "$DOCUMENTED_COUNT" ]; then
    echo "✅ Test counts match!"
    exit 0
else
    DIFF=$((ACTUAL_COUNT - DOCUMENTED_COUNT))
    if [ $DIFF -gt 0 ]; then
        DIRECTION="increased"
    else
        DIRECTION="decreased"
        DIFF=$((-DIFF))
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ Test count mismatch!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "   Actual: $ACTUAL_COUNT tests"
    echo "   Documented: $DOCUMENTED_COUNT tests"
    echo "   Difference: $DIFF tests ($DIRECTION)"
    echo ""
    echo "📝 Action required:"
    echo "   1. Update $TESTING_FILE with correct count: $ACTUAL_COUNT"
    echo "   2. Search and replace: s/$DOCUMENTED_COUNT tests/$ACTUAL_COUNT tests/"
    echo "   3. Verify no other docs reference the old count"
    echo ""
    echo "💡 Prevention (MISTAKE-002):"
    echo "   - TESTING.md is single source of truth"
    echo "   - All other docs should reference it"
    echo "   - Run this script before committing test changes"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    exit 1
fi
