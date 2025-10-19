#!/bin/bash
# Quick script to log a mistake with template

MISTAKES_FILE=".claude/MISTAKES.md"

# Get next mistake number
LAST_NUM=$(grep -o "MISTAKE-[0-9]\+" "$MISTAKES_FILE" | sed 's/MISTAKE-//' | sort -n | tail -1)
if [ -z "$LAST_NUM" ]; then
    NEXT_NUM="001"
else
    NEXT_NUM=$(printf "%03d" $((LAST_NUM + 1)))
fi

# Create template
DATE=$(date +%Y-%m-%d)
TEMPLATE="
## [MISTAKE-$NEXT_NUM] TITLE_HERE (Date: $DATE)

**Status:** open

**Category:** [missing-tests | missing-exposure | violated-tdd | violated-architecture | missing-docs | complexity-spike | other]

**Severity:** [critical | high | medium | low]

**Discovery Date:** $DATE
**Introduced In:** [Commit hash or Unknown]
**Recurrence Count:** 0
**Last Recurrence:** N/A
**Verification Deadline:** TBD (30 days after prevention implemented)

**What Happened:**


**Context:**
- **File(s):**
- **Function(s):**
- **Commit:**

**Impact:**


**Root Cause:**


**Fix:**

- **Resolved in commit:** pending
- **Prevention implemented in:** pending

**Prevention:**

- **Prevention Status:** [ ] Not Started  [ ] Implemented  [ ] Validated

**Related Mistakes:**


**Effectiveness Score:** pending

---
"

# Add to file (before the "Quick Reference" section)
# Use a temporary file to insert before the quick reference
TEMP_FILE=$(mktemp)
sed '/^## Quick Reference$/,$d' "$MISTAKES_FILE" > "$TEMP_FILE"
echo "$TEMPLATE" >> "$TEMP_FILE"
sed -n '/^## Quick Reference$/,$p' "$MISTAKES_FILE" >> "$TEMP_FILE"
mv "$TEMP_FILE" "$MISTAKES_FILE"

echo "✅ Created MISTAKE-$NEXT_NUM in $MISTAKES_FILE"
echo ""
echo "Next steps:"
echo "1. Edit $MISTAKES_FILE to fill in details"
echo "2. Move entry from 'Active Mistakes' section when addressed"
echo "3. Reference in commit message: 'Resolves: MISTAKE-$NEXT_NUM'"

# Update statistics (exclude template examples like MISTAKE-XXX)
TOTAL=$(grep "^## \[MISTAKE-" "$MISTAKES_FILE" | grep -v "MISTAKE-XXX" | wc -l | tr -d ' ')
sed -i.bak "s/^- Total Mistakes: [0-9]*/- Total Mistakes: $TOTAL/" "$MISTAKES_FILE"
rm -f "$MISTAKES_FILE.bak"
