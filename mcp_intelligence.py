#!/usr/bin/env python3
"""
MCP Intelligence Engine - Smart decision making for when to use MCP
"""
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

class MCPIntelligence:
    """Smart decision engine for MCP usage"""
    
    def __init__(self):
        self.usage_history = []
        self.last_mcp_usage = {}
        self.cost_tracker = {
            'search_count': 0,
            'analyze_count': 0,
            'research_count': 0,
            'monitor_count': 0
        }
        self.performance_metrics = {
            'successful_researches': 0,
            'failed_researches': 0,
            'valuable_insights': 0
        }
        
    def should_use_mcp(self, context: str, priority: str = "medium") -> bool:
        """Decide if MCP should be used based on context and priority"""
        
        # Check if MCP is available
        if not self._mcp_available():
            return False
        
        # Rate limiting check
        if self._is_rate_limited():
            return False
        
        # Context-based decision
        decision = self._analyze_context(context, priority)
        
        if decision['use_mcp']:
            # Track usage
            self._track_usage(context, decision['action'])
            return True
        
        return False
    
    def get_mcp_action(self, context: str, priority: str = "medium") -> Dict[str, Any]:
        """Get recommended MCP action"""
        
        action_map = {
            'content_creation': {
                'action': 'research',
                'query': f"AI agent content trends {datetime.now().strftime('%Y-%m')}",
                'analysis_type': 'trends'
            },
            'bounty_hunting': {
                'action': 'search',
                'query': "AI agent automation bounties Base L2 high value",
                'max_results': 10
            },
            'market_analysis': {
                'action': 'research',
                'query': f"AI agent market analysis {datetime.now().strftime('%Y-%m-%d')}",
                'depth': 'medium'
            },
            'competitive_intel': {
                'action': 'monitor',
                'sources': ['https://moltx.io', 'https://moltroad.com'],
                'keywords': ['AlleyBot', 'AI agent', 'automation']
            },
            'self_improvement': {
                'action': 'improve',
                'query': None
            }
        }
        
        # Determine action based on context
        if any(keyword in context.lower() for keyword in ['content', 'post', 'write', 'create']):
            return action_map['content_creation']
        elif any(keyword in context.lower() for keyword in ['bounty', 'earn', 'work', 'job']):
            return action_map['bounty_hunting']
        elif any(keyword in context.lower() for keyword in ['market', 'trend', 'analysis', 'compete']):
            return action_map['market_analysis']
        elif any(keyword in context.lower() for keyword in ['monitor', 'track', 'watch']):
            return action_map['competitive_intel']
        elif any(keyword in context.lower() for keyword in ['improve', 'better', 'optimize', 'enhance']):
            return action_map['self_improvement']
        else:
            # Default action based on priority
            if priority == "high":
                return action_map['bounty_hunting']
            elif priority == "low":
                return action_map['content_creation']
            else:
                return action_map['market_analysis']
    
    def _mcp_available(self) -> bool:
        """Check if MCP is available and configured"""
        try:
            # Check for API keys
            has_openai = bool(os.getenv('OPENAI_API_KEY'))
            has_gemini = bool(os.getenv('GOOGLE_API_KEY'))
            
            return has_openai or has_gemini
            
        except Exception:
            return False
    
    def _is_rate_limited(self) -> bool:
        """Check if we're rate limited"""
        current_time = datetime.now()
        
        # Check recent usage (last hour)
        recent_usage = [
            usage for usage in self.usage_history
            if datetime.fromisoformat(usage['timestamp']) > current_time - timedelta(hours=1)
        ]
        
        # Limit to 20 MCP calls per hour
        if len(recent_usage) >= 20:
            return True
        
        # Limit to 5 calls per 10 minutes
        very_recent_usage = [
            usage for usage in self.usage_history
            if datetime.fromisoformat(usage['timestamp']) > current_time - timedelta(minutes=10)
        ]
        
        if len(very_recent_usage) >= 5:
            return True
        
        return False
    
    def _analyze_context(self, context: str, priority: str) -> Dict[str, Any]:
        """Analyze context to decide MCP usage"""
        
        # High priority contexts always use MCP
        if priority == "high":
            return {
                'use_mcp': True,
                'action': self.get_mcp_action(context, priority),
                'reason': 'High priority task requires web intelligence'
            }
        
        # Low priority contexts are more selective
        if priority == "low":
            # Only use MCP for specific valuable contexts
            valuable_keywords = ['bounty', 'earn', 'market', 'trend', 'opportunity']
            if any(keyword in context.lower() for keyword in valuable_keywords):
                return {
                    'use_mcp': True,
                    'action': self.get_mcp_action(context, priority),
                    'reason': 'Low priority but high value context'
                }
            else:
                return {
                    'use_mcp': False,
                    'reason': 'Low priority and low value context'
                }
        
        # Medium priority - use MCP for research and analysis
        medium_keywords = ['research', 'analyze', 'trend', 'data', 'insight']
        if any(keyword in context.lower() for keyword in medium_keywords):
            return {
                'use_mcp': True,
                'action': self.get_mcp_action(context, priority),
                'reason': 'Medium priority research/analysis task'
            }
        
        # Check if we have recent successful MCP usage
        if self._has_recent_success():
            return {
                'use_mcp': True,
                'action': self.get_mcp_action(context, priority),
                'reason': 'Recent MCP success indicates good performance'
            }
        
        return {
            'use_mcp': False,
            'reason': 'Medium priority without clear MCP value'
        }
    
    def _has_recent_success(self) -> bool:
        """Check if we had recent successful MCP usage"""
        current_time = datetime.now()
        
        recent_usage = [
            usage for usage in self.usage_history
            if datetime.fromisoformat(usage['timestamp']) > current_time - timedelta(hours=2)
        ]
        
        # Check if we had successful results
        successful_usage = [
            usage for usage in recent_usage
            if usage.get('success', False)
        ]
        
        return len(successful_usage) >= 2
    
    def _track_usage(self, context: str, action: Dict[str, Any]):
        """Track MCP usage for analytics"""
        usage_entry = {
            'timestamp': datetime.now().isoformat(),
            'context': context,
            'action': action['action'],
            'success': None  # Will be updated later
        }
        
        self.usage_history.append(usage_entry)
        
        # Update cost tracker
        action_type = action.get('action', 'unknown')
        if action_type == 'search':
            self.cost_tracker['search_count'] += 1
        elif action_type == 'analyze':
            self.cost_tracker['analyze_count'] += 1
        elif action_type == 'research':
            self.cost_tracker['research_count'] += 1
        elif action_type == 'monitor':
            self.cost_tracker['monitor_count'] += 1
    
    def record_mcp_result(self, context: str, success: bool, value: str = ""):
        """Record MCP result for performance tracking"""
        # Find the most recent usage for this context
        for usage in reversed(self.usage_history):
            if usage['context'] == context and usage.get('success') is None:
                usage['success'] = success
                usage['value'] = value
                
                # Update performance metrics
                if success:
                    self.performance_metrics['successful_researches'] += 1
                    if 'insight' in value.lower() or 'opportunity' in value.lower():
                        self.performance_metrics['valuable_insights'] += 1
                else:
                    self.performance_metrics['failed_researches'] += 1
                break
    
    def get_usage_stats(self) -> str:
        """Get MCP usage statistics"""
        current_time = datetime.now()
        
        # Last 24 hours
        day_ago = current_time - timedelta(hours=24)
        daily_usage = [
            usage for usage in self.usage_history
            if datetime.fromisoformat(usage['timestamp']) > day_ago
        ]
        
        stats = f"📊 MCP Usage Statistics:\n\n"
        stats += f"📈 Last 24 hours: {len(daily_usage)} calls\n"
        stats += f"🔍 Total searches: {self.cost_tracker['search_count']}\n"
        stats += f"🧠 Total analyses: {self.cost_tracker['analyze_count']}\n"
        stats += f"🔬 Total research: {self.cost_tracker['research_count']}\n"
        stats += f"📡 Total monitors: {self.cost_tracker['monitor_count']}\n\n"
        
        stats += f"✅ Successful: {self.performance_metrics['successful_researches']}\n"
        stats += f"❌ Failed: {self.performance_metrics['failed_researches']}\n"
        stats += f"💎 Valuable insights: {self.performance_metrics['valuable_insights']}\n"
        
        if daily_usage:
            success_rate = len([u for u in daily_usage if u.get('success', False)]) / len(daily_usage) * 100
            stats += f"📊 Success rate (24h): {success_rate:.1f}%\n"
        
        return stats
    
    def get_smart_recommendations(self) -> List[str]:
        """Get smart recommendations based on usage patterns"""
        recommendations = []
        
        # Analyze usage patterns
        if self.cost_tracker['research_count'] > self.cost_tracker['search_count']:
            recommendations.append("🔍 Consider more targeted searches - research is expensive")
        
        if self.performance_metrics['successful_researches'] > self.performance_metrics['failed_researches']:
            recommendations.append("✅ MCP is performing well - consider increasing usage")
        else:
            recommendations.append("⚠️ MCP success rate is low - consider using it less")
        
        # Check for underutilized capabilities
        if self.cost_tracker['monitor_count'] == 0:
            recommendations.append("📡 Try monitoring competitors - valuable intelligence")
        
        if self.cost_tracker['analyze_count'] < 5:
            recommendations.append("🧠 Use MCP analysis for content optimization")
        
        return recommendations

# Global MCP intelligence instance
mcp_intelligence = MCPIntelligence()
