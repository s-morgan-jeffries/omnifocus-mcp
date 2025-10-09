#!/bin/bash

# Run Integration Tests with Test Database
# This script opens the test database in OmniFocus and runs integration tests

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
OF4_DIR="$HOME/Library/Containers/com.omnigroup.OmniFocus4/Data/Library/Application Support/OmniFocus"
TEST_DB="$OF4_DIR/OmniFocus-TEST.ofocus"

echo -e "${GREEN}OmniFocus Integration Test Runner${NC}"
echo "================================================"
echo ""

# Check if test database exists
if [ ! -d "$TEST_DB" ]; then
    echo -e "${RED}ERROR: Test database not found at:${NC}"
    echo "$TEST_DB"
    echo ""
    echo "Run ./scripts/setup_test_database.sh first to create it."
    exit 1
fi

# Check if OmniFocus is running
if pgrep -x "OmniFocus" > /dev/null; then
    echo -e "${YELLOW}OmniFocus is currently running.${NC}"
    echo ""
    read -p "Quit OmniFocus and open test database? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled. Please quit OmniFocus manually and run this script again."
        exit 0
    fi

    echo "Quitting OmniFocus..."
    osascript -e 'tell application "OmniFocus" to quit'
    sleep 2
fi

echo -e "${YELLOW}Step 1: Opening test database in OmniFocus...${NC}"
echo ""

# Open the test database in OmniFocus
open "$TEST_DB"

# Wait for OmniFocus to load the database
echo "Waiting for OmniFocus to load test database (5 seconds)..."
sleep 5

# Verify the correct database is open
DB_NAME=$(osascript -e 'tell application "OmniFocus" to tell front document to return name of it' 2>/dev/null || echo "")

if [ "$DB_NAME" != "OmniFocus-TEST.ofocus" ]; then
    echo -e "${RED}ERROR: Wrong database is open!${NC}"
    echo "Expected: OmniFocus-TEST.ofocus"
    echo "Got: $DB_NAME"
    echo ""
    echo "The test database file exists but OmniFocus didn't open it."
    echo "This might be a sandboxing issue. Try opening it manually:"
    echo "  File → Open Database → $TEST_DB"
    exit 1
fi

echo -e "${GREEN}✓ Test database is open: $DB_NAME${NC}"
echo ""

echo -e "${YELLOW}Step 2: Running integration tests...${NC}"
echo ""

# Run the tests with environment variables
export OMNIFOCUS_TEST_MODE=true
export OMNIFOCUS_TEST_DATABASE="OmniFocus-TEST.ofocus"

./venv/bin/python3 -m pytest tests/test_integration_real.py -v "$@"

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}✓ All integration tests passed!${NC}"
    echo -e "${GREEN}================================================${NC}"
else
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}✗ Some integration tests failed${NC}"
    echo -e "${RED}================================================${NC}"
fi

echo ""
echo -e "${YELLOW}NOTE: Test database is still open in OmniFocus.${NC}"
echo "To switch back to production:"
echo "  File → Open → Select your production database"
echo "Or just quit and reopen OmniFocus normally."

exit $TEST_EXIT_CODE
