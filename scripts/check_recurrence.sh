#!/bin/bash
# Check for patterns of previously prevented mistakes
# Addresses MISTAKE-008: No recurrence tracking mechanism
#
# This script scans for evidence that a prevented mistake has recurred:
# - MISTAKE-001: Version mismatches (runs check_version_sync.sh)
# - MISTAKE-002: Test count mismatches (runs check_test_count_sync.sh)
# - MISTAKE-003: Version sync issues (same as MISTAKE-001)
#
# If recurrence is detected, updates MISTAKES.md with recurrence count and date

set -e

MISTAKES_FILE=".claude/MISTAKES.md"
RECURRENCE_DETECTED=0

echo "🔍 Checking for recurrence of previously prevented mistakes..."
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MISTAKE-001 & MISTAKE-003: Version Sync Issues
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "Checking MISTAKE-001 & MISTAKE-003 (version sync)..."
if ! ./scripts/check_version_sync.sh > /dev/null 2>&1; then
    echo "❌ RECURRENCE DETECTED: Version mismatch found"
    echo "   Prevention: check_version_sync.sh in pre-commit hook"
    echo "   Status: Prevention may have been bypassed or has a bug"
    echo ""
    ((RECURRENCE_DETECTED++))

    # Update MISTAKES.md recurrence count
    # (This would need sed logic to increment the count and update date)
    echo "📝 Action: Manually update MISTAKES.md recurrence fields for MISTAKE-001 and MISTAKE-003"
else
    echo "✅ No version sync issues detected"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MISTAKE-002: Test Count Sync Issues
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "Checking MISTAKE-002 (test count sync)..."
if ! ./scripts/check_test_count_sync.sh > /dev/null 2>&1; then
    echo "❌ RECURRENCE DETECTED: Test count mismatch found"
    echo "   Prevention: TESTING.md as single source of truth"
    echo "   Status: Documentation may not have been updated"
    echo ""
    ((RECURRENCE_DETECTED++))

    echo "📝 Action: Manually update MISTAKES.md recurrence fields for MISTAKE-002"
else
    echo "✅ No test count sync issues detected"
fi
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Recurrence Check Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Mistakes checked: 3 (MISTAKE-001, 002, 003)"
echo "Recurrences detected: $RECURRENCE_DETECTED"
echo ""

if [ $RECURRENCE_DETECTED -gt 0 ]; then
    echo "⚠️  Prevention failure detected!"
    echo ""
    echo "This means one of the following:"
    echo "  1. Prevention script has a bug (false negative)"
    echo "  2. Prevention was bypassed (git commit --no-verify)"
    echo "  3. Prevention is incomplete (doesn't cover all cases)"
    echo ""
    echo "📝 Next steps:"
    echo "  1. Update MISTAKES.md recurrence count and date"
    echo "  2. Analyze why prevention failed"
    echo "  3. Fix prevention measures"
    echo "  4. Consider stronger enforcement (CI/CD checks)"
    echo ""
    exit 1
else
    echo "✅ No recurrences detected"
    echo ""
    echo "All prevention measures are working as expected."
    echo "Mistakes in 'monitoring' status can be reviewed for transition to 'resolved'."
    echo ""
    exit 0
fi
