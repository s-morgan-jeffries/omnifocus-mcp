# MCP Tool Documentation Audit for Claude Desktop

**Date**: 2025-10-08
**Total Tools**: 38
**Status**: ⚠️ Needs Improvement

## Executive Summary

With 38 tools exposed to Claude Desktop, documentation quality directly impacts Claude's ability to select the correct tool. This audit identifies areas where ambiguity or missing information could cause Claude to choose the wrong tool.

## Key Findings

### ✅ Strengths
- **86% of tools document parameters** in Args section
- **All tools have descriptions** (no missing docstrings)
- **Clear categorization** emerges from naming patterns

### ⚠️ Critical Issues

1. **Only 5% document Returns** (2/38 tools)
   - Claude can't predict output format
   - May re-call tool expecting different format

2. **12 tools start with "get_"**
   - High potential for confusion without clear differentiation
   - Similar names need distinct first-line descriptions

3. **Short descriptions** (3 tools <30 chars)
   - `set_project_status`: "Set the status of a project."
   - `get_tags`: "Get all tags from OmniFocus."
   - `delete_task`: "Delete a task from OmniFocus."

## Tool Categories

| Category | Count | Notes |
|----------|-------|-------|
| Project Management | 10 | Includes new Phase 7 tools |
| Task Management | 19 | Largest category - needs clear differentiation |
| Tag Management | 1 | Simple, clear |
| Folder Management | 2 | Simple, clear |
| Note Management | 2 | Simple, clear |
| Batch Operations | Embedded in above | Not explicitly separated |
| Review | 1 | Simple, clear |
| Other | 3 | Perspectives and estimates |

## Specific Ambiguity Risks

### High Risk: get_projects vs search_projects

**Current state:**
```
get_projects: "Get all active projects from OmniFocus with their folder hierarchy, names, notes, and status."
search_projects: "Search OmniFocus projects by name, note content, or folder path."
```

**Risk**: Claude might use search_projects when user wants all projects, or vice versa.

**Recommendation**: Make distinction explicit in first line:
```
get_projects: "Retrieve ALL active projects with full details and hierarchy (no filtering)"
search_projects: "Find specific projects by searching name, note, or folder path"
```

### Medium Risk: Batch operations

**Current state**: Many tools have both singular and plural forms:
- `complete_task` / `complete_tasks`
- `delete_task` / `delete_tasks`
- `move_task` / `move_tasks`
- `add_tag_to_task` / `add_tag_to_tasks`
- `drop_task` / `drop_tasks`

**Risk**: Claude might use singular form in loop instead of batch operation.

**Recommendation**: Emphasize performance benefit in plural versions:
```
complete_tasks: "Mark multiple tasks complete in one operation (more efficient than calling complete_task repeatedly)"
```

### Low Risk: Specialized getters

Tools like `get_projects_due_for_review` and `get_stalled_projects` are clearly named and won't be confused with general `get_projects`.

## Recommendations by Priority

### Priority 1: Add Returns Documentation

**Impact**: High - affects all tool calls
**Effort**: Low - simple docstring updates

Add Returns section to all 36 tools missing it. Format:
```python
Returns:
    Formatted text with project list (one per line with ID and name)
```

or

```python
Returns:
    Success message confirming the operation completed
```

### Priority 2: Enhance Short Descriptions

**Impact**: Medium - affects tool selection
**Effort**: Low - 3 tools need updating

Update these 3 tools to be more descriptive (40-80 chars):
- `set_project_status` → "Change a project's status to active, on hold, or done"
- `get_tags` → "Retrieve all available tags from OmniFocus with their names"
- `delete_task` → "Permanently remove a task from OmniFocus (cannot be undone)"

### Priority 3: Clarify get_* vs search_* Pattern

**Impact**: Medium - affects common operations
**Effort**: Low - update 2 tool descriptions

Clearly differentiate retrieval modes:
- `get_*`: Retrieve all/specific items (with optional filters)
- `search_*`: Find items matching search criteria

### Priority 4: Emphasize Batch Operation Benefits

**Impact**: Low - optimization more than correctness
**Effort**: Low - update 6-8 tool descriptions

Add performance note to plural tool descriptions.

## Testing Tool Selection

We currently don't have automated tests for "does Claude Desktop pick the right tool?" but we could create a test suite:

```python
# Example test cases
test_cases = [
    {
        "user_request": "Show me all my projects",
        "expected_tool": "get_projects",
        "should_not_use": ["search_projects"]
    },
    {
        "user_request": "Find projects with 'website' in the name",
        "expected_tool": "search_projects",
        "should_not_use": ["get_projects"]
    },
    {
        "user_request": "Complete these 5 tasks: task-1, task-2, ...",
        "expected_tool": "complete_tasks",
        "should_not_use": ["complete_task"]
    }
]
```

This would require real MCP client testing or LLM-based evaluation.

## Comparison to MCP Best Practices

According to MCP documentation, good tool descriptions should:

1. ✅ Be concise (most of ours are)
2. ⚠️ Clearly state what they return (only 5% do)
3. ✅ Document all parameters (86% do)
4. ⚠️ Disambiguate similar tools (needs improvement)
5. ✅ Use consistent naming patterns (we do: verb_noun)

## Next Steps

1. [ ] Add Returns documentation to all 36 tools
2. [ ] Enhance 3 short descriptions
3. [ ] Update get_projects and search_projects for clarity
4. [ ] Add performance notes to batch operations
5. [ ] Consider creating tool selection test suite
6. [ ] Review Phase 7 tools specifically for clarity

## Appendix: Tool Selection Criteria

How Claude Desktop likely chooses tools:

1. **First-line description match** to user intent
2. **Parameter availability** (can Claude provide the needed params?)
3. **Return type expectations** (does it return what's needed next?)
4. **Context from conversation** (what was just discussed?)

Our improvements target #1 and #3 most directly.
