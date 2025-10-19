# Architectural Mistakes Log

**Purpose:** Track high-level architectural and workflow mistakes to improve development process.

**Last Updated:** 2025-10-19

**Statistics:**
- Total Mistakes: 0
- By Category: None yet
- By Severity: None yet

**Recent Patterns:** No patterns detected yet (need 3+ mistakes in same category)

---

## Active Mistakes (Not Yet Addressed in CLAUDE.md)

*No active mistakes logged yet*

---

## Resolved Mistakes (Addressed in CLAUDE.md)

*No resolved mistakes yet*

---

## Archived Mistakes (Historical Record)

*No archived mistakes yet*

---

## Mistake Entries

*Mistakes will be logged below using this template:*

```
## [MISTAKE-XXX] Brief Title (Date: YYYY-MM-DD)

**Category:** [missing-tests | missing-exposure | violated-tdd | violated-architecture | missing-docs | complexity-spike | other]

**Severity:** [critical | high | medium | low]
- **Critical:** Production issue, user-facing bug, data loss risk
- **High:** Missing major functionality, violates core principles
- **Medium:** Incomplete implementation, future maintenance burden
- **Low:** Minor oversight, easily fixed

**What Happened:**
[Detailed description of the mistake]

**Context:**
- **File(s):** [Affected files]
- **Function(s):** [Affected functions]
- **Commit:** [Git commit hash if applicable]

**Impact:**
[What broke? What was missing? What was the consequence?]

**Root Cause:**
[Why did this happen? What process step was missed?]

**Fix:**
[What was done to fix it?]

**Prevention:**
[What could prevent this in the future? CLAUDE.md update? Checklist addition? New tooling?]

**Related Mistakes:**
[Links to similar mistakes, if any]
```

---

## Quick Reference

**Log a new mistake:**
```bash
./scripts/log_mistake.sh
```

**Analyze patterns:**
```bash
./scripts/analyze_mistakes.py  # When created
```

**Categories:**
- `missing-tests` - Failed to write unit, integration, or e2e tests
- `missing-exposure` - Implemented in client but didn't expose in server
- `violated-tdd` - Wrote implementation before tests
- `violated-architecture` - Didn't follow architecture principles/decision tree
- `missing-docs` - Failed to update CHANGELOG, API_REFERENCE, etc.
- `complexity-spike` - Function rated D or F without documentation
- `other` - Other architectural/workflow mistakes
