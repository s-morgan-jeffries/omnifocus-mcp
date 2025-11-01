# Test Coverage Check

**Purpose:** Perform comprehensive qualitative assessment of test coverage beyond the 85% minimum threshold.

**When to run:**
- Before minor/major version releases
- After adding new features or functions
- When addressing test gaps
- During code reviews
- Quarterly test quality audits

---

## Task Instructions

Use the Task tool with `subagent_type="general-purpose"` to perform a comprehensive test coverage analysis.

**Analysis scope:**
1. **Coverage Metrics and Trends**
   - Current coverage percentage vs 85% threshold
   - Coverage by module/file
   - Trend over time (if historical data available)
   - Lines/branches covered vs missed

2. **TODO Test Markers**
   - Identify TODO markers in source code indicating missing tests
   - Categorize by priority and age
   - Assess impact of missing tests

3. **Untested Functions**
   - List all public functions without obvious test coverage
   - Assess criticality of each function
   - Identify edge cases that may be missing

4. **Coverage Gaps by Module**
   - Which modules have lowest coverage?
   - Which critical paths lack coverage?
   - Are integration points well-tested?

5. **Test Quality Assessment**
   - Do tests check edge cases?
   - Are error conditions tested?
   - Is there proper mocking/isolation?
   - Are integration tests comprehensive?

6. **Testing Types Assessment**
   - What types of testing are currently in place? (unit, integration, e2e)
   - What types are missing or limited? (performance, load, property-based, mutation, security, stress, compatibility)
   - Which missing types would be most beneficial for this project?
   - Prioritize recommendations by value and effort

**Files to analyze:**

Run the existing test coverage script and analyze its output:
```bash
./scripts/check_test_coverage.sh
```

Then perform deeper analysis on:
- `src/omnifocus_mcp/**/*.py` - All source code
- `tests/**/*.py` - All test files
- Coverage reports: Run `pytest --cov=src/omnifocus_mcp --cov-report=term-missing`

**Output format:**

```markdown
# Test Coverage Report - v0.6.6

**Date:** YYYY-MM-DD
**Analyzed by:** Claude Code

---

## Executive Summary

[2-3 paragraphs summarizing overall test coverage, strengths, critical gaps]

**Current Coverage:** XX% (threshold: 85%)
**Status:** [ABOVE THRESHOLD ✅ | BELOW THRESHOLD ❌]

**Test Distribution:**
- Unit tests: XXX tests
- Integration tests: XX tests
- E2E tests: XX tests

**Coverage Trend:** [Improving/Stable/Declining] compared to last audit

---

## Critical Coverage Gaps (Must Fix Before Release)

- [ ] **omnifocus_connector.py:123** - Function `critical_function()` has 0% coverage
- [ ] **server_fastmcp.py:456** - Error handling path never tested
- [ ] **omnifocus_connector.py:789** - Edge case for empty database not covered

**Impact:** [Describe user impact if not fixed]
**Estimated Effort:** [X hours to add missing tests]

---

## Recommended Improvements (High Priority)

- [ ] **omnifocus_connector.py:234** - Function `get_tasks()` missing edge case tests (empty results)
- [ ] **omnifocus_connector.py:567** - `update_project()` missing integration test for note field
- [ ] **server_fastmcp.py:890** - MCP tool wrapper not tested end-to-end

**Impact:** [Describe benefit of addressing these]
**Estimated Effort:** [X hours to add comprehensive tests]

---

## Good Practices Observed

✅ **High overall coverage** - 89% exceeds 85% threshold
✅ **Comprehensive unit tests** - All public functions have basic test coverage
✅ **Integration test suite** - Real OmniFocus testing validates AppleScript
✅ **E2E testing** - MCP tool invocation tested end-to-end
✅ **Mock isolation** - Unit tests properly mock AppleScript calls
✅ **Edge case coverage** - Most functions test boundary conditions

---

## Minor Improvements (Low Priority)

- **test_tasks.py:345** - Consider adding performance test for large result sets
- **test_projects.py:678** - Test could be more readable with helper function
- **test_integration.py:901** - Add test for concurrent operations

---

## Coverage by Module

| Module | Coverage | Lines | Missing | Status |
|--------|----------|-------|---------|--------|
| omnifocus_connector.py | 92% | 450 | 36 | ✅ Excellent |
| server_fastmcp.py | 85% | 200 | 30 | ✅ Meets threshold |
| __init__.py | 100% | 10 | 0 | ✅ Complete |

**Lowest Coverage Modules:**
1. server_fastmcp.py (85%) - Error handling paths need coverage
2. omnifocus_connector.py (92%) - Some edge cases missing

---

## TODO Test Markers

**Found:** X TODO markers in source code

**High Priority (missing critical tests):**
- omnifocus_connector.py:123 - "TODO: Test retry logic for network failures" (6 months old)
- server_fastmcp.py:456 - "TODO: Test MCP error responses" (3 months old)

**Medium Priority (missing edge case tests):**
- omnifocus_connector.py:789 - "TODO: Test with malformed AppleScript response" (2 months old)

**Low Priority (nice-to-have tests):**
- omnifocus_connector.py:234 - "TODO: Add performance test" (has tracking issue #X)

---

## Untested Functions

**Found:** X public functions without obvious test coverage

**Critical Functions (must test before release):**
- None ✅ All critical functions have test coverage

**Nice-to-Have Coverage:**
- `_internal_helper()` - Private helper function, low priority
- `format_error_message()` - Simple formatting, manual testing OK

---

## Coverage Gaps by Function

**Functions Below 80% Coverage:**

| Function | Coverage | Missing Lines | Reason |
|----------|----------|---------------|--------|
| get_tasks() | 85% | Lines 123-130 | Empty result edge case |
| update_project() | 82% | Lines 456-460 | Error recovery path |

**Functions with Uncovered Error Paths:**
- omnifocus_connector.py:234 - `create_task()` missing test for invalid project_id
- omnifocus_connector.py:567 - `update_task()` missing test for AppleScript timeout

---

## Test Quality Assessment

**Unit Tests:**
- ✅ Comprehensive mocking of AppleScript calls
- ✅ Tests isolated from OmniFocus dependencies
- ⚠️ Some edge cases could be more thorough
- ✅ Good use of parametrized tests for similar cases

**Integration Tests:**
- ✅ Real OmniFocus validation
- ✅ Covers all 16 API functions
- ⚠️ Could add more concurrent operation tests
- ✅ Proper setup/teardown for test data

**E2E Tests:**
- ✅ MCP tool invocation tested
- ⚠️ Could expand error scenario coverage
- ✅ JSON serialization validated

**Overall Quality:** [EXCELLENT | GOOD | ACCEPTABLE | NEEDS WORK]

---

## Edge Cases Analysis

**Well-Covered Edge Cases:**
- ✅ Empty database scenarios
- ✅ Invalid IDs and null values
- ✅ Malformed input data
- ✅ Concurrent operations

**Missing Edge Cases:**
- ⚠️ Network timeout during long operations
- ⚠️ OmniFocus not running
- ⚠️ Extremely large result sets (>1000 items)

---

## Integration Points Assessment

**Critical Integration Points:**

| Integration | Coverage | Tests | Status |
|-------------|----------|-------|--------|
| AppleScript execution | 95% | 45 tests | ✅ Excellent |
| MCP FastMCP server | 85% | 12 tests | ✅ Good |
| JSON serialization | 100% | 20 tests | ✅ Complete |
| Error handling | 80% | 15 tests | ⚠️ Could improve |

**Recommendation:** Add more error scenario tests for MCP tool wrappers.

---

## Historical Trend

**Coverage over time:**
- v0.6.5: 89% (current)
- v0.6.4: 87%
- v0.6.3: 85%
- v0.6.0: 82%

**Trend:** ✅ Improving - coverage has increased 7% over last 3 versions

---

## Testing Types Assessment

**Current Testing Types:**
- ✅ Unit tests (mocked, fast, 333 tests)
- ✅ Integration tests (real OmniFocus, ~10-30s)
- ✅ E2E tests (full MCP stack)

**Missing or Limited Testing Types:**

### Performance Testing
- **Current Status:** Limited or none
- **Would Be Beneficial For:**
  - get_tasks() with large result sets (>1000 tasks)
  - Batch updates (update_tasks/update_projects with 100+ items)
  - Concurrent operations (multiple clients)
  - Memory usage with large data sets
- **Recommendation Priority:** Medium - Important for production use cases

### Load Testing
- **Current Status:** None
- **Would Be Beneficial For:**
  - MCP server handling multiple simultaneous requests
  - AppleScript execution under load
  - Database query performance
- **Recommendation Priority:** Low - Nice to have for production deployments

### Property-Based Testing
- **Current Status:** None
- **Would Be Beneficial For:**
  - Discovering edge cases in input validation
  - Testing update_task/update_project with random parameter combinations
  - Fuzzing date/time parsing logic
- **Tool Suggestion:** Hypothesis library
- **Recommendation Priority:** Medium - Good for robustness

### Mutation Testing
- **Current Status:** None
- **Would Be Beneficial For:**
  - Evaluating test suite effectiveness
  - Finding untested code paths
  - Ensuring tests actually validate behavior
- **Tool Suggestion:** mutmut or cosmic-ray
- **Recommendation Priority:** Low - Quality assurance tool

### Security Testing
- **Current Status:** Limited
- **Would Be Beneficial For:**
  - Input sanitization (SQL-like injection in AppleScript)
  - MCP tool parameter validation
  - Error message information disclosure
- **Recommendation Priority:** Medium - Important for production

### Stress Testing
- **Current Status:** None
- **Would Be Beneficial For:**
  - AppleScript timeout behavior
  - Recovery from OmniFocus crashes
  - Memory leaks in long-running server
- **Recommendation Priority:** Low - Useful for production stability

### Regression Testing
- **Current Status:** Implicit in test suite
- **Would Be Beneficial For:**
  - Automated testing of fixed bugs
  - Version upgrade validation
  - API compatibility verification
- **Recommendation Priority:** High - Already mostly in place

### Compatibility Testing
- **Current Status:** Limited
- **Would Be Beneficial For:**
  - Different OmniFocus versions
  - Different macOS versions
  - Different Python versions (3.10, 3.11, 3.12)
- **Recommendation Priority:** Medium - Important for broad deployment

---

## Suggestions for Future Enhancement

1. **Property-based testing** - Consider using Hypothesis for edge case discovery
2. **Performance tests** - Add tests for large data sets and concurrent operations
3. **Coverage goals** - Consider raising threshold to 90% for new code
4. **Mutation testing** - Evaluate test effectiveness with mutation testing tools
5. **Coverage dashboard** - Track coverage trends over time in CI

---

## Comparison with Project Standards

**Project Standards:**
- ✅ Minimum 85% coverage threshold (enforced in CI)
- ✅ Three test tiers required (unit, integration, E2E)
- ✅ All public functions must have tests
- ✅ Test-driven development (TDD) required for new features

**Current Compliance:**
- Coverage: XX% [ABOVE | BELOW] threshold
- Test tiers: [ALL PRESENT | MISSING X]
- Function coverage: XX% of public functions tested
- TDD adherence: [EXCELLENT | GOOD | NEEDS IMPROVEMENT]

---

## Conclusion

[Final assessment paragraph - is test coverage acceptable for release? What needs immediate attention?]

**Overall Test Coverage:** [EXCELLENT | GOOD | ACCEPTABLE | INADEQUATE]
**Recommendation:** [READY FOR RELEASE | ADD CRITICAL TESTS FIRST | NEEDS SIGNIFICANT WORK]

**Release Blockers:** [List any coverage gaps that must be fixed before release]

**Estimated Effort to Address Gaps:** [X hours/days for high-priority items]
```

**Important:**
- Focus on actionable feedback with specific file/line references
- Use severity levels (Critical/Recommended/Minor)
- Provide concrete examples of missing coverage
- Be honest about test quality - don't inflate coverage ratings
- Compare against project standards (85% threshold, three test tiers)
- Assess test quality, not just percentage
- Identify specific edge cases and error paths that lack coverage
- Provide effort estimates for addressing gaps

**Agent task:**

```
Analyze the test coverage for the OmniFocus MCP Server project.

Step 1: Run existing coverage check
Execute ./scripts/check_test_coverage.sh and capture its output.

Step 2: Generate detailed coverage report
Run pytest with coverage:
  pytest tests/ -m "not integration" --cov=src/omnifocus_mcp --cov-report=term-missing

Step 3: Analyze coverage by module
Identify which modules have lowest coverage.
List specific lines/functions that lack coverage.

Step 4: Scan for TODO test markers
Search src/omnifocus_mcp/ for "TODO.*test" comments.
Categorize by age and priority.

Step 5: Identify untested functions
List all public functions from omnifocus_connector.py.
Check if each has corresponding tests in tests/.
Identify critical functions without coverage.

Step 6: Assess test quality
Review test files to assess:
- Edge case coverage
- Error condition testing
- Mock/isolation quality
- Integration test comprehensiveness

Step 7: Analyze coverage gaps
Identify:
- Functions below 80% coverage
- Uncovered error paths
- Missing edge cases
- Integration points needing tests

Step 8: Assess testing types
Evaluate what types of testing would be beneficial:
- Performance testing (large data sets, concurrent operations)
- Property-based testing (edge case discovery)
- Security testing (input sanitization, parameter validation)
- Compatibility testing (different versions)
- Load/stress testing (production stability)
Prioritize by value and effort.

Step 9: Generate report
Generate a detailed coverage report using the template above. Focus on actionable recommendations with specific file/line references. Compare against project standards (85% threshold, three test tiers required). Include assessment of beneficial testing types.

Note: The check_test_coverage.sh script enforces the 85% threshold. Your analysis should go deeper and assess test quality and types, not just quantity.
```
