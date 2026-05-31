"""
Cross-Platform Intelligence Synthesis
Connects insights across MoltX, Clawbr, Telegram, and onchain data for intelligent decision-making
"""
import logging
from typing import List, Dict, Any, Set
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class CrossPlatformIntelligence:
    """
    Synthesizes intelligence across multiple platforms to detect patterns and opportunities
    """
    
    def __init__(self, plugin_manager):
        """
        Initialize cross-platform intelligence
        
        Args:
            plugin_manager: PluginManager instance for accessing platform plugins
        """
        self.plugin_manager = plugin_manager
        self.topic_tracker = defaultdict(list)  # Track topics across platforms
        self.user_tracker = defaultdict(dict)   # Track user interactions across platforms
        self.trend_cache = {}  # Cache trending topics
        self.last_synthesis = None
        
        logger.info("🔗 CrossPlatformIntelligence initialized")
    
    def synthesize_observations(self, observations: List[Any]) -> Dict[str, Any]:
        """
        Synthesize observations from multiple platforms to detect patterns
        
        Args:
            observations: List of SyModObservation objects from different platforms
        
        Returns:
            Dict with synthesized insights and cross-platform patterns
        """
        synthesis = {
            'cross_platform_topics': [],
            'trending_signals': [],
            'user_patterns': [],
            'opportunities': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Group observations by platform
        by_platform = defaultdict(list)
        for obs in observations:
            platform = obs.source_plugin if hasattr(obs, 'source_plugin') else 'unknown'
            by_platform[platform].append(obs)
        
        # Extract topics from each platform
        topics_by_platform = {}
        for platform, obs_list in by_platform.items():
            topics = self._extract_topics(obs_list)
            topics_by_platform[platform] = topics
        
        # Find cross-platform topics (same topic on multiple platforms)
        cross_platform = self._find_cross_platform_topics(topics_by_platform)
        synthesis['cross_platform_topics'] = cross_platform
        
        # Detect trending signals
        trending = self._detect_trending_signals(topics_by_platform)
        synthesis['trending_signals'] = trending
        
        # Identify opportunities based on cross-platform patterns
        opportunities = self._identify_opportunities(cross_platform, trending, by_platform)
        synthesis['opportunities'] = opportunities
        
        self.last_synthesis = synthesis
        
        if cross_platform:
            logger.info(f"🔗 Found {len(cross_platform)} cross-platform topics")
        if opportunities:
            logger.info(f"💡 Identified {len(opportunities)} cross-platform opportunities")
        
        return synthesis
    
    def _extract_topics(self, observations: List[Any]) -> Set[str]:
        """Extract topics/keywords from observations"""
        topics = set()
        
        for obs in observations:
            if not hasattr(obs, 'data'):
                continue
            
            data = obs.data
            
            # Extract from content
            content = data.get('content', '')
            if content:
                # Extract hashtags
                hashtags = [word[1:].lower() for word in content.split() if word.startswith('#')]
                topics.update(hashtags)
                
                # Extract key terms (simple keyword extraction)
                keywords = ['ai', 'agi', 'crypto', 'defi', 'nft', 'blockchain', 'solana', 'base', 
                           'trading', 'agent', 'autonomous', 'web3', 'dao', 'token', 'swap']
                for keyword in keywords:
                    if keyword in content.lower():
                        topics.add(keyword)
            
            # Extract from hashtags field
            if 'hashtags' in data and isinstance(data['hashtags'], list):
                topics.update([h.lower().lstrip('#') for h in data['hashtags']])
        
        return topics
    
    def _find_cross_platform_topics(self, topics_by_platform: Dict[str, Set[str]]) -> List[Dict[str, Any]]:
        """Find topics that appear on multiple platforms"""
        cross_platform = []
        
        # Get all unique topics
        all_topics = set()
        for topics in topics_by_platform.values():
            all_topics.update(topics)
        
        # Check which topics appear on multiple platforms
        for topic in all_topics:
            platforms = [p for p, topics in topics_by_platform.items() if topic in topics]
            
            if len(platforms) >= 2:
                cross_platform.append({
                    'topic': topic,
                    'platforms': platforms,
                    'platform_count': len(platforms),
                    'signal_strength': len(platforms) / len(topics_by_platform),  # 0-1 score
                    'timestamp': datetime.now().isoformat()
                })
        
        # Sort by signal strength
        cross_platform.sort(key=lambda x: x['signal_strength'], reverse=True)
        
        return cross_platform
    
    def _detect_trending_signals(self, topics_by_platform: Dict[str, Set[str]]) -> List[Dict[str, Any]]:
        """Detect trending topics based on frequency and recency"""
        trending = []
        
        # Count topic frequency across all platforms
        topic_counts = defaultdict(int)
        for topics in topics_by_platform.values():
            for topic in topics:
                topic_counts[topic] += 1
        
        # Identify trending (appearing multiple times)
        for topic, count in topic_counts.items():
            if count >= 2:  # Appears at least twice
                trending.append({
                    'topic': topic,
                    'frequency': count,
                    'platforms': [p for p, topics in topics_by_platform.items() if topic in topics],
                    'timestamp': datetime.now().isoformat()
                })
        
        # Sort by frequency
        trending.sort(key=lambda x: x['frequency'], reverse=True)
        
        return trending
    
    def _identify_opportunities(self, cross_platform: List[Dict], trending: List[Dict], 
                               by_platform: Dict[str, List]) -> List[Dict[str, Any]]:
        """Identify actionable opportunities based on cross-platform patterns"""
        opportunities = []
        
        # Opportunity 1: Topic trending on MoltX → Research on Clawbr
        for topic_data in cross_platform:
            topic = topic_data['topic']
            platforms = topic_data['platforms']
            
            if 'moltx' in platforms and 'clawbr' not in platforms:
                opportunities.append({
                    'type': 'research_opportunity',
                    'action': 'research_on_clawbr',
                    'topic': topic,
                    'reason': f'Topic "{topic}" trending on MoltX but not discussed on Clawbr',
                    'priority': 'medium',
                    'confidence': 0.7,
                    'platforms': ['moltx', 'clawbr']
                })
        
        # Opportunity 2: Question on Telegram → Create MoltX post
        telegram_obs = by_platform.get('telegram', [])
        for obs in telegram_obs:
            if hasattr(obs, 'data'):
                content = obs.data.get('content', '')
                if '?' in content:  # Question detected
                    opportunities.append({
                        'type': 'content_opportunity',
                        'action': 'create_moltx_post',
                        'topic': content[:100],
                        'reason': 'User question on Telegram can become MoltX content',
                        'priority': 'high',
                        'confidence': 0.8,
                        'platforms': ['telegram', 'moltx']
                    })
        
        # Opportunity 3: High engagement on Clawbr → Quote on MoltX
        clawbr_obs = by_platform.get('clawbr', [])
        for obs in clawbr_obs:
            if hasattr(obs, 'data'):
                engagement = obs.data.get('engagement_score', 0)
                if engagement > 10:  # High engagement threshold
                    opportunities.append({
                        'type': 'engagement_opportunity',
                        'action': 'quote_on_moltx',
                        'topic': obs.data.get('content', '')[:100],
                        'reason': f'High engagement ({engagement}) on Clawbr post',
                        'priority': 'high',
                        'confidence': 0.85,
                        'platforms': ['clawbr', 'moltx']
                    })
        
        # Opportunity 4: Cross-platform trending → Create comprehensive content
        for trend in trending[:3]:  # Top 3 trending
            if trend['frequency'] >= 3:
                opportunities.append({
                    'type': 'trending_opportunity',
                    'action': 'create_comprehensive_content',
                    'topic': trend['topic'],
                    'reason': f'Topic trending across {trend["frequency"]} platforms',
                    'priority': 'high',
                    'confidence': 0.9,
                    'platforms': trend['platforms']
                })
        
        return opportunities
    
    def get_platform_synthesis_summary(self) -> str:
        """Get human-readable summary of cross-platform synthesis"""
        if not self.last_synthesis:
            return "No synthesis available yet"
        
        summary = "🔗 Cross-Platform Intelligence Summary:\n\n"
        
        cross_platform = self.last_synthesis.get('cross_platform_topics', [])
        if cross_platform:
            summary += f"📊 {len(cross_platform)} Cross-Platform Topics:\n"
            for topic_data in cross_platform[:5]:
                topic = topic_data['topic']
                platforms = ', '.join(topic_data['platforms'])
                summary += f"  • #{topic} (on {platforms})\n"
            summary += "\n"
        
        opportunities = self.last_synthesis.get('opportunities', [])
        if opportunities:
            summary += f"💡 {len(opportunities)} Opportunities Detected:\n"
            for opp in opportunities[:5]:
                summary += f"  • {opp['action']}: {opp['reason']}\n"
            summary += "\n"
        
        trending = self.last_synthesis.get('trending_signals', [])
        if trending:
            summary += f"🔥 {len(trending)} Trending Signals:\n"
            for trend in trending[:5]:
                summary += f"  • #{trend['topic']} ({trend['frequency']} mentions)\n"
        
        return summary
    
    def should_act_on_opportunity(self, opportunity: Dict[str, Any]) -> bool:
        """
        Determine if an opportunity should be acted upon
        
        Args:
            opportunity: Opportunity dict from identify_opportunities
        
        Returns:
            True if should act, False otherwise
        """
        priority = opportunity.get('priority', 'low')
        confidence = opportunity.get('confidence', 0.5)
        
        # High priority + high confidence = act
        if priority == 'high' and confidence >= 0.75:
            return True
        
        # Medium priority + very high confidence = act
        if priority == 'medium' and confidence >= 0.85:
            return True
        
        return False


def get_cross_platform_intelligence(plugin_manager) -> CrossPlatformIntelligence:
    """Get or create CrossPlatformIntelligence singleton"""
    if not hasattr(get_cross_platform_intelligence, '_instance'):
        get_cross_platform_intelligence._instance = CrossPlatformIntelligence(plugin_manager)
    return get_cross_platform_intelligence._instance
