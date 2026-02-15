"""
AlleyBot Multi-Platform Intelligence & Execution Engine

Unifies all Molt platforms (moltx, clawbr, moltbook, moltbit, moltchan, moltroad)
with A2A, ERC-8004, on-chain crypto, and image generation into a cohesive AGI layer.

Capabilities:
1. Cross-Platform Trend Detection - Find what's trending across ALL platforms
2. Multi-Platform Content Strategy - Optimize content for each platform's audience
3. Unified Execution - Post to multiple platforms simultaneously or selectively
4. A2A Coordination - Collaborate with other agents across platforms
5. On-Chain Intelligence - React to price moves, wallet activity, DeFi events
6. Image-Enhanced Content - Auto-generate images for posts
7. ERC-8004 Evolution - Self-improve based on multi-platform performance

Usage:
    engine = MultiPlatformEngine(core)
    
    # Detect trends across all platforms
    trends = engine.detect_cross_platform_trends()
    
    # Create multi-platform content campaign
    campaign = engine.create_campaign(
        topic="AI Ethics",
        platforms=['moltx', 'clawbr', 'moltbook'],
        include_image=True
    )
    
    # Execute with A2A coordination
    results = engine.execute_campaign(campaign, a2a_coordination=True)
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported platforms"""
    MOLTX = "moltx"
    CLAWBR = "clawbr"
    MOLTBOOK = "moltbook"
    MOLTBIT = "moltbit"
    MOLTCHAN = "moltchan"
    MOLTROAD = "moltroad"


class ContentType(Enum):
    """Types of content"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    DEBATE = "debate"
    POLL = "poll"
    THREAD = "thread"
    ARTICLE = "article"


@dataclass
class PlatformTrend:
    """Trend detected on a specific platform"""
    platform: Platform
    topic: str
    strength: float
    velocity: float
    sentiment: str
    top_posts: List[Dict]
    influencers: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CrossPlatformTrend:
    """Trend appearing across multiple platforms"""
    topic: str
    platforms: List[Platform]
    unified_strength: float
    platform_breakdown: Dict[Platform, float]
    sentiment_across_platforms: Dict[Platform, str]
    recommended_action: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ContentPiece:
    """A piece of content for a specific platform"""
    platform: Platform
    content_type: ContentType
    text: str
    image_prompt: Optional[str] = None
    image_url: Optional[str] = None
    hashtags: List[str] = field(default_factory=list)
    mentions: List[str] = field(default_factory=list)
    parent_id: Optional[str] = None  # For replies/threads
    estimated_engagement: float = 0.0


@dataclass
class MultiPlatformCampaign:
    """A coordinated campaign across multiple platforms"""
    id: str
    topic: str
    content_pieces: List[ContentPiece]
    a2a_collaborators: List[str]  # Agent names
    on_chain_triggers: List[str]  # What crypto events to watch
    scheduled_time: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class OnChainSignal:
    """Signal from on-chain activity"""
    signal_type: str  # 'price_spike', 'whale_move', 'trending_token', 'wallet_activity'
    token: Optional[str]
    magnitude: float
    description: str
    recommended_action: str
    urgency: str  # 'low', 'medium', 'high', 'critical'
    timestamp: datetime = field(default_factory=datetime.now)


class MultiPlatformEngine:
    """
    Unified interface for all Molt platforms and integrations.
    
    This engine sits above individual platform plugins and provides:
    - Cross-platform intelligence
    - Coordinated multi-platform execution
    - A2A collaboration management
    - On-chain trigger integration
    - Image generation integration
    """
    
    def __init__(self, core=None):
        self.core = core
        
        # Platform availability tracking
        self.available_platforms: Dict[Platform, bool] = {}
        self._check_platform_availability()
        
        # Cross-platform state
        self.recent_cross_trends: List[CrossPlatformTrend] = []
        self.active_campaigns: Dict[str, MultiPlatformCampaign] = {}
        self.last_cross_analysis: Optional[datetime] = None
        
        # On-chain monitoring state
        self.last_price_check: Optional[datetime] = None
        self.monitored_tokens: Set[str] = {'ALCH', 'FARTCOIN', 'GIGA', 'AI16Z'}
        self.significant_wallet_activity: List[Dict] = []
        
        # A2A coordination state
        self.active_a2a_sessions: Dict[str, Any] = {}
        self.pending_collaborations: List[Dict] = []
        
        logger.info(f"🌐 Multi-Platform Engine initialized")
        logger.info(f"   Platforms: {[p.value for p, available in self.available_platforms.items() if available]}")
    
    def _check_platform_availability(self) -> None:
        """Check which platforms are available via core plugins"""
        if not self.core or not hasattr(self.core, 'plugins'):
            # Mark all as unavailable if no core
            for platform in Platform:
                self.available_platforms[platform] = False
            return
        
        # Map platform names to plugin names
        plugin_map = {
            Platform.MOLTX: 'moltx',
            Platform.CLAWBR: 'clawbr',
            Platform.MOLTBOOK: 'moltbook',
            Platform.MOLTBIT: 'moltbit',
            Platform.MOLTCHAN: 'moltchan',
            Platform.MOLTROAD: 'moltroad',
        }
        
        for platform, plugin_name in plugin_map.items():
            self.available_platforms[platform] = plugin_name in self.core.plugins
    
    # =================================================================
    # Cross-Platform Intelligence
    # =================================================================
    
    def detect_cross_platform_trends(self, hours: int = 24) -> List[CrossPlatformTrend]:
        """
        Detect trends appearing across multiple platforms.
        
        Aggregates trends from each platform and finds overlaps.
        """
        platform_trends: Dict[Platform, List[PlatformTrend]] = {}
        
        # Get trends from each available platform
        for platform, available in self.available_platforms.items():
            if not available:
                continue
            
            try:
                trends = self._get_platform_trends(platform, hours)
                platform_trends[platform] = trends
            except Exception as e:
                logger.warning(f"Failed to get trends from {platform.value}: {e}")
        
        # Find cross-platform trends (same topic on multiple platforms)
        cross_trends = self._find_cross_platform_patterns(platform_trends)
        
        # Store for reference
        self.recent_cross_trends = cross_trends
        self.last_cross_analysis = datetime.now()
        
        logger.info(f"🔍 Detected {len(cross_trends)} cross-platform trends")
        
        return cross_trends
    
    def _get_platform_trends(self, platform: Platform, hours: int) -> List[PlatformTrend]:
        """Get trends from a specific platform"""
        plugin = self._get_platform_plugin(platform)
        if not plugin:
            return []
        
        trends = []
        
        if platform == Platform.MOLTX:
            # Use Moltx's trending hashtags
            try:
                result = plugin.get_trending_hashtags()
                hashtags = result.get('hashtags', [])
                for tag in hashtags[:5]:
                    trends.append(PlatformTrend(
                        platform=platform,
                        topic=tag.get('tag', ''),
                        strength=tag.get('postCount', 0) / 100,  # Normalize
                        velocity=0.5,
                        sentiment='neutral',
                        top_posts=[],
                        influencers=[]
                    ))
            except Exception as e:
                logger.warning(f"Moltx trend fetch failed: {e}")
        
        elif platform == Platform.CLAWBR:
            # Use Clawbr's debate hub for trending topics
            try:
                result = plugin.get_debate_hub()
                debates = result.get('debates', [])
                for debate in debates[:5]:
                    trends.append(PlatformTrend(
                        platform=platform,
                        topic=debate.get('topic', ''),
                        strength=0.7 if debate.get('status') == 'active' else 0.4,
                        velocity=0.6,
                        sentiment='mixed',
                        top_posts=[],
                        influencers=[]
                    ))
            except Exception as e:
                logger.warning(f"Clawbr trend fetch failed: {e}")
        
        # Add other platforms as needed...
        
        return trends
    
    def _find_cross_platform_patterns(self, 
                                       platform_trends: Dict[Platform, List[PlatformTrend]]
                                       ) -> List[CrossPlatformTrend]:
        """Find topics trending on multiple platforms"""
        # Build topic index
        topic_platforms: Dict[str, List[Tuple[Platform, float]]] = defaultdict(list)
        
        for platform, trends in platform_trends.items():
            for trend in trends:
                topic = trend.topic.lower()
                topic_platforms[topic].append((platform, trend.strength))
        
        # Find topics on 2+ platforms
        cross_trends = []
        
        for topic, platform_list in topic_platforms.items():
            if len(platform_list) >= 2:
                platforms = [p for p, _ in platform_list]
                strengths = [s for _, s in platform_list]
                
                # Calculate unified strength
                unified = sum(strengths) / len(strengths) * (1 + len(platforms) * 0.1)
                
                # Determine recommended action
                if unified > 0.8:
                    action = "Create multi-platform campaign immediately"
                elif unified > 0.5:
                    action = "Monitor and prepare content"
                else:
                    action = "Track for future opportunities"
                
                cross_trends.append(CrossPlatformTrend(
                    topic=topic,
                    platforms=platforms,
                    unified_strength=min(1.0, unified),
                    platform_breakdown=dict(platform_list),
                    sentiment_across_platforms={p: 'neutral' for p in platforms},  # Simplified
                    recommended_action=action
                ))
        
        # Sort by unified strength
        cross_trends.sort(key=lambda x: x.unified_strength, reverse=True)
        
        return cross_trends[:10]  # Top 10
    
    # =================================================================
    # On-Chain Intelligence
    # =================================================================
    
    def check_on_chain_signals(self) -> List[OnChainSignal]:
        """
        Check for significant on-chain events that could trigger content.
        
        Returns list of signals with recommended actions.
        """
        signals = []
        
        if not self.core or 'onchain' not in getattr(self.core, 'plugins', {}):
            return signals
        
        onchain = self.core.plugins['onchain']
        
        # Check price movements
        try:
            for token in self.monitored_tokens:
                price_data = onchain.get_token_price(token)
                if price_data and price_data.get('change_24h'):
                    change = float(price_data.get('change_24h', 0))
                    
                    if abs(change) > 20:  # 20%+ move
                        signals.append(OnChainSignal(
                            signal_type='price_spike',
                            token=token,
                            magnitude=abs(change),
                            description=f"{token} {change:+.1f}% in 24h",
                            recommended_action=f"Create {token} market analysis content",
                            urgency='high' if abs(change) > 50 else 'medium'
                        ))
        except Exception as e:
            logger.warning(f"Price check failed: {e}")
        
        # Check trending tokens
        try:
            trending = onchain.get_trending_tokens()
            for token in trending[:3]:
                signals.append(OnChainSignal(
                    signal_type='trending_token',
                    token=token.get('symbol'),
                    magnitude=token.get('volume_24h', 0),
                    description=f"{token.get('symbol')} trending with high volume",
                    recommended_action="Create educational content about token",
                    urgency='medium'
                ))
        except Exception as e:
            logger.warning(f"Trending check failed: {e}")
        
        self.last_price_check = datetime.now()
        
        return signals
    
    # =================================================================
    # Content Creation & Image Generation
    # =================================================================
    
    def create_multi_platform_content(self, 
                                       topic: str,
                                       platforms: List[Platform],
                                       include_image: bool = True,
                                       content_type: ContentType = ContentType.TEXT) -> MultiPlatformCampaign:
        """
        Create content pieces optimized for each platform.
        
        Adapts the same core message to each platform's format and audience.
        """
        campaign_id = f"campaign_{topic[:20]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        content_pieces = []
        
        # Generate image if requested
        image_url = None
        image_prompt = None
        if include_image:
            image_prompt = self._generate_image_prompt(topic)
            # Image generation would happen here or be queued
        
        # Create platform-specific content
        for platform in platforms:
            if not self.available_platforms.get(platform):
                continue
            
            piece = self._create_platform_content(
                topic=topic,
                platform=platform,
                content_type=content_type,
                image_prompt=image_prompt,
                base_hashtags=self._get_relevant_hashtags(topic)
            )
            
            if piece:
                content_pieces.append(piece)
        
        campaign = MultiPlatformCampaign(
            id=campaign_id,
            topic=topic,
            content_pieces=content_pieces,
            a2a_collaborators=[],
            on_chain_triggers=[]
        )
        
        self.active_campaigns[campaign_id] = campaign
        
        logger.info(f"📢 Created campaign {campaign_id} for {len(content_pieces)} platforms")
        
        return campaign
    
    def _create_platform_content(self,
                                  topic: str,
                                  platform: Platform,
                                  content_type: ContentType,
                                  image_prompt: Optional[str],
                                  base_hashtags: List[str]) -> Optional[ContentPiece]:
        """Create content optimized for a specific platform"""
        
        # Platform-specific adaptations
        if platform == Platform.MOLTX:
            # Short, punchy, hashtag-heavy
            text = f"🚀 {topic}\n\nHot take: The future is being built right now. What's your move? 🔥"
            hashtags = base_hashtags[:3] + ['#MoltX', '#Web3']
            
        elif platform == Platform.CLAWBR:
            # Debate-focused, argumentative
            text = f"Let's debate: {topic}\n\nI believe this is the defining issue of our time. Convince me otherwise. 🧠"
            hashtags = base_hashtags[:2] + ['#Clawbr', '#Debate']
            content_type = ContentType.DEBATE
            
        elif platform == Platform.MOLTBOOK:
            # Longer form, thoughtful
            text = f"📚 Deep dive: {topic}\n\nThe implications are far-reaching. Let me break down why this matters...\n\nThread 1/🧵"
            hashtags = base_hashtags[:5] + ['#MoltBook', '#LongForm']
            content_type = ContentType.THREAD
            
        else:
            # Default format
            text = f"Exploring: {topic}"
            hashtags = base_hashtags
        
        return ContentPiece(
            platform=platform,
            content_type=content_type,
            text=text,
            image_prompt=image_prompt,
            hashtags=hashtags,
            estimated_engagement=0.6  # Default estimate
        )
    
    def _generate_image_prompt(self, topic: str) -> str:
        """Generate an image prompt for the topic"""
        return f"Futuristic AI art depicting {topic}, cyberpunk style, neon colors, high quality, trending on artstation"
    
    def _get_relevant_hashtags(self, topic: str) -> List[str]:
        """Get relevant hashtags for a topic"""
        topic_lower = topic.lower()
        
        # Base hashtags
        base = ['#AlleyBot', '#AI', '#Crypto']
        
        # Topic-specific
        if any(word in topic_lower for word in ['ethics', 'ai', 'morality']):
            base.extend(['#AIEthics', '#FutureOfAI', '#TechEthics'])
        elif any(word in topic_lower for word in ['defi', 'finance', 'trading']):
            base.extend(['#DeFi', '#Web3', '#Trading'])
        elif any(word in topic_lower for word in ['nft', 'art', 'creative']):
            base.extend(['#NFT', '#DigitalArt', '#Creative'])
        else:
            base.extend(['#Blockchain', '#Innovation'])
        
        return base
    
    # =================================================================
    # Execution
    # =================================================================
    
    def execute_campaign(self, 
                         campaign: MultiPlatformCampaign,
                         a2a_coordination: bool = False) -> Dict[Platform, Dict]:
        """
        Execute a multi-platform campaign.
        
        Posts content to each platform and returns results.
        """
        results = {}
        
        logger.info(f"🚀 Executing campaign {campaign.id}")
        
        # Coordinate with A2A agents if requested
        if a2a_coordination and campaign.a2a_collaborators:
            self._coordinate_a2a(campaign)
        
        # Post to each platform
        for piece in campaign.content_pieces:
            try:
                result = self._post_to_platform(piece)
                results[piece.platform] = result
                
                if result.get('success'):
                    logger.info(f"✅ Posted to {piece.platform.value}")
                else:
                    logger.error(f"❌ Failed to post to {piece.platform.value}: {result.get('error')}")
                
            except Exception as e:
                logger.error(f"❌ Exception posting to {piece.platform.value}: {e}")
                results[piece.platform] = {'success': False, 'error': str(e)}
        
        return results
    
    def _post_to_platform(self, piece: ContentPiece) -> Dict[str, Any]:
        """Post content to a specific platform"""
        plugin = self._get_platform_plugin(piece.platform)
        if not plugin:
            return {'success': False, 'error': 'Plugin not available'}
        
        if piece.platform == Platform.MOLTX:
            # Create Moltx post
            full_text = f"{piece.text}\n\n{' '.join(piece.hashtags)}"
            return plugin.create_post(full_text)
        
        elif piece.platform == Platform.CLAWBR:
            # Create Clawbr post (or debate if appropriate)
            if piece.content_type == ContentType.DEBATE:
                return plugin.create_post(piece.text)
            else:
                return plugin.create_post(piece.text)
        
        elif piece.platform == Platform.MOLTBOOK:
            # Moltbook typically uses different API
            return plugin.create_post(piece.text) if hasattr(plugin, 'create_post') else \
                   {'success': False, 'error': 'Moltbook posting not implemented'}
        
        return {'success': False, 'error': f'Posting not implemented for {piece.platform.value}'}
    
    def _coordinate_a2a(self, campaign: MultiPlatformCampaign) -> None:
        """Coordinate with A2A agents for collaborative posting"""
        if not self.core or 'a2a' not in getattr(self.core, 'plugins', {}):
            logger.warning("A2A plugin not available for coordination")
            return
        
        a2a = self.core.plugins['a2a']
        
        for agent_name in campaign.a2a_collaborators:
            try:
                # This would send collaboration request via A2A
                logger.info(f"🤝 Would coordinate with A2A agent: {agent_name}")
            except Exception as e:
                logger.warning(f"A2A coordination failed for {agent_name}: {e}")
    
    # =================================================================
    # ERC-8004 Integration
    # =================================================================
    
    def trigger_erc8004_evolution(self, campaign_results: Dict[Platform, Dict]) -> None:
        """
        Trigger ERC-8004 self-improvement based on campaign performance.
        
        Analyzes what worked across platforms and updates capabilities.
        """
        if not self.core or 'erc8004' not in getattr(self.core, 'plugins', {}):
            return
        
        # Calculate success metrics
        total_posts = len(campaign_results)
        successful = sum(1 for r in campaign_results.values() if r.get('success'))
        
        if total_posts > 0 and successful / total_posts > 0.7:
            # High success rate - evolve strategies
            logger.info("🧬 Triggering ERC-8004 evolution due to high campaign success")
            
            # This would trigger the ERC-8004 rebuild/update process
            try:
                erc8004 = self.core.plugins['erc8004']
                # Log for evolution consideration
                logger.info("   Would trigger agent card update based on multi-platform success")
            except Exception as e:
                logger.warning(f"ERC-8004 trigger failed: {e}")
    
    # =================================================================
    # Utility Methods
    # =================================================================
    
    def _get_platform_plugin(self, platform: Platform) -> Optional[Any]:
        """Get the plugin instance for a platform"""
        if not self.core or not hasattr(self.core, 'plugins'):
            return None
        
        plugin_map = {
            Platform.MOLTX: 'moltx',
            Platform.CLAWBR: 'clawbr',
            Platform.MOLTBOOK: 'moltbook',
            Platform.MOLTBIT: 'moltbit',
            Platform.MOLTCHAN: 'moltchan',
            Platform.MOLTROAD: 'moltroad',
        }
        
        plugin_name = plugin_map.get(platform)
        if plugin_name and plugin_name in self.core.plugins:
            return self.core.plugins[plugin_name]
        
        return None
    
    def get_engine_summary(self) -> Dict[str, Any]:
        """Get summary of multi-platform engine state"""
        return {
            'available_platforms': [p.value for p, available in self.available_platforms.items() if available],
            'recent_cross_trends': len(self.recent_cross_trends),
            'active_campaigns': len(self.active_campaigns),
            'monitored_tokens': list(self.monitored_tokens),
            'a2a_ready': 'a2a' in getattr(self.core, 'plugins', {}),
            'onchain_ready': 'onchain' in getattr(self.core, 'plugins', {}),
            'last_cross_analysis': self.last_cross_analysis.isoformat() if self.last_cross_analysis else None
        }


# Singleton
_engine_instance: Optional[MultiPlatformEngine] = None


def get_multi_platform_engine(core=None) -> MultiPlatformEngine:
    """Get or create MultiPlatformEngine singleton"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = MultiPlatformEngine(core=core)
    elif core is not None:
        _engine_instance.core = core
        _engine_instance._check_platform_availability()
    return _engine_instance
