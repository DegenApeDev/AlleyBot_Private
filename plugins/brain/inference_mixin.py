"""
Brain Plugin - Inference Mixin

Integrates World State Intelligence into the Brain plugin.
Provides trend detection, relationship analysis, and anomaly detection capabilities.

Part of AGI Core - Phase 7: World State Intelligence
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.autonomy.inference_engine import get_inference_engine, InferenceEngine

logger = logging.getLogger(__name__)


class InferenceMixin:
    """
    Mixin providing intelligence capabilities to the Brain plugin.
    
    This mixin integrates with the InferenceEngine to provide:
    - Trend awareness for content decisions
    - Relationship insights for engagement
    - Anomaly detection for alerts
    - Engagement predictions
    
    Usage:
        class BrainPlugin(InferenceMixin, ...):
            def __init__(self):
                self._setup_inference()
            
            def make_decision(self):
                trends = self.get_current_trends()
                if trends:
                    # Factor trends into decision
                    ...
    """
    
    def __init__(self):
        self._inference_engine: Optional[InferenceEngine] = None
        self._last_trend_check: Optional[datetime] = None
        self._cached_trends: List[Any] = []
        self._cached_anomalies: List[Any] = []
    
    def _setup_inference(self) -> None:
        """Initialize inference capabilities"""
        try:
            self._inference_engine = get_inference_engine()
            logger.info("🧠 InferenceMixin initialized")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize inference: {e}")
    
    def get_current_trends(self, refresh: bool = False, top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Get current trending topics.
        
        Args:
            refresh: Force refresh from database
            top_n: Number of trends to return
            
        Returns:
            List of trend dictionaries
        """
        if not self._inference_engine:
            return []
        
        # Cache for 5 minutes unless refresh requested
        if (refresh or 
            not self._cached_trends or 
            not self._last_trend_check or
            (datetime.now() - self._last_trend_check).seconds > 300):
            
            try:
                trends = self._inference_engine.detect_trends(hours=24, top_n=top_n)
                self._cached_trends = [t.to_dict() if hasattr(t, 'to_dict') else t for t in trends]
                self._last_trend_check = datetime.now()
            except Exception as e:
                logger.error(f"Error detecting trends: {e}")
                return []
        
        return self._cached_trends[:top_n]
    
    def get_relationship_insights(self) -> Dict[str, Any]:
        """
        Get insights about entity relationships.
        
        Returns:
            Dictionary with influencers, clusters, and bridges
        """
        if not self._inference_engine:
            return {}
        
        try:
            graph = self._inference_engine.analyze_relationships()
            
            return {
                'influencers': [
                    {
                        'entity_id': i['entity_id'],
                        'centrality': i['centrality'],
                        'connections': i['connections']
                    }
                    for i in graph.influencers[:10]
                ],
                'clusters_detected': len(graph.clusters),
                'echo_chambers': len(graph.echo_chambers),
                'bridges': len(graph.bridges)
            }
        except Exception as e:
            logger.error(f"Error analyzing relationships: {e}")
            return {}
    
    def predict_content_engagement(self, content: str) -> Dict[str, Any]:
        """
        Predict engagement for proposed content.
        
        Args:
            content: Content to analyze
            
        Returns:
            Prediction with estimated likes, replies, reposts
        """
        if not self._inference_engine:
            return {
                'predicted_likes': 10,
                'predicted_replies': 2,
                'predicted_reposts': 1,
                'confidence': 0.3,
                'factors': ['no_data']
            }
        
        try:
            prediction = self._inference_engine.predict_engagement(content)
            
            return {
                'predicted_likes': prediction.predicted_likes,
                'predicted_replies': prediction.predicted_replies,
                'predicted_reposts': prediction.predicted_reposts,
                'confidence': prediction.confidence,
                'factors': prediction.factors
            }
        except Exception as e:
            logger.error(f"Error predicting engagement: {e}")
            return {
                'predicted_likes': 10,
                'predicted_replies': 2,
                'predicted_reposts': 1,
                'confidence': 0.3,
                'factors': ['error']
            }
    
    def check_anomalies(self) -> List[Dict[str, Any]]:
        """
        Check for anomalies in world state.
        
        Returns:
            List of detected anomalies
        """
        if not self._inference_engine:
            return []
        
        try:
            anomalies = self._inference_engine.detect_anomalies(hours=6)
            
            return [
                {
                    'type': a.anomaly_type,
                    'severity': a.severity,
                    'description': a.description,
                    'entities': a.entities_involved,
                    'metrics': a.metrics,
                    'recommended_action': a.recommended_action
                }
                for a in anomalies
            ]
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []
    
    def get_sentiment_for_topic(self, topic: str) -> Dict[str, Any]:
        """
        Get sentiment evolution for a topic.
        
        Args:
            topic: Topic to analyze (hashtag or keyword)
            
        Returns:
            Sentiment evolution data
        """
        if not self._inference_engine:
            return {
                'topic': topic,
                'trend_direction': 'unknown',
                'volatility': 0,
                'key_events': []
            }
        
        try:
            evolution = self._inference_engine.track_sentiment(topic)
            
            return {
                'topic': evolution.topic,
                'trend_direction': evolution.trend_direction,
                'volatility': evolution.volatility,
                'timeline_length': len(evolution.timeline),
                'key_events': evolution.key_events
            }
        except Exception as e:
            logger.error(f"Error tracking sentiment: {e}")
            return {
                'topic': topic,
                'trend_direction': 'unknown',
                'volatility': 0,
                'key_events': []
            }
    
    def get_cross_platform_patterns(self) -> List[Dict[str, Any]]:
        """
        Find patterns across platforms.
        
        Returns:
            List of cross-platform patterns
        """
        if not self._inference_engine:
            return []
        
        try:
            patterns = self._inference_engine.find_cross_platform_patterns(hours=48)
            
            return [
                {
                    'type': p.pattern_type,
                    'platforms': p.platforms,
                    'description': p.description,
                    'strength': p.strength,
                    'entities': p.entities_involved[:5]
                }
                for p in patterns
            ]
        except Exception as e:
            logger.error(f"Error finding patterns: {e}")
            return []
    
    def should_alert_owner(self) -> Optional[Dict[str, Any]]:
        """
        Check if owner should be alerted about anomalies.
        
        Returns:
            Alert data if there are critical anomalies, None otherwise
        """
        anomalies = self.check_anomalies()
        
        critical_anomalies = [a for a in anomalies if a['severity'] == 'critical']
        
        if critical_anomalies:
            return {
                'alert_type': 'critical_anomaly',
                'count': len(critical_anomalies),
                'anomalies': critical_anomalies,
                'timestamp': datetime.now().isoformat()
            }
        
        # Also alert on viral opportunities
        viral_posts = [a for a in anomalies if a['type'] == 'viral_post']
        if viral_posts:
            return {
                'alert_type': 'viral_opportunity',
                'count': len(viral_posts),
                'posts': viral_posts,
                'timestamp': datetime.now().isoformat()
            }
        
        return None
    
    def get_intelligence_briefing(self) -> Dict[str, Any]:
        """
        Get comprehensive intelligence briefing for decision making.
        
        Returns:
            Summary of all intelligence data
        """
        if not self._inference_engine:
            return {'status': 'inference_unavailable'}
        
        try:
            summary = self._inference_engine.get_intelligence_summary()
            
            return {
                'status': 'active',
                'top_trends': self.get_current_trends(top_n=3),
                'relationship_insights': self.get_relationship_insights(),
                'cross_platform_patterns': len(self.get_cross_platform_patterns()),
                'active_anomalies': summary.get('active_anomalies', 0),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error generating briefing: {e}")
            return {'status': 'error', 'message': str(e)}


# Export mixin
__all__ = ['InferenceMixin']
