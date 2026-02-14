"""
MCP Plugin - Model Context Protocol Integration
Enables web browsing, research, and self-improvement through WindSurf
"""

"""
MCP Plugin for AlleyBot
Model Context Protocol integration for web access and research
"""
from .mcp_plugin import MCPPlugin

try:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from mcp_client import MCPClient, get_mcp_client, init_mcp, cleanup_mcp
    __all__ = ['MCPPlugin', 'MCPClient', 'get_mcp_client', 'init_mcp', 'cleanup_mcp']
except ImportError:
    __all__ = ['MCPPlugin']
