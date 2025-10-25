# Mistake Tracking Infrastructure

> **⚠️ HISTORICAL ARCHIVE**
>
> This entire directory (.claude/mistakes/) is a **historical archive** from the early development phase (pre-v0.6.2).
>
> **Current practice:** Mistake tracking has migrated to **GitHub Issues** with the `ai-process` label.
> - File issues immediately when mistakes occur
> - Use issue templates for consistency
> - Track recurrence through duplicate issue detection
> - Prevention measures documented in issue bodies
>
> This archive is preserved for reference but is **no longer actively maintained**.

---

## Original Documentation (Archive)

**Purpose:** Track, prevent, and learn from architectural and workflow mistakes in the OmniFocus MCP Server project.

**Status:** B+ grade, 75-80% functional, 85-90% closed feedback loop (as of 2025-10-19)
**Last Analysis:** Fourth (2025-10-19)
**Migration:** System migrated to GitHub Issues in v0.6.2

---

## What This Is

This directory contains the **recursive self-improvement system** for the OmniFocus MCP Server project. It's project infrastructure—like the `tests/` directory—that ensures development quality through systematic mistake tracking and prevention.

**Not a separate project:** This is development tooling, versioned alongside the main codebase.

**Why it exists:**
- Capture mistakes when they happen (while context is fresh)
- Prevent recurrence through automation
- Measure effectiveness with data
- Improve development process over time

---

## Directory Structure

```
.claude/mistakes/
├── README.md              # This file - overview and getting started
├── MISTAKES.md            # Mistake log (6 logged, 4 in monitoring)
├── METRICS.md             # Auto-generated metrics
├── ROADMAP.md             # Infrastructure roadmap and status
├── ANALYSIS_GAPS.md       # Open issues from analyses (with deadlines)
└── analyses/
    ├── MISTAKE_TRACKING_SECOND_ANALYSIS.md   # Second analysis (2025-10-19)
    ├── THIRD_ANALYSIS_HONEST_ASSESSMENT.md    # Third analysis + response
    └── FOURTH_ANALYSIS_VERIFICATION.md        # Fourth analysis (verification)
```

---

## Current State

### Logged Mistakes (6 total)

| ID | Category | Severity | Status | Prevention |
|----|----------|----------|--------|------------|
| MISTAKE-001 | missing-docs | high | resolved | Migration guide checklist |
| MISTAKE-002 | missing-docs | medium | monitoring | Test count automation |
| MISTAKE-003 | missing-docs | high | monitoring | Version sync script |
| MISTAKE-004 | other | high | resolved | Metrics auto-update |
| MISTAKE-007 | missing-tests | critical | monitoring | Prevention validation tests |
| MISTAKE-008 | missing-docs | critical | monitoring | Recurrence tracking |

### Infrastructure Components

| Component | Status | Notes |
|-----------|--------|-------|
| Template & logging | ✅ Complete | MISTAKES.md template, log_mistake.sh |
| Git hooks (pre-commit) | ⚠️ Partial | Detects 4/6 categories, warnings only |
| Git hooks (commit-msg) | ✅ Complete | Validates references, updates metrics |
| Prevention scripts | ✅ Complete | 6 scripts, all working |
| Prevention tests | ✅ Complete | 4/4 passing (positive & negative cases) |
| Recurrence detection | ✅ Complete | Dynamic, checks all monitoring mistakes |
| Metrics auto-update | ⚠️ Partial | Category/severity work, monthly broken |
| CI/CD enforcement | ⚠️ Untested | Configuration correct, not validated |
| Verification deadlines | ✅ Complete | All set to 2025-11-18 |

**Overall:** 75-80% functional, 85-90% closed loop

---

## Quick Start

### Logging a New Mistake

```bash
./scripts/log_mistake.sh
# Follow interactive prompts
# Updates MISTAKES.md, METRICS.md automatically
```

### Checking System Health

```bash
# Check if any prevention measures have failed
./scripts/check_recurrence.sh

# Check if verification deadlines are approaching
./scripts/check_monitoring_deadlines.sh

# Validate all prevention measures work
./scripts/test_prevention_measures.sh

# View current metrics
cat .claude/mistakes/METRICS.md
```

### Before Every Commit

Pre-commit hook runs automatically:
- Detects missing tests (pytest --collect-only)
- Detects missing docs (grep for CHANGELOG, API_REFERENCE updates)
- Detects complexity spikes (radon cc)
- Warns but doesn't block (CI/CD enforces)

**Manual bypass:** `git commit --no-verify` (use sparingly)
**Server enforcement:** CI/CD workflow blocks merge if checks fail

---

## Key Files

### MISTAKES.md

**The core log.** Contains:
- Template for logging new mistakes
- All logged mistakes with full context
- Prevention status and effectiveness scores
- Verification deadlines (30-day observation periods)

**Update via:** `./scripts/log_mistake.sh` (interactive)
**Manual edit:** When updating recurrence counts or effectiveness

### METRICS.md

**Auto-generated metrics** (do not edit manually):
- Mistake counts by category, severity, status
- Monthly breakdown (currently broken, see ANALYSIS_GAPS.md)
- Trend analysis (when monthly data fixed)

**Updated by:** `scripts/update_metrics.sh` (called by commit-msg hook)
**Regenerate:** `./scripts/update_metrics.sh`

### ANALYSIS_GAPS.md

**Open issues from analyses** with:
- Priority (1-3)
- Effort estimate
- Deadline
- What it blocks

**Purpose:** Ensure analysis findings don't get forgotten
**Check:** `./scripts/check_monitoring_deadlines.sh` (will be enhanced)

### ROADMAP.md

**Infrastructure development plan:**
- Completed phases
- Current priorities
- Future enhancements
- Verification milestones

**Separate from main ROADMAP.md** to avoid cluttering feature roadmap

---

## The Feedback Loop

```
Detection → Logging → Analysis → Fix → Prevention → Validation → Measurement → Detection
    ↑                                                                              ↓
    └──────────────────────────── Recurrence Tracking ─────────────────────────────┘
```

**85-90% complete** (as of fourth analysis)

### What's Working

1. **Detection** (67% coverage) - Pre-commit hook catches 4/6 categories
2. **Logging** (100%) - Template works, scripts automate
3. **Analysis** (100%) - Pattern detection (3+ threshold)
4. **Fix** (100%) - All 6 mistakes have documented fixes
5. **Prevention** (100%) - Scripts prevent recurrence
6. **Validation** (100%) - Tests prove prevention works
7. **Measurement** (70%) - Category/severity work, monthly broken
8. **Recurrence** (85%) - Dynamic detection, CI/CD untested

### What Needs Work

See [ANALYSIS_GAPS.md](ANALYSIS_GAPS.md) for current open issues.

---

## Analysis History

We've run **four independent analyses** to find gaps and verify fixes:

1. **First Analysis** (implicit) - Initial gap analysis, prioritized 15 improvements
2. **Second Analysis** (2025-10-19) - Found 14 gaps after Priority 1-2 implementation
3. **Third Analysis** (2025-10-19) - **Brutal honesty check**
   - Found: Metrics broken, claims inflated (95%→75%), premature effectiveness
   - Result: Fixed metrics, added CI/CD, set verification deadlines
4. **Fourth Analysis** (2025-10-19) - **Verification of fixes**
   - Result: All 5 fixes verified working
   - Finding: Percentages still slightly inflated (85%→80%, optimism bias)
   - New gaps: Monthly metrics broken, CI/CD untested

**Key learning:** Third analysis worked - problems were fixed, not explained away. System improved 75%→80% actual functionality.

**Next analysis:** Triggered by verification deadline (2025-11-18) or pattern threshold.

---

## Philosophy

### This IS Recursive Self-Improvement

**Evidence:**
1. ✅ Analyses find real problems (not theoretical)
2. ✅ Problems fixed immediately (not explained away)
3. ✅ System improves measurably (75%→80% functionality)
4. ✅ Honesty improves (95% claim→85% claim→80% actual)
5. ✅ Learns from feedback (each analysis addresses previous gaps)

**Residual issue:** Optimism bias (80% actual becomes 85% claimed) - human tendency to round up

### This is NOT a Separate Project

**Treat like test infrastructure:**
- Essential for quality ✅
- Versioned with project ✅
- Not on feature roadmap ✅
- Has own documentation ✅

**Purpose:** Improve **OmniFocus MCP Server** development, not build a standalone mistake tracking product.

---

## Verification Timeline

**Current observation period:** 2025-10-19 → 2025-11-18 (30 days)

**On 2025-11-18, we will:**
1. Check if any prevented mistakes recurred
2. Assess which prevention measures are truly effective
3. Update effectiveness scores from "pending" to "effective ✅" or "ineffective ❌"
4. Identify patterns (we have 4 missing-docs, threshold met)
5. Update CLAUDE.md based on learnings

**Don't claim effectiveness before then** - wait for data, not assumptions.

---

## Contributing

### When You Make a Mistake

1. Don't hide it - **log it while context is fresh**
2. Run `./scripts/log_mistake.sh`
3. Document what happened, why, how you fixed it
4. Implement prevention (checklist, script, or test)
5. Validate prevention works
6. Set verification deadline (30 days)

### When You Find a Pattern

If you notice 3+ mistakes in the same category:
1. Run root cause analysis
2. Update CLAUDE.md with stronger prevention
3. Consider triggering agent analysis for deep dive

### When Verification Deadline Arrives

1. Check `./scripts/check_recurrence.sh`
2. If no recurrences: Mark "effective ✅"
3. If recurred: Analyze why, improve prevention
4. Update CLAUDE.md with learnings

---

## Questions?

**For details:**
- Mistake categories and severities → [MISTAKES.md](MISTAKES.md#mistake-entries) template section
- Infrastructure roadmap → [ROADMAP.md](ROADMAP.md)
- Analysis history → [analyses/](analyses/) directory
- Open issues → [ANALYSIS_GAPS.md](ANALYSIS_GAPS.md)

**Main project documentation:**
- Development guidelines → [../.claude/CLAUDE.md](../.claude/CLAUDE.md)
- Architecture principles → [../../docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md)
- Project roadmap → [../../docs/ROADMAP.md](../../docs/ROADMAP.md)
