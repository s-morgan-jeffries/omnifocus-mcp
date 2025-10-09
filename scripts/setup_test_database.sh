#!/bin/bash

# OmniFocus Test Database Setup Script
# Creates a safe test database for integration testing

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
OF4_DIR="$HOME/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application Support/OmniFocus"
PROD_DB="$OF4_DIR/OmniFocus.ofocus"
TEST_DB="$OF4_DIR/OmniFocus-TEST.ofocus"
BACKUP_DIR="$OF4_DIR/Backups"

echo -e "${GREEN}OmniFocus Test Database Setup${NC}"
echo "================================================"
echo ""

# Safety check: Verify production database exists
if [ ! -d "$PROD_DB" ]; then
    echo -e "${RED}ERROR: Production database not found at:${NC}"
    echo "$PROD_DB"
    echo ""
    echo "Please ensure OmniFocus 4 is installed and has been run at least once."
    exit 1
fi

# Check if test database already exists
if [ -d "$TEST_DB" ]; then
    echo -e "${YELLOW}WARNING: Test database already exists at:${NC}"
    echo "$TEST_DB"
    echo ""
    read -p "Do you want to delete and recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing test database..."
        rm -rf "$TEST_DB"
    else
        echo "Keeping existing test database. Exiting."
        exit 0
    fi
fi

echo -e "${GREEN}Creating test database...${NC}"
echo ""

# Create test database using AppleScript
# This creates comprehensive test data for 90% coverage
osascript <<'EOF'
tell application "OmniFocus"
    tell front document
        -- Create folder hierarchy
        set rootFolder to make new folder with properties {name:"Test Root Folder"}
        set subFolder to make new folder with properties {name:"Test Sub Folder"}

        -- Create diverse projects
        tell rootFolder
            -- Active project with multiple tasks
            set activeProject to make new project with properties {name:"Active Test Project"}
            tell activeProject
                make new task with properties {name:"Task 1 - Flagged", flagged:true}
                make new task with properties {name:"Task 2 - With Note", note:"This task has a detailed note"}
                make new task with properties {name:"Task 3 - Available"}

                -- Task with subtasks
                set parentTask to make new task with properties {name:"Parent Task"}
                tell parentTask
                    make new task with properties {name:"Subtask 1"}
                    make new task with properties {name:"Subtask 2"}
                end tell
            end tell

            -- On-hold project
            set onHoldProj to make new project with properties {name:"On Hold Test Project", status:on hold}
            tell onHoldProj
                make new task with properties {name:"Blocked Task"}
            end tell

            -- Completed project (will be marked done later)
            set completedProj to make new project with properties {name:"Completed Test Project", status:done}

            -- Test Project 1 and 2 for backwards compatibility
            set testProject1 to make new project with properties {name:"Test Project 1"}
            tell testProject1
                make new task with properties {name:"Test Task 1", note:"This is a test task"}
                make new task with properties {name:"Test Task 2"}
            end tell

            set testProject2 to make new project with properties {name:"Test Project 2"}
            tell testProject2
                make new task with properties {name:"Another Test Task"}
            end tell
        end tell

        -- Project in subfolder
        tell subFolder
            set subProject to make new project with properties {name:"Subfolder Project"}
            tell subProject
                make new task with properties {name:"Subfolder Task"}
            end tell
        end tell

        -- Create a standalone project (no folder)
        set standaloneProj to make new project with properties {name:"Standalone Project"}
        tell standaloneProj
            make new task with properties {name:"Standalone Task 1"}
            make new task with properties {name:"Standalone Task 2"}
        end tell

        -- Create diverse tags
        make new tag with properties {name:"urgent"}
        make new tag with properties {name:"work"}
        make new tag with properties {name:"personal"}
        make new tag with properties {name:"waiting"}
        make new tag with properties {name:"someday"}
        -- Backwards compatibility tags
        make new tag with properties {name:"test-urgent"}
        make new tag with properties {name:"test-work"}
        make new tag with properties {name:"test-personal"}

        -- Create inbox tasks with various states
        make new inbox task with properties {name:"Inbox Task 1"}
        make new inbox task with properties {name:"Inbox Task 2 - Flagged", flagged:true}
        make new inbox task with properties {name:"Inbox Task 3 - With Note", note:"Inbox note"}
        -- Backwards compatibility
        make new inbox task with properties {name:"Test Inbox Task"}

        return "Comprehensive test data created successfully"
    end tell
end tell
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Test data created in OmniFocus${NC}"
else
    echo -e "${RED}✗ Failed to create test data${NC}"
    exit 1
fi

# Wait a moment for OmniFocus to save
sleep 2

# Copy the current database to create test database
echo "Copying database to test location..."
cp -R "$PROD_DB" "$TEST_DB"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Test database created successfully${NC}"
else
    echo -e "${RED}✗ Failed to copy database${NC}"
    exit 1
fi

# Set up environment variable instructions
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Test Database Setup Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Test database location:"
echo "  $TEST_DB"
echo ""
echo -e "${YELLOW}IMPORTANT: To run integration tests, set:${NC}"
echo ""
echo "  export OMNIFOCUS_TEST_MODE=true"
echo "  export OMNIFOCUS_TEST_DATABASE=\"OmniFocus-TEST.ofocus\""
echo ""
echo "Add these to your shell profile (~/.zshrc or ~/.bashrc) for persistence."
echo ""
echo -e "${YELLOW}WARNING:${NC}"
echo "- Integration tests will ONLY work with the test database"
echo "- Your production database will be protected by safety guards"
echo "- Never run tests without OMNIFOCUS_TEST_MODE=true"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Set the environment variables above"
echo "2. Run: pytest tests/test_integration_real.py"
echo ""
