"""
MCP Plugin - Model Context Protocol Integration for AlleyBot
Provides web browsing, research, and self-improvement capabilities
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
from plugin_manager import AlleyBotPlugin

# Add MCP client to path
try:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from mcp_client import MCPClient, get_mcp_client, init_mcp, cleanup_mcp
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️ MCP client not available")


class MCPPlugin(AlleyBotPlugin):
    """MCP integration plugin for web access and self-improvement"""
    
    def __init__(self, config):
        super().__init__(config)
        self.name = "mcp"
        self.version = "1.0.0"
        self.description = "Model Context Protocol - Web browsing and research"
        self.mcp_connected = False
        self.last_research = None
        self.research_cache = {}
        self.mcp_client = None
        
    def initialize(self, api, core):
        """Initialize MCP plugin"""
        super().initialize(api, core)
        
        if not MCP_AVAILABLE:
            print("⚠️  MCP plugin disabled - client not available")
            return
        
        print("🌐 Initializing MCP plugin...")
        
        # Get MCP server URL from config or env
        mcp_url = self.config.get('mcp_server_url') or os.getenv('MCP_SERVER_URL', 'http://localhost:3000')
        
        # Initialize MCP connection
        try:
            self.mcp_client = get_mcp_client(mcp_url)
            self.mcp_connected = self.mcp_client.connect()
            
            if self.mcp_connected:
                print("✅ MCP plugin initialized - Web access available")
            else:
                print("⚠️  MCP plugin initialized - Web access limited (server not found)")
                print(f"    Server: {mcp_url}")
                
        except Exception as e:
            print(f"⚠️  MCP initialization failed: {e}")
            self.mcp_connected = False
    
    def cleanup(self):
        """Cleanup MCP plugin"""
        if self.mcp_connected and self.mcp_client:
            try:
                self.mcp_client.disconnect()
            except Exception as e:
                print(f"❌ MCP cleanup failed: {e}")
        
        print("🌐 MCP plugin cleaned up")
    
    def get_commands(self):
        """Return MCP commands"""
        return {
            'mcp_search': self.search_command,
            'mcp_analyze': self.analyze_command,
            'mcp_research': self.research_command,
            'mcp_fetch': self.fetch_command,
            'mcp_improve': self.improve_command,
            'mcp_status': self.status_command
        }
    
    def get_tasks(self):
        """Return MCP scheduled tasks"""
        return {
            'mcp_self_improve': {
                'schedule': '0 */6 * * *',  # Every 6 hours
                'function': self._self_improve_heartbeat
            }
        }
    
    def search_command(self, query, max_results=10):
        """Search the web using MCP"""
        if not self.mcp_connected or not self.mcp_client:
            return "❌ MCP not connected - web search unavailable"
        
        try:
            result = self.mcp_client.search_web(query, int(max_results))
            
            # Cache the search
            self.last_research = {
                'query': query,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            if 'error' in result:
                return f"⚠️ Search warning: {result['error']}\n\nResults: {result.get('results', [])}"
            
            results = result.get('results', [])
            output = f"🔍 Web Search: {query}\n"
            output += f"Found {len(results)} results\n\n"
            for i, r in enumerate(results[:5], 1):
                output += f"{i}. {r.get('title', 'No title')}\n"
                output += f"   {r.get('url', 'No URL')}\n"
                output += f"   {r.get('snippet', '')[:100]}...\n\n"
            return output
            
        except Exception as e:
            return f"❌ Search failed: {e}"
    
    def analyze_command(self, content, analysis_type="summary"):
        """Analyze content using MCP"""
        if not self.mcp_connected or not self.mcp_client:
            return "❌ MCP not connected - content analysis unavailable"
        
        try:
            result = self.mcp_client.analyze_content(content, analysis_type)
            
            if 'error' in result:
                return f"⚠️ Analysis warning: {result['error']}"
            
            analysis = result.get('analysis', result)
            return f"🧠 Content Analysis ({analysis_type}):\n\n{analysis}"
            
        except Exception as e:
            return f"❌ Analysis failed: {e}"
    
    def research_command(self, topic, depth="medium"):
        """Deep research using MCP"""
        if not self.mcp_connected or not self.mcp_client:
            return "❌ MCP not connected - research unavailable"
        
        try:
            # First search for the topic
            search_result = self.mcp_client.search_web(topic, max_results=10)
            
            if 'error' in search_result:
                return f"⚠️ Research warning: {search_result['error']}"
            
            results = search_result.get('results', [])
            
            # Cache research
            self.research_cache[topic] = {
                'result': results,
                'timestamp': datetime.now().isoformat(),
                'depth': depth
            }
            
            output = f"🔬 Research Report: {topic}\n"
            output += f"Depth: {depth} | Sources: {len(results)}\n\n"
            
            for i, r in enumerate(results[:5], 1):
                output += f"{i}. {r.get('title', 'No title')}\n"
                output += f"   URL: {r.get('url', 'No URL')}\n"
                output += f"   {r.get('snippet', 'No description')[:150]}...\n\n"
            
            return output
            
        except Exception as e:
            return f"❌ Research failed: {e}"
    
    def fetch_command(self, url):
        """Fetch webpage content using MCP. Usage: mcp_fetch <url>"""
        if not self.mcp_connected or not self.mcp_client:
            return "❌ MCP not connected - fetch unavailable"
        
        try:
            result = self.mcp_client.fetch_webpage(url)
            
            if 'error' in result:
                return f"⚠️ Fetch warning: {result['error']}"
            
            title = result.get('title', 'No title')
            text = result.get('text', 'No content')[:500]
            
            return f"� Fetched: {title}\nURL: {url}\n\n{text}..."
            
        except Exception as e:
            return f"❌ Fetch failed: {e}"
    
    def improve_command(self):
        """Self-improvement research using MCP"""
        if not self.mcp_connected or not self.mcp_client:
            return "❌ MCP not connected - self-improvement unavailable"
        
        try:
            # Research AI agent trends
            trends = self.research_command("AI agent automation trends 2026", "quick")
            
            # Search for improvement opportunities  
            search_result = self.mcp_client.search_web("AI agent best practices 2026", max_results=5)
            
            return f"🚀 Self-Improvement Research:\n\n{trends}\n\nBest Practices:\n{search_result}"
            
        except Exception as e:
            return f"❌ Self-improvement failed: {e}"
    
    def status_command(self):
        """Show MCP status"""
        status = "🌐 MCP Plugin Status\n"
        status += "=" * 40 + "\n\n"
        status += f"Connected: {'✅ Yes' if self.mcp_connected else '❌ No'}\n"
        status += f"Client Available: {'✅ Yes' if MCP_AVAILABLE else '❌ No'}\n"
        
        if self.mcp_client and hasattr(self.mcp_client, 'server_url'):
            status += f"Server URL: {self.mcp_client.server_url}\n"
        
        if self.last_research:
            status += f"\nLast Search: {self.last_research.get('query', 'None')}\n"
            status += f"Time: {self.last_research.get('timestamp', 'Unknown')[:16]}\n"
        
        status += f"\nCached Research: {len(self.research_cache)} topics\n"
        
        if self.research_cache:
            status += "\n📚 Recent Research:\n"
            for topic in list(self.research_cache.keys())[-5:]:
                status += f"  • {topic}\n"
        
        if not self.mcp_connected:
            status += "\n💡 To enable MCP:\n"
            status += "  1. Install an MCP server (e.g., npm install -g @modelcontextprotocol/server-brave)\n"
            status += "  2. Start the server on port 3000\n"
            status += "  3. Or set MCP_SERVER_URL env var to your server URL\n"
        
        return status
    
    def _self_improve_heartbeat(self):
        """Scheduled self-improvement heartbeat"""
        if not self.mcp_connected:
            print("🌐 MCP not connected - skipping self-improvement")
            return
        
        print("🌐 MCP self-improvement heartbeat...")
        
        try:
            # Research AI agent trends
            trends = self.research_command("AI agent automation trends 2026", "quick")
            
            # Search for new opportunities
            opportunities = self.search_command("AI agent opportunities Base L2", 5)
            
            # Analyze and save insights
            insights = f"Trends: {trends}\n\nOpportunities: {opportunities}"
            
            # Save to memory
            self.core.save_memory('mcp_insights', {
                'insights': insights,
                'timestamp': datetime.now().isoformat()
            })
            
            print("✅ MCP self-improvement complete")
            
        except Exception as e:
            print(f"❌ MCP self-improvement failed: {e}")
    
    def get_research_for_content(self, topic: str) -> str:
        """Get research for content creation"""
        if topic in self.research_cache:
            return self.research_cache[topic]['result']
        
        # Research new topic
        result = self.research_command(topic, "medium")
        return result if not result.startswith("❌") else ""
