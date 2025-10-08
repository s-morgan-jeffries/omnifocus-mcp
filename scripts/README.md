# Scripts

Utility scripts for maintaining the OmniFocus MCP server.

## analyze_tool_docs.py

**Purpose**: Analyze MCP tool documentation quality for Claude Desktop

**Usage**:
```bash
python3 scripts/analyze_tool_docs.py
```

**When to use**:
- After adding new MCP tools
- When updating tool descriptions
- To verify documentation consistency
- To identify potentially ambiguous tools

**Output**:
- Tool count and categorization
- Returns section coverage
- Short description warnings
- Potential confusion points
- Recommendations for improvements

**Example**:
```
📊 Total tools: 38
✓ Tools with Returns section: 38 (100%)
⚠️  POTENTIAL CLAUDE DESKTOP CONFUSION POINTS
...
```
