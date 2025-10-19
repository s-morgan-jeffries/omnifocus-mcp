#!/usr/bin/env python3
"""Analyze MCP tool documentation quality for Claude Desktop discovery."""

import re


def extract_tools_from_file(filepath):
    """Parse server file to extract tool definitions."""
    with open(filepath, 'r') as f:
        content = f.read()

    tools = []

    # Find all @mcp.tool() decorated functions
    pattern = r'@mcp\.tool\(\)\s+def\s+(\w+)\s*\((.*?)\)\s*->\s*str:\s+"""(.*?)"""'

    for match in re.finditer(pattern, content, re.DOTALL):
        func_name = match.group(1)
        params_str = match.group(2)
        docstring = match.group(3)

        # Parse parameters
        params = []
        if params_str.strip():
            for param in params_str.split(','):
                param = param.strip()
                if param and param != 'self':
                    param_name = param.split(':')[0].strip()
                    params.append(param_name)

        # Parse docstring
        lines = docstring.strip().split('\n')
        description = lines[0].strip() if lines else ""

        # Find Args section
        args_section = []
        returns_section = []
        in_args = False
        in_returns = False

        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith('Args:'):
                in_args = True
                in_returns = False
                continue
            elif stripped.startswith('Returns'):
                in_returns = True
                in_args = False
                continue
            elif stripped and not line.startswith(' '):
                in_args = False
                in_returns = False

            if in_args and stripped:
                args_section.append(stripped)
            elif in_returns and stripped:
                returns_section.append(stripped)

        tools.append({
            'name': func_name,
            'description': description,
            'parameters': params,
            'param_count': len(params),
            'has_args_section': bool(args_section),
            'has_returns_section': bool(returns_section),
            'args_documented': len(args_section),
            'docstring_length': len(description)
        })

    return tools


def categorize_tools(tools):
    """Group tools by category based on name patterns."""
    categories = {
        'Project Management': [],
        'Task Management': [],
        'Tag Management': [],
        'Folder Management': [],
        'Note Management': [],
        'Batch Operations': [],
        'Inbox Operations': [],
        'Review': [],
        'Other': []
    }

    for tool in tools:
        name = tool['name']
        if 'project' in name:
            categories['Project Management'].append(tool)
        elif 'task' in name and 'batch' not in name:
            categories['Task Management'].append(tool)
        elif 'tag' in name:
            categories['Tag Management'].append(tool)
        elif 'folder' in name:
            categories['Folder Management'].append(tool)
        elif 'note' in name:
            categories['Note Management'].append(tool)
        elif 'batch' in name or 'complete_tasks' in name or 'move_tasks' in name or 'delete_tasks' in name or 'delete_projects' in name:
            categories['Batch Operations'].append(tool)
        elif 'inbox' in name:
            categories['Inbox Operations'].append(tool)
        elif 'review' in name:
            categories['Review'].append(tool)
        else:
            categories['Other'].append(tool)

    return categories


def find_similar_tools(tools):
    """Find tools that might be confusing due to similar names or purposes."""
    similar_groups = []

    # Check for similar prefixes
    get_tools = [t for t in tools if t['name'].startswith('get_')]
    search_tools = [t for t in tools if 'search' in t['name']]

    if get_tools:
        similar_groups.append(('get_* tools', get_tools))
    if search_tools:
        similar_groups.append(('search_* tools', search_tools))

    # Check for task operations
    task_ops = [t for t in tools if 'task' in t['name'] and not t['name'].startswith('get_')]
    if len(task_ops) > 3:
        similar_groups.append(('task operations', task_ops))

    return similar_groups


def print_analysis(tools):
    """Print comprehensive analysis of tool documentation."""

    print("=" * 80)
    print("MCP TOOL DOCUMENTATION ANALYSIS FOR CLAUDE DESKTOP")
    print("=" * 80)
    print()

    # Overall stats
    print(f"📊 Total tools: {len(tools)}")
    print(f"✓ Tools with Args section: {sum(1 for t in tools if t['has_args_section'])} ({sum(1 for t in tools if t['has_args_section'])*100//len(tools)}%)")
    print(f"✓ Tools with Returns section: {sum(1 for t in tools if t['has_returns_section'])} ({sum(1 for t in tools if t['has_returns_section'])*100//len(tools)}%)")
    print()

    # Categorize
    categories = categorize_tools(tools)

    print("📁 TOOLS BY CATEGORY")
    print("=" * 80)
    for category, category_tools in categories.items():
        if category_tools:
            print(f"\n{category} ({len(category_tools)} tools):")
            for tool in sorted(category_tools, key=lambda t: t['name']):
                desc_preview = tool['description'][:70] + "..." if len(tool['description']) > 70 else tool['description']
                param_info = f"{tool['param_count']} params" if tool['param_count'] > 0 else "no params"
                print(f"  • {tool['name']:<30} {param_info:<12} - {desc_preview}")

    print()
    print()
    print("⚠️  POTENTIAL CLAUDE DESKTOP CONFUSION POINTS")
    print("=" * 80)

    # Find similar tool groups
    similar_groups = find_similar_tools(tools)

    for group_name, group_tools in similar_groups:
        print(f"\n{group_name} ({len(group_tools)} tools):")
        print("  Claude might struggle to choose between:")
        for tool in sorted(group_tools, key=lambda t: t['name']):
            print(f"    - {tool['name']}: {tool['description'][:60]}")

    # Check description quality
    print("\n\n📝 DESCRIPTION QUALITY ISSUES")
    print("-" * 80)
    short_desc = [t for t in tools if t['docstring_length'] < 30]
    if short_desc:
        print("Tools with very short descriptions (<30 chars):")
        for tool in short_desc:
            print(f"  ⚠️  {tool['name']}: \"{tool['description']}\"")
    else:
        print("✓ All tools have adequate description length")

    # Check parameter documentation
    print("\n\n📋 PARAMETER DOCUMENTATION")
    print("-" * 80)
    underdoc = [t for t in tools if t['param_count'] > 0 and t['args_documented'] == 0]
    if underdoc:
        print("Tools with undocumented parameters:")
        for tool in underdoc:
            print(f"  ⚠️  {tool['name']}: {tool['param_count']} params, 0 documented")
    else:
        print("✓ All tools document their parameters")

    print()
    print()
    print("💡 RECOMMENDATIONS FOR CLAUDE DESKTOP CLARITY")
    print("=" * 80)
    print("""
1. TOOL NAMING & DISAMBIGUATION:
   • With 38 tools, clear naming is critical
   • Consider if get_tasks vs search_tasks is clear enough
   • Ensure similar tools have distinct first-line descriptions

2. DESCRIPTION BEST PRACTICES:
   • First line should be 40-80 chars
   • Start with action verb (Get/Create/Update/Delete/Search)
   • State the primary use case clearly
   • Example: "Get all tasks from a specific project with optional filters"

3. PARAMETER CLARITY:
   • Document all parameters in Args section
   • Specify if optional vs required
   • Include valid values/formats
   • State defaults clearly

4. RETURNS DOCUMENTATION:
   • Claude sees the return value, not just type signature
   • Specify format (formatted text, JSON list, success message)
   • Helps Claude know what to expect

5. GROUPING RELATED TOOLS:
   • Consider if we need all variations
   • Could batch operations be consolidated?
   • Are there redundant search/get patterns?
""")

    # Specific tool comparison analysis
    print("\n\n🔍 DETAILED COMPARISON: POTENTIALLY CONFUSING TOOLS")
    print("=" * 80)

    # Compare get_tasks vs search_tasks
    get_tasks = next((t for t in tools if t['name'] == 'get_tasks'), None)
    search_tasks = next((t for t in tools if t['name'] == 'search_tasks'), None)

    if get_tasks and search_tasks:
        print("\nget_tasks vs search_tasks:")
        print(f"  get_tasks:    {get_tasks['description']}")
        print(f"                Parameters: {', '.join(get_tasks['parameters'][:5])}...")
        print(f"  search_tasks: {search_tasks['description']}")
        print(f"                Parameters: {', '.join(search_tasks['parameters'][:5])}...")
        print("  Recommendation: Ensure descriptions clearly differentiate these")

    # Compare get_projects vs search_projects
    get_projects = next((t for t in tools if t['name'] == 'get_projects'), None)
    search_projects = next((t for t in tools if t['name'] == 'search_projects'), None)

    if get_projects and search_projects:
        print("\nget_projects vs search_projects:")
        print(f"  get_projects:    {get_projects['description']}")
        print(f"  search_projects: {search_projects['description']}")
        print("  Recommendation: Same pattern as tasks - clarify difference")


if __name__ == '__main__':
    tools = extract_tools_from_file('src/omnifocus_mcp/server_fastmcp.py')
    print_analysis(tools)
