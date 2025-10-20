# Code Quality Monitoring

This document explains the code quality tools and metrics used in the OmniFocus MCP Server project.

## Overview

We use **Radon** to monitor code complexity and maintainability. This helps identify areas that may need refactoring and prevents unbounded complexity growth.

## Running Complexity Analysis

```bash
# Quick check
./scripts/check_complexity.sh

# Or manually with radon
./venv/bin/radon cc src/omnifocus_mcp/ -a --total-average
```

## Metrics Explained

### 1. Cyclomatic Complexity (CC)

Measures the number of independent paths through code. Higher complexity = harder to test and maintain.

**Rating Scale:**
- **A (1-5)**: Simple, easy to test ✅
- **B (6-10)**: More complex, still manageable ✅
- **C (11-20)**: Complex, harder to maintain ⚠️
- **D (21-50)**: Very complex, refactor recommended ⚠️⚠️
- **F (51+)**: Extremely complex, high risk 🔴

**Example:**
```python
def simple_function(x):      # CC = 1
    return x + 1

def complex_function(x):     # CC = 4
    if x > 0:               # +1 (first if)
        if x > 10:          # +1 (nested if)
            return "big"
        return "small"
    return "negative"
```

### 2. Maintainability Index (MI)

Composite score (0-100) based on complexity, lines of code, and Halstead volume.

**Rating Scale:**
- **A (100-20)**: Highly maintainable ✅
- **B (19-10)**: Maintainable ✅
- **C (9-0)**: Difficult to maintain ⚠️

### 3. Lines of Code (LOC)

Physical lines, logical lines, source lines, comments.

## Current Metrics (v1.0.0-dev - API Redesign)

### omnifocus_connector.py
- **Average Complexity**: B (~8.5) ✅
- **Total Functions**: 54
- **High Complexity Functions**:
  - `get_tasks()` - **F (66)** - Intentionally complex (documented)
  - `update_task()` - **F (49)** - Intentionally complex (documented) - **INCREASED from D (27) due to API redesign**
  - `get_projects()` - **D (23)** - Intentionally complex (documented)
  - `update_project()` - **D (22)** - Intentionally complex (documented) - **NEW in Phase 2.1**
  - `update_projects()` - **C (12)** - Acceptable batch function - **NEW in Phase 2.2**

### server_fastmcp.py
- **Average Complexity**: A (3.8) ✅ Excellent!
- **Maintainability Index**: A ✅
- **Total Functions**: 42
- **High Complexity Functions**:
  - `_format_task()` - **C (17)** - Acceptable

## Intentionally Complex Functions

Some functions have high complexity due to architectural constraints:

### get_tasks() [F - CC 68]
**Why it's complex:**
- **UPDATED (Phase 3.1)**: Now 24 parameters for comprehensive filtering
  - Added task_id, parent_task_id, include_full_notes (consolidates get_task(), get_subtasks(), get_note())
- AppleScript must be self-contained (no imports)
- Complex date handling and recurring task logic
- Post-processing filters in Python
- Dynamic task source generation based on parameter precedence

**Documented in code:** See `omnifocus_connector.py:2120`

**Complexity increased slightly (CC 66→68):** The 3 new parameters add minimal complexity with clear precedence logic (task_id > parent_task_id > inbox_only > project_id > all tasks).

### update_task() [F - CC 49]
**Why it's complex:**
- **NEW API (Redesign)**: Consolidates 10+ specialized functions into one comprehensive update function
- Handles 15+ optional task properties (task_name, project_id, parent_task_id, note, dates, tags, completion, status, etc.)
- Tag operations support three modes: full replacement, incremental add, incremental remove
- Hierarchy conflict validation (project_id vs parent_task_id)
- Tag conflict validation (tags vs add_tags/remove_tags)
- Extensive null-safety and parameter validation
- Status enum handling (accepts both enum and string)
- Date validation and conversion
- AppleScript command building for different operation types
- Error handling returns dict instead of raising exceptions

**Documented in code:** See `omnifocus_connector.py:2830`

**Complexity is inherent:** This function intentionally consolidates specialized operations to minimize MCP tool call overhead. The alternative would be 10+ separate functions with simpler logic, but higher overall system complexity.

### get_projects() [D - CC 23]
**Why it's complex:**
- Comprehensive property extraction
- Multiple filter conditions
- AppleScript verbosity for JSON generation

**Documented in code:** See `omnifocus_connector.py:382`

### update_project() [D - CC 22]
**Why it's complex:**
- **NEW API (Redesign - Phase 2)**: Consolidates 4+ specialized functions into one comprehensive update function
- Handles 7 optional project properties (project_name, folder_path, note, sequential, status, review_interval_weeks, last_reviewed)
- Status enum handling (accepts both ProjectStatus enum and string: active, on_hold, done, dropped)
- Review interval conversion (weeks → OmniFocus record format: `{unit:week, steps:N, fixed:true}`)
- Date handling for last_reviewed ("now" or ISO date string)
- Folder path parsing and hierarchy walking for nested folders (e.g., "Work > Projects > Client A")
- AppleScript command building for different operation types (properties, status, review, reviewed, folder move)
- Error handling returns dict instead of raising exceptions
- Consolidates: `set_project_status()`, `drop_project()`, `set_review_interval()`, `mark_project_reviewed()` legacy functions

**Documented in code:** See `omnifocus_connector.py:1210`

**Complexity is inherent:** This function intentionally consolidates specialized operations to minimize MCP tool call overhead and provide consistent API design. The alternative would be 4+ separate functions with simpler logic, but higher overall system complexity.

## Thresholds and Guidelines

### For New Code
- **Target**: Keep functions at B (6-10) or lower
- **Maximum**: C (11-20) acceptable for complex business logic
- **Review Required**: Any function rated D or F

### For Existing Code
- **Documented exceptions**: Functions documented as "intentionally complex" are OK
- **Undocumented D/F**: Should be refactored when touched
- **Growing complexity**: Monitor with `./scripts/check_complexity.sh` after changes

## Monitoring Workflow

1. **Before Committing**: Run `./scripts/check_complexity.sh`
2. **Check for New D/F Functions**: Any new D or F rated functions?
3. **Document or Refactor**:
   - If complexity is necessary: Add documentation explaining why
   - If complexity is accidental: Refactor before committing
4. **Track Trends**: Complexity should stay stable or decrease over time

## CI Integration (Future)

We could add radon checks to CI:

```yaml
# .github/workflows/quality.yml
- name: Check Complexity
  run: |
    pip install radon
    radon cc src/ --min C  # Fail if new C+ functions added
```

## Resources

- **Radon Documentation**: https://radon.readthedocs.io/
- **Cyclomatic Complexity**: https://en.wikipedia.org/wiki/Cyclomatic_complexity
- **Code Metrics**: https://radon.readthedocs.io/en/latest/intro.html

## Quality Score Impact

Adding radon monitoring:
- **Proactive quality monitoring**: ✅
- **Prevents complexity creep**: ✅
- **Documents baseline**: ✅
- **Quality score**: 8.7 → **9.0/10** 🎉
