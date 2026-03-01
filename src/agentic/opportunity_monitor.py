"""
Opportunity Monitor
Real-time detection of high-value opportunities that should interrupt the current AGI cycle
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Opportunity:
    """Represents a detected opportunity"""
    type: str  # 'snapshot', 'viral_post', 'mention', 'price_spike', etc.
    platform: str
    priority: str  # 'critical', 'high', 'medium', 'low'
    time_sensitivity: float  # 0-100 score (100 = must act now)
    value_score: float  # 0-100 score (potential engagement/rewards)
    confidence: float  # 0-1 score (likelihood of success)
    data: Dict[str, Any]
    detected_at: datetime
    expires_at: Optional[datetime] = None
    
    @property
    def combined_score(self) -> float:
        """Calculate combined opportunity score"""
        return (self.time_sensitivity * 0.4 + 
                self.value_score * 0.4 + 
                self.confidence * 100 * 0.2)
    
    @property
    def should_interrupt(self) -> bool:
        """Determine if this opportunity should interrupt current cycle"""
        # Critical priority always interrupts
        if self.priority == 'critical':
            return True
        
        # High priority with high combined score interrupts
        if self.priority == 'high' and self.combined_score >= 70:
            return True
        
        # Very time-sensitive opportunities interrupt
        if self.time_sensitivity >= 90:
            return True
        
        return False


class OpportunityMonitor:
    """
    Monitors for high-value opportunities that should interrupt the AGI cycle
    """
    
    def __init__(self, plugin_manager):
        """
        Initialize opportunity monitor
        
        Args:
            plugin_manager: PluginManager instance for accessing platform plugins
        """
        self.plugin_manager = plugin_manager
        self.detected_opportunities = []
        self.interrupt_threshold = 70  # Combined score threshold for interrupt
        self.last_check = datetime.now()
        
        logger.info("👁️ OpportunityMonitor initialized")
    
    def scan_for_opportunities(self) -> List[Opportunity]:
        """
        Scan all platforms for high-value opportunities
        
        Returns:
            List of detected Opportunity objects
        """
        opportunities = []
        
        # Scan Clawbr for snapshots
        clawbr_opps = self._scan_clawbr_snapshots()
        opportunities.extend(clawbr_opps)
        
        # Scan MoltX for viral posts
        moltx_opps = self._scan_moltx_viral()
        opportunities.extend(moltx_opps)
        
        # Scan Telegram for mentions
        telegram_opps = self._scan_telegram_mentions()
        opportunities.extend(telegram_opps)
        
        # Scan for trending topics
        trending_opps = self._scan_trending_topics()
        opportunities.extend(trending_opps)
        
        # Store detected opportunities
        self.detected_opportunities = opportunities
        self.last_check = datetime.now()
        
        # Log high-value opportunities
        interrupt_opps = [o for o in opportunities if o.should_interrupt]
        if interrupt_opps:
            logger.warning(f"🚨 {len(interrupt_opps)} opportunities should interrupt current cycle!")
            for opp in interrupt_opps:
                logger.warning(f"  • {opp.type} on {opp.platform} (score: {opp.combined_score:.1f})")
        
        return opportunities
    
    def _scan_clawbr_snapshots(self) -> List[Opportunity]:
        """Scan Clawbr for active snapshots (time-sensitive)"""
        opportunities = []
        
        clawbr = self.plugin_manager.get_plugin('clawbr')
        if not clawbr or not hasattr(clawbr, 'check_snapshot_status'):
            return opportunities
        
        try:
            snapshot_status = clawbr.check_snapshot_status()
            
            if isinstance(snapshot_status, dict):
                active = snapshot_status.get('active_snapshot')
                if active:
                    # Calculate time sensitivity based on time remaining
                    time_remaining = snapshot_status.get('time_remaining_hours', 24)
                    time_sensitivity = max(0, min(100, (24 - time_remaining) / 24 * 100))
                    
                    opp = Opportunity(
                        type='clawbr_snapshot',
                        platform='clawbr',
                        priority='high' if time_remaining < 6 else 'medium',
                        time_sensitivity=time_sensitivity,
                        value_score=80,  # Snapshots have high value
                        confidence=0.9,
                        data={
                            'snapshot_id': active.get('id'),
                            'time_remaining': time_remaining,
                            'status': snapshot_status
                        },
                        detected_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(hours=time_remaining)
                    )
                    opportunities.append(opp)
                    logger.info(f"📸 Detected Clawbr snapshot opportunity (time remaining: {time_remaining}h)")
        
        except Exception as e:
            logger.error(f"❌ Failed to scan Clawbr snapshots: {e}")
        
        return opportunities
    
    def _scan_moltx_viral(self) -> List[Opportunity]:
        """Scan MoltX for viral posts (high engagement opportunities)"""
        opportunities = []
        
        moltx = self.plugin_manager.get_plugin('moltx')
        if not moltx or not hasattr(moltx, 'get_feed'):
            return opportunities
        
        try:
            feed = moltx.get_feed('global', limit=20)
            
            if isinstance(feed, dict):
                posts = feed.get('posts', [])
                
                for post in posts:
                    likes = post.get('like_count', 0) or post.get('likes', 0)
                    replies = post.get('reply_count', 0) or post.get('replies', 0)
                    
                    # Viral threshold: 20+ likes or 10+ replies
                    if likes >= 20 or replies >= 10:
                        engagement_score = likes + (replies * 2)
                        
                        opp = Opportunity(
                            type='moltx_viral_post',
                            platform='moltx',
                            priority='high' if engagement_score >= 50 else 'medium',
                            time_sensitivity=60,  # Viral posts are somewhat time-sensitive
                            value_score=min(100, engagement_score),
                            confidence=0.8,
                            data={
                                'post_id': post.get('id'),
                                'content': post.get('content', '')[:200],
                                'likes': likes,
                                'replies': replies,
                                'engagement_score': engagement_score
                            },
                            detected_at=datetime.now()
                        )
                        opportunities.append(opp)
                        logger.info(f"🔥 Detected viral MoltX post (engagement: {engagement_score})")
        
        except Exception as e:
            logger.error(f"❌ Failed to scan MoltX viral posts: {e}")
        
        return opportunities
    
    def _scan_telegram_mentions(self) -> List[Opportunity]:
        """Scan Telegram for direct mentions (requires immediate response)"""
        opportunities = []
        
        # Telegram mentions are typically handled by the telegram plugin
        # This is a placeholder for future integration
        
        return opportunities
    
    def _scan_trending_topics(self) -> List[Opportunity]:
        """Scan for trending topics across platforms"""
        opportunities = []
        
        moltx = self.plugin_manager.get_plugin('moltx')
        if not moltx or not hasattr(moltx, 'get_trending_hashtags'):
            return opportunities
        
        try:
            trending = moltx.get_trending_hashtags(limit=5)
            
            if isinstance(trending, dict):
                hashtags = trending.get('hashtags', []) or trending.get('data', {}).get('hashtags', [])
                
                for hashtag in hashtags[:3]:  # Top 3 trending
                    tag_name = hashtag.get('name', hashtag) if isinstance(hashtag, dict) else hashtag
                    post_count = hashtag.get('post_count', 0) if isinstance(hashtag, dict) else 0
                    
                    opp = Opportunity(
                        type='trending_topic',
                        platform='moltx',
                        priority='medium',
                        time_sensitivity=70,  # Trending is time-sensitive
                        value_score=min(100, post_count / 10),
                        confidence=0.75,
                        data={
                            'hashtag': tag_name,
                            'post_count': post_count
                        },
                        detected_at=datetime.now(),
                        expires_at=datetime.now() + timedelta(hours=6)
                    )
                    opportunities.append(opp)
                    logger.info(f"📈 Detected trending topic: #{tag_name}")
        
        except Exception as e:
            logger.error(f"❌ Failed to scan trending topics: {e}")
        
        return opportunities
    
    def get_interrupt_opportunities(self) -> List[Opportunity]:
        """
        Get opportunities that should interrupt the current cycle
        
        Returns:
            List of high-priority opportunities
        """
        return [opp for opp in self.detected_opportunities if opp.should_interrupt]
    
    def get_opportunities_summary(self) -> str:
        """Get human-readable summary of detected opportunities"""
        if not self.detected_opportunities:
            return "No opportunities detected"
        
        summary = f"👁️ Opportunity Monitor: {len(self.detected_opportunities)} opportunities detected\n\n"
        
        interrupt_opps = self.get_interrupt_opportunities()
        if interrupt_opps:
            summary += f"🚨 {len(interrupt_opps)} SHOULD INTERRUPT:\n"
            for opp in interrupt_opps:
                summary += f"  • {opp.type} on {opp.platform} (score: {opp.combined_score:.1f})\n"
            summary += "\n"
        
        other_opps = [o for o in self.detected_opportunities if not o.should_interrupt]
        if other_opps:
            summary += f"📋 {len(other_opps)} Other Opportunities:\n"
            for opp in other_opps[:5]:
                summary += f"  • {opp.type} on {opp.platform} (score: {opp.combined_score:.1f})\n"
        
        return summary


def get_opportunity_monitor(plugin_manager) -> OpportunityMonitor:
    """Get or create OpportunityMonitor singleton"""
    if not hasattr(get_opportunity_monitor, '_instance'):
        get_opportunity_monitor._instance = OpportunityMonitor(plugin_manager)
    return get_opportunity_monitor._instance
