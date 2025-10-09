"""OmniFocus MCP Server - Model Context Protocol server for OmniFocus integration."""

__version__ = "0.5.0"

from .omnifocus_client import OmniFocusClient, run_applescript

__all__ = ["OmniFocusClient", "run_applescript"]
