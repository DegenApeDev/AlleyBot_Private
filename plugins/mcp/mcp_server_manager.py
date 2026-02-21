"""
MCP Server Manager - Dynamic MCP Server Integration
Extends AlleyBot functionality through MCP servers
"""
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
from plugin_manager import AlleyBotPlugin

try:
    from fastmcp import FastMCP
    FASTMCP_AVAILABLE = True
except (ImportError, Exception) as e:
    FASTMCP_AVAILABLE = False
    print(f"⚠️ FastMCP not available - {e}")

# Fallback to original MCP SDK
try:
    from mcp import ClientSession
    from mcp.client.sse import sse_client
    from mcp.client.streamable_http import streamable_http_client
    from mcp.shared.session import MCPError
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


class MCPServerManager(AlleyBotPlugin):
    """Dynamic MCP Server Manager for extending AlleyBot functionality"""
    
    def __init__(self, config):
        super().__init__(config or {})
        self.name = "mcp_server_manager"
        self.id = "mcp_server_manager"
        self.version = "1.0.0"
        self.description = "Dynamic MCP Server Manager - Extends functionality through MCP servers"
        self.module = "plugins.mcp.mcp_server_manager"
        self.category = "tools"
        self.status = "initializing"
        self.registered_servers = {}
        self.dynamic_capabilities = {}
        self.server_registry = {}
        
    def __str__(self):
        return f"MCPServerManager(name={self.name}, servers={len(self.registered_servers)})"

    def initialize(self, api, core):
        """Initialize MCP Server Manager"""
        try:
            super().initialize(api, core)
            
            if not FASTMCP_AVAILABLE and not MCP_AVAILABLE:
                self.status = "failed"
                return "❌ Neither FastMCP nor MCP SDK available"
            
            # Load server registry
            self._load_server_registry()
            
            # Initialize configured servers
            servers = self.config.get('servers', {})
            connected_count = 0
            
            for server_name, server_config in servers.items():
                if server_config.get('enabled', True):
                    if self._register_server(server_name, server_config):
                        connected_count += 1
            
            self.status = f"connected_{connected_count}"
            return f"✅ MCP Server Manager connected to {connected_count} servers"
            
        except Exception as e:
            self.status = "failed"
            error_msg = f"❌ MCP Server Manager initialize() crashed: {e}"
            print(error_msg)
            return error_msg

    def _load_server_registry(self):
        """Load known MCP server registry"""
        registry_file = Path(__file__).parent / "server_registry.json"
        
        if registry_file.exists():
            try:
                with open(registry_file, 'r') as f:
                    self.server_registry = json.load(f)
                print(f"📋 Loaded {len(self.server_registry)} known MCP servers")
            except Exception as e:
                print(f"⚠️ Failed to load server registry: {e}")
                self.server_registry = {}
        else:
            # Default registry
            self.server_registry = {
                "coingecko": {
                    "name": "CoinGecko MCP",
                    "description": "Cryptocurrency market data",
                    "url": "https://mcp.api.coingecko.com/sse",
                    "type": "crypto",
                    "capabilities": ["get_price", "get_market_data", "search_crypto"]
                },
                "alphavantage": {
                    "name": "Alpha Vantage MCP", 
                    "description": "Stock market and financial data",
                    "url": "http://127.0.0.1:8000/mcp",
                    "type": "finance",
                    "capabilities": ["get_stock_price", "get_forex", "get_crypto_price"]
                },
                "yfinance": {
                    "name": "Yahoo Finance MCP",
                    "description": "Yahoo Finance data integration",
                    "url": "https://mcp.yfinance.dev/sse", 
                    "type": "finance",
                    "capabilities": ["get_stock_price", "get_market_data", "get_company_info"]
                },
                "finnhub": {
                    "name": "Finnhub MCP",
                    "description": "Real-time market data and news",
                    "url": "https://mcp.finnhub.io/mcp",
                    "type": "finance", 
                    "capabilities": ["get_quote", "get_news", "get_company_profile"]
                },
                "polygon": {
                    "name": "Polygon.io MCP",
                    "description": "Stock market data and APIs",
                    "url": "https://mcp.polygon.io/sse",
                    "type": "finance",
                    "capabilities": ["get_ticker", "get_aggregates", "get_trades"]
                },
                "weather": {
                    "name": "Weather MCP",
                    "description": "Weather data and forecasts",
                    "url": "https://mcp.weather.dev/sse",
                    "type": "weather",
                    "capabilities": ["get_current_weather", "get_forecast", "get_alerts"]
                },
                "news": {
                    "name": "News MCP",
                    "description": "News aggregation and search",
                    "url": "https://mcp.news.dev/sse",
                    "type": "news",
                    "capabilities": ["search_articles", "get_trending", "get_headlines"]
                },
                "github": {
                    "name": "GitHub MCP",
                    "description": "GitHub repository and code analysis",
                    "url": "https://mcp.github.dev/sse",
                    "type": "development",
                    "capabilities": ["get_repo", "search_code", "get_issues", "get_prs"]
                },
                "websearch": {
                    "name": "Web Search MCP",
                    "description": "Web search and content extraction",
                    "url": "https://mcp.search.dev/sse",
                    "type": "search",
                    "capabilities": ["search_web", "extract_content", "get_page_info"]
                },
                "database": {
                    "name": "Database MCP",
                    "description": "Database query and management",
                    "url": "https://mcp.db.dev/sse",
                    "type": "database",
                    "capabilities": ["query_sql", "get_schema", "execute_procedure"]
                }
            }
            
            # Save default registry
            try:
                with open(registry_file, 'w') as f:
                    json.dump(self.server_registry, f, indent=2)
                print(f"📋 Created default server registry with {len(self.server_registry)} servers")
            except Exception as e:
                print(f"⚠️ Failed to save server registry: {e}")

    def _register_server(self, server_name: str, server_config: dict) -> bool:
        """Register and connect to an MCP server"""
        try:
            # Get server info from registry if available
            registry_info = self.server_registry.get(server_name, {})
            
            # Merge config with registry info
            full_config = {**registry_info, **server_config}
            
            server_url = full_config.get('url')
            if not server_url:
                print(f"⚠️ No server URL for {server_name}")
                return False
            
            print(f"🔌 Registering {server_name} at {server_url}")
            
            # Connect using FastMCP or fallback
            if FASTMCP_AVAILABLE:
                success = self._connect_fastmcp(server_name, server_url, full_config)
            else:
                success = self._connect_mcp_sdk(server_name, server_url, full_config)
            
            if success:
                # Discover and register capabilities
                asyncio.run(self._discover_capabilities(server_name))
                return True
            
        except Exception as e:
            print(f"❌ Failed to register {server_name}: {e}")
        
        return False

    def _connect_fastmcp(self, server_name: str, server_url: str, server_config: dict) -> bool:
        """Connect using FastMCP"""
        try:
            client = FastMCP(server_name)
            
            # Handle authentication
            auth_config = server_config.get('auth', {})
            if auth_config:
                auth_type = auth_config.get('type')
                if auth_type == 'api_key':
                    param = auth_config.get('param', 'apikey')
                    token_env = auth_config.get('token_env')
                    if token_env and os.getenv(token_env):
                        separator = '&' if '?' in server_url else '?'
                        server_url = f"{server_url}{separator}{param}={os.getenv(token_env)}"
            
            asyncio.run(client.connect(server_url))
            
            self.registered_servers[server_name] = {
                'client': client,
                'type': 'fastmcp',
                'url': server_url,
                'config': server_config,
                'connected_at': datetime.now().isoformat()
            }
            
            print(f"✅ FastMCP {server_name} registered")
            return True
            
        except Exception as e:
            print(f"❌ FastMCP registration failed for {server_name}: {e}")
            return False

    def _connect_mcp_sdk(self, server_name: str, server_url: str, server_config: dict) -> bool:
        """Fallback: Connect using MCP SDK"""
        try:
            transport_type = server_config.get('transport', 'auto')
            
            if transport_type == 'sse' or ('sse' in server_url.lower()):
                transport_ctx = sse_client(server_url)
            else:
                transport_ctx = streamable_http_client(server_url)
            
            session = ClientSession(transport_ctx.__enter__())
            asyncio.run(session.initialize())
            
            self.registered_servers[server_name] = {
                'session': session,
                'transport_ctx': transport_ctx,
                'type': 'mcp_sdk',
                'url': server_url,
                'config': server_config,
                'connected_at': datetime.now().isoformat()
            }
            
            print(f"✅ MCP SDK {server_name} registered")
            return True
            
        except Exception as e:
            print(f"❌ MCP SDK registration failed for {server_name}: {e}")
            return False

    async def _discover_capabilities(self, server_name: str):
        """Discover and register server capabilities"""
        try:
            server_info = self.registered_servers.get(server_name)
            if not server_info:
                return
            
            # List available tools
            if server_info['type'] == 'fastmcp':
                tools = await server_info['client'].list_tools()
            else:
                tools = await server_info['session'].list_tools()
            
            # Register capabilities
            capabilities = []
            for tool in tools.tools:
                capability = {
                    'name': tool.name,
                    'description': tool.description,
                    'server': server_name,
                    'parameters': getattr(tool, 'inputSchema', {})
                }
                capabilities.append(capability)
                
                # Add to dynamic capabilities registry
                self.dynamic_capabilities[tool.name] = capability
            
            print(f"🔍 Discovered {len(capabilities)} capabilities for {server_name}")
            
        except Exception as e:
            print(f"⚠️ Failed to discover capabilities for {server_name}: {e}")

    async def call_capability(self, capability_name: str, **kwargs):
        """Call a specific capability from any registered server"""
        try:
            if capability_name not in self.dynamic_capabilities:
                return f"❌ Capability '{capability_name}' not found"
            
            capability = self.dynamic_capabilities[capability_name]
            server_name = capability['server']
            server_info = self.registered_servers.get(server_name)
            
            if not server_info:
                return f"❌ Server '{server_name}' not available"
            
            # Call the capability
            if server_info['type'] == 'fastmcp':
                result = await server_info['client'].call_tool(capability_name, kwargs)
            else:
                result = await server_info['session'].call_tool(capability_name, kwargs)
            
            return f"✅ {capability_name} result:\n{json.dumps(result, indent=2)}"
            
        except Exception as e:
            return f"❌ Failed to call {capability_name}: {e}"

    def discover_servers_command(self):
        """Discover and list available MCP servers"""
        try:
            output = ["🔍 MCP Server Discovery:\n"]
            
            # Registered servers
            output.append(f"✅ Connected Servers ({len(self.registered_servers)}):")
            for server_name, server_info in self.registered_servers.items():
                server_type = server_info['type']
                connected_at = server_info.get('connected_at', 'Unknown')
                capabilities_count = len([c for c in self.dynamic_capabilities.values() if c['server'] == server_name])
                output.append(f"  • {server_name} ({server_type}) - {capabilities_count} capabilities")
            
            # Available servers in registry
            unregistered = set(self.server_registry.keys()) - set(self.registered_servers.keys())
            if unregistered:
                output.append(f"\n📋 Available Servers ({len(unregistered)}):")
                for server_name in sorted(unregistered):
                    server_info = self.server_registry[server_name]
                    output.append(f"  • {server_name}: {server_info.get('description', 'No description')}")
            
            # All capabilities
            output.append(f"\n🎯 Total Capabilities: {len(self.dynamic_capabilities)}")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ Server discovery failed: {e}"

    def capabilities_command(self):
        """List all discovered capabilities"""
        try:
            if not self.dynamic_capabilities:
                return "❌ No capabilities discovered"
            
            # Group capabilities by server
            by_server = {}
            for cap_name, cap_info in self.dynamic_capabilities.items():
                server = cap_info['server']
                if server not in by_server:
                    by_server[server] = []
                by_server[server].append((cap_name, cap_info))
            
            output = [f"🎯 Discovered Capabilities ({len(self.dynamic_capabilities)} total):"]
            
            for server_name, capabilities in by_server.items():
                output.append(f"\n📡 {server_name}:")
                for cap_name, cap_info in capabilities:
                    description = cap_info.get('description', 'No description')
                    output.append(f"  • {cap_name}: {description}")
            
            return "\n".join(output)
            
        except Exception as e:
            return f"❌ Capabilities listing failed: {e}"

    def register_server_command(self, server_name: str, server_url: str, server_type: str = "auto"):
        """Register a new MCP server dynamically"""
        try:
            config = {
                'url': server_url,
                'type': server_type,
                'enabled': True
            }
            
            if self._register_server(server_name, config):
                return f"✅ Server '{server_name}' registered successfully"
            else:
                return f"❌ Failed to register server '{server_name}'"
                
        except Exception as e:
            return f"❌ Server registration failed: {e}"

    def get_commands(self):
        """Return available commands"""
        return {
            'mcp_discover': self.discover_servers_command,
            'mcp_capabilities': self.capabilities_command,
            'mcp_register': self.register_server_command,
        }

    def cleanup(self):
        """Cleanup MCP connections"""
        try:
            for server_name, server_info in self.registered_servers.items():
                try:
                    if server_info['type'] == 'fastmcp':
                        client = server_info['client']
                        if hasattr(client, 'close'):
                            asyncio.run(client.close())
                    else:
                        transport_ctx = server_info['transport_ctx']
                        if hasattr(transport_ctx, '__exit__'):
                            transport_ctx.__exit__(None, None, None)
                except Exception as e:
                    print(f"⚠️ Error cleaning up {server_name}: {e}")
            
            self.registered_servers.clear()
            self.dynamic_capabilities.clear()
            print("✅ MCP Server Manager cleanup complete")
            
        except Exception as e:
            print(f"⚠️ MCP Server Manager cleanup error: {e}")
