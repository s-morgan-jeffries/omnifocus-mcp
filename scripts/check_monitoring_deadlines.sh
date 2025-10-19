#!/bin/bash
# Check for mistakes in "monitoring" status that have passed their verification deadline
# Addresses MISTAKE-008: No recurrence tracking mechanism
#
# This script identifies mistakes that:
# 1. Have status "monitoring"
# 2. Have passed their verification deadline (30 days after prevention)
# 3. Should be transitioned to "resolved" if no recurrence detected

MISTAKES_FILE=".claude/MISTAKES.md"

if [ ! -f "$MISTAKES_FILE" ]; then
    echo "❌ $MISTAKES_FILE not found"
    exit 1
fi

echo "📅 Checking verification deadlines for mistakes in monitoring status..."
echo ""

TODAY=$(date +%Y-%m-%d)
TODAY_EPOCH=$(date -j -f "%Y-%m-%d" "$TODAY" +%s 2>/dev/null || date -d "$TODAY" +%s 2>/dev/null)

OVERDUE_FOUND=0
MONITORING_COUNT=0

# Extract all mistake blocks
while IFS= read -r line; do
    # Detect start of mistake entry
    if echo "$line" | grep -q "^## \[MISTAKE-[0-9]\+\]"; then
        MISTAKE_ID=$(echo "$line" | grep -o "MISTAKE-[0-9]\+")
        MISTAKE_TITLE=$(echo "$line" | sed "s/^## \[$MISTAKE_ID\] //" | sed "s/ (Date:.*//"  )
        IN_MISTAKE=true
        STATUS=""
        DEADLINE=""
        continue
    fi

    # Extract status
    if [ "$IN_MISTAKE" = true ] && echo "$line" | grep -q "^\*\*Status:\*\*"; then
        STATUS=$(echo "$line" | sed 's/\*\*Status:\*\* //' | tr -d ' ')
    fi

    # Extract verification deadline
    if [ "$IN_MISTAKE" = true ] && echo "$line" | grep -q "^\*\*Verification Deadline:\*\*"; then
        # Extract date in YYYY-MM-DD format
        DEADLINE=$(echo "$line" | grep -o "[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}" | head -1)
    fi

    # End of mistake block
    if echo "$line" | grep -q "^---$" && [ "$IN_MISTAKE" = true ]; then
        # Check if this mistake is in monitoring status
        if [ "$STATUS" = "monitoring" ]; then
            ((MONITORING_COUNT++))

            # Check if deadline is set and not "TBD"
            if [ -n "$DEADLINE" ] && [ "$DEADLINE" != "TBD" ]; then
                # Convert deadline to epoch for comparison
                DEADLINE_EPOCH=$(date -j -f "%Y-%m-%d" "$DEADLINE" +%s 2>/dev/null || date -d "$DEADLINE" +%s 2>/dev/null)

                if [ "$TODAY_EPOCH" -gt "$DEADLINE_EPOCH" ]; then
                    echo "⚠️  $MISTAKE_ID: OVERDUE for verification"
                    echo "   Title: $MISTAKE_TITLE"
                    echo "   Deadline: $DEADLINE ($(( (TODAY_EPOCH - DEADLINE_EPOCH) / 86400 )) days ago)"
                    echo "   Action: Review for recurrence, then transition to 'resolved' or extend deadline"
                    echo ""
                    ((OVERDUE_FOUND++))
                else
                    DAYS_REMAINING=$(( (DEADLINE_EPOCH - TODAY_EPOCH) / 86400 ))
                    echo "✅ $MISTAKE_ID: On track"
                    echo "   Deadline: $DEADLINE ($DAYS_REMAINING days remaining)"
                    echo ""
                fi
            else
                echo "⚠️  $MISTAKE_ID: No verification deadline set"
                echo "   Title: $MISTAKE_TITLE"
                echo "   Action: Set verification deadline (Prevention Date + 30 days)"
                echo ""
                ((OVERDUE_FOUND++))
            fi
        fi

        IN_MISTAKE=false
        MISTAKE_ID=""
        MISTAKE_TITLE=""
        STATUS=""
        DEADLINE=""
    fi
done < "$MISTAKES_FILE"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Mistakes in monitoring status: $MONITORING_COUNT"
echo "Overdue or missing deadlines: $OVERDUE_FOUND"
echo ""

if [ $OVERDUE_FOUND -gt 0 ]; then
    echo "📝 Action required:"
    echo "   1. Review overdue mistakes for recurrence evidence"
    echo "   2. If no recurrence: ./scripts/update_mistake_status.sh MISTAKE-XXX resolved"
    echo "   3. If recurrence found: Update recurrence count and analyze prevention failure"
    echo "   4. If deadline missing: Add verification deadline to MISTAKES.md"
    echo ""
    exit 1
else
    echo "✅ All monitoring mistakes are on track"
    exit 0
fi
