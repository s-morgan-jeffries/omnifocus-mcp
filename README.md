# OmniFocus MCP Server

An MCP (Model Context Protocol) server that provides tools for interacting with OmniFocus on macOS.

## Features

This server provides the following tools:

- **get_projects** - Get all active projects from OmniFocus with their folder hierarchy, names, notes, and status
- **search_projects** - Search projects by name, note content, or folder path
- **add_task** - Add a new task to a specific project
- **add_note** - Append a note to an existing project

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

# Install dependencies
pip install -r requirements.txt
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
        "server.py"
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
        "/absolute/path/to/omnifocus-mcp/server.py"
      ]
    }
  }
}
```

**Important:** Replace `/absolute/path/to/omnifocus-mcp` with the actual absolute path to this directory.

### For Other MCP Clients

Any MCP-compatible client can use this server by launching it with:

```bash
python server.py
```

The server communicates via stdin/stdout using the MCP protocol.

## Usage Examples

Once configured, you can ask Claude (or any MCP client) to interact with OmniFocus:

- "Show me all my OmniFocus projects"
- "Search for projects related to 'budget'"
- "Add a task 'Review Q4 numbers' to project proj-001"
- "Add a note to my project about the meeting outcome"

## Development

### Running Tests

The project has comprehensive test coverage with 67 tests covering all functionality:

```bash
# Run all tests
make test

# Or using pytest directly
./venv/bin/pytest

# Run with verbose output
make test-verbose
```

See [TESTING.md](TESTING.md) for detailed testing documentation.

### Testing the Server

You can test the server locally:

```bash
# Run the server (it will wait for MCP protocol messages on stdin)
python server.py
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
