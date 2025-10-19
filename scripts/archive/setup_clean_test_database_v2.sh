#!/bin/bash

# Create a CLEAN test database using OmniFocus's New Database feature

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

OF4_DIR="$HOME/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application Support/OmniFocus"
TEST_DB="$OF4_DIR/OmniFocus-TEST.ofocus"

echo -e "${GREEN}Clean Test Database Setup (Method 2)${NC}"
echo "================================================"
echo ""

# Remove old test database if it exists
if [ -d "$TEST_DB" ]; then
    echo -e "${YELLOW}Removing old test database...${NC}"
    rm -rf "$TEST_DB"
fi

echo -e "${GREEN}Creating test database using OmniFocus...${NC}"
echo ""
echo "MANUAL STEPS REQUIRED:"
echo "1. Open OmniFocus"
echo "2. Go to: File → New Database..."
echo "3. Name it: OmniFocus-TEST"
echo "4. Save it to: $OF4_DIR"
echo "5. Press Enter here when done"
echo ""
read -p "Press Enter after you've created the blank database..."

# Check if database was created
if [ ! -d "$TEST_DB" ]; then
    echo -e "${RED}Test database not found!${NC}"
    echo "Expected location: $TEST_DB"
    exit 1
fi

echo ""
echo -e "${GREEN}Database created! Now populating with test data...${NC}"
echo ""

# Populate it with test data
osascript <<'EOF'
tell application "OmniFocus"
    tell front document
        -- Verify we're using the test database
        set dbName to name of it
        if dbName does not contain "TEST" then
            error "ERROR: Not using test database! Current: " & dbName
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

        -- Standalone project
        set standaloneProj to make new project with properties {name:"Standalone Project"}
        tell standaloneProj
            make new task with properties {name:"Standalone Task 1"}
            make new task with properties {name:"Standalone Task 2"}
        end tell

        -- Tags
        make new tag with properties {name:"urgent"}
        make new tag with properties {name:"work"}
        make new tag with properties {name:"personal"}
        make new tag with properties {name:"waiting"}
        make new tag with properties {name:"someday"}
        make new tag with properties {name:"test-urgent"}
        make new tag with properties {name:"test-work"}
        make new tag with properties {name:"test-personal"}

        -- Inbox tasks
        make new inbox task with properties {name:"Inbox Task 1"}
        make new inbox task with properties {name:"Inbox Task 2 - Flagged", flagged:true}
        make new inbox task with properties {name:"Inbox Task 3 - With Note", note:"Inbox note"}
        make new inbox task with properties {name:"Test Inbox Task"}

        return "✓ Populated: " & dbName
    end tell
end tell
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}Test Database Ready!${NC}"
    echo -e "${GREEN}================================================${NC}"
    echo ""
    echo "You can now run integration tests:"
    echo "  ./scripts/run_integration_tests.sh"
    echo ""
else
    echo -e "${RED}Failed to populate test database${NC}"
    exit 1
fi
