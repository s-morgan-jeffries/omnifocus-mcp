# Documentation Quality Check

**Purpose:** Perform comprehensive qualitative assessment of project documentation.

**When to run:**
- Before minor/major version releases
- After significant documentation changes
- When onboarding new contributors
- Quarterly documentation audits

---

## Task Instructions

Use the Task tool with `subagent_type="general-purpose"` to perform a comprehensive documentation quality analysis.

**Analysis scope:**
1. **README completeness**
   - Installation instructions current and complete?
   - All 16 API functions documented with examples?
   - Quick start guide clear and accurate?
   - Configuration examples work with current setup?

2. **Foundation model interpretability**
   - Can AI assistants (Claude/GPT) understand the docs?
   - Are examples clear and unambiguous?
   - Is terminology consistent throughout?
   - Are edge cases and gotchas documented?

3. **Cross-reference integrity**
   - All internal links valid (markdown links to other docs)?
   - References to functions/files/versions correct?
   - Version references accurate across all docs?
   - CHANGELOG matches actual releases?

4. **Technical accuracy**
   - Code examples match current API (v0.6.5)?
   - Migration guides still relevant?
   - Architecture docs reflect actual implementation?
   - Test instructions work as written?

**Files to analyze:**
- README.md
- CHANGELOG.md
- docs/guides/CONTRIBUTING.md
- docs/guides/TESTING.md
- docs/guides/INTEGRATION_TESTING.md
- docs/reference/ARCHITECTURE.md
- docs/reference/API_REFERENCE.md
- docs/reference/HYGIENE_CHECK_CRITERIA.md
- docs/project/ROADMAP.md
- .claude/CLAUDE.md

**Output format:**

```markdown
# Documentation Quality Report - v0.6.5

**Date:** YYYY-MM-DD
**Analyzed by:** Claude Code

---

## Executive Summary

[2-3 paragraphs summarizing overall documentation quality, major strengths, critical gaps]

---

## Critical Issues (Must Fix Before Release)

- [ ] **README.md:** Example uses deprecated function X (line 45)
- [ ] **CONTRIBUTING.md:** Missing installation step for M1 Macs
- [ ] **API_REFERENCE.md:** Function signature doesn't match implementation

**Impact:** [Describe user impact if not fixed]

---

## Recommended Improvements (High Priority)

- [ ] **TESTING.md:** Add troubleshooting section for common test failures
- [ ] **ARCHITECTURE.md:** Expand rationale for batch update design decision
- [ ] **README.md:** Add example for common use case: bulk task updates

**Impact:** [Describe benefit of addressing these]

---

## Good Practices Observed

✅ **Consistent terminology** - "update" vs "set" used consistently throughout
✅ **Clear section headings** - Easy to navigate with table of contents
✅ **Version references accurate** - All docs show v0.6.5 consistently
✅ **Code examples tested** - Examples match current API signatures
✅ **Cross-references complete** - HYGIENE_CHECK_CRITERIA.md linked from key docs

---

## Minor Issues (Low Priority)

- **ROADMAP.md:** Could benefit from more specific timeline for future work
- **CONTRIBUTING.md:** Git workflow section could use diagrams
- **API_REFERENCE.md:** Consider adding "common mistakes" section

---

## Foundation Model Readability Analysis

**Clarity:** 9/10 - Documentation is clear and well-structured
**Completeness:** 8/10 - Missing some edge case documentation
**Consistency:** 10/10 - Terminology and formatting highly consistent
**Accuracy:** 9/10 - One outdated example found (see Critical Issues)

**Notes:**
- Architecture decision rationale is excellent - very clear "why" explanations
- CLAUDE.md provides great context for AI-assisted development
- Examples are practical and cover common use cases
- TDD requirements clearly stated and enforced

---

## Suggestions for Future Enhancement

1. **Video walkthrough** - Consider adding screencast for setup/first use
2. **API reference expansion** - More edge case examples in function docs
3. **Troubleshooting guide** - Dedicated doc for common issues and solutions
4. **Architecture decision records** - Formalize ADR pattern for future decisions

---

## Cross-Reference Verification

**Checked:** 47 internal links
**Valid:** 46 links
**Broken:** 1 link - `docs/archive/OLD_FILE.md` referenced in ROADMAP.md

---

## Conclusion

[Final assessment paragraph - ready for release? What needs immediate attention?]

**Recommendation:** [READY FOR RELEASE | FIX CRITICAL ISSUES FIRST | NEEDS SIGNIFICANT WORK]
```

**Important:**
- Focus on actionable feedback with specific line numbers/file names
- Use severity levels (Critical/Recommended/Minor)
- Provide concrete examples of issues found
- Be honest about documentation gaps - don't inflate quality
- Check that code examples actually work with current API
- Verify technical accuracy against actual implementation

**Agent task:**

```
Analyze the documentation quality for the OmniFocus MCP Server project.

Files to read:
- README.md
- CHANGELOG.md
- docs/guides/CONTRIBUTING.md
- docs/guides/TESTING.md
- docs/guides/INTEGRATION_TESTING.md
- docs/reference/ARCHITECTURE.md
- docs/reference/API_REFERENCE.md
- docs/reference/HYGIENE_CHECK_CRITERIA.md
- docs/project/ROADMAP.md
- .claude/CLAUDE.md

Perform comprehensive quality analysis covering:
1. README completeness and accuracy
2. Foundation model interpretability
3. Cross-reference integrity
4. Technical accuracy (code examples match current v0.6.5 API)
5. Clarity, consistency, and completeness

Generate a detailed quality report using the template above. Focus on actionable recommendations with specific file/line references.
```
