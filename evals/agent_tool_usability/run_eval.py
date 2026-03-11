#!/usr/bin/env python3
"""Run blind agent eval for OmniFocus MCP tool usability.

This eval spawns subagents that see ONLY tool descriptions (no codebase,
no web search, no prior OmniFocus knowledge). Each agent gets a scenario
and must plan which tool(s) to call with what parameters.

Usage:
    Run via Claude Code Agent tool (see README.md) or manually score
    by reviewing the scenarios in scenarios.py against agent responses.

The actual eval execution is done through Claude Code's Agent tool,
spawning blind subagents with the tool_descriptions.md content.
Results are scored and documented in results/scored_results.md.
"""

# This file documents the eval methodology.
# Actual execution is done via Claude Code Agent tool invocations.
# See scenarios.py for the 18 eval scenarios and scoring criteria.
