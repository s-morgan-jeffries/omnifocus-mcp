#!/bin/bash
# Check that all public client functions have corresponding MCP tools

CLIENT_FILE="src/omnifocus_mcp/omnifocus_client.py"
SERVER_FILE="src/omnifocus_mcp/server_fastmcp.py"

echo "Checking client/server parity..."
echo ""

# Extract public function names from client (exclude private/internal)
# Look for "def function_name(" but exclude "__init__", "_private", etc.
CLIENT_FUNCTIONS=$(grep -E "^    def [a-z][a-z_]*\(" "$CLIENT_FILE" | \
    grep -v "def _" | \
    sed 's/.*def \([a-z_]*\).*/\1/' | \
    sort | uniq)

# Extract tool function names from server
# Tools are decorated with @mcp.tool() and defined as "def function_name(" on the next line
SERVER_TOOLS=$(grep -A1 "@mcp.tool()" "$SERVER_FILE" | \
    grep "^def " | \
    sed 's/def \([a-z_]*\).*/\1/' | \
    sort | uniq)

# Find functions missing from server
MISSING=()
for func in $CLIENT_FUNCTIONS; do
    # Tool name might be exactly the same or have slight variations
    if ! echo "$SERVER_TOOLS" | grep -q "^${func}$"; then
        MISSING+=("$func")
    fi
done

# Display results
if [ ${#MISSING[@]} -eq 0 ]; then
    echo "✅ Client/server parity check PASSED"
    echo ""
    echo "All $(echo "$CLIENT_FUNCTIONS" | wc -l | tr -d ' ') client functions have corresponding MCP tools."
    exit 0
else
    echo "❌ Client/server parity check FAILED"
    echo ""
    echo "The following client functions are missing MCP tool exposure in server:"
    printf '  - %s\n' "${MISSING[@]}"
    echo ""
    echo "Action required:"
    echo "1. Add @mcp.tool() wrapper in $SERVER_FILE for each missing function"
    echo "2. Write e2e test in tests/test_e2e_mcp_tools.py"
    echo "3. Re-run this check"
    exit 1
fi
