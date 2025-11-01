# Code Quality Check

**Purpose:** Perform comprehensive qualitative assessment of code quality beyond basic complexity metrics.

**When to run:**
- Before minor/major version releases
- After significant code changes
- When addressing technical debt
- During code reviews
- Quarterly code quality audits

---

## Task Instructions

Use the Task tool with `subagent_type="general-purpose"` to perform a comprehensive code quality analysis.

**Analysis scope:**
1. **Cyclomatic Complexity**
   - Identify D-F rated functions (CC > 20)
   - Assess if complexity is documented or has exceptions
   - Compare against project standards (A-B target for new code)

2. **Code Maintenance Markers**
   - TODO/FIXME comments in source code
   - Context and priority of each marker
   - Age and ownership of technical debt

3. **Logging Standards**
   - print() statements that should use logging
   - Consistency of logging approach
   - Debug statements left in production code

4. **Exception Handling**
   - Bare except: clauses (should catch specific exceptions)
   - Error handling completeness
   - Exception propagation patterns

5. **Code Readability**
   - Lines exceeding 120 characters
   - Readability vs necessary length trade-offs
   - Formatting consistency

**Files to analyze:**

Run the existing hygiene check script and analyze its output:
```bash
./scripts/check_code_quality.sh
```

Then perform deeper analysis on:
- `src/omnifocus_mcp/**/*.py` - All source code
- Exclude: `venv/`, `.pytest_cache/`, `__pycache__/`

**Output format:**

```markdown
# Code Quality Report - v0.6.6

**Date:** YYYY-MM-DD
**Analyzed by:** Claude Code

---

## Executive Summary

[2-3 paragraphs summarizing overall code quality, major strengths, areas needing attention]

**Complexity Summary:**
- Total functions analyzed: X
- A-B rated (CC 1-10): X functions ✅
- C rated (CC 11-20): X functions ⚠️
- D-F rated (CC 21+): X functions 🔴

**Maintenance Markers:** X TODO/FIXME comments found
**Logging Issues:** X print() statements found
**Exception Handling:** X bare except clauses found
**Readability:** X lines over 120 characters

---

## Critical Issues (Must Fix Before Release)

- [ ] **file.py:123** - Function `foo()` has CC=25 (D rating) without documentation
- [ ] **file.py:456** - Bare except clause catching all exceptions silently
- [ ] **file.py:789** - print() statement in production error handling

**Impact:** [Describe user impact if not fixed]

---

## Recommended Improvements (High Priority)

- [ ] **file.py:234** - TODO marker from 6 months ago: "Refactor this logic"
- [ ] **file.py:567** - Function `bar()` has CC=18 (C rating), consider splitting
- [ ] **file.py:890** - print() used for debugging, should use logger.debug()

**Impact:** [Describe benefit of addressing these]

---

## Good Practices Observed

✅ **Low complexity** - 95% of functions have A-B rating (CC ≤ 10)
✅ **Specific exceptions** - Most error handling catches specific exception types
✅ **Consistent logging** - Core modules use proper logging infrastructure
✅ **Documented complexity** - Known complex functions (get_tasks, update_task) have justification
✅ **Type hints** - All public functions have complete type annotations

---

## Minor Issues (Low Priority)

- **file.py:345** - Line 130 characters (logging statement, acceptable)
- **file.py:678** - TODO for future enhancement (has tracking issue #X)
- **file.py:901** - FIXME for Python 3.12 compatibility (non-urgent)

---

## Complexity Analysis

**Functions Requiring Attention:**

| Function | File | CC Rating | Line | Notes |
|----------|------|-----------|------|-------|
| get_tasks() | omnifocus_connector.py | 22 (D) | 234 | Has documented exception ✅ |
| update_task() | omnifocus_connector.py | 21 (D) | 456 | Has documented exception ✅ |
| _parse_response() | omnifocus_connector.py | 18 (C) | 678 | Consider refactoring |

**Documented Exceptions:**
- `get_tasks()` - Complex filtering logic, comprehensive test coverage
- `update_task()` - Handles 15+ optional parameters, well-tested

---

## Maintenance Markers Analysis

**TODO Comments:** X found

**High Priority (blocking work or known bugs):**
- file.py:123 - "TODO: Fix race condition in task updates" (6 months old)
- file.py:456 - "TODO: Add retry logic for network failures" (3 months old)

**Medium Priority (improvements or refactoring):**
- file.py:789 - "TODO: Extract this into separate function" (2 months old)

**Low Priority (future enhancements):**
- file.py:234 - "TODO: Support batch operations in Python 3.12" (has issue #X)

**FIXME Comments:** X found
- file.py:567 - "FIXME: Temporary workaround for AppleScript timeout"

---

## Logging Standards Assessment

**print() Statements:** X found

**Production Code (should use logging):**
- file.py:123 - Error reporting in exception handler
- file.py:456 - Debug output in main processing loop

**Acceptable (if any):**
- scripts/helper.py:789 - User-facing CLI output (OK for scripts)

**Recommendation:** Replace production print() with appropriate logger calls:
- logger.error() for error reporting
- logger.debug() for debugging output
- logger.info() for important status updates

---

## Exception Handling Analysis

**Bare except: clauses:** X found

**Problematic:**
- file.py:123 - Catches all exceptions, suppresses errors silently
- file.py:456 - Generic exception handler without logging

**Recommendation:** Catch specific exceptions:
```python
# ❌ Bad
try:
    risky_operation()
except:
    pass

# ✅ Good
try:
    risky_operation()
except (ValueError, KeyError) as e:
    logger.error(f"Operation failed: {e}")
    raise
```

---

## Readability Analysis

**Lines over 120 characters:** X lines

**Acceptable long lines (data, logging, etc.):**
- file.py:123 - Logging statement with context (130 chars)
- file.py:456 - Type annotation with complex Union type (125 chars)

**Should be refactored:**
- file.py:789 - Complex conditional expression (145 chars)
- file.py:234 - Chained method calls (135 chars)

---

## Comparison with Project Standards

**Project Targets:**
- ✅ A-B rating (CC 1-10): Target for new code
- ⚠️ C rating (CC 11-20): Acceptable for complex business logic
- 🔴 D-F rating (CC 21+): Requires documentation or refactoring

**Current Status:**
- XX% of functions meet A-B target
- XX% have C rating (complex but acceptable)
- XX% have D-F rating (need attention)

**Trend:** [Improving/Stable/Declining] compared to last audit

---

## Suggestions for Future Enhancement

1. **Complexity refactoring** - Split D-rated functions without documented exceptions
2. **TODO cleanup** - Create tracking issues for all old TODOs, remove after tracking
3. **Logging consistency** - Establish logging standards in CONTRIBUTING.md
4. **Exception handling** - Add linting rule to catch bare except clauses
5. **Line length** - Configure formatter to enforce 120 char limit

---

## Technical Debt Assessment

**High-Priority Debt:**
- X unresolved TODOs over 3 months old
- X functions with D-F complexity without documentation
- X bare except clauses in production code

**Medium-Priority Debt:**
- X functions with C complexity that could be simplified
- X print() statements in library code
- X lines significantly over character limit

**Low-Priority Debt:**
- X TODO markers with tracking issues
- X acceptable-length lines slightly over limit

**Estimated Effort:** [X days to address high-priority debt]

---

## Conclusion

[Final assessment paragraph - is code quality acceptable for release? What needs immediate attention?]

**Overall Code Quality:** [EXCELLENT | GOOD | ACCEPTABLE | NEEDS WORK]
**Recommendation:** [READY FOR RELEASE | FIX CRITICAL ISSUES FIRST | NEEDS REFACTORING]

**Release Blockers:** [List any issues that must be fixed before release]
```

**Important:**
- Focus on actionable feedback with specific line numbers/file names
- Use severity levels (Critical/Recommended/Minor)
- Provide concrete examples of issues found
- Be honest about code quality - don't inflate ratings
- Compare against project standards (see `.claude/CLAUDE.md` and `docs/reference/CODE_QUALITY.md`)
- Assess trends over time if previous audit results available
- Provide effort estimates for addressing technical debt

**Agent task:**

```
Analyze the code quality for the OmniFocus MCP Server project.

Step 1: Run existing quality check
Execute ./scripts/check_code_quality.sh and capture its output.

Step 2: Analyze complexity
Run radon cc on src/omnifocus_mcp/ to get detailed complexity metrics.
Identify functions with D-F ratings (CC > 20).
Check if complex functions have documented exceptions (get_tasks, update_task).

Step 3: Scan for maintenance markers
Search src/omnifocus_mcp/ for TODO and FIXME comments.
Categorize by age, priority, and whether they have tracking issues.

Step 4: Check logging standards
Find print() statements in src/omnifocus_mcp/ (exclude scripts/).
Assess if they should use logging instead.

Step 5: Check exception handling
Find bare except: clauses in src/omnifocus_mcp/.
Assess if they should catch specific exceptions.

Step 6: Check readability
Find lines over 120 characters.
Assess if they're acceptable (data, logging) or should be refactored.

Step 7: Generate report
Generate a detailed quality report using the template above. Focus on actionable recommendations with specific file/line references. Compare against project standards (A-B target for new code, C acceptable, D-F needs documentation).

Note: The check_code_quality.sh script provides quick checks. Your analysis should go deeper and provide context, priorities, and recommendations.
```
