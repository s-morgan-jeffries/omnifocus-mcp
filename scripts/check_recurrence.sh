#!/bin/bash
# Check for recurrence of AI process failures
#
# This script checks open ai-process issues for prevention script failures.
# If a prevention measure has failed, it indicates the issue has recurred.
#
# Per the migration plan, we use standard GitHub workflow:
# - This script detects recurrences automatically
# - Reports which issues have prevention failures
# - Human then files new issue and marks as duplicate during triage

set -e

RECURRENCE_DETECTED=0
ISSUES_CHECKED=0

echo "🔍 Checking for AI process failure recurrences..."
echo ""

# Get all open ai-process issues
echo "📋 Fetching open ai-process issues from GitHub..."
ISSUES_JSON=$(gh issue list --label ai-process --state open --json number,title,body --limit 100)

if [ "$(echo "$ISSUES_JSON" | jq '. | length')" -eq 0 ]; then
    echo "✅ No open ai-process issues to check"
    exit 0
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Process each issue
for row in $(echo "$ISSUES_JSON" | jq -r '.[] | @base64'); do
    _jq() {
        echo "$row" | base64 --decode | jq -r "${1}"
    }

    ISSUE_NUM=$(_jq '.number')
    ISSUE_TITLE=$(_jq '.title')
    ISSUE_BODY=$(_jq '.body')

    echo "📋 Checking issue #$ISSUE_NUM: $ISSUE_TITLE"

    # Extract prevention script from issue body
    # Look for ## Prevention Script section followed by bash code block
    PREVENTION_SCRIPT=$(echo "$ISSUE_BODY" | awk '
        /^## Prevention Script/ { in_section=1; next }
        in_section && /^```bash/ { in_code=1; next }
        in_section && in_code && /^```/ { exit }
        in_section && in_code { print }
    ')

    if [ -z "$PREVENTION_SCRIPT" ]; then
        echo "   ⚠️  No prevention script found - skipping"
        echo ""
        continue
    fi

    ((ISSUES_CHECKED++)) || true

    # Run the prevention script
    if echo "$PREVENTION_SCRIPT" | bash > /dev/null 2>&1; then
        echo "   ✅ Prevention holding"
    else
        echo "   ❌ RECURRENCE DETECTED"
        echo "   Prevention script failed - this mistake has likely recurred"
        echo ""
        echo "   📝 Action required:"
        echo "      1. File new issue for this recurrence"
        echo "      2. During triage, mark new issue as duplicate of #$ISSUE_NUM"
        echo "      3. Add 'duplicate' label and link in comments"
        ((RECURRENCE_DETECTED++)) || true
    fi

    echo ""
done

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Recurrence Check Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Issues checked: $ISSUES_CHECKED"
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
    echo "  1. File new issue(s) for recurrence(s)"
    echo "  2. Mark as duplicates during triage"
    echo "  3. Analyze why prevention failed"
    echo "  4. Update prevention measures in original issue"
    echo "  5. Consider stronger enforcement (hooks, CI/CD)"
    echo ""
    exit 1
else
    echo "✅ No recurrences detected"
    echo ""
    echo "All prevention measures are working as expected."
    echo ""
    exit 0
fi
