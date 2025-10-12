# OmniFocus MCP Server: Quick Start Guide

## 30-Second Overview

**Goal**: Save OmniFocus users 5-10 hours per week by eliminating the "productivity tax" of mechanical task management using AI.

**Current State**:
- ✅ Basic project retrieval (get_projects, search_projects)
- ✅ Simple task creation (add_task with name and note only)
- ✅ Note addition (add_note to projects)

**Gap**: Missing tags, dates, task operations, intelligent features

---

## The Productivity Tax (What We're Solving)

```
Current Pain Points:
┌────────────────────────────────────────────────────────────┐
│ Email Processing:        2-3 min per email × 30/day       │
│                          = 60-90 min/day                   │
├────────────────────────────────────────────────────────────┤
│ Context Switching:       23-45 min recovery × 6/day       │
│                          = 2.5-4.5 hours/day               │
├────────────────────────────────────────────────────────────┤
│ Weekly Review:           2-3 hours once/week               │
│                          = 2-3 hours/week                  │
├────────────────────────────────────────────────────────────┤
│ Meeting Processing:      10-15 min × 4/week               │
│                          = 40-60 min/week                  │
├────────────────────────────────────────────────────────────┤
│ Project Setup:           20-30 min × 2/week               │
│                          = 40-60 min/week                  │
└────────────────────────────────────────────────────────────┘

TOTAL LOST TIME: 5-10 hours per week
                 20-40% of a typical work week!

AI Solution: Reduce to <1 hour/week (80-90% reduction)
```

---

## Priority Matrix: Impact vs. Effort

```
HIGH IMPACT ↑
           │
           │  UC4: Weekly Review    │ UC5: Context Switching
           │  [Analytics]           │ [AI Recommendations]
           │                        │
           │  ─────────────────────────────────────────
           │                        │
           │  UC1: Email-to-Task    │ UC2: Meeting Notes
           │  UC6: Natural Language │ UC3: Templates
           │                        │
           │                        │
           │                        │ UC7: GitHub/Jira Sync
           │  UC10: Waiting-For     │ UC8: Capacity Planning
           │                        │
           │                        │
LOW IMPACT │  UC11: Habits          │ UC12: Dependencies
           │  UC9: Reading Lists    │ UC15: Learning Tracker
           │  UC13: Voice           │ UC14: Time Tracking
           │                        │
           └────────────────────────┼─────────────────────→
             LOW EFFORT                    HIGH EFFORT
```

---

## Implementation Roadmap

```
PHASE 1: Foundation (Weeks 1-3) - MUST-HAVE
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│  Week 1: Foundation                                         │
│  ├─ Enhanced add_task (tags, dates, flags)    [2 days]     │
│  ├─ get_tasks with filtering                  [2 days]     │
│  └─ complete_task / update_task               [1 day]      │
│                                                              │
│  Week 2: Quick Wins                                         │
│  ├─ Natural language task creation            [2 days]     │
│  ├─ Email forwarding endpoint                 [3 days]     │
│  └─ Basic action item extraction              [in email]   │
│                                                              │
│  Week 3: Intelligence                                       │
│  ├─ Project health analysis                   [3 days]     │
│  ├─ Context switching assistant                [2 days]     │
│  └─ Beta user recruitment                      [2 days]     │
│                                                              │
│  Delivers: UC1, UC4, UC5, UC6                              │
│  Time Saved: 3-5 hours/week per user                       │
└─────────────────────────────────────────────────────────────┘

PHASE 2: Intelligence (Weeks 4-8) - SHOULD-HAVE
┌─────────────────────────────────────────────────────────────┐
│  ├─ Meeting transcription integration         [4 days]     │
│  ├─ create_project tool                       [3 days]     │
│  ├─ Template instantiation                    [5 days]     │
│  ├─ Calendar integration basics               [5 days]     │
│  └─ Beta testing and iteration                [ongoing]    │
│                                                              │
│  Delivers: UC2, UC3                                         │
│  Time Saved: Additional 2-3 hours/week per user            │
└─────────────────────────────────────────────────────────────┘

PHASE 3: Advanced (Months 3-4) - NICE-TO-HAVE
┌─────────────────────────────────────────────────────────────┐
│  ├─ GitHub/Jira integration                                 │
│  ├─ Waiting-for tracking                                    │
│  ├─ Capacity planning                                       │
│  └─ Voice interface                                         │
│                                                              │
│  Delivers: UC7, UC8, UC10, UC13                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Use Case Dependency Tree

```
Foundation (Week 1)
    │
    ├─ Enhanced add_task ────────┬─────────────────────────────┐
    │                             │                             │
    ├─ get_tasks ─────────────────┼──────────────────┐          │
    │                             │                  │          │
    └─ complete/update_task ──────┼──────┐           │          │
                                  │      │           │          │
                                  ▼      ▼           ▼          ▼
                          UC1: Email  UC4: Review  UC5: Context  UC6: NL
                          to Task     Assistant   Switching    Creation
                             │          │           │            │
                             │          └───────────┼────────────┘
                             │                      │
                             ▼                      ▼
                          UC2: Meeting          create_project
                          Notes                      │
                                                     ▼
                                                 UC3: Templates
                                                     │
                          ┌──────────────────────────┴────────────┐
                          ▼                                        ▼
                    UC7: GitHub/Jira                     UC8: Capacity
                    Integration                          Planning
                          │                                        │
                          └────────────────┬───────────────────────┘
                                           ▼
                                    UC10: Waiting-For
                                    Tracking
```

---

## The 5 Core Personas (Prioritized)

```
1. THE OVERWHELMED (Sarah, James, Linda)
   Pain: Drowning in information
   Need: Inbox processor, meeting notes, daily digest
   Priority: HIGHEST - affects everyone
   ▼ Delivers UC1, UC2, UC4

2. THE CONTEXT SWITCHER (Marcus, Priya, Robert)
   Pain: 23-45 min context recovery
   Need: Project summaries, smart suggestions
   Priority: HIGHEST - huge time drain
   ▼ Delivers UC5, UC7

3. THE TEMPLATE USER (Jasmine, Robert, James)
   Pain: Recreating similar projects
   Need: Smart template instantiation
   Priority: HIGH - significant time savings
   ▼ Delivers UC3, UC6

4. THE CROSS-TOOL JUGGLER (Marcus, Priya, Taylor)
   Pain: Multiple systems, duplication
   Need: Bi-directional sync, unified view
   Priority: MEDIUM-HIGH - developer/PM critical
   ▼ Delivers UC7

5. THE CAPACITY OPTIMIZER (Alex, Linda, James)
   Pain: Chronic over-commitment
   Need: Realistic planning, workload analysis
   Priority: MEDIUM - prevents burnout
   ▼ Delivers UC8, UC10
```

---

## Gap Analysis: What's Missing

```
CURRENT MCP CAPABILITIES:
┌────────────────────────────────┐
│ ✅ get_projects                │  Read all projects
│ ✅ search_projects             │  Search by name/note
│ ✅ add_task                    │  Create task (limited)
│ ✅ add_note                    │  Append project notes
└────────────────────────────────┘

CRITICAL GAPS (BLOCKING):
┌────────────────────────────────┐
│ ❌ Task properties             │  No tags, dates, flags
│ ❌ Task operations             │  No get, update, complete
│ ❌ Project creation            │  Can't create projects
│ ❌ Search/filter tasks         │  Can't query tasks
└────────────────────────────────┘

NEEDED FOR MUST-HAVE USE CASES:
┌────────────────────────────────┐
│ 🔧 add_task enhancement        │  + tags, dates, flags
│ 🔧 get_tasks                   │  Query with filters
│ 🔧 complete_task               │  Mark done
│ 🔧 update_task                 │  Modify properties
│ 🔧 create_project              │  New projects
│ 🔧 Email integration           │  Receive/parse emails
└────────────────────────────────┘

HIGH-PRIORITY (SHOULD-HAVE):
┌────────────────────────────────┐
│ 📊 Task analytics              │  Completion history
│ 📊 Project health              │  Stalled detection
│ 📊 Capacity calculation        │  Workload analysis
│ 🔗 Calendar integration        │  Availability aware
│ 🔗 Meeting transcription       │  Action extraction
└────────────────────────────────┘

MEDIUM-PRIORITY (NICE-TO-HAVE):
┌────────────────────────────────┐
│ 🔗 GitHub/Jira sync            │  Dev tool integration
│ 🔗 Time tracking               │  Profitability
│ 🗣️ Voice interface             │  Hands-free
│ 📝 Template library            │  Reusable structures
└────────────────────────────────┘
```

---

## Week 1 Implementation Checklist

### Day 1-2: Enhanced add_task
```python
# Before (limited):
add_task(project_id="xyz", task_name="Call client", note="Discuss Q3")

# After (full GTD support):
add_task(
    project_id="xyz",
    task_name="Call client about Q3 results",
    note="Discuss revenue targets and next steps",
    tags=["@calls", "@priority-high"],
    due_date="2025-10-15",
    defer_date="2025-10-14",
    estimated_minutes=30,
    flagged=True
)
```

**Implementation Steps**:
- [ ] Extend omnifocus_client.py add_task method
- [ ] Update AppleScript to set tags, dates, flags
- [ ] Add parameter validation
- [ ] Test with 10 sample tasks
- [ ] Update MCP tool schema

---

### Day 3-4: get_tasks Tool
```python
# Get available next actions
tasks = get_tasks(status="available", limit=20, sort_by="priority")

# Get overdue tasks
tasks = get_tasks(overdue=True, include_flagged_first=True)

# Get project tasks
tasks = get_tasks(project_id="xyz")

# Get waiting-for items
tasks = get_tasks(tags=["@waiting"])
```

**Implementation Steps**:
- [ ] Create get_tasks AppleScript
- [ ] Add filtering logic (status, tags, dates)
- [ ] Implement sorting options
- [ ] Test query performance (1000+ tasks)
- [ ] Add MCP tool definition

---

### Day 5: Task Operations
```python
# Mark task complete
complete_task(task_id="abc123")

# Update task properties
update_task(task_id="abc123", due_date="2025-10-20", tags=["@priority-high"])

# Defer task
defer_task(task_id="abc123", defer_until="2025-10-18")
```

**Implementation Steps**:
- [ ] Create complete_task AppleScript
- [ ] Create update_task AppleScript
- [ ] Add error handling
- [ ] Test edge cases
- [ ] Add MCP tool definitions

---

## Week 2 Quick Wins

### Natural Language Task Creation
```
User: "I need to call the dentist tomorrow morning to schedule Emma's
       cleaning before school starts"

AI Creates:
- Task: "Call dentist - schedule Emma's cleaning"
  Project: Personal > Family > Kids > Health
  Tag: @calls
  Defer: Tomorrow 8:30 AM
  Due: Tomorrow (before end of day)
  Note: Schedule before school starts
```

**Implementation**:
- Mostly prompt engineering (use Claude's NLP capabilities)
- Calls existing add_task with inferred parameters
- No new server code needed!

---

### Email Forwarding Integration
```
Architecture:
Email → Forwarding Address → Server → AI Parser → OmniFocus Tasks

Flow:
1. User forwards email to omnifocus@server.com
2. Server receives via SMTP/API
3. AI extracts action items and context
4. AI suggests project placement
5. Creates tasks with email link in notes
```

**Implementation Steps**:
- [ ] Set up email receiver (SMTP or SendGrid)
- [ ] Parse email (headers, body, sender)
- [ ] Extract action items with AI
- [ ] Suggest project based on content
- [ ] Create tasks via add_task
- [ ] Add email link to task notes

---

## Week 3 Intelligence Features

### Project Health Analysis
```
AI Weekly Review Report:

⚠️ ATTENTION NEEDED (5 projects):
1. "Grant Application" - No activity in 3 weeks, deadline in 30 days
   Next action missing. Suggest: "Draft research methodology"?

2. "Paper Revision" - Stalled since reviewer comments received
   Suggest: "Address reviewer comment #1"?

3. "Course Prep" - 12 tasks overdue, starts in 2 weeks
   Suggest: Defer non-critical tasks?

✅ HEALTHY PROJECTS (22 projects):
Active with clear next actions

📊 INSIGHTS:
- Completed 47 tasks this week (up 12%)
- Top priority: Grant application (30 days to deadline)
```

**Implementation**:
- [ ] Query all projects with get_tasks
- [ ] Analyze last activity dates
- [ ] Detect missing next actions
- [ ] Calculate overdue counts
- [ ] Generate AI summary and suggestions

---

### Context Switching Assistant
```
User: "I have 2 hours before my next meeting. What should I work on?"

AI Analysis:

🎯 RECOMMENDED:
[Auth Feature] Implement OAuth integration (2h)
→ High impact, you're in flow, good momentum
→ Related to tomorrow's security review
→ Blocks other team members

📞 ALTERNATIVE (if deep work not possible):
5 communication tasks (1.5h total)
→ All @calls and @email, can handle interruptions
```

**Implementation**:
- [ ] Get available tasks with get_tasks
- [ ] Access calendar for time constraints
- [ ] Score tasks by priority/impact
- [ ] Group by context for batching
- [ ] Generate AI recommendation with reasoning

---

## Success Metrics: What to Measure

```
WEEK 1 BASELINE (Before AI):
┌────────────────────────────────────────────────────────────┐
│ Metric                    Current    Target     Reduction  │
├────────────────────────────────────────────────────────────┤
│ Email → Task              2-3 min    15 sec     90%        │
│ Weekly Review             2-3 hrs    45 min     75%        │
│ Context Switch Recovery   25-45 min  5-10 min   75%        │
│ Meeting Processing        10-15 min  1 min      90%        │
│ Project Setup             20-30 min  3 min      90%        │
├────────────────────────────────────────────────────────────┤
│ TOTAL TIME SAVED:         5-10 hours/week per user         │
└────────────────────────────────────────────────────────────┘

ENGAGEMENT METRICS:
- Daily AI interactions: Target >5 per user
- AI task creation ratio: Target 50% of tasks via AI
- Suggestion acceptance: Target >70%

QUALITY METRICS:
- Action item accuracy: Target >90%
- Response time: Target <2 seconds
- False positives: Target <10%
```

---

## Beta Testing Plan

### Week 3-4: Recruit Users
```
PERSONA TARGETS (10 total users):
- 3 Overwhelmed (Sarah, James, Linda types)
- 2 Context Switchers (Marcus, Priya types)
- 2 Template Users (Jasmine, Robert types)
- 2 Cross-Tool Jugglers (Developer/PM types)
- 1 Capacity Optimizer (Alex, entrepreneur type)
```

### Week 4: Baseline Measurement
- Shadow users for 1 week
- Measure current time on tasks
- Identify pain points
- Document workflows

### Week 5-8: Beta Test
- Deploy enhanced MCP server
- Weekly check-ins
- Measure time savings
- Collect feedback
- Iterate rapidly

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                          USER                                │
│                (Claude Desktop or CLI)                       │
└───────────────────────────┬─────────────────────────────────┘
                            │ MCP Protocol
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   MCP SERVER (server.py)                     │
│                                                              │
│  Tools:                                                      │
│  ├─ get_projects          ├─ add_task                       │
│  ├─ search_projects       ├─ add_note                       │
│  ├─ get_tasks             ├─ complete_task                  │
│  ├─ create_project        └─ update_task                    │
│                                                              │
└───────────────────────────┬─────────────────────────────────┘
                            │ Python API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│            OmniFocus Client (omnifocus_client.py)           │
│                                                              │
│  Methods:                                                    │
│  ├─ get_projects()       → AppleScript → OmniFocus         │
│  ├─ add_task(...)        → AppleScript → OmniFocus         │
│  ├─ get_tasks(...)       → AppleScript → OmniFocus         │
│  └─ complete_task(...)   → AppleScript → OmniFocus         │
│                                                              │
└───────────────────────────┬─────────────────────────────────┘
                            │ AppleScript Bridge
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                     OMNIFOCUS APP                            │
│                   (macOS Application)                        │
│                                                              │
│  Local Database:                                             │
│  ├─ Projects (folders, hierarchy)                           │
│  ├─ Tasks (tags, dates, flags, status)                      │
│  └─ Notes (rich text content)                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘

EXTERNAL INTEGRATIONS (Future):
Email ──┐
Meeting │
Transcr.├──→ Parser Service ──→ MCP Server
GitHub  │
Calendar┘
```

---

## Quick Decision Matrix

### When to Build a Feature

```
                    YES                           NO
                     │                            │
    Is it MUST-HAVE?│                            │
                     ├──────────────┐             │
                     │              │             │
    High Impact?    YES            NO            │
                     │              │             │
    Low Effort?     YES            │             │
                     │              │             │
    ──────→ BUILD NOW!   DEFER TO PHASE 2    BACKLOG
                                    │
                         Still build if user demands
```

### Examples:

**BUILD NOW** (High Impact + Low Effort):
- ✅ Enhanced add_task (foundational)
- ✅ Natural language parsing (prompt engineering)
- ✅ Email forwarding (solves #1 pain point)

**PHASE 2** (High Impact + Medium Effort):
- ⏭️ Calendar integration (valuable but complex)
- ⏭️ Meeting transcription (major feature)

**BACKLOG** (Nice-to-Have):
- 📋 Voice interface (interesting but not critical)
- 📋 Habit tracking (niche use case)

---

## Common Pitfalls to Avoid

### ❌ DON'T:
1. **Over-automate**: Don't do things without user knowledge
   - Bad: Automatically mark tasks complete
   - Good: Suggest completion, user confirms

2. **Arbitrary due dates**: Don't set deadlines that aren't real
   - Bad: Assign "due tomorrow" to everything
   - Good: Only set due dates for actual deadlines

3. **Tag proliferation**: Don't create unlimited tags
   - Bad: Create new tag for every adjective
   - Good: Suggest existing tags, limit new ones

4. **Complexity creep**: Don't add features for features' sake
   - Bad: 50 configuration options
   - Good: Smart defaults, minimal configuration

5. **Privacy violations**: Don't access data without permission
   - Bad: Read all emails automatically
   - Good: Only read forwarded/explicitly granted emails

### ✅ DO:
1. **Start simple**: Basic features first, enhance later
2. **Explain decisions**: Show why AI suggested something
3. **Easy undo**: Make everything reversible
4. **Respect GTD**: Follow David Allen's principles
5. **Local-first**: Process locally when possible

---

## The 80/20 Rule: Focus Here

**20% of features that deliver 80% of value**:

1. **Enhanced add_task** (2 days)
   - Enables all other workflows
   - Foundation for everything

2. **Email-to-task** (3 days)
   - Solves #1 pain point
   - High-frequency use

3. **Weekly review assistant** (3 days)
   - Saves 1-2 hours weekly
   - Core GTD practice

4. **Context switching helper** (2 days)
   - Saves 23-45 min per switch
   - Huge productivity gain

5. **Natural language creation** (2 days)
   - Eliminates friction
   - Makes AI feel magical

**Total: 12 days of work for 80% of value**

---

## Getting Started (Today)

### Step 1: Review Current Code
```bash
cd /Users/Morgan/Development/claude-code-test/omnifocus-mcp
cat omnifocus_client.py
cat server.py
```

### Step 2: Plan Week 1
- [ ] Read full USE_CASES.md for details
- [ ] Review ROADMAP.md for technical approach
- [ ] Check SCHEMA_REVIEW.md for OmniFocus data model
- [ ] Start with enhanced add_task implementation

### Step 3: Build Foundation
```python
# Priority 1: Enhanced add_task
def add_task(
    self,
    project_id: str,
    task_name: str,
    note: Optional[str] = None,
    tags: Optional[List[str]] = None,      # NEW
    due_date: Optional[str] = None,         # NEW
    defer_date: Optional[str] = None,       # NEW
    estimated_minutes: Optional[int] = None,# NEW
    flagged: Optional[bool] = False         # NEW
) -> bool:
    # AppleScript implementation...
```

### Step 4: Test & Iterate
- Create 10 test tasks with various properties
- Verify in OmniFocus app
- Measure performance
- Refine based on results

---

## Resources

### Documentation
- **USE_CASES.md**: Full personas and use case details
- **USE_CASES_SUMMARY.md**: Quick reference
- **USE_CASES_ANALYSIS.md**: Research insights and novel workflows
- **ROADMAP.md**: 4-phase technical roadmap
- **SCHEMA_REVIEW.md**: OmniFocus data model
- **IMPLEMENTATION_EXAMPLES.md**: Code patterns

### External Resources
- [OmniFocus AppleScript Guide](https://support.omnigroup.com/omnifocus-applescript/)
- [GTD Methodology](https://gettingthingsdone.com/)
- [MCP Protocol Docs](https://modelcontextprotocol.io/)

### Research Sources
- GTD best practices and OmniFocus forums
- AI task manager competitive analysis (Motion, Reclaim, etc.)
- Productivity research on context switching
- User automation patterns via AppleScript

---

## Success Formula

```
TIME SAVINGS = Σ(frequency × time_per_task × reduction_rate)

Example for Email-to-Task:
= 30 emails/day × 2.5 min/email × 90% reduction
= 67.5 minutes saved daily
= 5.6 hours saved weekly

Multiply across all use cases:
Email-to-Task:      5.6 hours/week
Weekly Review:      1.5 hours/week
Context Switching:  2.0 hours/week
Meeting Processing: 0.7 hours/week
Project Setup:      0.5 hours/week
─────────────────────────────────────
TOTAL:             10.3 hours/week

Return on Investment:
User saves 10 hours/week × 50 weeks/year = 500 hours/year
At $50/hour = $25,000 in value per year per user
```

**That's the opportunity. Let's build it.**

---

Last Updated: October 7, 2025
