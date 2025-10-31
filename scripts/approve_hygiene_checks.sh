#!/bin/bash
# Approve hygiene check results for a release
#
# Usage: ./scripts/approve_hygiene_checks.sh <tag-name>
# Example: ./scripts/approve_hygiene_checks.sh v0.6.6-rc1
#
# This creates an approval file that allows the pre-tag hook to proceed
# even if some hygiene checks found issues (after manual review).

set -e

# Check if tag name provided
if [ -z "$1" ]; then
    echo "❌ Error: Tag name required"
    echo ""
    echo "Usage: ./scripts/approve_hygiene_checks.sh <tag-name>"
    echo "Example: ./scripts/approve_hygiene_checks.sh v0.6.6-rc1"
    exit 1
fi

TAG_NAME="$1"

# Validate tag name format (vX.Y.Z-rcN)
if ! echo "$TAG_NAME" | grep -qE "^v[0-9]+\.[0-9]+\.[0-9]+-rc[0-9]+$"; then
    echo "❌ Error: Invalid tag name format"
    echo "   Expected: vX.Y.Z-rcN (e.g., v0.6.6-rc1)"
    echo "   Got: $TAG_NAME"
    exit 1
fi

# Check if hygiene check results file exists
RESULTS_FILE=".hygiene-check-results-${TAG_NAME}.txt"
if [ ! -f "$RESULTS_FILE" ]; then
    echo "❌ Error: Hygiene check results not found"
    echo "   Expected file: $RESULTS_FILE"
    echo ""
    echo "You must run the hygiene checks first:"
    echo "  git tag $TAG_NAME  # This triggers pre-tag hook with checks"
    echo ""
    echo "After reviewing the results, you can approve with:"
    echo "  ./scripts/approve_hygiene_checks.sh $TAG_NAME"
    exit 1
fi

# Create approval file
APPROVAL_FILE=".hygiene-approved-${TAG_NAME}"

cat > "$APPROVAL_FILE" <<EOF
# Hygiene Check Approval
# Generated: $(date)
# Tag: $TAG_NAME
# Approved By: $(git config user.name) <$(git config user.email)>

This file indicates that hygiene check results have been reviewed
and approved for release tag $TAG_NAME.

The pre-tag hook will check for this file and allow tag creation
to proceed even if some checks found issues.

**IMPORTANT:** This approval is specific to $TAG_NAME only.

Results file: $RESULTS_FILE
EOF

echo "✅ Hygiene checks approved for $TAG_NAME"
echo ""
echo "Approval file created: $APPROVAL_FILE"
echo "Results reviewed from: $RESULTS_FILE"
echo ""
echo "You can now create the tag:"
echo "  git tag $TAG_NAME"
echo ""
echo "The pre-tag hook will see the approval and proceed."
echo ""
echo "⚠️  Note: Review the results file to ensure you've addressed"
echo "   any critical issues before proceeding."
