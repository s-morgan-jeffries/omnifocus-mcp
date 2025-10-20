# Reference Documentation

Technical reference materials for the OmniFocus MCP Server project.

## Quick Navigation

**New contributors start here:**
1. [ARCHITECTURE.md](#architecturemd) - Design principles and decision-making framework
2. [API_REFERENCE.md](#api_referencemd) - Complete API documentation
3. [CODE_QUALITY.md](#code_qualitymd) - Complexity metrics and quality standards

**When implementing:**
- Check [ARCHITECTURE.md](#architecturemd) for design patterns
- Refer to [API_REFERENCE.md](#api_referencemd) for function signatures
- Run complexity checks per [CODE_QUALITY.md](#code_qualitymd)

**When debugging AppleScript:**
- See [APPLESCRIPT_GOTCHAS.md](#applescript_gotchasmd) for common issues
- Consult [omnifocus-4.8.4-documentation.html](#omnifocus-484-documentationhtml) for OmniFocus properties

---

## Documents

### ARCHITECTURE.md

**Purpose:** Design principles, decision-making framework, and API patterns

**When to use:**
- ✅ Before adding any new function (use the decision tree)
- ✅ When unsure if existing functions can handle a use case
- ✅ To understand why the API is designed this way
- ✅ When reviewing code (check for anti-patterns)

**Key sections:**
- **Decision Tree** - 3-question framework for evaluating new features
- **Anti-Patterns** - What NOT to do (field-specific setters, specialized filters, etc.)
- **CRUD Patterns** - Templates for create/read/update/delete operations
- **Worked Examples** - Real decision-making scenarios with rationale

**Size:** ~12KB - Comprehensive but focused on daily decision-making

**Related:** See `.claude/CLAUDE.md` for project-wide guidelines

### API_REFERENCE.md

**Purpose:** Complete API documentation for all 16 MCP tools

**When to use:**
- ✅ To see exact function signatures and parameters
- ✅ To understand return formats
- ✅ To find migration paths from deprecated functions
- ✅ When writing client code that calls the MCP server

**Structure:**
- **Current API** (v0.6.0) - 16 core functions with full documentation
- **Function Groups** - Projects (5), Tasks (6), Folders (2), Tags (1), Perspectives (2)
- **Each function includes:**
  - Complete signature with all parameters
  - Return format with examples
  - Usage notes and edge cases
  - Related functions

**Size:** ~47KB - Comprehensive API documentation

**Note:** For usage examples, see `docs/project/ROADMAP.md` "What v0.6.0 Already Handles" section

### CODE_QUALITY.md

**Purpose:** Complexity metrics, Radon guidelines, and quality thresholds

**When to use:**
- ✅ Before committing code (run `./scripts/check_complexity.sh`)
- ✅ When refactoring complex functions
- ✅ To understand why certain functions have high complexity ratings
- ✅ When deciding if complexity is acceptable or needs refactoring

**Key sections:**
- **Complexity Thresholds** - A-B (1-10), C (11-20), D-F (21+)
- **Intentionally Complex Functions** - Documented exceptions with rationale
- **Radon Configuration** - Tool settings and interpretation

**Documented Complex Functions:**
- `get_tasks()` - F (CC 66) - 21 parameters, comprehensive filtering
- `update_task()` - D (CC 27) - 10+ optional properties
- `get_projects()` - D (CC 23) - Comprehensive property extraction

**Target for new code:** A-B rating (CC 1-10)

**Size:** ~7KB - Focused on complexity management

### APPLESCRIPT_GOTCHAS.md

**Purpose:** Common AppleScript issues, workarounds, and limitations

**When to use:**
- ✅ When debugging AppleScript errors
- ✅ Before implementing new OmniFocus operations
- ✅ When tests pass but real OmniFocus behavior is wrong
- ✅ Understanding why certain features can't be implemented

**Key sections:**
- **Rich Text Notes** - Can't read formatted text (OmniFocus API limitation)
- **Variable Naming** - Don't use OmniFocus property names as variable names
- **Recurring Tasks** - Use `mark complete` instead of setting `completed` property
- **Performance Notes** - Large database handling and timeout guidelines

**Size:** ~6KB - Focused on practical issues

**Example gotchas:**
- Variables named `recurrence` or `repetitionMethod` conflict with OmniFocus properties
- Can only access plain text notes via AppleScript (no formatting)
- Direct property setting fails for recurring tasks

### omnifocus-4.8.4-documentation.html

**Purpose:** Official OmniFocus 4.8.4 AppleScript dictionary (exported HTML)

**When to use:**
- ✅ Finding exact property names in OmniFocus
- ✅ Understanding available AppleScript commands
- ✅ Checking property types and valid values
- ✅ Research when implementing new features

**Size:** ~960KB - Complete OmniFocus AppleScript reference

**Note:** This is the authoritative source for OmniFocus properties and commands. Use [APPLESCRIPT_GOTCHAS.md](#applescript_gotchasmd) for practical implementation guidance.

**How to access:** Open in web browser for searchable, formatted documentation

---

## How These Documents Work Together

### Adding a New Feature

1. **Check ARCHITECTURE.md decision tree** - Can existing functions handle this?
2. **If yes:** Update API_REFERENCE.md with new parameters/usage
3. **If no:** Follow CRUD patterns from ARCHITECTURE.md
4. **During implementation:** Refer to APPLESCRIPT_GOTCHAS.md for known issues
5. **After implementation:** Run complexity check per CODE_QUALITY.md

### Debugging Issues

1. **Start with APPLESCRIPT_GOTCHAS.md** - Is this a known issue?
2. **Check omnifocus-4.8.4-documentation.html** - Verify property names/types
3. **Review API_REFERENCE.md** - Confirm expected behavior
4. **Consult ARCHITECTURE.md** - Is the approach aligned with design principles?

### Code Review

1. **ARCHITECTURE.md** - Check for anti-patterns
2. **CODE_QUALITY.md** - Run complexity analysis
3. **API_REFERENCE.md** - Verify consistency with existing API
4. **APPLESCRIPT_GOTCHAS.md** - Ensure workarounds are applied

---

## Document Maintenance

### When to Update

**ARCHITECTURE.md:**
- Add new patterns discovered during implementation
- Document new anti-patterns
- Add worked examples for complex decisions

**API_REFERENCE.md:**
- When function signatures change
- When adding new functions
- When updating return formats
- When deprecating functions

**CODE_QUALITY.md:**
- When adding intentionally complex functions
- When refactoring reduces complexity
- When changing complexity thresholds

**APPLESCRIPT_GOTCHAS.md:**
- When discovering new AppleScript issues
- When finding workarounds
- When OmniFocus updates change behavior

**omnifocus-4.8.4-documentation.html:**
- When upgrading to new OmniFocus major version
- Export from AppleScript Editor: File > Export > HTML

---

## See Also

- **Project Guidelines:** `../../.claude/CLAUDE.md` - TDD requirements, workflow, project memory
- **Testing Strategy:** `../guides/TESTING.md` - Test coverage, procedures, running tests
- **Contributing:** `../guides/CONTRIBUTING.md` - Development workflow, pre-commit checklist
- **Roadmap:** `../project/ROADMAP.md` - Current state, future work, what v0.6.0 handles

---

**Last Updated:** October 20, 2025
