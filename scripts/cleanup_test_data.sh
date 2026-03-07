#!/bin/bash
# Clean up ALL test and benchmark data from the OmniFocus test database.
#
# Removes projects, tasks, tags, and folders created by:
#   - scripts/setup_benchmark_data.sh (prefix: "Bench ", "bench-")
#   - scripts/setup_test_database.sh (prefix: "Test ", "test-")
#   - integration tests (prefix: "__bench_", "__test_")
#
# Prerequisites:
#   export OMNIFOCUS_TEST_MODE=true
#   export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"

set -e

if [ "$OMNIFOCUS_TEST_MODE" != "true" ]; then
    echo "ERROR: OMNIFOCUS_TEST_MODE must be set to 'true'"
    echo "Run: export OMNIFOCUS_TEST_MODE=true"
    exit 1
fi

echo "Cleaning up ALL test data from OmniFocus test database..."
echo ""

osascript <<'APPLESCRIPT'
use AppleScript version "2.4"
use scripting additions

tell application "OmniFocus"
    tell front document
        set deletedCount to 0

        -- Delete test/benchmark tags
        set testTags to every flattened tag whose name starts with "bench-" or name starts with "test-"
        set tagCount to count of testTags
        repeat with t in testTags
            delete t
        end repeat
        set deletedCount to deletedCount + tagCount

        -- Also delete non-prefixed test tags
        repeat with tagName in {"urgent", "work", "personal", "waiting", "someday"}
            try
                set t to first flattened tag whose name is tagName
                delete t
                set deletedCount to deletedCount + 1
            end try
        end repeat

        -- Delete test/benchmark folders (cascades to contained projects/tasks)
        set testFolders to every flattened folder whose name starts with "Bench " or name starts with "Test "
        set folderCount to count of testFolders
        repeat with f in testFolders
            delete f
        end repeat
        set deletedCount to deletedCount + folderCount

        -- Delete standalone test/benchmark projects (not in folders)
        set testProjects to every flattened project whose name starts with "Bench " or name starts with "Test " or name starts with "__bench_" or name starts with "Active Test" or name starts with "On Hold Test" or name starts with "Completed Test" or name starts with "Standalone " or name starts with "Subfolder "
        set projCount to count of testProjects
        repeat with p in testProjects
            delete p
        end repeat
        set deletedCount to deletedCount + projCount

        -- Delete test inbox tasks
        set testInbox to every inbox task whose name starts with "Bench " or name starts with "Test " or name starts with "Inbox Task" or name starts with "__bench_"
        set inboxCount to count of testInbox
        repeat with t in testInbox
            delete t
        end repeat
        set deletedCount to deletedCount + inboxCount

        return "Deleted " & deletedCount & " items (" & tagCount & " tags, " & folderCount & " folders, " & projCount & " projects, " & inboxCount & " inbox tasks)"
    end tell
end tell
APPLESCRIPT

if [ $? -eq 0 ]; then
    echo "Test data cleanup complete."
else
    echo "ERROR: Cleanup failed"
    exit 1
fi
