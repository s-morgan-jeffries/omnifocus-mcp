"""Protocol-level smoke tests for OmniFocus MCP over stdio transport.

These tests verify the MCP JSON-RPC protocol layer by spawning the server
as a subprocess and communicating over stdio — the same transport that
Claude Desktop uses. Unlike test_e2e_real.py which calls server functions
directly, these tests exercise the full transport path:

    MCP Client → JSON-RPC (stdin) → Server Process → OmniFocus
    MCP Client ← JSON-RPC (stdout) ← Server Process ← OmniFocus

Why this matters:
- Catches JSON-RPC serialization/deserialization issues
- Verifies FastMCP's tool dispatch from incoming protocol messages
- Tests response formatting as an MCP client would receive it
- Exercises the same code path as Claude Desktop

Safety:
- Requires OMNIFOCUS_TEST_MODE=true
- Requires test database active
- Run with: make test-protocol
"""
import asyncio
import os
import pytest

from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

# Skip all tests unless in test mode
pytestmark = pytest.mark.skipif(
    os.environ.get('OMNIFOCUS_TEST_MODE', '').lower() != 'true',
    reason="Protocol tests require OMNIFOCUS_TEST_MODE=true. Run with: make test-protocol"
)


def _make_server_params():
    """Create server parameters for stdio connection."""
    env = {**os.environ}
    env["OMNIFOCUS_TEST_MODE"] = "true"
    env["OMNIFOCUS_TEST_DATABASE"] = os.environ.get(
        "OMNIFOCUS_TEST_DATABASE", "OmniFocus-TEST.ofocus"
    )
    return StdioServerParameters(
        command="uv",
        args=["run", "python", "-m", "omnifocus_mcp.server_fastmcp"],
        env=env,
    )


async def _run_with_session(fn):
    """Run an async function with an MCP session, handling cleanup."""
    params = _make_server_params()
    async with stdio_client(params) as streams:
        async with ClientSession(
            read_stream=streams[0],
            write_stream=streams[1],
        ) as session:
            await session.initialize()
            return await fn(session)


class TestProtocolSmoke:
    """Smoke tests verifying MCP protocol over stdio transport."""

    def test_list_tools_returns_expected_count(self):
        """Server reports 21 MCP tools over the protocol."""
        async def check(session):
            result = await session.list_tools()
            return [t.name for t in result.tools]

        tool_names = asyncio.run(_run_with_session(check))
        assert len(tool_names) == 21, f"Expected 21 tools, got {len(tool_names)}: {tool_names}"

    def test_list_tools_contains_expected_names(self):
        """Core tools are present in the tool listing."""
        async def check(session):
            result = await session.list_tools()
            return {t.name for t in result.tools}

        tool_names = asyncio.run(_run_with_session(check))
        expected = {"get_projects", "get_tasks", "create_tasks", "update_tasks",
                    "get_tags", "set_focus", "get_focus"}
        assert expected.issubset(tool_names), f"Missing tools: {expected - tool_names}"

    def test_get_projects_returns_content(self):
        """get_projects returns non-empty text content over the protocol."""
        async def check(session):
            result = await session.call_tool("get_projects", {})
            return result.content[0].text

        text = asyncio.run(_run_with_session(check))
        assert text, "get_projects returned empty response"
        # Response is formatted text, should contain project field names
        assert "ID:" in text or "name" in text.lower() or "No projects" in text

    def test_get_tags_returns_content(self):
        """get_tags returns non-empty text content over the protocol."""
        async def check(session):
            result = await session.call_tool("get_tags", {})
            return result.content[0].text

        text = asyncio.run(_run_with_session(check))
        assert text, "get_tags returned empty response"
        assert "ID:" in text or "tag" in text.lower() or "No tags" in text

    def test_task_crud_roundtrip(self):
        """Create a task, read it back, delete it — full round-trip over protocol."""
        async def check(session):
            # Create
            create_result = await session.call_tool("create_tasks", {
                "tasks": [{"task_name": "protocol-test-task"}]
            })
            create_text = create_result.content[0].text
            assert "protocol-test-task" in create_text

            # Extract task ID from response
            task_id = None
            for line in create_text.split("\n"):
                if "Task ID:" in line:
                    task_id = line.split("Task ID:")[-1].strip()
                    break
            assert task_id, f"Could not extract task ID from: {create_text}"

            # Read back
            get_result = await session.call_tool("get_tasks", {
                "task_id": task_id
            })
            get_text = get_result.content[0].text
            assert "protocol-test-task" in get_text

            # Delete
            delete_result = await session.call_tool("delete_tasks", {
                "task_ids": task_id
            })
            delete_text = delete_result.content[0].text
            assert "1" in delete_text or "success" in delete_text.lower()

            return True

        result = asyncio.run(_run_with_session(check))
        assert result
