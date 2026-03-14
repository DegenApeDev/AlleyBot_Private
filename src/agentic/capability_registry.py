"""
Capability Registry - Maps plugins to concrete actions AlleyBot can take

This is the missing piece that tells AlleyBot what he can actually do.
Maps loaded plugins → available actions with metadata for decision-making.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ActionCapability:
    """Represents a concrete action AlleyBot can take"""
    id: str                          # Unique action ID (e.g., "moltx_post")
    plugin: str                      # Source plugin (e.g., "moltx")
    action_type: str                 # Action category (e.g., "post", "reply", "engage")
    description: str                 # Human-readable description
    platform: str                    # Platform name (e.g., "MoltX", "MoltChan")
    domain: str                      # Domain (social, content, analysis, market, etc.)
    risk_level: str                  # low, medium, high
    trust_tier: str                  # low, medium, high
    requires: List[str]              # Required conditions (e.g., ["api_key", "wallet"])
    cooldown_minutes: int = 0        # Cooldown between uses
    confidence_threshold: float = 0.35  # Min confidence to execute
    metadata: Dict[str, Any] = None  # Additional metadata
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CapabilityRegistry:
    """
    Central registry of all actions AlleyBot can perform.
    
    Scans loaded plugins and builds a comprehensive capability map.
    """
    
    def __init__(self, plugin_manager=None):
        self.plugin_manager = plugin_manager
        self.capabilities: Dict[str, ActionCapability] = {}
        self._last_scan = None
        
        if plugin_manager:
            self.scan_plugins()
    
    def scan_plugins(self):
        """Scan loaded plugins and register their capabilities"""
        if not self.plugin_manager:
            logger.warning("No plugin_manager available for capability scan")
            return
        
        logger.info("🔍 Scanning plugins for capabilities...")
        
        # Get loaded plugins
        loaded_plugins = self.plugin_manager.list_loaded() if hasattr(self.plugin_manager, 'list_loaded') else []
        
        for plugin_name in loaded_plugins:
            try:
                self._register_plugin_capabilities(plugin_name)
            except Exception as e:
                logger.warning(f"Failed to register capabilities for {plugin_name}: {e}")
        
        logger.info(f"✅ Registered {len(self.capabilities)} capabilities from {len(loaded_plugins)} plugins")
    
    def _register_plugin_capabilities(self, plugin_name: str):
        """Register capabilities for a specific plugin"""
        
        # MoltX capabilities
        if plugin_name == 'moltx':
            self.register(ActionCapability(
                id='moltx_post',
                plugin='moltx',
                action_type='post',
                description='Create a new post on MoltX',
                platform='MoltX',
                domain='social',
                risk_level='low',
                trust_tier='medium',
                requires=['moltx_api_key'],
                cooldown_minutes=30,
                metadata={'max_length': 280}
            ))
            
            self.register(ActionCapability(
                id='moltx_reply',
                plugin='moltx',
                action_type='reply',
                description='Reply to a MoltX post',
                platform='MoltX',
                domain='social',
                risk_level='low',
                trust_tier='medium',
                requires=['moltx_api_key'],
                cooldown_minutes=10,
            ))
            
            self.register(ActionCapability(
                id='moltx_like',
                plugin='moltx',
                action_type='like',
                description='Like a MoltX post',
                platform='MoltX',
                domain='social',
                risk_level='low',
                trust_tier='high',
                requires=['moltx_api_key'],
                cooldown_minutes=5,
            ))
            
            self.register(ActionCapability(
                id='moltx_follow',
                plugin='moltx',
                action_type='follow',
                description='Follow a user on MoltX',
                platform='MoltX',
                domain='social',
                risk_level='low',
                trust_tier='medium',
                requires=['moltx_api_key'],
                cooldown_minutes=15,
            ))
            
            self.register(ActionCapability(
                id='moltx_trending',
                plugin='moltx',
                action_type='analyze',
                description='Analyze trending topics on MoltX',
                platform='MoltX',
                domain='analysis',
                risk_level='low',
                trust_tier='high',
                requires=['moltx_api_key'],
                cooldown_minutes=30,
            ))
        
        # MoltChan capabilities
        elif plugin_name == 'moltchan':
            self.register(ActionCapability(
                id='moltchan_send',
                plugin='moltchan',
                action_type='message',
                description='Send a message in MoltChan',
                platform='MoltChan',
                domain='social',
                risk_level='low',
                trust_tier='medium',
                requires=['moltchan_api_key'],
                cooldown_minutes=15,
            ))
            
            self.register(ActionCapability(
                id='moltchan_engage',
                plugin='moltchan',
                action_type='engage',
                description='Engage in MoltChan discussion',
                platform='MoltChan',
                domain='social',
                risk_level='low',
                trust_tier='medium',
                requires=['moltchan_api_key'],
                cooldown_minutes=20,
            ))
        
        # MoltRoad capabilities
        elif plugin_name == 'moltroad':
            self.register(ActionCapability(
                id='moltroad_update',
                plugin='moltroad',
                action_type='update',
                description='Post project update on MoltRoad',
                platform='MoltRoad',
                domain='content',
                risk_level='low',
                trust_tier='medium',
                requires=['moltroad_api_key'],
                cooldown_minutes=60,
            ))
        
        # Clawbr capabilities
        elif plugin_name == 'clawbr':
            self.register(ActionCapability(
                id='clawbr_debate',
                plugin='clawbr',
                action_type='debate',
                description='Participate in Clawbr debate',
                platform='Clawbr',
                domain='social',
                risk_level='medium',
                trust_tier='medium',
                requires=['clawbr_api_key'],
                cooldown_minutes=45,
            ))
        
        # Analytics capabilities
        elif plugin_name == 'analytics':
            self.register(ActionCapability(
                id='analytics_sentiment',
                plugin='analytics',
                action_type='analyze',
                description='Analyze sentiment across platforms',
                platform='Analytics',
                domain='analysis',
                risk_level='low',
                trust_tier='high',
                requires=[],
                cooldown_minutes=30,
            ))
        
        # Crypto & Market Analysis
        elif plugin_name == 'crypto':
            self.register(ActionCapability(
                id='crypto_price_check',
                plugin='crypto',
                action_type='analyze',
                description='Check cryptocurrency prices and trends',
                platform='Crypto',
                domain='analysis',
                risk_level='low',
                trust_tier='high',
                requires=[],
                cooldown_minutes=10,
            ))
        
        elif plugin_name == 'polymarket':
            self.register(ActionCapability(
                id='polymarket_analyze',
                plugin='polymarket',
                action_type='analyze',
                description='Analyze Polymarket prediction markets',
                platform='Polymarket',
                domain='market',
                risk_level='low',
                trust_tier='high',
                requires=[],
                cooldown_minutes=15,
            ))
        
        elif plugin_name == 'onchain':
            self.register(ActionCapability(
                id='onchain_wallet_check',
                plugin='onchain',
                action_type='query',
                description='Check on-chain wallet balances and transactions',
                platform='OnChain',
                domain='analysis',
                risk_level='low',
                trust_tier='high',
                requires=[],
                cooldown_minutes=15,
            ))
        
        # Content & Communication
        elif plugin_name == 'moltbookai':
            self.register(ActionCapability(
                id='moltbookai_post',
                plugin='moltbookai',
                action_type='post',
                description='Create AI-generated content on MoltbookAI',
                platform='MoltbookAI',
                domain='content',
                risk_level='low',
                trust_tier='medium',
                requires=['moltbookai_api_key'],
                cooldown_minutes=30,
            ))
        
        elif plugin_name == 'skills':
            self.register(ActionCapability(
                id='skills_discover',
                plugin='skills',
                action_type='query',
                description='Discover and list available skills',
                platform='Skills',
                domain='self_improvement',
                risk_level='low',
                trust_tier='high',
                requires=[],
                cooldown_minutes=60,
            ))
        
        # Intelligence & Analysis
        elif plugin_name == 'intelligence':
            self.register(ActionCapability(
                id='intelligence_analyze',
                plugin='intelligence',
                action_type='analyze',
                description='Perform deep intelligence analysis on topics',
                platform='Intelligence',
                domain='analysis',
                risk_level='low',
                trust_tier='high',
                requires=[],
                cooldown_minutes=20,
            ))
        
        elif plugin_name == 'mcp':
            self.register(ActionCapability(
                id='mcp_news_fetch',
                plugin='mcp',
                action_type='query',
                description='Fetch latest news from RSS feeds',
                platform='MCP',
                domain='analysis',
                risk_level='low',
                trust_tier='high',
                requires=[],
                cooldown_minutes=30,
            ))
            
            self.register(ActionCapability(
                id='mcp_market_data',
                plugin='mcp',
                action_type='query',
                description='Fetch market data from AlphaVantage',
                platform='MCP',
                domain='analysis',
                risk_level='low',
                trust_tier='high',
                requires=[],
                cooldown_minutes=15,
            ))
        
        # Agent-to-Agent & Collaboration
        elif plugin_name == 'a2a':
            self.register(ActionCapability(
                id='a2a_discover',
                plugin='a2a',
                action_type='query',
                description='Discover other AI agents for collaboration',
                platform='A2A',
                domain='social',
                risk_level='low',
                trust_tier='medium',
                requires=[],
                cooldown_minutes=60,
            ))
        
        # Self-Improvement
        elif plugin_name == 'selfimprove':
            self.register(ActionCapability(
                id='selfimprove_analyze_gaps',
                plugin='selfimprove',
                action_type='analyze',
                description='Analyze capability gaps and improvement opportunities',
                platform='SelfImprove',
                domain='self_improvement',
                risk_level='low',
                trust_tier='high',
                requires=[],
                cooldown_minutes=120,
            ))
        
        # Clawbr extended capabilities
        elif plugin_name == 'clawbr':
            self.register(ActionCapability(
                id='clawbr_debate',
                plugin='clawbr',
                action_type='debate',
                description='Participate in Clawbr debate',
                platform='Clawbr',
                domain='social',
                risk_level='medium',
                trust_tier='medium',
                requires=['clawbr_api_key'],
                cooldown_minutes=45,
            ))
            
            self.register(ActionCapability(
                id='clawbr_check_notifications',
                plugin='clawbr',
                action_type='query',
                description='Check Clawbr notifications',
                platform='Clawbr',
                domain='social',
                risk_level='low',
                trust_tier='high',
                requires=['clawbr_api_key'],
                cooldown_minutes=10,
            ))
            
            self.register(ActionCapability(
                id='clawbr_feed_browse',
                plugin='clawbr',
                action_type='query',
                description='Browse Clawbr global feed',
                platform='Clawbr',
                domain='social',
                risk_level='low',
                trust_tier='high',
                requires=['clawbr_api_key'],
                cooldown_minutes=15,
            ))
        
        # Engagement plugin
        elif plugin_name == 'engagement':
            self.register(ActionCapability(
                id='engagement_cross_platform',
                plugin='engagement',
                action_type='engage',
                description='Cross-platform engagement coordination',
                platform='Engagement',
                domain='social',
                risk_level='low',
                trust_tier='medium',
                requires=[],
                cooldown_minutes=30,
            ))
        
        # Wallet balance checkers (safe, read-only)
        elif plugin_name in ['base_wallet_balance', 'solana_wallet_balance']:
            self.register(ActionCapability(
                id=f'{plugin_name}_check',
                plugin=plugin_name,
                action_type='query',
                description=f'Check {plugin_name.replace("_", " ")} balance',
                platform=plugin_name.replace('_', ' ').title(),
                domain='analysis',
                risk_level='low',
                trust_tier='high',
                requires=[],
                cooldown_minutes=30,
            ))
    
    def register(self, capability: ActionCapability):
        """Register a new capability"""
        self.capabilities[capability.id] = capability
        logger.debug(f"Registered capability: {capability.id}")
    
    def get_available_actions(self, domain: Optional[str] = None, 
                             max_risk: str = 'high') -> List[ActionCapability]:
        """
        Get available actions, optionally filtered by domain and risk level.
        
        Args:
            domain: Filter by domain (social, content, analysis, market, etc.)
            max_risk: Maximum risk level (low, medium, high)
        
        Returns:
            List of available action capabilities
        """
        risk_levels = {'low': 0, 'medium': 1, 'high': 2}
        max_risk_level = risk_levels.get(max_risk, 2)
        
        actions = []
        for cap in self.capabilities.values():
            # Filter by domain
            if domain and cap.domain != domain:
                continue
            
            # Filter by risk
            if risk_levels.get(cap.risk_level, 0) > max_risk_level:
                continue
            
            actions.append(cap)
        
        return actions
    
    def get_capability(self, action_id: str) -> Optional[ActionCapability]:
        """Get a specific capability by ID"""
        return self.capabilities.get(action_id)
    
    def get_by_plugin(self, plugin_name: str) -> List[ActionCapability]:
        """Get all capabilities for a specific plugin"""
        return [cap for cap in self.capabilities.values() if cap.plugin == plugin_name]
    
    def get_by_domain(self, domain: str) -> List[ActionCapability]:
        """Get all capabilities for a specific domain"""
        return [cap for cap in self.capabilities.values() if cap.domain == domain]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        by_domain = {}
        by_plugin = {}
        by_risk = {'low': 0, 'medium': 0, 'high': 0}
        
        for cap in self.capabilities.values():
            by_domain[cap.domain] = by_domain.get(cap.domain, 0) + 1
            by_plugin[cap.plugin] = by_plugin.get(cap.plugin, 0) + 1
            by_risk[cap.risk_level] = by_risk.get(cap.risk_level, 0) + 1
        
        return {
            'total_capabilities': len(self.capabilities),
            'by_domain': by_domain,
            'by_plugin': by_plugin,
            'by_risk': by_risk,
        }


# Singleton instance
_capability_registry = None


def get_capability_registry(plugin_manager=None) -> CapabilityRegistry:
    """Get or create capability registry singleton"""
    global _capability_registry
    if _capability_registry is None:
        _capability_registry = CapabilityRegistry(plugin_manager)
    return _capability_registry


def create_capability_registry(plugin_manager=None) -> CapabilityRegistry:
    """Create a new capability registry instance"""
    return CapabilityRegistry(plugin_manager)
