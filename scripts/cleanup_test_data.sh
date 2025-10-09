#!/bin/bash

# Clean up test data from production database
# This removes the test folder, projects, tasks, and tags created by setup_test_database.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}OmniFocus Test Data Cleanup${NC}"
echo "================================================"
echo ""

echo -e "${YELLOW}This will remove the following from your production database:${NC}"
echo "  - Test Projects folder (and all projects/tasks inside)"
echo "  - test-urgent tag"
echo "  - test-work tag"
echo "  - test-personal tag"
echo "  - Test Inbox Task"
echo ""

read -p "Continue with cleanup? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Cleaning up test data...${NC}"
echo ""

# Run AppleScript to remove test data
osascript <<'EOF'
tell application "OmniFocus"
    tell front document
        set cleanupLog to ""

        -- Remove test folder and all its contents
        try
            set testFolder to first folder whose name is "Test Projects"
            delete testFolder
            set cleanupLog to cleanupLog & "✓ Deleted 'Test Projects' folder\n"
        on error
            set cleanupLog to cleanupLog & "⚠ 'Test Projects' folder not found (may already be deleted)\n"
        end try

        -- Remove test tags
        try
            set urgentTag to first tag whose name is "test-urgent"
            delete urgentTag
            set cleanupLog to cleanupLog & "✓ Deleted 'test-urgent' tag\n"
        on error
            set cleanupLog to cleanupLog & "⚠ 'test-urgent' tag not found\n"
        end try

        try
            set workTag to first tag whose name is "test-work"
            delete workTag
            set cleanupLog to cleanupLog & "✓ Deleted 'test-work' tag\n"
        on error
            set cleanupLog to cleanupLog & "⚠ 'test-work' tag not found\n"
        end try

        try
            set personalTag to first tag whose name is "test-personal"
            delete personalTag
            set cleanupLog to cleanupLog & "✓ Deleted 'test-personal' tag\n"
        on error
            set cleanupLog to cleanupLog & "⚠ 'test-personal' tag not found\n"
        end try

        -- Remove test inbox task
        try
            set testInboxTask to first inbox task whose name is "Test Inbox Task"
            delete testInboxTask
            set cleanupLog to cleanupLog & "✓ Deleted 'Test Inbox Task' from inbox\n"
        on error
            set cleanupLog to cleanupLog & "⚠ 'Test Inbox Task' not found in inbox\n"
        end try

        return cleanupLog
    end tell
end tell
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}Cleanup Complete!${NC}"
    echo -e "${GREEN}================================================${NC}"
else
    echo -e "${RED}Some errors occurred during cleanup${NC}"
fi

echo ""
echo -e "${YELLOW}Note: Your test database (OmniFocus-TEST.ofocus) was NOT affected.${NC}"
echo "It still contains the test data for integration testing."
