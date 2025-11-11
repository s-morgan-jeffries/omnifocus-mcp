#!/bin/bash
# Automated tag creation with pre-tag hygiene checks
# Usage: ./scripts/create_tag.sh <tag-name>
#
# This script automates the tag creation workflow by:
# 1. Running pre-tag hygiene checks
# 2. Creating the git tag if checks pass
#
# Prevents the manual workflow confusion experienced in #116

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if tag name provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Tag name required${NC}"
    echo "Usage: $0 <tag-name>"
    echo "Example: $0 v0.6.7-rc1"
    exit 1
fi

TAG_NAME="$1"

# Validate tag name format (vX.Y.Z or vX.Y.Z-rcN)
if ! echo "$TAG_NAME" | grep -qE '^v[0-9]+\.[0-9]+\.[0-9]+(-rc[0-9]+)?$'; then
    echo -e "${RED}Error: Invalid tag name format${NC}"
    echo "Tag name must follow pattern: vX.Y.Z or vX.Y.Z-rcN"
    echo "Examples: v0.6.7, v0.7.0-rc1"
    exit 1
fi

# Get project root (parent of scripts directory)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Check if tag already exists
if git tag -l | grep -q "^${TAG_NAME}$"; then
    echo -e "${RED}Error: Tag ${TAG_NAME} already exists${NC}"
    echo "To delete and recreate: git tag -d ${TAG_NAME}"
    exit 1
fi

# Check for pending releases (RC tags without final tags)
# Only check when creating RC tags (prevents false positives when creating final tags)
if echo "$TAG_NAME" | grep -qE '^v[0-9]+\.[0-9]+\.[0-9]+-rc[0-9]+$'; then
    echo "Checking for pending releases..."
    if ! "$SCRIPT_DIR/check_pending_releases.sh"; then
        echo ""
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${RED}⚠️  BLOCKING: Pending release(s) detected${NC}"
        echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo "You must complete or document existing RC releases before creating new ones."
        echo ""
        echo "Options:"
        echo "  1. Complete pending release: ./scripts/create_tag.sh <version>"
        echo "  2. Document as skipped in CHANGELOG and delete RC tag"
        echo "  3. Override check (not recommended): SKIP_PENDING_CHECK=1 $0 $TAG_NAME"
        echo ""
        exit 1
    fi
    echo ""
fi

# Check if pre-tag hook exists
PRE_TAG_HOOK="$PROJECT_ROOT/scripts/git-hooks/pre-tag"
if [ ! -f "$PRE_TAG_HOOK" ]; then
    echo -e "${RED}Error: Pre-tag hook not found at $PRE_TAG_HOOK${NC}"
    exit 1
fi

if [ ! -x "$PRE_TAG_HOOK" ]; then
    echo -e "${RED}Error: Pre-tag hook is not executable${NC}"
    echo "Run: chmod +x $PRE_TAG_HOOK"
    exit 1
fi

# Display what we're about to do
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}Automated Tag Creation${NC}"
echo -e "${YELLOW}========================================${NC}"
echo "Tag name: ${TAG_NAME}"
echo ""

# Run pre-tag hygiene checks
echo -e "${YELLOW}Step 1: Running pre-tag hygiene checks...${NC}"
echo ""

if "$PRE_TAG_HOOK" "$TAG_NAME"; then
    echo ""
    echo -e "${GREEN}✓ Hygiene checks passed${NC}"
    echo ""
else
    EXIT_CODE=$?
    echo ""
    echo -e "${RED}✗ Hygiene checks failed (exit code: $EXIT_CODE)${NC}"
    echo ""
    echo "Review the output above to see what failed."
    echo "Fix the issues and try again."
    echo ""
    echo "If you want to approve known issues:"
    echo "  ./scripts/approve_hygiene_checks.sh ${TAG_NAME}"
    echo ""
    exit $EXIT_CODE
fi

# Create the tag
echo -e "${YELLOW}Step 2: Creating git tag...${NC}"
if git tag "$TAG_NAME"; then
    echo -e "${GREEN}✓ Tag ${TAG_NAME} created successfully${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Review the tag: git show ${TAG_NAME}"
    echo "2. Push the tag: git push origin ${TAG_NAME}"
    echo ""
    echo -e "${GREEN}Tag creation complete!${NC}"
else
    echo -e "${RED}✗ Failed to create tag${NC}"
    exit 1
fi
