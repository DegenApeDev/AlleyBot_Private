"""
Cross-Domain Pattern Detector - Phase 4: Horizontal Synthesis

Detects patterns across different domains (crypto, social, content, trading).
This is HORIZONTAL intelligence - connecting dots across platforms.

Part of AGI Core - Phase 4: Cross-Domain Intelligence
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class CrossDomainPattern:
    """A pattern detected across multiple domains"""
    pattern_type: str  # 'crypto_social', 'sentiment_price', 'engagement_trend'
    domains: List[str]  # ['crypto', 'social', 'content']
    description: str
    confidence: float  # 0-1
    evidence: List[Dict]
    detected_at: datetime = field(default_factory=datetime.now)
    correlation_score: float = 0.0  # -1 to 1
    
    def to_dict(self) -> Dict:
        return {
            'pattern_type': self.pattern_type,
            'domains': self.domains,
            'description': self.description,
            'confidence': self.confidence,
            'evidence': self.evidence,
            'detected_at': self.detected_at.isoformat(),
            'correlation_score': self.correlation_score
        }


class CrossDomainPatternDetector:
    """
    Detects patterns across different domains.
    
    This is HORIZONTAL intelligence - the ability to:
    1. Connect crypto price movements to social sentiment
    2. Detect trending topics across platforms
    3. Identify engagement patterns that predict success
    4. Synthesize knowledge from multiple sources
    """
    
    def __init__(self):
        self.detected_patterns: List[CrossDomainPattern] = []
        self.pattern_history: Dict[str, List[CrossDomainPattern]] = defaultdict(list)
    
    def detect_patterns(self, observations: List[Dict]) -> List[CrossDomainPattern]:
        """
        Detect cross-domain patterns from observations.
        
        Args:
            observations: List of observations from different platforms
            
        Returns:
            List of detected patterns
        """
        patterns = []
        
        # Group observations by domain
        by_domain = self._group_by_domain(observations)
        
        # 1. Crypto-Social Correlation
        if 'crypto' in by_domain and 'social' in by_domain:
            crypto_social = self._detect_crypto_social_correlation(
                by_domain['crypto'],
                by_domain['social']
            )
            patterns.extend(crypto_social)
        
        # 2. Sentiment-Price Correlation
        if 'crypto' in by_domain and 'social' in by_domain:
            sentiment_price = self._detect_sentiment_price_correlation(
                by_domain['crypto'],
                by_domain['social']
            )
            patterns.extend(sentiment_price)
        
        # 3. Cross-Platform Trending Topics
        if len(by_domain) >= 2:
            trending = self._detect_cross_platform_trends(by_domain)
            patterns.extend(trending)
        
        # 4. Engagement Success Patterns
        if 'social' in by_domain:
            engagement = self._detect_engagement_patterns(by_domain['social'])
            patterns.extend(engagement)
        
        # Store detected patterns
        for pattern in patterns:
            self.detected_patterns.append(pattern)
            self.pattern_history[pattern.pattern_type].append(pattern)
        
        return patterns
    
    def _group_by_domain(self, observations: List[Dict]) -> Dict[str, List[Dict]]:
        """Group observations by domain"""
        by_domain = defaultdict(list)
        
        for obs in observations:
            # Determine domain from observation
            domain = self._determine_domain(obs)
            if domain:
                by_domain[domain].append(obs)
        
        return by_domain
    
    def _determine_domain(self, observation: Dict) -> Optional[str]:
        """Determine which domain an observation belongs to"""
        platform = observation.get('platform', '').lower()
        obs_type = observation.get('type', '').lower()
        
        # Crypto domain
        if 'price' in obs_type or 'crypto' in platform or 'onchain' in platform:
            return 'crypto'
        
        # Social domain
        if platform in ['moltx', 'twitter', 'farcaster']:
            return 'social'
        
        # Content domain
        if platform in ['moltbook', 'medium', 'substack']:
            return 'content'
        
        # Trading domain
        if 'trade' in obs_type or 'swap' in obs_type:
            return 'trading'
        
        return None
    
    def _detect_crypto_social_correlation(
        self,
        crypto_obs: List[Dict],
        social_obs: List[Dict]
    ) -> List[CrossDomainPattern]:
        """
        Detect correlation between crypto prices and social activity.
        
        Example: BTC price up 10% → Social mentions up 50%
        """
        patterns = []
        
        try:
            # Extract crypto price movements
            price_movements = self._extract_price_movements(crypto_obs)
            
            # Extract social mention counts
            social_mentions = self._extract_social_mentions(social_obs)
            
            # Find correlations
            for token, price_change in price_movements.items():
                if token in social_mentions:
                    mention_change = social_mentions[token].get('change_pct', 0)
                    
                    # Strong correlation if both moving in same direction
                    if abs(price_change) > 5 and abs(mention_change) > 20:
                        correlation = 1.0 if (price_change > 0) == (mention_change > 0) else -1.0
                        
                        patterns.append(CrossDomainPattern(
                            pattern_type='crypto_social',
                            domains=['crypto', 'social'],
                            description=f"{token} price {price_change:+.1f}% correlates with social mentions {mention_change:+.1f}%",
                            confidence=min(0.9, abs(correlation) * 0.8),
                            evidence=[
                                {'type': 'price_change', 'token': token, 'change_pct': price_change},
                                {'type': 'mention_change', 'token': token, 'change_pct': mention_change}
                            ],
                            correlation_score=correlation
                        ))
        except Exception as e:
            logger.debug(f"Crypto-social correlation detection error: {e}")
        
        return patterns
    
    def _detect_sentiment_price_correlation(
        self,
        crypto_obs: List[Dict],
        social_obs: List[Dict]
    ) -> List[CrossDomainPattern]:
        """
        Detect correlation between social sentiment and price movements.
        
        Example: Positive sentiment → Price increase
        """
        patterns = []
        
        try:
            # Extract price movements
            price_movements = self._extract_price_movements(crypto_obs)
            
            # Extract sentiment scores
            sentiment_scores = self._extract_sentiment_scores(social_obs)
            
            # Find correlations
            for token, price_change in price_movements.items():
                if token in sentiment_scores:
                    sentiment = sentiment_scores[token]
                    
                    # Positive sentiment + price increase = strong correlation
                    if sentiment > 0.6 and price_change > 3:
                        patterns.append(CrossDomainPattern(
                            pattern_type='sentiment_price',
                            domains=['crypto', 'social'],
                            description=f"Positive sentiment ({sentiment:.2f}) predicts {token} price increase ({price_change:+.1f}%)",
                            confidence=0.75,
                            evidence=[
                                {'type': 'sentiment', 'token': token, 'score': sentiment},
                                {'type': 'price_change', 'token': token, 'change_pct': price_change}
                            ],
                            correlation_score=0.8
                        ))
                    
                    # Negative sentiment + price decrease = strong correlation
                    elif sentiment < 0.4 and price_change < -3:
                        patterns.append(CrossDomainPattern(
                            pattern_type='sentiment_price',
                            domains=['crypto', 'social'],
                            description=f"Negative sentiment ({sentiment:.2f}) predicts {token} price decrease ({price_change:+.1f}%)",
                            confidence=0.75,
                            evidence=[
                                {'type': 'sentiment', 'token': token, 'score': sentiment},
                                {'type': 'price_change', 'token': token, 'change_pct': price_change}
                            ],
                            correlation_score=0.8
                        ))
        except Exception as e:
            logger.debug(f"Sentiment-price correlation detection error: {e}")
        
        return patterns
    
    def _detect_cross_platform_trends(self, by_domain: Dict[str, List[Dict]]) -> List[CrossDomainPattern]:
        """
        Detect topics trending across multiple platforms.
        
        Example: "AI agents" trending on MoltX, MoltBook, and Clawbr
        """
        patterns = []
        
        try:
            # Extract topics from each domain
            domain_topics = {}
            for domain, obs_list in by_domain.items():
                topics = self._extract_topics(obs_list)
                if topics:
                    domain_topics[domain] = topics
            
            # Find topics appearing in multiple domains
            if len(domain_topics) >= 2:
                all_topics = set()
                for topics in domain_topics.values():
                    all_topics.update(topics.keys())
                
                for topic in all_topics:
                    # Count how many domains have this topic
                    domains_with_topic = [
                        domain for domain, topics in domain_topics.items()
                        if topic in topics
                    ]
                    
                    if len(domains_with_topic) >= 2:
                        # Calculate average frequency
                        avg_freq = sum(
                            domain_topics[d][topic] for d in domains_with_topic
                        ) / len(domains_with_topic)
                        
                        patterns.append(CrossDomainPattern(
                            pattern_type='cross_platform_trend',
                            domains=domains_with_topic,
                            description=f"'{topic}' trending across {len(domains_with_topic)} platforms",
                            confidence=min(0.9, len(domains_with_topic) / len(domain_topics)),
                            evidence=[
                                {'domain': d, 'topic': topic, 'frequency': domain_topics[d][topic]}
                                for d in domains_with_topic
                            ],
                            correlation_score=avg_freq
                        ))
        except Exception as e:
            logger.debug(f"Cross-platform trend detection error: {e}")
        
        return patterns
    
    def _detect_engagement_patterns(self, social_obs: List[Dict]) -> List[CrossDomainPattern]:
        """
        Detect patterns in what content gets engagement.
        
        Example: Posts with images get 3x more engagement
        """
        patterns = []
        
        try:
            # Analyze engagement by content type
            engagement_by_type = defaultdict(list)
            
            for obs in social_obs:
                content_type = obs.get('content_type', 'text')
                engagement = obs.get('engagement', 0)
                
                if engagement > 0:
                    engagement_by_type[content_type].append(engagement)
            
            # Find high-performing content types
            if engagement_by_type:
                avg_engagement = sum(
                    sum(engagements) / len(engagements)
                    for engagements in engagement_by_type.values()
                ) / len(engagement_by_type)
                
                for content_type, engagements in engagement_by_type.items():
                    if len(engagements) >= 3:
                        avg = sum(engagements) / len(engagements)
                        
                        # If 2x better than average, it's a pattern
                        if avg > avg_engagement * 2:
                            patterns.append(CrossDomainPattern(
                                pattern_type='engagement_pattern',
                                domains=['social'],
                                description=f"{content_type} content gets {avg/avg_engagement:.1f}x more engagement",
                                confidence=0.7,
                                evidence=[
                                    {'content_type': content_type, 'avg_engagement': avg, 'sample_size': len(engagements)}
                                ],
                                correlation_score=avg / avg_engagement
                            ))
        except Exception as e:
            logger.debug(f"Engagement pattern detection error: {e}")
        
        return patterns
    
    def _extract_price_movements(self, crypto_obs: List[Dict]) -> Dict[str, float]:
        """Extract price movements from crypto observations"""
        movements = {}
        
        for obs in crypto_obs:
            if 'price_change_pct' in obs:
                token = obs.get('token', obs.get('symbol', 'unknown')).upper()
                movements[token] = obs['price_change_pct']
        
        return movements
    
    def _extract_social_mentions(self, social_obs: List[Dict]) -> Dict[str, Dict]:
        """Extract social mention counts from social observations"""
        mentions = defaultdict(lambda: {'count': 0, 'change_pct': 0})
        
        for obs in social_obs:
            if 'mentions' in obs:
                for token, data in obs['mentions'].items():
                    mentions[token.upper()]['count'] += data.get('count', 1)
                    mentions[token.upper()]['change_pct'] = data.get('change_pct', 0)
        
        return mentions
    
    def _extract_sentiment_scores(self, social_obs: List[Dict]) -> Dict[str, float]:
        """Extract sentiment scores from social observations"""
        sentiment = {}
        
        for obs in social_obs:
            if 'sentiment' in obs:
                token = obs.get('token', obs.get('topic', 'unknown')).upper()
                sentiment[token] = obs['sentiment']
        
        return sentiment
    
    def _extract_topics(self, obs_list: List[Dict]) -> Dict[str, int]:
        """Extract topics and their frequencies"""
        topics = defaultdict(int)
        
        for obs in obs_list:
            if 'topics' in obs:
                for topic in obs['topics']:
                    topics[topic.lower()] += 1
            elif 'topic' in obs:
                topics[obs['topic'].lower()] += 1
        
        return topics
    
    def generate_strategy_from_patterns(self, patterns: List[CrossDomainPattern]) -> Optional[Dict]:
        """
        Generate a multi-domain strategy from detected patterns.
        
        This is HORIZONTAL SYNTHESIS - using patterns to create strategies.
        
        Example:
        - Pattern: BTC price up + positive sentiment
        - Strategy: Create educational content about BTC, engage with BTC discussions
        """
        if not patterns:
            return None
        
        # Sort by confidence
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        
        # Use highest confidence pattern
        top_pattern = patterns[0]
        
        strategy = {
            'based_on_pattern': top_pattern.pattern_type,
            'confidence': top_pattern.confidence,
            'actions': []
        }
        
        # Generate actions based on pattern type
        if top_pattern.pattern_type == 'crypto_social':
            # Crypto-social correlation → Create content + engage
            token = top_pattern.evidence[0].get('token', 'crypto')
            strategy['actions'] = [
                {'type': 'create_content', 'topic': f"{token} market analysis", 'platform': 'moltbook'},
                {'type': 'engage', 'topic': token, 'platform': 'moltx'},
                {'type': 'monitor', 'topic': f"{token} price", 'platform': 'crypto'}
            ]
        
        elif top_pattern.pattern_type == 'sentiment_price':
            # Sentiment-price correlation → Trade + share insights
            token = top_pattern.evidence[0].get('token', 'crypto')
            sentiment = top_pattern.evidence[0].get('score', 0.5)
            
            if sentiment > 0.6:
                strategy['actions'] = [
                    {'type': 'post', 'content': f"Positive sentiment on {token}", 'platform': 'moltx'},
                    {'type': 'monitor', 'topic': f"{token} price", 'platform': 'crypto'}
                ]
            else:
                strategy['actions'] = [
                    {'type': 'post', 'content': f"Caution on {token}", 'platform': 'moltx'},
                    {'type': 'monitor', 'topic': f"{token} price", 'platform': 'crypto'}
                ]
        
        elif top_pattern.pattern_type == 'cross_platform_trend':
            # Cross-platform trend → Create content on all platforms
            topic = top_pattern.evidence[0].get('topic', 'trending topic')
            strategy['actions'] = [
                {'type': 'create_content', 'topic': topic, 'platform': 'moltbook'},
                {'type': 'post', 'topic': topic, 'platform': 'moltx'},
                {'type': 'engage', 'topic': topic, 'platform': 'clawbr'}
            ]
        
        elif top_pattern.pattern_type == 'engagement_pattern':
            # Engagement pattern → Use high-performing content type
            content_type = top_pattern.evidence[0].get('content_type', 'text')
            strategy['actions'] = [
                {'type': 'create_content', 'content_type': content_type, 'platform': 'moltx'},
                {'type': 'create_content', 'content_type': content_type, 'platform': 'moltbook'}
            ]
        
        return strategy
    
    def get_pattern_stats(self) -> Dict:
        """Get statistics on detected patterns"""
        return {
            'total_patterns': len(self.detected_patterns),
            'by_type': {
                pattern_type: len(patterns)
                for pattern_type, patterns in self.pattern_history.items()
            },
            'avg_confidence': sum(p.confidence for p in self.detected_patterns) / len(self.detected_patterns) if self.detected_patterns else 0,
            'recent_patterns': [p.to_dict() for p in self.detected_patterns[-5:]]
        }


# Singleton
_pattern_detector_instance: Optional[CrossDomainPatternDetector] = None


def get_cross_domain_pattern_detector() -> CrossDomainPatternDetector:
    """Get or create cross-domain pattern detector singleton"""
    global _pattern_detector_instance
    if _pattern_detector_instance is None:
        _pattern_detector_instance = CrossDomainPatternDetector()
    return _pattern_detector_instance
