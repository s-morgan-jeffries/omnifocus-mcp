#!/bin/bash

# Create Comprehensive Test Data for 90% Coverage Testing
# This creates a rich test database with diverse scenarios

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Creating Comprehensive Test Data${NC}"
echo "This will create a rich test database supporting 90% test coverage"
echo "================================================"
echo ""

# Create comprehensive test data
osascript <<'EOF'
tell application "OmniFocus"
    tell front document
        set testData to {}

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
            set completedProj to make new project with properties {name:"Completed Test Project", status:done}
        end tell

        -- Project in subfolder
        tell subFolder
            set subProject to make new project with properties {name:"Subfolder Project"}
            tell subProject
                make new task with properties {name:"Subfolder Task"}
            end tell
        end tell

        -- Create diverse tags
        make new tag with properties {name:"urgent"}
        make new tag with properties {name:"work"}
        make new tag with properties {name:"personal"}
        make new tag with properties {name:"waiting"}
        make new tag with properties {name:"someday"}

        -- Create inbox tasks with various states
        make new inbox task with properties {name:"Inbox Task 1"}
        make new inbox task with properties {name:"Inbox Task 2 - Flagged", flagged:true}
        make new inbox task with properties {name:"Inbox Task 3 - With Note", note:"Inbox note"}

        -- Create a standalone project (no folder)
        set standaloneProj to make new project with properties {name:"Standalone Project"}
        tell standaloneProj
            make new task with properties {name:"Standalone Task 1"}
            make new task with properties {name:"Standalone Task 2"}
        end tell

        return "Comprehensive test data created successfully"
    end tell
end tell
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Comprehensive test data created${NC}"
    echo ""
    echo "Test database now includes:"
    echo "  • 2 folders (root + subfolder)"
    echo "  • 5 projects (active, on-hold, completed, in-subfolder, standalone)"
    echo "  • ~15 tasks (with various states: flagged, noted, parent/child)"
    echo "  • 5 tags (urgent, work, personal, waiting, someday)"
    echo "  • 3 inbox tasks (plain, flagged, with note)"
    echo ""
    echo -e "${YELLOW}Next: Wait 2 seconds for OmniFocus to save, then run setup_test_database.sh${NC}"
else
    echo "Failed to create test data"
    exit 1
fi
