#!/usr/bin/env python3
"""MCP Server for OmniFocus integration."""
import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.stdio import stdio_server

from omnifocus_client import OmniFocusClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("omnifocus-mcp")

# Create MCP server instance
app = Server("omnifocus-mcp")

# Initialize OmniFocus client
client = OmniFocusClient()


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available OmniFocus tools."""
    return [
        Tool(
            name="get_projects",
            description="Get all active projects from OmniFocus with their folder hierarchy, names, notes, and status",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="search_projects",
            description="Search OmniFocus projects by name, note content, or folder path",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query to match against project names, notes, or folder paths"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="add_task",
            description="Add a new task to a specific OmniFocus project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The ID of the project to add the task to"
                    },
                    "task_name": {
                        "type": "string",
                        "description": "The name/title of the task"
                    },
                    "note": {
                        "type": "string",
                        "description": "Optional note/description for the task"
                    }
                },
                "required": ["project_id", "task_name"]
            }
        ),
        Tool(
            name="add_note",
            description="Append a note to an existing OmniFocus project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "The ID of the project to add the note to"
                    },
                    "note_text": {
                        "type": "string",
                        "description": "The note text to append to the project"
                    }
                },
                "required": ["project_id", "note_text"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent | ImageContent | EmbeddedResource]:
    """Handle tool calls for OmniFocus operations."""
    try:
        if name == "get_projects":
            projects = client.get_projects()
            return [TextContent(
                type="text",
                text=f"Found {len(projects)} active projects:\n\n" +
                     "\n\n".join([
                         f"**{p['name']}**\n"
                         f"ID: {p['id']}\n"
                         f"Folder: {p['folderPath'] or '(root)'}\n"
                         f"Status: {p['status']}\n"
                         f"Note: {p['note'][:100] + '...' if len(p['note']) > 100 else p['note']}"
                         for p in projects
                     ])
            )]

        elif name == "search_projects":
            query = arguments.get("query")
            if not query:
                return [TextContent(type="text", text="Error: query parameter is required")]

            matches = client.search_projects(query)
            if not matches:
                return [TextContent(type="text", text=f"No projects found matching '{query}'")]

            return [TextContent(
                type="text",
                text=f"Found {len(matches)} projects matching '{query}':\n\n" +
                     "\n\n".join([
                         f"**{p['name']}**\n"
                         f"ID: {p['id']}\n"
                         f"Folder: {p['folderPath'] or '(root)'}\n"
                         f"Status: {p['status']}\n"
                         f"Note: {p['note'][:100] + '...' if len(p['note']) > 100 else p['note']}"
                         for p in matches
                     ])
            )]

        elif name == "add_task":
            project_id = arguments.get("project_id")
            task_name = arguments.get("task_name")
            note = arguments.get("note")

            if not project_id or not task_name:
                return [TextContent(
                    type="text",
                    text="Error: project_id and task_name are required"
                )]

            success = client.add_task(project_id, task_name, note)
            if success:
                return [TextContent(
                    type="text",
                    text=f"Successfully added task '{task_name}' to project {project_id}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Failed to add task '{task_name}' to project {project_id}"
                )]

        elif name == "add_note":
            project_id = arguments.get("project_id")
            note_text = arguments.get("note_text")

            if not project_id or not note_text:
                return [TextContent(
                    type="text",
                    text="Error: project_id and note_text are required"
                )]

            success = client.add_note(project_id, note_text)
            if success:
                return [TextContent(
                    type="text",
                    text=f"Successfully added note to project {project_id}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Failed to add note to project {project_id}"
                )]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.error(f"Error executing tool {name}: {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
