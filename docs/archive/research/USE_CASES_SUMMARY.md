# OmniFocus MCP Server: Use Cases Quick Reference

## 10 User Personas

1. **Sarah - GTD Purist** (Executive coach, 50-80 projects, strict GTD methodology)
2. **Marcus - Developer** (Senior engineer, multi-codebase work, 23-45 min context switch recovery)
3. **Jasmine - Creative Director** (Agency lead, 30-40 client projects, template-heavy)
4. **Dr. Chen - Academic Researcher** (Professor, long-term research projects, literature management)
5. **Alex - Entrepreneur** (Startup founder, frequent re-prioritization, over-commitment issues)
6. **Priya - Product Manager** (Cross-team coordination, heavy waiting-for dependencies)
7. **Robert - Consultant** (Multiple clients, billable time tracking, context switching)
8. **Linda - Parent Professional** (Work/life balance, mental load management, quick capture)
9. **James - Non-Profit Director** (Grant deadlines, volunteer coordination, stakeholder management)
10. **Taylor - Freelancer** (Multiple clients, pitch tracking, irregular income)

---

## 15 Use Case Scenarios (Prioritized)

### MUST-HAVE (Phase 1)

#### UC1: Email-to-Task Processing
- **Impact:** Universal need, addresses #1 pain point
- **Gap:** Need tags, dates, email integration, project suggestion AI
- **Example:** Client email → auto-create tasks with proper project placement

#### UC2: Meeting Notes to Action Items
- **Impact:** Major task source, collaboration critical
- **Gap:** Need transcript parsing, bulk creation, waiting-for detection
- **Example:** Meeting transcript → tasks for user + "waiting-for" others

#### UC4: Intelligent Weekly Review Assistant
- **Impact:** Core GTD practice, currently 2-3 hours
- **Gap:** Need task history, stalled project detection, statistics
- **Example:** AI identifies 5 projects needing attention vs. manual review of 50+

#### UC5: Context Switching Minimization
- **Impact:** 23-45 min productivity loss per switch
- **Gap:** Need task priorities, calendar integration, effort estimates
- **Example:** "What should I work on next?" → intelligent suggestions

#### UC6: Natural Language Project & Task Creation
- **Impact:** Dramatically reduces friction
- **Gap:** Need project creation, NLP parsing, template recognition
- **Example:** "Plan birthday party next month" → full project with tasks

---

### SHOULD-HAVE (Phase 2)

#### UC3: Project Template Smart Instantiation
- **Impact:** High for template-heavy workflows
- **Gap:** Need template system, variable substitution, relative dates
- **Example:** "New client onboarding for Acme Corp" → 20 tasks with proper dates

#### UC7: Cross-Tool Integration & Sync
- **Impact:** Critical for developers and PMs
- **Gap:** Need webhook support, bi-directional sync, duplicate prevention
- **Example:** GitHub issue #347 → OmniFocus task with link

#### UC8: Intelligent Task Prioritization & Capacity Planning
- **Impact:** Prevents over-commitment
- **Gap:** Need calendar integration, workload analysis, defer suggestions
- **Example:** "47 hours of work, 32 hours available - here's what to defer"

#### UC10: Waiting-For Tracking & Follow-up
- **Impact:** Essential for delegation
- **Gap:** Need email monitoring, follow-up timing, response detection
- **Example:** Auto-track "waiting for designs from Sarah", remind after 3 days

#### UC13: Voice-First Task Management
- **Impact:** Critical for mobile/busy users
- **Gap:** Need voice interface, context awareness, background processing
- **Example:** While driving: "Call dentist tomorrow morning" → task created

#### UC14: Financial & Time Investment Tracking
- **Impact:** Essential for consultants/freelancers
- **Gap:** Need time tracking integration, profitability analysis, reporting
- **Example:** "TechStart Inc has effective rate of $86/hr - below target"

---

### NICE-TO-HAVE (Phase 3)

#### UC9: Research & Reading List Management
- **Impact:** High for academics/researchers
- **Gap:** Need content analysis, reading app integration, citation management
- **Example:** Research paper → extract methodology into tasks

#### UC11: Habit & Recurring Task Intelligence
- **Impact:** Improves sustainability
- **Gap:** Need completion history, pattern analysis, flexible recurrence
- **Example:** "Exercise set to daily, actually 3x/week - adjust to reduce guilt"

#### UC12: Project Dependency & Critical Path Analysis
- **Impact:** High for complex projects
- **Gap:** Need dependency modeling, timeline calculation, risk analysis
- **Example:** "Design delayed 2 days → entire launch at risk"

#### UC15: Learning & Skill Development Tracker
- **Impact:** High for continuous learners
- **Gap:** Need milestone tracking, progress analysis, application detection
- **Example:** "Learn Rust" → 12-week plan with practice exercises and projects

---

## Critical Capability Gaps

### 1. Task Properties (BLOCKING)
**Missing:** tags, due dates, defer dates, priority, effort, flags, completion status
**Impact:** Cannot create properly structured GTD tasks

### 2. Project Management (BLOCKING)
**Missing:** create projects, duplicate templates, folder hierarchy
**Impact:** Cannot automate project workflows

### 3. Task Operations (HIGH PRIORITY)
**Missing:** get tasks, mark complete, update properties, move tasks
**Impact:** Cannot provide intelligent recommendations

### 4. Search & Query (HIGH PRIORITY)
**Missing:** filter by criteria, get overdue/flagged/waiting tasks, perspectives
**Impact:** Cannot surface relevant tasks

### 5. External Integrations (MEDIUM PRIORITY)
**Missing:** Email, calendar, notes, dev tools, time tracking, communication
**Impact:** Cannot automate cross-tool workflows

### 6. Intelligence & Analytics (MEDIUM PRIORITY)
**Missing:** Statistics, health analysis, workload calculation, predictions
**Impact:** Cannot provide proactive assistance

---

## Top 5 Quick Wins

### 1. Enhanced add_task with Properties
**Effort:** Low | **Impact:** Very High
```python
add_task(
    project_id="xyz",
    task_name="Call client",
    note="Discuss Q3 results",
    tags=["@calls", "@priority"],
    due_date="2025-10-10",
    defer_date="2025-10-09",
    flagged=True
)
```
**Unlocks:** UC1 (Email-to-Task), UC2 (Meeting Notes), UC6 (Natural Language)

---

### 2. get_tasks Tool
**Effort:** Low | **Impact:** Very High
```python
# Get all available next actions
tasks = get_tasks(status="available", limit=20)

# Get tasks in a project
tasks = get_tasks(project_id="xyz")

# Get overdue tasks
tasks = get_tasks(overdue=True)
```
**Unlocks:** UC4 (Weekly Review), UC5 (Context Switching)

---

### 3. create_project Tool
**Effort:** Medium | **Impact:** High
```python
create_project(
    name="Acme Corp - Website Redesign",
    folder_path="Clients > Active",
    note="Timeline: 8 weeks, Team: Sarah, Mike",
    status="active"
)
```
**Unlocks:** UC3 (Templates), UC6 (Natural Language)

---

### 4. Email Forwarding Integration
**Effort:** Medium | **Impact:** Very High
```
Forward to: omnifocus@your-mcp-server.com
Subject: Task: Call dentist tomorrow @calls
Body: Schedule Emma's cleaning
```
**Unlocks:** UC1 (Email-to-Task), UC10 (Waiting-For)

---

### 5. Basic Task Completion & History
**Effort:** Medium | **Impact:** High
```python
# Mark task complete
complete_task(task_id="abc123")

# Get completion history
history = get_completion_history(
    project_id="xyz",
    date_range="last_30_days"
)
```
**Unlocks:** UC4 (Weekly Review), UC8 (Capacity Planning), UC11 (Habits)

---

## Recommended Development Phases

### Phase 1: Foundation (Months 1-2)
**Goal:** Enable basic AI task management
- Enhanced task properties (tags, dates, flags)
- get_tasks and update_task tools
- create_project tool
- Email forwarding MVP

**Delivers:** UC1, UC6 (partial UC2, UC4, UC5)

---

### Phase 2: Intelligence (Months 3-4)
**Goal:** AI insights and automation
- Task analytics and statistics
- Meeting transcription integration
- Calendar integration
- Stalled project detection

**Delivers:** UC2, UC4, UC5 (fully)

---

### Phase 3: Advanced (Months 5-6)
**Goal:** Multi-tool integration
- Template system
- GitHub/Jira integration
- Waiting-for tracking
- Time tracking basics

**Delivers:** UC3, UC7, UC10, UC14 (partial)

---

### Phase 4: Optimization (Months 7+)
**Goal:** Personalization
- Pattern learning
- Advanced analytics
- Voice interface
- Specialized features

**Delivers:** UC8, UC9, UC11, UC12, UC13, UC14, UC15

---

## Success Metrics

### Time Savings
- Weekly review: 2-3 hours → 45-60 minutes (50% reduction)
- Email to task: 2-3 min → 15 seconds (90% reduction)
- Context switching: 23-45 min recovery → 5-10 min (75% reduction)

### Productivity
- Task completion rate: +15%
- Overdue tasks: -40%
- Context switches per day: -30%

### AI Effectiveness
- Action item extraction accuracy: >90%
- Suggestion acceptance rate: >70%
- False positive rate: <10%

---

## Key Insights

### What Makes This Unique
1. **Bridge unstructured → structured**: Email/meetings → organized GTD tasks
2. **Reduce cognitive load**: AI handles analysis, user handles decisions
3. **Context preservation**: Minimize 23-45 min context switch penalty
4. **Learning system**: Improves with use, adapts to patterns
5. **Privacy-focused**: User controls AI access to local data

### Competitive Advantages
- Preserves OmniFocus investment (not replacement)
- GTD methodology deeply integrated
- Apple ecosystem integration
- Local-first with AI enhancement

### Critical Success Factors
1. Balance automation with user control
2. High accuracy (>90%) on action item extraction
3. Fast response times (<2 seconds for suggestions)
4. Respect GTD principles (don't fight the methodology)
5. Progressive disclosure (simple by default, powerful when needed)

---

## Next Steps

### Immediate Actions
1. Implement enhanced add_task with full properties
2. Build get_tasks tool with filtering
3. Create email forwarding endpoint
4. Test with 5-10 beta users across personas

### User Research Needed
1. Time-to-task baseline measurement (current vs. AI-assisted)
2. Weekly review pain point survey
3. Integration priority ranking
4. Natural language pattern analysis
5. Trust & control preference study

### Technical Decisions
1. Email integration: Forwarding vs. OAuth vs. IMAP?
2. Calendar sync: CalDAV vs. platform APIs?
3. Meeting transcription: Whisper vs. external service?
4. Storage: Where to keep AI-generated metadata?
5. Privacy: On-device AI vs. cloud with encryption?
