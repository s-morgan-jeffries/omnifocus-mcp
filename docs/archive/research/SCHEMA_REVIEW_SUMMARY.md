# Schema Review Summary - Quick Reference

## Critical Issues Found

### 1. No Output Schemas (High Priority)
- **Problem**: Tools don't define what they return
- **Impact**: Clients can't validate responses, no structured data support
- **Fix**: Add `outputSchema` to all tools + return `structured_data`
- **MCP 2025 Best Practice**: Output schemas are standard since 2025-06-18 spec

### 2. Missing OmniFocus Data (High Priority)
Current tools only expose ~30% of available OmniFocus data:

**Missing from Projects:**
- Dates (due, defer, completion, review)
- Task counts
- Tags/contexts
- Sequential/parallel mode
- Flagged status
- Creation/modification dates

**Missing from Tasks:**
- Can't retrieve tasks at all
- Can't set due dates when creating
- Can't set tags/contexts
- Can't set flags

### 3. Inconsistent Error Handling (Medium Priority)
- **Problem**: Generic failure messages, no error codes
- **Impact**: Hard to debug, poor user experience
- **Fix**: Standardized error structure with codes + suggestions

### 4. Limited Filtering (Medium Priority)
- **Problem**: `get_projects` has no filters, returns everything
- **Impact**: Inefficient for large databases
- **Fix**: Add status, folder, limit, sort parameters

---

## Quick Wins (Implement First)

### Phase 1: Add Structured Output (Non-Breaking)
```python
# Add to each tool
outputSchema={
    "type": "object",
    "properties": {
        # Define response structure
    }
}

# Return both text + structured data
return [TextContent(
    type="text",
    text="Human readable...",
    structured_data={
        "projects": [...],
        "count": 3
    }
)]
```

### Phase 2: Enhance Existing Tools (Non-Breaking)
```python
# Add optional parameters to get_projects
inputSchema={
    "properties": {
        "status": {"type": "string", "default": "active"},
        "folder_path": {"type": "string"},
        "limit": {"type": "integer"},
        # ... more filters
    },
    "required": []  # Keep existing behavior
}
```

### Phase 3: Better Errors (Non-Breaking)
```python
structured_data={
    "error": {
        "code": "PROJECT_NOT_FOUND",
        "message": "Project 'xyz' not found",
        "suggestions": [
            "Use get_projects to list available projects",
            "Check that OmniFocus is running"
        ]
    }
}
```

---

## Current vs Improved Schema Comparison

### Example: `get_projects` Tool

#### Current Response (Text Only)
```
Found 3 active projects:

**Project A**
ID: proj-001
Folder: Work
Status: active
Note: Some text...
```

#### Improved Response (Text + Structured)
```json
{
    "text": "Found 3 active projects...",
    "structured_data": {
        "projects": [
            {
                "id": "proj-001",
                "name": "Project A",
                "status": "active",
                "folder_path": "Work > Clients",
                "dates": {
                    "due": "2025-10-15T17:00:00Z",
                    "defer": null,
                    "next_review": "2025-10-10T09:00:00Z"
                },
                "task_counts": {
                    "total": 12,
                    "completed": 8,
                    "available": 3,
                    "remaining": 4
                },
                "flags": {
                    "flagged": true,
                    "sequential": false,
                    "completed": false
                },
                "tags": ["client", "urgent"]
            }
        ],
        "count": 3,
        "filters_applied": {
            "status": "active",
            "folder_path": "Work"
        }
    }
}
```

---

## New Tools Needed

Based on OmniFocus capabilities:

1. **`get_tasks`** - Retrieve tasks with filters (CRITICAL)
2. **`update_project`** - Modify project properties
3. **`complete_task`** - Mark tasks complete
4. **`update_task`** - Modify task properties
5. **`get_contexts`** - List available tags/contexts
6. **`create_project`** - Create new projects

---

## MCP Best Practices Checklist

Current compliance:

- [ ] Output schemas defined
- [x] Input schemas defined
- [ ] Structured data in responses
- [x] Text responses (backward compatibility)
- [ ] Consistent error codes
- [ ] Error suggestions provided
- [x] Clear tool descriptions
- [ ] Complete documentation
- [ ] Field-level examples
- [ ] Validation helpers
- [ ] Filtering options
- [ ] Sorting options
- [ ] Pagination/limits

Score: **4/13** → Target: **13/13**

---

## Implementation Priority

### Must Have (Priority 1) - Week 1
- [ ] Add output schemas to all 4 tools
- [ ] Return structured_data in all responses
- [ ] Add error codes and standardized error structure
- [ ] Update tests for structured data

### Should Have (Priority 2) - Week 2-3
- [ ] Enhance `get_projects` with filters, dates, tags, counts
- [ ] Enhance `add_task` with dates, tags, flags
- [ ] Update AppleScript to capture more data
- [ ] Add validation helpers

### Nice to Have (Priority 3) - Week 4+
- [ ] Add `get_tasks` tool
- [ ] Add `update_project` tool
- [ ] Add `complete_task` tool
- [ ] Add more advanced tools

---

## Backward Compatibility

All changes are **backward compatible**:

✅ Existing clients continue working unchanged
✅ Same tool names
✅ Same required parameters
✅ Text responses maintained
✅ New features are optional parameters

Migration is **opt-in**:
- Old clients: Keep using text responses
- New clients: Use structured_data

---

## Code Changes Summary

### Files to Modify
1. `server.py` - Add schemas, structured responses, error handling
2. `omnifocus_client.py` - Enhanced data retrieval, validation
3. `test_*.py` - Update for structured data
4. New: `error_codes.py` - Error constants and helpers

### Lines of Code Impact
- `server.py`: ~300 lines (schemas + structured responses)
- `omnifocus_client.py`: ~500 lines (enhanced AppleScript)
- `error_codes.py`: ~100 lines (new file)
- Tests: ~200 lines (validation tests)

**Total:** ~1,100 lines (mostly schema definitions)

---

## Risks and Mitigations

### Risk: Breaking Existing Clients
**Mitigation**: All changes are additive, maintain text responses

### Risk: AppleScript Complexity
**Mitigation**: Incremental updates, comprehensive tests

### Risk: Performance Impact
**Mitigation**: Make enhanced data optional (include_tasks parameter)

### Risk: Date Format Compatibility
**Mitigation**: Use ISO 8601 standard, provide examples

---

## Success Metrics

After implementation:

1. **Schema Completeness**: 100% of OmniFocus data exposed
2. **Client Adoption**: Structured data usage in new integrations
3. **Error Rate**: Reduction in error reports due to better messages
4. **Performance**: No regression with enhanced data
5. **Test Coverage**: Maintain >95% coverage
6. **Documentation**: Complete examples for all tools

---

## Next Steps

1. **Review** this document + full SCHEMA_REVIEW.md
2. **Prioritize** implementation phases
3. **Design** detailed API for Phase 1
4. **Implement** output schemas + structured data
5. **Test** with existing clients (compatibility)
6. **Document** migration guide
7. **Release** v2.0 with enhanced schemas

---

## Resources

- Full review: [SCHEMA_REVIEW.md](./SCHEMA_REVIEW.md)
- MCP Spec: https://modelcontextprotocol.io/specification/2025-06-18
- OmniFocus AppleScript: https://inside.omnifocus.com/applescript
- Python SDK: https://github.com/modelcontextprotocol/python-sdk

---

**Document Version:** 1.0
**Date:** October 7, 2025
**Status:** Ready for Implementation Planning
