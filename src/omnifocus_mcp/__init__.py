"""OmniFocus MCP Server - Model Context Protocol server for OmniFocus integration."""

__version__ = "0.8.0"

from .omnifocus_connector import OmniFocusConnector, run_applescript

__all__ = ["OmniFocusConnector", "run_applescript"]
