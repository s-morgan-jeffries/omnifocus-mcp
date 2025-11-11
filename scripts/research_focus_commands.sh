#!/bin/bash
# Research script to test OmniFocus focus commands
# This script tests various AppleScript commands for setting focus on OmniFocus items

echo "=== Testing OmniFocus Focus Commands ==="
echo ""

# Test 1: Get a sample task ID from the test database
echo "Test 1: Getting a sample task ID..."
TASK_ID=$(osascript <<'EOF'
tell application "OmniFocus"
    tell default document
        set testTasks to flattened tasks whose name contains "Test"
        if (count of testTasks) > 0 then
            set firstTask to item 1 of testTasks
            return id of firstTask
        else
            return "NO_TEST_TASK_FOUND"
        end if
    end tell
end tell
EOF
)

if [ "$TASK_ID" = "NO_TEST_TASK_FOUND" ]; then
    echo "  ❌ No test tasks found. Please run scripts/setup_test_database.sh first."
    exit 1
fi

echo "  ✅ Found test task ID: $TASK_ID"
echo ""

# Test 2: Try to set focus on the task
echo "Test 2: Testing 'set focus' on task..."
FOCUS_RESULT=$(osascript <<EOF
tell application "OmniFocus"
    tell default document
        set targetTask to first flattened task whose id is "$TASK_ID"
        tell front document window
            set focus to targetTask
            return "SUCCESS"
        end tell
    end tell
end tell
EOF
)

if [ $? -eq 0 ]; then
    echo "  ✅ Focus command succeeded: $FOCUS_RESULT"
else
    echo "  ❌ Focus command failed"
fi
echo ""

# Test 3: Get a sample project ID
echo "Test 3: Getting a sample project ID..."
PROJECT_ID=$(osascript <<'EOF'
tell application "OmniFocus"
    tell default document
        set testProjects to flattened projects whose name contains "Test"
        if (count of testProjects) > 0 then
            set firstProject to item 1 of testProjects
            return id of firstProject
        else
            return "NO_TEST_PROJECT_FOUND"
        end if
    end tell
end tell
EOF
)

if [ "$PROJECT_ID" = "NO_TEST_PROJECT_FOUND" ]; then
    echo "  ⚠️  No test projects found"
else
    echo "  ✅ Found test project ID: $PROJECT_ID"

    # Test 4: Try to set focus on the project
    echo ""
    echo "Test 4: Testing 'set focus' on project..."
    FOCUS_PROJECT_RESULT=$(osascript <<EOF
tell application "OmniFocus"
    tell default document
        set targetProject to first flattened project whose id is "$PROJECT_ID"
        tell front document window
            set focus to targetProject
            return "SUCCESS"
        end tell
    end tell
end tell
EOF
)

    if [ $? -eq 0 ]; then
        echo "  ✅ Focus on project succeeded: $FOCUS_PROJECT_RESULT"
    else
        echo "  ❌ Focus on project failed"
    fi
fi
echo ""

# Test 5: Check if tabs are supported
echo "Test 5: Testing tab management support..."
TAB_TEST=$(osascript <<'EOF' 2>&1
tell application "OmniFocus"
    tell default document
        tell front document window
            -- Try to access tabs property
            try
                set tabCount to count of tabs
                return "TABS_SUPPORTED: " & tabCount
            on error errMsg
                return "TABS_NOT_SUPPORTED: " & errMsg
            end try
        end tell
    end tell
end tell
EOF
)

echo "  Result: $TAB_TEST"
echo ""

# Test 6: Check if folders support focus
echo "Test 6: Testing folder focus support..."
FOLDER_ID=$(osascript <<'EOF'
tell application "OmniFocus"
    tell default document
        if (count of folders) > 0 then
            return id of item 1 of folders
        else
            return "NO_FOLDERS"
        end if
    end tell
end tell
EOF
)

if [ "$FOLDER_ID" != "NO_FOLDERS" ]; then
    echo "  ✅ Found folder ID: $FOLDER_ID"
    FOLDER_FOCUS=$(osascript <<EOF 2>&1
tell application "OmniFocus"
    tell default document
        set targetFolder to first folder whose id is "$FOLDER_ID"
        tell front document window
            try
                set focus to targetFolder
                return "SUCCESS"
            on error errMsg
                return "FAILED: " & errMsg
            end try
        end tell
    end tell
end tell
EOF
)
    echo "  Result: $FOLDER_FOCUS"
else
    echo "  ⚠️  No folders found to test"
fi
echo ""

# Test 7: Check if tags support focus
echo "Test 7: Testing tag focus support..."
TAG_ID=$(osascript <<'EOF'
tell application "OmniFocus"
    tell default document
        if (count of flattened tags) > 0 then
            return id of item 1 of flattened tags
        else
            return "NO_TAGS"
        end if
    end tell
end tell
EOF
)

if [ "$TAG_ID" != "NO_TAGS" ]; then
    echo "  ✅ Found tag ID: $TAG_ID"
    TAG_FOCUS=$(osascript <<EOF 2>&1
tell application "OmniFocus"
    tell default document
        set targetTag to first flattened tag whose id is "$TAG_ID"
        tell front document window
            try
                set focus to targetTag
                return "SUCCESS"
            on error errMsg
                return "FAILED: " & errMsg
            end try
        end tell
    end tell
end tell
EOF
)
    echo "  Result: $TAG_FOCUS"
else
    echo "  ⚠️  No tags found to test"
fi
echo ""

echo "=== Research Complete ==="
echo ""
echo "Summary:"
echo "- Task focus: Tested"
echo "- Project focus: Tested"
echo "- Folder focus: Tested"
echo "- Tag focus: Tested"
echo "- Tab management: Tested"
echo ""
echo "Next steps:"
echo "1. Review test results above"
echo "2. Implement set_focus() function based on working commands"
echo "3. Decide on tab management based on AppleScript support"
