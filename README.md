# OmniFocus MCP Server

An MCP (Model Context Protocol) server that provides tools for interacting with OmniFocus on macOS.

## Features

This server provides **36 comprehensive tools** for managing OmniFocus:

### Project Management
- **get_projects** - Get all active projects with folder hierarchy, names, notes, and status (supports query parameter for text search)
- **create_project** - Create new projects with optional folder placement and sequential mode
- **delete_project** - Delete a project and all its tasks

### Task Management
- **get_tasks** - Get tasks with advanced filtering (flagged, available, overdue, by tag, text search, inbox-only)
- **add_task** - Add new tasks with due dates, defer dates, flags, tags, and estimated time
- **update_task** - Update any task properties (name, dates, flags, notes)
- **complete_task** - Mark tasks as completed
- **delete_task** - Delete tasks
- **move_task** - Move tasks between projects or to inbox
- **drop_task** - Mark task as dropped/on hold (task becomes inactive)
- **set_parent_task** - Create task hierarchies with parent/child relationships
- **set_estimated_minutes** - Set time estimates for tasks

### Inbox Operations
- **create_inbox_task** - Quickly capture tasks to inbox
- **Note:** Use `get_tasks(inbox_only=True)` to retrieve inbox tasks

### Folder & Organization
- **get_folders** - Get all folders and their hierarchy
- **create_folder** - Create new folders with optional parent folders

### Tags
- **get_tags** - Get all available tags
- **add_tag_to_task** - Add tags to tasks for better organization

### Project Review (GTD)
- **set_review_interval** - Set how often projects should be reviewed
- **mark_project_reviewed** - Mark a project as reviewed (resets review timer)
- **get_projects_due_for_review** - Find projects that need review

### Perspectives (OmniFocus Pro)
- **get_perspectives** - List all custom perspectives
- **switch_perspective** - Switch to a different perspective view

### Notes
- **add_note** - Append notes to projects or tasks
- **get_note** - Retrieve full note content from projects or tasks (no truncation)

## Prerequisites

- macOS (OmniFocus is macOS-only)
- OmniFocus app installed
- Python 3.10 or higher
- UV package manager (recommended) or pip

## Installation

### Option 1: Using UV (Recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone this repository
git clone <your-repo-url>
cd omnifocus-mcp

# Install dependencies
uv pip install -e .
```

### Option 2: Using pip

```bash
# Clone this repository
git clone <your-repo-url>
cd omnifocus-mcp

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install in development mode with dependencies
pip install -e ".[dev]"
```

## Configuration

### For Claude Desktop

Add this server to your Claude Desktop configuration file:

**Location:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "omnifocus": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/omnifocus-mcp",
        "run",
        "omnifocus-mcp"
      ]
    }
  }
}
```

Or if using a virtual environment directly:

```json
{
  "mcpServers": {
    "omnifocus": {
      "command": "/absolute/path/to/omnifocus-mcp/venv/bin/python",
      "args": [
        "-m",
        "omnifocus_mcp.server_fastmcp"
      ]
    }
  }
}
```

**Important:** Replace `/absolute/path/to/omnifocus-mcp` with the actual absolute path to this directory.

### For Other MCP Clients

Any MCP-compatible client can use this server by launching it with:

```bash
python -m omnifocus_mcp.server_fastmcp
```

The server communicates via stdin/stdout using the MCP protocol.

## Usage Examples

Once configured, you can ask Claude (or any MCP client) to interact with OmniFocus:

**Project Management:**
- "Show me all my OmniFocus projects"
- "Search for projects related to 'budget'" → uses `get_projects(query="budget")`
- "Create a new project called 'Q1 Planning' in my Work folder"
- "What projects are due for review?"

**Task Management:**
- "Add a task 'Review Q4 numbers' with a due date next Friday, flagged as important"
- "Show me all available tasks that are overdue"
- "Do I have a mortgage payment due this week?" → uses `get_tasks(query="mortgage", due_relative="this_week")`
- "Mark task task-001 as complete"
- "Move this task to my Personal project"
- "Set time estimate for task-001 to 90 minutes"

**Inbox & Quick Capture:**
- "Add 'Call dentist' to my inbox"
- "Show me what's in my inbox" → uses `get_tasks(inbox_only=True)`

**Organization:**
- "Add the 'urgent' tag to task-001"
- "Create a new folder called 'Personal Goals' inside 'Life'"
- "Make task-002 a subtask of task-001"

**GTD Review:**
- "Set the review interval for this project to 2 weeks"
- "Mark project proj-001 as reviewed"

**Perspectives (Pro):**
- "Switch to my 'Daily Worklist' perspective"
- "What perspectives do I have available?"

## Development

### Running Tests

The project has comprehensive test coverage with **393 tests passing (13 skipped integration tests)**:

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=src/omnifocus_mcp --cov-report=term-missing

# Run specific test file
pytest tests/test_omnifocus_client.py -v
```

**Test Suite Breakdown:**
- 149 unit tests for OmniFocus client operations
- 33 unit tests for FastMCP server
- 22 safety guard tests
- 13 real OmniFocus integration tests (skipped by default)

See [docs/TESTING.md](docs/TESTING.md) for detailed testing documentation.

### Testing the Server

You can test the server locally:

```bash
# Run the server (it will wait for MCP protocol messages on stdin)
python -m omnifocus_mcp.server_fastmcp
```

### Debugging

The server logs to stderr, which Claude Desktop captures. To see logs:

1. Open Claude Desktop
2. Go to the menu and enable developer mode
3. View logs in the developer console

## Permissions

The first time you run this server, macOS may prompt you to grant permissions for:
- Accessibility access (to control OmniFocus via AppleScript)
- Automation permissions for OmniFocus

Grant these permissions to allow the server to function properly.

## Troubleshooting

### "Operation not permitted" errors
- Check System Settings > Privacy & Security > Automation
- Ensure the terminal or Claude Desktop has permission to control OmniFocus

### "OmniFocus is not running" errors
- Make sure OmniFocus app is running
- Try restarting OmniFocus and the MCP server

### Server not appearing in Claude Desktop
- Check the configuration file syntax (must be valid JSON)
- Verify the absolute paths are correct
- Restart Claude Desktop after changing configuration
- Check Claude Desktop logs for error messages

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR.
