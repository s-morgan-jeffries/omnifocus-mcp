#!/bin/bash
# Update the status of a logged mistake

MISTAKES_FILE=".claude/mistakes/MISTAKES.md"

# Usage
if [ $# -lt 2 ]; then
    echo "Usage: ./scripts/update_mistake_status.sh MISTAKE-XXX <status> [details]"
    echo ""
    echo "Status options:"
    echo "  open                - Newly logged, not being worked on"
    echo "  fixing              - Currently implementing the fix"
    echo "  prevention-pending  - Fix implemented, prevention not yet added"
    echo "  monitoring          - Prevention implemented, monitoring effectiveness"
    echo "  resolved            - Prevention validated, no recurrence"
    echo "  archived            - Old mistake, moved to historical record"
    echo ""
    echo "Examples:"
    echo "  ./scripts/update_mistake_status.sh MISTAKE-001 fixing"
    echo "  ./scripts/update_mistake_status.sh MISTAKE-001 resolved abc1234"
    echo "  ./scripts/update_mistake_status.sh MISTAKE-001 prevention-pending '.claude/CLAUDE.md:247'"
    exit 1
fi

MISTAKE_ID="$1"
NEW_STATUS="$2"
DETAIL="$3"

# Validate status
case "$NEW_STATUS" in
    open|fixing|prevention-pending|monitoring|resolved|archived)
        ;;
    *)
        echo "❌ Invalid status: $NEW_STATUS"
        echo "Valid: open | fixing | prevention-pending | monitoring | resolved | archived"
        exit 1
        ;;
esac

# Check if mistake exists
if ! grep -q "\[${MISTAKE_ID}\]" "$MISTAKES_FILE"; then
    echo "❌ ${MISTAKE_ID} not found in $MISTAKES_FILE"
    exit 1
fi

# Update status field
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "/\[${MISTAKE_ID}\]/,/^## \[MISTAKE-/{s/^\*\*Status:\*\* .*/\*\*Status:\*\* ${NEW_STATUS}/;}" "$MISTAKES_FILE"
else
    # Linux
    sed -i "/\[${MISTAKE_ID}\]/,/^## \[MISTAKE-/{s/^\*\*Status:\*\* .*/\*\*Status:\*\* ${NEW_STATUS}/;}" "$MISTAKES_FILE"
fi

echo "✅ Updated ${MISTAKE_ID} status to: ${NEW_STATUS}"

# Handle status-specific updates
case "$NEW_STATUS" in
    resolved)
        if [ -n "$DETAIL" ]; then
            # Update "Resolved in commit" field
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "/\[${MISTAKE_ID}\]/,/^## \[MISTAKE-/{s|- \*\*Resolved in commit:\*\* .*|- \*\*Resolved in commit:\*\* ${DETAIL}|;}" "$MISTAKES_FILE"
            else
                sed -i "/\[${MISTAKE_ID}\]/,/^## \[MISTAKE-/{s|- \*\*Resolved in commit:\*\* .*|- \*\*Resolved in commit:\*\* ${DETAIL}|;}" "$MISTAKES_FILE"
            fi
            echo "   Resolved in commit: ${DETAIL}"
        fi
        echo ""
        echo "📋 Next steps:"
        echo "1. Verify prevention measure is documented in MISTAKES.md"
        echo "2. Check if prevention was actually implemented (use verify_prevention.sh)"
        echo "3. Consider moving to 'monitoring' status to track effectiveness"
        ;;
    prevention-pending)
        if [ -n "$DETAIL" ]; then
            # Update "Prevention implemented in" field
            if [[ "$OSTYPE" == "darwin"* ]]; then
                sed -i '' "/\[${MISTAKE_ID}\]/,/^## \[MISTAKE-/{s|- \*\*Prevention implemented in:\*\* .*|- \*\*Prevention implemented in:\*\* ${DETAIL}|;}" "$MISTAKES_FILE"
            else
                sed -i "/\[${MISTAKE_ID}\]/,/^## \[MISTAKE-/{s|- \*\*Prevention implemented in:\*\* .*|- \*\*Prevention implemented in:\*\* ${DETAIL}|;}" "$MISTAKES_FILE"
            fi
            echo "   Prevention implemented in: ${DETAIL}"
        fi
        echo ""
        echo "📋 Next steps:"
        echo "1. Add prevention reminder to CLAUDE.md or CONTRIBUTING.md"
        echo "2. Run: ./scripts/verify_prevention.sh ${MISTAKE_ID}"
        echo "3. Update status to 'monitoring' once prevention is in place"
        ;;
    archived)
        echo ""
        echo "📋 Next steps:"
        echo "1. Manually move ${MISTAKE_ID} entry to 'Archived Mistakes' section"
        echo "2. Run: ./scripts/update_metrics.sh to reflect archival"
        ;;
esac
