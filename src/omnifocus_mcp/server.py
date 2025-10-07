#!/usr/bin/env python3
"""MCP Server for OmniFocus integration."""
import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.stdio import stdio_server

from .omnifocus_client import OmniFocusClient

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
            description="Add a new task to a specific OmniFocus project with full properties support",
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
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date in ISO 8601 format. Examples: '2025-10-15' (date only) or '2025-10-15T17:00:00' (with time)"
                    },
                    "defer_date": {
                        "type": "string",
                        "description": "Defer date in ISO 8601 format (when task becomes available). Examples: '2025-10-08' or '2025-10-08T09:00:00'"
                    },
                    "flagged": {
                        "type": "boolean",
                        "description": "Whether to flag the task (default: false)"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tag names to assign to the task. Tags must already exist in OmniFocus."
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
        ),
        Tool(
            name="get_tasks",
            description="Retrieve tasks from OmniFocus with optional filtering by project, completion status, and flagged status",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Optional project ID to filter tasks. If not provided, returns tasks from all projects"
                    },
                    "include_completed": {
                        "type": "boolean",
                        "description": "Whether to include completed tasks (default: false)"
                    },
                    "flagged_only": {
                        "type": "boolean",
                        "description": "Only return flagged tasks (default: false)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="complete_task",
            description="Mark a task as completed in OmniFocus",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The ID of the task to mark as completed"
                    }
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="update_task",
            description="Update properties of an existing task in OmniFocus",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The ID of the task to update"
                    },
                    "name": {
                        "type": "string",
                        "description": "New task name"
                    },
                    "note": {
                        "type": "string",
                        "description": "New task note"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "New due date in ISO 8601 format, or empty string to clear"
                    },
                    "defer_date": {
                        "type": "string",
                        "description": "New defer date in ISO 8601 format, or empty string to clear"
                    },
                    "flagged": {
                        "type": "boolean",
                        "description": "New flagged status"
                    }
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="get_inbox_tasks",
            description="Retrieve all tasks from the OmniFocus inbox",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="create_inbox_task",
            description="Create a new task in the OmniFocus inbox for quick capture",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_name": {
                        "type": "string",
                        "description": "The name of the task"
                    },
                    "note": {
                        "type": "string",
                        "description": "Optional note for the task"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Optional due date in ISO 8601 format"
                    },
                    "flagged": {
                        "type": "boolean",
                        "description": "Whether to flag the task"
                    }
                },
                "required": ["task_name"]
            }
        ),
        Tool(
            name="get_tags",
            description="Retrieve all tags from OmniFocus",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="add_tag_to_task",
            description="Add an existing tag to a task in OmniFocus",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The ID of the task"
                    },
                    "tag_name": {
                        "type": "string",
                        "description": "The name of the tag to add"
                    }
                },
                "required": ["task_id", "tag_name"]
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
            due_date = arguments.get("due_date")
            defer_date = arguments.get("defer_date")
            flagged = arguments.get("flagged", False)
            tags = arguments.get("tags")

            if not project_id or not task_name:
                return [TextContent(
                    type="text",
                    text="Error: project_id and task_name are required"
                )]

            success = client.add_task(
                project_id,
                task_name,
                note=note,
                due_date=due_date,
                defer_date=defer_date,
                flagged=flagged,
                tags=tags
            )

            if success:
                details = []
                if due_date:
                    details.append(f"due {due_date}")
                if defer_date:
                    details.append(f"defer {defer_date}")
                if flagged:
                    details.append("flagged")
                if tags:
                    details.append(f"tags: {', '.join(tags)}")

                details_str = f" ({'; '.join(details)})" if details else ""
                return [TextContent(
                    type="text",
                    text=f"Successfully added task '{task_name}' to project {project_id}{details_str}"
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

        elif name == "get_tasks":
            project_id = arguments.get("project_id")
            include_completed = arguments.get("include_completed", False)
            flagged_only = arguments.get("flagged_only", False)

            tasks = client.get_tasks(
                project_id=project_id,
                include_completed=include_completed,
                flagged_only=flagged_only
            )

            if not tasks:
                filter_desc = []
                if project_id:
                    filter_desc.append(f"in project {project_id}")
                if flagged_only:
                    filter_desc.append("flagged")
                if include_completed:
                    filter_desc.append("including completed")
                filter_str = " ".join(filter_desc) if filter_desc else ""
                return [TextContent(
                    type="text",
                    text=f"No tasks found {filter_str}".strip()
                )]

            # Format task list
            task_list = []
            for task in tasks:
                task_info = f"**{task['name']}**\n"
                task_info += f"ID: {task['id']}\n"

                if task['projectName']:
                    task_info += f"Project: {task['projectName']}\n"

                status_parts = []
                if task['completed']:
                    status_parts.append("✓ Completed")
                if task['flagged']:
                    status_parts.append("🚩 Flagged")
                if status_parts:
                    task_info += f"Status: {', '.join(status_parts)}\n"

                if task['dueDate']:
                    task_info += f"Due: {task['dueDate']}\n"
                if task['deferDate']:
                    task_info += f"Defer: {task['deferDate']}\n"
                if task['tags']:
                    task_info += f"Tags: {task['tags']}\n"

                if task['note']:
                    note_preview = task['note'][:100] + '...' if len(task['note']) > 100 else task['note']
                    task_info += f"Note: {note_preview}"

                task_list.append(task_info)

            filter_desc = []
            if project_id:
                filter_desc.append(f"from project {project_id}")
            if flagged_only:
                filter_desc.append("(flagged only)")
            if include_completed:
                filter_desc.append("(including completed)")
            filter_str = " ".join(filter_desc) if filter_desc else ""

            return [TextContent(
                type="text",
                text=f"Found {len(tasks)} tasks {filter_str}:\n\n" + "\n\n".join(task_list)
            )]

        elif name == "complete_task":
            task_id = arguments.get("task_id")

            if not task_id:
                return [TextContent(
                    type="text",
                    text="Error: task_id is required"
                )]

            success = client.complete_task(task_id)
            if success:
                return [TextContent(
                    type="text",
                    text=f"Successfully completed task {task_id}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Failed to complete task {task_id}"
                )]

        elif name == "update_task":
            task_id = arguments.get("task_id")

            if not task_id:
                return [TextContent(
                    type="text",
                    text="Error: task_id is required"
                )]

            # Extract optional fields
            name_val = arguments.get("name")
            note = arguments.get("note")
            due_date = arguments.get("due_date")
            defer_date = arguments.get("defer_date")
            flagged = arguments.get("flagged")

            success = client.update_task(
                task_id,
                name=name_val,
                note=note,
                due_date=due_date,
                defer_date=defer_date,
                flagged=flagged
            )

            if success:
                # Build a description of what was updated
                updated_fields = []
                if name_val is not None:
                    updated_fields.append("name")
                if note is not None:
                    updated_fields.append("note")
                if due_date is not None:
                    updated_fields.append("due_date")
                if defer_date is not None:
                    updated_fields.append("defer_date")
                if flagged is not None:
                    updated_fields.append("flagged")

                return [TextContent(
                    type="text",
                    text=f"Successfully updated task {task_id} ({', '.join(updated_fields)})"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Failed to update task {task_id}"
                )]

        elif name == "get_inbox_tasks":
            tasks = client.get_inbox_tasks()

            if not tasks:
                return [TextContent(
                    type="text",
                    text="No tasks in inbox"
                )]

            # Format task list
            task_list = []
            for task in tasks:
                task_info = f"**{task['name']}**\n"
                task_info += f"ID: {task['id']}\n"

                status_parts = []
                if task['completed']:
                    status_parts.append("✓ Completed")
                if task['flagged']:
                    status_parts.append("🚩 Flagged")
                if status_parts:
                    task_info += f"Status: {', '.join(status_parts)}\n"

                if task['dueDate']:
                    task_info += f"Due: {task['dueDate']}\n"
                if task['deferDate']:
                    task_info += f"Defer: {task['deferDate']}\n"
                if task['tags']:
                    task_info += f"Tags: {task['tags']}\n"

                if task['note']:
                    note_preview = task['note'][:100] + '...' if len(task['note']) > 100 else task['note']
                    task_info += f"Note: {note_preview}"

                task_list.append(task_info)

            return [TextContent(
                type="text",
                text=f"Found {len(tasks)} inbox tasks:\n\n" + "\n\n".join(task_list)
            )]

        elif name == "create_inbox_task":
            task_name = arguments.get("task_name")

            if not task_name:
                return [TextContent(
                    type="text",
                    text="Error: task_name is required"
                )]

            note = arguments.get("note")
            due_date = arguments.get("due_date")
            flagged = arguments.get("flagged")

            success = client.create_inbox_task(
                task_name,
                note=note,
                due_date=due_date,
                flagged=flagged
            )

            if success:
                return [TextContent(
                    type="text",
                    text=f"Successfully created inbox task '{task_name}'"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Failed to create inbox task '{task_name}'"
                )]

        elif name == "get_tags":
            tags = client.get_tags()

            if not tags:
                return [TextContent(
                    type="text",
                    text="No tags found"
                )]

            # Format tag list
            tag_list = [f"• **{tag['name']}** (ID: {tag['id']})" for tag in tags]

            return [TextContent(
                type="text",
                text=f"Found {len(tags)} tags:\n\n" + "\n".join(tag_list)
            )]

        elif name == "add_tag_to_task":
            task_id = arguments.get("task_id")
            tag_name = arguments.get("tag_name")

            if not task_id:
                return [TextContent(
                    type="text",
                    text="Error: task_id is required"
                )]

            if not tag_name:
                return [TextContent(
                    type="text",
                    text="Error: tag_name is required"
                )]

            success = client.add_tag_to_task(task_id, tag_name)

            if success:
                return [TextContent(
                    type="text",
                    text=f"Successfully added tag '{tag_name}' to task {task_id}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Failed to add tag '{tag_name}' to task {task_id}"
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
