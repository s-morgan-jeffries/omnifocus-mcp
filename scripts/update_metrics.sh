#!/bin/bash
# Automatically update METRICS.md from MISTAKES.md data

MISTAKES_FILE=".claude/MISTAKES.md"
METRICS_FILE=".claude/METRICS.md"

echo "📊 Analyzing MISTAKES.md..."

# Count mistakes by category
MISSING_TESTS=$(grep -c "^\*\*Category:\*\* missing-tests$" "$MISTAKES_FILE" 2>/dev/null || echo "0")
MISSING_EXPOSURE=$(grep -c "^\*\*Category:\*\* missing-exposure$" "$MISTAKES_FILE" 2>/dev/null || echo "0")
VIOLATED_TDD=$(grep -c "^\*\*Category:\*\* violated-tdd$" "$MISTAKES_FILE" 2>/dev/null || echo "0")
VIOLATED_ARCH=$(grep -c "^\*\*Category:\*\* violated-architecture$" "$MISTAKES_FILE" 2>/dev/null || echo "0")
MISSING_DOCS=$(grep -c "^\*\*Category:\*\* missing-docs$" "$MISTAKES_FILE" 2>/dev/null || echo "0")
COMPLEXITY=$(grep -c "^\*\*Category:\*\* complexity-spike$" "$MISTAKES_FILE" 2>/dev/null || echo "0")
OTHER=$(grep -c "^\*\*Category:\*\* other$" "$MISTAKES_FILE" 2>/dev/null || echo "0")

# Count by severity
CRITICAL=$(grep -c "^\*\*Severity:\*\* critical$" "$MISTAKES_FILE" 2>/dev/null || echo "0")
HIGH=$(grep -c "^\*\*Severity:\*\* high$" "$MISTAKES_FILE" 2>/dev/null || echo "0")
MEDIUM=$(grep -c "^\*\*Severity:\*\* medium$" "$MISTAKES_FILE" 2>/dev/null || echo "0")
LOW=$(grep -c "^\*\*Severity:\*\* low$" "$MISTAKES_FILE" 2>/dev/null || echo "0")

# Count by status
OPEN=$(grep -c "^\*\*Status:\*\* open$" "$MISTAKES_FILE" 2>/dev/null || echo "0")
FIXING=$(grep -c "^\*\*Status:\*\* fixing$" "$MISTAKES_FILE" 2>/dev/null || echo "0")
PREVENTION_PENDING=$(grep -c "^\*\*Status:\*\* prevention-pending$" "$MISTAKES_FILE" 2>/dev/null || echo "0")
MONITORING=$(grep -c "^\*\*Status:\*\* monitoring$" "$MISTAKES_FILE" 2>/dev/null || echo "0")
RESOLVED=$(grep -c "^\*\*Status:\*\* resolved$" "$MISTAKES_FILE" 2>/dev/null || echo "0")
ARCHIVED=$(grep -c "^\*\*Status:\*\* archived$" "$MISTAKES_FILE" 2>/dev/null || echo "0")

# Total (exclude template MISTAKE-XXX)
TOTAL=$(grep "^## \[MISTAKE-" "$MISTAKES_FILE" | grep -v "MISTAKE-XXX" | wc -l | tr -d ' ')

# Update METRICS.md
echo "📝 Updating $METRICS_FILE..."

# Update "Mistake Count by Category" table
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/| missing-tests.*/| missing-tests | $MISSING_TESTS |/" "$METRICS_FILE"
    sed -i '' "s/| missing-exposure.*/| missing-exposure | $MISSING_EXPOSURE |/" "$METRICS_FILE"
    sed -i '' "s/| violated-tdd.*/| violated-tdd | $VIOLATED_TDD |/" "$METRICS_FILE"
    sed -i '' "s/| violated-architecture.*/| violated-architecture | $VIOLATED_ARCH |/" "$METRICS_FILE"
    sed -i '' "s/| missing-docs.*/| missing-docs | $MISSING_DOCS |/" "$METRICS_FILE"
    sed -i '' "s/| complexity-spike.*/| complexity-spike | $COMPLEXITY |/" "$METRICS_FILE"
    sed -i '' "s/| other.*/| other | $OTHER |/" "$METRICS_FILE"

    # Update severity distribution
    sed -i '' "s/| Critical.*/| Critical | $CRITICAL |/" "$METRICS_FILE"
    sed -i '' "s/| High.*/| High | $HIGH |/" "$METRICS_FILE"
    sed -i '' "s/| Medium.*/| Medium | $MEDIUM |/" "$METRICS_FILE"
    sed -i '' "s/| Low.*/| Low | $LOW |/" "$METRICS_FILE"

    # Update status tracking
    sed -i '' "s/| Open.*/| Open | $OPEN | Not started/" "$METRICS_FILE"
    sed -i '' "s/| Fixing.*/| Fixing | $FIXING | In progress |/" "$METRICS_FILE"
    sed -i '' "s/| Prevention Pending.*/| Prevention Pending | $PREVENTION_PENDING | Fix done, awaiting prevention |/" "$METRICS_FILE"
    sed -i '' "s/| Monitoring.*/| Monitoring | $MONITORING | Watching for recurrence |/" "$METRICS_FILE"
    sed -i '' "s/| Resolved.*/| Resolved | $RESOLVED | Complete, no recurrence |/" "$METRICS_FILE"
    sed -i '' "s/| Archived.*/| Archived | $ARCHIVED | Historical record |/" "$METRICS_FILE"

    # Update total
    sed -i '' "s/^- Total Mistakes: [0-9]*/- Total Mistakes: $TOTAL/" "$METRICS_FILE"
else
    # Linux
    sed -i "s/| missing-tests.*/| missing-tests | $MISSING_TESTS |/" "$METRICS_FILE"
    sed -i "s/| missing-exposure.*/| missing-exposure | $MISSING_EXPOSURE |/" "$METRICS_FILE"
    sed -i "s/| violated-tdd.*/| violated-tdd | $VIOLATED_TDD |/" "$METRICS_FILE"
    sed -i "s/| violated-architecture.*/| violated-architecture | $VIOLATED_ARCH |/" "$METRICS_FILE"
    sed -i "s/| missing-docs.*/| missing-docs | $MISSING_DOCS |/" "$METRICS_FILE"
    sed -i "s/| complexity-spike.*/| complexity-spike | $COMPLEXITY |/" "$METRICS_FILE"
    sed -i "s/| other.*/| other | $OTHER |/" "$METRICS_FILE"

    # Update severity distribution
    sed -i "s/| Critical.*/| Critical | $CRITICAL |/" "$METRICS_FILE"
    sed -i "s/| High.*/| High | $HIGH |/" "$METRICS_FILE"
    sed -i "s/| Medium.*/| Medium | $MEDIUM |/" "$METRICS_FILE"
    sed -i "s/| Low.*/| Low | $LOW |/" "$METRICS_FILE"

    # Update status tracking
    sed -i "s/| Open.*/| Open | $OPEN | Not started |/" "$METRICS_FILE"
    sed -i "s/| Fixing.*/| Fixing | $FIXING | In progress |/" "$METRICS_FILE"
    sed -i "s/| Prevention Pending.*/| Prevention Pending | $PREVENTION_PENDING | Fix done, awaiting prevention |/" "$METRICS_FILE"
    sed -i "s/| Monitoring.*/| Monitoring | $MONITORING | Watching for recurrence |/" "$METRICS_FILE"
    sed -i "s/| Resolved.*/| Resolved | $RESOLVED | Complete, no recurrence |/" "$METRICS_FILE"
    sed -i "s/| Archived.*/| Archived | $ARCHIVED | Historical record |/" "$METRICS_FILE"

    # Update total
    sed -i "s/^- Total Mistakes: [0-9]*/- Total Mistakes: $TOTAL/" "$METRICS_FILE"
fi

echo "✅ Updated METRICS.md successfully!"
echo ""
echo "📊 Current Statistics:"
echo "  Total Mistakes: $TOTAL"
echo ""
echo "  By Category:"
echo "    missing-docs: $MISSING_DOCS"
echo "    missing-tests: $MISSING_TESTS"
echo "    violated-architecture: $VIOLATED_ARCH"
echo "    (other categories: $((MISSING_EXPOSURE + VIOLATED_TDD + COMPLEXITY + OTHER)))"
echo ""
echo "  By Status:"
echo "    Open: $OPEN"
echo "    Fixing: $FIXING"
echo "    Prevention Pending: $PREVENTION_PENDING"
echo "    Monitoring: $MONITORING"
echo "    Resolved: $RESOLVED"
echo "    Archived: $ARCHIVED"
