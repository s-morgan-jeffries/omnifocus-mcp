# Automation Candidates

This file tracks issues found during interactive quality checks that seem likely to recur and might warrant automation.

**Philosophy:** Track selectively using heuristics, not exhaustively. Focus on patterns, not one-offs.

## When to Track an Issue

Track issues that meet ANY of these heuristics:

1. **Affects generated/auto-updated content** - Likely to recur when content regenerates
2. **Common mistake pattern** - Similar to known recurring mistakes in software projects
3. **Systemic problem** - Affects multiple files or areas
4. **High-change area** - Issue in code/docs that changes frequently
5. **Already recurred** - Second occurrence of any issue (even if not tracked initially)

**Don't track:**
- Typos or one-time mistakes
- Issues fixed immediately and unlikely to recur
- Highly specific edge cases

## Automation Criteria

An issue should be automated when it meets ALL 5 criteria:

1. **Clear Pass/Fail** - Objective, deterministic criteria that can be scripted
2. **Consistent Failures** - Failed in 3+ consecutive releases OR caused 2+ post-release issues
3. **High Impact** - Causes user-facing bugs, contributor friction, hotfixes, or security issues
4. **Low False Positives** - Won't block releases for acceptable cases
5. **Maintainable** - Can be implemented as script <30s, clear exit codes, actionable errors

**See:** `docs/reference/RELEASE_PROCESS.md` for complete automation criteria and examples

---

## Under Observation

*Issues being tracked for potential automation. Add new entries when running interactive quality checks for minor/major releases.*

<!-- Example template - remove after first real use:

### [Issue Title]

- **Check:** [/doc-quality | /code-quality | /test-coverage | /directory-check]
- **First seen:** vX.Y.Z
- **Occurrences:** X releases ([list versions])
- **Severity:** [Critical | Recommended | Minor]
- **Description:** [What was found]
- **Why tracking:** [Which heuristic applies - generated content, common pattern, systemic, etc.]
- **Criteria met:** X/5
  - [ ] Clear pass/fail
  - [ ] Consistent failures (3+ or 2+ post-release issues)
  - [ ] High impact
  - [ ] Low false positives
  - [ ] Maintainable
- **Proposed automation:**
  ```bash
  # Script that would check this
  ```
- **Next action:** [What to do if this recurs]

-->

---

## Recently Automated

*Issues that were automated - moved here for reference.*

### Test Coverage Below 85%

- **Automated in:** v0.6.3
- **Script:** `scripts/check_test_coverage.sh`
- **Why:** Consistent failures causing release delays, clear threshold
- **Criteria met:** 5/5 (all)

### Code Complexity Violations

- **Automated in:** v0.6.2
- **Script:** `scripts/check_complexity.sh`
- **Why:** Recurring D-F rated functions, clear CC threshold
- **Criteria met:** 5/5 (all)

### ROADMAP.md Sync Issues

- **Automated in:** v0.6.6
- **Script:** `scripts/check_roadmap_sync.sh`
- **Why:** Recurring forgotten updates after closing issues
- **Criteria met:** 5/5 (all)

---

## Review Process

**Before each minor/major release:**

1. Run all 4 interactive quality checks (`/doc-quality`, `/code-quality`, `/test-coverage`, `/directory-check`)
2. Review results for issues matching tracking heuristics
3. For tracked issues:
   - Update occurrence count
   - Check if criteria met has changed
   - If meets all 5 criteria → Create issue to automate
4. For new issues meeting heuristics:
   - Add to "Under Observation" section
   - Document why tracking (which heuristic)
5. Commit updates with release

**Don't stress about perfect tracking** - this is a lightweight pattern-detection tool, not a comprehensive database.

**Quarterly cleanup:**
- Review all candidates
- Remove issues that haven't recurred in 6+ months
- Move automated checks to "Recently Automated"

---

## Notes

- This file is intentionally lightweight - don't over-engineer it
- Focus on patterns and recurring issues, not perfect record-keeping
- Use judgment when deciding what to track
- When in doubt, don't track (keep the file focused)
