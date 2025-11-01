# Directory Organization Check

**Purpose:** Perform comprehensive qualitative assessment of project directory organization and file structure.

**When to run:**
- Before minor/major version releases
- When onboarding new contributors
- After significant restructuring
- During project audits
- Quarterly organization reviews

---

## Task Instructions

Use the Task tool with `subagent_type="general-purpose"` to perform a comprehensive directory organization analysis.

**Analysis scope:**
1. **Directory Structure**
   - Is the structure logical and intuitive?
   - Are similar files grouped together?
   - Is the purpose of each directory clear?
   - Does structure match common Python project conventions?

2. **File Organization**
   - Are files in appropriate directories?
   - Are there orphaned or misplaced files?
   - Is there excessive nesting or flat structure?
   - Are naming conventions consistent?

3. **Documentation Structure**
   - Is documentation well-organized by type (guides, reference, project)?
   - Are docs easy to find for new contributors?
   - Is there clear separation between user-facing and developer docs?
   - Are examples and reference material logically placed?

4. **Archive Organization**
   - Are outdated files properly archived?
   - Is there clear distinction between active and archived content?
   - Are archive directories labeled and organized?
   - Should any current files be archived?

5. **Configuration Files**
   - Are config files in appropriate locations?
   - Is there clear separation of concerns?
   - Are tool configs (.claude/, .github/) well-organized?
   - Are there duplicate or obsolete configs?

6. **New Contributor Clarity**
   - Can new contributors quickly understand project structure?
   - Are key files easy to locate?
   - Is there clear documentation of directory purposes?
   - Would a directory README be helpful anywhere?

**Files to analyze:**

List and analyze the complete directory structure:
```bash
# Get directory tree
tree -L 3 -d --dirsfirst

# List all files by directory
find . -type f -not -path "*/venv/*" -not -path "*/.pytest_cache/*" -not -path "*/__pycache__/*" | sort
```

**Output format:**

```markdown
# Directory Organization Report - v0.6.6

**Date:** YYYY-MM-DD
**Analyzed by:** Claude Code

---

## Executive Summary

[2-3 paragraphs summarizing overall directory organization, strengths, areas for improvement]

**Structure Assessment:** [EXCELLENT | GOOD | ACCEPTABLE | NEEDS WORK]
**New Contributor Clarity:** [HIGH | MEDIUM | LOW]
**Maintenance Burden:** [LOW | MEDIUM | HIGH]

---

## Critical Issues (Must Fix Before Release)

- [ ] **Root directory** - Critical config file misplaced (should be in .github/)
- [ ] **src/** - Module structure inconsistent with package conventions
- [ ] **docs/** - User-facing and developer docs mixed without clear separation

**Impact:** [Describe impact on contributors if not fixed]

---

## Recommended Improvements (High Priority)

- [ ] **docs/** - Create subdirectories for different doc types (guides, reference, project)
- [ ] **tests/** - Split integration tests into separate directory
- [ ] **scripts/** - Add README explaining purpose of each script

**Impact:** [Describe benefit of addressing these]

---

## Good Practices Observed

✅ **Clear src/ structure** - Single package with logical module organization
✅ **Separated tests/** - Test files clearly separated from source
✅ **docs/ organization** - Documentation in dedicated directory
✅ **Configuration isolation** - Tool configs in appropriate directories (.claude/, .github/)
✅ **Archive separation** - Old files properly archived in docs/archive/

---

## Minor Improvements (Low Priority)

- **Root directory** - Consider moving VERSION to src/omnifocus_mcp/
- **.claude/** - Some command files could use more descriptive names
- **scripts/** - Could organize by type (checks/, hooks/, utilities/)

---

## Directory Structure Analysis

### Root Directory

**Current Files:**
```
README.md
CHANGELOG.md
LICENSE
VERSION
pyproject.toml
requirements.txt
```

**Assessment:** ✅ Clean root directory with essential files only

**Recommendations:**
- None - root directory is well-organized

### Source Code (src/)

**Current Structure:**
```
src/
└── omnifocus_mcp/
    ├── __init__.py
    ├── omnifocus_connector.py
    ├── server_fastmcp.py
    └── types.py
```

**Assessment:** ✅ Excellent - follows Python package conventions

**Recommendations:**
- None - structure is appropriate for project size

### Tests (tests/)

**Current Structure:**
```
tests/
├── __init__.py
├── test_tasks.py
├── test_projects.py
├── test_integration.py
├── test_e2e_mcp_tools.py
└── conftest.py
```

**Assessment:** ⚠️ Good but could improve separation

**Recommendations:**
- Consider subdirectories: tests/unit/, tests/integration/, tests/e2e/
- Would make test organization clearer for new contributors

### Documentation (docs/)

**Current Structure:**
```
docs/
├── guides/
│   ├── CONTRIBUTING.md
│   ├── TESTING.md
│   └── INTEGRATION_TESTING.md
├── reference/
│   ├── ARCHITECTURE.md
│   ├── API_REFERENCE.md
│   ├── CODE_QUALITY.md
│   └── APPLESCRIPT_GOTCHAS.md
├── project/
│   └── ROADMAP.md
├── migration/
│   └── MIGRATION_v0.6.0.md
└── archive/
    └── [old docs]
```

**Assessment:** ✅ Excellent organization by doc type

**Recommendations:**
- None - structure is clear and intuitive

### Scripts (scripts/)

**Current Structure:**
```
scripts/
├── check_complexity.sh
├── check_code_quality.sh
├── check_test_coverage.sh
├── check_roadmap_sync.sh
├── hooks/
│   ├── pre_bash.sh
│   ├── post_bash.sh
│   └── session_start.sh
└── git-hooks/
    ├── pre-commit
    └── pre-tag
```

**Assessment:** ⚠️ Good but lacks documentation

**Recommendations:**
- Add scripts/README.md explaining purpose of each script
- Consider grouping: checks/, hooks/, utilities/

### Configuration (.claude/)

**Current Structure:**
```
.claude/
├── CLAUDE.md
├── settings.json
├── commands/
│   ├── doc-quality.md
│   ├── code-quality.md
│   ├── test-coverage.md
│   └── directory-check.md
└── mistakes/
    └── [archived mistakes]
```

**Assessment:** ✅ Good organization of AI assistant config

**Recommendations:**
- None - structure is clear

### GitHub Config (.github/)

**Current Structure:**
```
.github/
└── workflows/
    └── release-hygiene.yml
```

**Assessment:** ✅ Clean GitHub Actions setup

**Recommendations:**
- None - appropriate for current needs

---

## File Organization Analysis

### Orphaned or Misplaced Files

**Found:** X files in unusual locations

**Examples:**
- None found ✅

**If any found:**
- file.py in root (should be in src/)
- config.json in docs/ (should be in root or .github/)

### Naming Consistency

**Assessment:** [EXCELLENT | GOOD | INCONSISTENT]

**Examples of Good Naming:**
- test_*.py pattern for all test files
- check_*.sh pattern for hygiene check scripts
- Consistent use of snake_case for Python files
- Consistent use of UPPERCASE for markdown docs

**Examples of Inconsistency (if any):**
- None found ✅

### Nesting Depth

**Assessment:** ✅ Appropriate nesting depth (max 3-4 levels)

**Deepest Nests:**
- src/omnifocus_mcp/ (2 levels) - appropriate
- docs/guides/ (2 levels) - appropriate
- scripts/hooks/ (2 levels) - appropriate

**No excessive nesting found.**

---

## Documentation Organization Assessment

### Findability

**Can new contributors quickly find:**
- ✅ Contribution guidelines? (docs/guides/CONTRIBUTING.md)
- ✅ Testing instructions? (docs/guides/TESTING.md)
- ✅ API reference? (docs/reference/API_REFERENCE.md)
- ✅ Architecture docs? (docs/reference/ARCHITECTURE.md)
- ✅ Project roadmap? (docs/project/ROADMAP.md)

**Overall Findability:** [EXCELLENT | GOOD | POOR]

### Separation of Concerns

**User-facing docs:**
- README.md (overview, quick start)
- docs/guides/ (how-to guides)
- docs/reference/API_REFERENCE.md (function docs)

**Developer docs:**
- docs/guides/CONTRIBUTING.md (workflow)
- docs/guides/TESTING.md (test procedures)
- docs/reference/ARCHITECTURE.md (design decisions)
- docs/reference/CODE_QUALITY.md (standards)

**Assessment:** ✅ Clear separation between user and developer docs

### Documentation Types

**Available:**
- ✅ Getting started (README.md)
- ✅ How-to guides (docs/guides/)
- ✅ Reference material (docs/reference/)
- ✅ Project planning (docs/project/)
- ✅ Migration guides (docs/migration/)

**Missing:**
- ⚠️ Troubleshooting guide (could add docs/guides/TROUBLESHOOTING.md)
- ⚠️ FAQ (could add docs/guides/FAQ.md)

---

## Archive Organization Assessment

### Archive Directory

**Location:** docs/archive/

**Contents:**
- Old implementation plans
- Outdated documentation
- Historical decisions

**Assessment:** ✅ Good separation of archived content

**Recommendations:**
- Consider adding docs/archive/README.md explaining what's archived and why
- Date-stamp archived files (e.g., PLANNING_2025-10-15.md)

### Files That Should Be Archived

**Found:** X files that might be candidates for archiving

**Examples:**
- None currently - active docs are all relevant ✅

**If any found:**
- .claude/v0.6.3-implementation-plan.md (implementation complete, archive?)
- docs/VALIDATION_SPRINT_COMPLETE.md (temporary marker, archive?)

---

## Configuration File Analysis

### Root Config Files

**Found:**
- pyproject.toml (Python project metadata)
- requirements.txt (dependencies)
- VERSION (version tracking)

**Assessment:** ✅ Appropriate root configs

**Duplicates or Obsolete:**
- None found ✅

### Tool-Specific Configs

**.claude/ (AI assistant):**
- settings.json (hook configuration)
- CLAUDE.md (project memory)
- commands/ (slash commands)

**Assessment:** ✅ Well-organized AI tooling

**.github/ (GitHub Actions):**
- workflows/release-hygiene.yml (CI workflow)

**Assessment:** ✅ Minimal and focused CI config

**Recommendations:**
- None - configs are appropriately placed and organized

---

## New Contributor Experience

### Quick Start Path

**Can a new contributor find:**
1. ✅ What the project does? (README.md)
2. ✅ How to install? (README.md)
3. ✅ How to contribute? (docs/guides/CONTRIBUTING.md)
4. ✅ How to run tests? (docs/guides/TESTING.md)
5. ✅ Project architecture? (docs/reference/ARCHITECTURE.md)

**Assessment:** ✅ Clear path from README to detailed docs

### Directory Understanding

**Is it obvious what each directory contains?**
- ✅ src/ - source code
- ✅ tests/ - test files
- ✅ docs/ - documentation
- ✅ scripts/ - utility scripts
- ⚠️ .claude/ - might not be obvious (Claude Code config)
- ✅ .github/ - GitHub configuration

**Recommendations:**
- Consider adding brief directory guide to README.md
- Add scripts/README.md explaining script purposes

### Common Task Clarity

**Can new contributors easily find how to:**
- ✅ Add a new API function? (docs/guides/CONTRIBUTING.md)
- ✅ Run tests? (docs/guides/TESTING.md)
- ✅ Check code quality? (docs/guides/CONTRIBUTING.md)
- ⚠️ Understand slash commands? (.claude/CLAUDE.md - not obvious from README)

**Recommendations:**
- Link to .claude/CLAUDE.md from README for AI-assisted development

---

## Directory Purpose Documentation

### Directories with READMEs

**Current:**
- Root: README.md ✅
- scripts/: No README ⚠️
- docs/: No README (not needed, structure is clear) ✅

**Recommended:**
- Add scripts/README.md with:
  - Purpose of each hygiene check script
  - When to run each script
  - How scripts are used in CI/git hooks

### Missing Directory Documentation

**Would benefit from README:**
1. scripts/ - Explain purpose of each script
2. .claude/ - Explain Claude Code integration (or link from main README)

**Low priority:**
- docs/archive/ - Explain archiving policy

---

## Maintenance Burden Assessment

### Current Burden

**Low Maintenance Areas:**
- ✅ src/ - stable structure, unlikely to need reorganization
- ✅ docs/ - clear organization, easy to add new docs
- ✅ tests/ - straightforward structure

**Medium Maintenance Areas:**
- ⚠️ scripts/ - growing number of scripts, might need grouping eventually
- ⚠️ .claude/commands/ - adding more commands, structure is fine

**High Maintenance Areas:**
- None identified ✅

### Growth Considerations

**If project grows, consider:**
- Splitting scripts/ into subdirectories (checks/, hooks/, utilities/)
- Adding tests/unit/, tests/integration/, tests/e2e/ subdirectories
- Creating docs/examples/ for usage examples

---

## Comparison with Python Project Conventions

### Standard Conventions

**Following:**
- ✅ src/ layout (not flat layout)
- ✅ tests/ directory separate from src/
- ✅ pyproject.toml for project metadata
- ✅ requirements.txt for dependencies
- ✅ README.md in root
- ✅ LICENSE in root
- ✅ CHANGELOG.md in root

**Not Following (with justification):**
- docs/ instead of docs/ (actually following convention ✅)
- VERSION file in root (non-standard but works for this project)

**Assessment:** ✅ Excellent adherence to Python conventions

---

## Suggestions for Future Enhancement

1. **Add scripts/README.md** - Document purpose of each script for new contributors
2. **Consider test subdirectories** - tests/unit/, tests/integration/, tests/e2e/ for clarity
3. **Add troubleshooting guide** - docs/guides/TROUBLESHOOTING.md for common issues
4. **Link AI tooling in README** - Mention .claude/ directory for AI-assisted development
5. **Date-stamp archived files** - Add dates to filenames in docs/archive/

---

## Conclusion

[Final assessment paragraph - is directory organization acceptable? What needs attention?]

**Overall Organization:** [EXCELLENT | GOOD | ACCEPTABLE | NEEDS WORK]
**Recommendation:** [READY FOR RELEASE | MINOR IMPROVEMENTS SUGGESTED | NEEDS RESTRUCTURING]

**Critical Issues:** [None | List issues that block release]
**High-Priority Improvements:** [None | List top 3 improvements]
**Estimated Effort:** [X hours to address high-priority items]
```

**Important:**
- Focus on actionable feedback with specific directory/file paths
- Use severity levels (Critical/Recommended/Minor)
- Provide concrete examples of organizational issues
- Be honest about clarity for new contributors
- Compare against Python project conventions
- Consider maintenance burden as project grows
- Assess whether structure facilitates finding information

**Agent task:**

```
Analyze the directory organization for the OmniFocus MCP Server project.

Step 1: Survey directory structure
Use tree command or ls to understand directory hierarchy.
List all directories and their purposes.

Step 2: Analyze file placement
Check if files are in appropriate directories.
Identify orphaned or misplaced files.

Step 3: Assess documentation organization
Evaluate docs/ structure.
Check if docs are easy to find and well-categorized.

Step 4: Check archive organization
Review docs/archive/ contents.
Identify files that should be archived.

Step 5: Evaluate configuration files
Check placement of config files (root, .github/, .claude/).
Identify duplicates or obsolete configs.

Step 6: Assess new contributor clarity
Can new contributors quickly understand structure?
Are key files easy to locate?
Would directory READMEs help?

Step 7: Compare with conventions
Compare structure against Python project conventions.
Identify deviations and their justifications.

Step 8: Generate report
Generate a detailed organization report using the template above. Focus on actionable recommendations for improving findability and clarity. Assess maintenance burden as project grows.

Note: This is a qualitative assessment focused on organization, not file contents.
```
