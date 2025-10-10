#!/bin/bash

# Create a CLEAN test database without touching production
# This script creates a minimal OmniFocus database from scratch

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

OF4_DIR="$HOME/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application Support/OmniFocus"
TEST_DB="$OF4_DIR/OmniFocus-TEST.ofocus"

echo -e "${GREEN}Clean Test Database Setup${NC}"
echo "================================================"
echo ""

# Check if OmniFocus is running
if pgrep -x "OmniFocus" > /dev/null; then
    echo -e "${YELLOW}OmniFocus is currently running.${NC}"
    echo "This script needs to create a blank database."
    echo ""
    read -p "Quit OmniFocus and continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled."
        exit 0
    fi

    osascript -e 'tell application "OmniFocus" to quit'
    sleep 2
fi

# Remove old test database if it exists
if [ -d "$TEST_DB" ]; then
    echo -e "${YELLOW}Removing old test database...${NC}"
    rm -rf "$TEST_DB"
fi

echo -e "${GREEN}Creating blank test database...${NC}"
echo ""

# Create a minimal database structure
# We'll create the directory structure that OmniFocus expects
mkdir -p "$TEST_DB"

# Copy the minimal database structure from a template
# OmniFocus databases are actually packages with specific structure
# The easiest way is to let OmniFocus create it

echo "Opening blank test database in OmniFocus..."
open "$TEST_DB"

echo "Waiting for OmniFocus to initialize database (10 seconds)..."
sleep 10

# Now populate it with test data
echo ""
echo -e "${GREEN}Populating with comprehensive test data...${NC}"
echo ""

osascript <<'EOF'
tell application "OmniFocus"
    tell front document
        -- Verify we're using the test database
        set dbName to name of it
        if dbName does not contain "TEST" then
            error "ERROR: Not using test database! Current database: " & dbName
        end if

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

            -- Completed project
            set completedProj to make new project with properties {name:"Completed Test Project"}
            mark complete completedProj

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
        make new tag with properties {name:"test-urgent"}
        make new tag with properties {name:"test-work"}
        make new tag with properties {name:"test-personal"}

        -- Create inbox tasks
        make new inbox task with properties {name:"Inbox Task 1"}
        make new inbox task with properties {name:"Inbox Task 2 - Flagged", flagged:true}
        make new inbox task with properties {name:"Inbox Task 3 - With Note", note:"Inbox note"}
        make new inbox task with properties {name:"Test Inbox Task"}

        return "Test database populated: " & dbName
    end tell
end tell
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}Test Database Created Successfully!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo "Test database location:"
    echo "  $TEST_DB"
    echo ""
    echo "Database contains:"
    echo "  • 2 folders"
    echo "  • 6 projects (various states)"
    echo "  • ~20 tasks (various properties)"
    echo "  • 8 tags"
    echo "  • 4 inbox tasks"
    echo ""
    echo -e "${YELLOW}The test database is currently open in OmniFocus.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run integration tests: ./scripts/run_integration_tests.sh"
    echo "  2. Or manually: OMNIFOCUS_TEST_MODE=true OMNIFOCUS_TEST_DATABASE=\"OmniFocus-TEST.ofocus\" pytest tests/test_integration_real.py -v"
    echo ""
    echo "To switch back to production:"
    echo "  File → Open → Select your production database"
else
    echo -e "${RED}Failed to populate test database${NC}"
    exit 1
fi
