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
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from mcp_client import mcp_client, init_mcp, cleanup_mcp

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
        
    def initialize(self, api, core):
        """Initialize MCP plugin"""
        super().initialize(api, core)
        
        print("🌐 Initializing MCP plugin...")
        
        # Initialize MCP connection
        try:
            # Run async initialization
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.mcp_connected = loop.run_until_complete(init_mcp())
            loop.close()
            
            if self.mcp_connected:
                print("✅ MCP plugin initialized - Web access available")
            else:
                print("⚠️  MCP plugin initialized - Web access limited")
                
        except Exception as e:
            print(f"❌ MCP initialization failed: {e}")
            self.mcp_connected = False
    
    def cleanup(self):
        """Cleanup MCP plugin"""
        if self.mcp_connected:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(cleanup_mcp())
                loop.close()
            except Exception as e:
                print(f"❌ MCP cleanup failed: {e}")
        
        print("🌐 MCP plugin cleaned up")
    
    def get_commands(self):
        """Return MCP commands"""
        return {
            'mcp_search': self.search_command,
            'mcp_analyze': self.analyze_command,
            'mcp_research': self.research_command,
            'mcp_monitor': self.monitor_command,
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
        if not self.mcp_connected:
            return "❌ MCP not connected - web search unavailable"
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                mcp_client.search_web(query, int(max_results))
            )
            loop.close()
            
            # Cache the search
            self.last_research = {
                'query': query,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
            return f"🔍 Web Search Results:\n\n{result}"
            
        except Exception as e:
            return f"❌ Search failed: {e}"
    
    def analyze_command(self, content, analysis_type="insights"):
        """Analyze content using MCP"""
        if not self.mcp_connected:
            return "❌ MCP not connected - content analysis unavailable"
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                mcp_client.analyze_content(content, analysis_type)
            )
            loop.close()
            
            return f"🧠 Content Analysis:\n\n{result}"
            
        except Exception as e:
            return f"❌ Analysis failed: {e}"
    
    def research_command(self, topic, depth="medium"):
        """Deep research using MCP"""
        if not self.mcp_connected:
            return "❌ MCP not connected - research unavailable"
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                mcp_client.research_topic(topic, depth)
            )
            loop.close()
            
            # Cache research
            self.research_cache[topic] = {
                'result': result,
                'timestamp': datetime.now().isoformat(),
                'depth': depth
            }
            
            return f"🔬 Research Report:\n\n{result}"
            
        except Exception as e:
            return f"❌ Research failed: {e}"
    
    def monitor_command(self, sources, keywords=None):
        """Monitor web sources"""
        if not self.mcp_connected:
            return "❌ MCP not connected - monitoring unavailable"
        
        # Parse sources (comma-separated)
        source_list = [s.strip() for s in sources.split(',')] if isinstance(sources, str) else sources
        keyword_list = [k.strip() for k in keywords.split(',')] if keywords else []
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                mcp_client.monitor_sources(source_list, keyword_list)
            )
            loop.close()
            
            return f"📡 Monitoring Results:\n\n{result}"
            
        except Exception as e:
            return f"❌ Monitoring failed: {e}"
    
    def improve_command(self):
        """Self-improvement using MCP"""
        if not self.mcp_connected:
            return "❌ MCP not connected - self-improvement unavailable"
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                mcp_client.improve_alleybot()
            )
            loop.close()
            
            return f"🚀 Self-Improvement Analysis:\n\n{result}"
            
        except Exception as e:
            return f"❌ Self-improvement failed: {e}"
    
    def status_command(self):
        """Show MCP status"""
        status = "🌐 MCP Plugin Status:\n\n"
        status += f"Connected: {'✅ Yes' if self.mcp_connected else '❌ No'}\n"
        status += f"Last Search: {self.last_research.get('query', 'None') if self.last_research else 'None'}\n"
        status += f"Cached Research: {len(self.research_cache)} topics\n"
        
        if self.research_cache:
            status += "\n📚 Cached Research Topics:\n"
            for topic in list(self.research_cache.keys())[-5:]:  # Show last 5
                status += f"  • {topic}\n"
        
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
