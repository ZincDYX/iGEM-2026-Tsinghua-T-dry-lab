"""MCP-style tool surface for agent integrations."""

from .registry import ToolRegistry, create_default_registry
from .types import McpTool, McpToolResult

__all__ = ["McpTool", "McpToolResult", "ToolRegistry", "create_default_registry"]
