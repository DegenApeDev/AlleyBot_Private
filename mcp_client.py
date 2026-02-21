"""
MCP Client for AlleyBot
Model Context Protocol client for connecting to MCP servers.
Provides web browsing, research, and data fetching capabilities.
"""
import json
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

class MCPClient:
    """
    Model Context Protocol Client
    Connects to MCP servers for web access, research, and data fetching.
    """
    
    def __init__(self, server_url: str = None):
        self.server_url = server_url  # No default - require explicit URL
        self.connected = False
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "AlleyBot-MCP-Client/1.0"
        })
        self._cache = {}
        self._cache_ttl = timedelta(minutes=30)
        
    def connect(self) -> bool:
        """Connect to MCP server and verify connection"""
        if not self.server_url:
            print("⚠️ No server URL provided to MCP client")
            self.connected = False
            return False
            
        try:
            # Try to ping the MCP server
            response = self.session.get(
                f"{self.server_url}/health",
                timeout=10
            )
            self.connected = response.status_code == 200
            if self.connected:
                print(f"✅ MCP client connected to {self.server_url}")
            return self.connected
        except Exception as e:
            print(f"⚠️ MCP connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from MCP server"""
        self.connected = False
        self.session.close()
        print("🔌 MCP client disconnected")
    
    def search_web(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Search the web using MCP server.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            Search results with title, url, snippet
        """
        if not self.connected:
            return {"error": "MCP not connected", "results": []}
        
        cache_key = f"search:{query}:{max_results}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now() - cached['time'] < self._cache_ttl:
                return cached['data']
        
        try:
            response = self.session.post(
                f"{self.server_url}/tools/search",
                json={"query": query, "max_results": max_results},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self._cache[cache_key] = {
                    'time': datetime.now(),
                    'data': data
                }
                return data
            else:
                return {"error": f"Search failed: {response.status_code}", "results": []}
                
        except Exception as e:
            return {"error": f"Search error: {e}", "results": []}
    
    def fetch_webpage(self, url: str) -> Dict[str, Any]:
        """
        Fetch and extract content from a webpage.
        
        Args:
            url: URL to fetch
            
        Returns:
            Page content with title, text, links
        """
        if not self.connected:
            return {"error": "MCP not connected"}
        
        cache_key = f"fetch:{url}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.now() - cached['time'] < self._cache_ttl:
                return cached['data']
        
        try:
            response = self.session.post(
                f"{self.server_url}/tools/fetch",
                json={"url": url},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self._cache[cache_key] = {
                    'time': datetime.now(),
                    'data': data
                }
                return data
            else:
                return {"error": f"Fetch failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Fetch error: {e}"}
    
    def analyze_content(self, content: str, analysis_type: str = "summary") -> Dict[str, Any]:
        """
        Analyze content using MCP server's AI capabilities.
        
        Args:
            content: Content to analyze
            analysis_type: Type of analysis (summary, sentiment, keywords, etc.)
            
        Returns:
            Analysis results
        """
        if not self.connected:
            return {"error": "MCP not connected"}
        
        try:
            response = self.session.post(
                f"{self.server_url}/tools/analyze",
                json={"content": content, "type": analysis_type},
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Analysis failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Analysis error: {e}"}
    
    def execute_skill(self, skill_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a skill on the MCP server.
        
        Args:
            skill_name: Name of the skill to execute
            params: Skill parameters
            
        Returns:
            Skill execution results
        """
        if not self.connected:
            return {"error": "MCP not connected"}
        
        try:
            response = self.session.post(
                f"{self.server_url}/skills/{skill_name}",
                json=params,
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Skill execution failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Skill execution error: {e}"}
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get MCP server information and available tools/skills"""
        if not self.connected:
            return {"error": "MCP not connected"}
        
        try:
            response = self.session.get(
                f"{self.server_url}/info",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Info request failed: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Info request error: {e}"}
    
    def clear_cache(self):
        """Clear the response cache"""
        self._cache.clear()
        print("🧹 MCP cache cleared")


# Global MCP client instance
_mcp_client = None

def get_mcp_client(server_url: str = None) -> MCPClient:
    """Get or create global MCP client instance"""
    global _mcp_client
    if _mcp_client is None or (_mcp_client.server_url != server_url and server_url):
        _mcp_client = MCPClient(server_url)
    return _mcp_client

def init_mcp(server_url: str = None) -> bool:
    """Initialize MCP client and connect to server"""
    client = get_mcp_client(server_url)
    return client.connect()

def cleanup_mcp():
    """Cleanup MCP client connection"""
    global _mcp_client
    if _mcp_client:
        _mcp_client.disconnect()
        _mcp_client = None

# Backwards compatibility
mcp_client = get_mcp_client()
