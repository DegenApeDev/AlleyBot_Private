"""
FastMCP Plugin - Model Context Protocol Integration using FastMCP
Provides robust web browsing, research, and self-improvement capabilities
"""
import asyncio
import sys
import os
import traceback
import json
from pathlib import Path
from datetime import datetime
from plugin_manager import AlleyBotPlugin
from plugins.mcp.rss_news_fetcher import RSSNewsFetcher

# Try FastMCP first
try:
    from fastmcp import Client
    FASTMCP_AVAILABLE = True
except (ImportError, Exception) as e:
    FASTMCP_AVAILABLE = False
    print(f"⚠️ FastMCP not available - {e}")
    print("⚠️ FastMCP import failed - falling back to MCP SDK")

# Fallback to original MCP SDK
try:
    from mcp import ClientSession
    from mcp.client.sse import sse_client
    from mcp.client.streamable_http import streamable_http_client
    from mcp.shared.session import MCPError
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False


class FastMCPPlugin(AlleyBotPlugin):
    """FastMCP integration plugin for web access and self-improvement"""
    
    def __init__(self, config):
        super().__init__(config or {})
        self.name = "fastmcp"
        self.id = "fastmcp"
        self.version = "2.0.0"
        self.description = "FastMCP - Robust Model Context Protocol integration"
        self.module = "plugins.mcp.fastmcp_plugin"
        self.category = "tools"
        self.status = "initializing"
        self.mcp_servers = {}
        self.last_research = None
        self.research_cache = {}
        self.rss_news_fetcher = None
        
    def __str__(self):
        return f"FastMCPPlugin(name={self.name}, connected={len(self.mcp_servers)})"

    def initialize(self, api, core):
        """Initialize FastMCP plugin with multiple servers"""
        try:
            super().initialize(api, core)
            
            if not FASTMCP_AVAILABLE and not MCP_AVAILABLE:
                self.status = "failed"
                return "❌ Neither FastMCP nor MCP SDK available"
            
            # Get server configuration
            servers = self.config.get('servers', {})
            enabled_servers = {k: v for k, v in servers.items() if v.get('enabled', True)}
            
            if not enabled_servers:
                self.status = "no_servers"
                return "⚠️ No MCP servers configured"
            
            print(f"🔌 Initializing {len(enabled_servers)} MCP servers...")
            
            # Initialize each server
            connected_count = 0
            for server_name, server_config in enabled_servers.items():
                if self._connect_server(server_name, server_config):
                    connected_count += 1
            
            # Initialize RSS news fetcher
            try:
                custom_feeds = self.config.get('rss_feeds', [])
                self.rss_news_fetcher = RSSNewsFetcher(feeds=custom_feeds if custom_feeds else None)
                print(f"📰 RSS news fetcher initialized with {len(self.rss_news_fetcher.feeds)} feeds")
            except Exception as e:
                print(f"⚠️ RSS news fetcher failed to initialize: {e}")
            
            self.status = f"connected_{connected_count}"
            return f"✅ FastMCP connected to {connected_count} servers"
            
        except Exception as e:
            self.status = "failed"
            error_msg = f"❌ FastMCP initialize() crashed: {e}"
            print(error_msg)
            traceback.print_exc()
            return error_msg

    def _connect_server(self, server_name: str, server_config: dict) -> bool:
        """Connect to a single MCP server using FastMCP or fallback"""
        try:
            server_url = server_config.get('url')
            if not server_url:
                print(f"⚠️ No server URL for {server_name}")
                return False
            
            print(f"🔌 Connecting to {server_name} at {server_url}")
            
            # Try FastMCP first
            if FASTMCP_AVAILABLE:
                return self._connect_fastmcp(server_name, server_url, server_config)
            else:
                # Fallback to original MCP SDK
                return self._connect_mcp_sdk(server_name, server_url, server_config)
                
        except Exception as e:
            print(f"❌ Failed to connect {server_name}: {e}")
            return False

    def _connect_fastmcp(self, server_name: str, server_url: str, server_config: dict) -> bool:
        """Connect using FastMCP or direct API"""
        try:
            # Handle authentication
            auth_config = server_config.get('auth', {})
            auth = None
            if auth_config:
                auth_type = auth_config.get('type')
                if auth_type == 'api_key':
                    param = auth_config.get('param', 'apikey')
                    token_env = auth_config.get('token_env')
                    if token_env and os.getenv(token_env):
                        # For AlphaVantage, add API key to URL
                        if 'alphavantage' in server_url.lower():
                            separator = '&' if '?' in server_url else '?'
                            server_url = f"{server_url}{separator}{param}={os.getenv(token_env)}"
                        # For FastMCP Client, we pass auth as a parameter
                        auth = os.getenv(token_env)
            
            # Check if this is a direct API endpoint (not MCP)
            if 'alphavantage.co/query' in server_url:
                # Store direct API connection info
                self.mcp_servers[server_name] = {
                    'type': 'direct_api',
                    'url': server_url,
                    'config': server_config
                }
                print(f"✅ Direct API {server_name} connected")
                return True
            
            # Try FastMCP Client for real MCP servers
            try:
                client = Client(server_url, name=server_name, auth=auth)
                self.mcp_servers[server_name] = {
                    'client': client,
                    'type': 'fastmcp',
                    'url': server_url,
                    'config': server_config
                }
                print(f"✅ FastMCP {server_name} connected")
                return True
            except Exception as e:
                print(f"⚠️ FastMCP failed, trying direct API: {e}")
                # Fallback to direct API
                self.mcp_servers[server_name] = {
                    'type': 'direct_api',
                    'url': server_url,
                    'config': server_config
                }
                print(f"✅ Direct API {server_name} connected (fallback)")
                return True
            
        except Exception as e:
            print(f"❌ Connection failed for {server_name}: {e}")
            return False

    def _connect_mcp_sdk(self, server_name: str, server_url: str, server_config: dict) -> bool:
        """Fallback: Connect using original MCP SDK"""
        try:
            # Determine transport type
            transport_type = server_config.get('transport', 'auto')
            
            if transport_type == 'sse' or ('sse' in server_url.lower()):
                # SSE transport
                transport_ctx = sse_client(server_url)
            else:
                # Streamable HTTP transport
                transport_ctx = streamable_http_client(server_url)
            
            # Create session
            session = ClientSession(transport_ctx.__enter__())
            
            # Initialize session
            asyncio.run(session.initialize())
            
            # Store session
            self.mcp_servers[server_name] = {
                'session': session,
                'transport_ctx': transport_ctx,
                'type': 'mcp_sdk',
                'url': server_url,
                'config': server_config
            }
            
            print(f"✅ MCP SDK {server_name} connected")
            return True
            
        except Exception as e:
            print(f"❌ MCP SDK connection failed for {server_name}: {e}")
            return False

    def _get_server_for_task(self, task_type: str = None):
        """Get appropriate server for a task"""
        if not self.mcp_servers:
            return None
        
        # If specific task type, try to find matching server
        if task_type:
            for server_name, server_info in self.mcp_servers.items():
                server_config = server_info.get('config', {})
                if server_config.get('type') == task_type:
                    return server_name, server_info
        
        # Return first available server
        server_name = list(self.mcp_servers.keys())[0]
        return server_name, self.mcp_servers[server_name]

    async def search_command(self, query: str, max_results: int = 5):
        """Search the web using MCP"""
        try:
            server_name, server_info = self._get_server_for_task('web')
            if not server_info:
                return "❌ No MCP server available"
            
            # Check cache first
            cache_key = f"search:{query}:{max_results}"
            if cache_key in self.research_cache:
                cached_result = self.research_cache[cache_key]
                if datetime.now().isoformat()[:10] in cached_result.get('timestamp', ''):
                    return cached_result['result']
            
            # Perform search based on server type
            if server_info['type'] == 'direct_api':
                result = await self._direct_api_search(server_info, query, max_results)
            elif server_info['type'] == 'fastmcp':
                result = await self._fastmcp_search(server_info['client'], query, max_results)
            else:
                result = await self._mcp_sdk_search(server_info['session'], query, max_results)
            
            # Cache result
            self.research_cache[cache_key] = {
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            return f"❌ Search failed: {e}"

    async def _direct_api_search(self, server_info: dict, query: str, max_results: int):
        """Search using direct API calls"""
        try:
            import httpx
            
            url = server_info['url']
            
            # For AlphaVantage, we need to modify the query
            if 'alphavantage' in url.lower():
                # Use a generic search function
                search_url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={query}&apikey={os.getenv('ALPHAVANTAGE_API_KEY', '')}"
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(search_url)
                    if response.status_code == 200:
                        data = response.json()
                        return f"🔍 Search Results:\n\n{self._format_content(str(data))}"
                    else:
                        return f"❌ Search failed: HTTP {response.status_code}"
            
            return "❌ Direct API search not implemented for this endpoint"
            
        except Exception as e:
            return f"❌ Direct API search failed: {e}"

    async def _direct_api_stock_price(self, server_info: dict, symbol: str):
        """Get stock price using direct API calls"""
        try:
            import httpx
            
            if 'alphavantage' in server_info['url'].lower():
                # Get stock quote
                quote_url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol.upper()}&apikey={os.getenv('ALPHAVANTAGE_API_KEY', '')}"
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(quote_url)
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Format the data nicely
                        if 'Global Quote' in data:
                            quote = data['Global Quote']
                            formatted_data = f"""📈 {symbol.upper()} Stock Data:

• Symbol: {quote.get('01. symbol', 'N/A')}
• Price: ${quote.get('05. price', 'N/A')}
• Change: {quote.get('09. change', 'N/A')}
• Change %: {quote.get('10. change percent', 'N/A')}
• Open: ${quote.get('02. open', 'N/A')}
• High: ${quote.get('03. high', 'N/A')}
• Low: ${quote.get('04. low', 'N/A')}
• Volume: {quote.get('06. volume', 'N/A')}
• Last Trading Day: {quote.get('07. latest trading day', 'N/A')}
• Previous Close: ${quote.get('08. previous close', 'N/A')}"""
                            
                            return formatted_data
                        else:
                            return f"❌ No stock data found for {symbol}"
                    else:
                        return f"❌ Stock price failed: HTTP {response.status_code}"
            
            return "❌ Direct API stock price not implemented for this endpoint"
            
        except Exception as e:
            return f"❌ Direct API stock price failed: {e}"
        """Search using FastMCP client"""
        try:
            # Use async context manager for connection
            async with client:
                # List available tools
                tools = await client.list_tools()
                
                # Find search tool
                search_tool = None
                for tool in tools:  # tools is already a list
                    if 'search' in tool.name.lower() or 'web' in tool.name.lower():
                        search_tool = tool
                        break
                
                if not search_tool:
                    return "❌ No search tool available"
                
                # Call search tool
                result = await client.call_tool(search_tool.name, {
                    'query': query,
                    'max_results': max_results
                })
                
                # Handle CallToolResult object
                if hasattr(result, 'content'):
                    if isinstance(result.content, list):
                        # Format list content more nicely
                        content_items = []
                        for item in result.content:
                            if hasattr(item, 'text'):
                                content_items.append(str(item.text))
                            else:
                                content_items.append(str(item))
                        content_text = '\n\n'.join(content_items)
                    else:
                        content_text = str(result.content)
                    
                    # Clean up the content for better readability
                    content_text = self._format_content(content_text)
                    
                    # Truncate long results to avoid message too long errors
                    if len(content_text) > 3500:
                        content_text = content_text[:3500] + "\n\n... (truncated)"
                    
                    return f"🔍 Search Results:\n\n{content_text}"
                else:
                    result_str = str(result)
                    result_str = self._format_content(result_str)
                    if len(result_str) > 3500:
                        result_str = result_str[:3500] + "\n\n... (truncated)"
                    return f"🔍 Search Results:\n\n{result_str}"
            
        except Exception as e:
            return f"❌ FastMCP search failed: {e}"

    async def _mcp_sdk_search(self, session, query: str, max_results: int):
        """Search using MCP SDK session"""
        try:
            # List available tools
            tools = await session.list_tools()
            
            # Find search tool
            search_tool = None
            for tool in tools.tools:
                if 'search' in tool.name.lower() or 'web' in tool.name.lower():
                    search_tool = tool
                    break
            
            if not search_tool:
                return "❌ No search tool available"
            
            # Call search tool
            result = await session.call_tool(search_tool.name, {
                'query': query,
                'max_results': max_results
            })
            
            return f"🔍 Search Results:\n{json.dumps(result, indent=2)}"
            
        except Exception as e:
            return f"❌ MCP SDK search failed: {e}"

    async def research_command(self, topic: str, depth: str = "standard"):
        """Research a topic using MCP"""
        try:
            server_name, server_info = self._get_server_for_task('research')
            if not server_info:
                return "❌ No MCP server available"
            
            # Perform research
            if server_info['type'] == 'fastmcp':
                result = await self._fastmcp_research(server_info['client'], topic)
            else:
                result = await self._mcp_sdk_research(server_info['session'], topic)
            
            self.last_research = {
                'topic': topic,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            return f"❌ Research failed: {e}"

    async def _fastmcp_research(self, client, topic: str):
        """Research using FastMCP client"""
        try:
            # Use async context manager for connection
            async with client:
                # List available tools
                tools = await client.list_tools()
                
                # Find research tool
                research_tool = None
                for tool in tools:  # tools is already a list
                    if 'research' in tool.name.lower() or 'analyze' in tool.name.lower():
                        research_tool = tool
                        break
                
                if not research_tool:
                    # Fallback to search
                    return await self._fastmcp_search(client, topic, 10)
                
                # Call research tool
                result = await client.call_tool(research_tool.name, {
                    'topic': topic
                })
                
                # Handle CallToolResult object
                if hasattr(result, 'content'):
                    if isinstance(result.content, list):
                        # Format list content more nicely
                        content_items = []
                        for item in result.content:
                            if hasattr(item, 'text'):
                                content_items.append(str(item.text))
                            else:
                                content_items.append(str(item))
                        content_text = '\n\n'.join(content_items)
                    else:
                        content_text = str(result.content)
                    
                    # Clean up the content for better readability
                    content_text = self._format_content(content_text)
                    
                    # Truncate long results to avoid message too long errors
                    if len(content_text) > 3500:
                        content_text = content_text[:3500] + "\n\n... (truncated)"
                    
                    return f"📚 Research Results:\n\n{content_text}"
                else:
                    result_str = str(result)
                    result_str = self._format_content(result_str)
                    if len(result_str) > 3500:
                        result_str = result_str[:3500] + "\n\n... (truncated)"
                    return f"📚 Research Results:\n\n{result_str}"
            
        except Exception as e:
            return f"❌ FastMCP research failed: {e}"

    async def _mcp_sdk_research(self, session, topic: str):
        """Research using MCP SDK session"""
        try:
            # List available tools
            tools = await session.list_tools()
            
            # Find research tool
            research_tool = None
            for tool in tools.tools:
                if 'research' in tool.name.lower() or 'analyze' in tool.name.lower():
                    research_tool = tool
                    break
            
            if not research_tool:
                # Fallback to search
                return await self._mcp_sdk_search(session, topic, 10)
            
            # Call research tool
            result = await session.call_tool(research_tool.name, {
                'topic': topic
            })
            
            return f"📚 Research Results:\n{json.dumps(result, indent=2)}"
            
        except Exception as e:
            return f"❌ MCP SDK research failed: {e}"

    async def get_stock_price(self, symbol: str):
        """Get stock price using financial MCP servers"""
        try:
            server_name, server_info = self._get_server_for_task('finance')
            if not server_info:
                return "❌ No financial MCP server available"
            
            # Get stock price based on server type
            if server_info['type'] == 'direct_api':
                result = await self._direct_api_stock_price(server_info, symbol)
            elif server_info['type'] == 'fastmcp':
                result = await self._fastmcp_stock_price(server_info['client'], symbol)
            else:
                result = await self._mcp_sdk_stock_price(server_info['session'], symbol)
            
            return result
            
        except Exception as e:
            return f"❌ Stock price query failed: {e}"

    async def _fastmcp_stock_price(self, client, symbol: str):
        """Get stock price using FastMCP client"""
        try:
            # Use async context manager for connection
            async with client:
                # List available tools
                tools = await client.list_tools()
                
                # Find stock price tool
                stock_tool = None
                for tool in tools:  # tools is already a list
                    if any(keyword in tool.name.lower() for keyword in ['stock', 'price', 'quote', 'ticker']):
                        stock_tool = tool
                        break
                
                if not stock_tool:
                    return f"❌ No stock price tool available on {client.name}"
                
                # Call stock tool
                result = await client.call_tool(stock_tool.name, {
                    'symbol': symbol.upper()
                })
                
                # Handle CallToolResult object
                if hasattr(result, 'content'):
                    if isinstance(result.content, list):
                        # Format list content more nicely
                        content_items = []
                        for item in result.content:
                            if hasattr(item, 'text'):
                                content_items.append(str(item.text))
                            else:
                                content_items.append(str(item))
                        content_text = '\n\n'.join(content_items)
                    else:
                        content_text = str(result.content)
                    
                    # Clean up the content for better readability
                    content_text = self._format_content(content_text)
                    
                    # Truncate long results to avoid message too long errors
                    if len(content_text) > 3500:
                        content_text = content_text[:3500] + "\n\n... (truncated)"
                    
                    return f"📈 {symbol.upper()} Stock Data:\n\n{content_text}"
                else:
                    result_str = str(result)
                    result_str = self._format_content(result_str)
                    if len(result_str) > 3500:
                        result_str = result_str[:3500] + "\n\n... (truncated)"
                    return f"📈 {symbol.upper()} Stock Data:\n\n{result_str}"
            
        except Exception as e:
            return f"❌ FastMCP stock query failed: {e}"

    async def _mcp_sdk_stock_price(self, session, symbol: str):
        """Get stock price using MCP SDK session"""
        try:
            # List available tools
            tools = await session.list_tools()
            
            # Find stock price tool
            stock_tool = None
            for tool in tools.tools:
                if any(keyword in tool.name.lower() for keyword in ['stock', 'price', 'quote', 'ticker']):
                    stock_tool = tool
                    break
            
            if not stock_tool:
                return f"❌ No stock price tool available"
            
            # Call stock tool
            result = await session.call_tool(stock_tool.name, {
                'symbol': symbol.upper()
            })
            
            return f"📈 {symbol.upper()} Stock Data:\n{json.dumps(result, indent=2)}"
            
        except Exception as e:
            return f"❌ MCP SDK stock query failed: {e}"

    async def get_crypto_price(self, symbol: str):
        """Get crypto price using crypto MCP servers"""
        try:
            # Try to find crypto-specific server
            server_name = None
            server_info = None
            
            for name, info in self.mcp_servers.items():
                if info.get('config', {}).get('type') == 'crypto':
                    server_name = name
                    server_info = info
                    break
            
            if not server_info:
                # Fallback to any finance server
                server_name, server_info = self._get_server_for_task('finance')
            
            if not server_info:
                return "❌ No crypto/finance MCP server available"
            
            # Get crypto price
            if server_info['type'] == 'fastmcp':
                result = await self._fastmcp_crypto_price(server_info['client'], symbol)
            else:
                result = await self._mcp_sdk_crypto_price(server_info['session'], symbol)
            
            return result
            
        except Exception as e:
            return f"❌ Crypto price query failed: {e}"

    async def _fastmcp_crypto_price(self, client, symbol: str):
        """Get crypto price using FastMCP client"""
        try:
            # Use async context manager for connection
            async with client:
                # List available tools
                tools = await client.list_tools()
                
                # Find crypto price tool
                crypto_tool = None
                for tool in tools:  # tools is already a list
                    if any(keyword in tool.name.lower() for keyword in ['crypto', 'bitcoin', 'ethereum', 'token']):
                        crypto_tool = tool
                        break
                
                if not crypto_tool:
                    return f"❌ No crypto price tool available on {client.name}"
                
                # Call crypto tool
                result = await client.call_tool(crypto_tool.name, {
                    'symbol': symbol.upper()
                })
                
                # Handle CallToolResult object
                if hasattr(result, 'content'):
                    if isinstance(result.content, list):
                        # Format list content more nicely
                        content_items = []
                        for item in result.content:
                            if hasattr(item, 'text'):
                                content_items.append(str(item.text))
                            else:
                                content_items.append(str(item))
                        content_text = '\n\n'.join(content_items)
                    else:
                        content_text = str(result.content)
                    
                    # Clean up the content for better readability
                    content_text = self._format_content(content_text)
                    
                    # Truncate long results to avoid message too long errors
                    if len(content_text) > 3500:
                        content_text = content_text[:3500] + "\n\n... (truncated)"
                    
                    return f"₿ {symbol.upper()} Crypto Data:\n\n{content_text}"
                else:
                    result_str = str(result)
                    result_str = self._format_content(result_str)
                    if len(result_str) > 3500:
                        result_str = result_str[:3500] + "\n\n... (truncated)"
                    return f"₿ {symbol.upper()} Crypto Data:\n\n{result_str}"
            
        except Exception as e:
            return f"❌ FastMCP crypto query failed: {e}"

    async def _mcp_sdk_crypto_price(self, session, symbol: str):
        """Get crypto price using MCP SDK session"""
        try:
            # List available tools
            tools = await session.list_tools()
            
            # Find crypto price tool
            crypto_tool = None
            for tool in tools.tools:
                if any(keyword in tool.name.lower() for keyword in ['crypto', 'bitcoin', 'ethereum', 'token']):
                    crypto_tool = tool
                    break
            
            if not crypto_tool:
                return f"❌ No crypto price tool available"
            
            # Call crypto tool
            result = await session.call_tool(crypto_tool.name, {
                'symbol': symbol.upper()
            })
            
            return f"₿ {symbol.upper()} Crypto Data:\n{json.dumps(result, indent=2)}"
            
        except Exception as e:
            return f"❌ MCP SDK crypto query failed: {e}"

    def status_command(self):
        """Show MCP connection status"""
        if not self.mcp_servers:
            return "❌ No MCP servers connected"
        
        status_lines = [f"✅ FastMCP Status ({len(self.mcp_servers)} servers):"]
        
        for server_name, server_info in self.mcp_servers.items():
            server_type = server_info['type']
            url = server_info['url']
            
            # Mask API keys in URL
            if 'apikey=' in url.lower():
                masked_url = url.split('apikey=')[0] + 'apikey=***MASKED***'
            else:
                masked_url = url
            
            status_lines.append(f"  • {server_name} ({server_type}): {masked_url}")
        
        if self.last_research:
            status_lines.append(f"\n📚 Last Research: {self.last_research['topic']} ({self.last_research['timestamp']})")
        
        return "\n".join(status_lines)

    async def analyze_command(self, query: str, analysis_type: str = "standard"):
        """Analyze data using MCP servers"""
        try:
            # Try to determine if this is a stock/crypto query
            query_lower = query.lower()
            
            if any(keyword in query_lower for keyword in ['stock', 'price', 'share', 'nasdaq', 'nyse']):
                # Stock analysis
                symbol = self._extract_symbol(query)
                if symbol:
                    return await self.get_stock_price(symbol)
            
            elif any(keyword in query_lower for keyword in ['crypto', 'bitcoin', 'ethereum', 'btc', 'eth']):
                # Crypto analysis
                symbol = self._extract_symbol(query)
                if symbol:
                    return await self.get_crypto_price(symbol)
            
            # Default to research
            return await self.research_command(query)
            
        except Exception as e:
            return f"❌ Analysis failed: {e}"
    
    def _extract_symbol(self, query: str) -> str:
        """Extract stock/crypto symbol from query"""
        import re
        # Look for uppercase symbols (2-5 letters)
        symbols = re.findall(r'\b[A-Z]{2,5}\b', query)
        return symbols[0] if symbols else None

    def _format_content(self, content: str) -> str:
        """Format content for better readability"""
        try:
            # Remove excessive whitespace
            content = ' '.join(content.split())
            
            # Add line breaks for better readability
            content = content.replace('. ', '.\n• ')
            content = content.replace('! ', '!\n• ')
            content = content.replace('? ', '?\n• ')
            
            # Format JSON-like content
            if content.startswith('{') or content.startswith('['):
                try:
                    import json
                    parsed = json.loads(content)
                    return json.dumps(parsed, indent=2)
                except:
                    pass
            
            # Add bullet points for lists
            lines = content.split('\n')
            formatted_lines = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('•') and not line.startswith('-'):
                    # Check if it looks like a list item
                    if any(char in line for char in [':', '-', '+', '*']):
                        line = f"• {line}"
                formatted_lines.append(line)
            
            return '\n'.join(formatted_lines)
            
        except Exception:
            return content

    async def query_news(self, query: str, limit: int = 10) -> list:
        """
        Query news from RSS feeds
        
        Args:
            query: Search query
            limit: Maximum number of articles
            
        Returns:
            List of news articles
        """
        if not self.rss_news_fetcher:
            print("⚠️ RSS news fetcher not initialized")
            return []
        
        try:
            # RSS fetcher is synchronous, run it directly
            articles = self.rss_news_fetcher.fetch_news(query, limit=limit)
            return articles
        except Exception as e:
            print(f"❌ Error fetching news: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_commands(self):
        """Return available commands"""
        return {
            'mcp_status': self.status_command,
            'mcp_search': self.search_command,
            'mcp_research': self.research_command,
            'mcp_analyze': self.analyze_command,
            'mcp_stock_price': self.get_stock_price,
            'mcp_crypto_price': self.get_crypto_price,
            'query_news': self.query_news,
        }

    def cleanup(self):
        """Cleanup MCP connections"""
        try:
            for server_name, server_info in self.mcp_servers.items():
                try:
                    if server_info['type'] == 'fastmcp':
                        # FastMCP cleanup
                        client = server_info['client']
                        if hasattr(client, 'close'):
                            asyncio.run(client.close())
                    else:
                        # MCP SDK cleanup
                        transport_ctx = server_info['transport_ctx']
                        if hasattr(transport_ctx, '__exit__'):
                            transport_ctx.__exit__(None, None, None)
                except Exception as e:
                    print(f"⚠️ Error cleaning up {server_name}: {e}")
            
            self.mcp_servers.clear()
            print("✅ FastMCP cleanup complete")
            
        except Exception as e:
            print(f"⚠️ FastMCP cleanup error: {e}")
