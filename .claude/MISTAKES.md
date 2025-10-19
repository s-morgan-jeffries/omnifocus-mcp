# Architectural Mistakes Log

**Purpose:** Track high-level architectural and workflow mistakes to improve development process.

**Last Updated:** 2025-10-19

**Statistics:**
- Total Mistakes: 3
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


## [MISTAKE-002] TESTING.md test counts repeatedly get out of sync with actual tests (Date: 2025-10-19)

**Category:** missing-docs

**Severity:** medium

**What Happened:**
TESTING.md contains hardcoded test counts and breakdowns that repeatedly become stale as tests are added/removed/refactored. During v0.6.0 API redesign, the documentation showed 393 tests in some places, 333 in others, and the actual count was 333. The coverage table in TESTING.md still referenced v0.5.0 function names (complete_task, add_task, etc.) even after v0.6.0 redesign removed them. This happened multiple times throughout the project.

**Context:**
- **File(s):** docs/TESTING.md (lines 21, 166-187, 336-365), README.md (lines 166-187), ROADMAP.md (lines 241-252), .claude/CLAUDE.md (line 143)
- **Function(s):** N/A (documentation)
- **Commits:** Multiple throughout v0.5.0 and v0.6.0 development

**Impact:**
- Documentation shows incorrect test counts, confusing contributors
- Coverage tables reference deprecated/removed functions
- Test count is duplicated in 4+ files, requiring manual sync across all
- Human readers get conflicting information
- AI readers may reference wrong function names from outdated coverage tables

**Root Cause:**
1. Test counts are manually hardcoded in documentation instead of generated
2. No automated check that TESTING.md matches actual pytest output
3. Coverage breakdown by function is manually maintained
4. Same information duplicated across 4+ files (TESTING.md, README.md, ROADMAP.md, CLAUDE.md)
5. No single source of truth for test statistics

**Fix:**
1. Consolidated test counts to single source (TESTING.md) with all other docs referencing it
2. Removed stale v0.5.0 coverage table from TESTING.md
3. Updated all docs to say "See TESTING.md for detailed breakdown" instead of duplicating numbers
4. Replaced obsolete coverage table with summary: "All 16 core v0.6.0 MCP tools have comprehensive coverage"

**Prevention:**
**Short term (manual maintenance):**
- Add to "Before Every Commit" checklist: "If tests added/removed, update test count in TESTING.md only"
- TESTING.md is single source of truth; all other docs reference it
- Don't duplicate test breakdowns; link to TESTING.md instead

**Long term (automation):**
- Create script `scripts/generate_test_stats.sh` that runs pytest and extracts actual counts
- Script outputs markdown snippet that can be pasted into TESTING.md
- Pre-commit hook could warn if TESTING.md test count differs from actual pytest output
- Even better: Generate TESTING.md statistics section automatically from pytest --collect-only

**Example automation:**
```bash
# scripts/generate_test_stats.sh
pytest --collect-only -q | tail -1  # "333 tests collected"
pytest tests/ --cov --cov-report=term | grep "TOTAL"  # Coverage percentage
```

**Related Mistakes:**
Similar to MISTAKE-003 (if version numbers are tracked there) - both are "duplicated information that gets out of sync"

---


## [MISTAKE-003] Version numbers duplicated across multiple files, get out of sync (Date: 2025-10-19)

**Category:** missing-docs

**Severity:** high

**What Happened:**
Version number is documented in multiple places (pyproject.toml, CHANGELOG.md, ROADMAP.md, README.md, CLAUDE.md, archive/README.md) and repeatedly gets out of sync. During v0.6.0 work, pyproject.toml showed 0.5.0 while all documentation claimed 0.6.0 was complete. Archive README still said "current version: v0.5.0" weeks after v0.6.0 completion. This has happened multiple times across different releases.

**Context:**
- **File(s):**
  - pyproject.toml (line 7 - authoritative source)
  - CHANGELOG.md (version headers)
  - docs/ROADMAP.md (multiple version references)
  - README.md (feature descriptions with versions)
  - .claude/CLAUDE.md (line 141 - "Current Version")
  - docs/archive/README.md (line 7, 73 - archive metadata)
- **Function(s):** N/A (documentation/metadata)
- **Commits:** Multiple throughout v0.5.0 and v0.6.0 development

**Impact:**
- Code says one version (pyproject.toml), docs say another
- PyPI package would have wrong version if published
- Users/contributors confused about actual project version
- Archive documentation references "current version" that's outdated
- No single source of truth for version number

**Root Cause:**
1. Version number manually duplicated in 6+ locations
2. No automated synchronization between pyproject.toml and documentation
3. No checklist reminder to update version across all files
4. Version bumping is manual, easy to miss files
5. Archive documentation says "current version" instead of "version when archived"

**Fix:**
1. Updated pyproject.toml from 0.5.0 to 0.6.0 (authoritative source)
2. Verified all documentation references v0.6.0 correctly
3. Updated archive/README.md to clarify "version when archive created" vs "current project version"
4. Consolidated version references where possible

**Prevention:**
**Short term (manual process):**
- Add to "Making a Release" workflow in CONTRIBUTING.md:
  1. Update pyproject.toml version (authoritative)
  2. Add CHANGELOG.md entry with new version header
  3. Update CLAUDE.md "Current Version" line
  4. Update README.md if version appears in feature descriptions
  5. Commit with message: "chore: bump version to vX.Y.Z"

**Long term (automation):**
- Use `bump2version` or similar tool to automate version bumping
- Script that reads version from pyproject.toml and validates docs match:
  ```bash
  # scripts/check_version_sync.sh
  VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
  grep -l "Current Version.*$VERSION" .claude/CLAUDE.md || echo "CLAUDE.md out of sync"
  grep -l "## \[$VERSION\]" CHANGELOG.md || echo "CHANGELOG.md missing version"
  ```
- Pre-commit hook that warns if CHANGELOG.md latest version ≠ pyproject.toml
- Consider using dynamic version from pyproject.toml in docs (e.g., include directive)

**Related Mistakes:**
Similar to MISTAKE-002 (test counts out of sync) - both are "duplicated information that gets out of sync"
Pattern: **Documentation duplication without single source of truth**

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
