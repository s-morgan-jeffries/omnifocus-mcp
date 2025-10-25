#!/bin/bash
# Check code quality beyond basic complexity
# Returns 0 if quality is acceptable, 1 if issues found

echo "Checking code quality..."

ISSUES_FOUND=0

# Check 1: Cyclomatic complexity (existing check)
echo "1. Checking cyclomatic complexity..."
if ./scripts/check_complexity.sh > /tmp/complexity.log 2>&1; then
    echo "   ✅ Complexity check passed"
else
    echo "   ❌ Complexity check failed"
    cat /tmp/complexity.log | grep "D\|F" | head -5 | sed 's/^/      /'
    ISSUES_FOUND=1
fi

# Check 2: Check for D-F rated functions
echo "2. Checking for high-complexity functions..."
HIGH_COMPLEXITY=$(radon cc src/omnifocus_mcp/ -s -n D 2>/dev/null | grep -E "^[A-Z]" | head -5 || true)
if [ -n "$HIGH_COMPLEXITY" ]; then
    echo "   ⚠️  Found D-F rated functions (complexity > 20):"
    echo "$HIGH_COMPLEXITY" | sed 's/^/      /'
    echo "      Consider refactoring these functions"
else
    echo "   ✅ No D-F rated functions found"
fi

# Check 3: Check for TODO/FIXME comments in source
echo "3. Checking for TODO/FIXME markers..."
TODOS=$(grep -rn "TODO\|FIXME" src/omnifocus_mcp/ 2>/dev/null | grep -v "__pycache__" || true)
TODO_COUNT=$(echo "$TODOS" | grep -c "." || echo "0")

if [ "$TODO_COUNT" -gt 0 ]; then
    echo "   ⚠️  Found $TODO_COUNT TODO/FIXME markers in source:"
    echo "$TODOS" | head -5 | sed 's/^/      /'
    if [ "$TODO_COUNT" -gt 5 ]; then
        echo "      ... and $((TODO_COUNT - 5)) more"
    fi
else
    echo "   ✅ No TODO/FIXME markers in source"
fi

# Check 4: Check for print() statements (should use logging)
echo "4. Checking for print() statements..."
PRINTS=$(grep -rn "print(" src/omnifocus_mcp/ 2>/dev/null | grep -v "__pycache__" | grep -v "# print OK" || true)
PRINT_COUNT=$(echo "$PRINTS" | grep -c "." || echo "0")

if [ "$PRINT_COUNT" -gt 0 ]; then
    echo "   ⚠️  Found $PRINT_COUNT print() statements (should use logging):"
    echo "$PRINTS" | head -3 | sed 's/^/      /'
else
    echo "   ✅ No print() statements found"
fi

# Check 5: Check for bare except: clauses
echo "5. Checking for bare except: clauses..."
BARE_EXCEPTS=$(grep -rn "except:" src/omnifocus_mcp/ 2>/dev/null | grep -v "__pycache__" | grep -v "# except: OK" || true)
EXCEPT_COUNT=$(echo "$BARE_EXCEPTS" | grep -c "." || echo "0")

if [ "$EXCEPT_COUNT" -gt 0 ]; then
    echo "   ⚠️  Found $EXCEPT_COUNT bare except: clauses:"
    echo "$BARE_EXCEPTS" | head -3 | sed 's/^/      /'
    echo "      Consider catching specific exceptions"
else
    echo "   ✅ No bare except: clauses found"
fi

# Check 6: Check for long lines
echo "6. Checking for overly long lines..."
LONG_LINES=$(grep -rn ".\{121,\}" src/omnifocus_mcp/*.py 2>/dev/null | grep -v "__pycache__" | wc -l || echo "0")

if [ "$LONG_LINES" -gt 10 ]; then
    echo "   ⚠️  Found $LONG_LINES lines over 120 characters"
    echo "      Consider breaking up long lines for readability"
elif [ "$LONG_LINES" -gt 0 ]; then
    echo "   ✅ Only $LONG_LINES lines over 120 characters (acceptable)"
else
    echo "   ✅ No overly long lines found"
fi

echo ""
if [ $ISSUES_FOUND -eq 0 ]; then
    echo "✅ Code quality check passed"
    echo "   (Warnings above are informational, not blocking)"
    exit 0
else
    echo "❌ Code quality check failed"
    echo "   Address critical issues before releasing"
    exit 1
fi
