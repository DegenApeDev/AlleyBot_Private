"""
Brain Plugin - Inference Mixin

Integrates World State Intelligence into the Brain plugin.
Provides trend detection, relationship analysis, and anomaly detection capabilities.
Incorporates voice emotion data for multimodal analysis.

Part of AGI Core - Phase 7: World State Intelligence
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.autonomy.inference_engine import get_inference_engine, InferenceEngine

try:
    from src.audio.voice_emotion import get_voice_emotion
    VOICE_EMOTION_AVAILABLE = True
except ImportError:
    get_voice_emotion = None
    VOICE_EMOTION_AVAILABLE = False

logger = logging.getLogger(__name__)


class InferenceMixin:
    """
    Mixin providing intelligence capabilities to the Brain plugin.
    
    This mixin integrates with the InferenceEngine to provide:
    - Trend awareness for content decisions
    - Relationship insights for engagement
    - Anomaly detection for alerts
    - Engagement predictions
    - Multimodal analysis incorporating voice emotion data
    
    Usage:
        class BrainPlugin(InferenceMixin, ...):
            def __init__(self):
                self._setup_inference()
            
            def make_decision(self):
                trends = self.get_current_trends()
                emotion = self.get_current_voice_emotion()
                if trends or emotion['confidence'] > 0.7:
                    # Factor trends and emotion into decision
                    ...
    """
    
    def __init__(self):
        self._inference_engine: Optional[InferenceEngine] = None
        self._voice_emotion: Optional[Any] = None
        self._last_trend_check: Optional[datetime] = None
        self._cached_trends: List[Any] = []
        self._cached_anomalies: List[Any] = []
        self._cached_emotion: Dict[str, Any] = {}
        self._last_emotion_check: Optional[datetime] = None
    
    def _setup_inference(self) -> None:
        """Initialize inference capabilities"""
        try:
            self._inference_engine = get_inference_engine()
            logger.info("🧠 InferenceMixin initialized")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize inference: {e}")
        
        if VOICE_EMOTION_AVAILABLE:
            try:
                self._voice_emotion = get_voice_emotion()
                logger.info("🎤 Voice emotion analyzer integrated")
            except Exception as e:
                logger.warning(f"⚠️ Failed to initialize voice emotion: {e}")
    
    def get_current_voice_emotion(self, refresh: bool = False) -> Dict[str, Any]:
        """Get latest voice emotion data with caching (30s)."""
        if (refresh or 
            not self._cached_emotion or 
            not self._last_emotion_check or
            (datetime.now() - self._last_emotion_check).seconds > 30):
            
            if not self._voice_emotion:
                self._cached_emotion = {"emotion": "unknown", "confidence": 0.0}
            else:
                try:
                    latest = self._voice_emotion.get_latest_emotion()
                    self._cached_emotion = {
                        "emotion": getattr(latest, "primary_emotion", "neutral"),
                        "confidence": float(getattr(latest, "confidence", 0.0)),
                        "valence": getattr(latest, "valence", None),
                        "arousal": getattr(latest, "arousal", None),
                        "timestamp": getattr(latest, "timestamp", datetime.now()).isoformat(),
                    }
                    self._last_emotion_check = datetime.now()
                except Exception as e:
                    logger.error(f"Failed to get voice emotion: {e}")
                    self._cached_emotion = {"emotion": "unknown", "confidence": 0.0}
        
        return self._cached_emotion.copy()
    
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
        Predict engagement for proposed content with voice emotion context.
        
        Args:
            content: Content to analyze
            
        Returns:
            Prediction with estimated likes, replies, reposts
        """
        emotion = self.get_current_voice_emotion()
        
        if not self._inference_engine:
            factor = 1.0
            if emotion["confidence"] > 0.6:
                emotion_map = {
                    "happy": 1.4,
                    "excited": 1.6,
                    "neutral": 1.0,
                    "sad": 0.6,
                    "angry": 0.4,
                    "fear": 0.5,
                    "disgust": 0.3,
                }
                factor = emotion_map.get(emotion["emotion"], 1.0)
            return {
                "predicted_likes": int(10 * factor),
                "predicted_replies": int(2 * factor),
                "predicted_reposts": int(1 * factor),
                "confidence": min(0.3 * emotion["confidence"], 0.9),
                "factors": [f"voice_emotion:{emotion['emotion']}:{factor:.2f}"]
            }
        
        try:
            context = (
                f"[Multimodal Voice Context] User emotion: {emotion['emotion']} "
                f"(conf: {emotion['confidence']:.2f}, valence: {emotion.get('valence', 'N/A')}). "
                f"Predict engagement for: {content}"
            )
            prediction = self._inference_engine.predict_engagement(context)
            
            return {
                'predicted_likes': prediction.predicted_likes,
                'predicted_replies': prediction.predicted_replies,
                'predicted_reposts': prediction.predicted_reposts,
                'confidence': prediction.confidence,
                'factors': prediction.factors + [f"voice:{emotion['emotion']}:{emotion['confidence']:.2f}"]
            }
        except Exception as e:
            logger.error(f"Error predicting engagement: {e}")
            return {
                'predicted_likes': 10,
                'predicted_replies': 2,
                'predicted_reposts': 1,
                'confidence': 0.3,
                'factors': ['error', f"voice:{emotion['emotion']}"]
            }
    
    def check_anomalies(self) -> List[Dict[str, Any]]:
        """
        Check for anomalies in world state, including voice emotion extremes.
        
        Returns:
            List of detected anomalies
        """
        anomalies: List[Any] = []
        if self._inference_engine:
            try:
                anomalies = self._inference_engine.detect_anomalies(hours=6)
            except Exception as e:
                logger.error(f"Error detecting anomalies: {e}")
        
        # Multimodal: add voice emotion anomaly
        voice_emotion = self.get_current_voice_emotion()
        extreme_emotions = ["fear", "anger", "disgust", "sadness"]
        if (voice_emotion["confidence"] > 0.7 and 
            voice_emotion["emotion"] in extreme_emotions):
            severity = "high" if voice_emotion["emotion"] in ["fear", "anger"] else "medium"
            voice_anomaly: Dict[str, Any] = {
                "type": "extreme_voice_emotion",
                "severity": severity,
                "description": f"Strong {voice_emotion['emotion']} emotion in user voice (conf: {voice_emotion['confidence']:.2f})",
                "entities": ["user_voice"],
                "metrics": {
                    "emotion": voice_emotion["emotion"],
                    "confidence": voice_emotion["confidence"],
                    "valence": voice_emotion.get("valence"),
                    "arousal": voice_emotion.get("arousal"),
                },
                "recommended_action": "Respond empathetically, validate emotions, de-escalate if needed",
            }
            anomalies.append(voice_anomaly)
        
        # Convert to standardized dicts
        result: List[Dict[str, Any]] = []
        for a in anomalies:
            if isinstance(a, dict):
                result.append(a)
            else:
                result.append({
                    "type": getattr(a, "anomaly_type", "unknown"),
                    "severity": getattr(a, "severity", "low"),
                    "description": getattr(a, "description", ""),
                    "entities": getattr(a, "entities_involved", []),
                    "metrics": getattr(a, "metrics", {}),
                    "recommended_action": getattr(a, "recommended_action", ""),
                })
        return result
    
    def get_sentiment_for_topic(self, topic: str) -> Dict[str, Any]:
        """
        Get sentiment evolution for a topic with voice emotion context.
        
        Args:
            topic: Topic to analyze (hashtag or keyword)
            
        Returns:
            Sentiment evolution data
        """
        emotion = self.get_current_voice_emotion()
        
        if not self._inference_engine:
            return {
                "topic": topic,
                "trend_direction": emotion["emotion"],
                "volatility": emotion["confidence"],
                "timeline_length": 0,
                "key_events": [f"Voice emotion: {emotion['emotion']} ({emotion['confidence']:.2f})"],
            }
        
        try:
            query = (
                f"Topic sentiment evolution: {topic}. "
                f"Current voice emotion context: {emotion['emotion']} (conf: {emotion['confidence']:.2f}). "
                f"Track sentiment trend."
            )
            evolution = self._inference_engine.track_sentiment(query)
            
            return {
                'topic': evolution.topic,
                'trend_direction': evolution.trend_direction,
                'volatility': evolution.volatility,
                'timeline_length': len(evolution.timeline),
                'key_events': evolution.key_events,
            }
        except Exception as e:
            logger.error(f"Error tracking sentiment: {e}")
            return {
                'topic': topic,
                'trend_direction': emotion["emotion"],
                'volatility': emotion["confidence"],
                'key_events': [f"Voice: {emotion['emotion']}"]
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