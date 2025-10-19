# Migration Guide: v0.4.0 → v0.5.0

## Breaking Changes

Version 0.5.0 consolidates the MCP tool API by removing redundant wrapper functions in favor of more powerful unified tools.

### Removed Tools

#### 1. `search_projects()` → Use `get_projects(query=...)`

**Before (v0.4.0):**
```python
search_projects(query="budget")
```

**After (v0.5.0):**
```python
get_projects(query="budget")
```

**Benefits:**
- Can combine search with other filters: `get_projects(query="budget", status="active")`
- One less tool to choose from (reduces confusion)

---

#### 2. `get_inbox_tasks()` → Use `get_tasks(inbox_only=True)`

**Before (v0.4.0):**
```python
get_inbox_tasks()
```

**After (v0.5.0):**
```python
get_tasks(inbox_only=True)
```

**Benefits:**
- Can apply filters to inbox: `get_tasks(inbox_only=True, flagged_only=True)`
- Can search inbox: `get_tasks(inbox_only=True, query="urgent")`

---

## New Capabilities

### Enhanced `get_tasks()`

**New parameters:**
- `query: Optional[str]` - Search task names and notes (case-insensitive)
- `inbox_only: bool` - Only return inbox tasks

**Powerful combinations:**
```python
# Search with date filters
get_tasks(query="mortgage", due_relative="this_week")

# Complex inbox queries
get_tasks(inbox_only=True, query="urgent", flagged_only=True)

# Search overdue tasks
get_tasks(query="report", overdue=True)
```

### Enhanced `get_projects()`

**New parameter:**
- `query: Optional[str]` - Search project name, note, or folder path (case-insensitive)

**Examples:**
```python
# Search with status filter
get_projects(query="budget", status="active")

# Search on-hold projects
get_projects(query="review", on_hold_only=True)
```

---

## Migration Checklist

### For MCP Clients (Claude Desktop, etc.)

✅ **No action required** - Claude Desktop will automatically use the new consolidated API

The tool descriptions have been updated to guide Claude toward the correct usage:
- When asked to "search projects", Claude will use `get_projects(query=...)`
- When asked about "inbox tasks", Claude will use `get_tasks(inbox_only=True)`

### For Direct API Users (Python code)

If you're calling these functions directly in Python code:

1. **Search for usage:**
   ```bash
   grep -r "search_projects\|get_inbox_tasks" your_code/
   ```

2. **Update calls:**
   - Replace `client.search_projects("foo")` with `client.get_projects(query="foo")`
   - Replace `client.get_inbox_tasks()` with `client.get_tasks(inbox_only=True)`

3. **Update tests:**
   - Update any mock assertions to include new parameters:
     ```python
     # Before
     mock_client.get_tasks.assert_called_once_with(project_id="proj-001")

     # After
     mock_client.get_tasks.assert_called_once_with(
         project_id="proj-001",
         # ... other parameters ...
         query=None,
         inbox_only=False
     )
     ```

---

## Why This Change?

### Problem
With 38 tools, Claude Desktop had difficulty selecting the right tool:
- `get_tasks()` couldn't search by text
- `search_tasks()` existed but wasn't exposed (internal only)
- `get_inbox_tasks()` was a separate tool that duplicated get_tasks logic

When asked "do I have a mortgage payment due?", Claude would:
1. Call `get_tasks()` with no query → return thousands of tasks
2. Or fail to find tasks because search wasn't available

### Solution
Consolidate redundant wrappers into unified, powerful tools:
- **38 → 36 tools** (5% reduction)
- Enables complex queries: `get_tasks(query="mortgage", due_relative="this_week")`
- Clearer API: one tool with many options vs many overlapping tools

### Impact
- ✅ Better tool selection by Claude Desktop
- ✅ More powerful query combinations
- ✅ Simpler API surface
- ✅ All 393 tests updated and passing
- ⚠️ Breaking change (hence v0.5.0 bump)

---

## Next Version

For migration from v0.5.0 → v0.6.0 (major API redesign, 26 tools → 16 core functions), see [MIGRATION_v0.6.md](MIGRATION_v0.6.md).

**Note:** v0.6.0 represents a much larger consolidation than v0.5.0, introducing comprehensive `update_task()` and `update_project()` functions that replace many specialized operations.

---

## Need Help?

If you encounter issues migrating:
1. Check the [tool consolidation analysis](./tool-consolidation-analysis.md) for detailed reasoning
2. Review updated [README.md](../README.md) for usage examples
3. Open an issue on GitHub with your use case
