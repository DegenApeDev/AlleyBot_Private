"""
MCP Plugin - Model Context Protocol Integration
Enables web browsing, research, and self-improvement through FastMCP
"""

"""
MCP Plugin for AlleyBot
Model Context Protocol integration for web access and research using FastMCP
"""
from .fastmcp_plugin import FastMCPPlugin
MCPPlugin = FastMCPPlugin  # Alias for compatibility
__all__ = ['FastMCPPlugin', 'MCPPlugin']
