#!/bin/bash
# Check for patterns of previously prevented mistakes
# Addresses MISTAKE-008: No recurrence tracking mechanism
#
# This script dynamically parses MISTAKES.md to find all mistakes in
# "monitoring" or "resolved" status, then runs their prevention checks
# to detect if they have recurred.
#
# If recurrence is detected, reports it and prompts to update MISTAKES.md

set -e

MISTAKES_FILE=".claude/MISTAKES.md"
RECURRENCE_DETECTED=0
MISTAKES_CHECKED=0

echo "🔍 Checking for recurrence of previously prevented mistakes..."
echo ""

# Parse MISTAKES.md for mistakes with prevention implemented
# Extract mistake IDs, statuses, and their prevention mechanisms
parse_mistakes() {
    local current_id=""
    local current_status=""

    while IFS= read -r line; do
        # Match mistake ID header
        if [[ "$line" =~ ^\#\#\ \[MISTAKE-([0-9]+)\] ]]; then
            current_id="${BASH_REMATCH[1]}"
        fi

        # Match status
        if [[ "$line" =~ ^\*\*Status:\*\*\ (monitoring|resolved) ]]; then
            current_status="${BASH_REMATCH[1]}"

            # If we found a monitoring/resolved mistake, output it
            if [[ -n "$current_id" ]]; then
                echo "$current_id:$current_status"
                current_id=""
                current_status=""
            fi
        fi
    done < "$MISTAKES_FILE"
}

echo "📋 Parsing $MISTAKES_FILE for monitoring/resolved mistakes..."
MISTAKES_TO_CHECK=$(parse_mistakes)

if [[ -z "$MISTAKES_TO_CHECK" ]]; then
    echo "✅ No mistakes in monitoring/resolved status to check"
    exit 0
fi

echo ""

# Map mistake IDs to their prevention check scripts
# This mapping defines how to check if each mistake has recurred
check_mistake() {
    local mistake_id="$1"

    case "$mistake_id" in
        001|003)
            # MISTAKE-001 & 003: Version sync issues
            echo "📋 Checking MISTAKE-$mistake_id (version synchronization)..."
            if ! ./scripts/check_version_sync.sh > /dev/null 2>&1; then
                echo "   ❌ RECURRENCE: Version mismatch detected"
                echo "   Prevention script: check_version_sync.sh (pre-commit hook)"
                return 1
            else
                echo "   ✅ No version sync issues"
                return 0
            fi
            ;;

        002)
            # MISTAKE-002: Test count sync issues
            echo "📋 Checking MISTAKE-$mistake_id (test count synchronization)..."
            if ! ./scripts/check_test_count_sync.sh > /dev/null 2>&1; then
                echo "   ❌ RECURRENCE: Test count mismatch detected"
                echo "   Prevention: TESTING.md single source of truth"
                return 1
            else
                echo "   ✅ No test count sync issues"
                return 0
            fi
            ;;

        004)
            # MISTAKE-004: Metrics automation
            # Check if update_metrics.sh is called in commit-msg hook
            echo "📋 Checking MISTAKE-$mistake_id (metrics automation)..."
            if grep -q "update_metrics.sh" scripts/git-hooks/commit-msg; then
                echo "   ✅ Metrics automation still integrated in commit-msg hook"
                return 0
            else
                echo "   ❌ RECURRENCE: update_metrics.sh not found in commit-msg hook"
                return 1
            fi
            ;;

        007)
            # MISTAKE-007: No prevention validation
            # Check if test_prevention_measures.sh exists and is executable
            echo "📋 Checking MISTAKE-$mistake_id (prevention validation)..."
            if [[ -x "./scripts/test_prevention_measures.sh" ]]; then
                echo "   ✅ Prevention validation script still exists and is executable"
                return 0
            else
                echo "   ❌ RECURRENCE: test_prevention_measures.sh missing or not executable"
                return 1
            fi
            ;;

        008)
            # MISTAKE-008: No recurrence tracking
            # This script itself addresses MISTAKE-008, so check it exists
            echo "📋 Checking MISTAKE-$mistake_id (recurrence tracking)..."
            if [[ -x "./scripts/check_recurrence.sh" ]] && [[ -x "./scripts/check_monitoring_deadlines.sh" ]]; then
                echo "   ✅ Recurrence tracking scripts still exist and are executable"
                return 0
            else
                echo "   ❌ RECURRENCE: Recurrence tracking scripts missing or not executable"
                return 1
            fi
            ;;

        *)
            echo "⚠️  MISTAKE-$mistake_id: No automated recurrence check defined"
            echo "   (Manual verification required)"
            return 0  # Don't count as failure
            ;;
    esac
}

# Iterate through each mistake and check for recurrence
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
while IFS=: read -r mistake_id status; do
    ((MISTAKES_CHECKED++))

    if ! check_mistake "$mistake_id"; then
        ((RECURRENCE_DETECTED++))
        echo "   📝 Action: Update MISTAKES.md recurrence count for MISTAKE-$mistake_id"
    fi
    echo ""
done <<< "$MISTAKES_TO_CHECK"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Recurrence Check Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Mistakes checked: $MISTAKES_CHECKED (dynamically parsed from MISTAKES.md)"
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
