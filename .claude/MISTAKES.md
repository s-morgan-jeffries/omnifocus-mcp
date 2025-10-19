# Architectural Mistakes Log

**Purpose:** Track high-level architectural and workflow mistakes to improve development process.

**Last Updated:** 2025-10-19

**Statistics:**
- Total Mistakes: 1
- By Category: missing-docs (1)
- By Severity: high (1)

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


## [MISTAKE-001] Missing MIGRATION_v0.6.md despite CHANGELOG reference (Date: 2025-10-19)

**Category:** missing-docs

**Severity:** high

**What Happened:**
During v0.6.0 API redesign implementation, updated CHANGELOG.md to reference `docs/MIGRATION_v0.6.md` for detailed migration guide, marked it as "(TODO)", but never created the file before marking the redesign as complete. This created a broken link in documentation and violated the established pattern (MIGRATION_v0.5.md exists for the v0.5.0 release).

**Context:**
- **File(s):** CHANGELOG.md (line 107), docs/MIGRATION_v0.6.md (missing)
- **Function(s):** N/A (documentation)
- **Commit:** 81aceb7 (added CHANGELOG v0.6.0 entry), be794b4 (marked redesign complete)

**Impact:**
- Created broken documentation link (CHANGELOG references non-existent file)
- Inconsistent with established pattern (v0.5.0 had migration guide)
- External users (if any exist) would have no migration path from v0.5.0 → v0.6.0
- Violated promise in CHANGELOG: "See docs/MIGRATION_v0.6.md"

**Root Cause:**
1. Focused on code implementation and basic CHANGELOG updates
2. Assumed migration guide could be created "later" as indicated by "(TODO)"
3. Marked redesign as "complete" without checking if all referenced documentation existed
4. No checklist item for "breaking changes require migration guide"
5. Didn't follow the pattern established by MIGRATION_v0.5.md

**Fix:**
1. Created docs/MIGRATION_v0.6.md following MIGRATION_v0.5.md template structure
2. Extracted migration examples from CHANGELOG.md (lines 24-51)
3. Documented all 26 removed functions with before/after examples
4. Removed "(TODO)" marker from CHANGELOG.md line 107

**Prevention:**
Add to "Before Every Commit" checklist or "Common Development Tasks":
- **Breaking change releases:** If CHANGELOG documents removed/changed functions, verify migration guide exists
- **Cross-references:** Before committing documentation that references other files, verify those files exist
- **Pattern consistency:** If pattern exists (like MIGRATION_vX.Y.md), follow it for all similar releases

Alternative: Add to "Making a Breaking Change Release" workflow in docs/CONTRIBUTING.md

**Related Mistakes:**
None yet (first logged mistake in tracking system)

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
