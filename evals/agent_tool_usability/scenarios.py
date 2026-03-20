"""Blind agent eval scenarios for OmniFocus MCP tool usability.

Each scenario tests whether an agent can correctly plan tool calls
based ONLY on tool descriptions (no codebase, no external knowledge).
"""

SCENARIOS = [
    # =========================================================================
    # Category 1: Core OmniFocus Concepts
    # =========================================================================
    {
        "id": 1,
        "category": "Core OF Concepts",
        "name": "Defer vs Due Date",
        "prompt": (
            "I need to call the dentist, but not until next Monday March 16. "
            "The appointment itself is next Friday March 20."
        ),
        "expected": {
            "tools": ["create_task"],
            "key_params": {
                "create_task": {
                    "task_name": "Call the dentist",
                    "defer_date": "2026-03-16",
                    "due_date": "2026-03-20",
                }
            },
        },
        "scoring_notes": (
            "PASS: defer_date=Monday (hidden until then), due_date=Friday (deadline). "
            "FAIL: due_date=Monday (confuses 'not until' with deadline). "
            "FAIL: Only sets one date."
        ),
        "safety_critical": False,
    },
    {
        "id": 2,
        "category": "Core OF Concepts",
        "name": "Sequential Project with Dependencies",
        "prompt": (
            "Create a project called 'Kitchen Renovation' where tasks must be done in order: "
            "get quotes, pick contractor, sign contract, demolition, installation."
        ),
        "expected": {
            "tools": ["create_project", "create_task", "create_task", "create_task", "create_task", "create_task"],
            "key_params": {
                "create_project": {"name": "Kitchen Renovation", "sequential": True},
                "create_task": {"project_id": "<returned_id>"},
            },
        },
        "scoring_notes": (
            "PASS: sequential=True, tasks created in specified order, uses returned project ID. "
            "PARTIAL: sequential=True but doesn't mention task order matters. "
            "FAIL: sequential=False or tries to set explicit dependencies."
        ),
        "safety_critical": False,
    },
    {
        "id": 3,
        "category": "Core OF Concepts",
        "name": "Available Tasks",
        "prompt": "Show me only the tasks I can actually work on right now.",
        "expected": {
            "tools": ["get_tasks"],
            "key_params": {"get_tasks": {"available_only": True}},
        },
        "scoring_notes": (
            "PASS: get_tasks(available_only=True). "
            "PARTIAL: Combines multiple filters to approximate 'available'. "
            "FAIL: No filter or wrong filter."
        ),
        "safety_critical": False,
    },
    {
        "id": 4,
        "category": "Core OF Concepts",
        "name": "Flagged Semantics",
        "prompt": (
            "I want to focus on these 3 tasks today: task-001, task-002, task-003."
        ),
        "expected": {
            "tools": ["update_tasks"],
            "key_params": {
                "update_tasks": {
                    "task_ids": ["task-001", "task-002", "task-003"],
                    "flagged": True,
                }
            },
        },
        "scoring_notes": (
            "PASS: update_tasks with flagged=True, correct task IDs as list. "
            "PARTIAL: Uses update_task 3x instead of batch. "
            "FAIL: Uses set_focus (focus is for projects/folders, not tasks)."
        ),
        "safety_critical": False,
    },

    # =========================================================================
    # Category 2: Tool Selection
    # =========================================================================
    {
        "id": 5,
        "category": "Tool Selection",
        "name": "Single vs Batch Boundary",
        "prompt": (
            "Rename task task-123 to 'Buy groceries' and also flag tasks task-456 and task-789."
        ),
        "expected": {
            "tools": ["update_task", "update_tasks"],
            "key_params": {
                "update_task": {"task_id": "task-123", "task_name": "Buy groceries"},
                "update_tasks": {"task_ids": ["task-456", "task-789"], "flagged": True},
            },
        },
        "scoring_notes": (
            "PASS: update_task for rename (single), update_tasks for flag (batch). "
            "PARTIAL: Uses update_task 3x (works but misses batch). "
            "FAIL: Tries to use update_tasks for rename (it doesn't accept task_name)."
        ),
        "safety_critical": False,
    },
    {
        "id": 6,
        "category": "Tool Selection",
        "name": "Move Task via update_task",
        "prompt": "Move task task-100 from my inbox to the 'Home Repairs' project (proj-200).",
        "expected": {
            "tools": ["update_task"],
            "key_params": {
                "update_task": {"task_id": "task-100", "project_id": "proj-200"}
            },
        },
        "scoring_notes": (
            "PASS: update_task(task_id='task-100', project_id='proj-200'). "
            "FAIL: Looks for a move_task tool or tries delete+create."
        ),
        "safety_critical": False,
    },
    {
        "id": 7,
        "category": "Tool Selection",
        "name": "Drop vs Delete (SAFETY)",
        "prompt": (
            "I'm not going to do the 'Learn Mandarin' project (proj-888) anymore, "
            "but I want to keep it in my records."
        ),
        "expected": {
            "tools": ["update_project"],
            "key_params": {
                "update_project": {"project_id": "proj-888", "status": "dropped"}
            },
        },
        "scoring_notes": (
            "PASS: update_project(status='dropped'). "
            "FAIL: delete_projects (permanent deletion, user wants to keep records). "
            "FAIL: status='done' (project wasn't completed, it was abandoned)."
        ),
        "safety_critical": True,
    },
    {
        "id": 8,
        "category": "Tool Selection",
        "name": "Reorder for Dependencies",
        "prompt": (
            "In my sequential project, task-B needs to happen before task-A. "
            "Currently task-A is first."
        ),
        "expected": {
            "tools": ["reorder_task"],
            "key_params": {
                "reorder_task": {"task_id": "task-B", "before_task_id": "task-A"}
            },
        },
        "scoring_notes": (
            "PASS: reorder_task(task_id='task-B', before_task_id='task-A'). "
            "PARTIAL: Correct tool but swapped parameters. "
            "FAIL: Tries to set explicit dependencies or uses wrong tool."
        ),
        "safety_critical": False,
    },

    # =========================================================================
    # Category 3: Parameter Usage
    # =========================================================================
    {
        "id": 9,
        "category": "Parameter Usage",
        "name": "Tags on Create vs Add Tags on Update",
        "prompt": (
            "Create a task 'Review PR' with tags Computer and Work, "
            "then add the tag 'Urgent' to existing task task-555."
        ),
        "expected": {
            "tools": ["create_task", "update_task"],
            "key_params": {
                "create_task": {"task_name": "Review PR", "tags": ["Computer", "Work"]},
                "update_task": {"task_id": "task-555", "add_tags": ["Urgent"]},
            },
        },
        "scoring_notes": (
            "PASS: create_task tags as native list, update_task add_tags as native list. "
            "PARTIAL: Correct tools but uses 'tags' instead of 'add_tags' on update. "
            "FAIL: Wrong tools or missing tag assignment entirely."
        ),
        "safety_critical": False,
    },
    {
        "id": 10,
        "category": "Parameter Usage",
        "name": "Clear a Date",
        "prompt": "Remove the due date from task task-300.",
        "expected": {
            "tools": ["update_task"],
            "key_params": {"update_task": {"task_id": "task-300", "due_date": ""}},
        },
        "scoring_notes": (
            "PASS: update_task(due_date=''). Empty string to clear. "
            "PARTIAL: update_task(due_date=None) — omitting means no change per docs. "
            "FAIL: Tries to delete/recreate the task or uses a non-existent clear function."
        ),
        "safety_critical": False,
    },
    {
        "id": 11,
        "category": "Parameter Usage",
        "name": "Mutual Exclusivity",
        "prompt": (
            "Create a subtask 'Buy nails' under task task-400 in project proj-500."
        ),
        "expected": {
            "tools": ["create_task"],
            "key_params": {
                "create_task": {
                    "task_name": "Buy nails",
                    "parent_task_id": "task-400",
                }
            },
        },
        "scoring_notes": (
            "PASS: create_task(parent_task_id='task-400') — only parent_task_id, NOT project_id. "
            "Notes that subtask inherits parent's project. "
            "FAIL: Passes both project_id and parent_task_id (mutually exclusive)."
        ),
        "safety_critical": False,
    },
    {
        "id": 12,
        "category": "Parameter Usage",
        "name": "Tag Filter AND Semantics",
        "prompt": "Show me all tasks tagged with both 'Errands' and 'Weekend'.",
        "expected": {
            "tools": ["get_tasks"],
            "key_params": {
                "get_tasks": {"tag_filter": ["Errands", "Weekend"]}
            },
        },
        "scoring_notes": (
            "PASS: get_tasks(tag_filter=['Errands', 'Weekend']). "
            "PARTIAL: Two separate queries, one per tag. "
            "FAIL: Wrong parameter or uses query instead of tag_filter."
        ),
        "safety_critical": False,
    },

    # =========================================================================
    # Category 4: Multi-Step Workflows
    # =========================================================================
    {
        "id": 13,
        "category": "Multi-Step Workflows",
        "name": "Daily Planning",
        "prompt": "Help me plan my day. What should I focus on?",
        "expected": {
            "tools": ["get_tasks", "get_tasks", "get_tasks", "get_tasks"],
            "key_params": {
                "query_1": {"overdue": True},
                "query_2": {"flagged_only": True},
                "query_3": {"inbox_only": True},
                "query_4": {"next_only": True},
            },
        },
        "scoring_notes": (
            "PASS: Follows the PLANNING PATTERN from server instructions — 4 queries "
            "(overdue, flagged+available, inbox, next). "
            "PARTIAL: Gets 2-3 of the 4 queries. "
            "FAIL: Single get_tasks() with no filters, or completely wrong approach."
        ),
        "safety_critical": False,
    },
    {
        "id": 14,
        "category": "Multi-Step Workflows",
        "name": "Project Creation with Phases",
        "prompt": (
            "Set up a 'Website Redesign' project under the 'Work' folder. "
            "It's sequential. Add these tasks in order: wireframes, design mockups, "
            "frontend build, backend API, QA testing, launch. "
            "Tag all tasks with 'Web Team'. Set review every 2 weeks."
        ),
        "expected": {
            "tools": ["create_project"] + ["create_task"] * 6,
            "key_params": {
                "create_project": {
                    "name": "Website Redesign",
                    "folder_path": "Work",
                    "sequential": True,
                    "review_interval_weeks": 2,
                },
                "create_task": {
                    "project_id": "<returned_id>",
                    "tags": ["Web Team"],
                },
            },
        },
        "scoring_notes": (
            "PASS: create_project with all params, 6x create_task in order with tags as native list, "
            "uses returned project ID. "
            "PARTIAL: Missing some params (e.g., no review_interval_weeks). "
            "FAIL: Parallel project or wrong task order."
        ),
        "safety_critical": False,
    },
    {
        "id": 15,
        "category": "Multi-Step Workflows",
        "name": "Project Review",
        "prompt": "Which of my projects are overdue for review?",
        "expected": {
            "tools": ["get_projects"],
            "key_params": {"get_projects": {}},
        },
        "scoring_notes": (
            "PASS: get_projects() then explains need to check last_reviewed + review_interval_weeks. "
            "Recognizes there's no direct 'overdue for review' filter. "
            "PARTIAL: Calls get_projects but doesn't mention review fields. "
            "FAIL: Looks for a non-existent review-specific tool."
        ),
        "safety_critical": False,
    },

    # =========================================================================
    # Category 5: Edge Cases
    # =========================================================================
    {
        "id": 16,
        "category": "Edge Cases",
        "name": "Done vs Dropped (SAFETY)",
        "prompt": (
            "I finished the 'Q1 Report' project (proj-777) — all tasks are done."
        ),
        "expected": {
            "tools": ["update_project"],
            "key_params": {
                "update_project": {"project_id": "proj-777", "status": "done"}
            },
        },
        "scoring_notes": (
            "PASS: update_project(status='done'). "
            "FAIL: status='dropped' (dropped = abandoned, not completed). "
            "FAIL: delete_projects (user completed it, didn't want it removed)."
        ),
        "safety_critical": True,
    },
    {
        "id": 17,
        "category": "Edge Cases",
        "name": "Focus Limitations",
        "prompt": "Focus on just task task-999 so I only see that one thing.",
        "expected": {
            "tools": [],
            "key_params": {},
        },
        "scoring_notes": (
            "PASS: Recognizes set_focus only works on projects and folders, NOT tasks. "
            "Suggests alternative (e.g., flag the task, or focus on the task's project). "
            "FAIL: Calls set_focus with a task ID (will error). "
            "FAIL: Doesn't mention the limitation."
        ),
        "safety_critical": True,
    },
    {
        "id": 18,
        "category": "Edge Cases",
        "name": "Inbox Completion",
        "prompt": "Complete all tasks in my inbox.",
        "expected": {
            "tools": ["get_tasks", "update_tasks"],
            "key_params": {
                "get_tasks": {"inbox_only": True},
                "update_tasks": {"completed": True},
            },
        },
        "scoring_notes": (
            "PASS: get_tasks(inbox_only=True) then update_tasks(task_ids=[...], completed=True). "
            "Bonus: Notes that completing unprocessed inbox items bypasses GTD 'process' step. "
            "PARTIAL: Correct approach but uses update_task per-task instead of batch. "
            "FAIL: Wrong tool or tries to delete inbox tasks."
        ),
        "safety_critical": False,
    },

    # =========================================================================
    # Category 6: Documentation Gap Scenarios (#263, #264)
    # =========================================================================
    {
        "id": 19,
        "category": "Documentation Gaps",
        "name": "Action Group — Blocked Parent Interpretation",
        "prompt": (
            "I ran get_tasks for my project and got back this task:\n"
            '{"id": "task-700", "name": "Renovate bathroom", "blocked": true, '
            '"subtaskCount": 3, "sequential": true}\n'
            "Why is this task blocked? Is something wrong?"
        ),
        "expected": {
            "tools": [],
            "key_params": {},
        },
        "scoring_notes": (
            "PASS: Recognizes this is an action group (task with subtasks). Explains that "
            "the parent appears blocked because its subtasks are active — this is normal. "
            "Suggests checking the subtasks via get_tasks(parent_task_id='task-700'). "
            "PARTIAL: Correctly identifies subtasks but doesn't explain the blocked behavior. "
            "FAIL: Interprets blocked as an error, suggests it's stuck in a sequential project, "
            "or tries to 'unblock' it."
        ),
        "safety_critical": False,
    },
    {
        "id": 20,
        "category": "Documentation Gaps",
        "name": "Next Task Semantics",
        "prompt": (
            "I have a parallel project with 5 tasks. When I call get_tasks, "
            "all 5 have next=true. But in my sequential project, only 1 task has "
            "next=true. Is that right? What does 'next' mean?"
        ),
        "expected": {
            "tools": [],
            "key_params": {},
        },
        "scoring_notes": (
            "PASS: Correctly explains that 'next' means 'first available action' in a sequential "
            "project/action group — only one at a time. In parallel projects, all incomplete tasks "
            "are 'next' because they're all available simultaneously. "
            "PARTIAL: Gets the sequential part right but doesn't explain parallel behavior. "
            "FAIL: Says it's a bug or gives incorrect explanation."
        ),
        "safety_critical": False,
    },
    {
        "id": 21,
        "category": "Documentation Gaps",
        "name": "Inherited Dates — Empty Due Date",
        "prompt": (
            "My project 'Q2 Planning' has a due date of April 15. But when I "
            "get_tasks(project_id='proj-q2'), the tasks show dueDate as empty. "
            "The OmniFocus UI shows them as due April 15 though. What's going on?"
        ),
        "expected": {
            "tools": [],
            "key_params": {},
        },
        "scoring_notes": (
            "PASS: Explains that dueDate reflects effective dates — tasks inheriting a due date "
            "from their project WILL show that date in dueDate (not empty). This is expected "
            "behavior, not a bug. Concludes the user should see April 15 in dueDate. "
            "PARTIAL: Acknowledges effective date inheritance but is uncertain about the outcome. "
            "FAIL: Says dates show directly-assigned only (stale pre-v0.9.0 behavior), or says "
            "it's a bug with no resolution."
        ),
        "safety_critical": False,
    },
    {
        "id": 22,
        "category": "Documentation Gaps",
        "name": "Sequential Ambiguity — Parallel vs Single Actions List",
        "prompt": (
            "I see two projects with sequential=false in get_projects. One is my "
            "'Home Repairs' project (tasks can be done in any order) and the other "
            "is 'Errands' (a grab-bag of unrelated tasks). Are they the same type?"
        ),
        "expected": {
            "tools": [],
            "key_params": {},
        },
        "scoring_notes": (
            "PASS: Explains that sequential=false is now deprecated/ambiguous, but the "
            "projectType field distinguishes them clearly. 'Home Repairs' is likely "
            "'parallel' (has a completion goal), 'Errands' is likely 'single_actions' "
            "(grab-bag, no completion goal, cannot auto-complete). Recommends checking "
            "projectType in get_projects output to confirm. "
            "PARTIAL: Knows the three types exist but doesn't mention projectType field. "
            "FAIL: Says they're the same type, or doesn't know about Single Actions Lists."
        ),
        "safety_critical": False,
    },
    {
        "id": 23,
        "category": "Documentation Gaps",
        "name": "Completing Recurring Tasks",
        "prompt": (
            "I have a recurring task 'Water plants' that repeats every week. "
            "If I use update_task(completed=True), will it create the next occurrence "
            "or just mark this one done and kill the recurrence?"
        ),
        "expected": {
            "tools": [],
            "key_params": {},
        },
        "scoring_notes": (
            "PASS: Explains that completed=True uses 'mark complete' internally, which "
            "correctly handles recurring tasks by spawning the next occurrence. The recurrence "
            "will continue. "
            "PARTIAL: Says it will complete but isn't sure about recurrence behavior. "
            "FAIL: Says it will kill the recurrence or doesn't know."
        ),
        "safety_critical": False,
    },

    # =========================================================================
    # Category 7: Planned Date Scenarios (#252)
    # =========================================================================
    {
        "id": 24,
        "category": "Planned Date",
        "name": "Planned Date vs Defer Date",
        "prompt": (
            "I want to schedule 'Write blog post' for next Wednesday March 18, "
            "but I could start it earlier if I have free time. It's due Friday March 20."
        ),
        "expected": {
            "tools": ["create_task"],
            "key_params": {
                "create_task": {
                    "task_name": "Write blog post",
                    "planned_date": "2026-03-18",
                    "due_date": "2026-03-20",
                }
            },
        },
        "scoring_notes": (
            "PASS: planned_date=Wednesday (scheduling intent, no hard constraint), "
            "due_date=Friday (deadline). Does NOT set defer_date (user said they could start earlier). "
            "PARTIAL: Uses defer_date instead of planned_date (wrong — defer hides the task until that date). "
            "FAIL: Only sets due_date, or confuses planned with defer."
        ),
        "safety_critical": False,
    },
    {
        "id": 25,
        "category": "Planned Date",
        "name": "Three Dates Scenario",
        "prompt": (
            "Create a task 'Prepare presentation'. I can't start until Monday March 16 "
            "(I need materials from a colleague). I'm planning to work on it Wednesday March 18. "
            "It's due for the meeting on Friday March 20."
        ),
        "expected": {
            "tools": ["create_task"],
            "key_params": {
                "create_task": {
                    "task_name": "Prepare presentation",
                    "defer_date": "2026-03-16",
                    "planned_date": "2026-03-18",
                    "due_date": "2026-03-20",
                }
            },
        },
        "scoring_notes": (
            "PASS: All three dates correct — defer=Monday (can't start before), "
            "planned=Wednesday (intend to work on it), due=Friday (deadline). "
            "PARTIAL: Gets 2 of 3 dates right. "
            "FAIL: Only uses 2 date types, or confuses which date serves which purpose."
        ),
        "safety_critical": False,
    },
    {
        "id": 26,
        "category": "Planned Date",
        "name": "Clear Planned Date",
        "prompt": (
            "I had task-600 planned for Wednesday but my schedule changed. "
            "Remove the planned date — I'll figure out when to do it later."
        ),
        "expected": {
            "tools": ["update_task"],
            "key_params": {
                "update_task": {"task_id": "task-600", "planned_date": ""}
            },
        },
        "scoring_notes": (
            "PASS: update_task(task_id='task-600', planned_date='') — empty string to clear. "
            "FAIL: Uses None/null (omitting means no change per docs). "
            "FAIL: Tries to delete the task or uses a non-existent clear function."
        ),
        "safety_critical": False,
    },

    # =========================================================================
    # Category 8: Recurrence Scenarios (#260)
    # =========================================================================
    {
        "id": 27,
        "category": "Recurrence",
        "name": "Read Repeat Summary",
        "prompt": (
            "I ran get_tasks and got this task back:\n"
            '{"id": "task-800", "name": "Team standup", "isRecurring": true, '
            '"recurrence": "FREQ=WEEKLY;INTERVAL=1;BYDAY=MO,WE,FR", '
            '"repetitionMethod": "fixed", '
            '"repeatSummary": "Every week on Mon, Wed, Fri"}\n'
            "How often does this task repeat?"
        ),
        "expected": {
            "tools": [],
            "key_params": {},
        },
        "scoring_notes": (
            "PASS: References repeatSummary ('Every week on Mon, Wed, Fri') to answer the question. "
            "Does not try to parse the raw recurrence RRULE. "
            "PARTIAL: Parses the RRULE manually instead of using repeatSummary. "
            "FAIL: Says it can't determine the recurrence schedule."
        ),
        "safety_critical": False,
    },
    {
        "id": 28,
        "category": "Recurrence",
        "name": "Modify Recurrence",
        "prompt": (
            "I have a task (task-810) that repeats every week. Can you change it to repeat "
            "every 2 weeks instead?"
        ),
        "expected": {
            "tools": ["update_task"],
            "key_params": {
                "update_task": {
                    "task_id": "task-810",
                    "recurrence": "FREQ=WEEKLY;INTERVAL=2",
                }
            },
        },
        "scoring_notes": (
            "PASS: update_task(task_id='task-810', recurrence='FREQ=WEEKLY;INTERVAL=2'). "
            "Uses RRULE format with INTERVAL=2 for biweekly. "
            "PARTIAL: Correct tool but wrong RRULE syntax (e.g., 'FREQ=BIWEEKLY'). "
            "FAIL: Says recurrence can't be modified, or uses wrong tool."
        ),
        "safety_critical": False,
    },
    {
        "id": 29,
        "category": "Recurrence",
        "name": "Repetition Method Semantics",
        "prompt": (
            "I completed 'Water plants' which repeats weekly. The task data shows "
            'repetitionMethod: "due_after_completion". When will the next occurrence '
            "be due — next Monday, or one week from today?"
        ),
        "expected": {
            "tools": [],
            "key_params": {},
        },
        "scoring_notes": (
            "PASS: Explains that 'due_after_completion' means the next due date is calculated "
            "from the completion date, so it will be due one week from when you completed it "
            "(not a fixed day like Monday). Contrasts with 'fixed' which would always be the "
            "same day each period. "
            "PARTIAL: Gives correct answer but doesn't explain the mechanism. "
            "FAIL: Ignores repetitionMethod or says it will be next Monday."
        ),
        "safety_critical": False,
    },
    {
        "id": 30,
        "category": "Recurrence",
        "name": "Remove Recurrence",
        "prompt": "I want to stop task task-900 from repeating. How do I remove the recurrence?",
        "expected": {
            "tools": ["update_task"],
            "key_params": {
                "update_task": {
                    "task_id": "task-900",
                    "recurrence": "",
                }
            },
        },
        "scoring_notes": (
            "PASS: update_task(task_id='task-900', recurrence='') — empty string to remove. "
            "PARTIAL: Correct tool but uses None instead of empty string. "
            "FAIL: Says recurrence can't be removed, or suggests deleting the task."
        ),
        "safety_critical": False,
    },
    {
        "id": 31,
        "category": "Recurrence",
        "name": "Set Recurrence with Method",
        "prompt": (
            "Make task task-820 repeat daily, but I want the next due date to be based "
            "on when I actually complete it, not on a fixed schedule."
        ),
        "expected": {
            "tools": ["update_task"],
            "key_params": {
                "update_task": {
                    "task_id": "task-820",
                    "recurrence": "FREQ=DAILY",
                    "repetition_method": "due_after_completion",
                }
            },
        },
        "scoring_notes": (
            "PASS: update_task with recurrence='FREQ=DAILY' and "
            "repetition_method='due_after_completion'. "
            "PARTIAL: Correct recurrence but wrong or missing method (defaults to 'fixed'). "
            "FAIL: Says recurrence can't be set, or uses wrong tool."
        ),
        "safety_critical": False,
    },
    {
        "id": 32,
        "category": "Recurrence",
        "name": "Add Recurrence to Non-Recurring Task",
        "prompt": (
            "Task task-830 'Take vitamins' doesn't repeat yet. Make it repeat every day "
            "on a fixed schedule."
        ),
        "expected": {
            "tools": ["update_task"],
            "key_params": {
                "update_task": {
                    "task_id": "task-830",
                    "recurrence": "FREQ=DAILY",
                    "repetition_method": "fixed",
                }
            },
        },
        "scoring_notes": (
            "PASS: update_task with recurrence='FREQ=DAILY' and repetition_method='fixed'. "
            "Also acceptable: omitting repetition_method since 'fixed' is the default. "
            "FAIL: Says recurrence can't be added to existing tasks, or creates a new task."
        ),
        "safety_critical": False,
    },

    # =========================================================================
    # Category 9: Tag Status (#259)
    # =========================================================================
    {
        "id": 33,
        "category": "Tag Status",
        "name": "Drop a Tag",
        "prompt": (
            "I'm no longer using the 'Low Energy' tag. I don't want to delete it "
            "(tasks still reference it), but I want it hidden from my tag picker. "
            "Tasks with this tag should still be available and actionable. "
            "Tag ID is tag-050."
        ),
        "expected": {
            "tools": ["update_tag"],
            "key_params": {
                "update_tag": {
                    "tag_id": "tag-050",
                    "status": "dropped",
                }
            },
        },
        "scoring_notes": (
            "PASS: update_tag(tag_id='tag-050', status='dropped') — understands "
            "dropped = hidden but preserved. "
            "PARTIAL: Uses delete_tags (destructive, contradicts 'don't delete'). "
            "FAIL: Says tags can't be hidden/dropped, or tries a non-existent tool."
        ),
        "safety_critical": False,
    },
    {
        "id": 34,
        "category": "Tag Status",
        "name": "Distinguish Tag Statuses",
        "prompt": (
            "I ran get_tags and see three tags:\n"
            '- {"id": "tag-051", "name": "Errands", "status": "active"}\n'
            '- {"id": "tag-052", "name": "Waiting", "status": "on hold"}\n'
            '- {"id": "tag-053", "name": "Archive", "status": "dropped"}\n'
            "I want 'Waiting' to be usable again — tasks with this tag should be "
            "available. And 'Archive' should stay hidden."
        ),
        "expected": {
            "tools": ["update_tag"],
            "key_params": {
                "update_tag": {
                    "tag_id": "tag-052",
                    "status": "active",
                }
            },
        },
        "scoring_notes": (
            "PASS: Only updates Waiting (tag-052) to status='active'. Does NOT touch "
            "Archive. Understands on_hold = tasks blocked, active = tasks available. "
            "PARTIAL: Updates Waiting correctly but also unnecessarily touches Archive. "
            "FAIL: Confuses on_hold with dropped, or sets wrong status."
        ),
        "safety_critical": True,
    },
    {
        "id": 35,
        "category": "Project Type",
        "name": "Create Single Actions List",
        "prompt": (
            "I want to create a new 'Someday/Maybe' list in OmniFocus — a grab-bag "
            "of ideas that has no completion goal and shouldn't auto-complete when I "
            "tick off items. How do I create it?"
        ),
        "expected": {
            "tools": ["create_project"],
            "key_params": {
                "create_project": {"project_type": "single_actions"},
            },
        },
        "scoring_notes": (
            "PASS: create_project(name='Someday/Maybe', project_type='single_actions'). "
            "Understands that single_actions = no completion goal, cannot auto-complete. "
            "PARTIAL: Creates with sequential=False (parallel) instead — works but doesn't "
            "capture the SAL semantics. Or creates correctly but doesn't explain why "
            "single_actions is the right choice. "
            "FAIL: Uses project_type='parallel', says SALs can't be created via the API, "
            "or tries a non-existent parameter."
        ),
        "safety_critical": False,
    },
    {
        "id": 36,
        "category": "Folder Status",
        "name": "Drop Folder (Archive Without Deleting)",
        "prompt": (
            "I have a folder called 'Old Work' (folder ID: folder-999) that I want "
            "to archive — hide it from view without deleting it. How do I do that?"
        ),
        "expected": {
            "tools": ["update_folder"],
            "key_params": {
                "update_folder": {"folder_id": "folder-999", "status": "dropped"},
            },
        },
        "scoring_notes": (
            "PASS: update_folder(folder_id='folder-999', status='dropped'). "
            "Understands dropped = hidden but preserved. Optionally notes that "
            "status='active' would restore it. "
            "PARTIAL: Uses correct tool but explains semantics incorrectly. "
            "FAIL: Tries delete_projects, says folders can't be hidden, or uses wrong tool."
        ),
        "safety_critical": False,
    },
    {
        "id": 37,
        "category": "Next Review Date",
        "name": "Force Project Review Date",
        "prompt": (
            "I have a project with ID proj-abc. I want to force it to come up for review "
            "on April 15th, 2026, regardless of when it was last reviewed or what the "
            "review interval is set to. How do I do that?"
        ),
        "expected": {
            "tools": ["update_project"],
            "key_params": {
                "update_project": {"project_id": "proj-abc", "next_review_date": "2026-04-15"},
            },
        },
        "scoring_notes": (
            "PASS: update_project(project_id='proj-abc', next_review_date='2026-04-15'). "
            "Correctly uses next_review_date to override the calculated date. "
            "PARTIAL: Uses last_reviewed instead of next_review_date, or uses both. "
            "FAIL: Says it can't be done, uses review_interval_weeks only, or uses wrong tool."
        ),
        "safety_critical": False,
    },
    {
        "id": 38,
        "category": "Complete With Last Action",
        "name": "Enable Auto-Complete When Last Task Done",
        "prompt": (
            "I have a project with ID proj-xyz. I want it to automatically mark itself "
            "as complete when I check off its last remaining task. How do I enable that?"
        ),
        "expected": {
            "tools": ["update_project"],
            "key_params": {
                "update_project": {"project_id": "proj-xyz", "completed_by_children": True},
            },
        },
        "scoring_notes": (
            "PASS: update_project(project_id='proj-xyz', completed_by_children=True). "
            "Correctly uses completed_by_children to enable auto-completion. "
            "PARTIAL: Mentions the right concept but uses wrong parameter name or tool. "
            "FAIL: Says it can't be done, uses status='done', or doesn't mention completed_by_children."
        ),
        "safety_critical": False,
    },
    {
        "id": 39,
        "category": "Next Occurrence Dates",
        "name": "Read Next Occurrence Date",
        "prompt": (
            "I have a recurring task 'Weekly team standup' that repeats every Monday. "
            "When is the next occurrence due? I don't want to complete the current one "
            "just to find out."
        ),
        "expected": {
            "tools": ["get_tasks"],
            "key_params": {},
        },
        "scoring_notes": (
            "PASS: Suggests using get_tasks to fetch the task and reading the nextDueDate "
            "field (or nextDeferDate/nextPlannedDate). Understands these fields show the "
            "next occurrence without needing to complete the current one. "
            "PARTIAL: Suggests get_tasks but doesn't mention the nextDueDate field. "
            "FAIL: Says you have to complete the task to see the next occurrence, "
            "or tries to calculate manually from the recurrence rule."
        ),
        "safety_critical": False,
    },
    {
        "id": 40,
        "category": "Stalled Projects",
        "name": "Find Projects With No Available Actions",
        "prompt": (
            "Which of my projects have no available actions right now? "
            "I want to review anything that might be stuck or needs new tasks added."
        ),
        "expected": {
            "tools": ["get_projects"],
            "key_params": {
                "get_projects": {"stalled_only": True},
            },
        },
        "scoring_notes": (
            "PASS: get_projects(stalled_only=True). "
            "PARTIAL: Uses get_projects(include_task_health=True) and filters manually, "
            "or mentions stalled concept but uses wrong param name. "
            "FAIL: Loops through all projects manually, uses get_tasks instead, "
            "or says it can't be done."
        ),
        "safety_critical": False,
    },
    {
        "id": 41,
        "category": "Catch Up Automatically",
        "name": "Missed Recurrence Behavior",
        "prompt": (
            "I have a daily task 'Take vitamins' that I haven't completed in 5 days. "
            "When I complete it, will I get 5 overdue occurrences flooding my inbox, "
            "or just one catch-up? How can I tell?"
        ),
        "expected": {
            "tools": ["get_tasks"],
            "key_params": {},
        },
        "scoring_notes": (
            "PASS: Suggests fetching the task with get_tasks and checking the "
            "catchUpAutomatically field. Explains that true = one catch-up occurrence, "
            "false = each missed interval spawns its own. "
            "PARTIAL: Mentions the field exists but doesn't explain the semantics clearly. "
            "FAIL: Says it depends on the repetition method only, doesn't mention "
            "catchUpAutomatically, or says there's no way to tell."
        ),
        "safety_critical": False,
    },
    {
        "id": 42,
        "category": "Tag Exclusivity",
        "name": "Mutually Exclusive Tag Warning",
        "prompt": (
            "I have a 'Priority' tag group with child tags 'High', 'Medium', 'Low'. "
            "A task currently has the 'High' tag. If I use update_task(add_tags=['Low']), "
            "will it keep both 'High' and 'Low', or will something weird happen?"
        ),
        "expected": {
            "tools": ["get_tags"],
            "key_params": {},
        },
        "scoring_notes": (
            "PASS: Warns that the Priority tag group might have childrenAreMutuallyExclusive=true, "
            "which would cause 'High' to be silently removed when 'Low' is added. Suggests "
            "checking get_tags to verify the exclusivity setting. "
            "PARTIAL: Mentions exclusivity concept but doesn't reference the specific field. "
            "FAIL: Says both tags will coexist, or doesn't warn about silent removal."
        ),
        "safety_critical": True,
    },
    # ── Project Dates ──────────────────────────────────────────────────
    {
        "id": 43,
        "category": "Project Dates",
        "name": "Create Project with Due Date",
        "prompt": (
            "Create a project called 'Q3 Report' in the 'Work' folder that must be "
            "completed by July 15, 2026. It should become available starting June 1, 2026."
        ),
        "expected": {
            "tools": ["create_project"],
            "key_params": {
                "create_project": {
                    "name": "Q3 Report",
                    "folder_path": "Work",
                    "due_date": "2026-07-15",
                    "defer_date": "2026-06-01",
                }
            },
        },
        "scoring_notes": (
            "PASS: Uses create_project with due_date for deadline and defer_date for "
            "availability start. Both in ISO format. "
            "PARTIAL: Gets one date right but not the other, or uses update_project "
            "as a second step instead of setting at creation. "
            "FAIL: Tries to set dates on tasks instead of the project, or doesn't "
            "use the date parameters at all."
        ),
        "safety_critical": False,
    },
    {
        "id": 44,
        "category": "Project Dates",
        "name": "Clear Project Due Date",
        "prompt": (
            "Project 'proj-abc' currently has a due date. I want to remove the due date "
            "so it's no longer deadline-driven."
        ),
        "expected": {
            "tools": ["update_project"],
            "key_params": {
                "update_project": {
                    "project_id": "proj-abc",
                    "due_date": "",
                }
            },
        },
        "scoring_notes": (
            "PASS: Uses update_project with due_date=\"\" (empty string to clear). "
            "PARTIAL: Uses update_project but sets due_date to null/None instead of "
            "empty string. "
            "FAIL: Tries to delete and recreate the project, or doesn't know how to "
            "clear a date."
        ),
        "safety_critical": False,
    },
    {
        "id": 45,
        "category": "Project Dates",
        "name": "Check Project Dates",
        "prompt": (
            "I want to see what dates are set on project 'proj-xyz' — specifically "
            "its due date, defer date, and planned date."
        ),
        "expected": {
            "tools": ["get_projects"],
            "key_params": {
                "get_projects": {
                    "project_id": "proj-xyz",
                }
            },
        },
        "scoring_notes": (
            "PASS: Uses get_projects with project_id filter. Mentions that dueDate, "
            "deferDate, plannedDate are returned in the project dict. "
            "PARTIAL: Uses get_projects but doesn't mention the specific date fields "
            "by name. "
            "FAIL: Tries to use get_tasks or a non-existent get_project_dates tool."
        ),
        "safety_critical": False,
    },
    # ── Task Movement ──────────────────────────────────────────────────
    {
        "id": 46,
        "category": "Task Movement",
        "name": "Make Task a Subtask",
        "prompt": (
            "I have a task 'Write introduction' (task-101) that's currently in my inbox. "
            "I want to make it a subtask of 'Draft report' (task-200), which is in the "
            "'Q3 Report' project."
        ),
        "expected": {
            "tools": ["update_task"],
            "key_params": {
                "update_task": {
                    "task_id": "task-101",
                    "parent_task_id": "task-200",
                }
            },
        },
        "scoring_notes": (
            "PASS: Uses update_task with task_id and parent_task_id. Does NOT also "
            "pass project_id (mutually exclusive — subtask inherits parent's project). "
            "PARTIAL: Uses update_task correctly but also passes project_id. "
            "FAIL: Tries to use a non-existent move_task tool, or uses project_id "
            "instead of parent_task_id."
        ),
        "safety_critical": False,
    },
    # ── Text Search ────────────────────────────────────────────────────
    {
        "id": 47,
        "category": "Text Search",
        "name": "Search Tasks by Keyword",
        "prompt": (
            "Do I have any tasks related to 'mortgage'? I'm not sure which "
            "project they'd be in."
        ),
        "expected": {
            "tools": ["get_tasks"],
            "key_params": {
                "get_tasks": {
                    "query": "mortgage",
                }
            },
        },
        "scoring_notes": (
            "PASS: Uses get_tasks with query='mortgage' (no project filter). "
            "PARTIAL: Uses query but also unnecessarily restricts to a specific "
            "project or adds filters that weren't requested. "
            "FAIL: Tries to list all tasks and filter client-side, or uses "
            "tag_filter instead of query."
        ),
        "safety_critical": False,
    },
    # ── Tag Hierarchy ──────────────────────────────────────────────────
    {
        "id": 48,
        "category": "Tag Hierarchy",
        "name": "Find Parent of Nested Tag",
        "prompt": (
            "I have a tag called 'High' that I think is nested under an 'Energy' "
            "parent tag. How can I confirm this?"
        ),
        "expected": {
            "tools": ["get_tags"],
            "key_params": {},
        },
        "scoring_notes": (
            "PASS: Uses get_tags and references parentTagId field to identify "
            "that 'High' has a non-empty parentTagId pointing to the 'Energy' tag. "
            "PARTIAL: Uses get_tags but doesn't mention parentTagId by name. "
            "FAIL: Tries to use a non-existent get_tag_hierarchy tool or doesn't "
            "know how to check tag nesting."
        ),
        "safety_critical": False,
    },
    # ── Dropping ───────────────────────────────────────────────────────
    {
        "id": 49,
        "category": "Dropping",
        "name": "Drop a Task",
        "prompt": (
            "I have a task 'Learn Esperanto' (task-500) that I've decided I'm never "
            "going to do. I don't want to delete it — I just want to abandon it."
        ),
        "expected": {
            "tools": ["update_task"],
            "key_params": {
                "update_task": {
                    "task_id": "task-500",
                    "status": "dropped",
                }
            },
        },
        "scoring_notes": (
            "PASS: Uses update_task with status='dropped'. Does NOT use delete_tasks. "
            "PARTIAL: Uses update_task but with completed=True instead of dropped. "
            "FAIL: Uses delete_tasks (destructive, can't recover)."
        ),
        "safety_critical": True,
    },
    {
        "id": 50,
        "category": "Dropping",
        "name": "Drop Multiple Projects",
        "prompt": (
            "I want to abandon these three projects: proj-A, proj-B, proj-C. "
            "Don't delete them, just mark them as abandoned."
        ),
        "expected": {
            "tools": ["update_projects"],
            "key_params": {
                "update_projects": {
                    "project_ids": ["proj-A", "proj-B", "proj-C"],
                    "status": "dropped",
                }
            },
        },
        "scoring_notes": (
            "PASS: Uses update_projects (batch) with status='dropped'. "
            "PARTIAL: Uses update_project 3 times individually instead of batch. "
            "FAIL: Uses delete_projects (destructive)."
        ),
        "safety_critical": True,
    },
    # ── Inherited Status ───────────────────────────────────────────────
    {
        "id": 51,
        "category": "Inherited Status",
        "name": "Tasks in Completed Project",
        "prompt": (
            "I completed a project last month but now get_tasks is returning some "
            "tasks from it as active (completed=false). The project shows as done "
            "in OmniFocus. Why are these tasks showing up?"
        ),
        "expected": {
            "tools": [],
            "key_params": {},
        },
        "scoring_notes": (
            "PASS: Explains that completed=false is expected (task-level status isn't "
            "inherited), but the available field accounts for container status — those "
            "tasks should show available=false. Recommends available_only=True to "
            "exclude them. "
            "PARTIAL: Correctly recommends available_only=True but doesn't explain why "
            "completed=false is expected. "
            "FAIL: Says this is a bug, or suggests marking each task complete individually."
        ),
        "safety_critical": False,
    },
    # ── Project Reordering ────────────────────────────────────────────────
    {
        "id": 52,
        "category": "Project Reordering",
        "name": "Reorder Project Within Folder",
        "prompt": (
            "I have three projects in my Work folder: proj-A, proj-B, proj-C "
            "(in that order). I want proj-C to appear first, before proj-A."
        ),
        "expected": {
            "tools": ["reorder_project"],
            "key_params": {
                "reorder_project": {
                    "project_id": "proj-C",
                    "before_project_id": "proj-A",
                }
            },
        },
        "scoring_notes": (
            "PASS: reorder_project(project_id='proj-C', before_project_id='proj-A'). "
            "PARTIAL: Correct tool but swapped parameters or used after instead of before. "
            "FAIL: Tries to use update_project or reorder_task instead."
        ),
        "safety_critical": False,
    },
    # ── Tag Exclusivity: Creation & Configuration ─────────────────────────
    {
        "id": 53,
        "category": "Tag Exclusivity",
        "name": "Create Mutually Exclusive Tag Group",
        "prompt": (
            "I want to set up a 'Priority' tag group where each task can only have one "
            "priority level at a time. If a task has 'High' and I assign 'Low', "
            "the 'High' tag should be automatically removed. Create the Priority "
            "parent tag with child tags High, Medium, and Low."
        ),
        "expected": {
            "tools": ["create_tag", "create_tag", "create_tag", "create_tag"],
            "key_params": {
                "create_tag (parent)": {
                    "name": "Priority",
                    "children_are_mutually_exclusive": True,
                },
                "create_tag (children)": {
                    "parent_tag": "Priority",
                },
            },
        },
        "scoring_notes": (
            "PASS: Creates parent tag with children_are_mutually_exclusive=True, "
            "then creates child tags with parent_tag='Priority'. "
            "PARTIAL: Correct structure but forgets children_are_mutually_exclusive=True. "
            "FAIL: Doesn't use children_are_mutually_exclusive, or creates flat tags "
            "without parent-child relationship."
        ),
        "safety_critical": False,
    },
    {
        "id": 54,
        "category": "Tag Exclusivity",
        "name": "Toggle Exclusivity on Existing Tag",
        "prompt": (
            "I have an existing 'Energy' tag (ID: tag-energy-001) with child tags "
            "'High Energy', 'Medium Energy', 'Low Energy'. Right now a task can have "
            "multiple energy levels, but I want to change it so only one energy level "
            "can be assigned at a time. How do I fix this?"
        ),
        "expected": {
            "tools": ["update_tag"],
            "key_params": {
                "update_tag": {
                    "tag_id": "tag-energy-001",
                    "children_are_mutually_exclusive": True,
                },
            },
        },
        "scoring_notes": (
            "PASS: update_tag(tag_id='tag-energy-001', children_are_mutually_exclusive=True). "
            "PARTIAL: Correct tool and concept but wrong parameter name or missing tag_id. "
            "FAIL: Suggests recreating tags, or doesn't know about children_are_mutually_exclusive."
        ),
        "safety_critical": False,
    },
]
