#!/bin/bash

# Clean up comprehensive test data from production database

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Cleaning Comprehensive Test Data${NC}"
echo "================================================"
echo ""

echo -e "${YELLOW}This will remove comprehensive test data:${NC}"
echo "  - Test Root Folder (and all contents)"
echo "  - Test Sub Folder (and all contents)"
echo "  - All tags: urgent, work, personal, waiting, someday, test-*"
echo "  - All inbox tasks starting with 'Inbox Task' or 'Test Inbox'"
echo ""

read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Cleaning up...${NC}"
echo ""

osascript <<'EOF'
tell application "OmniFocus"
    tell front document
        set cleanupLog to ""

        -- Remove Test Root Folder
        try
            set rootFolder to first folder whose name is "Test Root Folder"
            delete rootFolder
            set cleanupLog to cleanupLog & "✓ Deleted 'Test Root Folder' and all contents\n"
        on error
            set cleanupLog to cleanupLog & "⚠ 'Test Root Folder' not found\n"
        end try

        -- Remove Test Sub Folder
        try
            set subFolder to first folder whose name is "Test Sub Folder"
            delete subFolder
            set cleanupLog to cleanupLog & "✓ Deleted 'Test Sub Folder' and all contents\n"
        on error
            set cleanupLog to cleanupLog & "⚠ 'Test Sub Folder' not found\n"
        end try

        -- Remove standalone project
        try
            set standaloneProj to first flattened project whose name is "Standalone Project"
            delete standaloneProj
            set cleanupLog to cleanupLog & "✓ Deleted 'Standalone Project'\n"
        on error
            set cleanupLog to cleanupLog & "⚠ 'Standalone Project' not found\n"
        end try

        -- Remove tags
        set tagNames to {"urgent", "work", "personal", "waiting", "someday", "test-urgent", "test-work", "test-personal"}
        repeat with tagName in tagNames
            try
                set theTag to first tag whose name is tagName
                delete theTag
                set cleanupLog to cleanupLog & "✓ Deleted '" & tagName & "' tag\n"
            on error
                set cleanupLog to cleanupLog & "⚠ '" & tagName & "' tag not found\n"
            end try
        end repeat

        -- Remove inbox tasks
        set inboxTaskNames to {"Inbox Task 1", "Inbox Task 2 - Flagged", "Inbox Task 3 - With Note", "Test Inbox Task"}
        repeat with taskName in inboxTaskNames
            try
                set theTask to first inbox task whose name is taskName
                delete theTask
                set cleanupLog to cleanupLog & "✓ Deleted inbox task '" & taskName & "'\n"
            on error
                set cleanupLog to cleanupLog & "⚠ Inbox task '" & taskName & "' not found\n"
            end try
        end repeat

        return cleanupLog
    end tell
end tell
EOF

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Cleanup Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Your production database should now be clean."
