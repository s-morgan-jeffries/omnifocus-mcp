#!/bin/bash
# Verify that prevention measures from a logged mistake were actually implemented

MISTAKES_FILE=".claude/MISTAKES.md"

# Usage
if [ $# -lt 1 ]; then
    echo "Usage: ./scripts/verify_prevention.sh MISTAKE-XXX"
    echo ""
    echo "Checks if prevention measures documented in MISTAKES.md were actually implemented."
    exit 1
fi

MISTAKE_ID="$1"

# Check if mistake exists
if ! grep -q "\[${MISTAKE_ID}\]" "$MISTAKES_FILE"; then
    echo "❌ ${MISTAKE_ID} not found in $MISTAKES_FILE"
    exit 1
fi

echo "🔍 Verifying prevention measures for ${MISTAKE_ID}..."
echo ""

# Extract the Prevention section for this mistake
PREVENTION_TEXT=$(sed -n "/\[${MISTAKE_ID}\]/,/^## \[MISTAKE-/{/^\*\*Prevention:\*\*/,/^\*\*.*:\*\*/p}" "$MISTAKES_FILE" | grep -v "^\*\*")

if [ -z "$PREVENTION_TEXT" ]; then
    echo "⚠️  No prevention measures documented for ${MISTAKE_ID}"
    exit 0
fi

echo "📋 Documented Prevention:"
echo "$PREVENTION_TEXT"
echo ""

# Check for common prevention patterns
CHECKS_PASSED=0
CHECKS_TOTAL=0

# Check 1: If prevention mentions CLAUDE.md, verify it was updated
if echo "$PREVENTION_TEXT" | grep -qi "claude.md\|checklist"; then
    ((CHECKS_TOTAL++))
    # Extract what should be in CLAUDE.md
    if echo "$PREVENTION_TEXT" | grep -qi "before every commit"; then
        echo "✓ Check 1: Looking for 'Before Every Commit' checklist updates..."
        if grep -q "${MISTAKE_ID}" ".claude/CLAUDE.md"; then
            echo "  ✅ CLAUDE.md references ${MISTAKE_ID}"
            ((CHECKS_PASSED++))
        else
            echo "  ⚠️  CLAUDE.md doesn't reference ${MISTAKE_ID}"
            echo "      (Check may not be required if prevention is implicit)"
        fi
    fi
fi

# Check 2: If prevention mentions CONTRIBUTING.md, verify it was updated
if echo "$PREVENTION_TEXT" | grep -qi "contributing.md\|making a release\|workflow"; then
    ((CHECKS_TOTAL++))
    echo "✓ Check 2: Looking for CONTRIBUTING.md updates..."
    # Check last modified date of CONTRIBUTING.md vs. mistake discovery date
    DISCOVERY_DATE=$(sed -n "/\[${MISTAKE_ID}\]/,/^## \[MISTAKE-/{/^\*\*Discovery Date:\*\*/p}" "$MISTAKES_FILE" | sed 's/\*\*Discovery Date:\*\* //')

    if [ -n "$DISCOVERY_DATE" ]; then
        CONTRIB_MODIFIED=$(git log -1 --format="%ai" -- "docs/guides/CONTRIBUTING.md" 2>/dev/null | cut -d' ' -f1)
        if [ "$CONTRIB_MODIFIED" ">" "$DISCOVERY_DATE" ] || [ "$CONTRIB_MODIFIED" == "$DISCOVERY_DATE" ]; then
            echo "  ✅ CONTRIBUTING.md was updated after ${DISCOVERY_DATE}"
            ((CHECKS_PASSED++))
        else
            echo "  ⚠️  CONTRIBUTING.md last modified: ${CONTRIB_MODIFIED} (before mistake discovery)"
        fi
    fi
fi

# Check 3: If prevention mentions scripts, verify they exist
if echo "$PREVENTION_TEXT" | grep -qi "scripts/\|\.sh"; then
    ((CHECKS_TOTAL++))
    echo "✓ Check 3: Looking for mentioned scripts..."
    SCRIPTS=$(echo "$PREVENTION_TEXT" | grep -o "scripts/[a-z_]*.sh" | sort -u)

    if [ -n "$SCRIPTS" ]; then
        SCRIPTS_EXIST=true
        for SCRIPT in $SCRIPTS; do
            if [ -f "$SCRIPT" ]; then
                echo "  ✅ $SCRIPT exists"
            else
                echo "  ❌ $SCRIPT mentioned but doesn't exist"
                SCRIPTS_EXIST=false
            fi
        done
        if $SCRIPTS_EXIST; then
            ((CHECKS_PASSED++))
        fi
    fi
fi

# Check 4: Verify Prevention Status checkbox
PREVENTION_STATUS=$(sed -n "/\[${MISTAKE_ID}\]/,/^## \[MISTAKE-/{/^\*\*Prevention Status:\*\*/p}" "$MISTAKES_FILE")

if echo "$PREVENTION_STATUS" | grep -q "\[x\] Implemented"; then
    echo "✓ Check 4: Prevention Status marked as Implemented"
    ((CHECKS_TOTAL++))
    ((CHECKS_PASSED++))
elif echo "$PREVENTION_STATUS" | grep -q "\[x\] Validated"; then
    echo "✓ Check 4: Prevention Status marked as Validated ✅"
    ((CHECKS_TOTAL++))
    ((CHECKS_PASSED++))
else
    echo "⚠️  Check 4: Prevention Status not marked as Implemented or Validated"
    echo "     Current: $PREVENTION_STATUS"
fi

# Summary
echo ""
echo "═══════════════════════════════════════"
if [ $CHECKS_TOTAL -eq 0 ]; then
    echo "ℹ️  No automatic checks available for this mistake type"
    echo "   Manual verification required"
elif [ $CHECKS_PASSED -eq $CHECKS_TOTAL ]; then
    echo "✅ All checks passed ($CHECKS_PASSED/$CHECKS_TOTAL)"
    echo ""
    echo "Recommendation: Update status to 'monitoring' to track effectiveness"
    echo "   ./scripts/update_mistake_status.sh ${MISTAKE_ID} monitoring"
else
    echo "⚠️  Checks passed: $CHECKS_PASSED/$CHECKS_TOTAL"
    echo ""
    echo "Some prevention measures may not be fully implemented."
    echo "Review the prevention section and update CLAUDE.md or CONTRIBUTING.md"
fi
