#!/bin/bash
# Generate representative test data for performance benchmarking.
#
# Creates ~30 projects, ~200 tasks, ~10 tags across a folder hierarchy.
# Designed for performance profiling — enough variety for filters to matter,
# small enough for fast feedback loops.
#
# Prerequisites:
#   export OMNIFOCUS_TEST_MODE=true
#   export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"
#   OmniFocus must be running with the test database active.
#
# Usage:
#   ./scripts/setup_benchmark_data.sh

set -e

if [ "$OMNIFOCUS_TEST_MODE" != "true" ]; then
    echo "ERROR: OMNIFOCUS_TEST_MODE must be set to 'true'"
    echo "Run: export OMNIFOCUS_TEST_MODE=true"
    exit 1
fi

echo "Cleaning up old benchmark data..."
osascript <<'CLEANUP'
use AppleScript version "2.4"
use scripting additions

tell application "OmniFocus"
    tell front document
        -- Delete benchmark tags
        set benchTags to every flattened tag whose name starts with "bench-"
        repeat with t in benchTags
            delete t
        end repeat

        -- Delete benchmark folders (and their projects/tasks)
        set benchFolders to every flattened folder whose name starts with "Bench "
        repeat with f in benchFolders
            delete f
        end repeat

        -- Delete standalone benchmark projects
        set benchProjects to every flattened project whose name starts with "Bench "
        repeat with p in benchProjects
            delete p
        end repeat

        -- Delete benchmark inbox tasks
        set benchInbox to every inbox task whose name starts with "Bench "
        repeat with t in benchInbox
            delete t
        end repeat

        return "Cleanup complete"
    end tell
end tell
CLEANUP

if [ $? -ne 0 ]; then
    echo "WARNING: Cleanup failed (may be first run). Continuing..."
fi

echo "Setting up benchmark data in OmniFocus test database..."
echo "This will create ~30 projects, ~200 tasks, ~10 tags."
echo ""

osascript <<'APPLESCRIPT'
use AppleScript version "2.4"
use scripting additions

tell application "OmniFocus"
    tell front document

        -- Create tags first (referenced by tasks later)
        set tagUrgent to make new tag with properties {name:"bench-urgent"}
        set tagWork to make new tag with properties {name:"bench-work"}
        set tagPersonal to make new tag with properties {name:"bench-personal"}
        set tagWaiting to make new tag with properties {name:"bench-waiting"}
        set tagSomeday to make new tag with properties {name:"bench-someday"}
        set tagEmail to make new tag with properties {name:"bench-email"}
        set tagCall to make new tag with properties {name:"bench-call"}
        set tagReview to make new tag with properties {name:"bench-review"}
        set tagLowEnergy to make new tag with properties {name:"bench-low-energy"}
        set tagDeep to make new tag with properties {name:"bench-deep-work"}

        -- Create folder hierarchy
        set folderWork to make new folder with properties {name:"Bench Work"}
        set folderPersonal to make new folder with properties {name:"Bench Personal"}
        set folderArchive to make new folder with properties {name:"Bench Archive"}
        -- Nested subfolder
        set folderTeam to make new folder with properties {name:"Bench Team"}

        -- Helper: current date for relative dates
        set now to current date
        set yesterday to now - (1 * days)
        set lastWeek to now - (7 * days)
        set nextWeek to now + (7 * days)
        set nextMonth to now + (30 * days)
        set twoWeeksAgo to now - (14 * days)

        -- ============================================
        -- WORK PROJECTS (12 projects in Work folder)
        -- ============================================
        tell folderWork
            -- 1. Large active project with many tasks
            set projLarge to make new project with properties {name:"Bench Large Project", note:"A large project with many tasks for benchmarking"}
            tell projLarge
                repeat with i from 1 to 15
                    set taskProps to {name:"Large task " & i}
                    if i mod 3 = 0 then set taskProps to taskProps & {flagged:true}
                    if i mod 5 = 0 then set taskProps to taskProps & {note:"This is a note for task " & i & ". It contains some details about the work that needs to be done, including context and background information that might be relevant."}
                    make new task with properties taskProps
                end repeat
                -- Add some with due dates
                make new task with properties {name:"Large overdue task", due date:yesterday}
                make new task with properties {name:"Large upcoming task", due date:nextWeek}
                make new task with properties {name:"Large deferred task", defer date:nextWeek}
            end tell

            -- 2. Sequential project
            set projSeq to make new project with properties {name:"Bench Sequential Project", sequential:true}
            tell projSeq
                repeat with i from 1 to 8
                    make new task with properties {name:"Sequential step " & i}
                end repeat
            end tell

            -- 3. Project with deep nesting (subtasks)
            set projDeep to make new project with properties {name:"Bench Deep Nesting"}
            tell projDeep
                set parent1 to make new task with properties {name:"Parent task 1"}
                tell parent1
                    set child1 to make new task with properties {name:"Child 1.1"}
                    tell child1
                        make new task with properties {name:"Grandchild 1.1.1"}
                        make new task with properties {name:"Grandchild 1.1.2"}
                    end tell
                    make new task with properties {name:"Child 1.2"}
                end tell
                set parent2 to make new task with properties {name:"Parent task 2"}
                tell parent2
                    make new task with properties {name:"Child 2.1"}
                    make new task with properties {name:"Child 2.2"}
                    make new task with properties {name:"Child 2.3"}
                end tell
            end tell

            -- 4. Project with tagged tasks
            set projTagged to make new project with properties {name:"Bench Tagged Tasks"}
            tell projTagged
                set t1 to make new task with properties {name:"Urgent work task", flagged:true}
                add tagUrgent to tags of t1
                add tagWork to tags of t1

                set t2 to make new task with properties {name:"Email followup task"}
                add tagEmail to tags of t2
                add tagWork to tags of t2

                set t3 to make new task with properties {name:"Deep work task", note:"Requires focus and concentration. Block out 2 hours minimum."}
                add tagDeep to tags of t3

                set t4 to make new task with properties {name:"Waiting for response"}
                add tagWaiting to tags of t4

                set t5 to make new task with properties {name:"Review document"}
                add tagReview to tags of t5
                add tagWork to tags of t5
            end tell

            -- 5. Project with many overdue tasks
            set projOverdue to make new project with properties {name:"Bench Overdue Project"}
            tell projOverdue
                repeat with i from 1 to 6
                    make new task with properties {name:"Overdue task " & i, due date:lastWeek}
                end repeat
                make new task with properties {name:"Not overdue task", due date:nextMonth}
            end tell

            -- 6. Project with deferred tasks
            set projDeferred to make new project with properties {name:"Bench Deferred Project"}
            tell projDeferred
                repeat with i from 1 to 5
                    make new task with properties {name:"Deferred task " & i, defer date:nextWeek}
                end repeat
                make new task with properties {name:"Available task in deferred project"}
            end tell

            -- 7-9. Medium projects (5-7 tasks each)
            repeat with pNum from 1 to 3
                set projMed to make new project with properties {name:"Bench Medium Project " & pNum}
                tell projMed
                    repeat with i from 1 to (5 + pNum)
                        make new task with properties {name:"Medium " & pNum & " task " & i}
                    end repeat
                end tell
            end repeat

            -- 10. On-hold project
            set projHold to make new project with properties {name:"Bench On Hold Project", status:on hold}
            tell projHold
                make new task with properties {name:"On hold task 1"}
                make new task with properties {name:"On hold task 2"}
                make new task with properties {name:"On hold task 3"}
            end tell

            -- 11. Project with long notes
            set projNotes to make new project with properties {name:"Bench Long Notes Project", note:"This project has extensive notes. It covers multiple areas of concern and includes background context, acceptance criteria, and implementation details that span several paragraphs. The purpose is to test how note length affects performance."}
            tell projNotes
                make new task with properties {name:"Task with very long note", note:"This is a deliberately long note to test performance impact of note length. It includes multiple paragraphs of text, details about the task, context for why it exists, references to other work, and various other information that might be stored in a real task note. The note continues with more detail about the requirements, including edge cases to consider, potential risks, and dependencies on other tasks. This should be enough text to meaningfully test note extraction performance. Adding even more text here to simulate a real-world task note that someone has been updating over time with meeting notes, decisions, and follow-up items. Final paragraph with conclusions and next steps."}
                make new task with properties {name:"Task with short note", note:"Brief."}
                make new task with properties {name:"Task with no note"}
                make new task with properties {name:"Another long note task", note:"Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."}
            end tell

            -- 12. Empty project (no tasks)
            make new project with properties {name:"Bench Empty Project"}
        end tell

        -- ============================================
        -- PERSONAL PROJECTS (8 projects in Personal folder)
        -- ============================================
        tell folderPersonal
            -- 1. Flagged personal project
            set projFlag to make new project with properties {name:"Bench Flagged Personal"}
            tell projFlag
                repeat with i from 1 to 5
                    set t to make new task with properties {name:"Flagged personal task " & i, flagged:true}
                    add tagPersonal to tags of t
                end repeat
            end tell

            -- 2-5. Regular personal projects
            repeat with pNum from 1 to 4
                set projPers to make new project with properties {name:"Bench Personal Project " & pNum}
                tell projPers
                    repeat with i from 1 to 4
                        make new task with properties {name:"Personal " & pNum & " task " & i}
                    end repeat
                end tell
            end repeat

            -- 6. Project with mixed dates
            set projMixed to make new project with properties {name:"Bench Mixed Dates"}
            tell projMixed
                make new task with properties {name:"Past due personal", due date:twoWeeksAgo}
                make new task with properties {name:"Due this week", due date:now + (3 * days)}
                make new task with properties {name:"Due next month", due date:nextMonth}
                make new task with properties {name:"Deferred to next week", defer date:nextWeek}
                make new task with properties {name:"No dates personal task"}
            end tell

            -- 7. Someday project
            set projSomeday to make new project with properties {name:"Bench Someday Project", status:on hold}
            tell projSomeday
                repeat with i from 1 to 3
                    set t to make new task with properties {name:"Someday task " & i}
                    add tagSomeday to tags of t
                end repeat
            end tell

            -- 8. Review-focused project
            set projReview to make new project with properties {name:"Bench Weekly Review"}
            tell projReview
                set t1 to make new task with properties {name:"Review inbox"}
                add tagReview to tags of t1
                set t2 to make new task with properties {name:"Review waiting list"}
                add tagReview to tags of t2
                add tagWaiting to tags of t2
                set t3 to make new task with properties {name:"Review someday list"}
                add tagReview to tags of t3
            end tell
        end tell

        -- ============================================
        -- TEAM PROJECTS (5 projects in Team subfolder)
        -- ============================================
        tell folderTeam
            repeat with pNum from 1 to 5
                set projTeam to make new project with properties {name:"Bench Team Project " & pNum}
                tell projTeam
                    repeat with i from 1 to 3
                        set t to make new task with properties {name:"Team " & pNum & " task " & i}
                        if i = 1 then add tagWork to tags of t
                    end repeat
                end tell
            end repeat
        end tell

        -- ============================================
        -- ARCHIVE PROJECTS (5 completed projects)
        -- ============================================
        tell folderArchive
            repeat with pNum from 1 to 5
                set projArch to make new project with properties {name:"Bench Archived Project " & pNum}
                tell projArch
                    repeat with i from 1 to 3
                        make new task with properties {name:"Archived " & pNum & " task " & i}
                    end repeat
                end tell
                mark complete projArch
            end repeat
        end tell

        -- ============================================
        -- STANDALONE PROJECTS (no folder, 2 projects)
        -- ============================================
        set projStandalone1 to make new project with properties {name:"Bench Standalone 1"}
        tell projStandalone1
            repeat with i from 1 to 4
                make new task with properties {name:"Standalone task " & i}
            end repeat
        end tell

        set projStandalone2 to make new project with properties {name:"Bench Standalone 2", note:"A project without a folder"}
        tell projStandalone2
            make new task with properties {name:"Another standalone task", flagged:true}
            make new task with properties {name:"Standalone with due date", due date:nextWeek}
        end tell

        -- ============================================
        -- INBOX TASKS (10 tasks)
        -- ============================================
        make new inbox task with properties {name:"Bench inbox task 1"}
        make new inbox task with properties {name:"Bench inbox task 2", flagged:true}
        make new inbox task with properties {name:"Bench inbox task 3", note:"Inbox task with a note"}
        make new inbox task with properties {name:"Bench inbox task 4"}
        make new inbox task with properties {name:"Bench inbox task 5", flagged:true}
        set t6 to make new inbox task with properties {name:"Bench inbox urgent"}
        add tagUrgent to tags of t6
        make new inbox task with properties {name:"Bench inbox task 7"}
        set t8 to make new inbox task with properties {name:"Bench inbox call"}
        add tagCall to tags of t8
        make new inbox task with properties {name:"Bench inbox task 9"}
        make new inbox task with properties {name:"Bench inbox task 10", note:"Last inbox task with note"}

        return "Benchmark data created: ~32 projects, ~200 tasks, 10 tags, 4 folders"
    end tell
end tell
APPLESCRIPT

if [ $? -eq 0 ]; then
    echo "Benchmark data created successfully."
    echo ""
    echo "Data summary:"
    echo "  ~32 projects (12 work, 8 personal, 5 team, 5 archived, 2 standalone)"
    echo "  ~200 tasks (various: flagged, overdue, deferred, tagged, nested)"
    echo "  10 tags (bench-urgent, bench-work, bench-personal, etc.)"
    echo "  4 folders (Work, Personal, Team, Archive)"
    echo "  10 inbox tasks"
    echo ""
    echo "Run benchmarks with:"
    echo "  pytest tests/test_benchmark.py -v -s"
else
    echo "ERROR: Failed to create benchmark data"
    exit 1
fi
