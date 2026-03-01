"""
AlleyBot World State Intelligence Engine - Phase 7

Turns raw world state data into actionable intelligence.
Implements trend detection, relationship analysis, predictive engagement,
sentiment evolution tracking, cross-platform patterns, and anomaly detection.

Part of AGI Core - Phase 7: World State Intelligence
"""

import json
import sqlite3
import statistics
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import logging

from src.autonomy.world_state import WorldStateManager, get_world_state_manager

logger = logging.getLogger(__name__)


@dataclass
class Trend:
    """A detected trend with metadata"""
    topic: str
    direction: str  # 'rising', 'falling', 'stable', 'volatile'
    strength: float  # 0-1 trend strength
    velocity: float  # Rate of change per hour
    acceleration: float  # Change in velocity
    data_points: int
    start_time: datetime
    predicted_peak: Optional[datetime] = None
    confidence: float = 0.0


@dataclass
class RelationshipGraph:
    """Graph of entity relationships with influence metrics"""
    central_entities: List[Dict[str, Any]]  # Most connected nodes
    clusters: List[Dict[str, Any]]  # Detected communities
    bridges: List[Dict[str, Any]]  # Entities connecting clusters
    influencers: List[Dict[str, Any]]  # High-impact entities
    echo_chambers: List[Dict[str, Any]]  # Tightly knit groups


@dataclass
class EngagementPrediction:
    """Predicted engagement for content"""
    content_hash: str
    predicted_likes: int
    predicted_replies: int
    predicted_reposts: int
    confidence: float
    factors: List[str]  # What drove this prediction


@dataclass
class SentimentEvolution:
    """How sentiment changed over time for a topic"""
    topic: str
    timeline: List[Dict[str, Any]]  # [{time, sentiment, volume}, ...]
    trend_direction: str  # 'improving', 'worsening', 'stable'
    volatility: float  # How much sentiment swings
    key_events: List[Dict[str, Any]]  # Events that caused shifts


@dataclass
class CrossPlatformPattern:
    """Pattern detected across multiple platforms"""
    pattern_type: str  # 'trend', 'sentiment', 'entity', 'topic'
    platforms: List[str]
    description: str
    strength: float
    entities_involved: List[str]
    time_window: Tuple[datetime, datetime]
    confidence: float = 0.0  # Confidence score 0-1


@dataclass
class Anomaly:
    """Detected anomaly in world state"""
    anomaly_type: str  # 'viral_post', 'engagement_spike', 'sentiment_shift', 'new_entity_burst'
    severity: str  # 'info', 'warning', 'critical'
    description: str
    entities_involved: List[str]
    metrics: Dict[str, float]  # What metrics are anomalous
    detected_at: datetime
    recommended_action: Optional[str] = None


class InferenceEngine:
    """
    World State Intelligence Engine
    
    Capabilities:
    1. Trend Detection - Identify rising topics before they peak
    2. Relationship Graph Analysis - Find influencers, clusters, echo chambers
    3. Predictive Engagement - Predict which posts will perform well
    4. Sentiment Evolution - Track how sentiment changes over time
    5. Cross-Platform Pattern Matching - Detect trends across platforms
    6. Anomaly Detection - Alert on unusual activity
    
    Usage:
        engine = InferenceEngine()
        
        # Detect trends
        trends = engine.detect_trends(hours=24)
        
        # Analyze relationships
        graph = engine.analyze_relationships()
        
        # Predict engagement
        prediction = engine.predict_engagement(content="My post text")
        
        # Track sentiment evolution
        evolution = engine.track_sentiment("#AlleyBot")
        
        # Find cross-platform patterns
        patterns = engine.find_cross_platform_patterns()
        
        # Detect anomalies
        anomalies = engine.detect_anomalies()
    """
    
    # Trend detection thresholds
    MIN_DATA_POINTS = 5
    TREND_THRESHOLD = 0.3  # Minimum velocity to be considered trending
    PEAK_PREDICTION_HOURS = 12  # How far ahead to predict peaks
    
    # Anomaly detection thresholds (standard deviations)
    ANOMALY_Z_SCORE = 2.5
    
    def __init__(self, world_state: Optional[WorldStateManager] = None):
        self.world_state = world_state or get_world_state_manager()
    
    def detect_trends(self, hours: int = 24, top_n: int = 10) -> List[Trend]:
        """
        Detect trending topics from world state.
        
        Analyzes topic mentions over time to identify:
        - Rising trends (increasing velocity)
        - Falling trends (decreasing velocity)
        - Predicted peak times
        
        Args:
            hours: Time window to analyze
            top_n: Number of top trends to return
            
        Returns:
            List of Trend objects sorted by strength
        """
        cutoff = datetime.now().replace(tzinfo=None) - timedelta(hours=hours)
        
        # Get all interactions in time window
        interactions = self._get_recent_interactions(cutoff)
        
        if not interactions:
            return []
        
        # Extract topics and their frequencies over time
        topic_timeline = defaultdict(list)
        
        for interaction in interactions:
            content = interaction.get('content', '')
            timestamp = interaction.get('timestamp', datetime.now())
            
            # Extract hashtags and mentions
            topics = self._extract_topics(content)
            
            for topic in topics:
                topic_timeline[topic].append(timestamp)
        
        # Calculate trend metrics for each topic
        trends = []
        
        for topic, timestamps in topic_timeline.items():
            if len(timestamps) < self.MIN_DATA_POINTS:
                continue
            
            # Sort chronologically
            timestamps.sort()
            
            # Calculate velocity and acceleration
            velocity, acceleration = self._calculate_trend_metrics(timestamps, hours)
            
            # Determine direction
            if velocity > self.TREND_THRESHOLD:
                direction = 'rising'
            elif velocity < -self.TREND_THRESHOLD:
                direction = 'falling'
            elif abs(velocity) < 0.1:
                direction = 'stable'
            else:
                direction = 'volatile'
            
            # Calculate strength (0-1)
            strength = min(1.0, abs(velocity) + abs(acceleration) * 0.5)
            
            # Predict peak time
            predicted_peak = None
            if direction == 'rising' and acceleration > 0:
                # Predict when trend will peak
                time_to_peak = hours * (1 - strength) * 0.5
                predicted_peak = datetime.now().replace(tzinfo=None) + timedelta(hours=time_to_peak)
            
            trend = Trend(
                topic=topic,
                direction=direction,
                strength=strength,
                velocity=velocity,
                acceleration=acceleration,
                data_points=len(timestamps),
                start_time=timestamps[0],
                predicted_peak=predicted_peak,
                confidence=min(0.95, len(timestamps) / 50)  # More data = higher confidence
            )
            
            trends.append(trend)
        
        # Sort by strength
        trends.sort(key=lambda t: t.strength, reverse=True)
        
        return trends[:top_n]
    
    def _get_recent_interactions(self, cutoff: datetime) -> List[Dict]:
        """Get recent interactions from world state"""
        interactions = []
        
        # Get all entities and their interactions
        with sqlite3.connect(self.world_state.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get posts/interactions from facts table using 'content' attribute
            rows = conn.execute('''
                SELECT * FROM facts 
                WHERE attribute IN ('content', 'post', 'interaction') 
                AND timestamp > ?
                ORDER BY timestamp DESC
            ''', (cutoff.isoformat(),)).fetchall()
            
            for row in rows:
                # Parse the value field as JSON or use directly
                try:
                    value_data = json.loads(row['value'])
                except:
                    value_data = {'content': row['value']}
                
                interactions.append({
                    'entity_id': row['entity_id'],
                    'content': value_data.get('content', row['value']),
                    'timestamp': datetime.fromisoformat(row['timestamp']),
                    'platform': value_data.get('platform', 'unknown')
                })
        
        return interactions
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract hashtags and key terms from content"""
        import re
        
        topics = []
        
        # Extract hashtags
        hashtags = re.findall(r'#\w+', content)
        topics.extend([h.lower() for h in hashtags])
        
        # Extract mentions
        mentions = re.findall(r'@\w+', content)
        topics.extend([m.lower() for m in mentions])
        
        return topics
    
    def _calculate_trend_metrics(self, timestamps: List[datetime], hours: int) -> Tuple[float, float]:
        """Calculate velocity and acceleration from timestamp series"""
        if len(timestamps) < 2:
            return 0.0, 0.0
        
        # Split into time buckets (hourly)
        bucket_counts = defaultdict(int)
        for ts in timestamps:
            bucket = int((ts - timestamps[0]).total_seconds() / 3600)
            bucket_counts[bucket] += 1
        
        # Calculate velocity (change per hour)
        if len(bucket_counts) < 2:
            return 0.0, 0.0
        
        buckets = sorted(bucket_counts.keys())
        counts = [bucket_counts[b] for b in buckets]
        
        # Linear regression for velocity
        n = len(buckets)
        sum_x = sum(buckets)
        sum_y = sum(counts)
        sum_xy = sum(x * y for x, y in zip(buckets, counts))
        sum_x2 = sum(x * x for x in buckets)
        
        velocity = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x) if (n * sum_x2 - sum_x * sum_x) != 0 else 0
        
        # Calculate acceleration (change in velocity)
        if len(counts) >= 3:
            first_half = counts[:len(counts)//2]
            second_half = counts[len(counts)//2:]
            
            v1 = sum(first_half) / len(first_half) if first_half else 0
            v2 = sum(second_half) / len(second_half) if second_half else 0
            
            acceleration = (v2 - v1) / (len(counts) / 2) if len(counts) > 0 else 0
        else:
            acceleration = 0
        
        return velocity, acceleration
    
    def analyze_relationships(self, min_interactions: int = 3) -> RelationshipGraph:
        """
        Analyze entity relationships to find influencers and clusters.
        
        Args:
            min_interactions: Minimum interactions to include entity
            
        Returns:
            RelationshipGraph with influencers, clusters, and echo chambers
        """
        # Build interaction graph
        entity_interactions = defaultdict(lambda: defaultdict(int))
        entity_metrics = defaultdict(lambda: {'mentions': 0, 'engagement': 0})
        
        cutoff = datetime.now() - timedelta(hours=48)
        interactions = self._get_recent_interactions(cutoff)
        
        for interaction in interactions:
            source = interaction['entity_id']
            content = interaction.get('content', '')
            
            # Extract mentioned entities
            import re
            mentions = re.findall(r'@(\w+)', content)
            
            for target in mentions:
                entity_interactions[source][target] += 1
                entity_metrics[target]['mentions'] += 1
        
        # Calculate centrality scores
        centrality = {}
        for entity in entity_interactions:
            # Simple degree centrality
            connections = len(entity_interactions[entity])
            total_interactions = sum(entity_interactions[entity].values())
            centrality[entity] = connections + total_interactions * 0.1
        
        # Find influencers (high centrality)
        sorted_entities = sorted(centrality.items(), key=lambda x: x[1], reverse=True)
        influencers = [
            {
                'entity_id': e[0],
                'centrality': e[1],
                'connections': len(entity_interactions[e[0]]),
                'total_interactions': sum(entity_interactions[e[0]].values())
            }
            for e in sorted_entities[:10]
        ]
        
        # Simple clustering (entities that interact with same others)
        clusters = self._find_clusters(entity_interactions, min_size=3)
        
        # Find bridges (entities connecting clusters)
        bridges = self._find_bridges(entity_interactions, clusters)
        
        # Find echo chambers (tightly connected groups)
        echo_chambers = self._find_echo_chambers(entity_interactions)
        
        return RelationshipGraph(
            central_entities=sorted_entities[:20],
            clusters=clusters,
            bridges=bridges,
            influencers=influencers,
            echo_chambers=echo_chambers
        )
    
    def _find_clusters(self, interactions: Dict, min_size: int = 3) -> List[Dict]:
        """Find clusters using simple connected components"""
        # Build adjacency list
        adj = defaultdict(set)
        for source, targets in interactions.items():
            for target in targets:
                adj[source].add(target)
                adj[target].add(source)
        
        # Find connected components
        visited = set()
        clusters = []
        
        for entity in adj:
            if entity in visited:
                continue
            
            # BFS to find component
            component = set()
            queue = [entity]
            
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                
                visited.add(current)
                component.add(current)
                
                for neighbor in adj[current]:
                    if neighbor not in visited:
                        queue.append(neighbor)
            
            if len(component) >= min_size:
                clusters.append({
                    'id': f'cluster_{len(clusters)}',
                    'entities': list(component),
                    'size': len(component)
                })
        
        return clusters
    
    def _find_bridges(self, interactions: Dict, clusters: List[Dict]) -> List[Dict]:
        """Find entities that connect multiple clusters"""
        # Build cluster membership
        entity_clusters = defaultdict(list)
        for i, cluster in enumerate(clusters):
            for entity in cluster['entities']:
                entity_clusters[entity].append(i)
        
        # Find entities in multiple clusters
        bridges = []
        for entity, cluster_ids in entity_clusters.items():
            if len(cluster_ids) > 1:
                bridges.append({
                    'entity_id': entity,
                    'connects_clusters': cluster_ids,
                    'bridge_strength': len(cluster_ids)
                })
        
        return bridges
    
    def _find_echo_chambers(self, interactions: Dict) -> List[Dict]:
        """Find tightly connected groups (high internal interaction rate)"""
        chambers = []
        
        clusters = self._find_clusters(interactions, min_size=3)
        
        for cluster in clusters:
            entities = set(cluster['entities'])
            internal_edges = 0
            external_edges = 0
            
            for entity in entities:
                for target, count in interactions.get(entity, {}).items():
                    if target in entities:
                        internal_edges += count
                    else:
                        external_edges += count
            
            # Calculate density
            total_possible = len(entities) * (len(entities) - 1)
            density = internal_edges / total_possible if total_possible > 0 else 0
            
            # Echo chamber if high density and low external interaction
            isolation = internal_edges / (internal_edges + external_edges + 1)
            
            if density > 0.3 and isolation > 0.7:
                chambers.append({
                    'id': cluster['id'],
                    'entities': list(entities),
                    'density': density,
                    'isolation': isolation,
                    'size': len(entities)
                })
        
        return chambers
    
    def predict_engagement(self, content: str, author_id: Optional[str] = None) -> EngagementPrediction:
        """
        Predict engagement for a piece of content.
        
        Uses historical patterns and content analysis.
        
        Args:
            content: The content to analyze
            author_id: Optional author for personalized prediction
            
        Returns:
            EngagementPrediction with predicted metrics
        """
        factors = []
        
        # Factor 1: Content length
        length = len(content)
        if 100 <= length <= 280:
            length_score = 1.0
            factors.append("optimal_length")
        elif length < 50:
            length_score = 0.5
            factors.append("too_short")
        else:
            length_score = max(0.3, 1 - (length - 280) / 1000)
            factors.append("long_content")
        
        # Factor 2: Hashtags
        import re
        hashtags = re.findall(r'#\w+', content)
        if 1 <= len(hashtags) <= 3:
            hashtag_score = 1.0
            factors.append("good_hashtag_count")
        elif len(hashtags) > 5:
            hashtag_score = 0.6
            factors.append("too_many_hashtags")
        else:
            hashtag_score = 0.7
            factors.append("no_hashtags")
        
        # Factor 3: Questions (engagement driver)
        questions = content.count('?')
        if questions > 0:
            question_score = 1.2
            factors.append("asks_question")
        else:
            question_score = 1.0
        
        # Factor 4: Author history
        author_score = 0.5
        if author_id:
            author_metrics = self._get_author_metrics(author_id)
            avg_engagement = author_metrics.get('avg_engagement', 10)
            author_score = min(1.5, max(0.5, avg_engagement / 20))
            factors.append("author_history")
        
        # Calculate predictions
        base_likes = 20
        base_replies = 5
        base_reposts = 3
        
        combined_score = length_score * hashtag_score * question_score * author_score
        
        prediction = EngagementPrediction(
            content_hash=hash(content) % 10000000000,
            predicted_likes=int(base_likes * combined_score),
            predicted_replies=int(base_replies * combined_score * (1.5 if questions > 0 else 1)),
            predicted_reposts=int(base_reposts * combined_score),
            confidence=min(0.9, 0.5 + len(factors) * 0.1),
            factors=factors
        )
        
        return prediction
    
        
        engagements = []
        for row in rows:
            try:
                value_data = json.loads(row['value'])
                total = value_data.get('likes', 0) + value_data.get('replies', 0) + value_data.get('reposts', 0)
            except:
                total = 0
            engagements.append(total)
        
        return {
            'avg_engagement': statistics.mean(engagements) if engagements else 10,
            'max_engagement': max(engagements) if engagements else 0,
            'post_count': len(engagements)
        }
    
    def track_sentiment(self, topic: str, hours: int = 168) -> SentimentEvolution:
        """
        Track sentiment evolution for a topic over time.
        
        Args:
            topic: Topic to track (hashtag or keyword)
            hours: Time window to analyze (default 1 week)
            
        Returns:
            SentimentEvolution with timeline and key events
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Get mentions of topic
        mentions = self._get_topic_mentions(topic, cutoff)
        
        if not mentions:
            return SentimentEvolution(
                topic=topic,
                timeline=[],
                trend_direction='stable',
                volatility=0.0,
                key_events=[]
            )
        
        # Calculate hourly sentiment buckets
        hourly_sentiment = defaultdict(list)
        
        for mention in mentions:
            hour_bucket = mention['timestamp'].replace(minute=0, second=0, microsecond=0)
            sentiment = self._estimate_sentiment(mention['content'])
            hourly_sentiment[hour_bucket].append(sentiment)
        
        # Build timeline
        timeline = []
        for hour in sorted(hourly_sentiment.keys()):
            sentiments = hourly_sentiment[hour]
            avg_sentiment = statistics.mean(sentiments)
            volume = len(sentiments)
            
            timeline.append({
                'time': hour.isoformat(),
                'sentiment': avg_sentiment,
                'volume': volume,
                'sentiment_label': 'positive' if avg_sentiment > 0.2 else 'negative' if avg_sentiment < -0.2 else 'neutral'
            })
        
        # Determine trend
        if len(timeline) >= 2:
            first_half = timeline[:len(timeline)//2]
            second_half = timeline[len(timeline)//2:]
            
            avg_first = statistics.mean([t['sentiment'] for t in first_half])
            avg_second = statistics.mean([t['sentiment'] for t in second_half])
            
            diff = avg_second - avg_first
            
            if diff > 0.1:
                trend_direction = 'improving'
            elif diff < -0.1:
                trend_direction = 'worsening'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'stable'
        
        # Calculate volatility
        if len(timeline) >= 3:
            sentiments = [t['sentiment'] for t in timeline]
            volatility = statistics.stdev(sentiments) if len(sentiments) > 1 else 0
        else:
            volatility = 0
        
        # Identify key events (sentiment shifts)
        key_events = []
        for i in range(1, len(timeline)):
            prev = timeline[i-1]
            curr = timeline[i]
            
            shift = abs(curr['sentiment'] - prev['sentiment'])
            if shift > 0.3:
                key_events.append({
                    'time': curr['time'],
                    'shift': shift,
                    'direction': 'positive' if curr['sentiment'] > prev['sentiment'] else 'negative',
                    'volume': curr['volume']
                })
        
        return SentimentEvolution(
            topic=topic,
            timeline=timeline,
            trend_direction=trend_direction,
            volatility=volatility,
            key_events=key_events[:5]  # Top 5 events
        )
    
    def _get_topic_mentions(self, topic: str, cutoff: datetime) -> List[Dict]:
        """Get all mentions of a topic"""
        mentions = []
        
        topic_lower = topic.lower().lstrip('#')
        
        with sqlite3.connect(self.world_state.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('''
                SELECT * FROM facts 
                WHERE attribute IN ('content', 'post', 'interaction')
                AND timestamp > ?
            ''', (cutoff.isoformat(),)).fetchall()
        
        for row in rows:
            try:
                value_data = json.loads(row['value'])
                content = value_data.get('content', row['value']).lower()
            except:
                content = row['value'].lower()
            
            if f'#{topic_lower}' in content or topic_lower in content:
                mentions.append({
                    'entity_id': row['entity_id'],
                    'content': content,
                    'timestamp': datetime.fromisoformat(row['timestamp'])
                })
        
        return mentions
    
    def _estimate_sentiment(self, text: str) -> float:
        """Simple sentiment estimation (-1 to 1)"""
        positive_words = ['great', 'awesome', 'love', 'best', 'amazing', 'excellent', 'good', 'happy', 'thanks']
        negative_words = ['bad', 'terrible', 'hate', 'worst', 'awful', 'sucks', 'annoying', 'angry', 'disappointed']
        
        text_lower = text.lower()
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count + neg_count == 0:
            return 0.0
        
        return (pos_count - neg_count) / (pos_count + neg_count)
    
    def find_cross_platform_patterns(self, hours: int = 48) -> List[CrossPlatformPattern]:
        """
        Detect patterns that appear across multiple platforms.
        
        Args:
            hours: Time window to analyze
            
        Returns:
            List of cross-platform patterns
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Get interactions by platform
        platform_interactions = defaultdict(list)
        
        with sqlite3.connect(self.world_state.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('''
                SELECT * FROM facts 
                WHERE attribute IN ('content', 'post', 'interaction')
                AND timestamp > ?
            ''', (cutoff.isoformat(),)).fetchall()
        
        for row in rows:
            try:
                value_data = json.loads(row['value'])
                platform = value_data.get('platform', 'unknown')
            except:
                platform = 'unknown'
            
            platform_interactions[platform].append({
                'content': value_data.get('content', row['value']),
                'timestamp': datetime.fromisoformat(row['timestamp']),
                'entity_id': row['entity_id']
            })
        
        patterns = []
        platforms = list(platform_interactions.keys())
        
        if len(platforms) < 2:
            return patterns
        
        # Find common topics across platforms
        all_topics = defaultdict(lambda: defaultdict(int))
        
        for platform, interactions in platform_interactions.items():
            for interaction in interactions:
                topics = self._extract_topics(interaction['content'])
                for topic in topics:
                    all_topics[topic][platform] += 1
        
        # Identify patterns (topic appearing on multiple platforms)
        for topic, platform_counts in all_topics.items():
            if len(platform_counts) >= 2:
                platforms_with_topic = list(platform_counts.keys())
                total_mentions = sum(platform_counts.values())
                
                # Find entities involved
                entities = set()
                for platform in platforms_with_topic:
                    for interaction in platform_interactions[platform]:
                        if topic in interaction['content'].lower():
                            entities.add(interaction['entity_id'])
                
                pattern = CrossPlatformPattern(
                    pattern_type='trend',
                    platforms=platforms_with_topic,
                    description=f"Topic '{topic}' trending across {len(platforms_with_topic)} platforms",
                    strength=min(1.0, total_mentions / 20),
                    entities_involved=list(entities)[:10],
                    time_window=(cutoff, datetime.now())
                )
                
                patterns.append(pattern)
        
        # Sort by strength
        patterns.sort(key=lambda p: p.strength, reverse=True)
        
        return patterns[:10]
    
    def detect_anomalies(self, hours: int = 24) -> List[Anomaly]:
        """
        Detect anomalies in world state.
        
        Args:
            hours: Time window to analyze
            
        Returns:
            List of detected anomalies
        """
        anomalies = []
        cutoff = datetime.now() - timedelta(hours=hours)
        
        # Get historical baseline (previous period)
        baseline_cutoff = cutoff - timedelta(hours=hours)
        
        baseline_metrics = self._calculate_metrics(baseline_cutoff, cutoff)
        current_metrics = self._calculate_metrics(cutoff, datetime.now())
        
        # Check for engagement spikes
        if baseline_metrics['avg_engagement'] > 0:
            engagement_ratio = current_metrics['avg_engagement'] / baseline_metrics['avg_engagement']
            
            if engagement_ratio > 3:
                anomalies.append(Anomaly(
                    anomaly_type='engagement_spike',
                    severity='warning',
                    description=f"Engagement spike detected: {engagement_ratio:.1f}x normal levels",
                    entities_involved=current_metrics['top_entities'][:5],
                    metrics={'engagement_ratio': engagement_ratio},
                    detected_at=datetime.now(),
                    recommended_action="Monitor for viral content or drama"
                ))
        
        # Check for viral posts
        viral_threshold = baseline_metrics['avg_engagement'] * 5
        for entity, engagement in current_metrics['entity_engagement'].items():
            if engagement > viral_threshold:
                anomalies.append(Anomaly(
                    anomaly_type='viral_post',
                    severity='info',
                    description=f"Viral content detected from {entity}",
                    entities_involved=[entity],
                    metrics={'engagement': engagement, 'threshold': viral_threshold},
                    detected_at=datetime.now(),
                    recommended_action="Consider engaging with viral content"
                ))
        
        # Check for sentiment shifts
        if baseline_metrics['sentiment'] and current_metrics['sentiment']:
            sentiment_shift = abs(current_metrics['sentiment'] - baseline_metrics['sentiment'])
            
            if sentiment_shift > 0.3:
                anomalies.append(Anomaly(
                    anomaly_type='sentiment_shift',
                    severity='warning' if sentiment_shift > 0.5 else 'info',
                    description=f"Significant sentiment shift detected: {sentiment_shift:.0%}",
                    entities_involved=[],
                    metrics={'sentiment_shift': sentiment_shift},
                    detected_at=datetime.now(),
                    recommended_action="Investigate cause of sentiment change"
                ))
        
        # Check for new entity bursts
        new_entities = set(current_metrics['entities']) - set(baseline_metrics['entities'])
        if len(new_entities) > 10:
            anomalies.append(Anomaly(
                anomaly_type='new_entity_burst',
                severity='info',
                description=f"Sudden influx of {len(new_entities)} new entities",
                entities_involved=list(new_entities)[:10],
                metrics={'new_entity_count': len(new_entities)},
                detected_at=datetime.now(),
                recommended_action="Monitor for bot activity or coordinated campaign"
            ))
        
        return anomalies
    
    def _calculate_metrics(self, start: datetime, end: datetime) -> Dict[str, Any]:
        """Calculate metrics for a time period"""
        with sqlite3.connect(self.world_state.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute('''
                SELECT * FROM facts 
                WHERE timestamp > ? AND timestamp <= ?
            ''', (start.isoformat(), end.isoformat())).fetchall()
        
        if not rows:
            return {
                'avg_engagement': 0,
                'sentiment': 0,
                'entities': [],
                'top_entities': [],
                'entity_engagement': {}
            }
        
        # Calculate engagement
        engagements = []
        entity_engagement = defaultdict(int)
        entities = set()
        sentiments = []
        
        for row in rows:
            try:
                value_data = json.loads(row['value'])
                engagement = value_data.get('likes', 0) + value_data.get('replies', 0) + value_data.get('reposts', 0)
                sentiments.append(self._estimate_sentiment(value_data.get('content', row['value'])))
            except:
                engagement = 0
            
            entities.add(row['entity_id'])
            engagements.append(engagement)
            entity_engagement[row['entity_id']] += engagement
        
        # Sort by engagement
        top_entities = sorted(entity_engagement.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'avg_engagement': statistics.mean(engagements) if engagements else 0,
            'sentiment': statistics.mean(sentiments) if sentiments else 0,
            'entities': list(entities),
            'top_entities': [e[0] for e in top_entities[:10]],
            'entity_engagement': dict(entity_engagement)
        }
    
    def get_intelligence_summary(self) -> Dict[str, Any]:
        """Get comprehensive intelligence summary"""
        return {
            'trends': [t.topic for t in self.detect_trends(hours=24, top_n=5)],
            'influencers': len(self.analyze_relationships().influencers),
            'cross_platform_patterns': len(self.find_cross_platform_patterns()),
            'active_anomalies': len(self.detect_anomalies()),
            'sentiment_tracked': len(self.track_sentiment('#AlleyBot').timeline)
        }


# Singleton
_inference_engine_instance: Optional[InferenceEngine] = None


def get_inference_engine(world_state: Optional[WorldStateManager] = None) -> InferenceEngine:
    """Get or create InferenceEngine singleton"""
    global _inference_engine_instance
    if _inference_engine_instance is None:
        _inference_engine_instance = InferenceEngine(world_state)
    return _inference_engine_instance
